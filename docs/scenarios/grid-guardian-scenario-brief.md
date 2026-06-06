# Grid Guardian — Scenario Workshop Brief

**Prepared by:** Ray (NEM Energy Market Analyst)
**Date:** 2026-06-06
**Purpose:** Working brief for scenario planning — foundation for Sam's pre-hackathon scenario workshop

---

## Context

Watt The Hack hackathon, Stone & Chalk Melbourne, 5–6 June 2026. Team is entered in **Track 2: Grid Guardian** — managing a city-level energy system: balancing supply and demand, managing storage and infrastructure, responding to weather and grid stress events.

Hackathon theme: *what happens in the home affects the grid, and what happens in the grid affects the home.*

**Platform state entering the hackathon:**
- Live VIC1 data ingestion: OpenNEM prices, demand, generation mix, interconnectors (5-min cron)
- BOM weather + Solcast solar forecasts
- NEM-wide scenario engine: multi-region ingestion, interconnector failure modelling, bulk generation loss via simplified merit-order
- Storage dispatch optimiser: BatteryAsset model, 6-rule dispatch engine with decision reasoning, forecast pre-positioning, SoC gauges
- Demand response stack: ControllableLoad model, 4-rule DR engine, curtailment waterfall
- Ray: live voice NEM analyst with CityLab instruments

---

## Likely Scenario Classes

These are the scenario types the Grid Guardian simulation is most likely to throw at teams, mapped to NEM mechanics.

### 1. Renewable Intermittency

**What happens:** Solar output drops sharply (cloud bank, rooftop PV cut-off) or wind falls in a corridor. Net load spikes faster than thermal can ramp.

**NEM mechanic:** Duck curve deepens. Ramping gas OCGTs fill the gap at $150–$300/MWh. If wind collapse is cross-regional, interconnector flows reverse.

**Home↔grid link:** Rooftop PV dropping simultaneously across a distribution zone can cause a step-change in net demand — the simulation may model this as a residential DER event, not just utility-scale generation loss.

**Platform levers:** Storage discharge (SoC permitting), demand response activation (defer EV charging, hot water), forecast pre-positioning (Solcast cloud opacity signal).

**Key decision:** When does the platform pre-position storage ahead of forecast solar dropout vs hold SoC for a later, larger event?

---

### 2. Interconnector Failure

**What happens:** A major interconnector trips — Basslink (VIC↔TAS, ~500 MW), Heywood (VIC↔SA, ~650 MW import), or VNI (VIC↔NSW).

**NEM mechanic:** The losing region loses its marginal import supply. Its price-setting generator shifts up the merit order. Verified in CityLab: Heywood failure moves SA1 from $103 → $310/MWh, VIC1 from $94 → $217/MWh. Asymmetry is correct — SA is a price-taker on Heywood, VIC is the exporter.

**Why the asymmetry matters for the demo:** SA spikes harder because it loses its import source; VIC spikes less because it just loses an export destination. This is a 20-second judge explanation that demonstrates real market understanding.

**Platform levers:** Scenario engine (already built — can model this directly), storage discharge into the price spike, demand response to reduce net load.

**Key decision:** Do you discharge storage into the price spike for revenue, or hold reserve for the frequency event that follows the trip?

---

### 3. Demand Spike — Weather-Driven

**What happens:** A cold snap (heating load) or unexpected heat event (cooling load) drives demand above forecast. Evening peak compounds it.

**NEM mechanic:** Demand forecasting error widens the supply gap at dispatch. AEMO may issue Lack of Reserve (LOR) notice. Prices spike as peakers are called.

**Home↔grid link:** Residential heating/cooling is the driver. This is where the demand response stack is most credible — deferring hot water and EV charging during a residential demand surge is exactly what DNSPs do via demand management programs.

**LOR escalation path:**
- LOR1: reserves adequate but tight — AEMO publishes notice
- LOR2: reserves inadequate — AEMO activates RERT
- LOR3: load shedding imminent — emergency protocols

**Platform levers:** Demand response waterfall (cheapest curtailment first), storage discharge, BOM temperature forecast as pre-positioning signal.

**Key decision:** At what LOR level does the platform activate demand response vs hold for storage dispatch?

---

### 4. Price Spike / Market Price Cap Event

**What happens:** Spot hits the Market Price Cap ($17,500/MWh) or approaches it. Cumulative Price Threshold (CPT) may trigger Administered Price Cap ($300/MWh) if sustained.

