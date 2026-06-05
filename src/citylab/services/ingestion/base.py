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
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
BASE_BACKOFF_SECONDS = 1.0

# Maximum automatic gap-fill window per scheduled run. Larger gaps require an
# explicit `flask backfill` (FR5 / D3).
MAX_GAP_FILL = timedelta(days=7)


class BaseFetcher(ABC):
    """Abstract base for all data source fetchers."""

    #: source_type string this fetcher handles (set on subclass)
    source_type: str = "base"

    #: normal collection interval in seconds. Gap-fill triggers when the gap
    #: since last_fetch_at exceeds 2x this value. Overridden per fetcher.
    #: (OpenNEM 10min, BOM 6hr, Solcast 2hr per FR5.)
    normal_interval_seconds: int = 600

    #: max fetch attempts before recording an error. None -> module default
    #: (MAX_ATTEMPTS). Set to 1 on fetchers with a metered request budget
    #: (e.g. Solcast) so a failed fetch is NOT retried and never multiplies
    #: real, budget-consuming API calls.
    max_attempts: int | None = None

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

    def fetch_range(self, start: datetime, end: datetime, progress=None):
        """Fetch raw data for a specific [start, end) date range.

        Returns the same payload shape as fetch() so transform()/store() work
        unchanged. Used by the backfill CLI (FR3) and gap-fill (FR5).

        ``progress`` is an optional callback ``progress(done, total, label)``
        invoked per internal chunk so callers can report progress.

        Default raises NotImplementedError; sources that don't support
        historical queries (Solcast) keep this default with a clear message.
        """
        raise NotImplementedError(
            f"{self.source_type} does not support fetch_range()"
        )

    # --- orchestration ---

    def run(self) -> dict:
        """Run fetch → transform → store with retry, updating DataSource status.

        Returns a result dict: {ok, rows, attempts, error}.
        """
        from citylab.extensions import db

        attempts = 0
        last_exc = None
        rows = 0
        max_attempts = self.max_attempts or MAX_ATTEMPTS

        # Gap-fill: if the source was disabled/missed runs, fill the gap before
        # the normal current-interval fetch so the dataset stays continuous.
        rows += self._gap_fill()

        while attempts < max_attempts:
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
                    max_attempts,
                    self.data_source.name,
                    exc,
                )
                if attempts < max_attempts:
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

    def _gap_fill(self) -> int:
        """Detect and fill a collection gap via fetch_range (FR5 / D3).

        If the gap since last_fetch_at exceeds 2x the normal interval and is
        within MAX_GAP_FILL, fetch the whole gap range before the normal fetch.
        Gaps larger than MAX_GAP_FILL are logged and skipped (use `flask
        backfill`). Fetchers that don't implement fetch_range (Solcast) skip
        gap-fill silently.

        Returns the number of rows written during gap-fill (0 if none).
        """
        last = self.data_source.last_fetch_at
        if last is None:
            # First run ever — the fetcher's own first-run backfill handles this.
            return 0

        now = datetime.now(timezone.utc)
        last_utc = last if last.tzinfo else last.replace(tzinfo=timezone.utc)
        gap = now - last_utc

        threshold = timedelta(seconds=2 * self.normal_interval_seconds)
        if gap <= threshold:
            return 0  # no meaningful gap

        if gap > MAX_GAP_FILL:
            logger.warning(
                "%s: gap of %s exceeds max auto gap-fill (%s); skipping — use "
                "`flask backfill`",
                self.data_source.name,
                gap,
                MAX_GAP_FILL,
            )
            return 0

        try:
            raw = self.fetch_range(last_utc, now)
        except NotImplementedError:
            # Source can't backfill (e.g. Solcast) — skip gap-fill quietly.
            return 0
        except Exception as exc:  # noqa: BLE001 - gap-fill is best-effort
            logger.warning(
                "%s: gap-fill fetch_range failed (%s); continuing with normal "
                "fetch",
                self.data_source.name,
                exc,
            )
            return 0

        try:
            records = self.transform(raw)
            written = self.store(records)
            logger.info(
                "%s: gap-fill wrote %s rows for gap %s", self.data_source.name,
                written, gap,
            )
            return written
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "%s: gap-fill transform/store failed (%s)",
                self.data_source.name, exc,
            )
            return 0

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
