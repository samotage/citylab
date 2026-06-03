---
validation:
  status: valid
  validated_at: '2026-06-03T07:42:07+10:00'
---

# Data Ingestion Test Harness

## Problem

Three data ingestion pipelines (OpenNEM, BOM, Solcast) are being built in parallel. Each has fetchers, transforms, storage, and agent-queryable APIs. If we arrive at the hackathon with pipelines that fetch but silently drop fields, store stale data, return empty results from the API, or fail on rate limits — we're debugging plumbing instead of building the demo. We need a test harness that exercises every pipeline end-to-end and confirms the data is correct, complete, and agent-usable before we trust it.

This PRD depends on all three data ingestion PRDs being built first.

## Approach

### Test Levels

Three levels of verification, each catching a different class of failure:

**Level 1: Fetcher Contract Tests (unit)**
- Each fetcher class (OpenNEMFetcher, BOMFetcher, SolcastFetcher) tested against recorded API responses (fixtures)
- Validates: correct parsing, field mapping, null/missing field handling, error responses, rate limit handling
- Runs offline — no external API calls. Uses saved JSON response fixtures from real API calls captured during build
- Fixtures stored in `tests/fixtures/data/` (opennem/, bom/, solcast/ subdirectories)

**Level 2: Pipeline Integration Tests (integration)**
- Full fetch → transform → store cycle using the test database (`citylab_test`)
- Validates: data lands in correct tables, foreign keys resolve, timestamps parse correctly, no silent data loss (row counts match expected), indexes exist and are used
- Each data model gets a completeness check: are all required fields populated? Are there nulls where there shouldn't be?
- Tests the DataSource registry wiring: create a source → trigger a fetch → verify data arrived

**Level 3: Agent API Smoke Tests (end-to-end)**
- Exercises every agent-facing endpoint and CLI command with real data in the test database
- Validates: endpoints return non-empty results, JSON envelope is correct, time-range filters work, summary endpoints aggregate correctly
- Tests the agent reasoning path: can an agent call `energy summary` → `weather outlook --factor wind` → `solar summary` and get a coherent cross-source picture?
- Validates CLI commands produce parseable output (exit code 0, valid JSON or formatted text)

### Fixture Capture

During build of each data PRD, capture real API responses as test fixtures:
- `tests/fixtures/data/opennem/` — sample responses for prices, generation, interconnectors, forecasts, submissions
- `tests/fixtures/data/bom/` — sample forecast and observation responses
- `tests/fixtures/data/solcast/` — sample irradiance forecast responses
- Each fixture is a real response from the actual API, saved as JSON, with a companion `.meta.json` noting the capture date and endpoint

### Data Quality Assertions

Specific checks that catch the "half-baked" failure modes:

**Completeness:**
- Every EnergyPrice row has a non-null price_aud_mwh
- Every GenerationOutput row has a non-null output_mw and a valid fuel_type from the known enum
- Every InterconnectorFlow row maps to one of the 5 known corridors
- Every WeatherForecast row has at least temperature and wind speed populated
- Every SolarForecast row has GHI populated (DNI/DHI may be null depending on source tier)

**Freshness:**
- After a fetch cycle, the most recent data point is within the expected interval window (e.g., within 10 minutes for 5-min dispatch data)
- DataSource.last_fetch_at updated after each successful run
- No data gaps longer than 2x the expected interval

**Consistency:**
- Generation output by fuel type sums to approximately total generation (within 5% tolerance — rooftop solar estimation varies)
- Interconnector flows are present for all 5 corridors
- Price forecasts have forecast_for timestamps in the future relative to forecast_issued_at

**Agent Usability:**
- Summary endpoints return data within 2 seconds (agent timeout tolerance)
- Time-range queries with from/to parameters return only data within that range
- Empty time ranges return empty arrays, not errors
- All summary and data endpoints include `data_as_of` ISO timestamp in the response envelope (freshness contract from PRD 1 Part A)
- `GET /api/v1/data/market-intelligence` returns a cross-source summary combining energy, weather, and solar data with per-source `data_as_of` timestamps

### Test Runner

- All Level 1 and 2 tests run via `pytest tests/data/` — fast, offline, part of the standard test suite
- Level 3 smoke tests run via `pytest tests/data/test_agent_api_smoke.py -m integration` — requires seeded test database
- A single CLI command exercises all levels: `cli-citylab data verify` — runs the pipeline checks against the live database and reports pass/fail per source, per check category
- `cli-citylab data verify` is the pre-hackathon gate: green = ready, red = fix before proceeding

### Test File Structure

```
tests/data/
├── conftest.py                    — shared fixtures, test DB seeding helpers
├── test_opennem_fetcher.py        — Level 1: OpenNEM fetcher contract
├── test_bom_fetcher.py            — Level 1: BOM fetcher contract  
├── test_solcast_fetcher.py        — Level 1: Solcast fetcher contract
├── test_pipeline_integration.py   — Level 2: end-to-end pipeline per source
├── test_data_quality.py           — Level 2: completeness, freshness, consistency
├── test_agent_api_smoke.py        — Level 3: agent API and CLI verification
└── fixtures/
    ├── opennem/                   — captured API response fixtures
    ├── bom/
    └── solcast/
```

## Done When

- [ ] Level 1 fetcher contract tests pass for all three sources using captured fixtures
- [ ] Level 2 pipeline integration tests confirm data lands correctly in `citylab_test` for all three sources
- [ ] Level 2 data quality assertions catch: missing fields, stale data, gaps, inconsistent aggregates
- [ ] Level 3 agent API smoke tests confirm all energy, weather, and solar endpoints return valid data
- [ ] Level 3 CLI smoke tests confirm `cli-citylab energy summary`, `cli-citylab weather summary`, `cli-citylab solar summary`, and `cli-citylab data market-intelligence` all return parseable output with `data_as_of` timestamps
- [ ] `cli-citylab data verify` runs all checks against the live database and reports per-source pass/fail
- [ ] API response fixtures captured from real API calls during build of each data PRD
- [ ] All tests run in under 60 seconds (Level 1 + 2); Level 3 under 30 seconds with seeded data
- [ ] A failing fetcher, a dropped field, or a stale pipeline produces a clear test failure — not a silent pass

## Demo Script

1. `pytest tests/data/ -v` — see all fetcher contract and pipeline integration tests pass
2. `cli-citylab data verify` — see per-source verification: OpenNEM ✓, BOM ✓, Solcast ✓ with check counts
3. Intentionally break something (e.g., invalidate an API fixture) → re-run → see specific failure identifying the broken source and check
4. The key proof: if `cli-citylab data verify` is green, the data pipelines are trustworthy and we can focus on the hackathon problem, not debugging plumbing
