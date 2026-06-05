"""Remote agent session API — init, status, shutdown, send-message.

Powers the energy-dashboard chat panel and the `cli-citylab agent` commands.
All endpoints require the API Bearer token (NFR3). Responses serialise sessions
via ``AgentSession.to_dict()``, which omits the server-side session token — only
the embed_url ever reaches the browser (NFR1).
"""

import logging

from flask import Blueprint, jsonify, request

from citylab.models.agent import AgentSession
from citylab.extensions import db
from citylab.routes.api_v1.auth import require_api_token
from citylab.services import agent_service
from citylab.services.headspace_client import HeadspaceError

logger = logging.getLogger(__name__)

agent_api_bp = Blueprint("agent_api", __name__)


def _session_payload(session, config) -> dict:
    """Build the standard session response (no session_token — NFR1)."""
    data = session.to_dict()
    data["persona"] = {
        "name": config.name,
        "persona_slug": config.persona_slug,
        "role": config.description,
    }
    return data


@agent_api_bp.route("/agent/init", methods=["POST"])
@require_api_token
def init_agent():
    """Resume-or-create an agent session (FR13).

    Body (optional): {"persona": "<slug>", "initial_prompt": "..."}.
    Returns the session (id, persona, embed_url, status) — never the token.
    """
    data = request.get_json(silent=True) or {}
    persona = data.get("persona") or data.get("persona_slug")
    initial_prompt = data.get("initial_prompt")

    try:
        session = agent_service.resume_or_create(
            persona_slug=persona, initial_prompt=initial_prompt
        )
        config = session.config
        return jsonify({"ok": True, "data": _session_payload(session, config)}), 201
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e), "code": "VALIDATION_ERROR"}), 400
    except HeadspaceError as e:
        logger.error("init_agent failed: %s", e.technical_message)
        return (
            jsonify({"ok": False, "error": e.user_message, "code": "HEADSPACE_ERROR"}),
            502,
        )


@agent_api_bp.route("/agent/status", methods=["GET"])
@require_api_token
def agent_status():
    """Return the current active session status (FR15).

    Optional ?persona=<slug> filters to that config. For an active session this
    runs a live Headspace liveness probe and updates the stored status.
    """
    persona = request.args.get("persona")
    config_id = None
    if persona:
        cfg = agent_service.get_config_by_slug(persona)
        if cfg is None:
            return (
                jsonify({"ok": False, "error": "Persona not found", "code": "NOT_FOUND"}),
                404,
            )
        config_id = cfg.id

    session = agent_service.get_active_session(config_id)
    if session is None:
        return jsonify({"ok": True, "data": {"active": False}})

    # Live liveness probe for active sessions.
    try:
        agent_service.check_session(session)
    except HeadspaceError as e:
        logger.warning("status liveness probe failed: %s", e.technical_message)

    config = session.config
    payload = _session_payload(session, config)
    payload["active"] = session.status.value == "active"
    return jsonify({"ok": True, "data": payload})


@agent_api_bp.route("/agent/shutdown", methods=["POST"])
@require_api_token
def shutdown_agent():
    """Shut down a session (FR14).

    Body (optional): {"session_id": N} or {"persona": "<slug>"}. With neither,
    shuts down the most recent active session.
    """
    data = request.get_json(silent=True) or {}
    session = None

    if data.get("session_id"):
        session = db.session.get(AgentSession, int(data["session_id"]))
    elif data.get("persona") or data.get("persona_slug"):
        slug = data.get("persona") or data.get("persona_slug")
        cfg = agent_service.get_config_by_slug(slug)
        if cfg:
            session = agent_service.get_active_session(cfg.id)
    else:
        session = agent_service.get_active_session()

    if session is None:
        return jsonify({"ok": True, "data": {"active": False, "message": "No active session"}})

    try:
        session = agent_service.shutdown_session(session)
    except HeadspaceError as e:
        logger.warning("shutdown failed: %s", e.technical_message)

    return jsonify({"ok": True, "data": session.to_dict()})


@agent_api_bp.route("/agent/message", methods=["POST"])
@require_api_token
def send_agent_message():
    """Send a message to a running session (FR16).

    Body: {"message": "...", optional "session_id" or "persona"}.
    """
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return (
            jsonify({"ok": False, "error": "message is required", "code": "VALIDATION_ERROR"}),
            400,
        )

    session = None
    if data.get("session_id"):
        session = db.session.get(AgentSession, int(data["session_id"]))
    elif data.get("persona") or data.get("persona_slug"):
        slug = data.get("persona") or data.get("persona_slug")
        cfg = agent_service.get_config_by_slug(slug)
        if cfg:
            session = agent_service.get_active_session(cfg.id)
    else:
        session = agent_service.get_active_session()

    if session is None:
        return (
            jsonify({"ok": False, "error": "No active agent session", "code": "NO_SESSION"}),
            404,
        )

    try:
        result = agent_service.send_message(session, message)
        return jsonify({"ok": True, "data": result})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e), "code": "VALIDATION_ERROR"}), 400
    except HeadspaceError as e:
        logger.error("send_message failed: %s", e.technical_message)
        return (
            jsonify({"ok": False, "error": e.user_message, "code": "HEADSPACE_ERROR"}),
            502,
        )


@agent_api_bp.route("/agent/configs", methods=["GET"])
@require_api_token
def list_configs():
    """List configured agent personas (FR23)."""
    include_inactive = request.args.get("all") in ("1", "true")
    configs = agent_service.list_agent_configs(include_inactive=include_inactive)
    return jsonify({"ok": True, "data": [c.to_dict() for c in configs]})


@agent_api_bp.route("/agent/configs", methods=["POST"])
@require_api_token
def add_config():
    """Add an agent config (FR23)."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    slug = (data.get("persona_slug") or data.get("persona") or "").strip()
    if not name or not slug:
        return (
            jsonify({"ok": False, "error": "name and persona_slug required", "code": "VALIDATION_ERROR"}),
            400,
        )
    try:
        cfg = agent_service.add_agent_config(
            name=name,
            persona_slug=slug,
            description=data.get("description"),
            is_default=bool(data.get("is_default")),
        )
        return jsonify({"ok": True, "data": cfg.to_dict()}), 201
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e), "code": "DUPLICATE"}), 409


@agent_api_bp.route("/agent/configs/default", methods=["POST"])
@require_api_token
def set_default():
    """Set the default agent config (FR23)."""
    data = request.get_json(silent=True) or {}
    slug = (data.get("persona_slug") or data.get("persona") or "").strip()
    if not slug:
        return (
            jsonify({"ok": False, "error": "persona_slug required", "code": "VALIDATION_ERROR"}),
            400,
        )
    try:
        cfg = agent_service.set_default_config(slug)
        return jsonify({"ok": True, "data": cfg.to_dict()})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e), "code": "NOT_FOUND"}), 404
