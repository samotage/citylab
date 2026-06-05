# cli-citylab — Command Reference

CLI for the CityLab energy operations hub. All commands hit the REST API (`/api/v1/*`) via Bearer token auth. All output is JSON.

**Read this doc before answering any data or market question.** It tells you what instruments you have and what each one returns.

## Command Groups

| Group | Purpose |
|---|---|
| `app` | Application health and status |
| `energy` | Victorian spot prices, generation mix, interconnectors, forecasts, timeseries |
| `weather` | BOM forecasts and observations for energy-relevant locations |
| `solar` | Solcast solar irradiance forecasts |
| `data` | Data source registry, cross-source intelligence, ingestion controls |
| `schedules` | Scheduled task (cron job) management |
| `agent` | Remote agent session lifecycle and config |

## Response Envelope

Every endpoint returns: `{"ok": true, "data": {...}, "data_as_of": "ISO timestamp"}`. Check `data_as_of` to judge freshness — stale data needs a fetch trigger or a caveat to the operator.

---

## app

### `cli-citylab app status`

Application health check — database connectivity, scheduler state, job count.

```
cli-citylab app status
```

Returns: `{app, version, database, scheduler, scheduled_jobs}`

---

## energy

### `cli-citylab energy summary --region VIC1`

**Start here for any market question.** Current snapshot in one call: latest spot price, demand, generation mix by fuel type, interconnector flows, price trend, forecast direction.

```
cli-citylab energy summary
cli-citylab energy summary --region VIC1
```

Returns: `{current_price, demand_mw, generation_mix: [{fuel_type, output_mw}], interconnectors: [{name, flow_mw}], price_trend, forecast_direction}`

### `cli-citylab energy prices`

Historical/current spot prices. Defaults to last 24h if no range specified.

```
cli-citylab energy prices
cli-citylab energy prices --region VIC1 --from 2026-06-04 --to 2026-06-05
```

Returns: list of `{interval_start, price_aud_mwh, region}`

### `cli-citylab energy generation`

Generation output by fuel type. Shows what's running and how much.

```
cli-citylab energy generation
cli-citylab energy generation --region VIC1 --from 2026-06-04
```

Returns: list of `{interval_start, fuel_type, output_mw, region}`

Fuel types: `brown_coal`, `gas` (CCGT/OCGT/recip/steam), `hydro`, `wind`, `solar` (utility/rooftop), `battery_discharging`, `battery_charging`, `biomass`, `distillate`, `other`.

### `cli-citylab energy interconnectors`

Cross-border power flows for VIC corridors: Basslink (TAS), Heywood (SA), Murraylink (SA), VNI (NSW), VNI West (NSW).

```
cli-citylab energy interconnectors
cli-citylab energy interconnectors --from 2026-06-04
```

Returns: list of `{interval_start, interconnector_id, flow_mw}`. Positive = import to VIC, negative = export.

### `cli-citylab energy forecasts`

Forward price forecasts from the latest available forecast run.

```
cli-citylab energy forecasts
cli-citylab energy forecasts --region VIC1
```

Returns: list of `{forecast_time, price_aud_mwh, forecast_type}`

### Timeseries (chart-ready data)

Windowed, interval-bucketed data designed for charts and trend analysis. Use these when you need to reason about trends over time ("prices rising for 3 hours", "demand peaked at 6pm").

**Ranges:** `1h`, `6h`, `24h` (default), `7d`, `30d`
**Intervals:** auto-selected per range, or override: `5min`, `1h`, `1d`

| Range | Default interval | Allowed intervals |
|---|---|---|
| 1h | 5min | 5min |
| 6h | 5min | 5min, 1h |
| 24h | 1h | 5min, 1h |
| 7d | 1h | 1h, 1d |
| 30d | 1d | 1h, 1d |

**Note:** These endpoints exist in the API (`/api/v1/energy/timeseries/{price,demand,generation}`) but do not yet have CLI commands. Call via the API directly or use the dashboard at `/energy` for visual charts.

