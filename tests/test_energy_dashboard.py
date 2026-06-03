"""Tests for the energy dashboard UI routes (/energy + HTMX partials).

These exercise the session-auth (login_required) UI routes — NOT the
token-protected api_v1 endpoints. Uses the shared fixture system; the
_force_test_database fixture ensures citylab_test is the target DB.
"""

import pytest


@pytest.fixture
def dash_user(app):
    """An authenticated user for dashboard routes."""
    from citylab.extensions import db
    from citylab.models.user import User

    with app.app_context():
        user = User(email="dash@citylab.local")
        user.set_password("dashpass123")
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


@pytest.fixture
def logged_in(client, dash_user):
    """Log the dash_user in via the session login flow."""
    client.post(
        "/login",
        data={"email": "dash@citylab.local", "password": "dashpass123"},
        follow_redirects=True,
    )
    return client


# --- Auth gate ------------------------------------------------------------

def test_dashboard_requires_login(client):
    """GET /energy without auth redirects to /login."""
    resp = client.get("/energy/")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_partial_requires_login(client):
    """A partial route also requires auth."""
    resp = client.get("/energy/partials/price")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


# --- Main page ------------------------------------------------------------

def test_dashboard_renders_when_logged_in(logged_in):
    """GET /energy returns 200 with the dashboard scaffold."""
    resp = logged_in.get("/energy/")
    assert resp.status_code == 200
    body = resp.data
    assert b"Victorian Energy Market" in body
    # Chart.js is loaded
    assert b"vendor/chart.min.js" in body
    # Panels are wired with their HTMX endpoints
    assert b"/energy/partials/price" in body
    assert b"/energy/partials/generation" in body
    assert b"/energy/partials/interconnectors" in body
    assert b"/energy/partials/weather" in body
    assert b"/energy/partials/forecast" in body
    assert b"/energy/partials/sources" in body


def test_sidebar_has_energy_link(logged_in):
    """The base layout exposes an Energy nav link."""
    resp = logged_in.get("/")
    assert resp.status_code == 200
    assert b"/energy" in resp.data


# --- Partials (render with empty DB; must not 500) ------------------------

@pytest.mark.parametrize(
    "path,marker",
    [
        ("/energy/partials/price", b"Spot Price"),
        ("/energy/partials/generation", b"Generation Mix"),
        ("/energy/partials/interconnectors", b"Interconnectors"),
        ("/energy/partials/weather", b"Renewable Outlook"),
        ("/energy/partials/forecast", b"Price Forecast"),
        ("/energy/partials/sources", b"Data Sources"),
    ],
)
def test_partials_render(logged_in, path, marker):
    """Each partial returns 200 and its key content, even with no data."""
    resp = logged_in.get(path)
    assert resp.status_code == 200, f"{path} -> {resp.status_code}"
    assert marker in resp.data


# --- View-model unit coverage --------------------------------------------

def test_price_colour_states():
    from citylab.routes.energy import _price_colour_state

    assert _price_colour_state(None) == "unknown"
    assert _price_colour_state(20) == "low"
    assert _price_colour_state(100) == "amber"
    assert _price_colour_state(200) == "high"
    assert _price_colour_state(350) == "spike"


def test_generation_fuel_aggregation():
    from citylab.routes.energy import _aggregate_generation

    mix = [
        {"fuel_type": "gas_ccgt", "output_mw": 100, "capacity_mw": 200},
        {"fuel_type": "gas_ocgt", "output_mw": 50, "capacity_mw": 100},
        {"fuel_type": "solar_utility", "output_mw": 300, "capacity_mw": 500},
        {"fuel_type": "solar_rooftop", "output_mw": 200, "capacity_mw": 400},
        {"fuel_type": "brown_coal", "output_mw": 1000, "capacity_mw": 1200},
        {"fuel_type": "battery_charging", "output_mw": -40, "capacity_mw": None},
    ]
    vm = _aggregate_generation(mix)
    # Gas buckets summed
    gas_idx = vm["labels"].index("Gas")
    assert vm["outputs"][gas_idx] == 150
    # Solar buckets summed
    solar_idx = vm["labels"].index("Solar")
    assert vm["outputs"][solar_idx] == 500
    # Battery charge shown as magnitude
    charge_idx = vm["labels"].index("Battery (charge)")
    assert vm["outputs"][charge_idx] == 40
    # Total excludes charging
    assert vm["total_output_mw"] == 100 + 50 + 500 + 1000
