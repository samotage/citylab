"""Energy market data API — prices, generation, interconnectors, forecasts, summary."""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from citylab.routes.api_v1.auth import require_api_token
from citylab.services import energy_query as eq

energy_api_bp = Blueprint("energy_api", __name__)


def _range_args():
    region = request.args.get("region", "VIC1")
    dt_from = eq._parse_dt(request.args.get("from"))
    dt_to = eq._parse_dt(request.args.get("to"))
    return region, dt_from, dt_to


def _timeseries_window():
    """Resolve (region, range_key, interval, dt_from, dt_to) for chart endpoints.

    Validates ``range`` (default 24h) and ``interval`` (auto-selected/validated
    per range, FR5/NFR2).
    """
    region = request.args.get("region", "VIC1")
    range_key = request.args.get("range", "24h")
    if range_key not in eq.RANGE_HOURS:
        range_key = "24h"
    interval = eq.resolve_interval(range_key, request.args.get("interval"))
    dt_to = datetime.now(timezone.utc)
    dt_from = dt_to - timedelta(hours=eq.RANGE_HOURS[range_key])
    return region, range_key, interval, dt_from, dt_to


@energy_api_bp.route("/energy/timeseries/price", methods=["GET"])
@require_api_token
def timeseries_price():
    region, range_key, interval, dt_from, dt_to = _timeseries_window()
    series = eq.price_timeseries(region, dt_from, dt_to, interval)
    return jsonify(
        {
            "ok": True,
            "region": region,
            "range": range_key,
            "interval": interval,
            "series": series,
            "data_as_of": eq.latest_fetch_timestamp("opennem"),
        }
    )


@energy_api_bp.route("/energy/timeseries/demand", methods=["GET"])
@require_api_token
def timeseries_demand():
    region, range_key, interval, dt_from, dt_to = _timeseries_window()
    series = eq.demand_timeseries(region, dt_from, dt_to, interval)
    return jsonify(
        {
            "ok": True,
            "region": region,
            "range": range_key,
            "interval": interval,
            "series": series,
            "data_as_of": eq.latest_fetch_timestamp("opennem"),
        }
    )


@energy_api_bp.route("/energy/timeseries/generation", methods=["GET"])
@require_api_token
def timeseries_generation():
    region, range_key, interval, dt_from, dt_to = _timeseries_window()
    series = eq.generation_timeseries(region, dt_from, dt_to, interval)
    return jsonify(
        {
            "ok": True,
            "region": region,
            "range": range_key,
            "interval": interval,
            "series": series,
            "data_as_of": eq.latest_fetch_timestamp("opennem"),
        }
    )


@energy_api_bp.route("/energy/prices", methods=["GET"])
@require_api_token
def prices():
    region, dt_from, dt_to = _range_args()
    return jsonify(
        {
            "ok": True,
            "data": eq.query_prices(region, dt_from, dt_to),
            "data_as_of": eq.latest_fetch_timestamp(),
        }
    )


@energy_api_bp.route("/energy/generation", methods=["GET"])
@require_api_token
def generation():
    region, dt_from, dt_to = _range_args()
    return jsonify(
        {
            "ok": True,
            "data": eq.query_generation(region, dt_from, dt_to),
            "data_as_of": eq.latest_fetch_timestamp(),
        }
    )


@energy_api_bp.route("/energy/interconnectors", methods=["GET"])
@require_api_token
def interconnectors():
    _, dt_from, dt_to = _range_args()
    return jsonify(
        {
            "ok": True,
            "data": eq.query_interconnectors(dt_from, dt_to),
            "data_as_of": eq.latest_fetch_timestamp(),
        }
    )


@energy_api_bp.route("/energy/forecasts", methods=["GET"])
@require_api_token
def forecasts():
    region = request.args.get("region", "VIC1")
    return jsonify(
        {
            "ok": True,
            "data": eq.query_forecasts(region),
            "data_as_of": eq.latest_fetch_timestamp(),
        }
    )


@energy_api_bp.route("/energy/inertia", methods=["GET"])
@require_api_token
def inertia_timeseries():
    from citylab.services import inertia as inertia_svc

    region, range_key, interval, dt_from, dt_to = _timeseries_window()
    contingency = request.args.get("contingency", "heywood")
    series = inertia_svc.inertia_timeseries(
        region, dt_from, dt_to, interval, contingency
    )
    label, mw = inertia_svc.resolve_contingency(contingency)
    return jsonify(
        {
            "ok": True,
            "region": region,
            "range": range_key,
            "interval": interval,
            "contingency_label": label,
            "contingency_mw": mw,
            "caveat": inertia_svc.MVA_CAVEAT,
            "series": series,
            "data_as_of": eq.latest_fetch_timestamp("opennem"),
        }
    )


@energy_api_bp.route("/energy/inertia/current", methods=["GET"])
@require_api_token
def inertia_current():
    from citylab.services import inertia as inertia_svc

    region = request.args.get("region", "VIC1")
    contingency = request.args.get("contingency", "heywood")
    return jsonify(
        {
            "ok": True,
            "region": region,
            "caveat": inertia_svc.MVA_CAVEAT,
            "data": inertia_svc.current_inertia(region, contingency),
            "data_as_of": eq.latest_fetch_timestamp("opennem"),
        }
    )


@energy_api_bp.route("/energy/summary", methods=["GET"])
@require_api_token
def summary():
    region = request.args.get("region", "VIC1")
    return jsonify(
        {
            "ok": True,
            "data": eq.current_snapshot(region),
            "data_as_of": eq.latest_fetch_timestamp(),
        }
    )


@energy_api_bp.route("/energy/scenario", methods=["POST"])
@require_api_token
def scenario():
    from citylab.services.scenario import ScenarioEngine

    body = request.get_json(silent=True) or {}
    engine = ScenarioEngine()
    result = engine.run(body)
    status = 200 if result.get("ok") else 400
    return jsonify(result), status
