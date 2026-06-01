"""App status API endpoint."""

from flask import Blueprint, jsonify

from citylab.routes.api_v1.auth import require_api_token

app_api_bp = Blueprint("app_api", __name__)


@app_api_bp.route("/app/status")
@require_api_token
def app_status():
    """Return app health and scheduler summary."""
    from citylab.extensions import db

    status = {
        "app": "citylab",
        "version": "0.1.0",
        "database": "unknown",
        "scheduler": "unknown",
    }

    try:
        db.session.execute(db.text("SELECT 1"))
        status["database"] = "connected"
    except Exception:
        status["database"] = "disconnected"

    try:
        from citylab.services.scheduler import get_scheduler

        sched = get_scheduler()
        if sched and sched.running:
            jobs = sched.get_jobs()
            status["scheduler"] = "running"
            status["scheduled_jobs"] = len(jobs)
        else:
            status["scheduler"] = "stopped"
    except Exception:
        status["scheduler"] = "not_initialized"

    return jsonify({"ok": True, "data": status})
