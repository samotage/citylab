# Tasks: Solcast Solar Irradiance Forecast Ingestion

Source PRD: docs/prds/data/solcast-solar-forecast-ingestion.md
Branch: feature/hack-solcast-solar-forecast-ingestion

This feature reuses the shared ingestion architecture already on master. It is
closely modelled on the BOM weather feature: SolarLocation + SolarForecast
models, a SolcastFetcher (live-probe with synthetic fallback), a solar_query
read service, a solar API blueprint, a solar CLI group, location seeding, a
config.yaml data_sources entry, an Alembic migration, and the wiring across the
ingestion package, scheduler, models, API, and CLI.

Pre-done on master: `solcast` is already present in `DataSource.SOURCE_TYPES`
(src/citylab/models/data_source.py:12) and in `_SOURCE_TYPE_BY_KEY`
(src/citylab/services/ingestion/seed.py:16).

Known issue (carried from prior PRDs): `cli-citylab` is not on PATH unless the
package is pip-installed. Run the CLI via
`PYTHONPATH=src python -m citylab.cli_wrapper ...` for the demo, or
`pip install -e .`.

## Task List

- [x] 1. Add models `SolarLocation` and `SolarForecast` in
  `src/citylab/models/solar.py`. Follow `src/citylab/models/weather.py`.
  - `SolarLocation`: name (unique), latitude, longitude, state,
    region_relevance (e.g. "utility_solar", "rooftop_aggregate", "hybrid_zone"),
    reference_pv_capacity_kw, plus `to_dict()` / `__repr__`.
  - `SolarForecast`: location_id FK, issued_at, forecast_for, forecast_period
    ("30min"/"hourly"), ghi_wm2, dni_wm2, dhi_wm2, cloud_opacity_pct,
    air_temp_c, estimated_pv_output_kw, plus an
    `ix_solar_forecasts_location_for` index on (location_id, forecast_for) and
    `to_dict()` / `__repr__`.

- [x] 2. Register the new models in `src/citylab/models/__init__.py`
  (import `SolarLocation`, `SolarForecast` alongside the weather models).

- [x] 3. Generate the Alembic migration for the two solar tables. Run
  `flask db migrate -m "solcast solar forecast ingestion tables"`, then review
  the generated file in `migrations/versions/` against the weather migration
  (35961a27f104) to confirm columns + index are correct. Down-revision must be
  the current head. Do NOT auto-apply to a non-test DB without confirming the
  target.

- [x] 4. Implement `SolcastFetcher` in
  `src/citylab/services/ingestion/solcast.py`. Follow `bom.py`:
  - `source_type = "solcast"`, `register_fetcher("solcast", SolcastFetcher)` at
    module end.
  - `fetch()` tries a live reachability probe against the Solcast base_url
    (raise on failure), else falls back to `_synthetic()`. Stamp source
    "live"/"synthetic". Respect a daily rate-limit guard from config (free-tier
    awareness — back off if a configured call budget is exhausted).
  - Synthetic irradiance must be diurnal: GHI peaks at solar noon, zero at
    night; DNI/DHI derived from GHI; cloud_opacity_pct modulates GHI down;
    estimated_pv_output_kw scaled from GHI and reference_pv_capacity_kw. Bias by
    region_relevance so NW Vic / Riverland read sunnier.
  - Horizons (PRD): 30-min intervals out to 24h (intraday) + hourly out to 7
    days (short-range). On first run (backfill, last_fetch_at is None) stamp the
    last 3 days of issued forecasts for history.
  - `transform(raw)` builds `SolarForecast(**row)` instances; `store()` adds +
    flushes and returns the count.

- [x] 5. Register the fetcher on package import in
  `src/citylab/services/ingestion/__init__.py`
  (add `from citylab.services.ingestion import solcast  # noqa: F401,E402`).

- [x] 6. Add `seed_solar_locations()` in
  `src/citylab/services/ingestion/seed.py`, modelled on
  `seed_weather_locations()`. Seed the 6 PRD locations, each with lat/long,
  state, region_relevance, and a reference_pv_capacity_kw, idempotent (matched
  by name):
  - NW Vic (Mildura/Swan Hill) — utility_solar
  - Western Vic (Ballarat/Bendigo) — hybrid_zone
  - Melbourne metro — rooftop_aggregate
  - Gippsland — utility_solar
  - Northern SA (Port Augusta) — hybrid_zone
  - Riverland (Renmark/Berri) — utility_solar

