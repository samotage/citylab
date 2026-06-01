"""API token authentication decorator."""

import functools

from flask import current_app, jsonify, request


def require_api_token(f):
    """Decorator that requires a valid Bearer token."""

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"ok": False, "error": "Missing API token", "code": "UNAUTHORIZED"}), 401

        token = auth_header[7:]  # Strip "Bearer "
        expected = current_app.config.get("CITYLAB_CONFIG", {}).get("api", {}).get("token", "")

        if not expected or token != expected:
            return jsonify({"ok": False, "error": "Invalid API token", "code": "UNAUTHORIZED"}), 401

        return f(*args, **kwargs)

    return decorated
