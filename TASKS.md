# Tasks: Agentic Engineering — Ray Operational Layer

Source PRD: docs/prds/core/agentic-engineering-ray-operational.md
Branch: feature/hack-agentic-engineering-ray-operational

## Context

The instruction-layer work for this PRD is already committed and does NOT need
rebuilding (per PRD "What's Done" + "Tasks Implemented"):
- CLI reference doc: `docs/help/cli-citylab.md` (verified present)
- Ray skill file CityLab operational layer (Headspace repo)
- Startup prompt update in `headspace_client.py`
- Task 1 (timeseries routing), Task 2 (market-intelligence Solcast routing),
  Task 3 (voice interface tuning — instruction layer) all marked DONE

All CLI commands named in the Demo Script are verified to exist in the
`cli-citylab` wrapper (`energy summary`, `energy timeseries-price`,
`weather outlook --factor wind`, `solar outlook`, `energy generation`,
`data sources`).

The remaining work is the live-environment verification checklist from Task 3,
which the PRD explicitly deferred to "demo environment readiness". These tasks
prove the demo script runs end to end.

## Task List

- [ ] 1. Verify CityLab server is up and healthy (`curl http://127.0.0.1:15099/health`); restart via `./restart_server.sh` only if down.
- [ ] 2. Verify the help doc read trigger: confirm `docs/help/cli-citylab.md` is readable and the startup prompt in `headspace_client.py` still points Ray to read it before greeting.
- [ ] 3. Run the demo-script CLI commands directly to confirm they return data: `cli-citylab energy summary --region VIC1`, `cli-citylab energy timeseries-price --range 24h`, `cli-citylab weather outlook --factor wind`, `cli-citylab solar outlook`, `cli-citylab energy generation`, `cli-citylab data sources`.
- [ ] 4. Verify data freshness signalling: confirm `data sources` reports per-source staleness so Ray can caveat stale data (demo step 6).
- [ ] 5. Verify the dashboard pointer: confirm `/energy` route renders (the target Ray directs to for "can I see this on a chart?", demo step 5).
- [ ] 6. Record verification results: note any command that fails or returns empty, and whether each is a blocker for the demo or acceptable (synthetic-fallback data is acceptable).

## Demo Script

1. Start Ray via dashboard chat panel or `cli-citylab agent start --persona energy-market-analyst-ray-50`
2. Ask: "What's happening in the market right now?"
   - Ray reads help doc (first question), runs `energy summary`, interprets: "VIC spot price is $X — [reason from generation mix / weather / interconnectors]"
3. Ask: "How have prices moved today?"
   - Ray runs `energy timeseries-price --range 24h`, describes the trend with NEM context
4. Ask: "What's the weather doing to generation?"
   - Ray runs `weather outlook --factor wind` + `solar outlook`, correlates with `energy generation`, briefs on supply-side weather impact
5. Ask: "Can I see this on a chart?"
   - Ray directs to `/energy` dashboard
6. Ask: "Are the data pipelines healthy?"
   - Ray runs `data sources`, reports status per source with freshness assessment

The key insight: Ray isn't just a chatbot with energy knowledge — he's an analyst with live instruments, pulling real data and interpreting it through NEM expertise.
