# Historical Backfill & Continuous Collection

## Problem

CityLab's three data fetchers (OpenNEM, BOM, Solcast) generate synthetic data with a 3–7 day backfill window. The synthetic fallback was correct for the hackathon demo, but for meaningful energy market analysis agents need 12 months of real historical data plus continuous forward collection that automatically fills gaps when a source is re-enabled after being disabled.

Today's specific gaps:
1. **No real API parsing** — all three fetchers probe the live API but still generate synthetic data regardless of the response. The parsing step was deferred during hackathon scope.
2. **No dedup** — `store()` does naive `INSERT` via `db.session.add()`. Running a fetcher twice for the same interval creates duplicate rows.
3. **No gap-fill** — OpenNEM's synthetic path has rudimentary gap detection (delta from `last_fetch_at`), but BOM and Solcast don't. None of the live paths detect or fill gaps.
4. **No backfill mechanism** — there's no CLI command or API endpoint to trigger a historical data load for a date range.

## Scope

**In scope:**
- Upsert/dedup infrastructure across all time-series tables
- Backfill CLI command with per-source, date-range parameters
- Gap-fill integrated into the scheduled collection cycle
- OpenNEM: real API response parsing + 12-month historical backfill
- BOM: real API response parsing + historical observation backfill (12 months where available)
- Solcast: forward collection only (real parsing where API key exists, synthetic fallback otherwise)

**Out of scope:**
- Solcast historical backfill (deferred — Sam has an archive in another production project; import interface will be a follow-up PRD)
- Gas market data (separate future PRD)
- AEMO secondary source parsing (generator submissions, pre-dispatch forecasts — follow-up)
- Data retention/pruning policies

## Decisions

