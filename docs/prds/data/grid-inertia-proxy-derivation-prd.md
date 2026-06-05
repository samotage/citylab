# Grid Inertia Proxy Derivation

## Problem

CityLab has zero observability on grid inertia — the rotational kinetic energy in synchronous generators that buffers frequency after a disturbance. As renewables displace thermal plant, inertia drops and the grid becomes brittle: frequency falls faster after contingency events, and FCAS must respond sooner. We ingest generation mix by fuel type at 5-minute intervals but don't classify synchronous vs inverter-coupled sources, so we can't answer "how fragile is the grid right now?" or forecast when it will become fragile.

The grid doesn't carry a frequency sensor we can read. But we already have the ingredients: MW output per fuel type, each of which maps to a known inertia constant (H). This PRD builds a proxy inertia derivation from existing data, backfills it historically, and correlates it with weather to forecast ahead.

## Approach

### Derivation model

Classify each fuel type as synchronous or inverter-coupled:

| Class | Fuel types | H (seconds) |
|-------|-----------|-------------|
| Synchronous | brown_coal, black_coal | 4.0 |
| Synchronous | gas (ccgt, ocgt, recip, steam) | 3.0 |
| Synchronous | hydro | 3.0 |
| Synchronous | biomass | 3.5 |
| Synchronous | distillate | 2.5 |
| Inverter | wind, solar_utility, solar_rooftop, battery_discharging, battery_charging | 0 |

Two derived metrics per 5-minute interval:

1. **Synchronous fraction** = `sync_mw / total_mw` — the intuitive headline. Less sensitive to the MVA-vs-MW problem (see caveat below) because it's a ratio.
2. **E_proxy (MWs)** = `Σ (sync_output_mw × H)` — the physical stored energy estimate that feeds the payoff metric.

**Payoff metric — reference-contingency RoCoF:**

```
E_total = E_proxy + EXTERNAL_INERTIA_MWS
RoCoF (Hz/s) = (ΔP_ref × 50) / (2 × E_total)
```

VIC is synchronously coupled to the mainland NEM (NSW, QLD, SA) through interconnectors. The inertia that buffers a VIC contingency is the **entire mainland synchronous pool**, not VIC alone. `EXTERNAL_INERTIA_MWS` (default ~35,000 MWs) represents the mainland inertia VIC sees through its interconnectors. Without it, RoCoF runs 3–5× too hot and every interval reads "brittle" — which misrepresents VIC's actual grid state.

When an interconnector trips (scenario 2 in the brief), VIC's external inertia baseline drops — so an interconnector failure and an inertia spike become the same story. The `EXTERNAL_INERTIA_MWS` value could be reduced dynamically based on interconnector flow data we already ingest, but the static default is sufficient for the hackathon.

`ΔP_ref` = largest credible VIC contingency. Two configurable presets:
- **Heywood interconnector trip: 650 MW** (default) — largest interconnector contingency
- **Loy Yang A unit trip: 560 MW** — largest single generator contingency in VIC

Offering both in the UI is the strongest demo move: "biggest generator" vs "biggest interconnector" tells different risk stories. This converts the abstract inertia number into "if we lost the biggest unit right now, frequency would fall at X Hz/s" — the judge-facing sentence.

**Threshold bands** (NEM-typical VIC, configurable):

| State | Sync fraction | Ref-contingency RoCoF | Meaning |
|-------|--------------|----------------------|---------|
| Comfortable | ≥ 50% | < 0.25 Hz/s | Sufficient spinning mass |
| Watch | 30–50% | 0.25–0.5 Hz/s | Inertia thinning |
| Brittle | < 30% | > 0.5 Hz/s | 1 Hz/s is cascade danger zone |

Sync fraction bands are a within-VIC relative indicator of VIC's exposure within the mainland pool — not a claim that VIC is about to island. RoCoF bands are meaningful only with the external inertia term included (see E_total above).

### Central caveat — MVA vs MW

Inertia depends on MVA *spinning*, not MW *produced*. A coal unit at 40% load has its full rotor mass at synchronous speed and delivers nearly full inertia, but our proxy only sees the MW output. The proxy **understates** inertia whenever synchronous plant is backed off but still online. High-renewable midday periods will read more brittle than reality. Flag this in the UI and note it in API responses. This is an inherent limitation of the MW-output proxy — it can only be resolved with unit-commitment data we don't have.

### Implementation

**New service: `src/citylab/services/inertia.py`**

Pure derivation module — no new database tables. Computes inertia metrics from existing `GenerationOutput` rows on the fly.

Functions:
- `SYNC_H_MAP: dict[str, float]` — fuel_type → H constant mapping (H=0 omitted, unknown defaults to 0)
- `compute_inertia(generation_rows, contingency_preset="heywood") -> dict` — takes a list of `{fuel_type, output_mw}` dicts (same shape as `current_snapshot()` returns in `generation_mix`), returns `{sync_mw, total_mw, sync_fraction, e_proxy_mws, e_total_mws, rocof_hz_s, inertia_state, contingency_label, contingency_mw}`
- `inertia_timeseries(region, dt_from, dt_to, interval) -> list[dict]` — queries `GenerationOutput`, groups by interval, calls `compute_inertia` per interval, returns `[{timestamp, sync_mw, total_mw, sync_fraction, e_proxy_mws, rocof_hz_s, inertia_state}]`
- `current_inertia(region) -> dict` — convenience wrapper: latest interval snapshot

