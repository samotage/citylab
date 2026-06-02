# Tasks: Energy Market Data Ingestion — Victorian NEM

Source PRD: docs/prds/data/energy-market-data-ingestion.md
Branch: feature/hack-energy-market-data-ingestion

## Task List

### Foundation: Models & Migrations

- [x] 1. Create `DataSource` model in `src/citylab/models/data_source.py` (inherits BaseModel): name (unique), source_type (enum: opennem/bom/solcast/custom), base_url, config (JSONB), cron_expression, is_active, last_fetch_at, last_fetch_status (success/error/pending), last_error, next_fetch_at. Add `to_dict()`. Register in `src/citylab/models/__init__.py`.
- [x] 2. Create the six energy data models in `src/citylab/models/energy.py` (each inherits BaseModel, each with `to_dict()`):
      - `EnergyPrice` (region, interval_start, interval_end, interval_type, price_aud_mwh)
      - `EnergyDemand` (region, interval_start, demand_mw, demand_type)
      - `GenerationOutput` (region, interval_start, fuel_type, output_mw, capacity_mw)
      - `InterconnectorFlow` (interconnector_id, from_region, to_region, interval_start, flow_mw, capacity_mw, limit_mw)
      - `GeneratorSubmission` (station_name, unit_id, fuel_type, region, interval_start, bid_band, price_aud_mwh, volume_mw)
      - `PriceForecast` (region, forecast_issued_at, forecast_for, price_aud_mwh, forecast_type)
      Register all six in `src/citylab/models/__init__.py`.
- [x] 3. Add indexes per PRD retention section: (region, interval_start) on all time-series tables; composite (region, interval_start, fuel_type) on GenerationOutput. Define via `__table_args__` on each model.
- [x] 4. Generate and apply Alembic migration for all seven new tables (`flask db migrate` + `flask db upgrade`). Confirm target DB is the `citylab` dev DB before running (additive upgrade is permitted).

### Ingestion Architecture (source-agnostic, reusable)

- [x] 5. Create `src/citylab/services/ingestion/__init__.py` and `base.py` with `BaseFetcher` abstract class defining the `fetch()` / `transform()` / `store()` contract plus a `run()` orchestrator that calls all three, updates DataSource status (last_fetch_at, last_fetch_status, last_error, next_fetch_at), and handles retry with exponential backoff (3 attempts).
- [x] 6. Create a fetcher registry in `src/citylab/services/ingestion/registry.py` — dict mapping source_type string → fetcher class, with `register_fetcher()` and `get_fetcher(source_type)` helpers. This is the extension point: new source = new class + one registry entry.
- [x] 7. Wire the ingestion scheduler: extend `src/citylab/services/scheduler.py` (or add `ingestion_scheduler.py`) so each active DataSource row gets an APScheduler cron job that resolves its fetcher via the registry and calls `run()`. Mirror the existing `sync_jobs()` pattern; update next_fetch_at on the DataSource.

### OpenNEM Fetcher (first concrete source)

- [x] 8. Implement `OpenNEMFetcher` in `src/citylab/services/ingestion/opennem.py` (subclass BaseFetcher, registered under `opennem`): API calls to OpenNEM for VIC1 (prices, demand, generation, interconnectors), rate limiting, pagination, 7-day backfill on first run / incremental from last_fetch_at thereafter. Map fuel types incl. battery_charging/battery_discharging; map the 5 interconnector corridors (Basslink/T-V, Heywood/V-SA, Murraylink/V-S, VNI, VNI West). Fetch generator submissions and pre-dispatch forecasts from AEMO endpoints within the same fetcher where OpenNEM lacks them.
- [ ] 9. Add a `data_sources` section to `config.yaml` (env-var refs for API keys/credentials) and a seed routine/CLI that creates the OpenNEM DataSource row from config, injecting credentials into DataSource.config. Show config.yaml diff before applying.

### Data API (source-agnostic)

- [ ] 10. Create `src/citylab/routes/api_v1/data.py` blueprint: `GET /data/sources` (list + status), `GET /data/sources/{id}/status`, `GET /data/market-intelligence` (cross-source summary; energy-only until BOM/Solcast exist; per-source `data_as_of`). Register blueprint in `src/citylab/routes/api_v1/__init__.py`. Use `require_api_token` and the `{"ok": ..., "data": ...}` envelope.

### Energy API

- [ ] 11. Create `src/citylab/routes/api_v1/energy.py` blueprint: `GET /energy/prices`, `/energy/generation`, `/energy/interconnectors`, `/energy/forecasts`, `/energy/summary` (current snapshot: latest price, demand, generation mix, interconnector flows, battery state, nearest forecast). Support `region`/`from`/`to` query params. Every response includes a `data_as_of` timestamp. Register in api_v1 `__init__.py`.

### CLI

- [ ] 12. Create `src/citylab/cli_wrapper/commands_data.py` (`data` group: `sources`, `market-intelligence`) and `commands_energy.py` (`energy` group: `summary`, `prices` with `--from`/`--to`, `generation`, `interconnectors`, `forecasts`). Register both groups in `src/citylab/cli_wrapper/__init__.py`. Mirror the existing APIClient / JSON-print pattern.

### Tests

- [ ] 13. Add targeted tests: model creation/to_dict, fetcher registry register/lookup, BaseFetcher status-update + retry logic (mock the HTTP layer — no live OpenNEM calls), and energy/data API endpoints returning the envelope with `data_as_of`. Use existing fixtures (`app`, `client`, `db_session`). No live network in tests.

## Demo Script

1. Start the app: `python run.py`
2. In terminal: `cli-citylab data sources` — see OpenNEM registered as active data source
3. Wait for first fetch cycle (or trigger manually via API)
4. `cli-citylab energy summary` — see current Victorian spot price, demand, generation mix breakdown, interconnector flows (Basslink, Heywood, Murraylink, VNI, VNI West), battery state, and nearest forward price forecast
5. `cli-citylab energy prices --from 2025-06-01` — see historical spot prices
6. `cli-citylab energy generation` — see generation mix: brown coal, gas, solar, wind, hydro, battery
7. The key proof: an agent can call `cli-citylab energy summary` and get everything it needs to reason about the current Victorian energy market in one call
