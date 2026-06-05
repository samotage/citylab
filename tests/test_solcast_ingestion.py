"""Tests for Solcast solar ingestion: models, seeding, fetcher, query, API, CLI.

The fetcher now hits the REAL Solcast API — these tests mock `requests.get` so
they never make a network call or consume the metered request budget.
"""

from datetime import datetime, timedelta, timezone

import pytest

AUTH = {"Authorization": "Bearer dev-token-changeme"}


@pytest.fixture(autouse=True)
def _clean_solar(db_session):
    """Clear solar_forecasts before each test.

    The test fixture rolls back via SAVEPOINT, but fetcher run()/seed commit()
    calls escape it and persist into citylab_test. Clearing forecasts (txn-local)
    gives every test a clean slate so absolute counts and the unique constraint
    behave deterministically regardless of prior tests/runs."""
    from citylab.models.solar import SolarForecast

    db_session.query(SolarForecast).delete()
    db_session.flush()
    yield


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


def test_solar_models_to_dict(db_session):
    from citylab.models.solar import SolarForecast, SolarLocation

    now = datetime.now(timezone.utc)
    loc = SolarLocation(
        name="Test Solar Loc",
        state="VIC",
        region_relevance="utility_solar",
        latitude=-34.0,
        longitude=142.0,
        reference_pv_capacity_kw=100000.0,
    )
    db_session.add(loc)
    db_session.flush()

    fc = SolarForecast(
        location_id=loc.id,
        issued_at=now,
        forecast_for=now,
        forecast_period="30min",
        ghi_wm2=850.0,
        dni_wm2=600.0,
        dhi_wm2=200.0,
        cloud_opacity_pct=15.0,
        air_temp_c=24.0,
        estimated_pv_output_kw=85000.0,
    )
    db_session.add(fc)
    db_session.flush()

    assert loc.to_dict()["region_relevance"] == "utility_solar"
    assert loc.to_dict()["reference_pv_capacity_kw"] == 100000.0
    assert fc.to_dict()["ghi_wm2"] == 850.0
    assert fc.to_dict()["forecast_period"] == "30min"


# ---------------------------------------------------------------------------
# Seeding — single real Melbourne CBD location
# ---------------------------------------------------------------------------


def test_seed_solar_locations_single(db_session):
    from citylab.models.solar import SolarLocation
    from citylab.services.ingestion.seed import seed_solar_locations

    first = seed_solar_locations()
    assert len(first) == 1
    count_after_first = db_session.query(SolarLocation).count()

    # Idempotent.
    second = seed_solar_locations()
    assert len(second) == 1
    assert count_after_first == db_session.query(SolarLocation).count()

    loc = db_session.query(SolarLocation).one()
    assert "Melbourne" in loc.name
    assert loc.region_relevance == "rooftop_aggregate"
    assert loc.state == "VIC"


# ---------------------------------------------------------------------------
# Fetcher — REAL Solcast API (mocked), no synthetic fallback
# ---------------------------------------------------------------------------


def test_solcast_self_registered():
    from citylab.services.ingestion.registry import get_fetcher
    from citylab.services.ingestion.solcast import SolcastFetcher

    assert get_fetcher("solcast") is SolcastFetcher


def _make_ds(db_session, name, *, api_key="test-solcast-key", used_fc=0,
             used_live=0, budget=10):
    from citylab.models.data_source import DataSource

    ds = db_session.query(DataSource).filter_by(name=name).first()
    if not ds:
        ds = DataSource(
            name=name,
            source_type="solcast",
            base_url="https://api.solcast.com.au",
            cron_expression="0 * * * *",
            is_active=False,
            config={
                "timeout_seconds": 5,
                "api_key": api_key,
                "period": "PT30M",
                "output_parameters": ["ghi", "dni", "dhi", "air_temp",
                                      "cloud_opacity"],
                "forecast_request_budget": budget,
                "live_request_budget": budget,
                "forecast_requests_used": used_fc,
                "live_requests_used": used_live,
            },
        )
        db_session.add(ds)
        db_session.flush()
    ds.last_fetch_at = datetime.now(timezone.utc)
    db_session.flush()
    return ds


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _periods(key, n=4):
    """Build a small Solcast-shaped series under `key` (forecasts/estimated_actuals)."""
    base = datetime(2026, 6, 5, 0, 0, tzinfo=timezone.utc)
    items = []
    for i in range(n):
        end = base + timedelta(minutes=30 * (i + 1))
        items.append({
            "period_end": end.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
            "period": "PT30M",
            "ghi": 100.0 + i * 50,
            "dni": 80.0 + i * 40,
            "dhi": 20.0 + i * 10,
            "air_temp": 12.0 + i,
            "cloud_opacity": 30.0,
        })
    return {key: items}


def _install_mock(monkeypatch, calls=None):
    def fake_get(url, params=None, headers=None, timeout=None):
        if calls is not None:
            calls.append(url)
        if "forecast/radiation_and_weather" in url:
            return _FakeResp(_periods("forecasts"))
        if "live/radiation_and_weather" in url:
            return _FakeResp(_periods("estimated_actuals"))
        raise AssertionError(f"unexpected Solcast URL: {url}")

    import requests
    monkeypatch.setattr(requests, "get", fake_get)


