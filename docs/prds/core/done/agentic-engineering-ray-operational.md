---
validation:
  status: valid
  validated_at: '2026-06-05T12:54:21+10:00'
---

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

## Agentic Engineering Tasks — Implemented

### Task 1: Timeseries routing (DONE)

- Timeseries commands added to Ray's Tools Inventory routing table with explicit trigger conditions (windowed trends vs raw historical)
- Phase 3 decision tree split: branch 2 routes to timeseries for trend questions, new branch 3 routes to raw prices/generation for specific-moment lookups
- CLI help doc updated: timeseries moved from "API-only" to full CLI entries with synopsis and examples
- Anti-convergence pattern added: using raw `energy prices` for trend analysis when timeseries commands with proper windowing are available

### Task 2: Market-intelligence Solcast routing (DONE)

- CLI help doc return shape updated: `solar: null` replaced with `solar: {summary, outlook}`
- Ray's Tools Inventory `data market-intelligence` row updated to mention solar

### Task 3: Voice interface tuning (DONE — instruction layer)

- Data Response Discipline section added to Communication Style: no JSON dumps, headline-then-why structure, quantify sparingly, voice compression rule
- Voice-specific constraint: one sentence headline, one sentence cause
- Live testing against demo script questions deferred to demo environment readiness

**Remaining (requires live environment):**
- [ ] Verify session-start help doc read trigger fires correctly
- [ ] Test 5 representative questions route to correct CLI commands
- [ ] Verify data freshness caveat triggers when data is stale
- [ ] Verify dashboard pointer works for visual requests

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
