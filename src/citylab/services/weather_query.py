"""Read-side query helpers for BOM weather data.

Shared by the weather API blueprint and the CLI. Mirrors energy_query: keeps the
"current conditions + outlook" logic in one place. Reuses
energy_query.latest_fetch_timestamp() for the data_as_of freshness contract.

Locations can be addressed by name (case-insensitive substring), numeric id,
region_relevance ("wind_corridor", "hydro_catchment", "demand_centre",
"solar_region"), or state ("VIC", "TAS", "SA", "NSW").
"""

from datetime import datetime, timezone

from sqlalchemy import func

from citylab.extensions import db
from citylab.models.weather import (
    WeatherForecast,
    WeatherLocation,
    WeatherObservation,
)
from citylab.services.energy_query import _parse_dt, latest_fetch_timestamp  # noqa: F401

# Maps an outlook factor to the relevance groups it draws from + the
# forecast fields that matter for it.
_FACTOR_GROUPS = {
    "wind": ["wind_corridor", "demand_centre"],
    "rain": ["hydro_catchment", "demand_centre"],
    "temperature": ["demand_centre", "wind_corridor", "hydro_catchment", "solar_region"],
}

# Human grouping labels for summary output.
_GROUP_LABELS = {
    "demand_centre": "demand_centres",
    "wind_corridor": "wind_corridors",
    "hydro_catchment": "hydro_catchments",
    "solar_region": "solar_regions",
}


def _resolve_locations(selector: str | None):
    """Return a list of WeatherLocation rows matching a selector.

    None/empty -> all locations. Otherwise tries id, then region_relevance,
    then state, then case-insensitive name substring.
    """
    q = db.session.query(WeatherLocation)
    if not selector:
        return q.order_by(WeatherLocation.id).all()

    sel = str(selector).strip()

    # numeric id
    if sel.isdigit():
        loc = db.session.get(WeatherLocation, int(sel))
        return [loc] if loc else []

    low = sel.lower()
    # region_relevance exact
    if low in _GROUP_LABELS:
        return (
            q.filter(WeatherLocation.region_relevance == low)
            .order_by(WeatherLocation.id)
            .all()
        )
    # state exact (e.g. VIC, TAS)
    if len(sel) <= 4 and sel.upper() in {"VIC", "TAS", "SA", "NSW"}:
        return (
            q.filter(WeatherLocation.state == sel.upper())
            .order_by(WeatherLocation.id)
            .all()
        )
    # name substring
    return (
        q.filter(WeatherLocation.name.ilike(f"%{sel}%"))
        .order_by(WeatherLocation.id)
        .all()
    )


def _latest_issue_for(location_id: int):
    """Most recent issued_at for a location's forecasts."""
    return (
        db.session.query(func.max(WeatherForecast.issued_at))
        .filter(WeatherForecast.location_id == location_id)
        .scalar()
    )


def query_forecasts(location=None, dt_from=None, dt_to=None, limit: int = 1000):
    """Forecasts for the resolved location(s), latest issue only, in time order."""
    locations = _resolve_locations(location)
    out = []
    for loc in locations:
        latest_issue = _latest_issue_for(loc.id)
        q = db.session.query(WeatherForecast).filter(
            WeatherForecast.location_id == loc.id
        )
        if latest_issue is not None:
            q = q.filter(WeatherForecast.issued_at == latest_issue)
        if dt_from:
            q = q.filter(WeatherForecast.forecast_for >= dt_from)
        if dt_to:
            q = q.filter(WeatherForecast.forecast_for <= dt_to)
        q = q.order_by(WeatherForecast.forecast_for.asc()).limit(limit)
        rows = [r.to_dict() for r in q.all()]
        out.append({"location": loc.to_dict(), "forecasts": rows})
    return out


def query_observations(location=None):
    """Latest observation per resolved location."""
    locations = _resolve_locations(location)
    out = []
    for loc in locations:
        latest = (
            db.session.query(WeatherObservation)
            .filter(WeatherObservation.location_id == loc.id)
            .order_by(WeatherObservation.observed_at.desc())
            .first()
        )
        out.append(
            {
                "location": loc.to_dict(),
                "observation": latest.to_dict() if latest else None,
            }
        )
    return out


