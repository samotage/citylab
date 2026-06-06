# citEther — Q&A Data Cheat Sheet

Quick-reference for Sam when judges probe after the pitch. Organised by likely question area, headline answer first, backing data below.

---

## 1. Follow Me Power — How Does Settlement Actually Work?

**Headline:** Virtual settlement, not physical transfer. The grid is the wire, citEther is the accounting layer.

- Your home solar exports to the grid at your local node. citEther logs the credit.
- At a remote location (job site, parent's flat, EV charger), you draw from the grid. citEther logs the debit.
- citEther nets them out across your account. You pay/earn the difference based on node rates.
- No physical electron tracking — financial settlement against metered data at both endpoints.
- Analogous to how telcos handle roaming: you don't carry your signal, you carry your account.

**If they ask "is this legal under NEM rules?":**
- Current NEM retail framework is meter-based. citEther operates within the retail framework by partnering with a licensed retailer (the "retailer-of-record" model) — the retailer handles market settlement, citEther handles consumer-facing accounting and dispatch optimisation.
- AEMC's Consumer Energy Resources rule changes (2025) are opening flexibility for behind-the-meter aggregation and multi-site settlement.
- The regulatory path is real but requires a retail partner — we're not proposing to bypass the market.

---

## 2. Competitive Whitespace — Why Hasn't Anyone Done This?

**Headline:** Every current player optimises at the meter. No Australian platform offers location-independent consumer energy settlement.

| Player | What they do | Why it's not Follow Me Power |
|--------|-------------|------|
| AGL/Origin VPPs | Dispatch home batteries for grid services | Single meter, retailer-controlled |
| Wholesale pass-through retailers | Wholesale price exposure to consumers | Single meter, consumer watches prices |
| Power Ledger | Peer-to-peer trading | Same distribution feeder only |
| Enosi | Community energy matching | Same feeder, retrospective matching |
| ShineHub / Reposit | Home energy management | Single site optimisation |
| Tesla Energy | Powerwall + Virtual Power Plant | Tesla hardware only, single site |

**Why it hasn't been done:** Settlement across multiple meters requires (a) real-time metering at both endpoints, (b) a coordination layer that maps node-level value, and (c) a retail partnership for market settlement. Smart meters are now standard (Victorian AMI rollout complete). The coordination layer is what citEther builds. The retail partner is the go-to-market strategy.

---

## 3. Follow Me Power Example Data

**Tradie on a job site:**
- Home solar exports at ~8c/kWh FiT
- Diesel generator on site costs $0.40-0.60/kWh
- citEther settlement: home credits offset site consumption at effective cost of ~10-15c/kWh (home generation cost + citEther margin)
- Net saving: $15-25/day on a typical construction site
- 2.4M+ sole traders in Australia, 1.1M in construction/trades

**Aged care / parent's flat:**
- Average electricity bill for a 1-2 person household: $1,200-1,800/yr
- Typical 6.6 kW rooftop system generates 24-28 kWh/day in Melbourne
- Average household self-consumption: 30-40%. Remaining 60-70% exported at 8c FiT
- Redirecting 5-10 kWh/day to parent's flat offsets $500-900/yr of their bill
- Emotional pitch: "I power my mum's flat from my roof"

**EV road trip:**
- DC fast charger cost: $0.50-0.80/kWh
- Home solar effective generation cost: $0.05-0.08/kWh (system cost amortised over 10 years)
- Follow Me Power offset: home solar credits reduce net EV charging cost to ~$0.10-0.15/kWh
- A Melbourne-to-Geelong return trip (~150 km): ~25 kWh consumed. Cost at fast charger: $15-20. With Follow Me Power: $2.50-3.75

**Shift worker (nurse at hospital):**
- EV parked for 12-hour shift at a constrained hospital node
- V2G discharge at high-demand times: $0.30-0.50/kWh grid value at constrained nodes
- Typical V2G discharge over a shift: 15-25 kWh
- Earnings: $40-60 per shift, varying by node constraint level
- Nurse works 3-4 shifts/week: $120-240/week, $500-1,000/month potential

**Kids at uni:**
- Student apartment consumption: ~5-8 kWh/day
- Parents' excess solar covers this entirely
- Annual offset: $600-1,000 off the student's power bill

---

## 4. NEM Fleet Stats

- **Solar PV:** 4.3M systems, 28.3 GW total capacity. Largest distributed generation fleet in the NEM.
- **Batteries:** 450K+ home batteries, 11.2 GWh total storage.
- **EVs:** 500K+ on Australian roads. V2G-capable models growing (BYD Atto 3, Nissan Leaf, MG ZS).
- **HVAC:** 18M+ units nationally. Largest controllable load class in residential.
- **Smart meters:** Victorian AMI rollout complete — universal smart metering. Other states catching up.

---

## 5. Curtailment & Negative Pricing

- **7 TWh** curtailed in 2025 (+60% year-on-year)
- **31%** of NEM trading intervals had negative prices in Q4 2025
- SA worst at **48.4%** negative intervals, VIC at **43.1%**
- Curtailment is wasted clean energy — solar being told to switch off because the grid can't absorb it
- Follow Me Power helps: instead of curtailing, redirect excess to remote consumption points where demand exists

**Do NOT use the $2.1B figure.** It implies ~$300/MWh average — indefensible for expert judges. Use 7 TWh and let them do the maths. At average wholesale (~$70/MWh), the value is ~$490M. Say "$500M+ in wasted clean energy" if a dollar figure is needed.

---

## 6. Auto-Arb Arbitrage Margins

- **Off-peak buy:** ~$30-50/MWh ($0.03-0.05/kWh)
- **Peak sell:** ~$150-300/MWh ($0.15-0.30/kWh)
- **Battery round-trip efficiency:** 85-90%
- **Net margin per cycle:** $80-200/MWh
- **Daily cycles:** 1-2 in normal conditions, 2-4 during volatile periods
- **Household earnings:** $3-8/day typical, $15-30/day during high volatility events
- **Annual range:** $1,100-2,900/yr for a 10 kWh battery under active arbitrage
- **Guardrail cost:** comfort guardrails (min SoC, HVAC override) reduce theoretical maximum by ~15-20% but eliminate the catastrophic loss scenario (one hot day wiping a year's savings)

---

## 7. Social Norming Evidence

- **OPower trials:** 2-4% sustained reduction in residential energy consumption through peer comparison alone
- **Mechanism:** descriptive norms ("your neighbours use X") + injunctive norms ("efficient households do Y")
- **Boomerang effect warning:** high performers shown they're above average may reduce effort. Solution: pair descriptive norm with injunctive approval (smiley face for good performers — the OPower design)
- **citEther application:** same mechanism applied to grid participation, not just conservation. "Your street responded to 87% of grid events. You responded to 62%. Top performers earned $52 this month."
- **Why judges care:** social norming is the cheapest customer acquisition and retention lever in energy. Zero marginal cost, self-sustaining behavioural loop.

---

## 8. Pod & Distribution Loss Economics

- **NEM transmission losses:** 5-10% average
- **Suburban distribution feeder losses:** 5-7%
- **Network charges:** 40-50% of a retail electricity bill
- **Pod benefit:** energy shared within the pod avoids both transmission losses and the most expensive network charge layer
- **DNSP value:** a pod that self-balances reduces net demand on the local transformer. Fewer voltage excursions, fewer hosting capacity violations, deferred infrastructure spend.
- **Community battery scale:** single 500 kWh battery is cheaper per kWh than fifty 10 kWh home batteries. Better thermal management, lower install cost per unit, optimal DNSP placement at substation.

---

## 9. Inverter Compliance & Direct-to-Endpoint

- **40%** of installed inverters non-compliant with AS/NZS 4777.2
- Can't respond to remote dispatch signals through standard grid protocols
- citEther bypasses this via direct local protocols: **Modbus TCP, MQTT, local API**
- Brand-agnostic: works with Fronius, Enphase, GoodWe, Sigenergy, Sungrow, SMA, Tesla
- Local-first architecture: runs on the home network, keeps working offline, no forced cloud dependency
- **Why this matters:** VPPs that rely on cloud APIs and standards compliance miss 40% of the fleet. citEther talks to the hardware directly.

---

## 10. Data Centre Load & Grid Stress

- NEM data centre consumption: **3.9 TWh** in FY25
- Projected: **~12 TWh by 2030** (6% of total NEM demand)
- Driven by AI compute, cloud expansion, hyperscaler investment (Microsoft, Google, AWS all building in Australia)
- Increases grid stress and the value of flexible distributed capacity
- Follow Me Power relevance: more demand = more value for coordinated consumer DER that can respond to location-specific stress

---

## 11. Network Charges — The Honest Business Case

**Follow Me Power uses third-party network infrastructure. Full network charges apply.**

**Cost stack for Follow Me Power at a remote location:**

| Component | Cost ($/kWh) | Notes |
|-----------|-------------|-------|
| Home solar generation | $0.05-0.08 | System cost amortised over 10 years |
| Distribution (DNSP/DUOS) | $0.04-0.07 | Local poles-and-wires |
| Transmission (TNSP/TUOS) | $0.02-0.04 | High-voltage backbone |
| Market fees (AEMO) | $0.005-0.01 | Market operation, settlement |
| citEther margin | $0.02-0.03 | Platform fee |
| **Total delivered cost** | **$0.15-0.23** | |

**Vs alternatives at the remote location:**

| Alternative | Cost ($/kWh) |
|------------|-------------|
| Retail electricity | $0.25-0.35 |
| Diesel generator (job site) | $0.40-0.60 |
| DC fast charger (EV) | $0.50-0.80 |

**The margin is real even with full network fees.** The honest pitch: "We're not bypassing the grid — we're using it. But when your generation cost is five cents and retail is thirty-five, the margin is there even after the grid takes its cut."

**Pod advantage:** energy shared within the same distribution transformer zone uses minimal network infrastructure. TUOS is avoided entirely (no transmission), DUOS is minimal (same transformer). This is why Pods have stronger economics than cross-city Follow Me Power — the network fees shrink when energy stays local.

**Regulatory tailwind:** AEMC's DER access and pricing reforms are actively discussing reduced network charges for local energy exchange. If enacted, Pod economics improve further.

---

## 12. Revenue Model Detail

**Three streams:**

1. **Savings-share (primary):** citEther takes a margin on the arbitrage delta. Consumer always nets positive. Uber margin model — we earn when you earn.
2. **DNSP capacity payments:** distribution networks pay for coordinated demand flexibility. Each kW of managed load = a transformer upgrade deferred. B2B, scales with fleet size.
3. **Grid services:** FCAS (frequency control), demand management, coordinated curtailment management. Aggregated fleet provides services individual households can't offer alone.

**Why the grid pays:** coordinated DER is cheaper than building gas peakers ($2B+ per new facility). A fleet of 100,000 managed batteries provides more flexible capacity than a single peaking plant, at a fraction of the cost, deployable in minutes not years.

---

## 12. Regulatory & Market Context

- **AEMC Consumer Energy Resources rule changes (2025):** opening flexibility for DER aggregation, behind-the-meter coordination, and potentially multi-site settlement
- **AEMO Integrated System Plan:** explicitly calls for consumer DER as a grid resource
- **Victorian AMI rollout:** complete — universal smart metering enables the data layer Follow Me Power needs
- **Retailer-of-record model:** citEther doesn't need a retail licence to start. Partner with a licensed retailer for market settlement, handle consumer-facing coordination and value delivery.
- **Feed-in tariff decline:** Ergon export went 15c -> 12c -> 8c year-on-year. Makes self-consumption and Follow Me Power more valuable — the alternative (export for 8c) is increasingly unattractive.

---

## 13. Follow Me Power — Extended Value Modes

**Donate to charity:**
- ~60,000 registered charities in Australia. Community centres, food banks, homeless shelters, aged care facilities — all pay retail for electricity.
- Consumer donates excess solar credits to a registered charity through citEther. Charity's power bill drops. Consumer receives a tax-deductible donation receipt.
- Retention lever: emotionally sticky. People don't cancel a platform that powers their local shelter.
- Pitch line: "Your roof powers the local food bank."

**Businesses bid on community energy:**
- Local businesses (cafe, gym, small manufacturer) bid for energy from their neighbourhood Pod or community battery.
- Price band: $0.15-0.20/kWh — less than retail ($0.25-0.35/kWh), more than FiT (8c/kWh). Both sides win.
- Creates a local energy marketplace. The Pod becomes a supplier, not just a self-consumption unit.
- DNSP benefit: energy stays within the distribution transformer zone. Zero network transport cost.

**Sell directly to the grid (AEMO):**
- Aggregated community fleet sells into the wholesale market or provides grid services.
- FCAS (frequency control) market pays $100-300/MWh during grid stress events — far above retail.
- AEMO's RERT (Reliability and Emergency Reserve Trader) pays for emergency capacity.
- A fleet of 100,000 managed batteries = a virtual peaking plant. More flexible than gas ($2B+ to build), deployable in milliseconds not minutes.
- The framing: consumers aren't just saving money, they're becoming grid infrastructure.

**Six destinations, one account:** yourself (anywhere), your family, your community, a charity, a local business, or the grid itself.

---

## Quick-Draw Responses

**"How is this different from peer-to-peer trading?"**
P2P (Power Ledger, Enosi) matches buyers and sellers on the same distribution feeder. Follow Me Power is location-agnostic — your energy follows you to any grid connection point in the country, not just your neighbours.

**"What about network charges?"**
Network charges still apply at both endpoints. The value proposition isn't avoiding network charges — it's that the effective cost of your remote consumption is your home generation cost (~5-8c/kWh) plus citEther's margin, vs retail rates ($0.25-0.35/kWh) or diesel ($0.40-0.60/kWh).

**"Do you need a retail licence?"**
No. Retailer-of-record partnership model. The retailer handles NEM settlement. citEther handles consumer coordination, dispatch optimisation, and value accounting.

**"What's the TAM?"**
4.3M solar households today. Add 2.4M sole traders with home solar and remote work sites. Add 500K+ EV owners. Intersecting segments, but the addressable base is 2-3M households within 3 years as battery and EV adoption grows.

**"How do you handle gaming/fraud?"**
Both endpoints are smart-metered. citEther reconciles against metered data — you can't claim credits you didn't generate or consumption you didn't use. The smart meter is the source of truth.
