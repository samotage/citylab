"""Read-side query helpers for energy market data.

Shared by the energy API blueprint, the data market-intelligence endpoint, and
the CLI. Keeps the "current snapshot" logic in one place.
"""

from datetime import datetime, timezone

from sqlalchemy import func

from citylab.extensions import db
from citylab.models.energy import (
    EnergyDemand,
    EnergyPrice,
    GenerationOutput,
    InterconnectorFlow,
    PriceForecast,
)

DEFAULT_REGION = "VIC1"


# --- Shared fuel-type palette --------------------------------------------
#
# Single source of truth for generation fuel buckets, in stacking order, with
# brand colours. Both the static generation panel (routes/energy.py) and the
# new stacked-area chart consume this so colours/labels stay identical (FR8,
# SC9).
FUEL_BUCKETS = [
    ("brown_coal", "Brown Coal", "#6366f1"),
    ("black_coal", "Black Coal", "#4338ca"),
    ("gas", "Gas", "#a855f7"),
    ("hydro", "Hydro", "#14b8a6"),
    ("wind", "Wind", "#0ea5e9"),
    ("solar", "Solar", "#eab308"),
    ("battery_discharging", "Battery (discharge)", "#f472b6"),
    ("battery_charging", "Battery (charge)", "#6B21A8"),
    ("biomass", "Biomass", "#65A30D"),
    ("distillate", "Distillate", "#DC2626"),
    ("other", "Other", "#94a3b8"),
]

_GAS_TYPES = {"gas_ccgt", "gas_ocgt", "gas_recip", "gas_steam"}
_SOLAR_TYPES = {"solar_utility", "solar_rooftop"}


def bucket_for(fuel_type: str) -> str:
    """Map a raw fuel_type to its display bucket key (shared with the panel)."""
    if fuel_type in _GAS_TYPES:
        return "gas"
    if fuel_type in _SOLAR_TYPES:
        return "solar"
    if fuel_type in ("brown_coal", "black_coal", "wind", "hydro", "biomass", "distillate"):
        return fuel_type
    if fuel_type in ("battery_charging", "battery_discharging"):
        return fuel_type
    return "other"


# --- Time-series aggregation ----------------------------------------------

# Valid intervals per range + the default to auto-select (FR5, NFR2).
RANGE_HOURS = {
    "1h": 1,
    "6h": 6,
    "24h": 24,
    "7d": 24 * 7,
    "30d": 24 * 30,
}

RANGE_INTERVALS = {
    "1h": (["5min"], "5min"),
    "6h": (["5min", "1h"], "5min"),
    "24h": (["5min", "1h"], "1h"),
    "7d": (["1h", "1d"], "1h"),
    "30d": (["1h", "1d"], "1d"),
}

_MAX_POINTS = 10000


def valid_intervals(range_key: str):
    """Return (allowed_intervals, default_interval) for a range key."""
    return RANGE_INTERVALS.get(range_key, (["5min", "1h"], "1h"))


def resolve_interval(range_key: str, interval: str | None) -> str:
    """Validate the requested interval against the range; fall back to default."""
    allowed, default = valid_intervals(range_key)
    if interval in allowed:
        return interval
    return default


def _trunc_expr(column, interval: str):
    """date_trunc bucketing expression for an interval ('1h'/'1d')."""
    unit = "hour" if interval == "1h" else "day"
    return func.date_trunc(unit, column)


def price_timeseries(region, dt_from, dt_to, interval: str = "5min"):
    """Ordered [{timestamp, value}] of spot price ($/MWh) for a window."""
    if interval == "5min":
        rows = (
            db.session.query(
                EnergyPrice.interval_start, EnergyPrice.price_aud_mwh
            )
            .filter(
                EnergyPrice.region == region,
                EnergyPrice.interval_start >= dt_from,
                EnergyPrice.interval_start <= dt_to,
            )
            .order_by(EnergyPrice.interval_start.asc())
            .limit(_MAX_POINTS)
            .all()
        )
        return [
            {"timestamp": ts.isoformat(), "value": round(v, 2)}
            for ts, v in rows
            if v is not None
        ]

    bucket = _trunc_expr(EnergyPrice.interval_start, interval)
    rows = (
        db.session.query(bucket.label("b"), func.avg(EnergyPrice.price_aud_mwh))
        .filter(
            EnergyPrice.region == region,
            EnergyPrice.interval_start >= dt_from,
            EnergyPrice.interval_start <= dt_to,
        )
        .group_by("b")
        .order_by("b")
        .limit(_MAX_POINTS)
        .all()
    )
    return [
        {"timestamp": ts.isoformat(), "value": round(float(v), 2)}
        for ts, v in rows
        if v is not None
    ]


