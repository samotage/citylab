# NEM-Wide Data Ingestion + Scenario Analysis

## Problem

CityLab currently ingests data for VIC1 only. The hackathon scenarios may require analysing price/supply impacts across the entire NEM (NSW1, QLD1, SA1, TAS1, VIC1) and modelling contingencies — interconnector failures (e.g. Heywood drops to zero) or bulk generation loss (e.g. 500MW of brown coal offline in VIC1). Without multi-region data and a scenario engine, we can't answer "what happens to SA prices if the VIC interconnector fails?"

## Approach

### Phase 1 — Multi-Region Ingestion

Parameterise the OpenNEM fetcher to ingest all five NEM regions instead of hardcoded VIC1.

- Replace `REGION = "VIC1"` constant with a config-driven list of regions: `["NSW1", "QLD1", "SA1", "TAS1", "VIC1"]`
- One fetcher instance per region, each registered as its own `DataSource` (e.g. `opennem_nsw1`, `opennem_qld1`, etc.)
- Expand the `INTERCONNECTORS` list to include all NEM interconnectors (QNI, Directlink, Terranora for QLD-NSW; etc.)
- The data model already supports multi-region (all tables have a `region` column) — no migration needed
- Weather/solar location seeding expanded to cover key sites per region (BOM stations near demand centres, Solcast sites per solar zone)

### Phase 2 — Scenario Analysis Engine

A service layer that applies hypothetical modifications to real data and projects impacts.

**Scenario types:**
1. **Interconnector failure** — set a named interconnector's capacity to zero (or reduced value) and recompute regional supply balance. Stranded generation in the exporting region, supply deficit in the importing region, price impact derived from merit-order position of marginal replacement generation.
2. **Bulk generation loss** — remove N MW of a specified fuel type from a region. Remaining demand met by next fuel types in merit order → price impact.

**Implementation:**
- `src/citylab/services/scenario.py` — ScenarioEngine class
- Input: scenario definition (type, parameters, time window)
- Method: take actual generation/demand/flow snapshot for the time window, apply the modification, rebalance using a simplified merit-order model (stack available generation by fuel-type cost, fill demand from cheapest up)
- Output: modified price estimate per region, supply surplus/deficit per region, flow redistribution across interconnectors
- No new database tables — scenarios are computed on the fly from stored actuals
- API endpoint: `POST /api/v1/energy/scenario` accepting scenario definition JSON, returning projected state

### Merit-Order Simplification

For hackathon speed, use a static fuel-cost ladder (brown coal < black coal < gas CCGT < gas OCGT < hydro < distillate) rather than actual bid stacks. This gives directionally correct price signals without needing full AEMO bid data parsing.

### Dashboard Integration

- Region selector on `/energy` dashboard (dropdown, default VIC1)
- Scenario panel: pick scenario type, set parameters, see projected vs actual prices side-by-side
- Interconnector map showing flow directions with ability to "break" a link and see impact

## Done When

- [ ] All five NEM regions ingesting price, demand, generation, and interconnector data on the 5-minute cron
- [ ] `cli-citylab energy summary --region NSW1` (and QLD1, SA1, TAS1) returns current data
- [ ] Interconnector list covers all NEM corridors (not just VIC-touching)
- [ ] `POST /api/v1/energy/scenario` with interconnector-failure payload returns price/supply projections for affected regions
- [ ] `POST /api/v1/energy/scenario` with generation-loss payload returns adjusted prices
- [ ] Dashboard region selector works — switching region shows that region's live data
- [ ] Dashboard scenario panel demonstrates at least one "Heywood offline" scenario with visible price impact

## Demo Script

1. Open the app at the energy dashboard
2. Show the region selector — switch from VIC1 to SA1, show live SA data
3. Navigate to the scenario panel
4. Select "Interconnector Failure" → pick "Heywood (VIC1↔SA1)" → set capacity to 0
5. Click "Run Scenario" — show the projected price spike in SA1 (isolated from VIC supply) and the surplus/price drop in VIC1
6. Switch to "Generation Loss" → pick VIC1 → brown coal → 1400MW (≈ one Loy Yang unit equivalent)
7. Show the projected VIC1 price increase as gas fills the gap
8. The key insight: "We can model real contingencies against live market data and see cascading price impacts across the interconnected grid in seconds"
