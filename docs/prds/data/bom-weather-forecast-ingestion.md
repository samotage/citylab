---
validation:
  status: valid
  validated_at: '2026-06-03T07:42:05+10:00'
---

# BOM Weather Forecast Ingestion

## Problem

Victorian energy prices are heavily influenced by weather conditions across south-eastern Australia — not just in Victoria. Rain drives hydro generation in Tasmania and the Snowy scheme. Wind drives South Australia's surplus that flows into Victoria via Heywood and Murraylink. Temperature drives Victorian demand (heating in winter, cooling in summer). Cloud cover suppresses solar output. Without weather forecast data, an agent reasoning about energy prices is missing the causal layer that explains *why* generation and demand behave the way they do.

This PRD delivers BOM weather forecast ingestion using the shared data source architecture established in PRD 1 (energy-market-data-ingestion).

## Approach

### Data Source Registration

Register BOM as a data source in the DataSource registry (source_type: `bom`). Implement `BOMFetcher` class following the fetcher pattern from PRD 1 (fetch → transform → store).

### BOM Data Source

Bureau of Meteorology public forecast data. BOM publishes forecast data via:
- FTP product files (XML/JSON) — structured forecast data by region
- Public API (api.weather.bom.gov.au) — observation and forecast endpoints
- Confirm exact access method during build — BOM has historically been inconsistent about API stability

### Forecast Locations

Weather stations and forecast areas selected for their influence on Victorian energy price:

**Victorian (direct demand + local generation):**
- Melbourne metro — demand driver (population centre)
- Western Victoria (e.g., Ballarat/Ararat region) — wind farm corridor
- Gippsland — brown coal generation + offshore wind

**Tasmanian (hydro → Basslink):**
- Western Tasmania (Strahan/Queenstown) — hydro catchment rainfall
- Central Highlands — hydro catchment rainfall

**South Australian (wind → Heywood/Murraylink):**
- Mid-North SA (Port Augusta/Clare) — major wind farm corridor
- Yorke Peninsula / Adelaide Hills — wind generation

**NSW/Snowy (hydro + interconnector):**
- Snowy Mountains region — Snowy Hydro catchment rainfall
- Southern NSW — VNI interconnector demand context

### Data Models

1. **Weather Forecast** — `WeatherForecast`
   - location_id (FK to WeatherLocation), issued_at, forecast_for (target datetime), forecast_period (hourly/3hourly/daily), temperature_min_c, temperature_max_c, temperature_c (point forecast), wind_speed_kmh, wind_direction, wind_gust_kmh, rainfall_mm, rainfall_probability_pct, cloud_cover_pct (where available), humidity_pct, weather_description
   - Source: BOM forecast product files or API

2. **Weather Location** — `WeatherLocation`
   - name, bom_station_id, bom_forecast_area_id, latitude, longitude, state, region_relevance (text — why this location matters: "hydro_catchment", "wind_corridor", "demand_centre", "solar_region")
   - Seeded on first deploy with the locations listed above

3. **Weather Observation** — `WeatherObservation`
   - location_id (FK), observed_at, temperature_c, wind_speed_kmh, wind_direction, wind_gust_kmh, rainfall_since_9am_mm, humidity_pct, pressure_hpa
   - Actuals for validating forecasts and providing current conditions
   - Source: BOM observation API

### Forecast Horizons

- **Short-range:** Hourly/3-hourly out to 3 days — highest value for next-day energy market decisions
- **Medium-range:** Daily out to 7 days — useful for weekly generation planning
- **Long-range (extended):** Weekly outlook out to 14 days where available — hydro catchment planning

### Agent-Queryable API

- `GET /api/v1/weather/forecasts?location=...&from=...&to=...` — forecasts for a location or region
- `GET /api/v1/weather/observations?location=...` — latest observations
- `GET /api/v1/weather/summary` — current conditions and short-range outlook across all tracked locations, grouped by relevance (demand centres, wind corridors, hydro catchments)
- `GET /api/v1/weather/outlook?factor=wind|rain|temperature` — filtered view: "what's the wind outlook across SA and Vic wind corridors?" or "what's the rainfall outlook for hydro catchments?"
- CLI: `cli-citylab weather summary`, `cli-citylab weather outlook --factor wind`, `cli-citylab weather forecasts --location melbourne`

**Freshness contract (from PRD 1 Part A):** All weather API responses include a `data_as_of` ISO timestamp in the response envelope indicating when weather data was last fetched. This feeds into the cross-source `market-intelligence` endpoint.

### Data Retention

- Keep all data — no rolling window (consistent with energy market data retention policy in PRD 1). Historical weather data has analytical value for pattern correlation with price movements.

### Scheduling

- Forecast fetch: every 3 hours (BOM updates forecasts roughly on this cycle)
- Observations: every 30 minutes
- Backfill: last 3 days of forecasts on first run (shorter than energy's 7 days because forecast data has less historical replay value than price data)

## Done When

- [ ] BOM registered as DataSource, BOMFetcher class implemented following PRD 1 fetcher pattern
- [ ] WeatherLocation, WeatherForecast, WeatherObservation models with migrations applied
- [ ] Forecast locations seeded covering Vic, Tas, SA, and Snowy regions
- [ ] Forecasts landing for all tracked locations — short-range (3-day) and medium-range (7-day)
- [ ] Observations landing for all tracked locations
- [ ] Weather API endpoints return real data: forecasts, observations, summary, outlook
- [ ] `cli-citylab weather summary` returns grouped conditions across all tracked regions
- [ ] `cli-citylab weather outlook --factor rain` returns rainfall outlook for hydro catchments
- [ ] Scheduled fetches running via APScheduler on configured intervals
- [ ] An agent can correlate weather forecasts with energy market data: "heavy rain in Tas catchments + strong wind in SA = likely oversupply pressure"

## Demo Script

1. `cli-citylab data sources` — see BOM listed alongside OpenNEM as active data source
2. `cli-citylab weather summary` — see current conditions: Melbourne temp and demand context, SA wind corridor speeds, Tas catchment rainfall, Snowy rainfall
3. `cli-citylab weather outlook --factor wind` — see 3-day wind forecast across SA and Vic wind corridors
4. `cli-citylab weather outlook --factor rain` — see rainfall outlook for Tasmanian and Snowy hydro catchments
5. The key proof: an agent reads `cli-citylab weather outlook --factor rain` → sees heavy rain forecast for Tas → infers Basslink imports likely to increase → correlates with `cli-citylab energy summary` → reasons that prices may soften