def demand_timeseries(region, dt_from, dt_to, interval: str = "5min"):
    """Ordered [{timestamp, value}] of demand (MW) for a window."""
    if interval == "5min":
        rows = (
            db.session.query(
                EnergyDemand.interval_start, EnergyDemand.demand_mw
            )
            .filter(
                EnergyDemand.region == region,
                EnergyDemand.interval_start >= dt_from,
                EnergyDemand.interval_start <= dt_to,
            )
            .order_by(EnergyDemand.interval_start.asc())
            .limit(_MAX_POINTS)
            .all()
        )
        return [
            {"timestamp": ts.isoformat(), "value": round(v, 1)}
            for ts, v in rows
            if v is not None
        ]

    bucket = _trunc_expr(EnergyDemand.interval_start, interval)
    rows = (
        db.session.query(bucket.label("b"), func.avg(EnergyDemand.demand_mw))
        .filter(
            EnergyDemand.region == region,
            EnergyDemand.interval_start >= dt_from,
            EnergyDemand.interval_start <= dt_to,
        )
        .group_by("b")
        .order_by("b")
        .limit(_MAX_POINTS)
        .all()
    )
    return [
        {"timestamp": ts.isoformat(), "value": round(float(v), 1)}
        for ts, v in rows
        if v is not None
    ]


