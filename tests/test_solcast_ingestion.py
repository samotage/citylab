"""Tests for Solcast solar ingestion: models, seeding, fetcher, query, API, CLI."""

from datetime import datetime, timezone

import pytest

AUTH = {"Authorization": "Bearer dev-token-changeme"}


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
# Seeding
# ---------------------------------------------------------------------------


def test_seed_solar_locations_idempotent(db_session):
    from citylab.models.solar import SolarLocation
    from citylab.services.ingestion.seed import seed_solar_locations

    first = seed_solar_locations()
    assert len(first) == 6
    count_after_first = db_session.query(SolarLocation).count()

    second = seed_solar_locations()
    assert len(second) == 6
    count_after_second = db_session.query(SolarLocation).count()

    assert count_after_first == count_after_second

    relevances = {
        loc.region_relevance for loc in db_session.query(SolarLocation).all()
    }
    assert "utility_solar" in relevances
    assert "rooftop_aggregate" in relevances
    assert "hybrid_zone" in relevances


# ---------------------------------------------------------------------------
# Registry + Fetcher (synthetic fallback, no live network)
# ---------------------------------------------------------------------------


def test_solcast_self_registered():
    from citylab.services.ingestion.registry import get_fetcher
    from citylab.services.ingestion.solcast import SolcastFetcher

    assert get_fetcher("solcast") is SolcastFetcher


def _make_ds(db_session, name):
    from citylab.models.data_source import DataSource

    ds = db_session.query(DataSource).filter_by(name=name).first()
    if not ds:
        ds = DataSource(
            name=name,
            source_type="solcast",
            base_url="http://127.0.0.1:1",  # unreachable -> synthetic fallback
            cron_expression="0 * * * *",
            config={"timeout_seconds": 1, "api_key": "${SOLCAST_API_KEY}"},
        )
        db_session.add(ds)
        db_session.flush()
    # Set last_fetch_at so we skip the 3-day backfill and keep the run small.
    ds.last_fetch_at = datetime.now(timezone.utc)
    db_session.flush()
    return ds


def test_solcast_fetcher_synthetic_lands_data(db_session):
    from citylab.models.solar import SolarForecast
    from citylab.services.ingestion.seed import seed_solar_locations
    from citylab.services.ingestion.solcast import SolcastFetcher

    seed_solar_locations()
    ds = _make_ds(db_session, "Solcast Test")

    result = SolcastFetcher(ds).run()
    assert result["ok"] is True
    assert result["rows"] > 0
    assert ds.last_fetch_status == "success"
    assert db_session.query(SolarForecast).count() > 0


def test_solcast_synthetic_irradiance_diurnal(db_session):
    """GHI must be non-negative, zero at night, positive at solar noon."""
    from citylab.services.ingestion.seed import seed_solar_locations
    from citylab.services.ingestion.solcast import SolcastFetcher

    seed_solar_locations()
    ds = _make_ds(db_session, "Solcast Diurnal Test")

    fetcher = SolcastFetcher(ds)
    raw = fetcher.fetch()
    rows = []
    for block in raw["locations"]:
        rows.extend(block["forecasts"])

    assert rows
    ghis = [r["ghi_wm2"] for r in rows]
    # Non-negative everywhere.
    assert all(g >= 0 for g in ghis)
    # Some night-time zeros and some daytime positives exist over 24h+ horizon.
    assert any(g == 0 for g in ghis)
    assert any(g > 0 for g in ghis)

    # Solar-noon-ish (UTC ~02:00, i.e. ~12:00 local AEST) should be bright;
    # midnight local (~14:00 UTC) should be dark.
    noon_factor = SolcastFetcher._solar_elevation_factor(
        datetime(2026, 6, 3, 2, 0, tzinfo=timezone.utc)
    )
    night_factor = SolcastFetcher._solar_elevation_factor(
        datetime(2026, 6, 3, 14, 0, tzinfo=timezone.utc)
    )
    assert noon_factor > 0.5
    assert night_factor == 0.0


# ---------------------------------------------------------------------------
# Query service
# ---------------------------------------------------------------------------


def _seed_and_fetch(db_session):
    from citylab.services.ingestion.seed import seed_solar_locations
    from citylab.services.ingestion.solcast import SolcastFetcher

    seed_solar_locations()
    ds = _make_ds(db_session, "Solcast QTest")
    SolcastFetcher(ds).run()


def test_solar_query_summary(db_session):
    from citylab.services import solar_query as sq

    _seed_and_fetch(db_session)
    s = sq.summary()
    assert "groups" in s
    assert "utility_solar_regions" in s["groups"]
    grp = s["groups"]["utility_solar_regions"]
    assert "locations" in grp
    assert "generation_impact" in grp
    sample = grp["locations"][0]
    assert "location" in sample
    assert "next_24h" in sample


def test_solar_query_outlook(db_session):
    from citylab.services import solar_query as sq

    _seed_and_fetch(db_session)
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

    _seed_and_fetch(db_session)
    res = sq.query_forecasts(location="mildura")
    assert len(res) == 1
    assert "mildura" in res[0]["location"]["name"].lower()
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
