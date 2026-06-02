# Tasks: BOM Weather Forecast Ingestion

Source PRD: docs/prds/data/bom-weather-forecast-ingestion.md
Branch: feature/hack-bom-weather-forecast-ingestion

Reuses the shared ingestion architecture already on master (BaseFetcher contract,
fetcher registry, DataSource model + seed, APScheduler `sync_data_sources`, the
`data_as_of` freshness envelope from energy_query). BOM scheduling is free once a
DataSource row exists — the scheduler reads DataSource rows generically. The
`bom` source_type is already in DataSource.SOURCE_TYPES and seed `_SOURCE_TYPE_BY_KEY`.

Note (carried from PRD 1 known issue): `cli-citylab` is not on PATH unless the
package is pip-installed. Run the CLI via `PYTHONPATH=src python -m citylab.cli_wrapper ...`
for the demo, or `pip install -e .`.

## Task List

- [x] 1. Add weather models — create `src/citylab/models/weather.py` with three
       BaseModel subclasses, each with `to_dict()`, mirroring the energy models:
       - `WeatherLocation` (name unique, bom_station_id, bom_forecast_area_id,
         latitude, longitude, state, region_relevance)
       - `WeatherForecast` (location_id FK, issued_at, forecast_for, forecast_period,
         temperature_min_c, temperature_max_c, temperature_c, wind_speed_kmh,
         wind_direction, wind_gust_kmh, rainfall_mm, rainfall_probability_pct,
         cloud_cover_pct, humidity_pct, weather_description)
       - `WeatherObservation` (location_id FK, observed_at, temperature_c,
         wind_speed_kmh, wind_direction, wind_gust_kmh, rainfall_since_9am_mm,
         humidity_pct, pressure_hpa)
       Add indexes (location_id, forecast_for) on forecasts and (location_id,
       observed_at) on observations via `__table_args__`. Register all three in
       `src/citylab/models/__init__.py`.

- [ ] 2. Generate and apply the Alembic migration for the three weather tables
       (`flask db migrate` + `flask db upgrade`). Confirm the target DB is the
       `citylab` dev DB before running (additive upgrade is permitted). Verify the
       tables exist.

- [ ] 3. Seed the 10 forecast locations — add a `seed_weather_locations()` helper
       (in `src/citylab/services/ingestion/seed.py` or `models/weather.py`), idempotent
       (match by name), covering the PRD locations with correct region_relevance:
       - Vic: Melbourne metro (demand_centre), Western Vic/Ballarat-Ararat (wind_corridor),
         Gippsland (demand_centre + offshore wind)
       - Tas: Western Tas/Strahan-Queenstown (hydro_catchment), Central Highlands (hydro_catchment)
       - SA: Mid-North/Port Augusta-Clare (wind_corridor), Yorke/Adelaide Hills (wind_corridor)
       - Snowy/NSW: Snowy Mountains (hydro_catchment), Southern NSW (demand_centre / interconnector context)
       Wire it to run alongside `seed_data_sources` on app startup.

- [ ] 4. Implement `BOMFetcher` — create `src/citylab/services/ingestion/bom.py`
       (source_type `bom`) following the OpenNEMFetcher pattern: `fetch()` attempts live
       BOM access (api.weather.bom.gov.au forecast + observation endpoints, base_url from
       DataSource), falling back to a synthetic-but-realistic per-location snapshot on any
       failure so the demo never breaks, clearly flagged in logs. Synthetic data must be
       region-plausible (Tas/Snowy wetter for hydro, SA/Western-Vic windier, Melbourne
       demand-driven temps). `transform()` builds WeatherForecast (short-range 3-day
       hourly/3-hourly + medium-range 7-day daily) and WeatherObservation instances for
       each seeded location. `store()` adds + flushes. Backfill last 3 days of forecasts
       on first run; incremental thereafter. Register via `register_fetcher("bom", BOMFetcher)`
       and import the module in `services/ingestion/__init__.py` so it self-registers.

- [ ] 5. Add BOM to `config.yaml` `data_sources` — a `bom` entry with name, base_url
       (https://api.weather.bom.gov.au), and cron_expression (forecast every 3 hours;
       observations fetched within the same run). Show the config.yaml diff before editing
       per the config-change guardrail.

- [ ] 6. Weather query service — create `src/citylab/services/weather_query.py`
       (mirror energy_query): `query_forecasts(location, dt_from, dt_to)`,
       `query_observations(location)`, `summary()` grouped by region_relevance (demand
       centres, wind corridors, hydro catchments), and `outlook(factor)` for
       wind|rain|temperature filtered across the relevant corridors/catchments. Reuse
       `energy_query.latest_fetch_timestamp()` (or a BOM-scoped equivalent) for
       `data_as_of`. Accept location by name / id / region/state.

- [ ] 7. Weather API blueprint — create `src/citylab/routes/api_v1/weather.py`
       (`weather_api_bp`) with `GET /weather/forecasts`, `/weather/observations`,
       `/weather/summary`, `/weather/outlook?factor=...`, each protected by
       `require_api_token` and returning the `{ok, data, data_as_of}` envelope. Register
       the blueprint in `src/citylab/routes/api_v1/__init__.py`.

- [ ] 8. Weather CLI group — create `src/citylab/cli_wrapper/commands_weather.py`
       (`weather_group`) with `summary`, `outlook --factor wind|rain|temperature`,
       `forecasts --location ...`, and `observations --location ...`, mirroring
       commands_energy (APIClient + JSON print). Register with
       `main.add_command(weather_group, "weather")` in `cli_wrapper/__init__.py`.

- [ ] 9. Tests — add targeted tests using the existing fixtures (`app`, `client`,
       `db_session`), no live network: BOMFetcher transform/store + synthetic fallback;
       location seeding idempotency; weather_query summary/outlook grouping; weather API
       endpoints returning the envelope with `data_as_of`.

- [ ] 10. End-to-end demo verification — run the BOM fetcher once (live or synthetic),
        confirm forecasts + observations land for all 10 locations, then walk the demo
        script via `PYTHONPATH=src python -m citylab.cli_wrapper`: `data sources` shows BOM,
        `weather summary`, `weather outlook --factor wind`, `weather outlook --factor rain`.
        Confirm the rain-outlook → Basslink → energy-summary correlation narrative is
        supported by the data.

## Demo Script

1. `cli-citylab data sources` — see BOM listed alongside OpenNEM as active data source
2. `cli-citylab weather summary` — see current conditions: Melbourne temp and demand context, SA wind corridor speeds, Tas catchment rainfall, Snowy rainfall
3. `cli-citylab weather outlook --factor wind` — see 3-day wind forecast across SA and Vic wind corridors
4. `cli-citylab weather outlook --factor rain` — see rainfall outlook for Tasmanian and Snowy hydro catchments
5. The key proof: an agent reads `cli-citylab weather outlook --factor rain` → sees heavy rain forecast for Tas → infers Basslink imports likely to increase → correlates with `cli-citylab energy summary` → reasons that prices may soften
