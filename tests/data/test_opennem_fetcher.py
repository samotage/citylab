"""Level 1 — OpenNEM fetcher contract tests (offline, recorded fixtures).

Asserts OpenNEMFetcher.transform() maps the recorded snapshot-dict into the
correct ORM instances with correct field mapping, tolerates null/missing fields,
keeps every fuel_type inside the known enum, and that the live path raises on an
unexpected payload then falls back to synthetic without crashing. No network.
"""

from datetime import datetime

import pytest

from tests.data.conftest import load_fixture, load_fixture_raw

from citylab.models.data_source import DataSource
from citylab.models.energy import (
    EnergyDemand,
    EnergyPrice,
    GenerationOutput,
    GeneratorSubmission,
    InterconnectorFlow,
    PriceForecast,
)
from citylab.services.ingestion.opennem import (
    FUEL_TYPES,
    INTERCONNECTORS,
    OPENNEM_FUEL_MAP,
    OpenNEMFetcher,
)

KNOWN_FUELS = set(FUEL_TYPES) | set(OPENNEM_FUEL_MAP.values())
KNOWN_CORRIDORS = {ic["id"] for ic in INTERCONNECTORS}


def _fetcher(db_session):
    """An OpenNEMFetcher bound to an unreachable source (synthetic on live)."""
    ds = DataSource(
        name="OpenNEM L1",
        source_type="opennem",
        base_url="http://127.0.0.1:1",
        cron_expression="*/5 * * * *",
        config={"timeout_seconds": 1},
    )
    return OpenNEMFetcher(ds)


def test_transform_maps_each_record_type(db_session):
    raw = load_fixture("opennem", "prices_generation_good")
    records = _fetcher(db_session).transform(raw)

    by_type = {}
    for r in records:
        by_type.setdefault(type(r), []).append(r)

    # Every record type the snapshot carries is produced.
    assert len(by_type[EnergyPrice]) == len(raw["prices"])
    assert len(by_type[EnergyDemand]) == len(raw["demand"])
    assert len(by_type[GenerationOutput]) == len(raw["generation"])
    assert len(by_type[InterconnectorFlow]) == len(raw["interconnectors"])
    assert len(by_type[GeneratorSubmission]) == len(raw["submissions"])
    assert len(by_type[PriceForecast]) == len(raw["forecasts"])


def test_transform_field_mapping_price(db_session):
    raw = load_fixture("opennem", "prices_generation_good")
    records = _fetcher(db_session).transform(raw)
    price = next(r for r in records if isinstance(r, EnergyPrice))
    src = raw["prices"][0]

    assert price.region == src["region"]
    assert price.price_aud_mwh == src["price_aud_mwh"]
    assert price.interval_type == src["interval_type"]
    assert isinstance(price.interval_start, datetime)
    assert price.interval_start == src["interval_start"]


def test_transform_field_mapping_interconnector(db_session):
    raw = load_fixture("opennem", "prices_generation_good")
    records = _fetcher(db_session).transform(raw)
    flows = [r for r in records if isinstance(r, InterconnectorFlow)]

    ids = {f.interconnector_id for f in flows}
    # Every corridor in the fixture maps to a known corridor.
    assert ids <= KNOWN_CORRIDORS
    sample = flows[0]
    assert sample.from_region
    assert sample.to_region
    assert isinstance(sample.flow_mw, float)


def test_every_generated_fuel_type_is_known(db_session):
    raw = load_fixture("opennem", "prices_generation_good")
    records = _fetcher(db_session).transform(raw)
    gens = [r for r in records if isinstance(r, GenerationOutput)]
    assert gens
    for g in gens:
        assert g.fuel_type in KNOWN_FUELS, f"unknown fuel_type {g.fuel_type}"
    # battery_charging must round-trip as a negative output (sign preserved).
    charging = [g for g in gens if g.fuel_type == "battery_charging"]
    if charging:
        assert charging[0].output_mw < 0


def test_transform_null_and_missing_fields(db_session):
    """Empty collections + null optionals must not crash transform()."""
    raw = load_fixture("opennem", "null_fields_edge")
    records = _fetcher(db_session).transform(raw)

    # demand/interconnectors/submissions/forecasts empty -> only prices + gen.
    prices = [r for r in records if isinstance(r, EnergyPrice)]
    gens = [r for r in records if isinstance(r, GenerationOutput)]
    assert len(prices) == 1
    assert len(gens) == 1
    # interval_end was null in the fixture; it must remain None.
    assert prices[0].interval_end is None


def test_synthetic_transform_fuels_all_known(db_session):
    """The fetcher's own synthetic path produces only known fuel types."""
    fetcher = _fetcher(db_session)
    snap = fetcher._synthetic(backfill=False)
    records = fetcher.transform(snap)
    gens = [r for r in records if isinstance(r, GenerationOutput)]
    assert gens
    for g in gens:
        assert g.fuel_type in KNOWN_FUELS


def test_live_path_raises_on_unexpected_payload_then_falls_back(db_session, monkeypatch):
    """An unexpected live payload makes _fetch_live raise; fetch() must fall back
    to a synthetic snapshot without crashing."""
    fetcher = _fetcher(db_session)
    bad_payload = load_fixture_raw("opennem", "unexpected_payload_edge")

    class _Resp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return bad_payload

    import requests

    def _fake_get(url, timeout=None):
        return _Resp()

    # _fetch_live does `import requests` locally, so patch requests.get itself.
    monkeypatch.setattr(requests, "get", _fake_get)

    # _fetch_live raises ValueError("Unexpected OpenNEM payload shape") on this.
    with pytest.raises(ValueError):
        fetcher._fetch_live(backfill=False)

    # The public fetch() swallows the error and returns a synthetic snapshot.
    snap = fetcher.fetch()
    assert snap["source"] == "synthetic"
    assert snap["prices"]
