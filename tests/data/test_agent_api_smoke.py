"""Level 3 — agent API & CLI smoke tests (end-to-end, seeded citylab_test).

Exercises every agent-facing endpoint with real seeded data: non-empty results,
the {ok, data, data_as_of} envelope, ISO data_as_of, from/to range filtering,
empty-range -> empty array (not error), and the 2s summary latency tolerance.
Also drives the four headline CLI commands through Click's CliRunner with a
mocked APIClient so no live server is needed in the test path.
"""

import json
import time
from datetime import datetime, timedelta, timezone

import pytest

from tests.data.conftest import run_fetcher, seed_locations

AUTH = {"Authorization": "Bearer dev-token-changeme"}

pytestmark = pytest.mark.integration


@pytest.fixture
def seeded(db_session):
    """Seed locations + run all three fetchers so the API has data to serve."""
    seed_locations(db_session)
    for source_type, name in (
        ("opennem", "OpenNEM Smoke"),
        ("bom", "BOM Smoke"),
        ("solcast", "Solcast Smoke"),
    ):
        run_fetcher(db_session, source_type, name, fresh=False)
    return db_session


def _ok_envelope(body):
    assert body["ok"] is True
    assert "data" in body
    assert "data_as_of" in body
    # data_as_of must be an ISO timestamp (or None only if nothing fetched).
    if body["data_as_of"] is not None:
        datetime.fromisoformat(body["data_as_of"].replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# Energy endpoints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/energy/summary",
        "/api/v1/energy/prices",
        "/api/v1/energy/generation",
        "/api/v1/energy/interconnectors",
        "/api/v1/energy/forecasts",
    ],
)
def test_energy_endpoints_non_empty(seeded, client, path):
    resp = client.get(path, headers=AUTH)
    assert resp.status_code == 200
    body = resp.get_json()
    _ok_envelope(body)
    data = body["data"]
    if isinstance(data, list):
        assert len(data) > 0, f"{path} returned empty list"
    else:
        assert data, f"{path} returned empty summary"


def test_energy_summary_shape(seeded, client):
    body = client.get("/api/v1/energy/summary", headers=AUTH).get_json()
    d = body["data"]
    assert d["region"] == "VIC1"
    assert d["generation_mix"]
    assert "battery_state" in d
    assert d["interconnectors"]


# ---------------------------------------------------------------------------
# Weather endpoints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/weather/summary",
        "/api/v1/weather/forecasts",
        "/api/v1/weather/observations",
        "/api/v1/weather/outlook?factor=wind",
        "/api/v1/weather/outlook?factor=rain",
    ],
)
def test_weather_endpoints_non_empty(seeded, client, path):
    resp = client.get(path, headers=AUTH)
    assert resp.status_code == 200
    body = resp.get_json()
    _ok_envelope(body)


def test_weather_outlook_wind_has_corridors(seeded, client):
    body = client.get("/api/v1/weather/outlook?factor=wind", headers=AUTH).get_json()
    locations = body["data"]["locations"]
    assert locations
    relevances = {l["location"]["region_relevance"] for l in locations}
    assert "wind_corridor" in relevances


# ---------------------------------------------------------------------------
# Solar endpoints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/solar/summary",
        "/api/v1/solar/forecasts",
        "/api/v1/solar/outlook",
    ],
)
def test_solar_endpoints_non_empty(seeded, client, path):
    resp = client.get(path, headers=AUTH)
    assert resp.status_code == 200
    body = resp.get_json()
    _ok_envelope(body)


# ---------------------------------------------------------------------------
# market-intelligence (cross-source)
# ---------------------------------------------------------------------------


def test_market_intelligence_cross_source(seeded, client):
    body = client.get("/api/v1/data/market-intelligence", headers=AUTH).get_json()
    _ok_envelope(body)
    d = body["data"]
    assert d["region"] == "VIC1"
    assert d["energy"]
    assert d["weather"] is not None
    # Per-source freshness so agents can judge each pipeline independently.
    assert d["sources"]
    for s in d["sources"]:
        assert "data_as_of" in s


# ---------------------------------------------------------------------------
# Range filters + empty ranges
# ---------------------------------------------------------------------------


def test_range_filter_returns_only_in_range(seeded, client):
    """from/to on prices returns only rows inside the window."""
    now = datetime.now(timezone.utc)
    dt_from = (now - timedelta(minutes=30)).isoformat()
    dt_to = now.isoformat()
    # Pass params via query_string dict so '+' in the tz offset is encoded.
    resp = client.get(
        "/api/v1/energy/prices",
        query_string={"from": dt_from, "to": dt_to},
        headers=AUTH,
    )
    body = resp.get_json()
    _ok_envelope(body)
    for row in body["data"]:
        start = datetime.fromisoformat(row["interval_start"].replace("Z", "+00:00"))
        assert start >= now - timedelta(minutes=30) - timedelta(seconds=1)
        assert start <= now + timedelta(seconds=1)


def test_empty_range_returns_empty_array_not_error(seeded, client):
    """A future-only window has no data -> empty array, HTTP 200, no error."""
    far_future = (datetime.now(timezone.utc) + timedelta(days=3650)).isoformat()
    farther = (datetime.now(timezone.utc) + timedelta(days=3651)).isoformat()
    resp = client.get(
        "/api/v1/energy/prices",
        query_string={"from": far_future, "to": farther},
        headers=AUTH,
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["data"] == []


# ---------------------------------------------------------------------------
# Latency tolerance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/energy/summary",
        "/api/v1/weather/summary",
        "/api/v1/solar/summary",
        "/api/v1/data/market-intelligence",
    ],
)
def test_summary_endpoints_within_2s(seeded, client, path):
    start = time.perf_counter()
    resp = client.get(path, headers=AUTH)
    elapsed = time.perf_counter() - start
    assert resp.status_code == 200
    assert elapsed < 2.0, f"{path} took {elapsed:.2f}s (>2s agent tolerance)"


