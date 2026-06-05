"""Tests for the carbon intensity derivation service + API."""

from datetime import datetime, timedelta, timezone

import pytest

from citylab.extensions import db
from citylab.models.energy import GenerationOutput
from citylab.services import carbon as carbon_svc

TOKEN = "dev-token-changeme"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


# --- compute_carbon: mixed fuel types --------------------------------------

def test_compute_carbon_mixed_fuel_types():
    rows = [
        {"fuel_type": "brown_coal", "output_mw": 2000.0},      # EF 1.25 -> 2500
        {"fuel_type": "gas_ccgt", "output_mw": 1000.0},        # EF 0.55 -> 550
        {"fuel_type": "wind", "output_mw": 1500.0},            # renewable, EF 0
        {"fuel_type": "solar_utility", "output_mw": 1000.0},   # renewable, EF 0
        {"fuel_type": "battery_charging", "output_mw": -200.0},  # load, excluded
    ]
    m = carbon_svc.compute_carbon(rows)

    # total = 2000 + 1000 + 1500 + 1000 = 5500 (battery_charging excluded)
    # emissions = 2500 + 550 = 3050; CI = 3050 / 5500 = 0.5545
    assert m["carbon_intensity_tco2_mwh"] == pytest.approx(0.5545, abs=1e-4)
    assert m["intensity_band"] == "Moderate"
    # renewables = wind + solar = 2500 -> 45.5%
    assert m["renewables_pct"] == pytest.approx(45.5, abs=0.1)
    # fossil = brown_coal + gas = 3000 -> 54.5%
    assert m["fossil_pct"] == pytest.approx(54.5, abs=0.1)


def test_fuel_breakdown_shape_and_ordering():
    rows = [
        {"fuel_type": "gas_ccgt", "output_mw": 500.0},
        {"fuel_type": "brown_coal", "output_mw": 2000.0},
        {"fuel_type": "wind", "output_mw": 1000.0},
    ]
    m = carbon_svc.compute_carbon(rows)
    breakdown = m["fuel_breakdown"]
    assert {"fuel", "mw", "pct"} <= set(breakdown[0])
    # Ordered by output descending: brown_coal (2000) > wind (1000) > gas (500).
    assert [b["fuel"] for b in breakdown] == ["brown_coal", "wind", "gas_ccgt"]
    assert sum(b["pct"] for b in breakdown) == pytest.approx(100.0, abs=0.5)


def test_battery_charging_excluded_from_both_num_and_denom():
    """battery_charging must not dilute the intensity or the totals."""
    base = [{"fuel_type": "brown_coal", "output_mw": 1000.0}]
    with_charge = base + [
        {"fuel_type": "battery_charging", "output_mw": 5000.0}  # positive magnitude
    ]
    m_base = carbon_svc.compute_carbon(base)
    m_charge = carbon_svc.compute_carbon(with_charge)
    # Pure brown coal -> CI == its EF (1.25), identical with/without charging.
    assert m_base["carbon_intensity_tco2_mwh"] == 1.25
    assert m_charge["carbon_intensity_tco2_mwh"] == 1.25
    assert m_base["fuel_breakdown"] == m_charge["fuel_breakdown"]


def test_battery_discharging_is_not_renewable():
    rows = [
        {"fuel_type": "wind", "output_mw": 500.0},
        {"fuel_type": "battery_discharging", "output_mw": 500.0},  # EF 0 but storage
    ]
    m = carbon_svc.compute_carbon(rows)
    # Only wind counts as renewable -> 50%, not 100%.
    assert m["renewables_pct"] == pytest.approx(50.0, abs=0.1)
    assert m["carbon_intensity_tco2_mwh"] == 0.0


def test_unknown_fuel_defaults_to_zero_ef():
    rows = [
        {"fuel_type": "brown_coal", "output_mw": 1000.0},
        {"fuel_type": "fusion_reactor", "output_mw": 1000.0},  # unknown -> EF 0
    ]
    m = carbon_svc.compute_carbon(rows)
    # emissions = 1250; total = 2000 -> CI 0.625. Unknown is neither fossil nor
    # renewable: 50% fossil, 0% renewable.
    assert m["carbon_intensity_tco2_mwh"] == pytest.approx(0.625, abs=1e-4)
    assert m["fossil_pct"] == pytest.approx(50.0, abs=0.1)
    assert m["renewables_pct"] == 0.0


