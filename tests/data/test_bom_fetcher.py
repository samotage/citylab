"""Level 1 — BOM fetcher contract tests (offline, recorded fixtures).

Asserts BOMFetcher.transform() maps the recorded forecast + observation snapshot
correctly, distinguishes short-range (3hourly) from daily forecast_period, keeps
temperature + wind populated, and tolerates missing optional fields. No network.
"""

from datetime import datetime

from tests.data.conftest import load_fixture

from citylab.models.data_source import DataSource
from citylab.models.weather import WeatherForecast, WeatherObservation
from citylab.services.ingestion.bom import BOMFetcher


def _fetcher(db_session):
    ds = DataSource(
        name="BOM L1",
        source_type="bom",
        base_url="http://127.0.0.1:1",
        cron_expression="0 */3 * * *",
        config={"timeout_seconds": 1},
    )
    return BOMFetcher(ds)


def test_transform_builds_forecasts_and_observations(db_session):
    raw = load_fixture("bom", "forecasts_observations_good")
    records = _fetcher(db_session).transform(raw)

    forecasts = [r for r in records if isinstance(r, WeatherForecast)]
    observations = [r for r in records if isinstance(r, WeatherObservation)]

    expected_fc = sum(len(b["forecasts"]) for b in raw["locations"])
    expected_obs = sum(1 for b in raw["locations"] if b.get("observation"))
    assert len(forecasts) == expected_fc
    assert len(observations) == expected_obs


def test_short_range_vs_daily_period_handling(db_session):
    raw = load_fixture("bom", "forecasts_observations_good")
    records = _fetcher(db_session).transform(raw)
    forecasts = [r for r in records if isinstance(r, WeatherForecast)]

    periods = {f.forecast_period for f in forecasts}
    assert "3hourly" in periods
    assert "daily" in periods

    short = [f for f in forecasts if f.forecast_period == "3hourly"]
    daily = [f for f in forecasts if f.forecast_period == "daily"]

    # Short-range carries a single temperature_c; daily carries min/max.
    assert all(f.temperature_c is not None for f in short)
    assert all(
        f.temperature_min_c is not None and f.temperature_max_c is not None
        for f in daily
    )


def test_temperature_and_wind_populated(db_session):
    raw = load_fixture("bom", "forecasts_observations_good")
    records = _fetcher(db_session).transform(raw)
    forecasts = [r for r in records if isinstance(r, WeatherForecast)]

    for f in forecasts:
        # Every forecast has wind and at least one temperature field.
        assert f.wind_speed_kmh is not None
        has_temp = (
            f.temperature_c is not None
            or (f.temperature_min_c is not None and f.temperature_max_c is not None)
        )
        assert has_temp


def test_observation_field_mapping(db_session):
    raw = load_fixture("bom", "forecasts_observations_good")
    records = _fetcher(db_session).transform(raw)
    obs = next(r for r in records if isinstance(r, WeatherObservation))
    src = raw["locations"][0]["observation"]

    assert obs.location_id == src["location_id"]
    assert obs.temperature_c == src["temperature_c"]
    assert obs.wind_speed_kmh == src["wind_speed_kmh"]
    assert obs.pressure_hpa == src["pressure_hpa"]
    assert isinstance(obs.observed_at, datetime)


def test_missing_field_tolerance(db_session):
    """A location with null observation + forecast null optionals must not crash."""
    raw = load_fixture("bom", "null_fields_edge")
    records = _fetcher(db_session).transform(raw)

    forecasts = [r for r in records if isinstance(r, WeatherForecast)]
    observations = [r for r in records if isinstance(r, WeatherObservation)]

    assert len(forecasts) == 1
    # observation was null -> no WeatherObservation produced.
    assert observations == []
    # Null optionals survive as None; required fields stay populated.
    f = forecasts[0]
    assert f.temperature_c == 10.0
    assert f.wind_direction is None
    assert f.rainfall_mm is None
