"""Carbon intensity derivation.

Pure derivation module — no new database tables. Estimates grid carbon intensity
from the generation mix already ingested in ``GenerationOutput``, mirroring the
inertia proxy pattern (see ``inertia.py``).

Each fuel type maps to a known emission factor (tCO₂ per MWh of generation).
Multiplying each generator's output by its factor and dividing by total
generation yields a generation-weighted average intensity for the interval:

    carbon_intensity (tCO₂/MWh) = Σ (output_mw × EF) / Σ output_mw

**Battery charging is load, not generation.** It is excluded from both the
numerator and the denominator — counting it as zero-EF "generation" would
artificially dilute the intensity figure. The same exclusion applies to the
renewables-percentage denominator.
"""

from datetime import datetime

from sqlalchemy import func

from citylab.extensions import db
from citylab.models.energy import GenerationOutput

DEFAULT_REGION = "VIC1"

# --- Emission factors ------------------------------------------------------
#
# fuel_type -> EF (tCO₂ per MWh generated). Zero-carbon and inverter-coupled
# sources are 0. Unknown fuels default to 0 via EMISSION_FACTORS.get(fuel, 0.0).
EMISSION_FACTORS: dict[str, float] = {
    "brown_coal": 1.25,
    "black_coal": 0.90,
    "gas_ccgt": 0.55,
    "gas_ocgt": 0.55,
    "gas_recip": 0.55,
    "gas_steam": 0.55,
    "distillate": 0.95,
    "hydro": 0.0,
    "wind": 0.0,
    "solar_utility": 0.0,
    "solar_rooftop": 0.0,
    "battery_discharging": 0.0,
    "battery_charging": 0.0,
    "biomass": 0.0,
}

# Renewable generation buckets. Battery discharge is storage, not generation
# (it may have been charged from coal), so it is NOT counted as renewable.
RENEWABLE_FUELS = {"hydro", "wind", "solar_utility", "solar_rooftop", "biomass"}

# Intensity bands (tCO₂/MWh).
#   Very Low  < 0.2   mostly renewables
#   Low       0.2–0.4 high renewables + some gas
#   Moderate  0.4–0.7 mixed fossil/renewable
#   High      0.7–1.0 coal-dominated
#   Very High > 1.0   heavy brown coal
BAND_VERY_LOW = 0.2
BAND_LOW = 0.4
BAND_MODERATE = 0.7
BAND_HIGH = 1.0


def intensity_band(carbon_intensity: float) -> str:
    """Classify a carbon intensity (tCO₂/MWh) into a named band."""
    if carbon_intensity < BAND_VERY_LOW:
        return "Very Low"
    if carbon_intensity < BAND_LOW:
        return "Low"
    if carbon_intensity < BAND_MODERATE:
        return "Moderate"
    if carbon_intensity <= BAND_HIGH:
        return "High"
    return "Very High"


def compute_carbon(generation_rows) -> dict:
    """Derive carbon metrics from a generation mix.

    ``generation_rows`` is a list of ``{"fuel_type", "output_mw"}`` dicts — the
    same shape ``current_snapshot()`` returns in ``generation_mix``. Only
    positive generation counts; ``battery_charging`` is excluded from both the
    numerator and the denominator because it is load, not generation.

    Returns ``{carbon_intensity_tco2_mwh, renewables_pct, fossil_pct,
    fuel_breakdown, intensity_band}`` where ``fuel_breakdown`` is a list of
    ``{fuel, mw, pct}`` ordered by output descending.
    """
    total_mw = 0.0
    emissions = 0.0  # Σ (output_mw × EF), tCO₂/MWh · MW
    renewable_mw = 0.0
    fossil_mw = 0.0
    by_fuel: dict[str, float] = {}

    for row in generation_rows:
        fuel = row.get("fuel_type")
        mw = row.get("output_mw")
        if fuel == "battery_charging":
            continue  # load, not generation — excluded from num AND denom
        if mw is None or mw <= 0:
            continue  # charging / offline — not generation
        total_mw += mw
        ef = EMISSION_FACTORS.get(fuel, 0.0)
        emissions += mw * ef
        by_fuel[fuel] = by_fuel.get(fuel, 0.0) + mw
        if ef > 0:
            fossil_mw += mw
        if fuel in RENEWABLE_FUELS:
            renewable_mw += mw

    carbon_intensity = emissions / total_mw if total_mw > 0 else 0.0
    renewables_pct = (renewable_mw / total_mw * 100) if total_mw > 0 else 0.0
    fossil_pct = (fossil_mw / total_mw * 100) if total_mw > 0 else 0.0

    fuel_breakdown = [
        {
            "fuel": fuel,
            "mw": round(mw, 1),
            "pct": round(mw / total_mw * 100, 1) if total_mw > 0 else 0.0,
        }
        for fuel, mw in sorted(by_fuel.items(), key=lambda kv: kv[1], reverse=True)
    ]

    return {
        "carbon_intensity_tco2_mwh": round(carbon_intensity, 4),
        "renewables_pct": round(renewables_pct, 1),
        "fossil_pct": round(fossil_pct, 1),
        "fuel_breakdown": fuel_breakdown,
        "intensity_band": intensity_band(carbon_intensity),
    }


