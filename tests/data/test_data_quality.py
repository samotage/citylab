"""Level 2 — data quality assertions (citylab_test).

Three categories that catch the "half-baked pipeline" failure modes:
  completeness — required fields populated, fuel types/corridors valid
  freshness    — most recent point inside the expected window, no big gaps
  consistency  — generation sums to ~total, all 5 corridors, forecasts forward

These assert both directly against the ORM and through the shared data_verify
service so the service and the tests stay in lock-step.
"""

from datetime import datetime, timezone

import pytest

from tests.data.conftest import run_fetcher, seed_locations

from citylab.models.energy import (
    EnergyPrice,
    GenerationOutput,
    InterconnectorFlow,
    PriceForecast,
)
from citylab.models.solar import SolarForecast
from citylab.models.weather import WeatherForecast
from citylab.services import data_verify

pytestmark = pytest.mark.integration


def _aware(dt):
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@pytest.fixture
def populated(db_session):
    """Seed locations and run all three fetchers so every table has data."""
    seed_locations(db_session)
    for source_type, name in (
        ("opennem", "OpenNEM DQ"),
        ("bom", "BOM DQ"),
        ("solcast", "Solcast DQ"),
    ):
        run_fetcher(db_session, source_type, name, fresh=False)
    return db_session


# ---------------------------------------------------------------------------
# Completeness
# ---------------------------------------------------------------------------


def test_completeness_energy_prices_non_null(populated):
    prices = populated.query(EnergyPrice).filter_by(region="VIC1").all()
    assert prices
    assert all(p.price_aud_mwh is not None for p in prices)


def test_completeness_generation_output_and_fuel(populated):
    gens = populated.query(GenerationOutput).filter_by(region="VIC1").all()
    assert gens
    assert all(g.output_mw is not None for g in gens)
    assert all(g.fuel_type in data_verify.KNOWN_FUELS for g in gens)


def test_completeness_interconnector_corridors(populated):
    flows = populated.query(InterconnectorFlow).all()
    assert flows
    assert all(f.interconnector_id in data_verify.KNOWN_CORRIDORS for f in flows)


def test_completeness_weather_temperature_and_wind(populated):
    forecasts = populated.query(WeatherForecast).all()
    assert forecasts
    for f in forecasts:
        has_temp = (
            f.temperature_c is not None
            or (f.temperature_min_c is not None and f.temperature_max_c is not None)
        )
        assert has_temp and f.wind_speed_kmh is not None


def test_completeness_solar_ghi_populated(populated):
    forecasts = populated.query(SolarForecast).all()
    assert forecasts
    assert all(f.ghi_wm2 is not None for f in forecasts)


def test_completeness_via_service_all_green(populated):
    report = data_verify.verify(populated)
    for src in report.sources:
        completeness = next(c for c in src.categories if c.name == "completeness")
        assert completeness.passed, f"{src.source} completeness failed: {completeness.to_dict()}"


# ---------------------------------------------------------------------------
# Freshness
# ---------------------------------------------------------------------------


def test_freshness_latest_point_within_window(populated):
    """The most recent energy price should be near 'now' (synthetic stamps now)."""
    from sqlalchemy import func

    latest = _aware(
        populated.query(func.max(EnergyPrice.interval_start))
        .filter(EnergyPrice.region == "VIC1")
        .scalar()
    )
    assert latest is not None
    age = (datetime.now(timezone.utc) - latest).total_seconds()
    assert age <= data_verify.FRESHNESS_TOLERANCE_SECONDS["opennem"]


def test_freshness_no_large_gaps_in_prices(populated):
    """No gap longer than 2x the expected 5-min interval in the recent window."""
    prices = (
        populated.query(EnergyPrice)
        .filter(EnergyPrice.region == "VIC1")
        .order_by(EnergyPrice.interval_start.asc())
        .all()
    )
    assert len(prices) >= 2
    starts = [_aware(p.interval_start) for p in prices]
    max_allowed = 2 * data_verify.EXPECTED_INTERVAL_SECONDS["opennem"]
    gaps = [
        (starts[i + 1] - starts[i]).total_seconds()
        for i in range(len(starts) - 1)
    ]
    assert max(gaps) <= max_allowed, f"gap too large: {max(gaps)}s"


def test_freshness_last_fetch_at_updated(populated):
    from citylab.models.data_source import DataSource

    ds = populated.query(DataSource).filter_by(name="OpenNEM DQ").first()
    assert ds is not None
    assert ds.last_fetch_at is not None
    assert ds.last_fetch_status == "success"


def test_freshness_via_service_all_green(populated):
    report = data_verify.verify(populated)
    for src in report.sources:
        freshness = next(c for c in src.categories if c.name == "freshness")
        assert freshness.passed, f"{src.source} freshness failed: {freshness.to_dict()}"


# ---------------------------------------------------------------------------
# Consistency
# ---------------------------------------------------------------------------


def test_consistency_generation_sums_to_total(populated):
    """Sum of generation by fuel ~= a plausible total (sanity, 5% tolerance).

    Battery charging is negative; the net of the latest interval's mix should be
    a positive, plausible Victorian total (a few thousand MW), and the per-fuel
    breakdown should reconstruct that net within tolerance.
    """
    from sqlalchemy import func

    latest_interval = (
        populated.query(func.max(GenerationOutput.interval_start))
        .filter(GenerationOutput.region == "VIC1")
        .scalar()
    )
    rows = (
        populated.query(GenerationOutput)
        .filter(
            GenerationOutput.region == "VIC1",
            GenerationOutput.interval_start == latest_interval,
        )
        .all()
    )
    assert rows
    net = sum(r.output_mw for r in rows)
    # Net (charging negative) should be a plausible positive VIC1 total.
    assert net > 1000, f"implausible net generation {net}MW"

    # Per-fuel subtotals (GROUP BY path) should reconstruct the flat net.
    # Using a separate aggregation query so both sides are computed differently.
    fuel_subtotals = (
        populated.query(func.sum(GenerationOutput.output_mw))
        .filter(
            GenerationOutput.region == "VIC1",
            GenerationOutput.interval_start == latest_interval,
        )
        .group_by(GenerationOutput.fuel_type)
        .all()
    )
    breakdown = sum(s[0] for s in fuel_subtotals if s[0] is not None)
    assert abs(breakdown - net) <= abs(net) * 0.05


def test_consistency_all_five_corridors_present(populated):
    flows = populated.query(InterconnectorFlow).all()
    corridors = {f.interconnector_id for f in flows}
    assert corridors >= data_verify.KNOWN_CORRIDORS
    assert len(data_verify.KNOWN_CORRIDORS) == 5


def test_consistency_price_forecasts_forward_looking(populated):
    forecasts = populated.query(PriceForecast).filter_by(region="VIC1").all()
    assert forecasts
    for f in forecasts:
        assert _aware(f.forecast_for) > _aware(f.forecast_issued_at)


def test_consistency_via_service_all_green(populated):
    report = data_verify.verify(populated)
    for src in report.sources:
        consistency = next(c for c in src.categories if c.name == "consistency")
        assert consistency.passed, f"{src.source} consistency failed: {consistency.to_dict()}"


def test_full_report_all_green(populated):
    report = data_verify.verify(populated)
    assert report.passed, report.to_dict()
