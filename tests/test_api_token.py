"""Tests for API token authentication."""


def test_api_without_token_returns_401(client):
    """API endpoint without token returns 401."""
    resp = client.get("/api/v1/app/status")
    assert resp.status_code == 401
    data = resp.get_json()
    assert data["ok"] is False
    assert data["code"] == "UNAUTHORIZED"


def test_api_with_invalid_token_returns_401(client):
    """API endpoint with invalid token returns 401."""
    resp = client.get("/api/v1/app/status", headers={
        "Authorization": "Bearer wrong-token"
    })
    assert resp.status_code == 401


def test_api_with_valid_token_returns_200(client):
    """API endpoint with valid token returns 200."""
    resp = client.get("/api/v1/app/status", headers={
        "Authorization": "Bearer dev-token-changeme"
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["data"]["app"] == "citylab"
