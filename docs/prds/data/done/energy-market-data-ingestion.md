---
validation:
  status: valid
  validated_at: '2026-06-03T07:42:04+10:00'
---

# Energy Market Data Ingestion — Victorian NEM

## Problem

CityLab needs a comprehensive picture of everything that influences the Victorian electricity spot price so that AI agents can reason across multiple factors and make energy market decisions. Today the app has no data — just a scheduling skeleton. Without market data, generation mix, interconnector flows, battery storage state, generator bids, and forward price forecasts, agents have nothing to reason on.

The data sources that feed this picture extend beyond Victoria itself: Tasmanian hydro (rain-driven, via Basslink), South Australian wind surplus (via Heywood/Murraylink), and NSW generation (via VNI/VNI West) all directly influence Victorian prices. This PRD delivers both the shared ingestion architecture (reusable for BOM weather, Solcast solar, gas market, and future sources) and the first concrete implementation: OpenNEM + AEMO data for the Victorian energy market.

## Approach

### Part A: Shared Ingestion Architecture

Establish a source-agnostic data ingestion framework that all future data PRDs reuse. Adding a new data source should be a configuration exercise, not a plumbing exercise.

**Data Source Registry model:**
- `DataSource` — name, source_type (enum: opennem, bom, solcast, custom), base_url, config (JSONB — source-specific parameters including API keys/credentials), cron_expression, is_active, last_fetch_at, last_fetch_status (success/error/pending), last_error, next_fetch_at. Inherits BaseModel.
- API credentials (Solcast API key, BOM auth tokens, etc.) stored in DataSource.config JSONB. Sensitive values referenced via env vars in config.yaml under a `data_sources` section, injected into DataSource.config at seed time.
- Each source type has a corresponding fetcher class registered in a simple fetcher registry (dict mapping source_type → fetcher class). New sources = new fetcher class + registry entry.

**Ingestion service pattern:**
- `src/citylab/services/ingestion/` — base fetcher class with `fetch()`, `transform()`, `store()` contract. Each source type implements these three methods.
- Fetcher returns normalised data; the service handles scheduling, error tracking, and status updates on the DataSource row.
- Scheduling via the existing APScheduler infrastructure — each active DataSource gets a cron job that triggers its fetcher.

**Agent-queryable API:**
- `GET /api/v1/data/sources` — list registered data sources and their status
- `GET /api/v1/data/sources/{id}/status` — fetch status, last run, error details
- `GET /api/v1/data/market-intelligence` — cross-source summary combining energy, weather, and solar data into a single response. Returns the latest data from all active sources with a `data_as_of` timestamp per source so the agent knows data freshness. This is the "give me everything" endpoint an agent calls first.
- CLI: `cli-citylab data sources` — list data sources and status
- CLI: `cli-citylab data market-intelligence` — cross-source summary in one call

**Freshness contract:** All summary and data endpoints include a `data_as_of` ISO timestamp in the response envelope indicating when the underlying data was last fetched. Agents can compare this to current time to detect stale data without a separate call to `/data/sources`.

### Part B: OpenNEM Victorian Energy Market Data

