"""Tests for health endpoint."""


def test_health_returns_200(client):
    """GET /health returns 200 with status=healthy."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
