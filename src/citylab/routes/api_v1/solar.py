"""Solar data API — Solcast forecasts, summary, outlook.

Mirrors the weather API: every endpoint is token-protected and returns the
{ok, data, data_as_of} envelope. data_as_of reuses the shared latest successful
fetch timestamp so agents can judge freshness across sources.
"""

from flask import Blueprint, jsonify, request

from citylab.routes.api_v1.auth import require_api_token
from citylab.services import solar_query as sq

solar_api_bp = Blueprint("solar_api", __name__)


@solar_api_bp.route("/solar/forecasts", methods=["GET"])
@require_api_token
def forecasts():
    location = request.args.get("location")
    dt_from = sq._parse_dt(request.args.get("from"))
    dt_to = sq._parse_dt(request.args.get("to"))
    return jsonify(
        {
            "ok": True,
            "data": sq.query_forecasts(location, dt_from, dt_to),
            "data_as_of": sq.latest_fetch_timestamp("solcast"),
        }
    )


@solar_api_bp.route("/solar/summary", methods=["GET"])
@require_api_token
def summary():
    return jsonify(
        {
            "ok": True,
            "data": sq.summary(),
            "data_as_of": sq.latest_fetch_timestamp("solcast"),
        }
    )


@solar_api_bp.route("/solar/outlook", methods=["GET"])
@require_api_token
def outlook():
    days = request.args.get("days", default=3, type=int)
    return jsonify(
        {
            "ok": True,
            "data": sq.outlook(days=days),
            "data_as_of": sq.latest_fetch_timestamp("solcast"),
        }
    )
