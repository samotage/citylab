"""Tests for the storage dispatch API endpoints.

Covers status / recommend / execute / log against the test database. The
``execute`` POST writes a DispatchEvent and is verified here (not against the
live dev server) per the test-data-isolation guardrail.
"""

import pytest

AUTH = {"Authorization": "Bearer dev-token-changeme"}


@pytest.fixture
def battery(app):
    """Seed a single BatteryAsset in the test database.

    The dispatch service commits (correct in production), so the conftest
    nested-transaction rollback cannot undo its writes. This fixture therefore
    commits its own seed and explicitly tears down the battery and any logged
    DispatchEvents afterwards so tests stay isolated.
    """
    from citylab.extensions import db
    from citylab.models.battery import BatteryAsset, DispatchEvent

    def _cleanup():
        existing = BatteryAsset.query.filter_by(name="Test BESS").all()
        for b in existing:
            DispatchEvent.query.filter_by(battery_id=b.id).delete()
            db.session.delete(b)
        db.session.commit()

    with app.app_context():
        _cleanup()
        b = BatteryAsset(
            name="Test BESS",
            region="VIC1",
            capacity_mwh=100.0,
            max_power_mw=50.0,
            roundtrip_eff=0.9,
            min_soc_pct=10.0,
            max_soc_pct=95.0,
            reserve_soc_pct=30.0,
            current_soc_pct=50.0,
            status="idle",
        )
        db.session.add(b)
        db.session.commit()
        yield b
        _cleanup()


def test_status_lists_batteries(client, battery):
    resp = client.get("/api/v1/energy/dispatch/status", headers=AUTH)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    names = [row["name"] for row in data["data"]]
    assert "Test BESS" in names
    row = next(r for r in data["data"] if r["name"] == "Test BESS")
    assert row["soc_pct"] == 50.0
    assert row["region"] == "VIC1"


def test_recommend_returns_decision_without_executing(client, battery):
    resp = client.get(
        "/api/v1/energy/dispatch/recommend?battery=Test BESS", headers=AUTH
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["battery"] == "Test BESS"
    assert data["action"] in {"charge", "discharge", "hold"}
    assert "reason" in data
    assert data["soc_before"] == 50.0
    # Dry run: no events logged, SoC unchanged
    from citylab.models.battery import DispatchEvent

    assert (
        DispatchEvent.query.filter_by(battery_id=battery.id).count() == 0
    )


def test_execute_logs_event_and_returns_it(client, battery):
    resp = client.post(
        "/api/v1/energy/dispatch/execute?battery=Test BESS", headers=AUTH
    )
    assert resp.status_code == 200
    event = resp.get_json()["data"]
    assert event is not None
    assert event["battery_id"] == battery.id
    assert event["action"] in {"charge", "discharge", "hold"}
    assert event["trigger"]
    assert event["reason"]

    from citylab.models.battery import DispatchEvent

    assert DispatchEvent.query.filter_by(battery_id=battery.id).count() == 1


def test_log_returns_events_newest_first(client, battery):
    # Two executions produce two events
    client.post("/api/v1/energy/dispatch/execute?battery=Test BESS", headers=AUTH)
    client.post("/api/v1/energy/dispatch/execute?battery=Test BESS", headers=AUTH)

    resp = client.get(
        "/api/v1/energy/dispatch/log?battery=Test BESS&limit=10", headers=AUTH
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["battery"] == "Test BESS"
    assert len(data["data"]) >= 2
    timestamps = [e["timestamp"] for e in data["data"]]
    assert timestamps == sorted(timestamps, reverse=True)


def test_unknown_battery_returns_404(client):
    resp = client.get(
        "/api/v1/energy/dispatch/recommend?battery=Nonexistent", headers=AUTH
    )
    assert resp.status_code == 404
    assert resp.get_json()["code"] == "NOT_FOUND"


def test_missing_battery_param_returns_400(client):
    resp = client.get("/api/v1/energy/dispatch/recommend", headers=AUTH)
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "BAD_REQUEST"


def test_dispatch_requires_token(client):
    resp = client.get("/api/v1/energy/dispatch/status")
    assert resp.status_code == 401
