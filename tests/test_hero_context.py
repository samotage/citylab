"""Tests for the hero panel context API + freeform content handling."""

from citylab.routes.api_v1 import hero as hero_mod

TOKEN = "dev-token-changeme"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


# --- Auth ------------------------------------------------------------------

def test_hero_context_requires_token(client):
    assert client.post("/api/v1/hero/context", json={"module": "grid"}).status_code == 401
    assert client.get("/api/v1/hero/context").status_code == 401


# --- Default + basic set/get -----------------------------------------------

def test_hero_default_is_prices():
    """A freshly created app starts on the default 'prices' module."""
    from citylab import create_app

    fresh = create_app(testing=True)
    with fresh.app_context():
        assert hero_mod.get_hero_module() == "prices"
        state = hero_mod.get_hero_state()
        assert state == {"module": "prices", "title": None, "content": None}


def test_set_module_returns_previous(client):
    # Establish a known state, then change it — previous must reflect the prior.
    client.post("/api/v1/hero/context", json={"module": "grid"}, headers=AUTH)
    resp = client.post("/api/v1/hero/context", json={"module": "carbon"}, headers=AUTH)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["data"]["module"] == "carbon"
    assert data["data"]["previous"] == "grid"


def test_get_context_reflects_active_module(client):
    client.post("/api/v1/hero/context", json={"module": "weather"}, headers=AUTH)
    resp = client.get("/api/v1/hero/context", headers=AUTH)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["module"] == "weather"
    assert data["title"] is None
    assert data["content"] is None


# --- Validation ------------------------------------------------------------

def test_invalid_module_returns_400(client):
    resp = client.post("/api/v1/hero/context", json={"module": "banana"}, headers=AUTH)
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["ok"] is False
    assert body["code"] == "INVALID_MODULE"


def test_missing_module_returns_400(client):
    resp = client.post("/api/v1/hero/context", json={}, headers=AUTH)
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


# --- Freeform: content types -----------------------------------------------

def test_freeform_mermaid(client):
    resp = client.post(
        "/api/v1/hero/context",
        json={
            "module": "freeform",
            "title": "Interconnector Topology",
            "content": {"type": "mermaid", "diagram": "graph LR; VIC-->NSW"},
        },
        headers=AUTH,
    )
    assert resp.status_code == 200
    state = client.get("/api/v1/hero/context", headers=AUTH).get_json()["data"]
    assert state["module"] == "freeform"
    assert state["title"] == "Interconnector Topology"
    assert state["content"]["type"] == "mermaid"
    assert state["content"]["diagram"] == "graph LR; VIC-->NSW"


def test_freeform_chart(client):
    cfg = {"type": "chart", "chart_type": "bar", "config": {"data": {"labels": ["a"]}}}
    resp = client.post(
        "/api/v1/hero/context",
        json={"module": "freeform", "title": "Scenario Compare", "content": cfg},
        headers=AUTH,
    )
    assert resp.status_code == 200
    state = client.get("/api/v1/hero/context", headers=AUTH).get_json()["data"]
    assert state["content"]["type"] == "chart"
    assert state["content"]["config"]["data"]["labels"] == ["a"]


def test_freeform_html_stored_after_sanitise(client):
    resp = client.post(
        "/api/v1/hero/context",
        json={
            "module": "freeform",
            "title": "Note",
            "content": {"type": "html", "body": '<p class="x">Hello</p>'},
        },
        headers=AUTH,
    )
    assert resp.status_code == 200
    state = client.get("/api/v1/hero/context", headers=AUTH).get_json()["data"]
    assert state["content"]["type"] == "html"
    assert '<p class="x">Hello</p>' in state["content"]["body"]


# --- Freeform: validation --------------------------------------------------

def test_freeform_missing_title_400(client):
    resp = client.post(
        "/api/v1/hero/context",
        json={"module": "freeform", "content": {"type": "mermaid", "diagram": "x"}},
        headers=AUTH,
    )
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "MISSING_TITLE"


def test_freeform_missing_content_400(client):
    resp = client.post(
        "/api/v1/hero/context",
        json={"module": "freeform", "title": "No content"},
        headers=AUTH,
    )
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "MISSING_CONTENT"


def test_freeform_invalid_content_type_400(client):
    resp = client.post(
        "/api/v1/hero/context",
        json={
            "module": "freeform",
            "title": "Bad type",
            "content": {"type": "video", "src": "x"},
        },
        headers=AUTH,
    )
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "INVALID_CONTENT_TYPE"


def test_freeform_content_missing_type_400(client):
    resp = client.post(
        "/api/v1/hero/context",
        json={"module": "freeform", "title": "No type", "content": {"body": "x"}},
        headers=AUTH,
    )
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "INVALID_CONTENT_TYPE"


# --- Freeform: lifecycle ---------------------------------------------------

def test_switching_to_templated_module_clears_freeform(client):
    client.post(
        "/api/v1/hero/context",
        json={
            "module": "freeform",
            "title": "Temp",
            "content": {"type": "mermaid", "diagram": "x"},
        },
        headers=AUTH,
    )
    client.post("/api/v1/hero/context", json={"module": "prices"}, headers=AUTH)
    state = client.get("/api/v1/hero/context", headers=AUTH).get_json()["data"]
    assert state["module"] == "prices"
    assert state["title"] is None
    assert state["content"] is None


# --- HTML sanitisation (unit) ----------------------------------------------

def test_sanitise_strips_script_and_forbidden_tags():
    dirty = (
        '<div class="card" onclick="steal()">'
        '<script>alert(1)</script>'
        '<iframe src="evil"></iframe>'
        '<p style="color: red; position: fixed">Safe</p>'
        '</div>'
    )
    clean = hero_mod.sanitise_html(dirty)
    assert "<script" not in clean and "alert(1)" not in clean
    assert "iframe" not in clean
    assert "onclick" not in clean
    assert "position" not in clean          # style prop not on allowlist
    assert "color: red" in clean            # allowed style prop kept
    assert "<div" in clean and 'class="card"' in clean
    assert "<p" in clean and "Safe" in clean


def test_sanitise_keeps_text_of_stripped_tags():
    assert "keep me" in hero_mod.sanitise_html("<article>keep me</article>")


def test_sanitise_blocks_javascript_url_in_style():
    clean = hero_mod.sanitise_html('<div style="background: url(javascript:x)">y</div>')
    assert "javascript" not in clean
    assert "y" in clean


def test_sanitise_empty():
    assert hero_mod.sanitise_html("") == ""
