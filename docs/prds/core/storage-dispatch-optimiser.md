# Storage Dispatch Optimiser + Forecast Pre-Positioning

## Problem

CityLab observes battery charge/discharge in the NEM but makes no dispatch decisions. In a Grid Guardian simulation, every team will have storage — the differentiator is whether the platform dispatches it intelligently. Without a dispatch engine, we're an expensive dashboard. With one, we're an operations centre that makes decisions and explains them.

The platform already has price forecasts (30-min predispatch), solar forecasts (GHI, cloud opacity, PV output), weather forecasts (wind speed/direction, temperature), and interconnector flow data with capacity limits. All the inputs for intelligent dispatch exist — no decision logic consumes them.

## Approach

### New Model: BatteryAsset

Config-driven battery definition, seeded from `config.yaml` via `flask seed-data-sources` (extend the existing seed command). One row per managed battery.

```
battery_assets table:
  name              String(120), unique     — e.g. "City BESS Alpha"
  region            String(20)              — NEM region (VIC1)
  capacity_mwh      Float                   — total energy capacity
  max_power_mw      Float                   — max charge/discharge rate
  roundtrip_eff     Float                   — roundtrip efficiency (0.0–1.0, e.g. 0.85)
  min_soc_pct       Float                   — hard floor (e.g. 10.0)
  max_soc_pct       Float                   — hard ceiling (e.g. 95.0)
  reserve_soc_pct   Float                   — contingency reserve threshold (e.g. 30.0)
  current_soc_pct   Float                   — current state of charge
  status            String(20)              — "idle" / "charging" / "discharging" / "holding"
```

No migration complexity — one new table, no FKs to existing models. Standard BaseModel inheritance.

### New Model: DispatchEvent

Logs every dispatch decision for the explainability surface and dashboard history.

```
dispatch_events table:
  battery_id        FK -> battery_assets.id
  timestamp         DateTime(tz)            — when the decision was made
  action            String(20)              — "charge" / "discharge" / "hold"
  power_mw          Float                   — MW dispatched (0 for hold)
  soc_before_pct    Float                   — SoC at decision time
  soc_after_pct     Float                   — projected SoC after action
  trigger           String(40)              — signal that fired: "price_forecast", "solar_pre_position", "wind_pre_position", "interconnector_stress", "contingency_hold", "schedule"
  reason            String(500)             — human-readable explanation
  market_price      Float, nullable         — spot price at decision time ($/MWh)
  forecast_price    Float, nullable         — next-period forecast price at decision time
```

Index on (battery_id, timestamp). This is the table Ray reads from to narrate decisions.

### New Service: `src/citylab/services/dispatch.py`

Rules-based dispatch engine. Evaluated on every ingestion cycle (5-min cron, after OpenNEM data lands) or on-demand via API.

**Decision tree, evaluated top-to-bottom — first matching rule wins:**

1. **Interconnector stress hold** — query latest InterconnectorFlow for the battery's region. If any interconnector touching the region is at >85% of capacity_mw (flow_mw / capacity_mw), and current SoC > reserve_soc_pct: action=hold. Reason: "Basslink import at 92% capacity — holding reserve for contingency headroom". This prevents discharging into a price spike when the grid is already stressed and may need emergency reserves.

2. **Solar pre-position** — query Solcast forecasts for the battery's region, next 2 hours. If average cloud_opacity_pct > 60% AND current hour is between 10:00–16:00 local AND current SoC < 70%: action=charge. Reason: "Cloud band forecast — pre-charging before solar output drops". Uses existing `solar_query.query_forecasts()`.

3. **Wind pre-position** — query BOM weather forecasts for wind_corridor locations in the battery's region, next 3 hours. If forecast wind_speed_kmh drops >30% from current observation: action=charge (if SoC < 70%). Reason: "Wind corridor speed dropping 40% in next 3h — pre-charging ahead of reduced wind generation". Uses existing `weather_query.query_forecasts()` + `weather_query.query_observations()`.

4. **Price arbitrage — discharge** — query latest PriceForecast for the battery's region. If next-period forecast price > discharge_threshold (configurable, default $150/MWh) AND current SoC > reserve_soc_pct: action=discharge at max_power_mw. Reason: "Forecast price $X/MWh exceeds discharge threshold — dispatching into high-price period".

5. **Price arbitrage — charge** — if current spot price < charge_threshold (configurable, default $40/MWh) AND current SoC < max_soc_pct: action=charge at max_power_mw. Reason: "Spot price $X/MWh below charge threshold — accumulating cheap energy".

6. **Default hold** — action=hold, power=0. Reason: "No dispatch trigger — holding current SoC at X%".

**SoC update:** after each dispatch decision, update `battery_assets.current_soc_pct` based on action, power_mw, interval duration (5 min), and roundtrip_eff. Clamp to [min_soc_pct, max_soc_pct].

**Config thresholds** in `config.yaml` under a new `dispatch` section:

```yaml
dispatch:
  discharge_threshold_aud_mwh: 150
  charge_threshold_aud_mwh: 40
  interconnector_stress_pct: 85
  solar_cloud_opacity_trigger_pct: 60
  wind_drop_trigger_pct: 30
  pre_position_soc_ceiling_pct: 70
```