Primary data source: [OpenNEM API](https://api.opennem.org.au). Where OpenNEM doesn't expose specific datasets (e.g., pre-dispatch forecasts, detailed generator submissions), the OpenNEMFetcher fetches directly from AEMO endpoints as a secondary source within the same fetcher — AEMO is not a separate DataSource, it's an implementation detail of the OpenNEM fetcher.

**Data categories and models:**

1. **Market Price** — `EnergyPrice`
   - region (VIC1), interval_start, interval_end, interval_type (5min/30min), price_aud_mwh
   - Spot prices only — forward price forecasts are stored in the separate PriceForecast model
   - Source: OpenNEM pricing endpoint for VIC1

2. **Demand** — `EnergyDemand`
   - region (VIC1), interval_start, demand_mw, demand_type (actual/forecast)
   - Source: OpenNEM demand endpoint

3. **Generation Mix** — `GenerationOutput`
   - region, interval_start, fuel_type (brown_coal, gas_ccgt, gas_ocgt, gas_recip, gas_steam, solar_utility, solar_rooftop, wind, hydro, battery_discharging, battery_charging, biomass, distillate), output_mw, capacity_mw (where available)
   - Source: OpenNEM power/energy endpoint for VIC1
   - Battery storage tracked explicitly: battery_charging and battery_discharging as distinct fuel types, plus aggregated battery state where available

4. **Interconnector Flow** — `InterconnectorFlow`
   - interconnector_id (e.g., V-SA, V-S, T-V-MNSP1), from_region, to_region, interval_start, flow_mw (positive = from→to direction), capacity_mw, limit_mw
   - Corridors: Basslink (Tas↔Vic), Heywood (SA↔Vic), Murraylink (SA↔Vic), VNI (NSW↔Vic), VNI West (NSW↔Vic)
   - Source: OpenNEM interconnector/flow endpoints

5. **Generator Submissions** — `GeneratorSubmission`
   - station_name, unit_id, fuel_type, region, interval_start, bid_band, price_aud_mwh, volume_mw
   - Source: OpenNEM or AEMO bid/offer data
   - These show what generators are offering at what price — reveals the supply curve

6. **Price Forecast** — `PriceForecast`
   - region, forecast_issued_at, forecast_for (target interval), price_aud_mwh, forecast_type (predispatch_30min, predispatch_5min, stpasa)
   - Source: AEMO pre-dispatch data (via OpenNEM if available, direct AEMO if not)
   - Horizon: up to 40 hours ahead for pre-dispatch, up to 6 days for ST PASA

**Fetcher implementation:**
- `OpenNEMFetcher` class — handles API calls to OpenNEM, rate limiting, pagination
- Region parameter: `NEM/VIC1` (confirm exact identifier during build)
- Interval: default 5-minute for dispatch data, 30-minute for trading data
- Initial backfill: fetch last 7 days on first run, then incremental from last_fetch_at
- Error handling: retry with exponential backoff (3 attempts), log failures to DataSource.last_error

**Agent-queryable API (energy-specific):**
- `GET /api/v1/energy/prices?region=VIC1&from=...&to=...` — spot prices with optional time range
- `GET /api/v1/energy/generation?region=VIC1&from=...&to=...` — generation mix
- `GET /api/v1/energy/interconnectors?from=...&to=...` — interconnector flows
- `GET /api/v1/energy/forecasts?region=VIC1` — forward price forecasts
- `GET /api/v1/energy/summary?region=VIC1` — current snapshot: latest price, demand, generation mix, interconnector flows, battery state, nearest forecast — the "what's happening right now" endpoint an agent hits first
- CLI: `cli-citylab energy summary`, `cli-citylab energy prices`, `cli-citylab energy generation`

**Scheduling:**
- Market data (prices, demand, generation, interconnectors): every 5 minutes, aligned to NEM dispatch intervals
- Generator submissions: every 30 minutes
- Price forecasts: every 30 minutes (matches AEMO pre-dispatch publication cycle)
- Backfill on first deploy: last 7 days

### Data Retention

- Keep all data — no rolling window. Historical data has analytical value for agent reasoning about patterns.
- Index on (region, interval_start) for all time-series tables. Composite index on (region, interval_start, fuel_type) for generation.
- Partition strategy deferred until volume warrants it (hackathon scope — premature to partition now).

## Done When

- [ ] DataSource model exists with CRUD API and CLI (`cli-citylab data sources`)
- [ ] Fetcher registry pattern works — registering a new source type is one class + one registry entry
- [ ] OpenNEMFetcher pulls Victorian market data from OpenNEM API
- [ ] All six data models (EnergyPrice, EnergyDemand, GenerationOutput, InterconnectorFlow, GeneratorSubmission, PriceForecast) have migrations applied and data landing
- [ ] 5 interconnector corridors tracked: Basslink, Heywood, Murraylink, VNI, VNI West
- [ ] Battery storage appears as explicit fuel types (charging/discharging) in generation data
- [ ] Energy API endpoints return real data: prices, generation, interconnectors, forecasts, summary
- [ ] `cli-citylab energy summary` returns a current snapshot an agent can reason on
- [ ] Scheduled fetches run on configured cron intervals via APScheduler
- [ ] Backfill of last 7 days completes on first run
- [ ] `cli-citylab data market-intelligence` returns a cross-source summary combining energy, weather, and solar data (populated once BOM and Solcast PRDs are built; returns energy-only until then)
- [ ] All summary and data API responses include `data_as_of` timestamp so agents can detect stale data
- [ ] A second data source could be added by writing a fetcher class and creating a DataSource row — no plumbing changes required

## Demo Script

1. Start the app: `python run.py`
2. In terminal: `cli-citylab data sources` — see OpenNEM registered as active data source
3. Wait for first fetch cycle (or trigger manually via API)
4. `cli-citylab energy summary` — see current Victorian spot price, demand, generation mix breakdown, interconnector flows (Basslink, Heywood, Murraylink, VNI, VNI West), battery state, and nearest forward price forecast
5. `cli-citylab energy prices --from 2025-06-01` — see historical spot prices
6. `cli-citylab energy generation` — see generation mix: brown coal, gas, solar, wind, hydro, battery
7. The key proof: an agent can call `cli-citylab energy summary` and get everything it needs to reason about the current Victorian energy market in one call
