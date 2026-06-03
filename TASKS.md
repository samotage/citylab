# Tasks: Data Ingestion Test Harness

Source PRD: docs/prds/data/data-ingestion-test-harness.md
Branch: feature/hack-data-ingestion-test-harness

A three-level verification harness over the OpenNEM, BOM, and Solcast ingestion
pipelines now on master. Level 1 = offline fetcher contract tests against
recorded fixtures; Level 2 = pipeline integration + data-quality assertions
against `citylab_test`; Level 3 = agent API + CLI smoke tests. Capped by a
`cli-citylab data verify` pre-hackathon gate.

Foundation-first: scaffolding and fixtures before tests, each level in order,
the `verify` CLI command last.

Note on fetchers: all three fetchers currently derive their data synthetically
(the live paths only probe reachability, then fall back). The Level 1 fixtures
therefore mirror the snapshot-dict shapes each fetcher's `transform()` consumes,
captured as JSON so the contract is pinned and a regression in field mapping
fails loudly.

Known issue (carried from prior PRDs): `cli-citylab` is not on PATH unless the
package is pip-installed. Run the CLI via
`PYTHONPATH=src python -m citylab.cli_wrapper ...` for the demo, or
`pip install -e .`.

## Task List

### Scaffolding & Fixtures (foundation)

- [x] 1. Create the `tests/data/` package: `tests/data/__init__.py` and the
  `tests/data/fixtures/{opennem,bom,solcast}/` directories (with `.gitkeep` so
  empty dirs are tracked). The PRD references both `tests/fixtures/data/` and
  `tests/data/fixtures/` — standardise on `tests/data/fixtures/` per the Test
  File Structure section and use it consistently.

- [x] 2. Capture API response fixtures. Generate representative JSON fixtures that
  mirror the snapshot-dict shapes each fetcher's `transform()` consumes — one
  good-case fixture per source plus the null/missing-field and error/unexpected
  -payload edge cases Level 1 needs. Save each as `<name>.json` with a companion
  `<name>.meta.json` recording capture date and the endpoint/shape it represents.
  Coverage: opennem (prices, generation, interconnectors, submissions,
  forecasts), bom (forecasts, observations), solcast (irradiance forecasts).

- [x] 3. Write `tests/data/conftest.py`: shared fixtures — a fixture-loading
  helper (`load_fixture(source, name)`), test-DB seeding helpers that create
  DataSource rows plus the WeatherLocation / SolarLocation rows the BOM/Solcast
  fetchers query, and a helper to run a fetcher end-to-end against the seeded DB.
  Reuse the existing `app` / `db_session` fixtures from `tests/conftest.py`; do
  NOT create ad-hoc DB connections.

### Level 1: Fetcher Contract Tests (unit, offline)

- [x] 4. Write `tests/data/test_opennem_fetcher.py`: assert `transform()` maps the
  captured OpenNEM fixture into the correct ORM instances with correct field
  mapping; assert null/missing-field handling; assert every generated fuel_type
  is in the known enum (OPENNEM_FUEL_MAP values); assert the live path raises on
  an unexpected payload and falls back to synthetic without crashing. No network.

- [x] 5. Write `tests/data/test_bom_fetcher.py`: assert `transform()` maps the
  captured BOM forecast + observation fixtures correctly; short-range
  (`3hourly`) vs daily (`daily`) forecast_period handling; temperature + wind
  populated; missing-field tolerance. No network.

- [x] 6. Write `tests/data/test_solcast_fetcher.py`: assert `transform()` maps the
  captured Solcast irradiance fixture correctly; GHI populated and zero at night
  / positive at solar noon; DNI/DHI derivation; the rate-limit/budget back-off
  path (`daily_call_budget` reached → synthetic, no live call); intraday
  (`30min`) vs short-range (`hourly`) forecast_period. No network.

### Level 2: Pipeline Integration

