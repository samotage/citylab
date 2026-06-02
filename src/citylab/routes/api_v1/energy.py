"""Energy market data API — prices, generation, interconnectors, forecasts, summary."""

from flask import Blueprint, jsonify, request

from citylab.routes.api_v1.auth import require_api_token
from citylab.services import energy_query as eq

energy_api_bp = Blueprint("energy_api", __name__)


def _range_args():
    region = request.args.get("region", "VIC1")
    dt_from = eq._parse_dt(request.args.get("from"))
    dt_to = eq._parse_dt(request.args.get("to"))
    return region, dt_from, dt_to


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
