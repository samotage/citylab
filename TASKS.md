# Tasks: Historical Backfill & Continuous Collection

Source PRD: docs/prds/data/historical-backfill-continuous-collection.md
Branch: feature/hack-historical-backfill-continuous-collection

## Task List

### Foundation — DB + upsert infrastructure

- [x] 1. **Dedup + UNIQUE constraints migration (FR1, Data Model).** Create a new Alembic migration in `migrations/versions/` that, for each of the 9 time-series tables, (a) deletes duplicate rows keeping the latest `updated_at` per natural-key group, then (b) adds a UNIQUE constraint on the natural key. Natural keys per D1: `energy_prices(region, interval_start, interval_type)`, `energy_demand(region, interval_start, demand_type)`, `generation_output(region, interval_start, fuel_type)`, `interconnector_flows(interconnector_id, interval_start)`, `generator_submissions(unit_id, interval_start, bid_band)`, `price_forecasts(region, forecast_issued_at, forecast_for, forecast_type)`, `weather_forecasts(location_id, issued_at, forecast_for, forecast_period)`, `weather_observations(location_id, observed_at)`, `solar_forecasts(location_id, issued_at, forecast_for, forecast_period)`. Name constraints `uq_<table>_<natkey>`. Run `flask db upgrade` against the dev DB to confirm it applies.

- [x] 2. **Reflect UNIQUE constraints in models.** Add matching `UniqueConstraint` entries to `__table_args__` on the affected models in `src/citylab/models/` (Energy*, Weather*, Solar*) so the ORM metadata matches the migration. Keep names identical to task 1.

- [x] 3. **Shared upsert helper (FR2 support).** Add a small helper (e.g. `upsert_records()` in `src/citylab/services/ingestion/base.py` or a new `upsert.py`) that takes a SQLAlchemy model, a list of row dicts, and the conflict-target column names, and issues `postgresql.insert(...).on_conflict_do_update(...)` updating only the mutable (non-natural-key) columns. Returns the count of rows processed. Used by all three fetchers' `store()`.

### Base infrastructure — fetch_range + gap-fill

- [x] 4. **`fetch_range()` on BaseFetcher (FR6).** Add a `fetch_range(start, end)` method to `BaseFetcher` (default raising `NotImplementedError`) returning the same payload shape as `fetch()`. Add a progress callback hook so callers can report per-chunk progress.

- [x] 5. **Gap-fill in run cycle (FR5).** Modify `BaseFetcher.run()` to: read `self.data_source.last_fetch_at`; compute gap = now − last_fetch_at; if gap > (2 × normal interval) and ≤ 7 days, call `fetch_range(last_fetch_at, now)` → transform → store before the normal `fetch()`; if gap > 7 days, log a warning and skip auto-fill. Per-source normal-interval thresholds (OpenNEM 10min, BOM 6hr, Solcast 2hr) configurable per fetcher (class attr or `config`). Guard so fetchers that don't implement `fetch_range` (Solcast) just skip gap-fill.

### Per-source: store() upserts

- [x] 6. **OpenNEM store() upsert (FR2).** Replace the `db.session.add(rec)` loop in `OpenNEMFetcher.store()` (opennem.py ~line 320) with the task-3 upsert helper, keyed per target table. Verify re-running the same interval does not double row counts.

- [x] 7. **BOM store() upsert (FR2).** Same refactor for `BOMFetcher.store()` in `bom.py` — weather_forecasts and weather_observations.

- [x] 8. **Solcast store() upsert (FR2).** Same refactor for `SolcastFetcher.store()` in `solcast.py` — solar_forecasts.

### Per-source: real API parsing + fetch_range

- [x] 9. **OpenNEM real parsing (FR7).** In `_fetch_live()`, replace the synthetic-after-probe stub with real parsing of the `/stats/power/network/NEM/VIC1` JSON `history`/`forecast` sections into the existing payload shape (prices, demand, generation, interconnectors), mapping fuel types via `OPENNEM_FUEL_MAP`. Set `source: "live"` on success. Preserve synthetic fallback on any parse/HTTP failure (D7), clearly logged.

- [x] 10. **OpenNEM `fetch_range()` (FR8).** Implement `fetch_range(start, end)` using OpenNEM's date-range query params, internally chunking if the API limits response size, reusing the task-9 parsing logic. Returns one payload per call covering the requested range.