def generation_timeseries(region, dt_from, dt_to, interval: str = "5min"):
    """Generation output (MW) by fuel bucket over time.

    Returns one series per fuel bucket present in the window, each:
        {"key", "label", "colour", "points": [{timestamp, value}, ...]}
    Series are ordered by FUEL_BUCKETS (stacking order). Charging is reported
    as positive magnitude. All series share the same ordered timestamp axis so
    the client can stack them directly.
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

    # bucket_key -> { ts_iso -> summed value }
    by_bucket: dict[str, dict[str, float]] = {}
    timestamps: list[str] = []
    seen_ts: set[str] = set()
    for ts, fuel_type, val in rows:
        if val is None:
            continue
        ts_iso = ts.isoformat()
        if ts_iso not in seen_ts:
            seen_ts.add(ts_iso)
            timestamps.append(ts_iso)
        bkey = bucket_for(fuel_type)
        slot = by_bucket.setdefault(bkey, {})
        slot[ts_iso] = slot.get(ts_iso, 0.0) + float(val)

    timestamps.sort()
    # Cap points: if a single series would exceed the limit, truncate the axis.
    if len(timestamps) > _MAX_POINTS:
        timestamps = timestamps[-_MAX_POINTS:]
        ts_set = set(timestamps)

    series = []
    for key, label, colour in FUEL_BUCKETS:
        if key not in by_bucket:
            continue
        slot = by_bucket[key]
        points = [
            {"timestamp": ts, "value": round(abs(slot.get(ts, 0.0)), 1)}
            for ts in timestamps
        ]
        series.append(
            {"key": key, "label": label, "colour": colour, "points": points}
        )
    return series


def _parse_dt(value: str | None):
    """Parse an ISO-ish datetime string; return None on failure/empty."""
    if not value:
        return None
    try:
        # Accept date-only and full ISO
        if len(value) == 10:
            return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def latest_fetch_timestamp(source_type: str | None = None) -> str | None:
    """Most recent successful DataSource fetch, as ISO string (data_as_of).

    With no ``source_type``, returns the max across all sources (cross-source
    freshness). Pass a ``source_type`` (e.g. ``"bom"``, ``"solcast"``) to scope
    the timestamp to a single source so per-source endpoints report their own
    fetch time rather than an unrelated source's.
    """
    from citylab.models.data_source import DataSource

    q = db.session.query(func.max(DataSource.last_fetch_at)).filter(
        DataSource.last_fetch_status == "success"
    )
    if source_type is not None:
        q = q.filter(DataSource.source_type == source_type)
    ts = q.scalar()
    return ts.isoformat() if ts else None


def query_prices(region: str, dt_from=None, dt_to=None, limit: int = 1000):
    q = db.session.query(EnergyPrice).filter(EnergyPrice.region == region)
    if dt_from:
        q = q.filter(EnergyPrice.interval_start >= dt_from)
    if dt_to:
        q = q.filter(EnergyPrice.interval_start <= dt_to)
    q = q.order_by(EnergyPrice.interval_start.desc()).limit(limit)
    return [r.to_dict() for r in q.all()]


def query_generation(region: str, dt_from=None, dt_to=None, limit: int = 5000):
    q = db.session.query(GenerationOutput).filter(GenerationOutput.region == region)
    if dt_from:
        q = q.filter(GenerationOutput.interval_start >= dt_from)
    if dt_to:
        q = q.filter(GenerationOutput.interval_start <= dt_to)
    q = q.order_by(GenerationOutput.interval_start.desc()).limit(limit)
    return [r.to_dict() for r in q.all()]


def query_interconnectors(dt_from=None, dt_to=None, limit: int = 5000):
    q = db.session.query(InterconnectorFlow)
    if dt_from:
        q = q.filter(InterconnectorFlow.interval_start >= dt_from)
    if dt_to:
        q = q.filter(InterconnectorFlow.interval_start <= dt_to)
    q = q.order_by(InterconnectorFlow.interval_start.desc()).limit(limit)
    return [r.to_dict() for r in q.all()]


def query_forecasts(region: str, limit: int = 200):
    q = (
        db.session.query(PriceForecast)
        .filter(PriceForecast.region == region)
        .order_by(PriceForecast.forecast_for.asc())
        .limit(limit)
    )
    return [r.to_dict() for r in q.all()]


def current_snapshot(region: str = DEFAULT_REGION) -> dict:
    """Build the 'what's happening right now' snapshot for a region."""
    now = datetime.now(timezone.utc)

    # Latest price
    latest_price = (
        db.session.query(EnergyPrice)
        .filter(EnergyPrice.region == region)
        .order_by(EnergyPrice.interval_start.desc())
        .first()
    )

    # Latest demand
    latest_demand = (
        db.session.query(EnergyDemand)
        .filter(EnergyDemand.region == region)
        .order_by(EnergyDemand.interval_start.desc())
        .first()
    )

    # Generation mix at the most recent interval
    latest_gen_interval = (
        db.session.query(func.max(GenerationOutput.interval_start))
        .filter(GenerationOutput.region == region)
        .scalar()
    )
    generation_mix = []
    battery = {"charging_mw": 0.0, "discharging_mw": 0.0, "net_mw": 0.0}
    if latest_gen_interval:
        gen_rows = (
            db.session.query(GenerationOutput)
            .filter(
                GenerationOutput.region == region,
                GenerationOutput.interval_start == latest_gen_interval,
            )
            .all()
        )
        for r in gen_rows:
            generation_mix.append(
                {"fuel_type": r.fuel_type, "output_mw": r.output_mw, "capacity_mw": r.capacity_mw}
            )
            if r.fuel_type == "battery_charging":
                battery["charging_mw"] = r.output_mw
            elif r.fuel_type == "battery_discharging":
                battery["discharging_mw"] = r.output_mw
        battery["net_mw"] = round(
            battery["discharging_mw"] + battery["charging_mw"], 1
        )

    # Interconnector flows at the most recent interval
    latest_ic_interval = (
        db.session.query(func.max(InterconnectorFlow.interval_start)).scalar()
    )
    interconnectors = []
    if latest_ic_interval:
        ic_rows = (
            db.session.query(InterconnectorFlow)
            .filter(InterconnectorFlow.interval_start == latest_ic_interval)
            .all()
        )
        interconnectors = [r.to_dict() for r in ic_rows]

    # Nearest upcoming forecast
    next_forecast = (
        db.session.query(PriceForecast)
        .filter(
            PriceForecast.region == region,
            PriceForecast.forecast_for >= now,
        )
        .order_by(PriceForecast.forecast_for.asc())
        .first()
    )

    # Grid inertia proxy, derived from the generation mix already fetched above
    # — zero additional DB queries (inertia.py is a pure derivation module).
    from citylab.services.inertia import compute_inertia

    inertia = compute_inertia(generation_mix)

    return {
        "region": region,
        "latest_price": latest_price.to_dict() if latest_price else None,
        "latest_demand": latest_demand.to_dict() if latest_demand else None,
        "generation_mix": generation_mix,
        "battery_state": battery,
        "interconnectors": interconnectors,
        "nearest_forecast": next_forecast.to_dict() if next_forecast else None,
        "inertia": inertia,
    }
