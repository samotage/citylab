"""Tests for the remote agent interface: HeadspaceClient, agent_service,
agent API routes, and model constraints.

Headspace HTTP is mocked throughout — no real agent service is contacted.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

AUTH = {"Authorization": "Bearer dev-token-changeme"}


# ---------------------------------------------------------------------------
# HeadspaceClient — retry + error wrapping
# ---------------------------------------------------------------------------


def _resp(status, json_body=None, ok=None):
    r = MagicMock()
    r.status_code = status
    r.ok = (status < 400) if ok is None else ok
    r.json.return_value = json_body or {}
    r.text = str(json_body)
    return r


def test_client_create_agent_success():
    from citylab.services.headspace_client import HeadspaceClient

    client = HeadspaceClient("http://hs:5001", "citylab", timeout=5)
    ok = _resp(
        201,
        {
            "agent_id": 42,
            "embed_url": "http://hs:5001/embed/42?token=abc",
            "session_token": "tok-abc",
        },
    )
    with patch.object(client._session, "post", return_value=ok) as m:
        result = client.create_agent("ray", initial_prompt="hi")
    assert result["agent_id"] == "42"
    assert result["embed_url"].endswith("token=abc")
    assert result["session_token"] == "tok-abc"
    # project_slug + persona + initial_prompt go in the payload.
    payload = m.call_args.kwargs["json"]
    assert payload["project_slug"] == "citylab"
    assert payload["persona_slug"] == "ray"
    assert payload["initial_prompt"] == "hi"


def test_client_create_agent_retries_once_on_503():
    from citylab.services.headspace_client import HeadspaceClient

    client = HeadspaceClient("http://hs:5001", "citylab")
    bad = _resp(503, {"error": "unavailable"})
    good = _resp(
        201,
        {"agent_id": 7, "embed_url": "http://e/7", "session_token": "t7"},
    )
    with patch.object(client._session, "post", side_effect=[bad, good]) as m:
        result = client.create_agent("ray")
    assert result["agent_id"] == "7"
    assert m.call_count == 2  # retried once


def test_client_wraps_connection_error():
    from citylab.services.headspace_client import HeadspaceClient, HeadspaceError

    client = HeadspaceClient("http://hs:5001", "citylab")
    with patch.object(
        client._session,
        "post",
        side_effect=requests.exceptions.ConnectionError("refused"),
    ):
        with pytest.raises(HeadspaceError) as exc:
            client.create_agent("ray")
    # Domain exception carries technical + user-friendly messages.
    assert "refused" in exc.value.technical_message
    assert "agent service" in exc.value.user_message.lower()


def test_client_check_alive_false_on_404():
    from citylab.services.headspace_client import HeadspaceClient

    client = HeadspaceClient("http://hs:5001", "citylab")
    with patch.object(client._session, "get", return_value=_resp(404, {}, ok=False)):
        assert client.check_alive("9", "tok") is False


def test_client_shutdown_idempotent_on_404():
    from citylab.services.headspace_client import HeadspaceClient

    client = HeadspaceClient("http://hs:5001", "citylab")
    with patch.object(client._session, "post", return_value=_resp(404, {}, ok=False)):
        assert client.shutdown_agent("9", "tok") is True


# ---------------------------------------------------------------------------
# Model constraints — default + active-session
# ---------------------------------------------------------------------------


def test_agent_session_to_dict_omits_token(db_session):
    from citylab.models.agent import AgentConfig, AgentSession, SessionStatus

    cfg = AgentConfig(name="Ray", persona_slug="ray-model-1", is_default=True)
    db_session.add(cfg)
    db_session.flush()
    sess = AgentSession(
        config_id=cfg.id,
        headspace_agent_id="11",
        embed_url="http://e/11",
        session_token="SECRET-TOKEN",
        status=SessionStatus.active,
    )
    db_session.add(sess)
    db_session.flush()
    d = sess.to_dict()
    assert "session_token" not in d
    assert "SECRET-TOKEN" not in str(d)
    assert d["embed_url"] == "http://e/11"
    assert d["status"] == "active"


def test_only_one_active_session_per_config(db_session):
    """The partial unique index forbids two active sessions for one config."""
    from sqlalchemy.exc import IntegrityError

    from citylab.models.agent import AgentConfig, AgentSession, SessionStatus

    cfg = AgentConfig(name="Ray", persona_slug="ray-model-2")
    db_session.add(cfg)
    db_session.flush()

    s1 = AgentSession(
        config_id=cfg.id,
        headspace_agent_id="1",
        embed_url="http://e/1",
        session_token="t1",
        status=SessionStatus.active,
    )
    db_session.add(s1)
    db_session.flush()

    s2 = AgentSession(
        config_id=cfg.id,
        headspace_agent_id="2",
        embed_url="http://e/2",
        session_token="t2",
        status=SessionStatus.active,
    )
    db_session.add(s2)
    with pytest.raises(IntegrityError):
        db_session.flush()


# ---------------------------------------------------------------------------
# agent_service — resume-or-create logic (Headspace mocked)
# ---------------------------------------------------------------------------


@pytest.fixture
def ray_config(app):
    """Seed a Ray config, yield it, then clean up its sessions + row."""
    from citylab.extensions import db
    from citylab.models.agent import AgentConfig, AgentSession

    with app.app_context():
        cfg = AgentConfig(
            name="Ray", persona_slug="ray-svc-1", is_default=True, is_active=True
        )
        db.session.add(cfg)
        db.session.commit()
        cfg_id = cfg.id
    yield cfg_id
    with app.app_context():
        db.session.query(AgentSession).filter_by(config_id=cfg_id).delete()
        obj = db.session.get(AgentConfig, cfg_id)
        if obj:
            db.session.delete(obj)
        db.session.commit()


def test_resume_or_create_creates_when_none(app, ray_config):
    from citylab.extensions import db
    from citylab.models.agent import AgentSession, SessionStatus
    from citylab.services import agent_service

    fake = MagicMock()
    fake.create_agent.return_value = {
        "agent_id": "100",
        "embed_url": "http://e/100",
        "session_token": "tok100",
    }
    with app.app_context():
        with patch.object(agent_service, "_get_client", return_value=fake):
            session = agent_service.resume_or_create(persona_slug="ray-svc-1")
        assert session.status == SessionStatus.active
        assert session.headspace_agent_id == "100"
        fake.create_agent.assert_called_once()


def test_resume_or_create_reuses_alive_session(app, ray_config):
    from citylab.extensions import db
    from citylab.models.agent import AgentSession, SessionStatus
    from citylab.services import agent_service

    # Pre-existing active session.
    with app.app_context():
        existing = AgentSession(
            config_id=ray_config,
            headspace_agent_id="200",
            embed_url="http://e/200",
            session_token="tok200",
            status=SessionStatus.active,
        )
        db.session.add(existing)
        db.session.commit()
        existing_id = existing.id

    fake = MagicMock()
    fake.check_alive.return_value = True
    with app.app_context():
        with patch.object(agent_service, "_get_client", return_value=fake):
            session = agent_service.resume_or_create(persona_slug="ray-svc-1")
        assert session.id == existing_id  # reused, not recreated
        fake.create_agent.assert_not_called()


def test_resume_or_create_replaces_dead_session(app, ray_config):
    from citylab.extensions import db
    from citylab.models.agent import AgentSession, SessionStatus
    from citylab.services import agent_service

    with app.app_context():
        existing = AgentSession(
            config_id=ray_config,
            headspace_agent_id="300",
            embed_url="http://e/300",
            session_token="tok300",
            status=SessionStatus.active,
        )
        db.session.add(existing)
        db.session.commit()
        existing_id = existing.id

    fake = MagicMock()
    fake.check_alive.return_value = False  # dead
    fake.create_agent.return_value = {
        "agent_id": "301",
        "embed_url": "http://e/301",
        "session_token": "tok301",
    }
    with app.app_context():
        with patch.object(agent_service, "_get_client", return_value=fake):
            session = agent_service.resume_or_create(persona_slug="ray-svc-1")
        assert session.id != existing_id
        assert session.headspace_agent_id == "301"
        old = db.session.get(AgentSession, existing_id)
        assert old.status == SessionStatus.dead
        fake.create_agent.assert_called_once()


# ---------------------------------------------------------------------------
# agent API routes — auth, no token leak, lifecycle
# ---------------------------------------------------------------------------


def test_agent_init_requires_auth(client):
    resp = client.post("/api/v1/agent/init", json={})
    assert resp.status_code == 401


def test_agent_status_requires_auth(client):
    resp = client.get("/api/v1/agent/status")
    assert resp.status_code == 401


def test_agent_init_returns_session_without_token(client, app, ray_config):
    from citylab.services import agent_service

    fake = MagicMock()
    fake.create_agent.return_value = {
        "agent_id": "400",
        "embed_url": "http://e/400?token=zzz",
        "session_token": "SECRET-ROUTE-TOKEN",
    }
    with patch.object(agent_service, "_get_client", return_value=fake):
        resp = client.post(
            "/api/v1/agent/init", json={"persona": "ray-svc-1"}, headers=AUTH
        )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["ok"] is True
    data = body["data"]
    assert data["embed_url"].endswith("token=zzz")
    assert data["persona"]["persona_slug"] == "ray-svc-1"
    # NFR1: the server-side session token never reaches the client.
    assert "session_token" not in data
    assert "SECRET-ROUTE-TOKEN" not in resp.get_data(as_text=True)


def test_agent_status_no_active_session(client, app, ray_config):
    resp = client.get(
        "/api/v1/agent/status?persona=ray-svc-1", headers=AUTH
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["data"]["active"] is False


def test_agent_shutdown_lifecycle(client, app, ray_config):
    from citylab.extensions import db
    from citylab.models.agent import AgentSession, SessionStatus
    from citylab.services import agent_service

    with app.app_context():
        sess = AgentSession(
            config_id=ray_config,
            headspace_agent_id="500",
            embed_url="http://e/500",
            session_token="tok500",
            status=SessionStatus.active,
        )
        db.session.add(sess)
        db.session.commit()

    fake = MagicMock()
    fake.shutdown_agent.return_value = True
    with patch.object(agent_service, "_get_client", return_value=fake):
        resp = client.post(
            "/api/v1/agent/shutdown", json={"persona": "ray-svc-1"}, headers=AUTH
        )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["data"]["status"] == "shutdown"


def test_agent_configs_list_includes_seeded(client, app, ray_config):
    resp = client.get("/api/v1/agent/configs", headers=AUTH)
    assert resp.status_code == 200
    body = resp.get_json()
    slugs = [c["persona_slug"] for c in body["data"]]
    assert "ray-svc-1" in slugs
