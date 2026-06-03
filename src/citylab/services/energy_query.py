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

    return {
        "region": region,
        "latest_price": latest_price.to_dict() if latest_price else None,
        "latest_demand": latest_demand.to_dict() if latest_demand else None,
        "generation_mix": generation_mix,
        "battery_state": battery,
        "interconnectors": interconnectors,
        "nearest_forecast": next_forecast.to_dict() if next_forecast else None,
    }
