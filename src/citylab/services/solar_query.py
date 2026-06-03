"""Read-side query helpers for Solcast solar forecast data.

Shared by the solar API blueprint and the CLI. Mirrors weather_query: keeps the
"current irradiance + outlook" logic in one place. Reuses
energy_query.latest_fetch_timestamp() for the data_as_of freshness contract.

Locations can be addressed by name (case-insensitive substring), numeric id,
region_relevance ("utility_solar", "rooftop_aggregate", "hybrid_zone"), or state
("VIC", "SA").
"""

from datetime import datetime, timezone

from sqlalchemy import func

from citylab.extensions import db
from citylab.models.solar import SolarForecast, SolarLocation
from citylab.services.energy_query import _parse_dt, latest_fetch_timestamp  # noqa: F401

# Human grouping labels for summary output.
_GROUP_LABELS = {
    "utility_solar": "utility_solar_regions",
    "rooftop_aggregate": "rooftop_aggregates",
    "hybrid_zone": "hybrid_zones",
}

_STATES = {"VIC", "SA", "NSW", "TAS", "QLD"}


def _resolve_locations(selector: str | None):
    """Return a list of SolarLocation rows matching a selector.

    None/empty -> all locations. Otherwise tries id, then region_relevance,
    then state, then case-insensitive name substring.
    """
    q = db.session.query(SolarLocation)
    if not selector:
        return q.order_by(SolarLocation.id).all()

    sel = str(selector).strip()

    if sel.isdigit():
        loc = db.session.get(SolarLocation, int(sel))
        return [loc] if loc else []

    low = sel.lower()
    if low in _GROUP_LABELS:
        return (
            q.filter(SolarLocation.region_relevance == low)
            .order_by(SolarLocation.id)
            .all()
        )
    if len(sel) <= 4 and sel.upper() in _STATES:
        return (
            q.filter(SolarLocation.state == sel.upper())
            .order_by(SolarLocation.id)
            .all()
        )
    return (
        q.filter(SolarLocation.name.ilike(f"%{sel}%"))
        .order_by(SolarLocation.id)
        .all()
    )


def _latest_issue_for(location_id: int):
    """Most recent issued_at for a location's forecasts."""
    return (
        db.session.query(func.max(SolarForecast.issued_at))
        .filter(SolarForecast.location_id == location_id)
        .scalar()
    )


def query_forecasts(location=None, dt_from=None, dt_to=None, limit: int = 1000):
    """Forecasts for the resolved location(s), latest issue only, in time order."""
    locations = _resolve_locations(location)
    out = []
    for loc in locations:
        latest_issue = _latest_issue_for(loc.id)
        q = db.session.query(SolarForecast).filter(
            SolarForecast.location_id == loc.id
        )
        if latest_issue is not None:
            q = q.filter(SolarForecast.issued_at == latest_issue)
        if dt_from:
            q = q.filter(SolarForecast.forecast_for >= dt_from)
        if dt_to:
            q = q.filter(SolarForecast.forecast_for <= dt_to)
        q = q.order_by(SolarForecast.forecast_for.asc()).limit(limit)
        rows = [r.to_dict() for r in q.all()]
        out.append({"location": loc.to_dict(), "forecasts": rows})
    return out


def _impact_headline(peak_ghi, avg_cloud) -> str:
    """A short, agent-readable generation-impact statement for a group."""
    if peak_ghi is None:
        return "no solar forecast data"
    if peak_ghi >= 800 and (avg_cloud is None or avg_cloud < 30):
        return "strong solar output expected — suppresses midday demand/price"
    if peak_ghi >= 500:
        return "moderate solar output — partial midday demand suppression"
    return "weak solar output — limited demand suppression, price support"


