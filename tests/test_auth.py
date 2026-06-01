"""Tests for authentication."""

import pytest


@pytest.fixture
def admin_user(app):
    """Create an admin user for testing."""
    from citylab.extensions import db
    from citylab.models.user import User

    with app.app_context():
        user = User(email="test@citylab.local")
        user.set_password("testpass123")
        db.session.add(user)
        db.session.commit()
        yield user
        # Cleanup
        db.session.delete(user)
        db.session.commit()


def test_login_page_renders(client):
    """GET /login returns 200."""
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Log In" in resp.data


def test_login_valid_credentials(client, admin_user):
    """POST /login with valid credentials succeeds."""
    resp = client.post("/login", data={
        "email": "test@citylab.local",
        "password": "testpass123",
    }, follow_redirects=True)
    assert resp.status_code == 200
    # Should be on the dashboard now
    assert b"Dashboard" in resp.data


def test_login_invalid_credentials(client, admin_user):
    """POST /login with invalid credentials shows error."""
    resp = client.post("/login", data={
        "email": "test@citylab.local",
        "password": "wrongpassword",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Invalid email or password" in resp.data


def test_protected_route_redirects(client):
    """GET / without login redirects to /login."""
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
