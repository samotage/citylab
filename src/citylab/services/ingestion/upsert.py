"""Shared bulk-upsert helper for time-series ingestion.

All three fetchers persist time-series rows that have a UNIQUE constraint on a
natural key (see the eb3b9c51c3f5 migration). Re-running a fetcher for the same
interval — whether from a scheduled run, a gap-fill, or a backfill — must update
the existing row rather than create a duplicate.

This helper issues a single PostgreSQL ``INSERT ... ON CONFLICT (natural_key)
DO UPDATE SET ...`` per call, updating only the mutable (non-natural-key)
columns. It is the idempotency primitive the whole PRD rests on.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger(__name__)


def instance_to_dict(instance) -> dict:
    """Extract a column->value dict from an unpersisted model instance.

    Skips the auto-managed id (None before insert) and lets created_at/updated_at
    defaults apply at insert time, so only meaningful set columns are included.
    """
    out = {}
    for col in instance.__table__.columns:
        name = col.name
        if name == "id":
            continue
        val = getattr(instance, name, None)
        # created_at/updated_at are typically unset on fresh instances — let the
        # column defaults populate them. If explicitly set, keep the value.
        if name in ("created_at", "updated_at") and val is None:
            continue
        out[name] = val
    return out


def upsert_records(model, rows: list[dict], conflict_cols: list[str]) -> int:
    """Bulk-upsert ``rows`` into ``model``'s table.

    Args:
        model: SQLAlchemy model class (e.g. EnergyPrice).
        rows: list of column->value dicts (one per row to persist).
        conflict_cols: the natural-key column names that form the UNIQUE
            constraint / ON CONFLICT target.

    Behaviour:
        - Inserts new rows.
        - On conflict (natural key already present) updates the mutable columns
          — every inserted column that is NOT part of the natural key and is not
          an auto-managed column (id / created_at). updated_at is bumped to the
          new value so the latest write wins.

    Returns the number of rows processed (len(rows)).
    """
    if not rows:
        return 0

    from citylab.extensions import db

    table = model.__table__

    # Columns we never overwrite on conflict: the natural key, the primary key,
    # and created_at (the original insert time is preserved).
    immutable = set(conflict_cols) | {"id", "created_at"}

    # The set of columns actually present across the supplied rows determines
    # what we insert; the update set is those minus the immutable columns.
    present_cols: set[str] = set()
    for r in rows:
        present_cols.update(r.keys())
    # Restrict to real table columns to be safe.
    table_col_names = {c.name for c in table.columns}
    insert_cols = present_cols & table_col_names

    stmt = pg_insert(table).values(rows)

    update_cols = {
        name: getattr(stmt.excluded, name)
        for name in insert_cols
        if name not in immutable
    }

    if update_cols:
        # onupdate=... does not fire on ON CONFLICT DO UPDATE, so bump
        # updated_at explicitly to keep "latest write wins" semantics that the
        # dedup migration (updated_at DESC) and freshness checks rely on.
        if "updated_at" in table_col_names:
            update_cols["updated_at"] = datetime.now(timezone.utc)
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_=update_cols,
        )
    else:
        # No mutable columns to update — natural key is the whole row; just skip
        # duplicates rather than erroring.
        stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols)

    db.session.execute(stmt)
    db.session.flush()
    return len(rows)