Configuration constants at module top:
- `REFERENCE_CONTINGENCY_MW = 650.0` (Heywood trip default, configurable)
- `CONTINGENCY_PRESETS = {"heywood": 650.0, "loy_yang_a": 560.0}` — selectable in API/UI
- `EXTERNAL_INERTIA_MWS = 35000.0` — mainland NEM inertia seen through interconnectors
- `SYSTEM_FREQUENCY_HZ = 50.0`
- Threshold tuples for state classification

**Extend `current_snapshot()` in `energy_query.py`:**

Add an `inertia` key to the snapshot dict by calling `compute_inertia()` on the generation mix already fetched. Zero additional DB queries.

**API endpoint: `routes/api_v1/energy.py`**

- `GET /api/v1/energy/inertia?region=VIC1&range=24h&interval=1h&contingency=heywood` — returns inertia timeseries
- `GET /api/v1/energy/inertia/current?region=VIC1&contingency=heywood` — returns current inertia snapshot

`contingency` param accepts preset keys (`heywood`, `loy_yang_a`) or a custom MW value.

Both use existing Bearer token auth.

**CLI: `cli_wrapper/commands_energy.py`**

- `cli-citylab energy inertia` — current inertia state (sync fraction, E_proxy, RoCoF, state label)
- `cli-citylab energy inertia --range 24h` — timeseries output

**Dashboard panel: `templates/energy/`**

New inertia panel on the energy dashboard:
- Inertia state indicator (Comfortable / Watch / Brittle) with colour coding matching the threshold bands
- Synchronous fraction gauge (percentage)
- RoCoF value with reference contingency label
- Sync MW vs total MW breakdown
- HTMX polling partial (same pattern as existing panels, 30s refresh)

**Inertia trend chart:**

Stacked area or line chart showing sync_fraction and/or E_proxy over time, alongside price and demand for correlation. Uses Chart.js (already vendored). Add as a tab or section within the energy dashboard.

### Backfill

No migration needed. The derivation runs against existing `GenerationOutput` rows. The `inertia_timeseries()` function works for any historical window where generation data exists. The API accepts arbitrary `dt_from`/`dt_to` or `range` params.

For the hackathon demo: query the full historical window we have (~3.5 days of VIC1 data) to show the inertia trend.

### Weather correlation and forecast

**Correlation layer:** The weather→renewable→inertia chain is: high wind/solar forecast → more inverter generation → lower sync fraction → higher RoCoF. Plot inertia timeseries alongside weather (wind speed, solar irradiance from existing BOM/Solcast data) to visually demonstrate the correlation.

**Forecast approach:** Use the Solcast solar forecast and BOM wind forecast (both already ingested) as leading indicators. When forecast renewable output is high and forecast demand is moderate, predicted sync fraction drops. This is a simple heuristic forecast, not ML:

- `forecast_inertia(region, hours_ahead) -> list[dict]` — for each forecast interval, estimate generation mix from price forecast + weather forecast, derive inertia metrics
- Display as a dashed overlay on the inertia trend chart

This is a stretch goal — the core derivation and backfill are the must-haves.

## Scope boundary

**In:** Sync/inverter classification, E_proxy derivation, RoCoF calculation, threshold bands, API endpoints, CLI command, dashboard panel, backfill over existing data, weather correlation display.

**Out:** Actual frequency data ingestion (no source available), unit-commitment data (would resolve MVA caveat but not available from OpenNEM), FCAS market data, ML-based forecasting, multi-region inertia (VIC1 only for hackathon).

**Deferred:** Grid-forming BESS detection (would reclassify some battery output as providing synthetic inertia — not distinguishable from current data). Hydro synchronous-condenser mode (spinning at 0 MW — invisible in output data). Dynamic external inertia reduction on interconnector-trip contingency (Heywood trip loses both import MW and a slice of the mainland inertia VIC was drawing through that link — current model treats external inertia as fixed, slightly understating RoCoF for interconnector contingencies).

## Done When

- [ ] `inertia.py` service computes sync_fraction, E_proxy, RoCoF, and inertia_state from generation mix data
- [ ] `compute_inertia()` handles all 14 fuel types with correct H mapping and unknown-defaults-to-zero
- [ ] `current_snapshot()` includes `inertia` key with all derived metrics
- [ ] API endpoints return inertia timeseries and current snapshot
- [ ] CLI `energy inertia` command prints current state and supports `--range`
- [ ] Dashboard panel shows inertia state, sync fraction, RoCoF, and sync/total MW
- [ ] Inertia trend chart renders over historical data with HTMX polling
- [ ] Backfill works: querying 24h+ of historical data returns correct inertia timeseries
- [ ] Weather data (wind, solar) is visually correlated with inertia on the dashboard
- [ ] Tests cover: compute_inertia with mixed fuel types, threshold boundary conditions, API response shape

## Demo Script

1. Open the energy dashboard at `https://smac.griffin-blenny.ts.net:5099/energy`
2. See the new **Grid Inertia** panel showing current state — e.g. "Watch — 42% synchronous, RoCoF 0.38 Hz/s if Heywood trips" (with mainland inertia buffering the number into a realistic band)
3. Toggle the contingency preset dropdown: Heywood (650 MW) vs Loy Yang A (560 MW) — RoCoF shifts, showing different risk profiles for interconnector vs generator loss
4. Click the inertia trend to see the 24h chart — notice inertia dips during midday solar peaks (high renewable, low sync fraction) and recovers in evening peaks (gas peakers online)
5. Overlay weather data — wind speed and solar irradiance track inversely with sync fraction
6. Point out the brittle window: "At 2pm yesterday, sync fraction hit 28% — if Heywood had tripped, RoCoF would have been 0.52 Hz/s, past the 0.5 watch threshold"
7. The key insight: **we derived grid fragility from data we already had — no new sensors, no new data sources, just physics applied to the generation mix**
