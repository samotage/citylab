"""Tests for demand response models, service, and API endpoints."""

import pytest
from datetime import datetime, timedelta, timezone

AUTH = {"Authorization": "Bearer dev-token-changeme"}


@pytest.fixture
def loads(app):
    """Seed controllable loads in the test database with explicit teardown."""
    from citylab.extensions import db
    from citylab.models.demand_response import ControllableLoad, DemandResponseEvent

    def _cleanup():
        DemandResponseEvent.query.delete()
        ControllableLoad.query.delete()
        db.session.commit()

    with app.app_context():
        _cleanup()
        specs = [
            ("Hot Water", "hot_water", 45.0, 15.0, 30, 240),
            ("EV Charging", "ev_charging", 25.0, 35.0, 15, 120),
            ("HVAC", "hvac_commercial", 60.0, 80.0, 15, 60),
            ("Industrial", "industrial_process", 150.0, 200.0, 60, 480),
        ]
        created = []
        for name, lt, cap, cost, mn, mx in specs:
            ld = ControllableLoad(
                name=name, region="VIC1", load_type=lt,
                capacity_mw=cap, curtailment_cost=cost,
                min_duration_min=mn, max_duration_min=mx,
                status="available",
            )
            db.session.add(ld)
            created.append(ld)
        db.session.commit()
        yield created
        _cleanup()


@pytest.fixture
def battery_for_dr(app):
    """Seed a battery so DR can read dispatch engine state."""
    from citylab.extensions import db
    from citylab.models.battery import BatteryAsset, DispatchEvent

    def _cleanup():
        existing = BatteryAsset.query.filter_by(name="DR Test BESS").all()
        for b in existing:
            DispatchEvent.query.filter_by(battery_id=b.id).delete()
            db.session.delete(b)
        db.session.commit()

    with app.app_context():
        _cleanup()
        b = BatteryAsset(
            name="DR Test BESS", region="VIC1",
            capacity_mwh=100.0, max_power_mw=50.0,
            roundtrip_eff=0.9, min_soc_pct=10.0,
            max_soc_pct=95.0, reserve_soc_pct=30.0,
            current_soc_pct=50.0, status="holding",
        )
        db.session.add(b)
        db.session.commit()
        yield b
        _cleanup()


def _seed_market_data(app, price, demand_mw, generation_mw):
    """Seed price, demand, and generation rows for DR trigger testing."""
    from citylab.extensions import db
    from citylab.models.energy import EnergyDemand, EnergyPrice, GenerationOutput

    now = datetime.now(timezone.utc)
    with app.app_context():
        db.session.add(EnergyPrice(
            region="VIC1", interval_start=now,
            price_aud_mwh=price,
        ))
        db.session.add(EnergyDemand(
            region="VIC1", interval_start=now,
            demand_mw=demand_mw,
        ))
        db.session.add(GenerationOutput(
            region="VIC1", interval_start=now,
            fuel_type="gas_ccgt", output_mw=generation_mw,
        ))
        db.session.commit()


def _cleanup_market_data(app):
    from citylab.extensions import db
    from citylab.models.energy import EnergyDemand, EnergyPrice, GenerationOutput
    with app.app_context():
        EnergyPrice.query.filter_by(region="VIC1").delete()
        EnergyDemand.query.filter_by(region="VIC1").delete()
        GenerationOutput.query.filter_by(region="VIC1").delete()
        db.session.commit()


# --- API endpoint tests ---

def test_status_returns_loads(client, loads):
    resp = client.get("/api/v1/energy/demand-response/status", headers=AUTH)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert len(data["data"]["loads"]) == 4
    assert data["data"]["total_curtailed_mw"] == 0
    names = [ld["name"] for ld in data["data"]["loads"]]
    assert names[0] == "Hot Water"
    assert names[-1] == "Industrial"


def test_log_empty(client, loads):
    resp = client.get("/api/v1/energy/demand-response/log", headers=AUTH)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["data"] == []


