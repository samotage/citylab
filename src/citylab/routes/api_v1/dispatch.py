"""Storage dispatch API — battery state, recommendations, execution, decision log.

All under ``/api/v1/energy/dispatch``, Bearer token auth. The dispatch engine
itself lives in ``citylab.services.dispatch`` (module-level ``evaluate`` /
``evaluate_region``); these endpoints are the read/act surface on top of it.
"""

from flask import Blueprint, jsonify, request

from citylab.extensions import db
from citylab.models.battery import BatteryAsset, DispatchEvent
from citylab.routes.api_v1.auth import require_api_token
from citylab.services import dispatch as dispatch_service

dispatch_api_bp = Blueprint("dispatch_api", __name__)


def _get_battery_or_error(name: str | None):
    """Resolve a battery by name. Returns (battery, error_response, status)."""
    if not name:
        return None, jsonify(
            {"ok": False, "error": "Missing 'battery' query parameter", "code": "BAD_REQUEST"}
        ), 400

    battery = (
        db.session.query(BatteryAsset)
        .filter(BatteryAsset.name == name)
        .first()
    )
    if not battery:
        return None, jsonify(
            {"ok": False, "error": f"Battery '{name}' not found", "code": "NOT_FOUND"}
        ), 404

    return battery, None, None


def _latest_event(battery_id: int) -> DispatchEvent | None:
    return (
        db.session.query(DispatchEvent)
        .filter(DispatchEvent.battery_id == battery_id)
        .order_by(DispatchEvent.timestamp.desc(), DispatchEvent.id.desc())
        .first()
    )


@dispatch_api_bp.route("/energy/dispatch/status", methods=["GET"])
@require_api_token
def status():
    """Current state of all batteries plus their last dispatch decision."""
    batteries = (
        db.session.query(BatteryAsset)
        .order_by(BatteryAsset.name.asc())
        .all()
    )

    data = []
    for b in batteries:
        last = _latest_event(b.id)
        data.append(
            {
                "name": b.name,
                "region": b.region,
                "soc_pct": b.current_soc_pct,
                "status": b.status,
                "last_action": last.action if last else None,
                "last_trigger": last.trigger if last else None,
                "last_reason": last.reason if last else None,
                "last_timestamp": last.timestamp.isoformat() if last else None,
            }
        )

    return jsonify({"ok": True, "data": data})


@dispatch_api_bp.route("/energy/dispatch/recommend", methods=["GET"])
@require_api_token
def recommend():
    """Run the dispatch engine for a battery WITHOUT executing (dry run)."""
    battery, err, code = _get_battery_or_error(request.args.get("battery"))
    if err:
        return err, code

    decision = dispatch_service.evaluate(battery, commit=False)
    return jsonify(
        {
            "ok": True,
            "data": {
                "battery": battery.name,
                "region": battery.region,
                "action": decision["action"],
                "power_mw": decision["power_mw"],
                "trigger": decision["trigger"],
                "reason": decision["reason"],
                "soc_before": decision["soc_before_pct"],
                "soc_after": decision["soc_after_pct"],
                "market_price": decision["market_price"],
                "forecast_price": decision["forecast_price"],
            },
        }
    )


@dispatch_api_bp.route("/energy/dispatch/execute", methods=["POST"])
@require_api_token
def execute():
    """Run AND execute the dispatch decision: update SoC, log a DispatchEvent."""
    battery, err, code = _get_battery_or_error(request.args.get("battery"))
    if err:
        return err, code

    dispatch_service.evaluate(battery, commit=True)
    event = _latest_event(battery.id)

    return jsonify({"ok": True, "data": event.to_dict() if event else None})


@dispatch_api_bp.route("/energy/dispatch/log", methods=["GET"])
@require_api_token
def log():
    """Recent dispatch decisions for a battery, newest first."""
    battery, err, code = _get_battery_or_error(request.args.get("battery"))
    if err:
        return err, code

    try:
        limit = int(request.args.get("limit", 50))
    except (TypeError, ValueError):
        limit = 50
    limit = max(1, min(limit, 500))

    events = (
        db.session.query(DispatchEvent)
        .filter(DispatchEvent.battery_id == battery.id)
        .order_by(DispatchEvent.timestamp.desc(), DispatchEvent.id.desc())
        .limit(limit)
        .all()
    )

    return jsonify(
        {
            "ok": True,
            "battery": battery.name,
            "data": [e.to_dict() for e in events],
        }
    )
