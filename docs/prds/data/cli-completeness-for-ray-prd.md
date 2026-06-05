---
validation:
  status: valid
  validated_at: '2026-06-05T12:54:20+10:00'
---

# CLI Completeness for Ray — Timeseries Commands + Market Intelligence Solar

## Problem

Ray (energy market analyst agent) has a CLI instrument panel (`cli-citylab`) covering 25 commands across 7 groups. Two gaps prevent him from operating at full capability:

1. **No timeseries CLI commands.** The API has 3 timeseries endpoints (`/energy/timeseries/{price,demand,generation}`) that return windowed, interval-bucketed data for trend analysis and charting. These are the only way to answer "how have prices moved today?" or "what's the demand trend this week?" — the existing `energy summary` is a point-in-time snapshot, not a time series. Ray can't reach these endpoints from the CLI.

2. **Market intelligence missing solar data.** The `data market-intelligence` endpoint — Ray's "give me everything" call — returns `solar: null`. The Solcast query service exists (`solar_query.summary()`, `solar_query.outlook()`), it's just not wired into the combined response. Ray gets energy + weather but no solar in his cross-source summary.

Both gaps were identified during the CLI workshop (#workshop-citylab-cli-332, Robbo + Kit, 2026-06-05). The CLI help doc at `docs/help/cli-citylab.md` already documents the timeseries endpoints as API-only — this PRD makes them CLI-accessible.

## Approach

### Part A: Timeseries CLI Commands

Add 3 commands to the `energy` group in `src/citylab/cli_wrapper/commands_energy.py`:

**`cli-citylab energy timeseries-price`**
```
cli-citylab energy timeseries-price --range 24h --region VIC1
cli-citylab energy timeseries-price --range 7d --interval 1h
```

**`cli-citylab energy timeseries-demand`**
```
cli-citylab energy timeseries-demand --range 24h
cli-citylab energy timeseries-demand --range 6h --interval 5min
```

**`cli-citylab energy timeseries-generation`**
```
cli-citylab energy timeseries-generation --range 24h
cli-citylab energy timeseries-generation --range 30d --interval 1d
```

Options (all 3 commands):
- `--region` — default `VIC1`
- `--range` — one of `1h`, `6h`, `24h` (default), `7d`, `30d`
- `--interval` — auto-selected per range if omitted. Valid intervals per range are defined in `energy_query.RANGE_INTERVALS`

Each command hits the corresponding `/api/v1/energy/timeseries/*` endpoint via `APIClient.get()` and prints the JSON response. Same pattern as all existing energy CLI commands.

Return shape: `{ok, region, range, interval, series: [{timestamp, value}], data_as_of}`

### Part B: Market Intelligence Solar Fix

In `src/citylab/routes/api_v1/data.py`, the `market_intelligence()` function (around line 127) returns `"solar": None`. Wire in the solar query service:

```python
from citylab.services import solar_query as sq

# Inside market_intelligence(), after the weather block:
try:
    solar = {
        "summary": sq.summary(),
        "outlook": sq.outlook(),
    }
except Exception:
    solar = None
```

Replace the hardcoded `"solar": None` with the `solar` variable. Same try/except pattern as the weather block — never break the combined endpoint.

### Part C: Update CLI Help Doc

After both parts land, update `docs/help/cli-citylab.md`:
- Add the 3 timeseries commands to the `energy` section (move them from "API-only" to full CLI entries)
- Update the `data market-intelligence` return shape to show `solar: {summary, outlook}` instead of `solar: null`

## Done When

- [ ] `cli-citylab energy timeseries-price --range 24h` returns a JSON series of `[{timestamp, value}]` with price data
- [ ] `cli-citylab energy timeseries-demand --range 7d --interval 1h` returns hourly demand buckets for the last 7 days
- [ ] `cli-citylab energy timeseries-generation --range 24h` returns generation data by fuel type
- [ ] All 3 timeseries commands respect `--region`, `--range`, `--interval` options and fall back to defaults
- [ ] `cli-citylab data market-intelligence` returns solar data (summary + outlook) instead of `null`
- [ ] `docs/help/cli-citylab.md` updated with the 3 new commands and corrected market-intelligence return shape
- [ ] Existing tests pass (no regressions)
- [ ] New commands have basic test coverage (at minimum: command invocation doesn't crash, options are accepted)

## Demo Script

1. Open a terminal connected to the CityLab server
2. Run `cli-citylab energy timeseries-price --range 24h` — see JSON with price series over 24 hours, interval-bucketed
3. Run `cli-citylab energy timeseries-demand --range 7d --interval 1d` — see daily demand aggregates for the week
4. Run `cli-citylab data market-intelligence --region VIC1` — see the combined response with energy, weather, AND solar data (no more `null`)
5. Start Ray: `cli-citylab agent start` — ask "How have prices moved today?" — Ray uses the timeseries data to answer with trend analysis, not just a snapshot
6. Ask Ray "Give me the full market picture" — the market-intelligence response now includes solar irradiance alongside energy and weather
