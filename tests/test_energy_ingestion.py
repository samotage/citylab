"""Tests for energy market data ingestion: models, registry, fetcher, APIs."""

from datetime import datetime, timezone

import pytest

AUTH = {"Authorization": "Bearer dev-token-changeme"}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


def test_data_source_to_dict_redacts_secrets(db_session):
    from citylab.models.data_source import DataSource

    ds = DataSource(
        name="Test Source",
        source_type="opennem",
        base_url="https://example.com",
        config={"api_key": "supersecret", "timeout_seconds": 8},
        cron_expression="*/5 * * * *",
    )
    db_session.add(ds)
    db_session.flush()
    d = ds.to_dict()
    assert d["name"] == "Test Source"
    assert d["source_type"] == "opennem"
    assert d["config"]["api_key"] == "***"  # redacted
    assert d["config"]["timeout_seconds"] == 8


def test_energy_models_to_dict(db_session):
    from citylab.models.energy import (
        EnergyDemand,
        EnergyPrice,
        GenerationOutput,
        GeneratorSubmission,
        InterconnectorFlow,
        PriceForecast,
    )

    now = datetime.now(timezone.utc)
    p = EnergyPrice(region="VIC1", interval_start=now, price_aud_mwh=85.5)
    d = EnergyDemand(region="VIC1", interval_start=now, demand_mw=5500.0)
    g = GenerationOutput(
        region="VIC1", interval_start=now, fuel_type="brown_coal", output_mw=3200.0
    )
    ic = InterconnectorFlow(
        interconnector_id="V-SA",
        from_region="VIC1",
        to_region="SA1",
        interval_start=now,
        flow_mw=400.0,
    )
    sub = GeneratorSubmission(
        station_name="Loy Yang A",
        unit_id="LYA1",
        region="VIC1",
        interval_start=now,
        bid_band=1,
        price_aud_mwh=-50.0,
        volume_mw=500.0,
    )
    fc = PriceForecast(
        region="VIC1",
        forecast_issued_at=now,
        forecast_for=now,
        price_aud_mwh=90.0,
    )
    for rec in (p, d, g, ic, sub, fc):
        db_session.add(rec)
    db_session.flush()

    assert p.to_dict()["price_aud_mwh"] == 85.5
    assert d.to_dict()["demand_mw"] == 5500.0
    assert g.to_dict()["fuel_type"] == "brown_coal"
    assert ic.to_dict()["interconnector_id"] == "V-SA"
    assert sub.to_dict()["bid_band"] == 1
    assert fc.to_dict()["forecast_type"] == "predispatch_30min"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def test_registry_register_and_lookup():
    from citylab.services.ingestion.registry import (
        get_fetcher,
        register_fetcher,
        registered_source_types,
    )

    class Dummy:
        pass

    register_fetcher("dummy_test_src", Dummy)
    assert get_fetcher("dummy_test_src") is Dummy
    assert "dummy_test_src" in registered_source_types()
    assert get_fetcher("nonexistent_src") is None


def test_opennem_self_registered():
    from citylab.services.ingestion.opennem import OpenNEMFetcher
    from citylab.services.ingestion.registry import get_fetcher

    assert get_fetcher("opennem") is OpenNEMFetcher


# ---------------------------------------------------------------------------
# BaseFetcher status update + retry (mocked, no live network)
# ---------------------------------------------------------------------------


def _make_source(db_session, name):
    """Create a DataSource with a unique name.

    BaseFetcher.run() commits, so rows persist past the rollback fixture —
    each test must use a unique name. Pre-existing rows are reused.
    """
    from citylab.models.data_source import DataSource

    existing = db_session.query(DataSource).filter_by(name=name).first()
    if existing:
        existing.last_fetch_status = "pending"
        existing.last_error = None
        db_session.flush()
        return existing
    ds = DataSource(
        name=name,
        source_type="custom",
        cron_expression="*/5 * * * *",
        config={},
    )
    db_session.add(ds)
    db_session.flush()
    return ds


