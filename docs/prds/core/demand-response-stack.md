# Demand Response Stack

## Problem

The storage dispatch optimiser gives the platform one decision lever — battery charge/discharge. Real grid operations have a second: shedding controllable demand when supply is stressed. Without demand response, the platform's only answer to a supply shortfall is "discharge the battery harder." With it, the platform can stage a ranked curtailment waterfall — cheapest loads first — that looks like an actual operations centre managing a city's energy.

This is the Saturday stretch target. It adds a second decision surface to the demo, transforming the platform from a single-trick optimiser into a portfolio manager balancing storage and demand.

## Approach

### New Model: ControllableLoad

Synthetic controllable loads representing a city's demand-side assets. Config-driven, seeded from `config.yaml`.

```
controllable_loads table:
  name              String(120), unique     — e.g. "Hot Water Systems (Residential)"
  region            String(20)              — NEM region
  load_type         String(40)              — "hot_water" / "ev_charging" / "hvac_commercial" / "industrial_process"
  capacity_mw       Float                   — max curtailable MW
  curtailment_cost  Float                   — $/MWh cost of curtailing this load (opportunity cost)
  min_duration_min  Integer                 — minimum curtailment duration (minutes)
  max_duration_min  Integer                 — maximum curtailment duration
  status            String(20)              — "available" / "curtailed" / "unavailable" / "recovering"
  curtailed_since   DateTime(tz), nullable  — when curtailment started (null if available)
```

No FKs to existing models. Loads are ordered by `curtailment_cost` ascending — cheapest shed first.

### New Model: DemandResponseEvent

Logs curtailment activations and releases.

```
demand_response_events table:
  load_id           FK -> controllable_loads.id
  timestamp         DateTime(tz)
  action            String(20)             — "curtail" / "release" / "hold"
  capacity_mw       Float                  — MW curtailed or released
  trigger           String(40)             — "lor_condition" / "price_spike" / "supply_deficit" / "schedule"
  reason            String(500)            — human-readable explanation
  market_price      Float, nullable
```

### Service: `src/citylab/services/demand_response.py`

Evaluates demand response activation on the same 5-min cycle as dispatch, after the dispatch engine runs.

**Decision logic:**

1. **Supply deficit trigger** — compare total generation (from `current_snapshot().generation_mix`) against demand. If demand exceeds supply + available battery discharge capacity: activate loads cheapest-first until the deficit is covered. Reason: "Supply deficit of X MW after battery dispatch — curtailing hot water (12 MW) and EV charging (8 MW)".

2. **Price spike trigger** — if spot price > demand_response_price_threshold (configurable, default $300/MWh) and battery is already discharging or holding for contingency: activate loads cheapest-first. Reason: "Price at $X/MWh with battery committed to contingency — activating demand response".

3. **Release logic** — if conditions normalise (supply surplus restored, price below threshold for 2 consecutive intervals): release loads in reverse order (most expensive first, since those have the highest curtailment cost). Respect min_duration_min before releasing.

4. **Recovery period** — after release, load enters "recovering" status for a configurable period (default 15 min) before becoming available again. Prevents cycling.

**Config thresholds** in `config.yaml`:

```yaml
demand_response:
  price_threshold_aud_mwh: 300
  recovery_period_min: 15
  max_simultaneous_curtailments: 4
```

### Config Seed

```yaml
controllable_loads:
  - name: "Hot Water Systems (Residential)"
    region: VIC1
    load_type: hot_water
    capacity_mw: 45
    curtailment_cost: 15
    min_duration_min: 30
    max_duration_min: 240
  - name: "EV Charging Network"
    region: VIC1
    load_type: ev_charging
    capacity_mw: 25
    curtailment_cost: 35
    min_duration_min: 15
    max_duration_min: 120
  - name: "Commercial HVAC"
    region: VIC1
    load_type: hvac_commercial
    capacity_mw: 60
    curtailment_cost: 80
    min_duration_min: 15
    max_duration_min: 60
  - name: "Industrial Process (Aluminium)"
    region: VIC1
    load_type: industrial_process
    capacity_mw: 150
    curtailment_cost: 200
    min_duration_min: 60
    max_duration_min: 480
```

Four loads gives the demo a realistic curtailment waterfall — cheap domestic first, expensive industrial last.

### API Endpoints

Under `/api/v1/energy/demand-response`, Bearer token auth.

- `GET /api/v1/energy/demand-response/status` — all loads, current status, curtailment cost, capacity
- `GET /api/v1/energy/demand-response/log?limit=20` — recent DemandResponseEvents
- `POST /api/v1/energy/demand-response/evaluate` — run the DR logic now, return recommendations

### Dashboard Integration

New sub-panel under "Storage Dispatch" or adjacent — "Demand Response":

- Ranked load list showing name, capacity_mw, curtailment_cost, status badge (available/curtailed/recovering)
- Visual curtailment waterfall — stacked horizontal bar showing which loads are active, ordered by cost
- Total curtailed MW counter
- Last activation reason text

### Interaction with Dispatch Engine

The demand response service reads the dispatch engine's output. If the battery is holding for contingency or already fully dispatched, that information feeds into the DR trigger logic. They compose — dispatch handles the battery, DR handles the loads, and the dashboard shows both decision surfaces together.

## Done When

- [ ] `ControllableLoad` and `DemandResponseEvent` models created with migration
- [ ] Loads seed from `config.yaml`
- [ ] DR service activates loads cheapest-first when supply deficit or price spike detected
- [ ] DR service releases loads most-expensive-first when conditions normalise
- [ ] Recovery period prevents load cycling
- [ ] `GET /api/v1/energy/demand-response/status` returns load states
- [ ] `GET /api/v1/energy/demand-response/log` returns recent events with reasons
- [ ] Dashboard shows curtailment waterfall and active status
- [ ] DR composes with dispatch engine — battery + loads visible as coordinated response

## Demo Script

1. From the dispatch demo (storage dispatch PRD step 6), the battery is holding at 30% SoC due to interconnector stress
2. Trigger a demand spike (hot afternoon scenario) — demand exceeds available supply
3. Watch the demand response panel activate: hot water systems curtailed first (cheapest at $15/MWh), then EV charging ($35/MWh)
4. Read the reason: "Supply deficit of 35 MW after battery contingency hold — curtailing hot water (45 MW)"
5. Show the curtailment waterfall — two loads active, two still available
6. Ask Ray: "What happens if we need more?" — Ray narrates the escalation path: HVAC next at $80/MWh, industrial last resort at $200/MWh
7. The key insight: "The platform doesn't just manage a battery — it orchestrates a city's entire flexible demand portfolio, cheapest-first, with full explainability"