API examples:
```
GET /api/v1/energy/timeseries/price?range=24h&region=VIC1
GET /api/v1/energy/timeseries/demand?range=7d&interval=1h
GET /api/v1/energy/timeseries/generation?range=6h&interval=5min
```

Returns: `{ok, region, range, interval, series: [{timestamp, value}], data_as_of}`

---

## weather

### `cli-citylab weather summary`

Current conditions grouped by energy-relevant regions — wind corridors, hydro catchments, solar zones.

```
cli-citylab weather summary
```

Returns: per-location current conditions (temperature, wind speed/direction, rain, humidity) grouped by relevance to Victorian energy generation.

### `cli-citylab weather outlook`

Filtered outlook for a specific weather factor across energy-relevant corridors.

```
cli-citylab weather outlook --factor wind --days 3
cli-citylab weather outlook --factor rain --days 5
cli-citylab weather outlook --factor temperature
```

Factors: `wind` (affects wind generation and interconnector corridors), `rain` (hydro catchments), `temperature` (demand driver — heating/cooling load).

Returns: per-corridor/catchment outlook for the specified factor and horizon.

### `cli-citylab weather forecasts`

Detailed forecasts for a location or region.

```
cli-citylab weather forecasts
cli-citylab weather forecasts --location Melbourne
cli-citylab weather forecasts --location VIC --from 2026-06-04 --to 2026-06-06
```

Returns: list of forecast periods with temperature, rain probability, wind speed/direction.

### `cli-citylab weather observations`

Latest actual observations for a location or region.

```
cli-citylab weather observations
cli-citylab weather observations --location Melbourne
```

Returns: latest observation data (temperature, wind, rain, humidity, pressure).

---

## solar

### `cli-citylab solar summary`

Current irradiance and next-24h solar outlook grouped by region relevance.

```
cli-citylab solar summary
```

Returns: per-location current GHI/DNI/DHI values and near-term forecast, grouped by VIC/SA solar regions.

### `cli-citylab solar outlook`

Multi-day solar outlook: peak GHI and cloud opacity by day per location.

```
cli-citylab solar outlook
cli-citylab solar outlook --days 5
```

Returns: per-location per-day peak GHI (W/m²) and cloud cover forecast.

### `cli-citylab solar forecasts`

Detailed irradiance forecasts (GHI/DNI/DHI) for a specific location.

```
cli-citylab solar forecasts
cli-citylab solar forecasts --location "VIC Solar Farm"
cli-citylab solar forecasts --location SA --from 2026-06-04
```

Returns: list of `{forecast_time, ghi, dni, dhi, cloud_opacity}` for the location.

---

## data

### `cli-citylab data sources`

List all registered data sources and their ingestion status.

```
cli-citylab data sources
```

Returns: list of `{id, name, source_type, is_active, last_fetch_status, last_fetch_at}`.

Three sources: OpenNEM (energy market, every 5min), BOM (weather, every 3h), Solcast (solar, hourly).

### `cli-citylab data status --id <source_id>`

Detailed fetch status for one data source.

```
cli-citylab data status --id 1
```

Returns: `{source, last_fetch_status, last_fetch_at, fetch_count, error_count, last_error}`

### `cli-citylab data fetch --id <source_id>`

Manually trigger an ingestion cycle. Use when data looks stale.

```
cli-citylab data fetch --id 1
```

Returns: `{ok, fetched_rows, source, duration_ms}`

### `cli-citylab data market-intelligence`

**Cross-source summary — the "give me everything" call.** Combines energy snapshot + weather conditions + source health in one response.

```
cli-citylab data market-intelligence
cli-citylab data market-intelligence --region VIC1
```

Returns: `{region, sources: [{name, source_type, status, data_as_of}], energy: {snapshot}, weather: {summary, rain_outlook, wind_outlook}, solar: null}`. Note: solar field is a placeholder — not yet wired.

### `cli-citylab data backfill`

Trigger historical data backfill for a source.

```
cli-citylab data backfill --source opennem --from 2026-06-01 --to 2026-06-04
cli-citylab data backfill --source bom --chunk-days 1
```