def test_evaluate_no_trigger(client, loads, battery_for_dr):
    resp = client.post(
        "/api/v1/energy/demand-response/evaluate?region=VIC1", headers=AUTH
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True


# --- Service logic tests ---

def test_cheapest_first_activation_on_deficit(app, loads, battery_for_dr):
    """Supply deficit should activate loads cheapest-first."""
    _seed_market_data(app, price=100.0, demand_mw=5100.0, generation_mw=5000.0)
    try:
        from citylab.services.demand_response import evaluate_region
        with app.app_context():
            results = evaluate_region("VIC1", commit=True)
            curtails = [r for r in results if r["action"] == "curtail"]
            assert len(curtails) >= 1
            assert curtails[0]["load"] == "Hot Water"
    finally:
        _cleanup_market_data(app)


def test_price_spike_activation(app, loads, battery_for_dr):
    """Price spike with battery committed should activate loads."""
    _seed_market_data(app, price=400.0, demand_mw=5000.0, generation_mw=5500.0)
    try:
        from citylab.services.demand_response import evaluate_region
        with app.app_context():
            results = evaluate_region("VIC1", commit=True)
            curtails = [r for r in results if r["action"] == "curtail"]
            assert len(curtails) >= 1
            assert curtails[0]["load"] == "Hot Water"
            for c in curtails:
                assert c["trigger"] == "price_spike"
    finally:
        _cleanup_market_data(app)


def test_release_most_expensive_first(app, loads, battery_for_dr):
    """When conditions normalise, release most expensive first."""
    from citylab.extensions import db
    from citylab.models.demand_response import ControllableLoad

    _seed_market_data(app, price=50.0, demand_mw=4000.0, generation_mw=5000.0)
    try:
        from citylab.services.demand_response import evaluate_region
        with app.app_context():
            now = datetime.now(timezone.utc)
            curtailed = (
                db.session.query(ControllableLoad)
                .filter(ControllableLoad.name.in_(["Hot Water", "EV Charging"]))
                .all()
            )
            for ld in curtailed:
                ld.status = "curtailed"
                ld.curtailed_since = now - timedelta(minutes=60)
            db.session.commit()

            results = evaluate_region("VIC1", commit=True)
            releases = [r for r in results if r["action"] == "release"]
            assert len(releases) == 2
            assert releases[0]["load"] == "EV Charging"
            assert releases[1]["load"] == "Hot Water"
    finally:
        _cleanup_market_data(app)


def test_recovery_period_prevents_cycling(app, loads, battery_for_dr):
    """A recovering load should not be available for re-curtailment."""
    from citylab.extensions import db
    from citylab.models.demand_response import ControllableLoad

    _seed_market_data(app, price=400.0, demand_mw=5000.0, generation_mw=5500.0)
    try:
        from citylab.services.demand_response import evaluate_region
        with app.app_context():
            hot_water = (
                db.session.query(ControllableLoad)
                .filter_by(name="Hot Water")
                .first()
            )
            hot_water.status = "recovering"
            hot_water.curtailed_since = datetime.now(timezone.utc)
            db.session.commit()

            results = evaluate_region("VIC1", commit=True)
            curtailed_names = [r["load"] for r in results if r["action"] == "curtail"]
            assert "Hot Water" not in curtailed_names
    finally:
        _cleanup_market_data(app)


def test_min_duration_respected(app, loads, battery_for_dr):
    """Curtailed load should not be released before min_duration_min."""
    from citylab.extensions import db
    from citylab.models.demand_response import ControllableLoad

    _seed_market_data(app, price=50.0, demand_mw=4000.0, generation_mw=5000.0)
    try:
        from citylab.services.demand_response import evaluate_region
        with app.app_context():
            hot_water = (
                db.session.query(ControllableLoad)
                .filter_by(name="Hot Water")
                .first()
            )
            hot_water.status = "curtailed"
            hot_water.curtailed_since = datetime.now(timezone.utc) - timedelta(minutes=5)
            db.session.commit()

            results = evaluate_region("VIC1", commit=True)
            holds = [r for r in results if r["action"] == "hold" and r["load"] == "Hot Water"]
            assert len(holds) == 1
            assert "minimum duration" in holds[0]["reason"]
    finally:
        _cleanup_market_data(app)
