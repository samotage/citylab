"""Data verification service — the shared pre-hackathon gate logic.

Runs completeness / freshness / consistency checks against the database for each
ingestion source (OpenNEM / BOM / Solcast) and returns a structured, per-source,
per-category pass/fail result. Both the `cli-citylab data verify` command and the
Level 2 data-quality tests call this so there is one source of truth for "are the
pipelines trustworthy?".

Design notes:
  - Pure read-side: only SELECTs, safe against any database.
  - Each check returns a CheckResult; categories aggregate checks; sources
    aggregate categories; the report aggregates sources.
  - A category with zero relevant data is reported as a FAILURE (empty pipeline
    is not "passing") unless the source itself has never been seeded — that is
    surfaced explicitly as `no_data`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from citylab.extensions import db

# Canonical fuel set (kept in sync with the OpenNEM fetcher).
from citylab.services.ingestion.opennem import (
    FUEL_TYPES,
    INTERCONNECTORS,
    OPENNEM_FUEL_MAP,
)

KNOWN_FUELS = set(FUEL_TYPES) | set(OPENNEM_FUEL_MAP.values())
KNOWN_CORRIDORS = {ic["id"] for ic in INTERCONNECTORS}

# Expected sampling intervals per source (seconds), used for freshness windows.
# Generous 2x multipliers keep the gate from flapping on demo cadence.
EXPECTED_INTERVAL_SECONDS = {
    "opennem": 5 * 60,       # 5-minute dispatch
    "bom": 3 * 3600,         # 3-hourly forecasts
    "solcast": 30 * 60,      # 30-minute intraday
}

# Freshness tolerance: most recent point must be within this many seconds of now.
# Synthetic snapshots stamp data around "now", so a wide window is fine.
FRESHNESS_TOLERANCE_SECONDS = {
    "opennem": 30 * 60,
    "bom": 24 * 3600,
    "solcast": 6 * 3600,
}


def _aware(dt):
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""
    count: int = 0


@dataclass
class CategoryResult:
    name: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks) if self.checks else False

    def to_dict(self) -> dict:
        return {
            "category": self.name,
            "passed": self.passed,
            "checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail, "count": c.count}
                for c in self.checks
            ],
        }


@dataclass
class SourceResult:
    source: str
    has_data: bool
    categories: list[CategoryResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.has_data and all(c.passed for c in self.categories)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "has_data": self.has_data,
            "passed": self.passed,
            "categories": [c.to_dict() for c in self.categories],
        }


@dataclass
class VerifyReport:
    sources: list[SourceResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return bool(self.sources) and all(s.passed for s in self.sources)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "sources": [s.to_dict() for s in self.sources],
        }


# ---------------------------------------------------------------------------
# OpenNEM checks
# ---------------------------------------------------------------------------


def _verify_opennem(session, region: str = "VIC1") -> SourceResult:
    from citylab.models.energy import (
        EnergyPrice,
        GenerationOutput,
        InterconnectorFlow,
        PriceForecast,
    )

    price_count = (
        session.query(func.count(EnergyPrice.id))
        .filter(EnergyPrice.region == region)
        .scalar()
    )
    has_data = bool(price_count)
    src = SourceResult(source="opennem", has_data=has_data)
    if not has_data:
        return src

    # --- Completeness ---
    completeness = CategoryResult(name="completeness")
    null_prices = (
        session.query(func.count(EnergyPrice.id))
        .filter(EnergyPrice.region == region, EnergyPrice.price_aud_mwh.is_(None))
        .scalar()
    )
    completeness.checks.append(
        CheckResult("price_non_null", null_prices == 0,
                    f"{null_prices} null price rows", price_count)
    )

    gen_rows = (
        session.query(GenerationOutput)
        .filter(GenerationOutput.region == region)
        .all()
    )
    bad_output = [g for g in gen_rows if g.output_mw is None]
    bad_fuel = [g for g in gen_rows if g.fuel_type not in KNOWN_FUELS]
    completeness.checks.append(
        CheckResult("generation_output_non_null", not bad_output,
                    f"{len(bad_output)} null output_mw rows", len(gen_rows))
    )
    completeness.checks.append(
        CheckResult("generation_fuel_known", not bad_fuel,
                    f"{len(bad_fuel)} unknown fuel_type rows", len(gen_rows))
    )

    flows = session.query(InterconnectorFlow).all()
    bad_corridor = [f for f in flows if f.interconnector_id not in KNOWN_CORRIDORS]
    completeness.checks.append(
        CheckResult("interconnector_known_corridor", not bad_corridor,
                    f"{len(bad_corridor)} unknown-corridor flows", len(flows))
    )
    src.categories.append(completeness)

    # --- Freshness ---
    freshness = CategoryResult(name="freshness")
    latest = _aware(
        session.query(func.max(EnergyPrice.interval_start))
        .filter(EnergyPrice.region == region)
        .scalar()
    )
    now = datetime.now(timezone.utc)
    tol = FRESHNESS_TOLERANCE_SECONDS["opennem"]
    fresh_ok = latest is not None and (now - latest).total_seconds() <= tol
    freshness.checks.append(
        CheckResult("price_recent", fresh_ok,
                    f"latest={latest.isoformat() if latest else None}", 0)
    )
    src.categories.append(freshness)

    # --- Consistency ---
    consistency = CategoryResult(name="consistency")
    corridors_present = {f.interconnector_id for f in flows}
    all_corridors = corridors_present >= KNOWN_CORRIDORS
    consistency.checks.append(
        CheckResult("all_corridors_present", all_corridors,
                    f"{len(corridors_present)}/{len(KNOWN_CORRIDORS)} corridors",
                    len(corridors_present))
    )

    # Price forecasts must look forward.
    forecasts = (
        session.query(PriceForecast).filter(PriceForecast.region == region).all()
    )
    backward = [
        f for f in forecasts
        if _aware(f.forecast_for) and _aware(f.forecast_issued_at)
        and _aware(f.forecast_for) <= _aware(f.forecast_issued_at)
    ]
    consistency.checks.append(
        CheckResult("forecasts_forward_looking", not backward,
                    f"{len(backward)} backward forecasts", len(forecasts))
    )
    src.categories.append(consistency)

    return src


# ---------------------------------------------------------------------------
# BOM checks
# ---------------------------------------------------------------------------


def _verify_bom(session) -> SourceResult:
    from citylab.models.weather import WeatherForecast

    fc_count = session.query(func.count(WeatherForecast.id)).scalar()
    has_data = bool(fc_count)
    src = SourceResult(source="bom", has_data=has_data)
    if not has_data:
        return src

    forecasts = session.query(WeatherForecast).all()

    # --- Completeness: temperature + wind populated ---
    completeness = CategoryResult(name="completeness")
    missing = []
    for f in forecasts:
        has_temp = (
            f.temperature_c is not None
            or (f.temperature_min_c is not None and f.temperature_max_c is not None)
        )
        if not has_temp or f.wind_speed_kmh is None:
            missing.append(f)
    completeness.checks.append(
        CheckResult("temperature_and_wind_present", not missing,
                    f"{len(missing)} forecasts missing temp/wind", len(forecasts))
    )
    src.categories.append(completeness)

    # --- Freshness ---
    freshness = CategoryResult(name="freshness")
    latest_issue = _aware(
        session.query(func.max(WeatherForecast.issued_at)).scalar()
    )
    now = datetime.now(timezone.utc)
    tol = FRESHNESS_TOLERANCE_SECONDS["bom"]
    fresh_ok = latest_issue is not None and (now - latest_issue).total_seconds() <= tol
    freshness.checks.append(
        CheckResult("forecast_recent", fresh_ok,
                    f"latest_issue={latest_issue.isoformat() if latest_issue else None}", 0)
    )
    src.categories.append(freshness)

    # --- Consistency: both short-range and daily periods present ---
    consistency = CategoryResult(name="consistency")
    periods = {f.forecast_period for f in forecasts}
    has_both = "3hourly" in periods and "daily" in periods
    consistency.checks.append(
        CheckResult("period_coverage", has_both,
                    f"periods={sorted(periods)}", len(periods))
    )
    src.categories.append(consistency)

    return src


# ---------------------------------------------------------------------------
# Solcast checks
# ---------------------------------------------------------------------------


def _verify_solcast(session) -> SourceResult:
    from citylab.models.solar import SolarForecast

    fc_count = session.query(func.count(SolarForecast.id)).scalar()
    has_data = bool(fc_count)
    src = SourceResult(source="solcast", has_data=has_data)
    if not has_data:
        return src

    forecasts = session.query(SolarForecast).all()

    # --- Completeness: GHI populated ---
    completeness = CategoryResult(name="completeness")
    missing_ghi = [f for f in forecasts if f.ghi_wm2 is None]
    completeness.checks.append(
        CheckResult("ghi_present", not missing_ghi,
                    f"{len(missing_ghi)} rows missing GHI", len(forecasts))
    )
    # GHI must be non-negative.
    negative = [f for f in forecasts if f.ghi_wm2 is not None and f.ghi_wm2 < 0]
    completeness.checks.append(
        CheckResult("ghi_non_negative", not negative,
                    f"{len(negative)} negative GHI rows", len(forecasts))
    )
    src.categories.append(completeness)

    # --- Freshness ---
    freshness = CategoryResult(name="freshness")
    latest_issue = _aware(
        session.query(func.max(SolarForecast.issued_at)).scalar()
    )
    now = datetime.now(timezone.utc)
    tol = FRESHNESS_TOLERANCE_SECONDS["solcast"]
    fresh_ok = latest_issue is not None and (now - latest_issue).total_seconds() <= tol
    freshness.checks.append(
        CheckResult("forecast_recent", fresh_ok,
                    f"latest_issue={latest_issue.isoformat() if latest_issue else None}", 0)
    )
    src.categories.append(freshness)

    # --- Consistency: intraday + short-range periods present; daytime GHI > 0 ---
    consistency = CategoryResult(name="consistency")
    periods = {f.forecast_period for f in forecasts}
    has_both = "30min" in periods and "hourly" in periods
    consistency.checks.append(
        CheckResult("period_coverage", has_both,
                    f"periods={sorted(periods)}", len(periods))
    )
    any_daytime = any(f.ghi_wm2 and f.ghi_wm2 > 0 for f in forecasts)
    consistency.checks.append(
        CheckResult("daytime_ghi_present", any_daytime,
                    "no positive-GHI rows" if not any_daytime else "ok", 0)
    )
    src.categories.append(consistency)

    return src


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def verify(session=None, region: str = "VIC1") -> VerifyReport:
    """Run all checks for all three sources and return a VerifyReport.

    session defaults to the Flask-SQLAlchemy db.session (requires app context).
    """
    if session is None:
        session = db.session
    report = VerifyReport()
    report.sources.append(_verify_opennem(session, region=region))
    report.sources.append(_verify_bom(session))
    report.sources.append(_verify_solcast(session))
    return report