Sources: `opennem`, `bom`, `solcast`.

### `cli-citylab data verify`

Run data completeness, freshness, and consistency checks. Non-zero exit on failure.

```
cli-citylab data verify
cli-citylab data verify --region VIC1 --json
```

Returns: per-source, per-category check results with pass/fail and detail on failures. Use `--json` for machine-readable output.

---

## schedules

### `cli-citylab schedules list`

List all scheduled tasks (cron jobs).

```
cli-citylab schedules list
```

Returns: list of `{id, name, cron_expression, agent_persona, agent_action, is_active, last_run_at}`

### `cli-citylab schedules create`

Create a new scheduled task.

```
cli-citylab schedules create --name "morning-report" --cron "0 6 * * *" --persona energy-market-analyst-ray-50 --action "Run a morning market summary"
```

### `cli-citylab schedules delete --id <task_id>`

Delete a scheduled task.

```
cli-citylab schedules delete --id 3
```

---

## agent

Session lifecycle and config for remote agents (Headspace integration).

### `cli-citylab agent start`

Start (resume-or-create) an agent session.

```
cli-citylab agent start
cli-citylab agent start --persona energy-market-analyst-ray-50
cli-citylab agent start --persona energy-market-analyst-ray-50 --prompt "Morning market brief"
```

### `cli-citylab agent stop`

Stop the active agent session.

```
cli-citylab agent stop
cli-citylab agent stop --persona energy-market-analyst-ray-50
cli-citylab agent stop --session-id 42
```

### `cli-citylab agent status`

Show the active session status with live liveness check.

```
cli-citylab agent status
cli-citylab agent status --persona energy-market-analyst-ray-50
```

### `cli-citylab agent check`

Alias for `status` — liveness probe on the active session.

### `cli-citylab agent message <text>`

Send a message to the active agent session.

```
cli-citylab agent message "What's the current spot price?"
cli-citylab agent message "Run a generation mix analysis" --persona energy-market-analyst-ray-50
```

### `cli-citylab agent list`

List configured agent personas.

```
cli-citylab agent list
cli-citylab agent list --all
```

### `cli-citylab agent add-config`

Add a new agent config.

```
cli-citylab agent add-config --name "Ray" --persona energy-market-analyst-ray-50 --description "NEM energy market analyst" --default
```

### `cli-citylab agent set-default`

Set the default agent config.

```
cli-citylab agent set-default --persona energy-market-analyst-ray-50
```

---

## Common Workflows

### "What's happening in the market right now?"
```
cli-citylab energy summary --region VIC1
```
One call gives you price, demand, generation mix, interconnector flows, and forecast direction.

### "Give me everything across all sources"
```
cli-citylab data market-intelligence --region VIC1
```
Cross-source summary: energy + weather + source health in one response.

### "Are the data pipelines healthy?"
```
cli-citylab data sources
cli-citylab data verify --region VIC1
```
First shows source status, second runs completeness/freshness/consistency checks.

### "What's driving the price?"
1. `cli-citylab energy summary` — current price + generation mix
2. `cli-citylab energy generation` — detailed fuel breakdown over time
3. `cli-citylab weather outlook --factor wind` — wind generation outlook
4. `cli-citylab solar outlook` — solar generation outlook
5. `cli-citylab energy interconnectors` — cross-border flows

### "What's the weather doing to generation?"
1. `cli-citylab weather summary` — conditions across energy regions
2. `cli-citylab weather outlook --factor wind --days 3` — wind corridor forecast
3. `cli-citylab solar outlook --days 3` — solar irradiance forecast
4. `cli-citylab energy generation` — actual generation to correlate

### "Show me charts / visual data"
Direct the operator to the energy dashboard at `/energy` — it renders live charts for price, generation mix, interconnector flows, and forecasts. For raw chart data, use the timeseries API endpoints documented above.

### Data feels stale — refresh it
```
cli-citylab data sources          # check last_fetch_at per source
cli-citylab data fetch --id 1     # manually trigger the stale source
cli-citylab data verify           # confirm data is now fresh
```