def test_solcast_real_fetch_mocked(db_session, monkeypatch):
    from citylab.models.solar import SolarForecast
    from citylab.services.ingestion.seed import seed_solar_locations
    from citylab.services.ingestion.solcast import SolcastFetcher

    seed_solar_locations()
    ds = _make_ds(db_session, "Solcast Real Test")
    calls = []
    _install_mock(monkeypatch, calls)

    result = SolcastFetcher(ds).run()

    assert result["ok"] is True
    assert result["rows"] == 8  # 4 forecast + 4 live for the one location
    assert ds.last_fetch_status == "success"
    # Exactly one forecast + one live HTTP call (no retries, one location).
    assert len(calls) == 2

    rows = db_session.query(SolarForecast).all()
    assert len(rows) == 8
    # Forecast rows: issued_at != forecast_for. Live rows: issued_at == forecast_for.
    assert any(r.issued_at != r.forecast_for for r in rows)
    assert any(r.issued_at == r.forecast_for for r in rows)
    # Real values mapped through.
    assert {r.ghi_wm2 for r in rows} == {100.0, 150.0, 200.0, 250.0}

    # Budget counters advanced and persisted.
    assert ds.config["forecast_requests_used"] == 1
    assert ds.config["live_requests_used"] == 1


def test_solcast_budget_guard_blocks_calls(db_session, monkeypatch):
    from citylab.services.ingestion.seed import seed_solar_locations
    from citylab.services.ingestion.solcast import SolcastFetcher

    seed_solar_locations()
    ds = _make_ds(db_session, "Solcast Exhausted", used_fc=10, used_live=10)
    calls = []
    _install_mock(monkeypatch, calls)

    result = SolcastFetcher(ds).run()

    assert result["ok"] is False
    assert "budget exhausted" in (result["error"] or "")
    assert calls == []  # no HTTP call attempted when budget is spent


def test_solcast_no_key_no_synthetic(db_session, monkeypatch):
    from citylab.models.solar import SolarForecast
    from citylab.services.ingestion.seed import seed_solar_locations
    from citylab.services.ingestion.solcast import SolcastFetcher

    monkeypatch.delenv("SOLCAST_API_KEY", raising=False)  # no env fallback
    seed_solar_locations()
    ds = _make_ds(db_session, "Solcast NoKey", api_key="${SOLCAST_API_KEY}")
    calls = []
    _install_mock(monkeypatch, calls)

    result = SolcastFetcher(ds).run()

    assert result["ok"] is False
    assert "no Solcast API key" in (result["error"] or "")
    assert calls == []
    # No synthetic data fabricated.
    assert db_session.query(SolarForecast).count() == 0


# ---------------------------------------------------------------------------
# Query service — seed one location + insert rows directly (no network)
# ---------------------------------------------------------------------------


def _seed_with_rows(db_session):
    from citylab.models.solar import SolarForecast
    from citylab.services.ingestion.seed import seed_solar_locations

    seed_solar_locations()
    from citylab.models.solar import SolarLocation

    loc = (
        db_session.query(SolarLocation)
        .filter(SolarLocation.name.ilike("%melbourne%"))
        .first()
    )
    issued = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    for i in range(48):  # 24h of 30-min forecasts
        target = issued + timedelta(minutes=30 * i)
        # crude diurnal: positive during the middle of the window
        ghi = max(0.0, 400.0 - abs(i - 24) * 15)
        db_session.add(SolarForecast(
            location_id=loc.id,
            issued_at=issued,
            forecast_for=target,
            forecast_period="30min",
            ghi_wm2=ghi,
            dni_wm2=ghi * 0.7,
            dhi_wm2=ghi * 0.3,
            cloud_opacity_pct=25.0,
            air_temp_c=14.0,
            estimated_pv_output_kw=ghi * 100,
        ))
    db_session.flush()
    return loc


def test_solar_query_summary(db_session):
    from citylab.services import solar_query as sq

    _seed_with_rows(db_session)
    s = sq.summary()
    assert "groups" in s
    assert "rooftop_aggregates" in s["groups"]
    grp = s["groups"]["rooftop_aggregates"]
    assert "locations" in grp
    assert "generation_impact" in grp
    sample = grp["locations"][0]
    assert "location" in sample
    assert "next_24h" in sample


def test_solar_query_outlook(db_session):
    from citylab.services import solar_query as sq

    _seed_with_rows(db_session)
    o = sq.outlook(days=3)
    assert o["days"] == 3
    assert len(o["locations"]) > 0
    sample = o["locations"][0]
    assert "daily" in sample
    assert len(sample["daily"]) > 0
    day = sample["daily"][0]
    assert "peak_ghi_wm2" in day
    assert "assessment" in day


def test_solar_query_resolve_by_name(db_session):
    from citylab.services import solar_query as sq

    _seed_with_rows(db_session)
    res = sq.query_forecasts(location="melbourne")
    assert len(res) == 1
    assert "melbourne" in res[0]["location"]["name"].lower()
    assert len(res[0]["forecasts"]) > 0


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/solar/summary",
        "/api/v1/solar/forecasts",
        "/api/v1/solar/outlook?days=3",
    ],
)
def test_solar_endpoints_envelope(client, path):
    resp = client.get(path, headers=AUTH)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert "data" in body
    assert "data_as_of" in body


def test_solar_endpoint_requires_token(client):
    resp = client.get("/api/v1/solar/summary")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# CLI registration
# ---------------------------------------------------------------------------


def test_solar_cli_group_registered():
    from citylab.cli_wrapper import main

    assert "solar" in main.commands
    sub = main.commands["solar"].commands
    assert {"summary", "outlook", "forecasts"} <= set(sub)
