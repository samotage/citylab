"""CLI commands: energy group."""

import json
from urllib.parse import urlencode

import click

from citylab.cli_wrapper.client import APIClient


def _range_qs(region, dt_from, dt_to):
    params = {"region": region}
    if dt_from:
        params["from"] = dt_from
    if dt_to:
        params["to"] = dt_to
    return urlencode(params)


@click.group("energy")
def energy_group():
    """Victorian energy market data."""
    pass


@energy_group.command("summary")
@click.option("--region", default="VIC1", help="Region (default VIC1)")
def summary(region):
    """Current market snapshot an agent can reason on in one call."""
    client = APIClient()
    result = client.get(f"/api/v1/energy/summary?region={region}")
    print(json.dumps(result, indent=2))


@energy_group.command("prices")
@click.option("--region", default="VIC1", help="Region (default VIC1)")
@click.option("--from", "dt_from", default=None, help="Start time (ISO or YYYY-MM-DD)")
@click.option("--to", "dt_to", default=None, help="End time (ISO or YYYY-MM-DD)")
def prices(region, dt_from, dt_to):
    """Historical/current spot prices."""
    client = APIClient()
    result = client.get(f"/api/v1/energy/prices?{_range_qs(region, dt_from, dt_to)}")
    print(json.dumps(result, indent=2))


@energy_group.command("generation")
@click.option("--region", default="VIC1", help="Region (default VIC1)")
@click.option("--from", "dt_from", default=None, help="Start time (ISO or YYYY-MM-DD)")
@click.option("--to", "dt_to", default=None, help="End time (ISO or YYYY-MM-DD)")
def generation(region, dt_from, dt_to):
    """Generation mix by fuel type."""
    client = APIClient()
    result = client.get(f"/api/v1/energy/generation?{_range_qs(region, dt_from, dt_to)}")
    print(json.dumps(result, indent=2))


@energy_group.command("interconnectors")
@click.option("--from", "dt_from", default=None, help="Start time (ISO or YYYY-MM-DD)")
@click.option("--to", "dt_to", default=None, help="End time (ISO or YYYY-MM-DD)")
def interconnectors(dt_from, dt_to):
    """Interconnector flows (Basslink, Heywood, Murraylink, VNI, VNI West)."""
    client = APIClient()
    result = client.get(f"/api/v1/energy/interconnectors?{_range_qs('VIC1', dt_from, dt_to)}")
    print(json.dumps(result, indent=2))


@energy_group.command("forecasts")
@click.option("--region", default="VIC1", help="Region (default VIC1)")
def forecasts(region):
    """Forward price forecasts."""
    client = APIClient()
    result = client.get(f"/api/v1/energy/forecasts?region={region}")
    print(json.dumps(result, indent=2))
