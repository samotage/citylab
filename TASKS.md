# Tasks: Energy Market Dashboard

Source PRD: docs/prds/ui/energy-dashboard.md
Branch: feature/hack-energy-dashboard

A single-page, login-required dashboard at `/energy` that visualises the current
Victorian energy market state over the three ingestion pipelines now on master
(OpenNEM energy, BOM weather, Solcast solar). Server-rendered Jinja2 + HTMX
auto-refresh + Chart.js, consistent with the existing `base.html` / Tailwind
(dark) architecture.

## Architecture notes (for the build worker)

- **Routes:** new `energy_bp` blueprint in `src/citylab/routes/energy.py`, registered
  in `src/citylab/__init__.py` alongside `main_bp`. All routes `@login_required`
  (session auth, like `main.index`) — NOT the API-token auth used by `api_v1`.
- **Data:** the dashboard routes consume the existing query SERVICES directly
  (`energy_query`, `weather_query`, `solar_query`) — same data the agent API
  serves, but in-process (no token, no HTTP round-trip). Reuse:
  - `energy_query.current_snapshot("VIC1")` → price, demand, generation_mix,
    battery_state, interconnectors, nearest_forecast
  - `energy_query.query_prices` (for trend vs last hour), `query_forecasts`
  - `weather_query.summary()` / `weather_query.outlook("wind"|"rain"|"temperature")`
  - `solar_query.summary()`
  - `energy_query.latest_fetch_timestamp()` and the `DataSource` model
    (`name`, `last_fetch_at`, `last_fetch_status`) for the source-health strip.
- **Fuel aggregation:** map generation_mix fuel_types in the route/template:
  gas_ccgt+gas_ocgt+gas_recip+gas_steam→"Gas"; solar_utility+solar_rooftop→
  "Solar"; battery_charging & battery_discharging shown separately; all others 1:1.
- **CSS:** Tailwind v3. `static/css/main.css` is COMPILED from
  `static/css/src/input.css` — never edit main.css directly. Add any custom
  classes (price colour states, panel styling) to `input.css` `@layer components`,
  then rebuild with `npx tailwindcss -i static/css/src/input.css -o static/css/main.css`.
- **Chart.js:** must be vendored to `static/vendor/chart.min.js` (not yet present).
  Load it in the dashboard page `{% block head %}`. HTMX is already vendored.
- **HTMX refresh:** each panel is a `hx-get` partial with `hx-trigger="load, every Ns"`
  (5min market, 30min weather, 1hr solar — use shorter intervals if helpful for demo).
  Charts re-init on swap via inline `<script>` in the partial, or an `htmx:afterSwap` hook.
- **Nav:** add an "Energy" sidebar link in `templates/base.html`.

## Task List

- [x] 1. Create `energy_bp` blueprint (`src/citylab/routes/energy.py`) with `GET /energy` stub returning a placeholder template; register it in `src/citylab/__init__.py`; add the "Energy" sidebar link in `base.html`. Verify `/energy` loads when logged in.
- [x] 2. Scaffold `templates/energy/dashboard.html` extending `base.html`: page title, panel grid layout (top snapshot strip, then 2-col panel grid, then forecast strip, then source-health strip), each panel an empty container wired with its `hx-get` partial endpoint + `hx-trigger`. Add `{% block head %}` to load `static/vendor/chart.min.js`.
- [x] 3. Vendor Chart.js to `static/vendor/chart.min.js` (download the UMD build of Chart.js v4, e.g. `chart.umd.min.js`). Confirm it is served and the page's head loads it without 404.
- [x] 4. Price snapshot: route `GET /energy/partials/price` + `templates/energy/partials/price.html`. Build a view-model from `current_snapshot` + recent prices: current VIC1 spot price (large), colour state (green <$50, amber $50–150, red >$150, flashing red >$300), trend arrow vs ~1h ago, current demand MW, next forecast price + direction. Add the price colour-state classes to `input.css`.
- [x] 5. Generation mix: route `GET /energy/partials/generation` + partial template. Aggregate `generation_mix` per the fuel mapping into labelled+coloured buckets (brown coal=brown, gas=orange, solar=yellow, wind=teal, hydro=blue, battery discharge=purple, battery charge=purple outline). Render a Chart.js donut/stacked bar with the brand colours; show total output and a utilisation indicator. Re-init chart on HTMX swap.
- [x] 6. Interconnector panel: route `GET /energy/partials/interconnectors` + partial. For each of the 5 corridors (Basslink, Heywood, Murraylink, VNI, VNI West) show flow direction arrow, flow volume MW, % capacity utilisation, colour (green normal / amber >75% / red constrained). Compute and show Victoria net import/export summary.
- [x] 7. Weather & renewable outlook: route `GET /energy/partials/weather` + partial. From `weather_query.outlook("wind"/"rain"/"temperature")` and `solar_query.summary()` derive: wind strong/moderate/light, solar sunny/partly cloudy/overcast, rain dry/light/moderate/heavy (Tas+Snowy catchments), Melbourne temp current+forecast. Show as labelled indicator chips.
- [x] 8. Price forecast strip: route `GET /energy/partials/forecast` + partial. From `query_forecasts("VIC1")` build the forward price curve for the next 12–24h as a Chart.js line; overlay recent actual prices to show forecast accuracy. Re-init chart on HTMX swap.
- [x] 9. Data source health strip: route `GET /energy/partials/sources` + partial. From the `DataSource` model show OpenNEM / BOM / Solcast status (✓/✗), last fetch time (display in local/clear format), and a stale indicator when `last_fetch_at` is older than 2x the expected interval.
- [x] 10. Styling & polish: ensure panels are visually consistent with the dark theme (reuse `.card`), tune the panel grid for desktop-first responsiveness, finalise the flashing-red price-spike animation, verify no flicker on HTMX swaps. Rebuild Tailwind and spot-check custom selectors survive the build.
- [x] 11. Real-time refresh & full-page verification: confirm every panel auto-refreshes on its interval without full-page reload, the page loads in under 3s, and the whole dashboard renders end-to-end with seeded/real pipeline data while logged in.

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
