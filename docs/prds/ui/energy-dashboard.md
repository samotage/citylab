---
validation:
  status: valid
  validated_at: '2026-06-03T07:42:07+10:00'
---

# Energy Market Dashboard

## Problem

The data ingestion pipelines deliver a comprehensive picture of the Victorian energy market — prices, generation, interconnectors, weather, solar forecasts — but it's only accessible via CLI and API. For the hackathon demo and for human operators supervising agent decisions, we need a visual dashboard that presents the current market state at a glance. An operator should be able to open the browser and immediately understand what's happening in the Victorian energy market without running CLI commands.

This PRD depends on the three data ingestion PRDs being built first. It consumes the data they produce.

## Approach

### Dashboard Layout

Single-page dashboard at `/energy` (login required), extending the existing `base.html` layout. The page is a real-time market overview, not a deep analytics tool — it shows current state and recent trends.

**Top strip — Market Snapshot:**
- Current VIC1 spot price (large, prominent) with colour coding: green (<$50), amber ($50–$150), red (>$150), flashing red (>$300 — price spike)
- Price trend arrow (up/down/flat vs last hour)
- Current total demand (MW)
- Next forecast price and direction

**Generation Mix Panel:**
- Stacked bar or donut chart showing current generation by fuel type
- Colour-coded: brown coal (brown), gas (orange), solar (yellow), wind (teal), hydro (blue), battery discharge (purple), battery charge (purple outline)
- Fuel type aggregation from data model to display: gas_ccgt + gas_ocgt + gas_recip + gas_steam → "Gas"; solar_utility + solar_rooftop → "Solar"; battery_charging + battery_discharging shown separately; all other fuel types map 1:1
- Total capacity vs current output as a utilisation indicator
- Updates every 5 minutes with dispatch data

**Interconnector Panel:**
- Visual representation of the 5 corridors: Basslink, Heywood, Murraylink, VNI, VNI West
- Each shows: flow direction (arrow), flow volume (MW), capacity utilisation (%)
- Colour: green (normal), amber (>75% capacity), red (constrained/at limit)
- Net import/export summary for Victoria

**Weather & Renewable Outlook Panel:**
- Wind outlook: current and forecast wind speeds across SA and Vic wind corridors — strong/moderate/light indicator
- Solar outlook: current and forecast GHI across Vic solar regions — sunny/partly cloudy/overcast indicator
- Rain outlook: rainfall forecast for Tas and Snowy hydro catchments — dry/light/moderate/heavy
- Temperature: Melbourne current and forecast — contextualises demand

**Price Forecast Strip:**
- Timeline showing forward price curve from AEMO pre-dispatch
- Horizon: next 12–24 hours
- Overlay actual prices as they arrive to show forecast accuracy

**Data Source Health:**
- Small status strip at bottom: OpenNEM ✓/✗, BOM ✓/✗, Solcast ✓/✗
- Last fetch time for each source
- Visual indicator if any source is stale (last fetch > 2x expected interval)

### Technical Approach

- Server-rendered HTML with Jinja2 templates (consistent with bootstrap architecture)
- HTMX for auto-refresh — each panel polls its data endpoint on an interval matching the data refresh rate (5min for market data, 30min for weather, 1hr for solar)
- Charts via Chart.js (lightweight, no build step, CDN or vendored)
- No JavaScript framework — vanilla JS + HTMX + Chart.js keeps it simple
- All data pulled from the existing agent API endpoints (same endpoints agents use)
- Responsive but desktop-first — hackathon demo will be on a laptop/projector

### New Routes

- `GET /energy` — main dashboard page (login required)
- `GET /energy/partials/price` — HTMX partial: price snapshot
- `GET /energy/partials/generation` — HTMX partial: generation mix chart
- `GET /energy/partials/interconnectors` — HTMX partial: interconnector flows
- `GET /energy/partials/weather` — HTMX partial: weather/renewable outlook
- `GET /energy/partials/forecast` — HTMX partial: price forecast timeline
- `GET /energy/partials/sources` — HTMX partial: data source health strip

### Templates

- `templates/energy/dashboard.html` — main layout, extends base.html, contains panel grid
- `templates/energy/partials/` — one partial template per panel (price, generation, interconnectors, weather, forecast, sources)

### Static Assets

- Chart.js vendored to `static/vendor/chart.min.js`
- Dashboard-specific CSS in `static/css/src/input.css` (Tailwind custom layer) — compiled to main.css
- No additional JS build tooling

## Done When

- [ ] `/energy` renders the dashboard with all panels when logged in
- [ ] Price snapshot shows current VIC1 spot price with colour coding and trend
- [ ] Generation mix chart shows current output by fuel type, including battery
- [ ] Interconnector panel shows all 5 corridors with flow direction, volume, and utilisation
- [ ] Weather panel shows wind, solar, rain, and temperature outlook
- [ ] Price forecast strip shows forward curve for next 12–24 hours
- [ ] Data source health strip shows status and freshness for all three sources
- [ ] HTMX auto-refresh updates panels without full page reload
- [ ] Dashboard works with real data from the ingestion pipelines
- [ ] Page loads in under 3 seconds, panels refresh without visible flicker
- [ ] Navigation: sidebar link to Energy Dashboard from base template

## Demo Script

1. Log in to CityLab at `http://127.0.0.1:5099`
2. Click "Energy" in the sidebar → see the full market dashboard
3. Current VIC1 spot price displayed prominently — green at $45/MWh
4. Generation mix shows brown coal baseload, wind contributing 20%, solar at midday peak, gas filling gaps
5. Interconnectors: Basslink importing from Tas, Heywood importing from SA, VNI exporting to NSW — arrows and flow volumes visible
6. Weather panel: strong wind in SA corridors, sunny across Vic solar regions, rain forecast for Tas catchments
7. Price forecast: pre-dispatch shows prices softening over next 6 hours as solar ramps up
8. Data source health: all three green, last fetch within expected intervals
9. Wait 5 minutes — watch the price and generation panels auto-update via HTMX
10. The key proof: a human and an agent see the same market picture — the dashboard visualises exactly what `cli-citylab energy summary` + `weather summary` + `solar summary` return