def test_empty_generation_rows():
    m = carbon_svc.compute_carbon([])
    assert m["carbon_intensity_tco2_mwh"] == 0.0
    assert m["renewables_pct"] == 0.0
    assert m["fossil_pct"] == 0.0
    assert m["fuel_breakdown"] == []
    assert m["intensity_band"] == "Very Low"


# --- Intensity band boundaries ---------------------------------------------

@pytest.mark.parametrize(
    "ci,expected",
    [
        (0.0, "Very Low"),
        (0.19, "Very Low"),
        (0.2, "Low"),       # boundary -> Low
        (0.39, "Low"),
        (0.4, "Moderate"),  # boundary -> Moderate
        (0.69, "Moderate"),
        (0.7, "High"),      # boundary -> High
        (1.0, "High"),      # inclusive upper bound
        (1.01, "Very High"),
        (1.25, "Very High"),
    ],
)
def test_intensity_band_boundaries(ci, expected):
    assert carbon_svc.intensity_band(ci) == expected


def test_all_emission_factors_present():
    """All 14 OpenNEM fuel types carry an explicit emission factor."""
    expected = {
        "brown_coal", "black_coal", "gas_ccgt", "gas_ocgt", "gas_recip",
        "gas_steam", "distillate", "hydro", "wind", "solar_utility",
        "solar_rooftop", "battery_discharging", "battery_charging", "biomass",
    }
    assert expected <= set(carbon_svc.EMISSION_FACTORS)
    assert carbon_svc.EMISSION_FACTORS["brown_coal"] == 1.25
    assert carbon_svc.EMISSION_FACTORS["black_coal"] == 0.90
    assert carbon_svc.EMISSION_FACTORS["distillate"] == 0.95
    for g in ("gas_ccgt", "gas_ocgt", "gas_recip", "gas_steam"):
        assert carbon_svc.EMISSION_FACTORS[g] == 0.55


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


def test_carbon_timeseries_shape(app, seeded):
    with app.app_context():
        now = datetime.now(timezone.utc)
        series = carbon_svc.carbon_timeseries(
            "VIC1", now - timedelta(hours=4), now, "1h"
        )
        assert series
        pt = series[0]
        assert {
            "timestamp", "carbon_intensity_tco2_mwh", "renewables_pct",
            "fossil_pct", "intensity_band", "total_mw",
        } <= set(pt)
        assert pt["total_mw"] == 3800.0  # 2000 + 800 + 600 + 400


def test_current_carbon_snapshot(app, seeded):
    with app.app_context():
        snap = carbon_svc.current_carbon("VIC1")
        assert snap["region"] == "VIC1"
        assert snap["as_of"] is not None
        assert snap["carbon_intensity_tco2_mwh"] > 0
        assert snap["intensity_band"] in {
            "Very Low", "Low", "Moderate", "High", "Very High"
        }


def test_current_carbon_no_data(app):
    with app.app_context():
        db.session.query(GenerationOutput).delete()
        db.session.commit()
        snap = carbon_svc.current_carbon("VIC1")
        assert snap["as_of"] is None
        assert snap["carbon_intensity_tco2_mwh"] == 0.0


# --- API response shape ----------------------------------------------------

def test_api_carbon_requires_token(client):
    assert client.get("/api/v1/energy/carbon?range=24h").status_code == 401
    assert client.get("/api/v1/energy/carbon/current").status_code == 401


def test_api_carbon_timeseries_shape(client, seeded):
    resp = client.get(
        "/api/v1/energy/carbon?range=24h&interval=1h", headers=AUTH
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["region"] == "VIC1"
    assert data["range"] == "24h"
    assert data["interval"] == "1h"
    assert isinstance(data["series"], list) and data["series"]
    pt = data["series"][0]
    assert {
        "timestamp", "carbon_intensity_tco2_mwh", "renewables_pct",
        "intensity_band",
    } <= set(pt)


def test_api_carbon_current_shape(client, seeded):
    resp = client.get("/api/v1/energy/carbon/current?region=VIC1", headers=AUTH)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["region"] == "VIC1"
    snap = data["data"]
    assert {
        "carbon_intensity_tco2_mwh", "renewables_pct", "fossil_pct",
        "fuel_breakdown", "intensity_band", "region", "as_of",
    } <= set(snap)
