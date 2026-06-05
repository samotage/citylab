"""Level 2 — pipeline integration tests (citylab_test).

For each source: seed a DataSource (+ locations), run the fetcher end-to-end via
the registry, and assert data lands in the right tables, FKs resolve, timestamps
parse, row counts are non-trivial (no silent loss), and DataSource status columns
update. Exercises registry wiring: lookup by source_type -> run -> verify rows.
"""

from datetime import datetime, timedelta, timezone

import pytest

from tests.data.conftest import run_fetcher, seed_locations

from citylab.models.energy import (
    EnergyPrice,
    GenerationOutput,
    InterconnectorFlow,
    PriceForecast,
)
from citylab.models.solar import SolarForecast, SolarLocation
from citylab.models.weather import (
    WeatherForecast,
    WeatherLocation,
    WeatherObservation,
)
from citylab.services.ingestion.registry import get_fetcher

pytestmark = pytest.mark.integration


def _aware(dt):
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Registry wiring
# ---------------------------------------------------------------------------


def test_registry_resolves_all_three_sources():
    for source_type in ("opennem", "bom", "solcast"):
        cls = get_fetcher(source_type)
        assert cls is not None
        assert cls.source_type == source_type


# ---------------------------------------------------------------------------
# OpenNEM
# ---------------------------------------------------------------------------


def test_opennem_pipeline_lands_data(db_session):
    ds, result = run_fetcher(db_session, "opennem", "OpenNEM Pipeline", fresh=False)

    assert result["ok"] is True
    assert result["rows"] > 0

    prices = db_session.query(EnergyPrice).filter_by(region="VIC1").all()
    gens = db_session.query(GenerationOutput).filter_by(region="VIC1").all()
    flows = db_session.query(InterconnectorFlow).all()
    forecasts = db_session.query(PriceForecast).filter_by(region="VIC1").all()

    assert prices and gens and flows and forecasts
    # Timestamps parsed into real datetimes.
    assert isinstance(prices[0].interval_start, datetime)
    # Forecasts look forward relative to when issued.
    fc = forecasts[0]
    assert _aware(fc.forecast_for) > _aware(fc.forecast_issued_at)

    # Status columns updated.
    assert ds.last_fetch_status == "success"
    assert ds.last_fetch_at is not None
    assert ds.last_error is None


# ---------------------------------------------------------------------------
# BOM
# ---------------------------------------------------------------------------


def test_bom_pipeline_lands_data_with_fk_resolution(db_session):
    ds, result = run_fetcher(db_session, "bom", "BOM Pipeline", seed=True, fresh=False)

    assert result["ok"] is True
    assert result["rows"] > 0

    forecasts = db_session.query(WeatherForecast).all()
    observations = db_session.query(WeatherObservation).all()
    assert forecasts and observations

    # FK resolution: every forecast/observation points at a real location.
    location_ids = {
        l.id for l in db_session.query(WeatherLocation).all()
    }
    assert all(f.location_id in location_ids for f in forecasts)
    assert all(o.location_id in location_ids for o in observations)
    # One observation per seeded location (10).
    assert len({o.location_id for o in observations}) == 10

    assert ds.last_fetch_status == "success"


# ---------------------------------------------------------------------------
# Solcast
# ---------------------------------------------------------------------------


def _mock_solcast(monkeypatch):
    """Mock requests.get with Solcast-shaped forecast + live payloads (no network)."""
    base = datetime(2026, 6, 5, 0, 0, tzinfo=timezone.utc)

    def _items(key):
        return {key: [{
            "period_end": (base + timedelta(minutes=30 * (i + 1)))
                .strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
            "period": "PT30M", "ghi": 100.0 + i * 50, "dni": 80.0, "dhi": 20.0,
            "air_temp": 12.0, "cloud_opacity": 30.0,
        } for i in range(4)]}

    class _R:
        def __init__(self, p):
            self._p = p

        def raise_for_status(self):
            return None

        def json(self):
            return self._p

    def fake_get(url, params=None, headers=None, timeout=None):
        return _R(_items("forecasts" if "forecast/" in url else "estimated_actuals"))

    import requests
    monkeypatch.setattr(requests, "get", fake_get)


def test_solcast_pipeline_lands_data_with_fk_resolution(db_session, monkeypatch):
    from tests.data.conftest import make_data_source

    seed_locations(db_session)
    _mock_solcast(monkeypatch)
    ds = make_data_source(
        db_session, "Solcast Pipeline", "solcast", fresh=False,
        config={"api_key": "test-key", "timeout_seconds": 5},
    )
    result = get_fetcher("solcast")(ds).run()

    assert result["ok"] is True
    assert result["rows"] > 0

    forecasts = db_session.query(SolarForecast).all()
    assert forecasts

    location_ids = {l.id for l in db_session.query(SolarLocation).all()}
    assert all(f.location_id in location_ids for f in forecasts)
    # GHI populated on every row.
    assert all(f.ghi_wm2 is not None for f in forecasts)

    assert ds.last_fetch_status == "success"


# ---------------------------------------------------------------------------
# No silent loss: rows == records produced by transform()
# ---------------------------------------------------------------------------


def test_no_silent_row_loss_solcast(db_session, monkeypatch):
    """store() must persist exactly the rows transform() produced."""
    from tests.data.conftest import make_data_source

    seed_locations(db_session)
    _mock_solcast(monkeypatch)
    ds = make_data_source(
        db_session, "Solcast NoLoss", "solcast", fresh=False,
        config={"api_key": "test-key", "timeout_seconds": 5},
    )
    fetcher = get_fetcher("solcast")(ds)

    raw = fetcher.fetch()
    records = fetcher.transform(raw)
    stored = fetcher.store(records)
    assert stored == len(records)
