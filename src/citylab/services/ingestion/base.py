"""BaseFetcher — the fetch/transform/store contract plus run() orchestrator.

A fetcher implements three methods:
  - fetch()      -> raw payload from the source (network I/O lives here)
  - transform(raw) -> list of ORM model instances (or dicts) ready to persist
  - store(records) -> int count of rows persisted

run() wires them together with retry/backoff and updates the DataSource status
columns (last_fetch_at, last_fetch_status, last_error, next_fetch_at).
"""

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
BASE_BACKOFF_SECONDS = 1.0


class BaseFetcher(ABC):
    """Abstract base for all data source fetchers."""

    #: source_type string this fetcher handles (set on subclass)
    source_type: str = "base"

    def __init__(self, data_source):
        """data_source: a DataSource ORM instance."""
        self.data_source = data_source
        self.config = data_source.config or {}

    # --- contract methods (implement on subclass) ---

    @abstractmethod
    def fetch(self):
        """Pull raw data from the source. Returns an opaque payload."""
        raise NotImplementedError

    @abstractmethod
    def transform(self, raw):
        """Normalise raw payload into persistable records (model instances)."""
        raise NotImplementedError

    @abstractmethod
    def store(self, records) -> int:
        """Persist records. Returns number of rows written."""
        raise NotImplementedError

    # --- orchestration ---

    def run(self) -> dict:
        """Run fetch → transform → store with retry, updating DataSource status.

        Returns a result dict: {ok, rows, attempts, error}.
        """
        from citylab.extensions import db

        attempts = 0
        last_exc = None
        rows = 0

        while attempts < MAX_ATTEMPTS:
            attempts += 1
            try:
                raw = self.fetch()
                records = self.transform(raw)
                rows = self.store(records)
                last_exc = None
                break
            except Exception as exc:  # noqa: BLE001 - we record and retry
                last_exc = exc
                logger.warning(
                    "Fetch attempt %s/%s failed for %s: %s",
                    attempts,
                    MAX_ATTEMPTS,
                    self.data_source.name,
                    exc,
                )
                if attempts < MAX_ATTEMPTS:
                    time.sleep(BASE_BACKOFF_SECONDS * (2 ** (attempts - 1)))

        now = datetime.now(timezone.utc)
        self.data_source.last_fetch_at = now
        if last_exc is None:
            self.data_source.last_fetch_status = "success"
            self.data_source.last_error = None
        else:
            self.data_source.last_fetch_status = "error"
            self.data_source.last_error = str(last_exc)[:2000]

        # next_fetch_at is best-effort; the scheduler is the source of truth,
        # but we record an estimate so the API reflects scheduling intent.
        self.data_source.next_fetch_at = self._estimate_next_fetch(now)

        try:
            db.session.add(self.data_source)
            db.session.commit()
        except Exception as commit_exc:  # noqa: BLE001
            db.session.rollback()
            logger.error("Failed to persist DataSource status: %s", commit_exc)

        return {
            "ok": last_exc is None,
            "rows": rows,
            "attempts": attempts,
            "error": str(last_exc) if last_exc else None,
        }

    def _estimate_next_fetch(self, after: datetime):
        """Estimate the next fetch time from the cron expression.

        Falls back to None if the expression can't be parsed.
        """
        try:
            from apscheduler.triggers.cron import CronTrigger

            parts = (self.data_source.cron_expression or "").split()
            if len(parts) != 5:
                return None
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
            )
            return trigger.get_next_fire_time(None, after)
        except Exception:  # noqa: BLE001
            return None
