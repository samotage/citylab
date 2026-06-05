"""CLI commands: dispatch group — storage dispatch optimiser surface."""

import json
from urllib.parse import urlencode

import click

from citylab.cli_wrapper.client import APIClient


@click.group("dispatch")
def dispatch_group():
    """Battery storage dispatch — state, recommendations, decision log."""
    pass


@dispatch_group.command("status")
def status():
    """Current state of all batteries and their last dispatch decision."""
    client = APIClient()
    result = client.get("/api/v1/energy/dispatch/status")
    print(json.dumps(result, indent=2))


@dispatch_group.command("recommend")
@click.option("--battery", required=True, help="Battery name, e.g. 'City BESS Alpha'")
def recommend(battery):
    """Run the dispatch engine now and show the recommendation (no execute)."""
    client = APIClient()
    qs = urlencode({"battery": battery})
    result = client.get(f"/api/v1/energy/dispatch/recommend?{qs}")
    print(json.dumps(result, indent=2))


@dispatch_group.command("log")
@click.option("--battery", required=True, help="Battery name, e.g. 'City BESS Alpha'")
@click.option("--limit", default=50, help="Number of events (default 50)")
def log(battery, limit):
    """Recent dispatch decisions with reasons, newest first."""
    client = APIClient()
    qs = urlencode({"battery": battery, "limit": limit})
    result = client.get(f"/api/v1/energy/dispatch/log?{qs}")
    print(json.dumps(result, indent=2))