def summary() -> dict:
    """Current GHI + next-24h solar outlook grouped by region_relevance."""
    locations = (
        db.session.query(SolarLocation).order_by(SolarLocation.id).all()
    )
    now = datetime.now(timezone.utc)
    horizon = now.timestamp() + 24 * 3600

    groups: dict[str, dict] = {}
    for loc in locations:
        label = _GROUP_LABELS.get(loc.region_relevance, loc.region_relevance)
        latest_issue = _latest_issue_for(loc.id)

        base_q = db.session.query(SolarForecast).filter(
            SolarForecast.location_id == loc.id
        )
        if latest_issue is not None:
            base_q = base_q.filter(SolarForecast.issued_at == latest_issue)

        # Current: forecast at/after now (nearest).
        current = (
            base_q.filter(SolarForecast.forecast_for >= now)
            .order_by(SolarForecast.forecast_for.asc())
            .first()
        )

        # Next-24h window for peak GHI / avg cloud.
        next24 = [
            r
            for r in base_q.filter(SolarForecast.forecast_for >= now)
            .order_by(SolarForecast.forecast_for.asc())
            .all()
            if r.forecast_for and r.forecast_for.timestamp() <= horizon
        ]
        ghis = [r.ghi_wm2 for r in next24 if r.ghi_wm2 is not None]
        clouds = [
            r.cloud_opacity_pct for r in next24 if r.cloud_opacity_pct is not None
        ]
        pvs = [
            r.estimated_pv_output_kw
            for r in next24
            if r.estimated_pv_output_kw is not None
        ]
        peak_ghi = round(max(ghis), 1) if ghis else None
        avg_cloud = round(sum(clouds) / len(clouds), 0) if clouds else None
        peak_pv = round(max(pvs), 1) if pvs else None

        grp = groups.setdefault(label, {"locations": [], "_peaks": []})
        grp["locations"].append(
            {
                "location": loc.to_dict(),
                "current": current.to_dict() if current else None,
                "next_24h": {
                    "peak_ghi_wm2": peak_ghi,
                    "avg_cloud_opacity_pct": avg_cloud,
                    "peak_estimated_pv_output_kw": peak_pv,
                },
            }
        )
        if peak_ghi is not None:
            grp["_peaks"].append((peak_ghi, avg_cloud))

    # Compute a per-group generation-impact headline.
    out_groups = {}
    for label, grp in groups.items():
        peaks = grp.pop("_peaks")
        group_peak = max((p[0] for p in peaks), default=None)
        clouds = [p[1] for p in peaks if p[1] is not None]
        group_cloud = round(sum(clouds) / len(clouds), 0) if clouds else None
        grp["generation_impact"] = _impact_headline(group_peak, group_cloud)
        grp["group_peak_ghi_wm2"] = group_peak
        grp["group_avg_cloud_opacity_pct"] = group_cloud
        out_groups[label] = grp

    return {"groups": out_groups}


def outlook(days: int = 3) -> dict:
    """Multi-day, narrative-friendly solar outlook per location.

    For each location, over the next `days` (from the latest issue), surface the
    peak GHI and average cloud opacity per day so an agent can say "strong solar
    across NW Vic next 3 days, cloud band day 4".
    """
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() + days * 86400

    locations = (
        db.session.query(SolarLocation).order_by(SolarLocation.id).all()
    )

    results = []
    for loc in locations:
        latest_issue = _latest_issue_for(loc.id)
        q = db.session.query(SolarForecast).filter(
            SolarForecast.location_id == loc.id,
            SolarForecast.forecast_for >= now,
        )
        if latest_issue is not None:
            q = q.filter(SolarForecast.issued_at == latest_issue)
        rows = [
            r
            for r in q.order_by(SolarForecast.forecast_for.asc()).all()
            if r.forecast_for and r.forecast_for.timestamp() <= cutoff
        ]

        # Bucket by calendar date.
        by_day: dict[str, list] = {}
        for r in rows:
            key = r.forecast_for.date().isoformat()
            by_day.setdefault(key, []).append(r)

        daily = []
        for day in sorted(by_day):
            day_rows = by_day[day]
            ghis = [r.ghi_wm2 for r in day_rows if r.ghi_wm2 is not None]
            clouds = [
                r.cloud_opacity_pct
                for r in day_rows
                if r.cloud_opacity_pct is not None
            ]
            pvs = [
                r.estimated_pv_output_kw
                for r in day_rows
                if r.estimated_pv_output_kw is not None
            ]
            peak_ghi = round(max(ghis), 1) if ghis else None
            avg_cloud = round(sum(clouds) / len(clouds), 0) if clouds else None
            daily.append(
                {
                    "date": day,
                    "peak_ghi_wm2": peak_ghi,
                    "avg_cloud_opacity_pct": avg_cloud,
                    "peak_estimated_pv_output_kw": round(max(pvs), 1)
                    if pvs
                    else None,
                    "assessment": _impact_headline(peak_ghi, avg_cloud),
                }
            )

        results.append({"location": loc.to_dict(), "daily": daily})

    return {"days": days, "locations": results}
