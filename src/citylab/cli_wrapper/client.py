"""HTTP client for CLI → API communication."""

import json
import sys

import requests

from citylab.cli_wrapper.config import get_api_token, get_base_url


class APIClient:
    """HTTP client with Bearer token auth and error mapping."""

    def __init__(self):
        self.base_url = get_base_url()
        self.token = get_api_token()

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get(self, path: str) -> dict:
        """GET request to API."""
        url = f"{self.base_url}{path}"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=10)
            return self._handle_response(resp)
        except requests.ConnectionError:
            self._error("Cannot connect to CityLab server", exit_code=2)
        except requests.Timeout:
            self._error("Request timed out", exit_code=2)

    def post(self, path: str, data: dict = None) -> dict:
        """POST request to API."""
        url = f"{self.base_url}{path}"
        try:
            resp = requests.post(url, headers=self._headers(), json=data or {}, timeout=10)
            return self._handle_response(resp)
        except requests.ConnectionError:
            self._error("Cannot connect to CityLab server", exit_code=2)
        except requests.Timeout:
            self._error("Request timed out", exit_code=2)

    def delete(self, path: str) -> dict:
        """DELETE request to API."""
        url = f"{self.base_url}{path}"
        try:
            resp = requests.delete(url, headers=self._headers(), timeout=10)
            return self._handle_response(resp)
        except requests.ConnectionError:
            self._error("Cannot connect to CityLab server", exit_code=2)
        except requests.Timeout:
            self._error("Request timed out", exit_code=2)

    def _handle_response(self, resp: requests.Response) -> dict:
        """Handle API response, mapping errors to exit codes."""
        try:
            body = resp.json()
        except (json.JSONDecodeError, ValueError):
            body = {"raw": resp.text}

        if resp.status_code == 401:
            self._error("Unauthorized — check your API token", exit_code=1)
        elif resp.status_code == 404:
            self._error("Not found", exit_code=1)
        elif resp.status_code >= 400:
            error = body.get("error", f"HTTP {resp.status_code}")
            self._error(error, exit_code=3)

        return body

    @staticmethod
    def _error(message: str, exit_code: int = 1):
        """Print error and exit."""
        print(json.dumps({"ok": False, "error": message}), file=sys.stderr)
        sys.exit(exit_code)
