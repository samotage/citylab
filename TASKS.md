# Tasks: CLI Completeness for Ray — Timeseries Commands + Market Intelligence Solar

Source PRD: docs/prds/data/cli-completeness-for-ray-prd.md
Branch: feature/hack-cli-completeness-for-ray-prd

## Task List

- [x] 1. Inspect existing patterns: energy CLI commands in `src/citylab/cli_wrapper/commands_energy.py`, the timeseries API endpoints in `src/citylab/routes/api_v1/energy.py`, and `energy_query.RANGE_INTERVALS`. Confirm endpoint paths, accepted query params (region/range/interval), and return shape before writing CLI commands.
- [x] 2. Add `cli-citylab energy timeseries-price` command in `commands_energy.py` — options `--region` (default VIC1), `--range` (default 24h), `--interval` (optional). Hits `/api/v1/energy/timeseries/price` via `APIClient.get()` and prints the JSON response. Mirror the existing energy command pattern.
- [x] 3. Add `cli-citylab energy timeseries-demand` command — same options, hits `/api/v1/energy/timeseries/demand`.
- [x] 4. Add `cli-citylab energy timeseries-generation` command — same options, hits `/api/v1/energy/timeseries/generation`.
- [x] 5. Part B: Wire solar into `market_intelligence()` in `src/citylab/routes/api_v1/data.py` (~line 127). Import `solar_query as sq`, build `solar = {"summary": sq.summary(), "outlook": sq.outlook()}` inside a try/except (mirror the weather block), and replace the hardcoded `"solar": None`.
- [x] 6. Part C: Update `docs/help/cli-citylab.md` — add the 3 timeseries commands as full CLI entries in the energy section, and update the `data market-intelligence` return shape to show `solar: {summary, outlook}` instead of `null`.
- [x] 7. Add test coverage for the 3 new CLI commands (invocation doesn't crash, options accepted) following existing CLI wrapper test patterns under `tests/`. Confirm market-intelligence solar wiring is covered.
- [x] 8. Run targeted tests (energy CLI + data market-intelligence) and confirm no regressions.

## Demo Script

1. Open a terminal connected to the CityLab server
2. Run `cli-citylab energy timeseries-price --range 24h` — see JSON with price series over 24 hours, interval-bucketed
3. Run `cli-citylab energy timeseries-demand --range 7d --interval 1d` — see daily demand aggregates for the week
4. Run `cli-citylab data market-intelligence --region VIC1` — see the combined response with energy, weather, AND solar data (no more `null`)
5. Start Ray: `cli-citylab agent start` — ask "How have prices moved today?" — Ray uses the timeseries data to answer with trend analysis, not just a snapshot
6. Ask Ray "Give me the full market picture" — the market-intelligence response now includes solar irradiance alongside energy and weather
