"""Agent service layer — remote-agent lifecycle business logic.

Sits between the API/CLI surface and the HeadspaceClient. Owns:

- Config CRUD: seed from config.yaml, list, add, set-default (FR1-FR4).
- Session lifecycle with resume-or-create (FR5-FR9): if a config already has an
  active session, probe Headspace; reuse it if alive, otherwise mark it dead and
  create a fresh one.

Session tokens live server-side only — they are stored on the AgentSession row
and passed to HeadspaceClient, but never returned to callers (NFR1). The API
layer serialises sessions via ``AgentSession.to_dict()`` which omits the token.
"""

import logging
from datetime import datetime, timezone

from flask import current_app

from citylab.extensions import db
from citylab.models.agent import AgentConfig, AgentSession, SessionStatus
from citylab.services.headspace_client import HeadspaceClient, HeadspaceError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Headspace client factory
# ---------------------------------------------------------------------------


def _headspace_cfg() -> dict:
    return current_app.config.get("CITYLAB_CONFIG", {}).get("headspace", {})


def _get_client() -> HeadspaceClient:
    """Build a HeadspaceClient from app config.

    Raises HeadspaceError if Headspace is not configured.
    """
    cfg = _headspace_cfg()
    url = cfg.get("url")
    if not url:
        raise HeadspaceError(
            "Headspace not configured (no headspace.url)",
            "Remote agent integration is not configured. Set headspace.url in "
            "config.yaml or the HEADSPACE_URL env var.",
        )
    return HeadspaceClient(
        base_url=url,
        project_slug=cfg.get("project_name", "citylab"),
        timeout=cfg.get("timeout_seconds", 30),
    )


# ---------------------------------------------------------------------------
# Config CRUD (FR1-FR4)
# ---------------------------------------------------------------------------


def seed_agent_configs() -> list[dict]:
    """Seed/refresh AgentConfig rows from config.yaml's headspace.personas.

    Idempotent: existing personas are updated (name/role), new ones inserted.
    The first persona in the list becomes the default if no default exists.
    Returns a list of summary dicts.
    """
    personas = _headspace_cfg().get("personas", []) or []
    results = []
    have_default = (
        db.session.query(AgentConfig).filter_by(is_default=True).first() is not None
    )

    for idx, p in enumerate(personas):
        slug = p.get("slug")
        if not slug:
            continue
        name = p.get("name") or slug
        role = p.get("role")

        existing = (
            db.session.query(AgentConfig).filter_by(persona_slug=slug).first()
        )
        if existing:
            existing.name = name
            existing.description = role
            existing.is_active = True
            cfg = existing
        else:
            make_default = (idx == 0) and not have_default
            cfg = AgentConfig(
                name=name,
                persona_slug=slug,
                description=role,
                is_active=True,
                is_default=make_default,
            )
            db.session.add(cfg)
            if make_default:
                have_default = True

        results.append(
            {"name": name, "persona_slug": slug, "role": role}
        )

    db.session.commit()
    return results


def list_agent_configs(include_inactive: bool = False) -> list[AgentConfig]:
    q = db.session.query(AgentConfig)
    if not include_inactive:
        q = q.filter(AgentConfig.is_active.is_(True))
    return q.order_by(AgentConfig.name).all()


def get_default_config() -> AgentConfig | None:
    return (
        db.session.query(AgentConfig)
        .filter_by(is_default=True, is_active=True)
        .first()
    )


def get_config_by_slug(persona_slug: str) -> AgentConfig | None:
    return (
        db.session.query(AgentConfig).filter_by(persona_slug=persona_slug).first()
    )


def add_agent_config(
    name: str,
    persona_slug: str,
    description: str | None = None,
    is_default: bool = False,
) -> AgentConfig:
    """Create a new agent config. Raises ValueError on duplicate slug."""
    if get_config_by_slug(persona_slug):
        raise ValueError(f"Agent config '{persona_slug}' already exists")

    if is_default:
        _unset_default()

    cfg = AgentConfig(
        name=name,
        persona_slug=persona_slug,
        description=description,
        is_active=True,
        is_default=is_default,
    )
    db.session.add(cfg)
    db.session.commit()
    return cfg


def set_default_config(persona_slug: str) -> AgentConfig:
    """Mark a config the default, unsetting the previous one (FR2)."""
    cfg = get_config_by_slug(persona_slug)
    if cfg is None:
        raise ValueError(f"Agent config '{persona_slug}' not found")
    if not cfg.is_active:
        raise ValueError(f"Agent '{cfg.name}' is inactive")
    _unset_default()
    cfg.is_default = True
    db.session.commit()
    return cfg


