# Tasks: Energy Market Charts

Source PRD: docs/prds/ui/energy-market-charts-prd.md
Branch: feature/hack-energy-market-charts-prd

## Task List

- [x] 1. **Time-series query helpers** — In `src/citylab/services/energy_query.py`, add aggregation-aware time-series query functions: `price_timeseries`, `demand_timeseries`, and `generation_timeseries` (grouped by fuel type bucket). Each accepts `region`, `dt_from`, `dt_to`, and an `interval` of `5min`/`1h`/`1d`, returning ordered `{timestamp, value}` arrays (generation returns one series per fuel bucket). Aggregate at `1h`/`1d` via SQL date-truncation/averaging; cap series length under 10,000 points (NFR2). Reuse the same fuel bucketing as `_FUEL_BUCKETS` / `_bucket_for` in `routes/energy.py` so labels and grouping stay consistent (FR8).

- [x] 2. **Shared fuel colour mapping** — Promote the `_FUEL_BUCKETS` colour list (currently in `src/citylab/routes/energy.py`) to a single shared source the API and templates can both consume (e.g. a module-level constant in `energy_query.py` or a small `energy_palette.py`), so the static generation panel and the new stacked-area chart use identical colours (FR8, SC9). Update `routes/energy.py` to import from the shared source.

- [x] 3. **Chart data API endpoints** — In `src/citylab/routes/api_v1/energy.py`, add Bearer-authed endpoints returning chart-ready JSON time-series (FR7): `GET /api/v1/energy/timeseries/price`, `/timeseries/demand`, `/timeseries/generation`. Each accepts `range` (1h/6h/24h/7d/30d) and `interval` (5min/1h/1d) query params, resolves the time window, calls the new query helpers from Task 1, and returns `{region, range, interval, series:[...]}`. Generation returns labelled, colour-tagged series per fuel bucket. Return a clear empty-series payload when no rows exist (supports FR10).

- [x] 4. **Interval auto-selection + validation** — Add a small helper (route or service) mapping each `range` to its valid intervals and a sensible default (e.g. 1h→5min only; 6h→5min/1h default 5min; 24h→5min/1h default 1h; 7d→1h/1d default 1h; 30d→1h/1d default 1d) per FR5/NFR2. Endpoints from Task 3 use it to validate the requested interval and fall back to the default when omitted or invalid.

- [x] 5. **Charts partial template** — Create `templates/energy/partials/charts.html` rendering: a time-range selector bar (1h/6h/24h/7d/30d, default 24h, active-state highlight), an interval control (valid options per range), a full-width price+demand chart (~300px, demand on secondary y-axis per FR3), and a full-width generation stacked-area chart (~300px). Use the already-vendored Chart.js 4.4.1 (NFR3). JS fetches the Task 3 endpoints, builds datasets, enables hover crosshair + tooltips showing exact timestamp and value(s) — generation tooltip lists all fuel values plus total (FR6). Charts share the same x-axis window so correlation is immediate (FR1–FR4, FR6, UI Overview).

- [x] 6. **Empty-state handling** — In `charts.html` JS, when an endpoint returns no data for the selected range, render a clear "No data available for this range" message in place of a blank/erroring canvas (FR10).

- [x] 7. **Dashboard integration + route** — Add a `/energy/partials/charts` route in `src/citylab/routes/energy.py` rendering the charts partial, and include the charts section in `templates/energy/dashboard.html` below the existing snapshot panels (FR9). Verify the responsive layout (≥768px) does not break the existing dashboard (SC8).

- [x] 8. **Tests** — Add targeted tests (e.g. `tests/test_energy_charts_api.py`) covering the three new timeseries endpoints (Bearer auth required, range/interval params honoured, JSON shape, empty-state payload) and the query helpers' aggregation/interval behaviour. Use the existing fixture system (`app`, `client`, `db_session`); seed sample energy rows where needed. Run `pytest tests/` and confirm no regressions.

## Demo Script

(No explicit Demo Script section in the PRD — derived from Success Moment §1.3 and Success Criteria §3.)

1. Start the server (`./restart_server.sh`) and confirm `curl http://127.0.0.1:15099/health` is OK.
2. Log in and open `/energy`. The existing snapshot panels render unchanged, and a new charting section appears below them.
3. The default 24h range is active. The price+demand chart shows VIC1 spot price ($/MWh) over the last 24 hours with demand (MW) on a secondary axis; the generation stacked-area chart shows MW by fuel type with colours matching the static generation mix panel (SC1, SC2, SC3, SC9).
4. Observe the morning price peak, the midday solar ramp driving a price dip, and the evening demand surge correlated across both charts (Success Moment §1.3).
5. Switch the range to **7d** then **1h**; all charts update simultaneously and the interval control offers only valid intervals for the selected range (SC4, FR5).
6. Hover over any chart — a vertical crosshair and tooltip show the exact timestamp and value(s); the generation tooltip lists each fuel type plus the total (SC5, FR6).
7. Confirm charts show real database data, never synthetic placeholders (SC6), and that a range with no data shows "No data available for this range" rather than a blank canvas (FR10).
8. Verify the three API endpoints directly:
   `curl -H "Authorization: Bearer <token>" "http://127.0.0.1:15099/api/v1/energy/timeseries/price?range=24h&interval=1h"`
   returns `{region, range, interval, series:[{timestamp, value}, ...]}`; likewise `/timeseries/demand` and `/timeseries/generation` (generation returns one labelled, colour-tagged series per fuel bucket).
