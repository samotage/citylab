"""Weather data API — forecasts, observations, summary, outlook.

Mirrors the energy API: every endpoint is token-protected and returns the
{ok, data, data_as_of} envelope. data_as_of reuses the shared latest successful
fetch timestamp so agents can judge freshness across sources.
"""

from flask import Blueprint, jsonify, request

from citylab.routes.api_v1.auth import require_api_token
from citylab.services import weather_query as wq

weather_api_bp = Blueprint("weather_api", __name__)


@weather_api_bp.route("/weather/forecasts", methods=["GET"])
@require_api_token
def forecasts():
    location = request.args.get("location")
    dt_from = wq._parse_dt(request.args.get("from"))
    dt_to = wq._parse_dt(request.args.get("to"))
    return jsonify(
        {
            "ok": True,
            "data": wq.query_forecasts(location, dt_from, dt_to),
            "data_as_of": wq.latest_fetch_timestamp("bom"),
        }
    )


@weather_api_bp.route("/weather/observations", methods=["GET"])
@require_api_token
def observations():
    location = request.args.get("location")
    return jsonify(
        {
            "ok": True,
            "data": wq.query_observations(location),
            "data_as_of": wq.latest_fetch_timestamp("bom"),
        }
    )


@weather_api_bp.route("/weather/summary", methods=["GET"])
@require_api_token
def summary():
    return jsonify(
        {
            "ok": True,
            "data": wq.summary(),
            "data_as_of": wq.latest_fetch_timestamp("bom"),
        }
    )


@weather_api_bp.route("/weather/outlook", methods=["GET"])
@require_api_token
def outlook():
    factor = request.args.get("factor", "wind")
    days = request.args.get("days", default=3, type=int)
    return jsonify(
        {
            "ok": True,
            "data": wq.outlook(factor, days=days),
            "data_as_of": wq.latest_fetch_timestamp("bom"),
        }
    )
