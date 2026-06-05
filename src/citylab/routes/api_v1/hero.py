"""Hero panel context — ephemeral active-module state for the dynamic hero panel.

The dashboard's hero box shows one swappable content module at a time. The agent
(Ray) sets the active module via ``POST /api/v1/hero/context``; the frontend
polls the current state and renders the matching partial.

State is ephemeral — a single dict held in ``app.config`` (no DB table). It
resets to the default (``prices``) on server restart, which is the intended
lifecycle for this whiteboard-style surface.

The ``freeform`` module carries agent-authored content (Mermaid diagram, Chart.js
config, or HTML). HTML content is sanitised to a tag/attribute allowlist before
storage — the content is trusted (Bearer-authenticated agent), but sanitisation
keeps the surface bounded regardless.
"""

import re

from flask import Blueprint, current_app, jsonify, request

from citylab.routes.api_v1.auth import require_api_token

hero_api_bp = Blueprint("hero_api", __name__)

# Templated modules render a fixed server-side partial; freeform renders
# agent-authored content.
TEMPLATED_MODULES = ("prices", "grid", "carbon", "weather")
VALID_MODULES = TEMPLATED_MODULES + ("freeform",)
DEFAULT_MODULE = "prices"

VALID_CONTENT_TYPES = ("mermaid", "chart", "html")

_STATE_KEY = "HERO_STATE"


# --- HTML sanitisation -----------------------------------------------------
#
# Allowlist-based: any tag not listed is stripped (markup removed, inner text
# kept); any attribute not listed is dropped; style properties are filtered to a
# safe subset. This is a deliberately simple regex sanitiser — adequate because
# the author is the trusted agent, not arbitrary user input.
_ALLOWED_TAGS = {
    "div", "span", "p", "table", "tr", "td", "th", "thead", "tbody",
    "h3", "h4", "strong", "em", "br",
}
_ALLOWED_ATTRS = {"class", "style"}
_ALLOWED_STYLE_PROPS = {
    "color", "background", "background-color", "font-weight", "font-size",
    "font-style", "text-align", "padding", "margin", "border", "border-radius",
    "width", "height", "display", "grid-template-columns", "gap",
}

_SCRIPT_STYLE_RE = re.compile(
    r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL
)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_TAG_RE = re.compile(r"<\s*(/?)\s*([a-zA-Z][a-zA-Z0-9]*)([^>]*?)(/?)\s*>")
_ATTR_RE = re.compile(
    r"""([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*("([^"]*)"|'([^']*)'|([^\s"'>]+))"""
)
_STYLE_PROP_RE = re.compile(r"([a-zA-Z-]+)\s*:\s*([^;]+)")


def _sanitise_style(value: str) -> str:
    parts = []
    for m in _STYLE_PROP_RE.finditer(value):
        prop = m.group(1).strip().lower()
        val = m.group(2).strip()
        low = val.lower()
        if prop not in _ALLOWED_STYLE_PROPS:
            continue
        if "expression" in low or "url(" in low or "javascript:" in low:
            continue
        parts.append(f"{prop}: {val}")
    return "; ".join(parts)


def _sanitise_attrs(attr_str: str) -> str:
    kept = []
    for m in _ATTR_RE.finditer(attr_str):
        name = m.group(1).lower()
        raw = m.group(3)
        if raw is None:
            raw = m.group(4)
        if raw is None:
            raw = m.group(5)
        raw = raw or ""
        if name not in _ALLOWED_ATTRS:
            continue
        if name == "style":
            cleaned = _sanitise_style(raw)
            if cleaned:
                kept.append(f'style="{cleaned}"')
        else:  # class
            safe = re.sub(r"[^\w\s-]", "", raw)
            kept.append(f'{name}="{safe}"')
    return (" " + " ".join(kept)) if kept else ""


def sanitise_html(html: str) -> str:
    """Strip tags/attributes not on the allowlist; keep inner text of stripped
    tags. Removes ``<script>``/``<style>`` blocks and comments wholesale."""
    if not html:
        return ""
    html = _SCRIPT_STYLE_RE.sub("", html)
    html = _COMMENT_RE.sub("", html)

    def repl(m):
        closing = m.group(1)
        tag = m.group(2).lower()
        attrs = m.group(3) or ""
        self_close = m.group(4)
        if tag not in _ALLOWED_TAGS:
            return ""  # strip the tag markup, keep surrounding text
        if closing:
            return f"</{tag}>"
        cleaned_attrs = _sanitise_attrs(attrs)
        slash = " /" if (self_close or tag == "br") else ""
        return f"<{tag}{cleaned_attrs}{slash}>"

    return _TAG_RE.sub(repl, html)


# --- State helpers ---------------------------------------------------------

def _default_state() -> dict:
    return {"module": DEFAULT_MODULE, "title": None, "content": None}


def get_hero_state() -> dict:
    """Current hero state ``{module, title, content}`` (default if unset)."""
    return current_app.config.get(_STATE_KEY) or _default_state()


def get_hero_module() -> str:
    """Convenience accessor for the active module key (used by the frontend)."""
    return get_hero_state()["module"]


# --- Routes ----------------------------------------------------------------

@hero_api_bp.route("/hero/context", methods=["POST"])
@require_api_token
def set_context():
    body = request.get_json(silent=True) or {}
    module = body.get("module")

    if module not in VALID_MODULES:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": f"Invalid module '{module}'. Valid: {', '.join(VALID_MODULES)}",
                    "code": "INVALID_MODULE",
                }
            ),
            400,
        )

    previous = get_hero_state()["module"]

    if module == "freeform":
        title = body.get("title")
        content = body.get("content")
        if not title or not isinstance(title, str):
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "freeform requires a non-empty 'title' string",
                        "code": "MISSING_TITLE",
                    }
                ),
                400,
            )
        if not isinstance(content, dict):
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "freeform requires a 'content' object",
                        "code": "MISSING_CONTENT",
                    }
                ),
                400,
            )
        ctype = content.get("type")
        if ctype not in VALID_CONTENT_TYPES:
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": f"content.type must be one of {', '.join(VALID_CONTENT_TYPES)}",
                        "code": "INVALID_CONTENT_TYPE",
                    }
                ),
                400,
            )
        if ctype == "html":
            content = {**content, "body": sanitise_html(content.get("body", ""))}
        new_state = {"module": "freeform", "title": title, "content": content}
    else:
        # Switching to any templated module clears freeform content.
        new_state = {"module": module, "title": None, "content": None}

    current_app.config[_STATE_KEY] = new_state
    return jsonify({"ok": True, "data": {"module": module, "previous": previous}})


@hero_api_bp.route("/hero/context", methods=["GET"])
@require_api_token
def get_context():
    """Return the current hero state — module key plus freeform title/content.

    Lets the frontend poll for context changes and render the active module.
    """
    return jsonify({"ok": True, "data": get_hero_state()})