def summary() -> dict:
    """Current conditions + near-term outlook grouped by region_relevance."""
    locations = (
        db.session.query(WeatherLocation).order_by(WeatherLocation.id).all()
    )
    groups: dict[str, list] = {}
    for loc in locations:
        label = _GROUP_LABELS.get(loc.region_relevance, loc.region_relevance)

        latest_obs = (
            db.session.query(WeatherObservation)
            .filter(WeatherObservation.location_id == loc.id)
            .order_by(WeatherObservation.observed_at.desc())
            .first()
        )

        # Near-term forecast: next forecast at/after now from the latest issue.
        now = datetime.now(timezone.utc)
        latest_issue = _latest_issue_for(loc.id)
        next_fc_q = db.session.query(WeatherForecast).filter(
            WeatherForecast.location_id == loc.id,
            WeatherForecast.forecast_for >= now,
        )
        if latest_issue is not None:
            next_fc_q = next_fc_q.filter(
                WeatherForecast.issued_at == latest_issue
            )
        next_fc = next_fc_q.order_by(WeatherForecast.forecast_for.asc()).first()

        groups.setdefault(label, []).append(
            {
                "location": loc.to_dict(),
                "current": latest_obs.to_dict() if latest_obs else None,
                "next_forecast": next_fc.to_dict() if next_fc else None,
            }
        )

    return {"groups": groups}


def outlook(factor: str, days: int = 3) -> dict:
    """Filtered multi-day outlook for one factor across relevant locations.

    factor in {wind, rain, temperature}. Returns each relevant location with its
    forecast series (latest issue) trimmed to `days` and the factor-relevant
    fields surfaced, plus a peak/total headline per location.
    """
    factor = (factor or "").lower()
    groups = _FACTOR_GROUPS.get(factor)
    if groups is None:
        return {"factor": factor, "error": "unknown factor", "locations": []}

    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() + days * 86400

    locations = (
        db.session.query(WeatherLocation)
        .filter(WeatherLocation.region_relevance.in_(groups))
        .order_by(WeatherLocation.id)
        .all()
    )

    results = []
    for loc in locations:
        latest_issue = _latest_issue_for(loc.id)
        q = db.session.query(WeatherForecast).filter(
            WeatherForecast.location_id == loc.id,
            WeatherForecast.forecast_for >= now,
        )
        if latest_issue is not None:
            q = q.filter(WeatherForecast.issued_at == latest_issue)
        q = q.order_by(WeatherForecast.forecast_for.asc())
        rows = [
            r
            for r in q.all()
            if r.forecast_for and r.forecast_for.timestamp() <= cutoff
        ]

        series = []
        headline = {}
        if factor == "wind":
            speeds = [r.wind_speed_kmh for r in rows if r.wind_speed_kmh is not None]
            gusts = [r.wind_gust_kmh for r in rows if r.wind_gust_kmh is not None]
            headline = {
                "peak_wind_kmh": round(max(speeds), 1) if speeds else None,
                "peak_gust_kmh": round(max(gusts), 1) if gusts else None,
                "avg_wind_kmh": round(sum(speeds) / len(speeds), 1) if speeds else None,
            }
            series = [
                {
                    "forecast_for": r.forecast_for.isoformat(),
                    "wind_speed_kmh": r.wind_speed_kmh,
                    "wind_gust_kmh": r.wind_gust_kmh,
                    "wind_direction": r.wind_direction,
                }
                for r in rows
            ]
        elif factor == "rain":
            totals = [r.rainfall_mm for r in rows if r.rainfall_mm is not None]
            probs = [
                r.rainfall_probability_pct
                for r in rows
                if r.rainfall_probability_pct is not None
            ]
            headline = {
                "total_rainfall_mm": round(sum(totals), 1) if totals else None,
                "peak_probability_pct": round(max(probs), 0) if probs else None,
            }
            series = [
                {
                    "forecast_for": r.forecast_for.isoformat(),
                    "rainfall_mm": r.rainfall_mm,
                    "rainfall_probability_pct": r.rainfall_probability_pct,
                }
                for r in rows
            ]
        else:  # temperature
            temps = [
                r.temperature_c
                for r in rows
                if r.temperature_c is not None
            ]
            maxes = [
                r.temperature_max_c
                for r in rows
                if r.temperature_max_c is not None
            ]
            mins = [
                r.temperature_min_c
                for r in rows
                if r.temperature_min_c is not None
            ]
            pool = temps + maxes
            headline = {
                "max_temp_c": round(max(pool), 1) if pool else None,
                "min_temp_c": round(min(temps + mins), 1) if (temps or mins) else None,
            }
            series = [
                {
                    "forecast_for": r.forecast_for.isoformat(),
                    "temperature_c": r.temperature_c,
                    "temperature_min_c": r.temperature_min_c,
                    "temperature_max_c": r.temperature_max_c,
                }
                for r in rows
            ]

        results.append(
            {
                "location": loc.to_dict(),
                "headline": headline,
                "series": series,
            }
        )

    return {"factor": factor, "days": days, "locations": results}
