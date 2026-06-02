---
validation:
  status: valid
  validated_at: '2026-06-03T07:42:06+10:00'
---

# Solcast Solar Irradiance Forecast Ingestion

## Problem

Solar generation is a major and growing component of the Victorian energy mix — both utility-scale solar farms and rooftop PV. On a sunny day, rooftop solar alone can suppress midday demand by several gigawatts across the NEM. An agent reasoning about energy prices needs to know not just current solar output (available from OpenNEM generation data) but *forecast* solar irradiance — what's the sun going to do over the next hours and days? BOM provides cloud cover as a rough proxy, but Solcast provides purpose-built solar irradiance forecasts at the granularity the energy market cares about.

This PRD delivers Solcast forecast ingestion using the shared data source architecture from PRD 1.

## Approach

### Data Source Registration

Register Solcast as a data source in the DataSource registry (source_type: `solcast`). Implement `SolcastFetcher` class following the fetcher pattern from PRD 1.

### Solcast API

[Solcast](https://solcast.com/) provides solar irradiance and PV power forecasts via REST API. They offer a free tier for research/non-commercial use and paid tiers for commercial. Key endpoints:
- Radiation forecasts — GHI (Global Horizontal Irradiance), DNI (Direct Normal Irradiance), DHI (Diffuse Horizontal Irradiance)
- PV power forecasts — estimated output for a given system configuration
- Confirm API access tier, rate limits, and authentication (API key) during build

### Forecast Locations

Solar forecast points selected for their influence on Victorian energy supply:

**Victorian solar regions:**
- North-west Victoria (Mildura/Swan Hill corridor) — utility-scale solar farm concentration
- Western Victoria (Ballarat/Bendigo) — solar + wind mixed corridor
- Melbourne metro — rooftop PV aggregate (significant demand-side impact)
- Gippsland — emerging solar region

**South Australian solar (interconnector influence):**
- Northern SA (Port Augusta) — large-scale solar + wind hybrid zone
- Riverland (Renmark/Berri) — solar corridor near Murraylink interconnect

### Data Models

1. **Solar Forecast** — `SolarForecast`
   - location_id (FK to SolarLocation), issued_at, forecast_for (target datetime), forecast_period (hourly/30min), ghi_wm2 (Global Horizontal Irradiance, W/m²), dni_wm2 (Direct Normal Irradiance), dhi_wm2 (Diffuse Horizontal Irradiance), cloud_opacity_pct, air_temp_c, estimated_pv_output_kw (for a reference system size, where available)
   - Source: Solcast radiation and PV power forecast endpoints

2. **Solar Location** — `SolarLocation`
   - name, latitude, longitude, state, region_relevance (text — "utility_solar", "rooftop_aggregate", "hybrid_zone"), reference_pv_capacity_kw (for PV output estimation context)
   - Seeded on first deploy with the locations listed above

### Forecast Horizons

- **Intraday:** 30-minute intervals out to 24 hours — highest value for same-day dispatch decisions
- **Short-range:** Hourly out to 7 days — generation planning horizon
- GHI is the primary metric (total irradiance on a flat surface); DNI and DHI add value for tracking-system vs fixed-panel generation estimates

### Agent-Queryable API

- `GET /api/v1/solar/forecasts?location=...&from=...&to=...` — irradiance forecasts for a location
- `GET /api/v1/solar/summary` — current and next-24h solar outlook across all tracked locations, with estimated generation impact
- `GET /api/v1/solar/outlook` — multi-day solar forecast summary: "sunny across Vic and SA next 3 days" vs "cloud band moving through, solar output dropping tomorrow"
- CLI: `cli-citylab solar summary`, `cli-citylab solar outlook`, `cli-citylab solar forecasts --location mildura`

**Freshness contract (from PRD 1 Part A):** All solar API responses include a `data_as_of` ISO timestamp in the response envelope indicating when solar data was last fetched. This feeds into the cross-source `market-intelligence` endpoint.

### Data Retention

- Keep all data — no rolling window (consistent with energy market data retention policy in PRD 1). Historical irradiance data supports pattern analysis against price movements.

### Scheduling

- Forecast fetch: every 1 hour (Solcast updates roughly hourly; respect rate limits)
- Backfill: last 3 days on first run (shorter than energy's 7 days — irradiance forecasts have less historical replay value than price data)
- Rate limit awareness: Solcast free tier has daily API call limits — the fetcher must track usage and back off if approaching limits

### Integration with Energy Reasoning

The solar forecast data complements OpenNEM generation data and BOM weather:
- OpenNEM tells you current solar output
- Solcast tells you forecast solar output (authoritative for solar-specific irradiance and cloud impact on PV)
- BOM tells you the broader weather context (cloud, wind, rain)
- Together: an agent can forecast the renewable generation mix and its impact on price

**Boundary with BOM:** BOM provides general cloud_cover_pct as part of weather forecasts. Solcast provides solar-specific cloud_opacity_pct tuned to irradiance impact. For solar generation reasoning, Solcast cloud data is authoritative. BOM cloud data is context for general weather understanding. An agent should use Solcast for "how much will solar panels produce?" and BOM for "what's the weather doing broadly?"

## Done When

- [ ] Solcast registered as DataSource, SolcastFetcher class implemented following PRD 1 fetcher pattern
- [ ] SolarLocation, SolarForecast models with migrations applied
- [ ] Forecast locations seeded covering Vic and SA solar regions
- [ ] Solar irradiance forecasts (GHI, DNI, DHI) landing for all tracked locations
- [ ] Solar API endpoints return real data: forecasts, summary, outlook
- [ ] `cli-citylab solar summary` returns current and next-24h solar outlook
- [ ] `cli-citylab solar outlook` returns multi-day narrative an agent can reason on
- [ ] Scheduled fetches running via APScheduler, respecting Solcast rate limits
- [ ] An agent can correlate solar forecasts with energy data: "GHI dropping tomorrow across Vic solar regions → expect reduced solar generation → price likely to rise if wind doesn't compensate"

## Demo Script

1. `cli-citylab data sources` — see Solcast listed alongside OpenNEM and BOM as active data sources
2. `cli-citylab solar summary` — see current irradiance and next-24h forecast across Victorian and SA solar regions
3. `cli-citylab solar outlook` — see multi-day view: "strong solar forecast across NW Vic for next 3 days, cloud band approaching from west on day 4"
4. `cli-citylab solar forecasts --location mildura` — see detailed hourly GHI/DNI/DHI forecast for the Mildura solar corridor
5. The key proof: an agent reads solar outlook → correlates with energy generation data → reasons about renewable supply impact on price