def test_base_fetcher_success_updates_status(db_session, monkeypatch):
    from citylab.services.ingestion.base import BaseFetcher

    ds = _make_source(db_session, "Fetcher OK Src")

    class OKFetcher(BaseFetcher):
        source_type = "custom"

        def fetch(self):
            return {"v": 1}

        def transform(self, raw):
            return [raw]

        def store(self, records):
            return len(records)

    result = OKFetcher(ds).run()
    assert result["ok"] is True
    assert result["rows"] == 1
    assert result["attempts"] == 1
    assert ds.last_fetch_status == "success"
    assert ds.last_error is None
    assert ds.last_fetch_at is not None


def test_base_fetcher_retries_then_fails(db_session, monkeypatch):
    import citylab.services.ingestion.base as base_mod
    from citylab.services.ingestion.base import BaseFetcher

    # No real sleeping during retry backoff
    monkeypatch.setattr(base_mod.time, "sleep", lambda *_a, **_k: None)

    ds = _make_source(db_session, "Fetcher Fail Src")
    calls = {"n": 0}

    class FailFetcher(BaseFetcher):
        source_type = "custom"

        def fetch(self):
            calls["n"] += 1
            raise RuntimeError("boom")

        def transform(self, raw):
            return []

        def store(self, records):
            return 0

    result = FailFetcher(ds).run()
    assert result["ok"] is False
    assert result["attempts"] == base_mod.MAX_ATTEMPTS
    assert calls["n"] == base_mod.MAX_ATTEMPTS
    assert "boom" in result["error"]
    assert ds.last_fetch_status == "error"
    assert "boom" in ds.last_error


def test_opennem_fetcher_synthetic_run_lands_data(db_session):
    """OpenNEM fetcher falls back to synthetic data and persists rows."""
    from citylab.models.data_source import DataSource
    from citylab.models.energy import EnergyPrice
    from citylab.services.ingestion.opennem import OpenNEMFetcher

    ds = db_session.query(DataSource).filter_by(name="OpenNEM Test").first()
    if not ds:
        ds = DataSource(
            name="OpenNEM Test",
            source_type="opennem",
            base_url="http://127.0.0.1:1",  # unreachable -> forces synthetic fallback
            cron_expression="*/5 * * * *",
            # Opt into the synthetic fallback: production fails loud, but this
            # offline test exercises the demo-safety path explicitly.
            config={"timeout_seconds": 1, "allow_synthetic_fallback": True},
        )
        db_session.add(ds)
        db_session.flush()

    # last_fetch_at is None -> first run -> 7-day backfill. That's a lot of rows;
    # set last_fetch_at so we only ingest a small incremental window for speed.
    ds.last_fetch_at = datetime.now(timezone.utc)
    db_session.flush()

    result = OpenNEMFetcher(ds).run()
    assert result["ok"] is True
    assert result["rows"] > 0
    assert ds.last_fetch_status == "success"

    prices = db_session.query(EnergyPrice).filter_by(region="VIC1").count()
    assert prices > 0


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


def test_data_sources_endpoint_envelope(client):
    resp = client.get("/api/v1/data/sources", headers=AUTH)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert isinstance(body["data"], list)
    assert "data_as_of" in body


def test_market_intelligence_endpoint(client):
    resp = client.get("/api/v1/data/market-intelligence", headers=AUTH)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["data"]["region"] == "VIC1"
    assert "energy" in body["data"]
    assert "weather" in body["data"]  # placeholder until BOM exists
    assert "data_as_of" in body


def test_energy_summary_endpoint(client):
    resp = client.get("/api/v1/energy/summary", headers=AUTH)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["data"]["region"] == "VIC1"
    assert "generation_mix" in body["data"]
    assert "battery_state" in body["data"]
    assert "interconnectors" in body["data"]
    assert "data_as_of" in body


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/energy/prices",
        "/api/v1/energy/generation",
        "/api/v1/energy/interconnectors",
        "/api/v1/energy/forecasts",
    ],
)
def test_energy_list_endpoints_envelope(client, path):
    resp = client.get(path, headers=AUTH)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert isinstance(body["data"], list)
    assert "data_as_of" in body


def test_energy_endpoint_requires_token(client):
    resp = client.get("/api/v1/energy/summary")
    assert resp.status_code == 401
