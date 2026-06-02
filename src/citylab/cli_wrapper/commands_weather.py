"""CLI commands: weather group."""

import json
from urllib.parse import urlencode

import click

from citylab.cli_wrapper.client import APIClient


@click.group("weather")
def weather_group():
    """BOM weather forecasts and observations across energy-relevant regions."""
    pass


@weather_group.command("summary")
def summary():
    """Current conditions + near-term outlook grouped by region relevance."""
    client = APIClient()
    result = client.get("/api/v1/weather/summary")
    print(json.dumps(result, indent=2))


@weather_group.command("outlook")
@click.option(
    "--factor",
    type=click.Choice(["wind", "rain", "temperature"]),
    default="wind",
    help="Which factor to surface across the relevant corridors/catchments.",
)
@click.option("--days", default=3, type=int, help="Outlook horizon in days.")
def outlook(factor, days):
    """Filtered outlook: wind (corridors), rain (hydro catchments), temperature."""
    client = APIClient()
    qs = urlencode({"factor": factor, "days": days})
    result = client.get(f"/api/v1/weather/outlook?{qs}")
    print(json.dumps(result, indent=2))


@weather_group.command("forecasts")
@click.option("--location", default=None, help="Name, id, state, or relevance group.")
@click.option("--from", "dt_from", default=None, help="Start (ISO or YYYY-MM-DD).")
@click.option("--to", "dt_to", default=None, help="End (ISO or YYYY-MM-DD).")
def forecasts(location, dt_from, dt_to):
    """Forecasts for a location or region (latest issue)."""
    client = APIClient()
    params = {}
    if location:
        params["location"] = location
    if dt_from:
        params["from"] = dt_from
    if dt_to:
        params["to"] = dt_to
    qs = ("?" + urlencode(params)) if params else ""
    result = client.get(f"/api/v1/weather/forecasts{qs}")
    print(json.dumps(result, indent=2))


@weather_group.command("observations")
@click.option("--location", default=None, help="Name, id, state, or relevance group.")
def observations(location):
    """Latest observations for a location or region."""
    client = APIClient()
    qs = ("?" + urlencode({"location": location})) if location else ""
    result = client.get(f"/api/v1/weather/observations{qs}")
    print(json.dumps(result, indent=2))