**D1: Upsert via UNIQUE constraints + ON CONFLICT DO UPDATE.**
Every time-series table gets a UNIQUE constraint on its natural key. `store()` methods use PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` via SQLAlchemy. This is simpler and more reliable than application-level dedup (SELECT before INSERT), and it means backfill and gap-fill are idempotent — you can re-run them without creating duplicates.

Natural keys:
| Table | Natural key |
|-------|------------|
| `energy_prices` | `(region, interval_start, interval_type)` |
| `energy_demand` | `(region, interval_start, demand_type)` |
| `generation_output` | `(region, interval_start, fuel_type)` |
| `interconnector_flows` | `(interconnector_id, interval_start)` |
| `generator_submissions` | `(unit_id, interval_start, bid_band)` |
| `price_forecasts` | `(region, forecast_issued_at, forecast_for, forecast_type)` |
| `weather_forecasts` | `(location_id, issued_at, forecast_for, forecast_period)` |
| `weather_observations` | `(location_id, observed_at)` |
| `solar_forecasts` | `(location_id, issued_at, forecast_for, forecast_period)` |

**D2: Backfill via Flask CLI command, chunked by date range.**
`flask backfill --source opennem --from 2025-06-01 --to 2026-06-01` fetches data in day-sized chunks with progress reporting. Chunking avoids API rate limits and memory pressure. The command reuses the existing fetcher infrastructure — it calls a `fetch_range(start, end)` method on the fetcher rather than the normal `fetch()`.

Why Flask CLI and not a REST endpoint: backfill is a long-running operator-initiated task, not something an agent triggers mid-conversation. CLI gives progress output and can be backgrounded. The `cli-citylab data backfill` wrapper exposes it to agent tooling if needed.

**D3: Gap-fill integrated into fetcher run cycle.**
When a scheduled run fires, the fetcher checks `last_fetch_at`. If the gap exceeds the normal collection interval (e.g., >10 minutes for a 5-min source), it fetches the entire gap range before fetching the current interval. This means disabling and re-enabling a source automatically produces a continuous dataset — no manual backfill needed for short outages.

Gap-fill cap: maximum 7 days of automatic gap-fill per run. Gaps longer than 7 days require an explicit backfill command (to avoid a scheduled run accidentally trying to fetch months of data).

**D4: Natural per-source collection cadence.**
Each source keeps its own cron schedule matching the API's natural update rate:
- OpenNEM: `*/5 * * * *` (5-minute — matches NEM dispatch intervals)
- BOM: `0 */3 * * *` (3-hourly — matches BOM forecast issuance)
- Solcast: `0 * * * *` (hourly — matches Solcast update cadence)

All three get the same enable/disable + gap-fill behaviour.

**D5: BOM backfill covers observations only.**
Weather forecasts are ephemeral — you can't retrieve a forecast that was issued 6 months ago. Observations (temperature, wind, rainfall) are recorded facts and can be backfilled. Forward collection captures both forecasts and observations.

**D6: Solcast historical backfill deferred.**
Solcast's free-tier API doesn't support historical queries. Sam has a production archive of Melbourne solar irradiance data that will be imported separately. This PRD specs Solcast for forward collection only. The archive import interface is a follow-up.

**D7: Synthetic fallback preserved.**
Real API parsing is the primary path. The existing synthetic fallback remains as a safety net — if a live API call fails, the fetcher falls back to synthetic data so the demo never breaks. The synthetic path is clearly logged and flagged in API responses via the existing `source` field.

## Functional Requirements

### Infrastructure

**FR1: UNIQUE constraints on all time-series tables.**
Add a database migration that creates UNIQUE constraints on the natural keys listed in D1. These constraints serve double duty: they prevent duplicate rows AND they provide the `ON CONFLICT` target for upsert. Existing duplicate rows (if any from prior synthetic runs) must be deduped before the constraint can be applied — the migration should handle this.

Done-when: migration applies cleanly, UNIQUE constraints exist on all 9 tables, `\d+ <table>` shows the constraint.

**FR2: Bulk upsert in store() methods.**
Refactor all three fetchers' `store()` methods to use `INSERT ... ON CONFLICT (natural_key) DO UPDATE SET ...` instead of naive `db.session.add()`. Use SQLAlchemy's `insert().on_conflict_do_update()` dialect. Update the mutable columns (the data values) and leave the natural key columns unchanged.

Done-when: calling `store()` with records that share a natural key with existing rows updates those rows rather than creating duplicates. Verified by running a fetcher twice for the same interval and confirming row count doesn't double.

**FR3: Backfill CLI command.**
```
flask backfill --source <source_type> [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--chunk-days N]
```
- `--source`: required. One of `opennem`, `bom`, `solcast`.
- `--from`: start date, defaults to 12 months ago.
- `--to`: end date, defaults to now.
- `--chunk-days`: chunk size in days, defaults to 1 (one API call per day).
- Iterates day-by-day (or per `--chunk-days`), calling `fetcher.fetch_range(start, end)` for each chunk.
- Reports progress: `[opennem] 2025-06-01 ... 42/365 days (11.5%) — 1,204 rows`
- On error: logs the failed chunk, continues to the next chunk, reports failures at the end.
- Idempotent: safe to re-run — upsert handles duplicates.

Done-when: `flask backfill --source opennem --from 2025-06-04 --to 2026-06-04` populates 12 months of real OpenNEM data. Progress is reported per chunk. Re-running does not create duplicates.

**FR4: cli-citylab backfill wrapper.**
```
cli-citylab data backfill --source opennem [--from YYYY-MM-DD] [--to YYYY-MM-DD]
```
Hits a REST endpoint that triggers the backfill. For hackathon scope, this can be a thin wrapper that shells out to the Flask CLI command, or a proper async endpoint — builder's discretion. The important thing is agent tooling can trigger a backfill.

Done-when: `cli-citylab data backfill --source opennem` triggers a backfill and reports progress or job status.

**FR5: Gap-fill in scheduled runs.**
Modify `BaseFetcher.run()` (or override in each fetcher) to detect gaps:
1. Read `self.data_source.last_fetch_at`
2. Calculate gap = `now - last_fetch_at`
3. If gap > (2 × normal interval) AND gap ≤ 7 days: call `fetch_range(last_fetch_at, now)` before the normal `fetch()`
4. If gap > 7 days: log a warning ("gap too large for auto-fill, use `flask backfill`"), proceed with normal `fetch()` only
5. Normal interval thresholds: OpenNEM 10min, BOM 6hr, Solcast 2hr

Done-when: disabling a source for 1 hour, then re-enabling, results in continuous data with no gap. Verified by querying `interval_start` values and confirming no missing intervals.

**FR6: fetch_range() method on BaseFetcher.**
Abstract method `fetch_range(start: datetime, end: datetime) -> raw_payload` added to BaseFetcher. Each fetcher implements it to query the source API for a specific date range. This is used by both the backfill CLI command (FR3) and gap-fill (FR5). Returns the same payload shape as `fetch()` so `transform()` and `store()` work unchanged.

Done-when: each fetcher has a `fetch_range()` that returns data for the requested range, or raises if the source doesn't support historical queries (Solcast).

### OpenNEM Real API Parsing

**FR7: Parse OpenNEM API response for current data.**
Replace the stub in `_fetch_live()` that generates synthetic data after a successful API probe. Parse the actual JSON response from `/stats/power/network/NEM/VIC1` into the existing payload shape (prices, demand, generation, interconnectors). Map OpenNEM's fuel-type labels to our canonical set using the existing `OPENNEM_FUEL_MAP`.

The OpenNEM API returns time-series data with `history` and `forecast` sections. Parse both. Consult OpenNEM API documentation for the exact response schema — the endpoint is public, no key required.

Done-when: with a live API connection, `fetch()` returns real VIC1 data (not synthetic). Verified by checking `source: "live"` in the payload and comparing values against the OpenNEM website.

**FR8: OpenNEM historical date-range fetching.**
Implement `fetch_range(start, end)` for OpenNEM. The API supports date-range queries — consult the API docs for the parameter format. Chunk internally if needed (the API may limit response size). Parse the response using the same parsing logic as FR7.

Done-when: `fetch_range(datetime(2025, 6, 1), datetime(2025, 6, 2))` returns one day of real VIC1 data.

### BOM Real API Parsing

**FR9: Parse BOM API responses for forecasts and observations.**
Replace the stub in `_fetch_live()`. BOM's API uses geohash-based endpoints:
- Forecasts: `/v1/locations/{geohash}/forecasts/daily` and `/v1/locations/{geohash}/forecasts/3-hourly`
- Observations: `/v1/locations/{geohash}/observations`

Each `WeatherLocation` has coordinates — derive the BOM geohash from lat/lon (or store it on the location model if BOM requires a specific geohash). Parse temperature, wind, rainfall, humidity, cloud cover from the response.

Done-when: with a live BOM API connection, `fetch()` returns real weather data for all seeded locations.

**FR10: BOM historical observation backfill.**
Implement `fetch_range(start, end)` for BOM. BOM's observation history may be available via their API or via the BOM Climate Data Online service. Observations only — not forecasts (see D5).

If the BOM API's historical depth is limited, backfill as far as available and log the actual coverage achieved: "BOM backfill: 3 months available (API limit), requested 12 months."

Done-when: `flask backfill --source bom` populates historical observations. Coverage depth logged.

### Solcast

**FR11: Solcast forward collection unchanged.**
No changes to Solcast fetcher behaviour. It continues to:
- Attempt live API call with API key (if configured)
- Fall back to synthetic if no key or API failure
- Collect forward from now

`fetch_range()` on SolcastFetcher raises `NotImplementedError("Solcast historical backfill not supported — use archive import")`.

Done-when: Solcast collection runs at its existing hourly cadence. `flask backfill --source solcast` exits with a clear message about archive import.

## Data Model Changes

### New migration: UNIQUE constraints

Add UNIQUE constraints to all 9 time-series tables. The migration must:
1. Delete duplicate rows (keeping the most recent `updated_at` per natural key group) before adding the constraint
2. Add the UNIQUE constraint

### WeatherLocation: optional geohash column

Add `bom_geohash: str | None` to `WeatherLocation` for BOM API endpoint routing. Populated at seed time from config. If BOM requires geohashes and we're deriving them from lat/lon, a utility function is fine instead of a column — builder's discretion.

## Success Criteria

- [ ] 12 months of real OpenNEM data (prices, demand, generation, interconnectors) in the database
- [ ] 12 months of real BOM observations in the database (or as deep as BOM API permits, with coverage logged)
- [ ] All time-series tables have UNIQUE constraints — no duplicate rows possible
- [ ] `flask backfill --source opennem --from 2025-06-04 --to 2026-06-04` completes successfully and is idempotent
- [ ] Disabling a source for 1 hour then re-enabling results in continuous data (gap-fill works)
- [ ] Synthetic fallback still works when APIs are unreachable
- [ ] Existing dashboard, API endpoints, and CLI commands work unchanged with real data
- [ ] No regressions in existing tests