- [x] 11. **BOM real parsing (FR9).** In BOM `_fetch_live()`, replace stub with real parsing of geohash endpoints (`/v1/locations/{geohash}/forecasts/daily`, `/3-hourly`, `/observations`). Derive the BOM geohash from each `WeatherLocation` lat/lon (utility function preferred; column optional per Data Model). Parse temp, wind, rainfall, humidity, cloud cover. Synthetic fallback preserved (D7).

- [x] 12. **BOM `fetch_range()` — observations only (FR10, D5).** Implement `fetch_range(start, end)` fetching historical observations (not forecasts). If BOM history depth is limited, backfill as far as available and log actual coverage ("BOM backfill: N months available, requested 12").

- [ ] 13. **Solcast forward-only guard (FR11).** Leave Solcast fetch/synthetic behaviour unchanged. Implement `fetch_range()` to raise `NotImplementedError("Solcast historical backfill not supported — use archive import")`.

### CLI + agent wrapper

- [ ] 14. **`flask backfill` CLI command (FR3).** Add `flask backfill --source <opennem|bom|solcast> [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--chunk-days N]` in `src/citylab/cli/commands.py`. Defaults: `--from` = 12 months ago, `--to` = now, `--chunk-days` = 1. Iterate chunk-by-chunk calling `fetcher.fetch_range()` → transform → store; print progress `[opennem] 2025-06-01 ... 42/365 days (11.5%) — 1,204 rows`; on chunk error log and continue, report failures at the end. Idempotent via upsert. Handle Solcast's `NotImplementedError` with a clear archive-import message.

- [ ] 15. **`cli-citylab data backfill` wrapper + endpoint (FR4).** Add a `data/backfill` REST endpoint in `src/citylab/routes/api_v1/data.py` (Bearer auth) that triggers the backfill (thin wrapper shelling to the Flask CLI, or inline — builder's discretion), and a `cli-citylab data backfill --source <s> [--from] [--to]` subcommand in `src/citylab/cli_wrapper/commands_data.py` that calls it and reports progress/job status.

### Tests + polish

- [ ] 16. **Tests.** Add/extend tests in `tests/data/` for: upsert idempotency (run fetcher twice, row count stable), gap-fill (last_fetch_at gap triggers fetch_range), backfill CLI happy path, Solcast fetch_range raises, synthetic fallback still fires on API failure. Run `pytest tests/data/` and confirm no regressions in the broader suite.

## Demo Script

```bash
# 0. Apply the new migration (UNIQUE constraints + dedup) against dev DB
flask db upgrade
psql citylab -c "\d+ energy_prices" | grep -i unique   # constraint present

# 1. Backfill 12 months of real OpenNEM data
flask backfill --source opennem --from 2025-06-04 --to 2026-06-04
#   -> progress lines per chunk, e.g. "[opennem] 2025-06-04 ... 1/365 days (0.3%) — N rows"

# 2. Idempotency: capture row count, re-run, confirm unchanged
psql citylab -c "SELECT count(*) FROM energy_prices;"      # note count
flask backfill --source opennem --from 2025-06-04 --to 2026-06-04
psql citylab -c "SELECT count(*) FROM energy_prices;"      # SAME count (upsert, no dupes)

# 3. BOM historical observation backfill (coverage logged)
flask backfill --source bom
#   -> logs actual coverage depth, e.g. "BOM backfill: 3 months available, requested 12"

# 4. Gap-fill check: disable a source, wait, re-enable, confirm continuous data
cli-citylab data sources                                   # find opennem source id / status
# (disable opennem, wait > gap threshold, re-enable, trigger a run)
cli-citylab data verify --region VIC1                      # no missing intervals reported
psql citylab -c "SELECT interval_start FROM energy_prices WHERE region='VIC1' ORDER BY interval_start DESC LIMIT 20;"  # continuous, no gap

# 5. Agent-facing wrapper triggers backfill
cli-citylab data backfill --source opennem --from 2026-05-01 --to 2026-06-01

# 6. Synthetic fallback still works (APIs unreachable):
#    with no network / bad endpoint, a normal fetch falls back to synthetic and
#    payloads show source != "live". Confirm via:
cli-citylab energy summary --region VIC1                   # still returns data
#    and existing dashboard at /energy renders unchanged with real data.

# 7. Solcast backfill exits with archive-import message
flask backfill --source solcast
#   -> "Solcast historical backfill not supported — use archive import"

# 8. No regressions
pytest tests/data/
```
