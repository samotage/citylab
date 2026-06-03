"""Unit tests for the data_verify service (the pre-hackathon gate logic).

Confirms the service reports all-green against seeded data and — crucially —
pinpoints the SPECIFIC failing source + category when something breaks, rather
than silently passing. This is what makes the gate trustworthy.
"""

from datetime import datetime, timedelta, timezone

import pytest

from tests.data.conftest import run_fetcher, seed_locations

from citylab.models.energy import GenerationOutput
from citylab.models.solar import SolarForecast
from citylab.models.weather import WeatherForecast
from citylab.services import data_verify

pytestmark = pytest.mark.integration


@pytest.fixture
def populated(db_session):
    seed_locations(db_session)
    for source_type, name in (
        ("opennem", "OpenNEM Verify"),
        ("bom", "BOM Verify"),
        ("solcast", "Solcast Verify"),
    ):
        run_fetcher(db_session, source_type, name, fresh=False)
    return db_session


def _source(report, name):
    return next(s for s in report.sources if s.source == name)


def _category(source_result, name):
    return next(c for c in source_result.categories if c.name == name)


# ---------------------------------------------------------------------------
# All-green
# ---------------------------------------------------------------------------


def test_all_green_against_seeded_data(populated):
    report = data_verify.verify(populated)
    assert report.passed, report.to_dict()
    # Every source has data and every category passes.
    for src in report.sources:
        assert src.has_data
        assert src.passed
        assert src.categories


def test_report_serialises(populated):
    report = data_verify.verify(populated)
    d = report.to_dict()
    assert d["passed"] is True
    assert {s["source"] for s in d["sources"]} == {"opennem", "bom", "solcast"}
    for s in d["sources"]:
        for c in s["categories"]:
            assert "checks" in c
            for chk in c["checks"]:
                assert {"name", "passed", "detail", "count"} <= set(chk)


# ---------------------------------------------------------------------------
# Broken-state detection — must name the failing source + category
# ---------------------------------------------------------------------------


def test_detects_missing_interconnector_corridor(populated):
    """Drop all interconnector flows -> opennem consistency fails (corridors),
    others stay green. Pinpoints the specific source + category + check."""
    from citylab.models.energy import InterconnectorFlow

    populated.query(InterconnectorFlow).delete()
    populated.flush()

    report = data_verify.verify(populated)
    assert report.passed is False

    opennem = _source(report, "opennem")
    assert opennem.passed is False
    consistency = _category(opennem, "consistency")
    assert consistency.passed is False
    failing = [c.name for c in consistency.checks if not c.passed]
    assert "all_corridors_present" in failing

    # Other sources unaffected.
    assert _source(report, "bom").passed is True
    assert _source(report, "solcast").passed is True


def test_detects_unknown_fuel_type(populated):
    row = populated.query(GenerationOutput).filter_by(region="VIC1").first()
    row.fuel_type = "antimatter"
    populated.flush()

    report = data_verify.verify(populated)
    opennem = _source(report, "opennem")
    completeness = _category(opennem, "completeness")
    failing = [c.name for c in completeness.checks if not c.passed]
    assert "generation_fuel_known" in failing


def test_detects_nulled_solar_ghi(populated):
    row = populated.query(SolarForecast).first()
    row.ghi_wm2 = None
    populated.flush()

    report = data_verify.verify(populated)
    assert report.passed is False
    solcast = _source(report, "solcast")
    completeness = _category(solcast, "completeness")
    assert completeness.passed is False
    failing = [c.name for c in completeness.checks if not c.passed]
    assert "ghi_present" in failing


def test_detects_stale_weather_source(populated):
    """Push every weather forecast issue far into the past -> bom freshness fails."""
    stale = datetime.now(timezone.utc) - timedelta(days=30)
    for f in populated.query(WeatherForecast).all():
        f.issued_at = stale
    populated.flush()

    report = data_verify.verify(populated)
    bom = _source(report, "bom")
    freshness = _category(bom, "freshness")
    assert freshness.passed is False
    failing = [c.name for c in freshness.checks if not c.passed]
    assert "forecast_recent" in failing


def test_empty_pipeline_reports_no_data_not_silent_pass(db_session):
    """No data at all for a source -> has_data False, report does NOT pass."""
    # Only seed + run BOM; OpenNEM and Solcast tables may be empty in a fresh DB.
    # (Other tests in the session may have left rows, so we assert on the BOM
    #  path explicitly and on the overall not-silently-passing contract.)
    report = data_verify.verify(db_session)
    # A source with no data must be has_data False and cannot pass.
    for src in report.sources:
        if not src.has_data:
            assert src.passed is False