def _unset_default() -> None:
    current = db.session.query(AgentConfig).filter_by(is_default=True).first()
    if current:
        current.is_default = False


# ---------------------------------------------------------------------------
# Session lifecycle (FR5-FR9)
# ---------------------------------------------------------------------------


def _active_session(config_id: int) -> AgentSession | None:
    return (
        db.session.query(AgentSession)
        .filter_by(config_id=config_id, status=SessionStatus.active)
        .first()
    )


def resolve_config(persona_slug: str | None = None) -> AgentConfig:
    """Resolve the target config: explicit slug, else the default."""
    if persona_slug:
        cfg = get_config_by_slug(persona_slug)
        if cfg is None:
            raise ValueError(f"Agent config '{persona_slug}' not found")
        if not cfg.is_active:
            raise ValueError(f"Agent '{cfg.name}' is inactive")
        return cfg
    cfg = get_default_config()
    if cfg is None:
        raise ValueError(
            "No default agent configured. Run 'flask seed-agents' or pass a "
            "persona slug."
        )
    return cfg


def resume_or_create(
    persona_slug: str | None = None, initial_prompt: str | None = None
) -> AgentSession:
    """Resume an alive session for the config, or create a fresh one (FR6).

    Resolution order:
      1. Resolve the config (explicit slug or default).
      2. If an active session exists, probe Headspace liveness.
         - alive  -> reuse it, stamp last_alive_at.
         - dead   -> mark it dead, fall through to create.
      3. Create a new Headspace agent and persist the session.
    """
    cfg = resolve_config(persona_slug)
    client = _get_client()

    existing = _active_session(cfg.id)
    if existing:
        if client.check_alive(existing.headspace_agent_id, existing.session_token):
            existing.mark_alive()
            db.session.commit()
            logger.info("Resumed alive agent session %s", existing.id)
            return existing
        # Stale active row — the Headspace agent is gone.
        existing.status = SessionStatus.dead
        existing.ended_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info("Marked dead stale session %s; creating new", existing.id)

    result = client.create_agent(
        persona_slug=cfg.persona_slug, initial_prompt=initial_prompt
    )
    session = AgentSession(
        config_id=cfg.id,
        headspace_agent_id=result["agent_id"],
        embed_url=result["embed_url"],
        session_token=result["session_token"],
        status=SessionStatus.active,
        last_alive_at=datetime.now(timezone.utc),
    )
    db.session.add(session)
    db.session.commit()
    logger.info("Started agent session %s for %s", session.id, cfg.name)
    return session


def check_session(session: AgentSession) -> bool:
    """Probe a session's liveness, updating its status (FR7).

    Returns True if alive. A previously-active session that fails the probe is
    transitioned to disconnected.
    """
    client = _get_client()
    alive = client.check_alive(session.headspace_agent_id, session.session_token)
    if alive:
        session.mark_alive()
    elif session.status == SessionStatus.active:
        session.status = SessionStatus.disconnected
        logger.warning("Agent session %s disconnected", session.id)
    db.session.commit()
    return alive


def shutdown_session(session: AgentSession) -> AgentSession:
    """Gracefully shut down a session (FR8).

    Calls Headspace shutdown (best-effort) and marks the row shutdown locally
    even if the remote call fails.
    """
    if session.status in (SessionStatus.shutdown, SessionStatus.dead):
        return session
    try:
        client = _get_client()
        client.shutdown_agent(session.headspace_agent_id, session.session_token)
    except HeadspaceError as e:
        logger.warning(
            "Headspace shutdown failed for session %s: %s",
            session.id,
            e.technical_message,
        )
    session.status = SessionStatus.shutdown
    session.ended_at = datetime.now(timezone.utc)
    db.session.commit()
    logger.info("Shut down agent session %s", session.id)
    return session


def get_active_session(config_id: int | None = None) -> AgentSession | None:
    """Return the active session for a config, or any active session."""
    q = db.session.query(AgentSession).filter_by(status=SessionStatus.active)
    if config_id is not None:
        q = q.filter_by(config_id=config_id)
    return q.order_by(AgentSession.id.desc()).first()


def send_message(session: AgentSession, message: str) -> dict:
    """Send a message to an active session via Headspace."""
    if session.status != SessionStatus.active:
        raise ValueError(
            f"Cannot message a session in '{session.status.value}' state — "
            "start a new session first."
        )
    client = _get_client()
    return client.send_message(
        session.headspace_agent_id, message, session.session_token
    )