def _trunc_expr(column, interval: str):
    """date_trunc bucketing expression for an interval ('1h'/'1d')."""
    unit = "hour" if interval == "1h" else "day"
    return func.date_trunc(unit, column)


def carbon_timeseries(region, dt_from, dt_to, interval: str = "1h") -> list[dict]:
    """Carbon metrics per interval over a window.

    Queries ``GenerationOutput``, groups by interval, and runs ``compute_carbon``
    per bucket. Returns ``[{timestamp, carbon_intensity_tco2_mwh, renewables_pct,
    fossil_pct, intensity_band, total_mw}]`` ordered ascending.
    """
    if interval == "5min":
        time_expr = GenerationOutput.interval_start
    else:
        time_expr = _trunc_expr(GenerationOutput.interval_start, interval)

    rows = (
        db.session.query(
            time_expr.label("b"),
            GenerationOutput.fuel_type,
            func.avg(GenerationOutput.output_mw),
        )
        .filter(
            GenerationOutput.region == region,
            GenerationOutput.interval_start >= dt_from,
            GenerationOutput.interval_start <= dt_to,
        )
        .group_by("b", GenerationOutput.fuel_type)
        .order_by("b")
        .all()
    )

    # bucket timestamp -> list of generation rows
    by_ts: dict[str, list[dict]] = {}
    order: list[str] = []
    for ts, fuel_type, val in rows:
        if val is None:
            continue
        ts_iso = ts.isoformat()
        if ts_iso not in by_ts:
            by_ts[ts_iso] = []
            order.append(ts_iso)
        by_ts[ts_iso].append({"fuel_type": fuel_type, "output_mw": float(val)})

    order.sort()
    series = []
    for ts_iso in order:
        m = compute_carbon(by_ts[ts_iso])
        total_mw = sum(f["mw"] for f in m["fuel_breakdown"])
        series.append(
            {
                "timestamp": ts_iso,
                "carbon_intensity_tco2_mwh": m["carbon_intensity_tco2_mwh"],
                "renewables_pct": m["renewables_pct"],
                "fossil_pct": m["fossil_pct"],
                "intensity_band": m["intensity_band"],
                "total_mw": round(total_mw, 1),
            }
        )
    return series


def current_carbon(region: str = DEFAULT_REGION) -> dict:
    """Latest-interval carbon snapshot for a region.

    Returns the ``compute_carbon`` dict plus ``region`` and ``as_of``. Empty
    (zeroed) snapshot if no generation data exists.
    """
    latest_interval = (
        db.session.query(func.max(GenerationOutput.interval_start))
        .filter(GenerationOutput.region == region)
        .scalar()
    )
    if not latest_interval:
        snapshot = compute_carbon([])
        snapshot["region"] = region
        snapshot["as_of"] = None
        return snapshot

    gen_rows = (
        db.session.query(GenerationOutput.fuel_type, GenerationOutput.output_mw)
        .filter(
            GenerationOutput.region == region,
            GenerationOutput.interval_start == latest_interval,
        )
        .all()
    )
    generation_rows = [{"fuel_type": ft, "output_mw": mw} for ft, mw in gen_rows]
    snapshot = compute_carbon(generation_rows)
    snapshot["region"] = region
    snapshot["as_of"] = (
        latest_interval.isoformat()
        if isinstance(latest_interval, datetime)
        else str(latest_interval)
    )
    return snapshot
