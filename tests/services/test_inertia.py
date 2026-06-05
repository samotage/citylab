"""Tests for the grid inertia proxy derivation service + API."""

from datetime import datetime, timedelta, timezone

import pytest

from citylab.extensions import db
from citylab.models.energy import GenerationOutput
from citylab.services import inertia as inertia_svc

TOKEN = "dev-token-changeme"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


# --- compute_inertia: mixed fuel types -------------------------------------

def test_compute_inertia_mixed_fuel_types():
    rows = [
        {"fuel_type": "brown_coal", "output_mw": 2000.0},   # H=4.0 sync
        {"fuel_type": "gas_ccgt", "output_mw": 1000.0},     # H=3.0 sync
        {"fuel_type": "hydro", "output_mw": 500.0},         # H=3.0 sync
        {"fuel_type": "wind", "output_mw": 1500.0},         # inverter
        {"fuel_type": "solar_utility", "output_mw": 1000.0},  # inverter
        {"fuel_type": "battery_charging", "output_mw": -200.0},  # load, excluded
    ]
    m = inertia_svc.compute_inertia(rows)  # default heywood

    assert m["sync_mw"] == 3500.0
    assert m["total_mw"] == 6000.0  # charging excluded
    assert m["sync_fraction"] == pytest.approx(0.5833, abs=1e-4)
    # E_proxy = 2000*4 + 1000*3 + 500*3 = 12500
    assert m["e_proxy_mws"] == 12500.0
    assert m["e_total_mws"] == 12500.0 + inertia_svc.EXTERNAL_INERTIA_MWS
    # RoCoF = (650 * 50) / (2 * 47500) = 0.34210...
    assert m["rocof_hz_s"] == pytest.approx(0.3421, abs=1e-4)
    assert m["contingency_label"] == "heywood"
    assert m["contingency_mw"] == 650.0
    # sync 0.58 -> Comfortable. Sync fraction is the sole state driver now;
    # RoCoF (0.34 -> Moderate) is informational only and does not pull state down.
    assert m["inertia_state"] == "Comfortable"
    assert m["rocof_label"] == "Moderate"


def test_external_inertia_term_present():
    """Without the 35,000 MWs mainland term, RoCoF runs 3–5× too hot."""
    rows = [{"fuel_type": "brown_coal", "output_mw": 1000.0}]
    m = inertia_svc.compute_inertia(rows)
    e_proxy = 1000.0 * 4.0
    assert m["e_total_mws"] == e_proxy + 35000.0
    # With external term the divisor is large -> realistic RoCoF.
    assert m["rocof_hz_s"] < 0.5


def test_unknown_fuel_defaults_to_zero_h():
    rows = [
        {"fuel_type": "brown_coal", "output_mw": 1000.0},
        {"fuel_type": "fusion_reactor", "output_mw": 500.0},  # unknown -> H=0
    ]
    m = inertia_svc.compute_inertia(rows)
    assert m["sync_mw"] == 1000.0       # unknown not counted as sync
    assert m["total_mw"] == 1500.0      # but counted in total generation
    assert m["e_proxy_mws"] == 4000.0


def test_all_fourteen_fuel_types_classified():
    """All 14 OpenNEM fuel types: 9 synchronous (H>0), 5 inverter (H=0)."""
    sync_fuels = {
        "brown_coal": 4.0, "black_coal": 4.0,
        "gas_ccgt": 3.0, "gas_ocgt": 3.0, "gas_recip": 3.0, "gas_steam": 3.0,
        "hydro": 3.0, "biomass": 3.5, "distillate": 2.5,
    }
    inverter_fuels = [
        "wind", "solar_utility", "solar_rooftop",
        "battery_discharging", "battery_charging",
    ]
    for fuel, h in sync_fuels.items():
        assert inertia_svc.SYNC_H_MAP[fuel] == h
    for fuel in inverter_fuels:
        assert inertia_svc.SYNC_H_MAP.get(fuel, 0.0) == 0.0
    # 9 synchronous + 5 inverter = 14 total fuel types.
    assert len(sync_fuels) + len(inverter_fuels) == 14


def test_empty_generation_rows():
    m = inertia_svc.compute_inertia([])
    assert m["sync_mw"] == 0.0
    assert m["total_mw"] == 0.0
    assert m["sync_fraction"] == 0.0
    assert m["e_proxy_mws"] == 0.0
    assert m["e_total_mws"] == 35000.0


# --- Threshold boundary conditions (sync fraction is the sole state driver) --

@pytest.mark.parametrize(
    "sync_fraction,expected",
    [
        (0.80, "Comfortable"),   # well above
        (0.50, "Comfortable"),   # boundary (>= 0.5)
        (0.49, "Watch"),         # just below comfortable
        (0.30, "Watch"),         # boundary (>= 0.3)
        (0.29, "Brittle"),       # just below watch
        (0.10, "Brittle"),       # well below
    ],
)
def test_classify_state_boundaries(sync_fraction, expected):
    assert inertia_svc.classify_state(sync_fraction) == expected


def test_classify_state_ignores_rocof():
    """77% sync reads Comfortable regardless of RoCoF — RoCoF no longer drives
    state. This is the calibration bug the fix targets."""
    rows = [
        {"fuel_type": "brown_coal", "output_mw": 770.0},  # sync
        {"fuel_type": "wind", "output_mw": 230.0},        # inverter
    ]
    m = inertia_svc.compute_inertia(rows)
    assert m["sync_fraction"] == pytest.approx(0.77, abs=1e-4)
    assert m["inertia_state"] == "Comfortable"


# --- RoCoF informational label bands ---------------------------------------

