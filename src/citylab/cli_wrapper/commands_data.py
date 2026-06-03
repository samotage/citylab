"""CLI commands: data group (source-agnostic)."""

import json
import sys

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


# Pretty status glyphs (fall back gracefully where unicode is unwanted).
_PASS = "✓"  # ✓
_FAIL = "✗"  # ✗


@data_group.command("verify")
@click.option("--region", default="VIC1", help="Region (default VIC1)")
@click.option("--json", "as_json", is_flag=True, help="Emit the raw report as JSON.")
def verify(region, as_json):
    """Pre-hackathon gate: run completeness/freshness/consistency checks.

    Runs the shared data_verify service against the database (read-only, no live
    server required) and prints per-source (OpenNEM / BOM / Solcast) and
    per-category results. Exits non-zero on any failure so CI / a smoke step can
    gate on it.
    """
    from citylab import create_app
    from citylab.services import data_verify

    app = create_app()
    with app.app_context():
        report = data_verify.verify(region=region)

    if as_json:
        print(json.dumps(report.to_dict(), indent=2))
        sys.exit(0 if report.passed else 1)

    overall = _PASS if report.passed else _FAIL
    click.echo(f"\nData verify [{region}]  overall: {overall}\n")
    for src in report.sources:
        glyph = _PASS if src.passed else _FAIL
        label = src.source.upper()
        if not src.has_data:
            click.echo(f"  {_FAIL} {label:<9} no data (pipeline never seeded/run)")
            continue
        click.echo(f"  {glyph} {label}")
        for cat in src.categories:
            cglyph = _PASS if cat.passed else _FAIL
            passed_n = sum(1 for c in cat.checks if c.passed)
            click.echo(
                f"      {cglyph} {cat.name:<13} {passed_n}/{len(cat.checks)} checks"
            )
            for chk in cat.checks:
                if not chk.passed:
                    click.echo(f"          {_FAIL} {chk.name}: {chk.detail}")
    click.echo("")
    sys.exit(0 if report.passed else 1)