### Scheduler Integration

Register a new job type in `scheduler.py`: after each successful OpenNEM ingestion for a region, run the dispatch evaluation for all active BatteryAssets in that region. This piggybacks on the existing 5-min cron — no new scheduler entry needed, just a post-ingestion hook.

### API Endpoints

All under `/api/v1/energy/dispatch`, Bearer token auth (existing `require_api_token` decorator).

- `GET /api/v1/energy/dispatch/status` — current state of all batteries: name, region, soc_pct, status, last dispatch action/reason/timestamp
- `GET /api/v1/energy/dispatch/recommend?battery=<name>` — run the dispatch engine NOW for a specific battery, return the recommendation without executing it: {action, power_mw, trigger, reason, soc_before, soc_after}
- `POST /api/v1/energy/dispatch/execute?battery=<name>` — run and execute the dispatch decision, update SoC, log DispatchEvent, return the event
- `GET /api/v1/energy/dispatch/log?battery=<name>&limit=50` — recent DispatchEvents for a battery, newest first. This is Ray's narration surface.

### CLI Integration

Extend `cli-citylab` with dispatch commands:

- `cli-citylab dispatch status` — all batteries, current state
- `cli-citylab dispatch recommend --battery "City BESS Alpha"` — what would the engine do right now?
- `cli-citylab dispatch log --battery "City BESS Alpha" --limit 10` — recent decisions with reasons

### Dashboard Integration

New panel on `/energy` dashboard — "Storage Dispatch":

- SoC gauge per battery (radial or horizontal bar, coloured by zone: green > reserve, amber near reserve, red at min)
- Current action badge (CHARGING / DISCHARGING / HOLDING / IDLE)
- Last decision reason text (the `reason` field — this is the explainability surface)
- Trigger indicator (icon or label showing what signal fired)
- Mini timeline of recent dispatch events (last 6–12 decisions as a compact horizontal strip)
- HTMX polling on 60s interval to stay current

### Config Seed

Add battery assets to `config.yaml` under `battery_assets`:

```yaml
battery_assets:
  - name: "City BESS Alpha"
    region: VIC1
    capacity_mwh: 200
    max_power_mw: 100
    roundtrip_eff: 0.85
    min_soc_pct: 10
    max_soc_pct: 95
    reserve_soc_pct: 30
    initial_soc_pct: 50
  - name: "City BESS Beta"
    region: VIC1
    capacity_mwh: 50
    max_power_mw: 25
    roundtrip_eff: 0.90
    min_soc_pct: 5
    max_soc_pct: 95
    reserve_soc_pct: 20
    initial_soc_pct: 60
```

Two batteries gives the demo portfolio management depth — one large grid-scale, one smaller distributed.

### Simulation Adapter Note

The dispatch engine reads market state from CityLab's own tables (EnergyPrice, PriceForecast, InterconnectorFlow, SolarForecast, WeatherForecast). If the hackathon simulation provides its own market data, the adapter path is: ingest simulation data into these same tables (new fetcher subclass), and the dispatch engine works unchanged. No conditional logic needed — just a different data source.

## Done When

- [ ] `BatteryAsset` and `DispatchEvent` models created with migration
- [ ] Battery assets seed from `config.yaml` via extended `flask seed-data-sources`
- [ ] Dispatch service evaluates all 6 rules in priority order and produces action + reason
- [ ] SoC updates correctly after each dispatch (respects efficiency, clamps to min/max)
- [ ] Dispatch runs automatically after each OpenNEM ingestion cycle
- [ ] `GET /api/v1/energy/dispatch/status` returns current battery states
- [ ] `GET /api/v1/energy/dispatch/recommend` returns recommendation with reason
- [ ] `POST /api/v1/energy/dispatch/execute` executes and logs a DispatchEvent
- [ ] `GET /api/v1/energy/dispatch/log` returns recent events with reasons
- [ ] `cli-citylab dispatch status` and `dispatch log` work
- [ ] Dashboard shows SoC gauge, current action, and decision reason for each battery
- [ ] Dispatch config thresholds are in `config.yaml` and respected by the engine

## Demo Script

1. Open the energy dashboard — show the new Storage Dispatch panel alongside live market data
2. Point to the SoC gauge — "We're managing a 200 MWh grid-scale battery and a 50 MWh distributed unit"
3. Wait for (or trigger) a price spike scenario — the dispatch engine fires, action changes to DISCHARGING
4. Read the reason field: "Forecast price $180/MWh exceeds discharge threshold — dispatching into high-price period"
5. Run a Basslink stress scenario (from the scenario engine PRD) — watch the dispatch engine switch to HOLDING
6. Read the reason: "Basslink import at 91% capacity — holding 30% SoC reserve for contingency headroom"
7. Show the dispatch log — a timeline of decisions with reasons, showing the platform reasoning about grid state over time
8. Ask Ray (voice): "Why did the battery hold instead of discharging into that price spike?" — Ray reads the dispatch log and explains the interconnector stress logic
9. The key insight: "This isn't a dashboard — it's an operations centre that makes decisions, explains why, and has a domain specialist you can interrogate in real time"
