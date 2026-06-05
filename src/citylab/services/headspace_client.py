"""HeadspaceClient — HTTP wrapper for the Headspace remote agent API.

Talks to a Headspace instance's `/api/remote_agents/*` namespace to create,
probe, message, and shut down remote agents. Uses a pooled requests.Session.
Every connection/timeout/HTTP error is wrapped in :class:`HeadspaceError`,
which carries both a technical message (logging) and a user-friendly message
(UI/CLI display) — NFR2.

Ported from the Beans/Kenwood remote-agent client pattern, adapted for CityLab.

The legacy ``trigger_agent()`` helper is kept as a thin shim over
``create_agent`` so the existing scheduler callsite keeps working (FR12).
"""

import logging

import requests
from flask import current_app

logger = logging.getLogger(__name__)


class HeadspaceError(Exception):
    """Error from the Headspace remote agent API.

    Attributes:
        technical_message: Detailed error for logging/debugging.
        user_message: User-friendly message for display in UI and CLI.
    """

    def __init__(self, technical_message: str, user_message: str | None = None):
        self.technical_message = technical_message
        self.user_message = user_message or technical_message
        super().__init__(self.technical_message)


class HeadspaceClient:
    """HTTP client for the Headspace remote agent API.

    Args:
        base_url: Headspace server base URL (e.g. "http://127.0.0.1:5001").
        project_slug: CityLab's project identifier in Headspace.
        timeout: HTTP timeout in seconds (connect + read).
    """

    def __init__(self, base_url: str, project_slug: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.project_slug = project_slug
        self.timeout = timeout
        self._session = requests.Session()

    # -- internals ---------------------------------------------------------

    def _headers(self, session_token: str | None = None) -> dict:
        headers = {"Content-Type": "application/json"}
        if session_token:
            headers["Authorization"] = f"Bearer {session_token}"
        return headers

    def _handle_error(self, response, context: str = "API call"):
        """Wrap an HTTP error response in HeadspaceError."""
        status = response.status_code
        try:
            body = response.json()
            detail = body.get(
                "detail", body.get("message", body.get("error", response.text))
            )
        except Exception:
            detail = response.text

        technical = f"Headspace {context} failed: HTTP {status} — {detail}"

        user_messages = {
            400: "Invalid request to agent service.",
            401: "Authentication failed with agent service.",
            403: "Access denied to agent service.",
            404: "Agent not found.",
            408: "Agent service timed out.",
            409: "Agent is busy processing another request. Please wait a moment.",
            410: "Agent session has ended. Please start a new session.",
            422: "Agent configuration is missing required guardrails.",
            429: "Too many requests. Please wait before sending another message.",
            500: "Agent service encountered an internal error.",
            502: "Agent service is temporarily unavailable.",
            503: "Agent service is temporarily unavailable.",
        }
        user_msg = user_messages.get(status, f"Agent service error ({status}).")
        raise HeadspaceError(technical, user_msg)

    def _request(self, method, url, context, *, json=None, session_token=None):
        """Execute an HTTP request, wrapping transport errors."""
        try:
            fn = getattr(self._session, method)
            kwargs = {
                "headers": self._headers(session_token),
                "timeout": self.timeout,
            }
            if json is not None:
                kwargs["json"] = json
            return fn(url, **kwargs)
        except HeadspaceError:
            raise
        except requests.exceptions.ConnectionError as e:
            raise HeadspaceError(
                f"Cannot connect to Headspace at {self.base_url}: {e}",
                "Cannot connect to agent service. Please check that Headspace "
                "is running.",
            )
        except requests.exceptions.Timeout as e:
            raise HeadspaceError(
                f"Headspace {context} timed out after {self.timeout}s: {e}",
                "Agent service timed out. Please try again.",
            )
        except Exception as e:  # noqa: BLE001
            raise HeadspaceError(
                f"Unexpected error in {context}: {e}",
                "Unexpected error communicating with agent service.",
            )

    # -- public API --------------------------------------------------------

    def create_agent(
        self,
        persona_slug: str,
        initial_prompt: str | None = None,
        feature_flags: dict | None = None,
    ) -> dict:
        """Create a remote agent session.

        POST /api/remote_agents/create. Retries once on a transient failure
        (HTTP 408/502/503 or connection error) — FR11.

        Returns dict with: agent_id, embed_url, session_token.
        """
        url = f"{self.base_url}/api/remote_agents/create"
        payload = {
            "project_slug": self.project_slug,
            "persona_slug": persona_slug,
            # Headspace requires a non-empty initial_prompt. Default to a
            # conversation-first greeting so Ray waits for questions rather
            # than dumping an orientation data wall (FR21).
            "initial_prompt": initial_prompt
            or (
                "You are now live inside the CityLab energy dashboard. Greet "
                "the operator in one short sentence and wait for their "
                "questions. Do not run any commands yet."
            ),
        }
        if feature_flags is not None:
            payload["feature_flags"] = feature_flags

        last_error = None
        for attempt in range(2):
            try:
                resp = self._request("post", url, "create_agent", json=payload)

                if resp.status_code in (408, 502, 503) and attempt == 0:
                    logger.warning(
                        "Headspace create_agent got %d, retrying once",
                        resp.status_code,
                    )
                    continue

                if not resp.ok:
                    self._handle_error(resp, "create_agent")

                data = resp.json()
                return {
                    "agent_id": str(data["agent_id"]),
                    "embed_url": data["embed_url"],
                    "session_token": data["session_token"],
                }

            except HeadspaceError as e:
                if attempt == 0 and "connect" in e.technical_message.lower():
                    last_error = e
                    continue
                raise

        if last_error:
            raise last_error
        raise HeadspaceError(
            "create_agent exhausted retries with no response",
            "Could not start the agent. Please try again.",
        )

    def check_alive(self, agent_id: str, session_token: str) -> bool:
        """Liveness probe — GET /api/remote_agents/{id}/alive.

        Returns True if alive, False if dead/not-found or on any error.
        """
        url = f"{self.base_url}/api/remote_agents/{agent_id}/alive"
        try:
            resp = self._request(
                "get", url, "check_alive", session_token=session_token
            )
            if resp.status_code == 404:
                return False
            if not resp.ok:
                logger.warning(
                    "Headspace check_alive returned %d for agent %s",
                    resp.status_code,
                    agent_id,
                )
                return False
            return True
        except HeadspaceError:
            logger.warning("Headspace check_alive failed for agent %s", agent_id)
            return False

    def shutdown_agent(self, agent_id: str, session_token: str) -> bool:
        """Shut down an agent — POST /api/remote_agents/{id}/shutdown.

        Idempotent: a 404 (already gone) is treated as success.
        """
        url = f"{self.base_url}/api/remote_agents/{agent_id}/shutdown"
        resp = self._request(
            "post", url, "shutdown_agent", session_token=session_token
        )
        if resp.status_code == 404:
            logger.info("Agent %s already gone (404), treating as success", agent_id)
            return True
        if not resp.ok:
            self._handle_error(resp, "shutdown_agent")
        return True

    def send_message(self, agent_id: str, message: str, session_token: str) -> dict:
        """Send a message — POST /api/remote_agents/{id}/message.

        Returns dict with: status, agent_id, command_id (when present).
        """
        url = f"{self.base_url}/api/remote_agents/{agent_id}/message"
        resp = self._request(
            "post",
            url,
            "send_message",
            json={"message": message},
            session_token=session_token,
        )
        if not resp.ok:
            self._handle_error(resp, "send_message")
        data = resp.json()
        return {
            "status": data.get("status"),
            "agent_id": data.get("agent_id"),
            "command_id": data.get("command_id"),
        }


def trigger_agent(persona: str, action: str) -> dict | None:
    """Legacy shim — start an agent and send it an initial action prompt.

    Retained so the existing scheduler callsite keeps working (FR12). Builds a
    HeadspaceClient from app config, creates the agent with ``action`` as the
    initial prompt. Returns None (with a warning) if Headspace is unconfigured.
    """
    config = current_app.config.get("CITYLAB_CONFIG", {})
    headspace_cfg = config.get("headspace", {})
    url = headspace_cfg.get("url", "")
    if not url:
        logger.warning("Headspace URL not configured — skipping agent trigger")
        return None

    project_slug = headspace_cfg.get("project_name", "citylab")
    timeout = headspace_cfg.get("timeout_seconds", 30)
    client = HeadspaceClient(url, project_slug, timeout)
    try:
        result = client.create_agent(persona_slug=persona, initial_prompt=action)
        logger.info("Agent dispatched: persona=%s, action=%s", persona, action)
        return result
    except HeadspaceError as e:
        logger.error("Headspace dispatch failed: %s", e.technical_message)
        raise