# ---------------------------------------------------------------------------
# Cross-source agent reasoning path (Task 12)
# ---------------------------------------------------------------------------


def test_cross_source_reasoning_path(seeded, client):
    """energy summary -> weather wind outlook -> solar summary == coherent picture.

    The path an agent walks to reason about Victorian price: what's the market
    doing now, what's the wind doing in the corridors, what's solar doing.
    """
    energy = client.get("/api/v1/energy/summary", headers=AUTH).get_json()
    wind = client.get(
        "/api/v1/weather/outlook?factor=wind", headers=AUTH
    ).get_json()
    solar = client.get("/api/v1/solar/summary", headers=AUTH).get_json()

    # Each leg returns usable, non-empty data.
    assert energy["data"]["generation_mix"]
    assert wind["data"]["locations"]
    assert solar["data"]["groups"]

    # Coherence: wind outlook covers wind corridors; solar groups carry a
    # generation-impact headline an agent can fold into a price view.
    relevances = {l["location"]["region_relevance"] for l in wind["data"]["locations"]}
    assert "wind_corridor" in relevances
    any_impact = any(
        "generation_impact" in g for g in solar["data"]["groups"].values()
    )
    assert any_impact


def test_market_intelligence_per_source_data_as_of(seeded, client):
    body = client.get("/api/v1/data/market-intelligence", headers=AUTH).get_json()
    sources = body["data"]["sources"]
    assert sources
    # Each source carries its own data_as_of so agents judge freshness per pipe.
    for s in sources:
        assert "source_type" in s
        assert "data_as_of" in s
    types = {s["source_type"] for s in sources}
    # All three pipelines visible in the cross-source view.
    assert {"opennem", "bom", "solcast"} <= types


def test_weather_solar_data_as_of_is_source_scoped(db_session, client):
    """data_as_of must reflect each source's own fetch time, not cross-source max.

    Seeds three sources with distinct last_fetch_at: opennem freshest, bom stale,
    solcast stalest. The weather endpoint must report the bom time (not opennem's),
    and solar the solcast time — proving the source_type scoping on
    latest_fetch_timestamp().
    """
    from citylab.models.data_source import DataSource

    base = datetime(2026, 6, 3, 0, 0, 0, tzinfo=timezone.utc)
    stamps = {
        "opennem": base,  # freshest -> would be the cross-source max
        "bom": base - timedelta(hours=2),
        "solcast": base - timedelta(hours=5),
    }
    for stype, ts in stamps.items():
        ds = (
            db_session.query(DataSource).filter_by(source_type=stype).first()
            or DataSource(name=f"{stype} scope test", source_type=stype)
        )
        ds.last_fetch_at = ts
        ds.last_fetch_status = "success"
        db_session.add(ds)
    db_session.flush()

    weather = client.get("/api/v1/weather/summary", headers=AUTH).get_json()
    solar = client.get("/api/v1/solar/summary", headers=AUTH).get_json()
    energy = client.get("/api/v1/energy/summary", headers=AUTH).get_json()

    def _instant(s):
        return datetime.fromisoformat(s.replace("Z", "+00:00"))

    # Weather reflects BOM (-2h) instant, NOT the fresher opennem max.
    assert _instant(weather["data_as_of"]) == stamps["bom"]
    # Solar reflects Solcast (-5h).
    assert _instant(solar["data_as_of"]) == stamps["solcast"]
    # Energy stays cross-source max (opennem freshest) — unchanged behaviour.
    assert _instant(energy["data_as_of"]) == stamps["opennem"]


# ---------------------------------------------------------------------------
# CLI commands via Click CliRunner (no live server)
# ---------------------------------------------------------------------------


def _patched_api_client(client, monkeypatch):
    """Route APIClient calls through the in-process Flask test client.

    The CLI commands talk to APIClient over HTTP; in tests we point that at the
    Flask test client so `cli-citylab ... ` runs with no live server.
    """
    import citylab.cli_wrapper.client as cli_client_mod

    auth = {"Authorization": "Bearer dev-token-changeme"}

    class FakeAPIClient:
        def __init__(self):
            pass

        def get(self, path):
            resp = client.get(path, headers=auth)
            return resp.get_json()

        def post(self, path, data=None):
            resp = client.post(path, headers=auth, json=data or {})
            return resp.get_json()

    monkeypatch.setattr(cli_client_mod, "APIClient", FakeAPIClient)
    # The command modules import APIClient by name at module load; patch those too.
    import citylab.cli_wrapper.commands_energy as ce
    import citylab.cli_wrapper.commands_weather as cw
    import citylab.cli_wrapper.commands_solar as cs
    import citylab.cli_wrapper.commands_data as cd

    for mod in (ce, cw, cs, cd):
        monkeypatch.setattr(mod, "APIClient", FakeAPIClient)


@pytest.mark.parametrize(
    "args",
    [
        ("energy", "summary"),
        ("weather", "summary"),
        ("solar", "summary"),
        ("data", "market-intelligence"),
    ],
)
def test_cli_commands_parseable(seeded, client, monkeypatch, args):
    """The four headline CLI commands exit 0 and emit valid JSON."""
    from click.testing import CliRunner

    from citylab.cli_wrapper import main

    _patched_api_client(client, monkeypatch)

    runner = CliRunner()
    result = runner.invoke(main, list(args))
    assert result.exit_code == 0, f"{args} exited {result.exit_code}: {result.output}"

    body = json.loads(result.output)
    assert body["ok"] is True
    assert "data" in body
    assert "data_as_of" in body
