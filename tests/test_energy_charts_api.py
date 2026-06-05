"""Tests for the energy chart timeseries API + query helpers."""

from datetime import datetime, timedelta, timezone

import pytest

from citylab.extensions import db
from citylab.models.energy import EnergyDemand, EnergyPrice, GenerationOutput
from citylab.services import energy_query as eq

TOKEN = "dev-token-changeme"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture
def seeded(app):
    """Seed ~3h of VIC1 price/demand/generation at 5-min intervals."""
    with app.app_context():
        # Clear any prior rows for a clean window.
        db.session.query(EnergyPrice).delete()
        db.session.query(EnergyDemand).delete()
        db.session.query(GenerationOutput).delete()

        now = datetime.now(timezone.utc).replace(microsecond=0)
        start = now - timedelta(hours=3)
        for i in range(36):  # 36 * 5min = 3h
            ts = start + timedelta(minutes=5 * i)
            db.session.add(
                EnergyPrice(
                    region="VIC1", interval_start=ts,
                    interval_type="5min", price_aud_mwh=50.0 + i,
                )
            )
            db.session.add(
                EnergyDemand(
                    region="VIC1", interval_start=ts,
                    demand_mw=5000.0 + i * 10, demand_type="actual",
                )
            )
            for fuel, mw in (("brown_coal", 2000.0), ("solar_utility", 800.0), ("wind", 600.0)):
                db.session.add(
                    GenerationOutput(
                        region="VIC1", interval_start=ts,
                        fuel_type=fuel, output_mw=mw + i, capacity_mw=None,
                    )
                )
        db.session.commit()
        yield
        db.session.query(EnergyPrice).delete()
        db.session.query(EnergyDemand).delete()
        db.session.query(GenerationOutput).delete()
        db.session.commit()


# --- Auth ------------------------------------------------------------------

def test_timeseries_requires_token(client):
    resp = client.get("/api/v1/energy/timeseries/price?range=24h")
    assert resp.status_code == 401


def test_timeseries_price_shape(client, seeded):
    resp = client.get("/api/v1/energy/timeseries/price?range=24h&interval=1h", headers=AUTH)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["region"] == "VIC1"
    assert data["range"] == "24h"
    assert data["interval"] == "1h"
    assert isinstance(data["series"], list)
    assert data["series"]
    pt = data["series"][0]
    assert "timestamp" in pt and "value" in pt


def test_timeseries_demand_shape(client, seeded):
    resp = client.get("/api/v1/energy/timeseries/demand?range=6h&interval=5min", headers=AUTH)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["interval"] == "5min"
    assert data["series"]
    assert {"timestamp", "value"} <= set(data["series"][0])


def test_timeseries_generation_series_per_bucket(client, seeded):
    resp = client.get("/api/v1/energy/timeseries/generation?range=6h&interval=1h", headers=AUTH)
    assert resp.status_code == 200
    data = resp.get_json()
    keys = {s["key"] for s in data["series"]}
    # brown_coal + solar + wind seeded.
    assert {"brown_coal", "solar", "wind"} <= keys
    for s in data["series"]:
        assert s["label"] and s["colour"].startswith("#")
        assert s["points"] and {"timestamp", "value"} <= set(s["points"][0])


def test_invalid_interval_falls_back_to_default(client, seeded):
    # 30d only allows 1h/1d; requesting 5min must fall back to default (1d).
    resp = client.get("/api/v1/energy/timeseries/price?range=30d&interval=5min", headers=AUTH)
    assert resp.status_code == 200
    assert resp.get_json()["interval"] == "1d"


def test_invalid_range_defaults_to_24h(client, seeded):
    resp = client.get("/api/v1/energy/timeseries/price?range=bogus", headers=AUTH)
    assert resp.status_code == 200
    assert resp.get_json()["range"] == "24h"


def test_empty_series_when_no_data(client, app):
    with app.app_context():
        db.session.query(EnergyPrice).delete()
        db.session.commit()
    resp = client.get("/api/v1/energy/timeseries/price?range=1h&interval=5min", headers=AUTH)
    assert resp.status_code == 200
    assert resp.get_json()["series"] == []


# --- Query helpers ---------------------------------------------------------

def test_resolve_interval():
    assert eq.resolve_interval("1h", "5min") == "5min"
    assert eq.resolve_interval("1h", "1d") == "5min"  # invalid -> default
    assert eq.resolve_interval("24h", None) == "1h"
    assert eq.resolve_interval("30d", "1h") == "1h"


def test_price_timeseries_hourly_aggregation(app, seeded):
    with app.app_context():
        now = datetime.now(timezone.utc)
        raw = eq.price_timeseries("VIC1", now - timedelta(hours=4), now, "5min")
        hourly = eq.price_timeseries("VIC1", now - timedelta(hours=4), now, "1h")
        assert len(raw) == 36
        # Hourly buckets are fewer than raw 5-min points.
        assert 0 < len(hourly) < len(raw)


def test_generation_timeseries_buckets_gas_and_solar(app):
    with app.app_context():
        db.session.query(GenerationOutput).delete()
        ts = datetime.now(timezone.utc).replace(microsecond=0)
        db.session.add(GenerationOutput(region="VIC1", interval_start=ts, fuel_type="gas_ccgt", output_mw=100.0))
        db.session.add(GenerationOutput(region="VIC1", interval_start=ts, fuel_type="gas_ocgt", output_mw=50.0))
        db.session.add(GenerationOutput(region="VIC1", interval_start=ts, fuel_type="solar_rooftop", output_mw=300.0))
        db.session.commit()
        series = eq.generation_timeseries("VIC1", ts - timedelta(minutes=10), ts + timedelta(minutes=10), "5min")
        by_key = {s["key"]: s for s in series}
        assert "gas" in by_key and "solar" in by_key
        # gas_ccgt + gas_ocgt summed into one gas bucket.
        assert by_key["gas"]["points"][0]["value"] == 150.0
        db.session.query(GenerationOutput).delete()
        db.session.commit()
