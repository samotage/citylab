"""Scheduled tasks CRUD API."""

from flask import Blueprint, jsonify, request

from citylab.extensions import db
from citylab.models.scheduled_task import ScheduledTask
from citylab.routes.api_v1.auth import require_api_token

schedules_api_bp = Blueprint("schedules_api", __name__)


@schedules_api_bp.route("/schedules", methods=["GET"])
@require_api_token
def list_schedules():
    """List all scheduled tasks."""
    tasks = db.session.query(ScheduledTask).order_by(ScheduledTask.name).all()
    return jsonify({"ok": True, "data": [t.to_dict() for t in tasks]})


@schedules_api_bp.route("/schedules", methods=["POST"])
@require_api_token
def create_schedule():
    """Create a new scheduled task."""
    data = request.get_json(silent=True) or {}

    required = ["name", "cron_expression", "agent_persona", "agent_action"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"ok": False, "error": f"Missing fields: {', '.join(missing)}", "code": "VALIDATION_ERROR"}), 400

    # Check duplicate name
    existing = db.session.query(ScheduledTask).filter_by(name=data["name"]).first()
    if existing:
        return jsonify({"ok": False, "error": f"Schedule '{data['name']}' already exists", "code": "DUPLICATE"}), 409

    task = ScheduledTask(
        name=data["name"],
        cron_expression=data["cron_expression"],
        agent_persona=data["agent_persona"],
        agent_action=data["agent_action"],
        is_active=data.get("is_active", True),
    )
    db.session.add(task)
    db.session.commit()

    return jsonify({"ok": True, "data": task.to_dict()}), 201


@schedules_api_bp.route("/schedules/<int:task_id>", methods=["PUT"])
@require_api_token
def update_schedule(task_id):
    """Update a scheduled task."""
    task = db.session.get(ScheduledTask, task_id)
    if not task:
        return jsonify({"ok": False, "error": "Schedule not found", "code": "NOT_FOUND"}), 404

    data = request.get_json(silent=True) or {}
    for field in ["name", "cron_expression", "agent_persona", "agent_action", "is_active"]:
        if field in data:
            setattr(task, field, data[field])

    db.session.commit()
    return jsonify({"ok": True, "data": task.to_dict()})


@schedules_api_bp.route("/schedules/<int:task_id>", methods=["DELETE"])
@require_api_token
def delete_schedule(task_id):
    """Delete a scheduled task."""
    task = db.session.get(ScheduledTask, task_id)
    if not task:
        return jsonify({"ok": False, "error": "Schedule not found", "code": "NOT_FOUND"}), 404

    db.session.delete(task)
    db.session.commit()
    return jsonify({"ok": True, "data": {"deleted": task_id}})


@schedules_api_bp.route("/schedules/sync", methods=["POST"])
@require_api_token
def sync_schedules():
    """Sync scheduled tasks with APScheduler."""
    try:
        from citylab.services.scheduler import sync_jobs

        count = sync_jobs()
        return jsonify({"ok": True, "data": {"synced": count}})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "code": "SCHEDULER_ERROR"}), 500