@pytest.mark.parametrize(
    "rocof,expected",
    [
        (0.20, "Low"),        # below window
        (0.32, "Low"),        # just below lower boundary
        (0.33, "Moderate"),   # lower boundary (>= 0.33)
        (0.40, "Moderate"),   # upper boundary (<= 0.40)
        (0.41, "Elevated"),   # just past upper boundary
        (0.46, "Elevated"),   # top of achievable window
    ],
)
def test_rocof_label_bands(rocof, expected):
    assert inertia_svc.rocof_label(rocof) == expected


def test_compute_inertia_includes_rocof_label():
    rows = [{"fuel_type": "brown_coal", "output_mw": 2000.0}]
    m = inertia_svc.compute_inertia(rows)
    assert "rocof_label" in m
    assert m["rocof_label"] in {"Low", "Moderate", "Elevated"}


# --- Contingency resolution ------------------------------------------------

@pytest.mark.parametrize(
    "selector,label,mw",
    [
        ("heywood", "heywood", 650.0),
        ("loy_yang_a", "loy_yang_a", 560.0),
        ("LOY_YANG_A", "loy_yang_a", 560.0),  # case-insensitive
        ("700", "custom", 700.0),             # numeric string
        (800.0, "custom", 800.0),             # numeric value
        ("bogus", "heywood", 650.0),          # fallback
    ],
)
def test_resolve_contingency(selector, label, mw):
    assert inertia_svc.resolve_contingency(selector) == (label, mw)


def test_contingency_changes_rocof():
    rows = [{"fuel_type": "brown_coal", "output_mw": 2000.0}]
    heywood = inertia_svc.compute_inertia(rows, "heywood")
    loy = inertia_svc.compute_inertia(rows, "loy_yang_a")
    # Smaller contingency (560 < 650) -> lower RoCoF.
    assert loy["rocof_hz_s"] < heywood["rocof_hz_s"]
    assert loy["contingency_mw"] == 560.0


# --- Timeseries + current snapshot (DB-backed) -----------------------------

@pytest.fixture
def seeded(app):
    """Seed ~3h of VIC1 generation at 5-min intervals across fuel types."""
    with app.app_context():
        db.session.query(GenerationOutput).delete()
        now = datetime.now(timezone.utc).replace(microsecond=0)
        start = now - timedelta(hours=3)
        for i in range(36):  # 36 * 5min = 3h
            ts = start + timedelta(minutes=5 * i)
            for fuel, mw in (
                ("brown_coal", 2000.0),
                ("gas_ccgt", 800.0),
                ("wind", 600.0),
                ("solar_utility", 400.0),
            ):
                db.session.add(
                    GenerationOutput(
                        region="VIC1", interval_start=ts,
                        fuel_type=fuel, output_mw=mw, capacity_mw=None,
                    )
                )
        db.session.commit()
        yield now
        db.session.query(GenerationOutput).delete()
        db.session.commit()


def test_inertia_timeseries_shape(app, seeded):
    with app.app_context():
        now = datetime.now(timezone.utc)
        series = inertia_svc.inertia_timeseries(
            "VIC1", now - timedelta(hours=4), now, "1h"
        )
        assert series
        pt = series[0]
        assert {
            "timestamp", "sync_mw", "total_mw", "sync_fraction",
            "e_proxy_mws", "rocof_hz_s", "inertia_state",
        } <= set(pt)
        # sync = brown_coal + gas_ccgt = 2800; total = 3800.
        assert pt["sync_mw"] == 2800.0
        assert pt["total_mw"] == 3800.0


def test_current_inertia_snapshot(app, seeded):
    with app.app_context():
        snap = inertia_svc.current_inertia("VIC1")
        assert snap["region"] == "VIC1"
        assert snap["as_of"] is not None
        assert snap["sync_mw"] == 2800.0
        assert snap["inertia_state"] in {"Comfortable", "Watch", "Brittle"}


def test_current_inertia_no_data(app):
    with app.app_context():
        db.session.query(GenerationOutput).delete()
        db.session.commit()
        snap = inertia_svc.current_inertia("VIC1")
        assert snap["as_of"] is None
        assert snap["total_mw"] == 0.0


# --- API response shape ----------------------------------------------------

def test_api_inertia_requires_token(client):
    assert client.get("/api/v1/energy/inertia?range=24h").status_code == 401
    assert client.get("/api/v1/energy/inertia/current").status_code == 401


def test_api_inertia_timeseries_shape(client, seeded):
    resp = client.get(
        "/api/v1/energy/inertia?range=24h&interval=1h&contingency=heywood",
        headers=AUTH,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["region"] == "VIC1"
    assert data["range"] == "24h"
    assert data["interval"] == "1h"
    assert data["contingency_label"] == "heywood"
    assert data["contingency_mw"] == 650.0
    assert "caveat" in data
    assert isinstance(data["series"], list) and data["series"]
    pt = data["series"][0]
    assert {"timestamp", "sync_fraction", "rocof_hz_s", "inertia_state"} <= set(pt)


def test_api_inertia_current_shape(client, seeded):
    resp = client.get(
        "/api/v1/energy/inertia/current?region=VIC1&contingency=loy_yang_a",
        headers=AUTH,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["region"] == "VIC1"
    assert "caveat" in data
    snap = data["data"]
    assert {
        "sync_mw", "total_mw", "sync_fraction", "e_proxy_mws",
        "e_total_mws", "rocof_hz_s", "inertia_state",
        "contingency_label", "contingency_mw",
    } <= set(snap)
    assert snap["contingency_label"] == "loy_yang_a"
    assert snap["contingency_mw"] == 560.0


def test_api_summary_includes_inertia(client, seeded):
    resp = client.get("/api/v1/energy/summary?region=VIC1", headers=AUTH)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert "inertia" in data
    assert {"sync_fraction", "rocof_hz_s", "inertia_state"} <= set(data["inertia"])
