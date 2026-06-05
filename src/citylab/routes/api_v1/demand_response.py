"""Demand response API — load status, event log, on-demand evaluation.

All under ``/api/v1/energy/demand-response``, Bearer token auth.
"""

from flask import Blueprint, jsonify, request

from citylab.extensions import db
from citylab.models.demand_response import ControllableLoad, DemandResponseEvent
from citylab.routes.api_v1.auth import require_api_token
from citylab.services import demand_response as dr_service

dr_api_bp = Blueprint("dr_api", __name__)


@dr_api_bp.route("/energy/demand-response/status", methods=["GET"])
@require_api_token
def status():
    """All controllable loads with current status."""
    region = request.args.get("region", "VIC1")
    loads = (
        db.session.query(ControllableLoad)
        .filter(ControllableLoad.region == region)
        .order_by(ControllableLoad.curtailment_cost.asc())
        .all()
    )

    curtailed_mw = sum(ld.capacity_mw for ld in loads if ld.status == "curtailed")

    last_event = (
        db.session.query(DemandResponseEvent)
        .order_by(DemandResponseEvent.timestamp.desc(), DemandResponseEvent.id.desc())
        .first()
    )

    return jsonify({
        "ok": True,
        "data": {
            "loads": [ld.to_dict() for ld in loads],
            "total_curtailed_mw": curtailed_mw,
            "last_activation_reason": last_event.reason if last_event else None,
        },
    })


@dr_api_bp.route("/energy/demand-response/log", methods=["GET"])
@require_api_token
def log():
    """Recent DemandResponseEvents, newest first."""
    try:
        limit = int(request.args.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, 500))

    events = (
        db.session.query(DemandResponseEvent)
        .order_by(DemandResponseEvent.timestamp.desc(), DemandResponseEvent.id.desc())
        .limit(limit)
        .all()
    )

    return jsonify({
        "ok": True,
        "data": [e.to_dict() for e in events],
    })


@dr_api_bp.route("/energy/demand-response/evaluate", methods=["POST"])
@require_api_token
def evaluate():
    """Run DR logic now and return decisions."""
    region = request.args.get("region", "VIC1")
    results = dr_service.evaluate_region(region, commit=True)
    return jsonify({
        "ok": True,
        "data": results,
    })
