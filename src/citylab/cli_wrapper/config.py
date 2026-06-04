"""CLI config discovery — finds config.yaml and reads API settings."""

import os
from pathlib import Path

import yaml


def find_config() -> dict:
    """Find config.yaml and return its contents."""
    # Walk up from cwd
    current = Path.cwd()
    for _ in range(10):
        candidate = current / "config.yaml"
        if candidate.exists():
            with open(candidate) as f:
                return yaml.safe_load(f) or {}
        current = current.parent

    # Try project root relative to this file
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    candidate = project_root / "config.yaml"
    if candidate.exists():
        with open(candidate) as f:
            return yaml.safe_load(f) or {}

    return {}


def get_api_token() -> str:
    """Get API token from env or config."""
    token = os.environ.get("CITYLAB_API_TOKEN")
    if token:
        return token
    config = find_config()
    return config.get("api", {}).get("token", "")


def get_base_url() -> str:
    """Get the API base URL."""
    url = os.environ.get("CITYLAB_URL")
    if url:
        return url.rstrip("/")
    config = find_config()
    server = config.get("server", {})
    host = server.get("host", "127.0.0.1")
    port = server.get("port", 15099)
    return f"http://{host}:{port}"
