"""Shared fixtures for the data ingestion test harness.

Reuses the top-level `app` / `db_session` fixtures (tests/conftest.py) — NO
ad-hoc DB connections. Provides:
  - load_fixture(source, name): load a recorded snapshot-dict JSON fixture,
    re-hydrating ISO datetime strings into aware datetimes so transform() sees
    the exact shape _synthetic() produces.
  - seeding helpers: DataSource rows + the WeatherLocation / SolarLocation rows
    the BOM/Solcast fetchers query.
  - run_fetcher(...): run a fetcher end-to-end against the seeded test DB.
"""

import json
import os
import re
from datetime import datetime, timedelta, timezone

import pytest

FIXTURE_ROOT = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(autouse=True)
def _mock_solcast_http(monkeypatch):
    """Intercept Solcast HTTP (no synthetic fallback) so offline runs get data.

    Only solcast.com.au URLs are mocked; opennem/bom keep their real (failing)
    requests to the unreachable test URL → their synthetic fallback path."""
    import requests

    real_get = requests.get
    base = datetime(2026, 6, 5, 0, 0, tzinfo=timezone.utc)

    def _items(key):
        return {key: [{
            "period_end": (base + timedelta(minutes=30 * (i + 1)))
                .strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
            "period": "PT30M", "ghi": 100.0 + i * 50, "dni": 80.0, "dhi": 20.0,
            "air_temp": 12.0, "cloud_opacity": 30.0,
        } for i in range(6)]}

    class _R:
        def __init__(self, p):
            self._p = p

        def raise_for_status(self):
            return None

        def json(self):
            return self._p

    def fake_get(*args, **kwargs):
        url = args[0] if args else kwargs.get("url", "")
        if "solcast.com.au" in url:
            return _R(_items("forecasts" if "forecast/" in url
                             else "estimated_actuals"))
        return real_get(*args, **kwargs)

    monkeypatch.setattr(requests, "get", fake_get)

# Matches ISO-8601 timestamps we serialised in the fixtures (with tz offset).
_ISO_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)?$"
)

# Keys whose string values are datetimes and must be re-hydrated.
_DT_KEYS = {
    "interval_start",
    "interval_end",
    "issued_at",
    "forecast_issued_at",
    "forecast_for",
    "observed_at",
    "as_of",
}


def _maybe_dt(key, value):
    if not isinstance(value, str):
        return value
    if key in _DT_KEYS and _ISO_RE.match(value):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    return value


def _rehydrate(obj):
    """Recursively convert ISO datetime strings under known keys to datetimes."""
    if isinstance(obj, dict):
        return {k: _rehydrate(_maybe_dt(k, v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_rehydrate(v) for v in obj]
    return obj


def load_fixture(source: str, name: str) -> dict:
    """Load a recorded snapshot fixture as a dict with datetimes re-hydrated.

    Raw JSON (datetimes still as strings) is also available via load_fixture_raw.
    """
    return _rehydrate(load_fixture_raw(source, name))


def load_fixture_raw(source: str, name: str) -> dict:
    """Load a recorded fixture verbatim (datetimes remain ISO strings)."""
    path = os.path.join(FIXTURE_ROOT, source, f"{name}.json")
    with open(path) as f:
        return json.load(f)


def load_fixture_meta(source: str, name: str) -> dict:
    """Load the companion .meta.json for a fixture."""
    path = os.path.join(FIXTURE_ROOT, source, f"{name}.meta.json")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def load_fixture_fn():
    """Expose load_fixture as a fixture for tests that prefer injection."""
    return load_fixture


# ---------------------------------------------------------------------------
# DB seeding helpers — all go through the existing db_session fixture.
# ---------------------------------------------------------------------------


def make_data_source(db_session, name, source_type, *, base_url=None, config=None,
                     fresh=True):
    """Create or reset a DataSource for a fetcher run.

    BaseFetcher.run() commits, so rows survive the rollback fixture; reuse by
    name to stay idempotent across tests. `fresh=False` leaves last_fetch_at so
    the synthetic backfill is skipped (smaller, faster runs).
    """
    from citylab.models.data_source import DataSource

    # In production the OpenNEM fetcher fails loud rather than fabricating data.
    # Tests deliberately point at an unreachable URL, so they opt into the
    # synthetic fallback to stay offline-safe — unless a test overrides it.
    # Solcast has no synthetic path: it needs a key + reset budget, and its
    # HTTP is intercepted by the _mock_solcast_http autouse fixture below.
    def _with_fallback(cfg):
        cfg = dict(cfg or {"timeout_seconds": 1})
        cfg.setdefault("allow_synthetic_fallback", True)
        if source_type == "solcast":
            cfg.setdefault("api_key", "test-solcast-key")
            cfg["forecast_request_budget"] = 1000
            cfg["live_request_budget"] = 1000
            cfg["forecast_requests_used"] = 0
            cfg["live_requests_used"] = 0
        return cfg

    # Solcast must hit a solcast.com.au URL so the mock intercepts it.
    default_url = (
        "https://api.solcast.com.au" if source_type == "solcast"
        else "http://127.0.0.1:1"  # unreachable -> synthetic (opennem/bom)
    )

    existing = db_session.query(DataSource).filter_by(name=name).first()
    if existing:
        existing.source_type = source_type
        existing.base_url = base_url or existing.base_url or default_url
        existing.config = (
            _with_fallback(config) if config is not None
            else _with_fallback(existing.config)
        )
        existing.last_fetch_status = "pending"
        existing.last_error = None
        if not fresh:
            existing.last_fetch_at = datetime.now(timezone.utc)
        db_session.flush()
        return existing

    ds = DataSource(
        name=name,
        source_type=source_type,
        base_url=base_url or default_url,
        cron_expression="*/5 * * * *",
        config=_with_fallback(config),
    )
    db_session.add(ds)
    db_session.flush()
    if not fresh:
        ds.last_fetch_at = datetime.now(timezone.utc)
        db_session.flush()
    return ds


def seed_locations(db_session):
    """Seed WeatherLocation + SolarLocation rows the BOM/Solcast fetchers query."""
    from citylab.services.ingestion.seed import (
        seed_solar_locations,
        seed_weather_locations,
    )

    weather = seed_weather_locations()
    solar = seed_solar_locations()
    return {"weather": weather, "solar": solar}


def run_fetcher(db_session, source_type, name, *, seed=False, fresh=False):
    """Run a fetcher end-to-end against the seeded test DB; return its result.

    seed=True first seeds locations (required for BOM/Solcast). fresh=False
    (default) sets last_fetch_at so we ingest a small incremental window rather
    than the multi-day backfill — keeps the suite fast.
    """
    from citylab.services.ingestion.registry import get_fetcher

    if seed:
        seed_locations(db_session)

    ds = make_data_source(db_session, name, source_type, fresh=fresh)
    fetcher_cls = get_fetcher(source_type)
    assert fetcher_cls is not None, f"no fetcher registered for {source_type}"
    result = fetcher_cls(ds).run()
    return ds, result


@pytest.fixture
def seeded_pipeline(db_session):
    """Seed locations and run all three fetchers once; yield the source rows.

    Gives Level 2/3 tests a populated citylab_test to query without each test
    re-seeding. fresh=False keeps the incremental window small.
    """
    seed_locations(db_session)
    sources = {}
    for source_type, name in (
        ("opennem", "OpenNEM Harness"),
        ("bom", "BOM Harness"),
        ("solcast", "Solcast Harness"),
    ):
        ds, result = run_fetcher(db_session, source_type, name, fresh=False)
        sources[source_type] = {"data_source": ds, "result": result}
    return sources
