"""Health check endpoint — no auth required."""

from flask import Blueprint, jsonify

from citylab.extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health():
    status = {"status": "healthy", "database": "unknown", "scheduler": "unknown"}

    # Check database
    try:
        db.session.execute(db.text("SELECT 1"))
        status["database"] = "connected"
    except Exception:
        status["database"] = "disconnected"
        status["status"] = "degraded"

    # Check Redis (best effort)
    try:
        import redis as redis_lib
        from flask import current_app

        redis_url = current_app.config.get("CITYLAB_CONFIG", {}).get("redis", {}).get("url", "")
        if redis_url:
            r = redis_lib.from_url(redis_url, socket_connect_timeout=1)
            r.ping()
            status["redis"] = "connected"
        else:
            status["redis"] = "not_configured"
    except Exception:
        status["redis"] = "disconnected"

    # Check scheduler
    try:
        from citylab.services.scheduler import get_scheduler

        sched = get_scheduler()
        if sched and sched.running:
            status["scheduler"] = "running"
        else:
            status["scheduler"] = "stopped"
    except Exception:
        status["scheduler"] = "not_initialized"

    return jsonify(status), 200
