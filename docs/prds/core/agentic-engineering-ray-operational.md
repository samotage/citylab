# Agentic Engineering — Ray Operational Layer

## Problem

Ray (energy-market-analyst-ray-50) has NEM domain knowledge but no operational method for using CityLab's instruments.  Without instruction-layer wiring, he defaults to answering from training data instead of pulling live stored data, guesses CLI syntax, and can't self-serve the help documentation.  The voice demo requires Ray to operate CityLab fluently — pull data, interpret it, brief the operator — without manual guidance on every command.

## What's Done (Workshop #332)

These artifacts are committed and do not need rebuilding:

1. **CLI reference doc** — `docs/help/cli-citylab.md` (committed `c5664fc`).  Consolidated reference covering all 7 command groups, return shapes, and common workflows.

2. **Ray skill file — CityLab operational layer** (committed `5e2e8d8` in Headspace repo):
   - Core Identity updated — "operational analyst for the CityLab energy platform"
   - CityLab Tools Inventory — CLI routing table, energy dashboard pointer, external data hooks (WebSearch/WebFetch for AEMO/OpenNEM/ASX)
   - Decision Boundaries expanded — read-only CLI autonomous, backfill/schedule-create gated
   - Phase 3 rewritten — 7-branch routing decision tree, session-start help doc trigger, data freshness discipline
   - 5 CityLab operational anti-convergence patterns

3. **Startup prompt update** — `headspace_client.py` default initial_prompt now instructs agent to read CLI help doc before greeting (committed `04e601f`).

## What Remains — Agentic Engineering Tasks

### Task 1: Update Ray routing table after timeseries CLI commands land

**Depends on:** Robbo's PRD for timeseries CLI commands (builder task).

**Scope:** When `energy timeseries-price`, `energy timeseries-demand`, `energy timeseries-generation` CLI commands exist:
- Add them to Ray's Tools Inventory routing table in skill.md
- Add routing entries to the Phase 3 decision tree: "trends over time" questions should route to timeseries commands (with `--range` and `--interval`) when windowed/bucketed data is needed, vs the existing `energy prices` for raw historical
- Update `docs/help/cli-citylab.md` — move timeseries from "API-only" to full CLI entries with synopsis and examples
- Add anti-convergence pattern: using raw `energy prices` for trend analysis when timeseries commands with proper windowing are available

**Done when:**
- [ ] Timeseries commands appear in Ray's routing table with explicit trigger conditions
- [ ] CLI help doc has full entries for all three timeseries commands
- [ ] Decision tree distinguishes "raw historical" (prices/generation) from "windowed trend" (timeseries) routing

### Task 2: Update Ray routing after market-intelligence Solcast fix

**Depends on:** Robbo's PRD for market-intelligence Solcast wiring (builder task).

**Scope:** When `data market-intelligence` returns solar data instead of `null`:
- Update the CLI help doc return shape documentation to include solar fields
- Verify Ray's routing table — `data market-intelligence` trigger already covers cross-source queries, but confirm the solar data is mentioned in the "what it returns" description

**Done when:**
- [ ] CLI help doc reflects solar data in market-intelligence response
- [ ] Ray's Tools Inventory mentions solar in the market-intelligence row

### Task 3: Voice interface tuning

**Depends on:** Tasks 1-2 complete, working demo environment.

**Scope:** Test Ray through the voice interface and tune the instruction layer for conversational flow:
- Verify the session-start help doc read trigger fires correctly
- Test the routing decision tree against 5-10 representative voice questions ("what's the spot price?", "how have prices moved today?", "what's the weather doing to generation?", "show me a chart", "are the pipelines healthy?")
- Tune response length — voice needs brief answers with interpretation, not JSON dumps.  Ray's Communication Style section already says "brief when the answer is simple" but may need a voice-specific constraint if responses are too long
- Verify data freshness caveat triggers when data is stale
- Verify dashboard pointer works for visual requests

**Done when:**
- [ ] Ray reads help doc on first data question (verified in transcript)
- [ ] 5/5 representative questions route to the correct CLI command
- [ ] Responses are conversational, not JSON dumps — market interpretation present
- [ ] Stale data triggers a freshness caveat
- [ ] "Show me a chart" directs to dashboard

## Demo Script

1. Start Ray via dashboard chat panel or `cli-citylab agent start --persona energy-market-analyst-ray-50`
2. Ask: "What's happening in the market right now?"
   - Ray reads help doc (first question), runs `energy summary`, interprets: "VIC spot price is $X — [reason from generation mix / weather / interconnectors]"
3. Ask: "How have prices moved today?"
   - Ray runs `energy prices --from today` (or timeseries command if available), describes the trend with NEM context
4. Ask: "What's the weather doing to generation?"
   - Ray runs `weather outlook --factor wind` + `solar outlook`, correlates with `energy generation`, briefs on supply-side weather impact
5. Ask: "Can I see this on a chart?"
   - Ray directs to `/energy` dashboard
6. Ask: "Are the data pipelines healthy?"
   - Ray runs `data sources`, reports status per source with freshness assessment

The key insight: Ray isn't just a chatbot with energy knowledge — he's an analyst with live instruments, pulling real data and interpreting it through NEM expertise.
