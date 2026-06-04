"""Tests for historical backfill, upsert idempotency, and gap-fill.

Covers the historical-backfill-continuous-collection PRD:
  - upsert idempotency (running a fetcher twice doesn't double rows)
  - gap-fill (a last_fetch_at gap triggers fetch_range before the normal fetch)
  - backfill CLI happy path (chunked, idempotent)
  - Solcast fetch_range raises NotImplementedError
  - synthetic fallback still fires when the live API is unreachable

All DB access goes through the existing db_session fixture (citylab_test).
"""

from datetime import datetime, timedelta, timezone

import pytest

from tests.data.conftest import make_data_source, run_fetcher, seed_locations


def _count(db_session, model):
    return db_session.query(model).count()


# ---------------------------------------------------------------------------
# Upsert idempotency
# ---------------------------------------------------------------------------


def test_opennem_store_is_idempotent(db_session):
    """Running the OpenNEM fetcher twice must not double row counts."""
    from citylab.models.energy import EnergyPrice

    # First run (fresh=False -> small incremental window).
    run_fetcher(db_session, "opennem", "OpenNEM Upsert Test", fresh=False)
    db_session.commit()
    c1 = _count(db_session, EnergyPrice)

    # Second run over the same window -> upsert, no growth.
    ds = make_data_source(db_session, "OpenNEM Upsert Test", "opennem", fresh=False)
    from citylab.services.ingestion.registry import get_fetcher

    get_fetcher("opennem")(ds).run()
    db_session.commit()
    c2 = _count(db_session, EnergyPrice)

    assert c1 > 0
    assert c2 == c1, f"row count grew on re-run: {c1} -> {c2}"


def test_bom_store_is_idempotent(db_session):
    """Running the BOM fetcher twice must not double observation counts."""
    from citylab.models.weather import WeatherObservation
    from citylab.services.ingestion.registry import get_fetcher

    seed_locations(db_session)
    ds = make_data_source(db_session, "BOM Upsert Test", "bom", fresh=False)
    get_fetcher("bom")(ds).run()
    db_session.commit()
    c1 = _count(db_session, WeatherObservation)

    ds = make_data_source(db_session, "BOM Upsert Test", "bom", fresh=False)
    get_fetcher("bom")(ds).run()
    db_session.commit()
    c2 = _count(db_session, WeatherObservation)

    assert c1 > 0
    assert c2 == c1


# ---------------------------------------------------------------------------
# Synthetic fallback (live API unreachable)
# ---------------------------------------------------------------------------


def test_synthetic_fallback_fires_on_unreachable_api(db_session):
    """An unreachable base_url must fall back to synthetic, not crash."""
    ds = make_data_source(
        db_session,
        "OpenNEM Fallback Test",
        "opennem",
        base_url="http://127.0.0.1:1",  # unreachable
        config={"timeout_seconds": 1},
        fresh=False,
    )
    from citylab.services.ingestion.registry import get_fetcher

    fetcher = get_fetcher("opennem")(ds)
    raw = fetcher.fetch()
    assert raw["source"] == "synthetic"
    result = fetcher.run()
    assert result["ok"] is True


# ---------------------------------------------------------------------------
# Gap-fill
# ---------------------------------------------------------------------------


def test_gap_fill_triggers_fetch_range(db_session, monkeypatch):
    """A gap beyond 2x the interval calls fetch_range before the normal fetch."""
    from citylab.services.ingestion.registry import get_fetcher

    ds = make_data_source(
        db_session, "OpenNEM GapFill Test", "opennem", fresh=False
    )
    # Force a 2-hour-old last_fetch_at: well beyond the 10-min OpenNEM threshold,
    # within the 7-day cap.
    ds.last_fetch_at = datetime.now(timezone.utc) - timedelta(hours=2)
    db_session.flush()

    fetcher = get_fetcher("opennem")(ds)

    calls = {"range": 0}
    real_range = fetcher.fetch_range

    def spy_range(start, end, progress=None):
        calls["range"] += 1
        return real_range(start, end, progress)

    monkeypatch.setattr(fetcher, "fetch_range", spy_range)
    fetcher.run()
    db_session.commit()

    assert calls["range"] == 1, "gap-fill should have called fetch_range once"


