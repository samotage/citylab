"""CLI commands: data group (source-agnostic)."""

import json

import click

from citylab.cli_wrapper.client import APIClient


@click.group("data")
def data_group():
    """Data source registry and cross-source intelligence."""
    pass


@data_group.command("sources")
def list_sources():
    """List registered data sources and their status."""
    client = APIClient()
    result = client.get("/api/v1/data/sources")
    print(json.dumps(result, indent=2))


@data_group.command("status")
@click.option("--id", "source_id", required=True, type=int, help="Data source ID")
def source_status(source_id):
    """Show fetch status for one data source."""
    client = APIClient()
    result = client.get(f"/api/v1/data/sources/{source_id}/status")
    print(json.dumps(result, indent=2))


@data_group.command("fetch")
@click.option("--id", "source_id", required=True, type=int, help="Data source ID")
def trigger_fetch(source_id):
    """Manually trigger an ingestion cycle for a data source."""
    client = APIClient()
    result = client.post(f"/api/v1/data/sources/{source_id}/fetch")
    print(json.dumps(result, indent=2))


@data_group.command("market-intelligence")
@click.option("--region", default="VIC1", help="Region (default VIC1)")
def market_intelligence(region):
    """Cross-source market intelligence summary in one call."""
    client = APIClient()
    result = client.get(f"/api/v1/data/market-intelligence?region={region}")
    print(json.dumps(result, indent=2))
