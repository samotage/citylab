"""CLI commands: solar group."""

import json
from urllib.parse import urlencode

import click

from citylab.cli_wrapper.client import APIClient


@click.group("solar")
def solar_group():
    """Solcast solar irradiance forecasts across Vic/SA solar regions."""
    pass


@solar_group.command("summary")
def summary():
    """Current irradiance + next-24h solar outlook grouped by region relevance."""
    client = APIClient()
    result = client.get("/api/v1/solar/summary")
    print(json.dumps(result, indent=2))


@solar_group.command("outlook")
@click.option("--days", default=3, type=int, help="Outlook horizon in days.")
def outlook(days):
    """Multi-day solar outlook: per-location peak GHI + cloud opacity by day."""
    client = APIClient()
    qs = urlencode({"days": days})
    result = client.get(f"/api/v1/solar/outlook?{qs}")
    print(json.dumps(result, indent=2))


@solar_group.command("forecasts")
@click.option("--location", default=None, help="Name, id, state, or relevance group.")
@click.option("--from", "dt_from", default=None, help="Start (ISO or YYYY-MM-DD).")
@click.option("--to", "dt_to", default=None, help="End (ISO or YYYY-MM-DD).")
def forecasts(location, dt_from, dt_to):
    """Irradiance forecasts (GHI/DNI/DHI) for a location (latest issue)."""
    client = APIClient()
    params = {}
    if location:
        params["location"] = location
    if dt_from:
        params["from"] = dt_from
    if dt_to:
        params["to"] = dt_to
    qs = ("?" + urlencode(params)) if params else ""
    result = client.get(f"/api/v1/solar/forecasts{qs}")
    print(json.dumps(result, indent=2))
