"""Tests for analytical price band classification + snapshot integration."""

from datetime import datetime, timezone

import pytest

from citylab.extensions import db
from citylab.models.energy import EnergyPrice
from citylab.services import energy_query as eq


# --- Band classification ---------------------------------------------------

@pytest.mark.parametrize(
    "price,band,label",
    [
        (-50.0, "Negative", "Solar oversupply"),
        (-0.01, "Negative", "Solar oversupply"),
        (0.0, "Low", "Renewable surplus"),
        (29.99, "Low", "Renewable surplus"),
        (30.0, "Normal", "Standard operation"),
        (149.99, "Normal", "Standard operation"),
        (150.0, "Elevated", "Gas peaker territory"),
        (299.99, "Elevated", "Gas peaker territory"),
        (300.0, "Stress", "Grid stress event"),
        (20299.99, "Stress", "Grid stress event"),
        (20300.0, "MPC", "Market Price Cap (FY2025-26)"),
        (25000.0, "MPC", "Market Price Cap (FY2025-26)"),
    ],
)
def test_classify_price_band(price, band, label):
    assert eq.classify_price_band(price) == (band, label)


def test_classify_price_band_none():
    assert eq.classify_price_band(None) == (None, None)


def test_market_price_cap_constant():
    assert eq.MARKET_PRICE_CAP_MWH == 20300.0


# --- Snapshot integration --------------------------------------------------

def test_current_snapshot_includes_price_band(app):
    with app.app_context():
        db.session.query(EnergyPrice).delete()
        ts = datetime.now(timezone.utc).replace(microsecond=0)
        db.session.add(
            EnergyPrice(
                region="VIC1", interval_start=ts,
                interval_type="5min", price_aud_mwh=85.0,  # Normal band
            )
        )
        db.session.commit()

        snap = eq.current_snapshot("VIC1")
        assert snap["price_band"] == "Normal"
        assert snap["price_band_label"] == "Standard operation"

        db.session.query(EnergyPrice).delete()
        db.session.commit()


def test_current_snapshot_price_band_none_without_price(app):
    with app.app_context():
        db.session.query(EnergyPrice).delete()
        db.session.commit()
        snap = eq.current_snapshot("VIC1")
        assert snap["price_band"] is None
        assert snap["price_band_label"] is None
