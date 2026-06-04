"""Flask CLI commands — seed-admin, backfill, etc."""

import os
from datetime import datetime, timedelta, timezone

import click


def register_cli_commands(app):
    """Register CLI commands with the Flask app."""

    @app.cli.command("seed-admin")
    def seed_admin():
        """Seed admin user from environment variables."""
        from citylab.extensions import db
        from citylab.models.user import User

        email = os.environ.get("CITYLAB_ADMIN_EMAIL")
        password = os.environ.get("CITYLAB_ADMIN_PASSWORD")

        if not email or not password:
            click.echo("Error: CITYLAB_ADMIN_EMAIL and CITYLAB_ADMIN_PASSWORD must be set.")
            return

        existing = db.session.query(User).filter_by(email=email).first()
        if existing:
            click.echo(f"Admin user {email} already exists.")
            return

        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin user {email} created.")

    @app.cli.command("seed-data-sources")
    def seed_data_sources_cmd():
        """Seed DataSource rows + weather locations from config.yaml."""
        from citylab.services.ingestion.seed import (
            seed_data_sources,
            seed_solar_locations,
            seed_weather_locations,
        )

        results = seed_data_sources()
        if not results:
            click.echo("No data_sources configured in config.yaml.")
        else:
            for r in results:
                click.echo(f"  {r['name']} ({r['source_type']}) -> {r['cron_expression']}")
            click.echo(f"Seeded/updated {len(results)} data source(s).")

        locations = seed_weather_locations()
        for loc in locations:
            click.echo(f"  {loc['name']} [{loc['state']}] ({loc['region_relevance']})")
        click.echo(f"Seeded/updated {len(locations)} weather location(s).")

        solar_locations = seed_solar_locations()
        for loc in solar_locations:
            click.echo(f"  {loc['name']} [{loc['state']}] ({loc['region_relevance']})")
        click.echo(f"Seeded/updated {len(solar_locations)} solar location(s).")

    @app.cli.command("backfill")
    @click.option(
        "--source",
        "source_type",
        required=True,
        type=click.Choice(["opennem", "bom", "solcast"]),
        help="Data source to backfill.",
    )
    @click.option("--from", "from_date", default=None,
                  help="Start date YYYY-MM-DD (default: 12 months ago).")
    @click.option("--to", "to_date", default=None,
                  help="End date YYYY-MM-DD (default: now).")
    @click.option("--chunk-days", default=1, type=int,
                  help="Chunk size in days (default: 1).")
    def backfill_cmd(source_type, from_date, to_date, chunk_days):
        """Backfill historical data for a source over a date range (FR3)."""
        result = run_backfill(
            source_type, from_date, to_date, chunk_days,
            emit=click.echo,
        )
        if result.get("error"):
            raise SystemExit(1)


def _parse_date(s):
    """Parse a YYYY-MM-DD string into a UTC datetime (start of day)."""
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def run_backfill(source_type, from_date, to_date, chunk_days=1, emit=None):
    """Run a chunked historical backfill for one source.

    Iterates the [from, to] range in ``chunk_days``-sized chunks, calling the
    fetcher's fetch_range -> transform -> store for each chunk. Idempotent via
    upsert. On a chunk error it logs and continues, reporting failures at the
    end. Returns a result dict {source, chunks, rows, failures, error}.

    ``emit`` is an optional callback (e.g. click.echo) for progress lines; if
    None, progress is collected into the returned ``log`` list only.
    """
    from citylab.extensions import db
    from citylab.models.data_source import DataSource
    from citylab.services.ingestion.registry import get_fetcher

    log: list[str] = []

    def _emit(msg):
        log.append(msg)
        if emit:
            emit(msg)

    chunk_days = max(1, int(chunk_days or 1))
    now = datetime.now(timezone.utc)
    start = _parse_date(from_date) if from_date else (now - timedelta(days=365))
    end = _parse_date(to_date) if to_date else now
    if start >= end:
        return {"source": source_type, "error": "from must be before to",
                "rows": 0, "chunks": 0, "failures": [], "log": log}

    ds = db.session.query(DataSource).filter_by(source_type=source_type).first()
    if not ds:
        return {"source": source_type, "error": f"no DataSource for {source_type}",
                "rows": 0, "chunks": 0, "failures": [], "log": log}

    fetcher_cls = get_fetcher(source_type)
    if not fetcher_cls:
        return {"source": source_type, "error": f"no fetcher for {source_type}",
                "rows": 0, "chunks": 0, "failures": [], "log": log}
    fetcher = fetcher_cls(ds)

    # Build chunk boundaries.
    chunks = []
    cur = start
    step = timedelta(days=chunk_days)
    while cur < end:
        chunks.append((cur, min(cur + step, end)))
        cur += step
    total_chunks = len(chunks)

    total_rows = 0
    failures = []
    for i, (cs, ce) in enumerate(chunks, start=1):
        try:
            raw = fetcher.fetch_range(cs, ce)
            records = fetcher.transform(raw)
            rows = fetcher.store(records)
            db.session.commit()
            total_rows += rows
            pct = (i / total_chunks * 100.0) if total_chunks else 100.0
            _emit(
                f"[{source_type}] {cs.date()} ... {i}/{total_chunks} chunks "
                f"({pct:.1f}%) — {rows:,} rows"
            )
        except NotImplementedError as exc:
            db.session.rollback()
            _emit(f"[{source_type}] backfill not supported: {exc}")
            return {"source": source_type, "error": str(exc), "rows": total_rows,
                    "chunks": i - 1, "failures": failures, "log": log}
        except Exception as exc:  # noqa: BLE001 - continue past chunk errors
            db.session.rollback()
            failures.append({"chunk": f"{cs.date()}..{ce.date()}", "error": str(exc)})
            _emit(f"[{source_type}] {cs.date()} CHUNK FAILED: {exc}")

    # Stamp last_fetch_at so forward collection resumes seamlessly.
    try:
        ds.last_fetch_at = end
        ds.last_fetch_status = "success" if not failures else "error"
        db.session.commit()
    except Exception:  # noqa: BLE001
        db.session.rollback()

    _emit(
        f"[{source_type}] DONE — {total_rows:,} rows over {total_chunks} chunks; "
        f"{len(failures)} chunk failure(s)."
    )
    return {"source": source_type, "rows": total_rows, "chunks": total_chunks,
            "failures": failures, "error": None, "log": log}