def test_no_gap_fill_when_recent(db_session, monkeypatch):
    """No gap-fill when last_fetch_at is within the threshold."""
    from citylab.services.ingestion.registry import get_fetcher

    ds = make_data_source(
        db_session, "OpenNEM NoGap Test", "opennem", fresh=False
    )
    ds.last_fetch_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.flush()

    fetcher = get_fetcher("opennem")(ds)
    calls = {"range": 0}

    def spy_range(start, end, progress=None):
        calls["range"] += 1
        return fetcher._synthetic_range(start, end)

    monkeypatch.setattr(fetcher, "fetch_range", spy_range)
    fetcher.run()
    db_session.commit()

    assert calls["range"] == 0


# ---------------------------------------------------------------------------
# Backfill CLI
# ---------------------------------------------------------------------------


def test_backfill_opennem_happy_path_and_idempotent(db_session):
    """run_backfill writes rows over chunks and is idempotent on re-run.

    Cleans up the historical rows it inserts so it does not pollute other
    tests' whole-table freshness/gap queries (the rows are dated days ago).
    """
    from citylab.cli.commands import run_backfill
    from citylab.models.energy import (
        EnergyDemand,
        EnergyPrice,
        GenerationOutput,
        InterconnectorFlow,
    )

    # Ensure an opennem source exists.
    make_data_source(db_session, "OpenNEM Victorian NEM", "opennem", fresh=False)
    db_session.commit()

    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=2)
    window_start = datetime.combine(
        start, datetime.min.time(), tzinfo=timezone.utc
    )
    window_end = datetime.combine(end, datetime.min.time(), tzinfo=timezone.utc)

    try:
        r1 = run_backfill("opennem", start.isoformat(), end.isoformat(), 1)
        db_session.commit()
        assert r1["error"] is None
        assert r1["rows"] > 0
        assert r1["chunks"] == 2
        c1 = _count(db_session, EnergyPrice)

        r2 = run_backfill("opennem", start.isoformat(), end.isoformat(), 1)
        db_session.commit()
        assert r2["error"] is None
        c2 = _count(db_session, EnergyPrice)
        assert c2 == c1, f"backfill not idempotent: {c1} -> {c2}"
    finally:
        # Remove the historical rows this test committed.
        for model in (
            EnergyPrice, EnergyDemand, GenerationOutput, InterconnectorFlow,
        ):
            db_session.query(model).filter(
                model.interval_start >= window_start,
                model.interval_start < window_end,
            ).delete(synchronize_session=False)
        db_session.commit()


def test_backfill_solcast_returns_not_supported(db_session):
    """Solcast backfill reports the archive-import message and errors out."""
    from citylab.cli.commands import run_backfill

    make_data_source(db_session, "Solcast Solar Forecasts", "solcast", fresh=False)
    db_session.commit()

    r = run_backfill("solcast", "2026-05-01", "2026-05-03", 1)
    assert r["error"] is not None
    assert "archive import" in r["error"].lower()


# ---------------------------------------------------------------------------
# Solcast fetch_range guard
# ---------------------------------------------------------------------------


def test_solcast_fetch_range_raises(db_session):
    """SolcastFetcher.fetch_range must raise NotImplementedError."""
    from citylab.services.ingestion.registry import get_fetcher

    ds = make_data_source(db_session, "Solcast Guard Test", "solcast", fresh=False)
    fetcher = get_fetcher("solcast")(ds)
    with pytest.raises(NotImplementedError) as exc:
        fetcher.fetch_range(
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
    assert "archive import" in str(exc.value).lower()
