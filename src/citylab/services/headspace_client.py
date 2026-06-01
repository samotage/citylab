"""HTTP client for Headspace API dispatch."""

import logging

import requests
from flask import current_app

logger = logging.getLogger(__name__)


def trigger_agent(persona: str, action: str) -> dict | None:
    """Dispatch an agent session via Headspace API."""
    config = current_app.config.get("CITYLAB_CONFIG", {})
    headspace_cfg = config.get("headspace", {})

    url = headspace_cfg.get("url", "")
    api_token = headspace_cfg.get("api_token", "")

    if not url:
        logger.warning("Headspace URL not configured — skipping agent trigger")
        return None

    endpoint = f"{url.rstrip('/')}/api/agents/dispatch"
    headers = {"Content-Type": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"

    payload = {
        "persona": persona,
        "action": action,
        "source": "citylab-scheduler",
    }

    try:
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        logger.info(f"Agent dispatched: persona={persona}, action={action}")
        return result
    except requests.RequestException as e:
        logger.error(f"Headspace dispatch failed: {e}")
        raise
