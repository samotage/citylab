"""CLI commands: app group."""

import json

import click

from citylab.cli_wrapper.client import APIClient


@click.group("app")
def app_group():
    """App management commands."""
    pass


@app_group.command("status")
def app_status():
    """Get app status."""
    client = APIClient()
    result = client.get("/api/v1/app/status")
    print(json.dumps(result, indent=2))
