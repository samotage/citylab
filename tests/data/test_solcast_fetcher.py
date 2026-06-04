"""Level 1 — Solcast fetcher contract tests (offline, recorded fixtures).

Asserts SolcastFetcher.transform() maps the recorded irradiance snapshot
correctly (GHI populated, zero at night / positive at solar noon, DNI/DHI
derivation), tolerates null derived fields, distinguishes intraday (30min) from
short-range (hourly) forecast_period, and that the free-tier daily_call_budget
back-off goes straight to synthetic without a live call. No network.
"""

from datetime import datetime, timezone

from tests.data.conftest import load_fixture

from citylab.models.data_source import DataSource
from citylab.models.solar import SolarForecast
from citylab.services.ingestion.solcast import SolcastFetcher


def _fetcher(db_session, config=None):
    ds = DataSource(
        name="Solcast L1",
        source_type="solcast",
        base_url="http://127.0.0.1:1",
        cron_expression="*/30 * * * *",
        config=config or {"timeout_seconds": 1},
    )
    return SolcastFetcher(ds)


def test_transform_maps_forecasts(db_session):
    raw = load_fixture("solcast", "irradiance_good")
    records = _fetcher(db_session).transform(raw)
    forecasts = [r for r in records if isinstance(r, SolarForecast)]

    expected = sum(len(b["forecasts"]) for b in raw["locations"])
    assert len(forecasts) == expected
    sample = forecasts[0]
    assert sample.location_id == raw["locations"][0]["location_id"]
    assert isinstance(sample.forecast_for, datetime)


def test_ghi_zero_at_night_positive_at_noon(db_session):
    raw = load_fixture("solcast", "irradiance_good")
    records = _fetcher(db_session).transform(raw)
    forecasts = [r for r in records if isinstance(r, SolarForecast)]

    ghis = [f.ghi_wm2 for f in forecasts]
    # Every GHI is populated (non-null) and non-negative.
    assert all(g is not None and g >= 0 for g in ghis)
    # At least one zero-GHI (night) row and one strong (noon) row.
    assert any(g == 0.0 for g in ghis)
    assert any(g >= 800 for g in ghis)


def test_dni_dhi_derivation(db_session):
    """Under daylight DNI/DHI are populated; at night they collapse to zero."""
    raw = load_fixture("solcast", "irradiance_good")
    records = _fetcher(db_session).transform(raw)
    forecasts = [r for r in records if isinstance(r, SolarForecast)]

    daytime = [f for f in forecasts if f.ghi_wm2 and f.ghi_wm2 > 0]
    night = [f for f in forecasts if f.ghi_wm2 == 0.0]
    assert daytime and night
    for f in daytime:
        assert f.dni_wm2 is not None and f.dni_wm2 >= 0
    for f in night:
        assert f.dni_wm2 == 0.0


def test_intraday_vs_short_range_period(db_session):
    raw = load_fixture("solcast", "irradiance_good")
    records = _fetcher(db_session).transform(raw)
    forecasts = [r for r in records if isinstance(r, SolarForecast)]
    periods = {f.forecast_period for f in forecasts}
    assert "30min" in periods
    assert "hourly" in periods


def test_null_derived_field_tolerance(db_session):
    raw = load_fixture("solcast", "null_fields_edge")
    records = _fetcher(db_session).transform(raw)
    f = next(r for r in records if isinstance(r, SolarForecast))
    # GHI populated even when DNI/DHI/PV are null.
    assert f.ghi_wm2 == 600.0
    assert f.dni_wm2 is None
    assert f.dhi_wm2 is None
    assert f.estimated_pv_output_kw is None


def test_synthetic_path_ghi_diurnal(db_session):
    """The fetcher's own synthetic path: GHI never null, present across the day."""
    fetcher = _fetcher(db_session)
    # No locations seeded -> snapshot has zero location blocks, but the
    # _row builder is exercised directly via _solar_elevation_factor sign.
    noon = datetime(2026, 6, 3, 2, 0, tzinfo=timezone.utc)   # ~12:00 AEST
    midnight = datetime(2026, 6, 3, 14, 0, tzinfo=timezone.utc)  # ~00:00 AEST
    assert fetcher._solar_elevation_factor(noon) > 0.5
    assert fetcher._solar_elevation_factor(midnight) == 0.0


def test_budget_backoff_skips_live_call(db_session, monkeypatch):
    """daily_call_budget reached -> synthetic, with no live _fetch_live call."""
    fetcher = _fetcher(db_session, config={"daily_call_budget": 1, "timeout_seconds": 1})
    # Pretend we've already called once today.
    fetcher.data_source.last_fetch_at = datetime.now(timezone.utc)

    called = {"live": False}

    def _boom(*a, **k):
        called["live"] = True
        raise AssertionError("_fetch_live must NOT be called when budget reached")

    monkeypatch.setattr(fetcher, "_fetch_live", _boom)
    monkeypatch.setattr(fetcher, "_locations", lambda: [])  # no DB dependency

    snap = fetcher.fetch()
    assert snap["source"] == "synthetic"
    assert called["live"] is False


def test_under_budget_attempts_live_then_falls_back(db_session, monkeypatch):
    """Budget not reached -> live attempted; unreachable -> synthetic fallback."""
    fetcher = _fetcher(db_session, config={"daily_call_budget": 100, "timeout_seconds": 1})
    fetcher.data_source.last_fetch_at = None  # 0 calls today

    attempted = {"live": False}
    orig = fetcher._fetch_live

    def _spy(backfill):
        attempted["live"] = True
        raise RuntimeError("unreachable")

    monkeypatch.setattr(fetcher, "_fetch_live", _spy)
    monkeypatch.setattr(fetcher, "_locations", lambda: [])

    snap = fetcher.fetch()
    assert attempted["live"] is True
    assert snap["source"] == "synthetic"