- [x] 7. Write `tests/data/test_pipeline_integration.py`: for each source, seed a
  DataSource (+ locations), run the fetcher end-to-end against `citylab_test`,
  and assert data lands in the correct tables, FKs resolve (forecasts →
  locations), timestamps parse, row counts match expected (no silent loss), and
  `DataSource.last_fetch_at` / `last_fetch_status` update. Exercise the registry
  wiring: lookup fetcher by source_type → run → verify rows arrived. Mark
  `@pytest.mark.integration`.

### Level 2: Data Quality Assertions

- [x] 8. Write `tests/data/test_data_quality.py` — completeness: every EnergyPrice
  has non-null price_aud_mwh; every GenerationOutput has non-null output_mw and a
  valid fuel_type from the known enum; every InterconnectorFlow maps to one of
  the 5 corridors; every WeatherForecast has temperature + wind; every
  SolarForecast has GHI populated.

- [x] 9. Extend `test_data_quality.py` — freshness: after a fetch the most recent
  data point is within the expected interval window; no data gaps longer than 2x
  the expected interval; `last_fetch_at` updated.

- [x] 10. Extend `test_data_quality.py` — consistency: generation by fuel type
  sums to ~total generation (5% tolerance, accounting for battery_charging being
  negative); interconnector flows present for all 5 corridors; price forecasts
  have forecast_for in the future relative to forecast_issued_at.

### Level 3: Agent API & CLI Smoke

- [x] 11. Write `tests/data/test_agent_api_smoke.py` — API: with seeded data,
  exercise every energy / weather / solar endpoint plus
  `/api/v1/data/market-intelligence`; assert non-empty results, correct
  `{ok, data, data_as_of}` envelope, `data_as_of` ISO timestamp present, from/to
  range filters return only in-range data, empty ranges return empty arrays (not
  errors), summary endpoints respond within the 2s agent tolerance. Mark
  `@pytest.mark.integration`.

- [x] 12. Extend `test_agent_api_smoke.py` — cross-source agent reasoning path:
  `energy summary` → `weather outlook --factor wind` → `solar summary` returns a
  coherent combined picture; `market-intelligence` returns per-source
  `data_as_of`. Verify the four CLI commands (`energy summary`, `weather
  summary`, `solar summary`, `data market-intelligence`) produce parseable output
  via Click's `CliRunner` (exit code 0, valid JSON) so no live server is needed
  in the test path.

### Pre-Hackathon Gate CLI

- [ ] 13. Factor the check logic into a reusable service
  `src/citylab/services/data_verify.py` that runs the completeness / freshness /
  consistency checks against the live database and returns a structured
  per-source, per-category pass/fail result. Then add `cli-citylab data verify`
  in `src/citylab/cli_wrapper/commands_data.py` that calls it, prints per-source
  (OpenNEM / BOM / Solcast) and per-category results with counts (green/red), and
  exits non-zero on any failure. Both the CLI and the Level 2 tests should be
  able to call the service.

- [ ] 14. Write `tests/data/test_data_verify.py`: unit-test the `data_verify`
  service against seeded data (all-green) and against a broken state (e.g. a
  nulled field or a stale source) to confirm it reports the specific failing
  source + category rather than silently passing.

### Wrap-up

- [ ] 15. Run `pytest tests/data/ -v` and confirm Level 1+2 run under 60s and
  Level 3 under 30s with seeded data. Run `cli-citylab data verify` against the
  seeded DB and confirm per-source green. Fix any failures.

## Demo Script

1. `pytest tests/data/ -v` — see all fetcher contract and pipeline integration tests pass
2. `cli-citylab data verify` — see per-source verification: OpenNEM ✓, BOM ✓, Solcast ✓ with check counts
3. Intentionally break something (e.g., invalidate an API fixture) → re-run → see specific failure identifying the broken source and check
4. The key proof: if `cli-citylab data verify` is green, the data pipelines are trustworthy and we can focus on the hackathon problem, not debugging plumbing