**NEM mechanic:** MPC events are typically short (1–3 dispatch intervals, 5–15 minutes) but extremely high-value for storage dispatch. The platform that discharges into the MPC interval maximises revenue. The platform that discharges one interval early at $300 leaves significant value on the table.

**Platform levers:** Price forecast signal (30-min predispatch in CityLab), storage discharge timing, FCAS participation logic (co-optimisation value is highest near MPC).

**Key decision:** How does the dispatch optimiser distinguish "discharge now at $300 heading to MPC" vs "hold — this is a false signal"?

---

### 5. Generation Outage — Bulk Loss

**What happens:** A large generator (coal unit, CCGT) trips unexpectedly. Instantaneous loss of 300–600 MW of dispatchable capacity. Frequency deviates.

**NEM mechanic:** NEMDE re-dispatches immediately. FCAS contingency markets activate (6-second, 60-second, 5-minute raise). The region's price spikes to whatever marginal generator can ramp fastest — often gas OCGT at $200–$500/MWh.

**Why FCAS matters here:** A BESS offering into contingency raise FCAS can earn $200–$500/MWh equivalent during a contingency event, often more than the energy arbitrage value in the same interval. The co-optimisation decision — split capacity between energy and FCAS — is the sophisticated play.

**Platform levers:** Storage dispatch optimiser (the reserve-hold override rule is key here), scenario engine (bulk generation loss modelling is already built).

**Key decision:** Does the platform hold storage reserve for FCAS co-optimisation, or discharge into the energy price spike? This is the non-obvious decision that demonstrates grid-state reasoning vs simple price reaction.

---

### 6. Compounding / Multi-Event Stress

**What happens:** Two or more stress events overlap — e.g., a generation outage during a hot afternoon demand peak, or an interconnector failure coinciding with low wind.

**NEM mechanic:** These are the scenarios AEMO's reliability standards are designed around (N-2 contingency). They are also the most dramatic and the most likely to separate teams that have decision logic from teams that just have dashboards.

**Platform levers:** All of the above, plus the scenario engine's ability to model concurrent failures.

**Key decision:** How does the platform triage competing response options when multiple levers are needed simultaneously?

---

## Dispatch Rule Thresholds — Calibration Notes

Current CityLab VIC1 data (last ~3.5 days as of 2026-06-06):
- Median: $13/MWh (unusually depressed — mild winter, high wind)
- p90: $71, p95: $83, max: $113
- 28% negative intervals (midday solar oversupply)
- Zero intervals above $200 in this window

**This week's data is not representative for threshold calibration.** Use NEM-typical VIC thresholds:

| Rule | Threshold | Rationale |
|---|---|---|
| Discharge trigger | ≥$150/MWh | Gas peaker territory in VIC evening peaks |
| High-value discharge | ≥$300/MWh | Significant stress event |
| Charge trigger | ≤$30/MWh | Renewable surplus window |
| Reserve hold override | Interconnector import >85% capacity | Basslink/Heywood stress |

---

## Open Questions for Sam (from team formation)

Three questions that shape the dispatch optimiser adapter:

1. **Real NEM vs synthetic market engine** — if the simulation uses its own price engine, the dispatch optimiser needs to consume simulation-provided price signals instead of CityLab forecasts. Architecture is adapter-agnostic; just a different data source.
2. **Team-defined vs assigned asset portfolio** — if assets are assigned, `BatteryAsset` model values come from simulation input rather than config. The model handles both; just a load path difference.
3. **Scoring weights** — cost efficiency, reliability, speed of response, or composite? Scoring weights determine which platform lever to prioritise when trade-offs arise (e.g., discharge for revenue vs hold for reliability).

---

## Workshop Prompts

Starting points for Sam's scenario workshop with Ray:

- "Which scenario is most likely to catch teams off-guard — and what would the platform need to do that they won't?"
- "What's the highest-value storage dispatch decision in a Basslink failure scenario, and how should the optimiser's reserve-hold logic respond?"
- "If the simulation runs LOR2 during a wind dropout, what's the platform's optimal response sequence?"
- "How should the demand response waterfall interact with storage dispatch when both levers are available simultaneously?"
- "What does FCAS co-optimisation look like in a bulk generation loss event, and can we narrate it convincingly without live FCAS data?"
