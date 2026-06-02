"""Tests for BOM weather ingestion: models, seeding, fetcher, query, API."""

from datetime import datetime, timezone

import pytest

AUTH = {"Authorization": "Bearer dev-token-changeme"}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


def test_weather_models_to_dict(db_session):
    from citylab.models.weather import (
        WeatherForecast,
        WeatherLocation,
        WeatherObservation,
    )

    now = datetime.now(timezone.utc)
    loc = WeatherLocation(
        name="Test Loc",
        state="VIC",
        region_relevance="wind_corridor",
        latitude=-37.0,
        longitude=144.0,
    )
    db_session.add(loc)
    db_session.flush()

    fc = WeatherForecast(
        location_id=loc.id,
        issued_at=now,
        forecast_for=now,
        forecast_period="3hourly",
        temperature_c=14.5,
        wind_speed_kmh=40.0,
        rainfall_mm=2.0,
        rainfall_probability_pct=60.0,
    )
    obs = WeatherObservation(
        location_id=loc.id,
        observed_at=now,
        temperature_c=13.0,
        wind_speed_kmh=38.0,
        pressure_hpa=1012.0,
    )
    db_session.add_all([fc, obs])
    db_session.flush()

    assert loc.to_dict()["region_relevance"] == "wind_corridor"
    assert fc.to_dict()["wind_speed_kmh"] == 40.0
    assert fc.to_dict()["forecast_period"] == "3hourly"
    assert obs.to_dict()["pressure_hpa"] == 1012.0


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------


def test_seed_weather_locations_idempotent(db_session):
    from citylab.models.weather import WeatherLocation
    from citylab.services.ingestion.seed import seed_weather_locations

    first = seed_weather_locations()
    assert len(first) == 10
    count_after_first = db_session.query(WeatherLocation).count()

    second = seed_weather_locations()
    assert len(second) == 10
    count_after_second = db_session.query(WeatherLocation).count()

    # Idempotent: re-seeding does not duplicate rows.
    assert count_after_first == count_after_second

    relevances = {
        loc.region_relevance
        for loc in db_session.query(WeatherLocation).all()
    }
    assert "hydro_catchment" in relevances
    assert "wind_corridor" in relevances
    assert "demand_centre" in relevances


# ---------------------------------------------------------------------------
# Registry + Fetcher (synthetic fallback, no live network)
# ---------------------------------------------------------------------------


def test_bom_self_registered():
    from citylab.services.ingestion.bom import BOMFetcher
    from citylab.services.ingestion.registry import get_fetcher

    assert get_fetcher("bom") is BOMFetcher


def test_bom_fetcher_synthetic_lands_data(db_session):
    from citylab.models.data_source import DataSource
    from citylab.models.weather import WeatherForecast, WeatherObservation
    from citylab.services.ingestion.bom import BOMFetcher
    from citylab.services.ingestion.seed import seed_weather_locations

    seed_weather_locations()

    ds = db_session.query(DataSource).filter_by(name="BOM Test").first()
    if not ds:
        ds = DataSource(
            name="BOM Test",
            source_type="bom",
            base_url="http://127.0.0.1:1",  # unreachable -> synthetic fallback
            cron_expression="0 */3 * * *",
            config={"timeout_seconds": 1},
        )
        db_session.add(ds)
        db_session.flush()

    # Set last_fetch_at so we skip the 3-day backfill and keep the run small.
    ds.last_fetch_at = datetime.now(timezone.utc)
    db_session.flush()

    result = BOMFetcher(ds).run()
    assert result["ok"] is True
    assert result["rows"] > 0
    assert ds.last_fetch_status == "success"

    # One observation per location, plus forecasts.
    assert db_session.query(WeatherObservation).count() >= 10
    assert db_session.query(WeatherForecast).count() > 0


# ---------------------------------------------------------------------------
# Query service
# ---------------------------------------------------------------------------


def _seed_and_fetch(db_session):
    """Seed locations + run a synthetic BOM fetch so queries have data."""
    from citylab.models.data_source import DataSource
    from citylab.services.ingestion.bom import BOMFetcher
    from citylab.services.ingestion.seed import seed_weather_locations

    seed_weather_locations()
    ds = db_session.query(DataSource).filter_by(name="BOM QTest").first()
    if not ds:
        ds = DataSource(
            name="BOM QTest",
            source_type="bom",
            base_url="http://127.0.0.1:1",
            cron_expression="0 */3 * * *",
            config={"timeout_seconds": 1},
        )
        db_session.add(ds)
        db_session.flush()
    ds.last_fetch_at = datetime.now(timezone.utc)
    db_session.flush()
    BOMFetcher(ds).run()


def test_weather_query_summary_grouping(db_session):
    from citylab.services import weather_query as wq

    _seed_and_fetch(db_session)
    s = wq.summary()
    assert "groups" in s
    assert "hydro_catchments" in s["groups"]
    assert "wind_corridors" in s["groups"]
    # Each entry carries current + next_forecast scaffolding.
    sample = s["groups"]["hydro_catchments"][0]
    assert "location" in sample
    assert "current" in sample


def test_weather_query_outlook_factors(db_session):
    from citylab.services import weather_query as wq

    _seed_and_fetch(db_session)

    rain = wq.outlook("rain")
    assert rain["factor"] == "rain"
    assert len(rain["locations"]) > 0
    # Hydro catchments must appear in the rain outlook (the Basslink narrative).
    relevances = {l["location"]["region_relevance"] for l in rain["locations"]}
    assert "hydro_catchment" in relevances

    wind = wq.outlook("wind")
    assert wind["factor"] == "wind"
    relevances_w = {l["location"]["region_relevance"] for l in wind["locations"]}
    assert "wind_corridor" in relevances_w

    bad = wq.outlook("nonsense")
    assert bad["locations"] == []


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/weather/summary",
        "/api/v1/weather/forecasts",
        "/api/v1/weather/observations",
        "/api/v1/weather/outlook?factor=rain",
        "/api/v1/weather/outlook?factor=wind",
    ],
)
def test_weather_endpoints_envelope(client, path):
    resp = client.get(path, headers=AUTH)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert "data" in body
    assert "data_as_of" in body


def test_weather_endpoint_requires_token(client):
    resp = client.get("/api/v1/weather/summary")
    assert resp.status_code == 401