- [x] 7. Add the `solcast` entry to the `data_sources` section of
  `config.yaml` (name "Solcast Solar Forecasts", base_url
  https://api.solcast.com.au, `api_key: ${SOLCAST_API_KEY}`,
  `cron_expression: "0 * * * *"` for hourly, a `timeout_seconds`, and a
  `daily_call_budget` for rate-limit awareness).
  NOTE: config.yaml is a protected file — show the diff and get approval before
  editing.

- [x] 8. Wire seeding + scheduling. In `src/citylab/services/scheduler.py` add
  `seed_solar_locations` to the imports and call it next to
  `seed_weather_locations()` on startup. In `src/citylab/cli/commands.py` add
  `seed_solar_locations` to the seed CLI command's imports and invocation so the
  flask seed command also seeds solar locations.

- [x] 9. Implement the read service `src/citylab/services/solar_query.py`,
  modelled on `weather_query.py`. Reuse
  `energy_query.latest_fetch_timestamp` and `_parse_dt` for the freshness
  contract. Provide:
  - `query_forecasts(location, dt_from, dt_to, limit)` — latest-issue forecasts
    for resolved location(s).
  - `summary()` — current GHI + next-24h solar outlook grouped by
    region_relevance, with an estimated generation-impact headline per group.
  - `outlook(days)` — multi-day, narrative-friendly view: per-location peak GHI /
    avg cloud_opacity over the horizon so an agent can say "strong solar across
    NW Vic next 3 days, cloud band day 4".
  - A `_resolve_locations` selector accepting name substring / id /
    region_relevance / state (VIC, SA, etc.), like weather_query.

- [x] 10. Add the API blueprint `src/citylab/routes/api_v1/solar.py`
  (`solar_api_bp`), modelled on `weather.py`. Token-protected endpoints, all
  returning the `{ok, data, data_as_of}` envelope:
  - `GET /solar/forecasts?location=&from=&to=`
  - `GET /solar/summary`
  - `GET /solar/outlook?days=`
  Register it in `src/citylab/routes/api_v1/__init__.py`.

- [x] 11. Add the CLI group `src/citylab/cli_wrapper/commands_solar.py`
  (`solar_group`), modelled on `commands_weather.py`, with subcommands
  `summary`, `outlook` (--days), and `forecasts` (--location/--from/--to).
  Register it in `src/citylab/cli_wrapper/__init__.py`
  (`main.add_command(solar_group, "solar")`).

- [x] 12. Add tests in `tests/test_solcast_ingestion.py`, modelled on
  `tests/test_weather_ingestion.py`. Use the existing fixture system
  (app/client/db_session) — NO ad-hoc DB connections. Cover: fetcher synthetic
  run produces SolarForecast rows for seeded locations with non-negative GHI
  that is zero at night and positive at solar noon; location seeding
  idempotency; solar_query summary/outlook return data; API endpoints return the
  envelope with data_as_of; CLI group is registered.

- [x] 13. Run targeted tests and apply the migration against the test DB.
  `pytest tests/test_solcast_ingestion.py`. Confirm the DataSource list now
  includes Solcast. Fix failures.

- [x] 14. Smoke the demo script end to end (see below) on the dev/test surface
  as governed by guardrails, then commit.

## Demo Script

1. `cli-citylab data sources` — see Solcast listed alongside OpenNEM and BOM as active data sources
2. `cli-citylab solar summary` — see current irradiance and next-24h forecast across Victorian and SA solar regions
3. `cli-citylab solar outlook` — see multi-day view: "strong solar forecast across NW Vic for next 3 days, cloud band approaching from west on day 4"
4. `cli-citylab solar forecasts --location mildura` — see detailed hourly GHI/DNI/DHI forecast for the Mildura solar corridor
5. The key proof: an agent reads solar outlook → correlates with energy generation data → reasons about renewable supply impact on price
