---
name: 'Complexity Audit'
description: 'Scan codebase for over-engineering, deep coupling, and unnecessary complexity'
---

# Complexity Audit

You are performing a systematic complexity audit of this codebase. Your goal is to identify over-engineered modules, unnecessary abstraction layers, and deep coupling chains where small misalignments cascade into compound failures.

**This is a read-only analysis.** Do not modify any code. Produce a report.

## Step 1: Scope the Audit

Before scanning anything, ask the user what they want to audit.

Use `AskUserQuestion` with these questions:

**Question 1 — Scope:**
- "Full codebase" — scan all services, models, routes, and background threads
- "Services only" — focus on `src/claude_headspace/services/` (where most complexity lives)
- "Specific subsystem" — let the user specify a module or flow to deep-dive

**Question 2 — Depth:**
- "Quick scan" — map service graph, flag obvious issues, skip deep path tracing. Good for periodic check-ins.
- "Deep audit" — full service graph, critical path tracing, coupling analysis, per-module assessment. Thorough but uses more context.

**Question 3 — Focus (multi-select):**
Which complexity patterns should this audit prioritise? (select all that apply)
- "Abstraction without payoff" — wrappers, registries, indirection layers serving one implementation
- "Deep call chains" — flows passing through 4+ service boundaries (the cascading failure concern)
- "Parallel mechanisms" — multiple systems accomplishing overlapping goals
- "State management sprawl" — same state tracked in multiple places
- "Defensive complexity" — error handling for impossible scenarios
- "Configuration-driven indirection" — strategy patterns with only one real path
- "All of the above"

## Step 2: Read Project Context

Read `CLAUDE.md` to understand:
- The service architecture and how services are registered (`app.extensions`)
- The key services list and their relationships
- The data models and state machine
- The critical flows (hooks -> state -> SSE, turns -> summarisation -> headspace, etc.)

This gives you the map. The audit validates whether the map matches reality and whether the territory is more complex than the map suggests.

## Step 3: Map the Service Graph

Read every service module in `src/claude_headspace/services/`. For each one, record:

1. **What it does** (1 sentence)
2. **Dependencies** — what other services/modules it imports or calls
3. **Dependents** — what calls this service (search for its usage across the codebase)
4. **Registered as** — its `app.extensions` key (if any)
5. **Complexity signals:**
   - Line count
   - Number of public methods
   - Number of dependencies
   - Does it wrap another service with minimal added logic?
   - Does it have only one caller?
   - Does it manage its own state (in-memory caches, registries)?

**Output:** Build a dependency table. Flag services that are:
- **Thin wrappers** — could be inlined into their single caller
- **Hub services** — everything depends on them (high blast radius for changes)
- **Orphans** — registered but rarely or never called
- **State holders** — maintain in-memory state that duplicates or diverges from the database

If the user selected "Quick scan" depth, skip to Step 5 after this.

## Step 4: Trace Critical Paths (Deep audit only)

Follow these flows end-to-end, recording every service boundary crossing:

### Flow 1: Hook -> State Transition -> SSE Broadcast
Starting from a hook HTTP request hitting a route in `routes/`, trace through:
hook route -> HookReceiver -> HookLifecycleBridge -> TaskLifecycleManager -> StateMachine -> IntentDetector -> EventWriter -> Broadcaster -> CardState

Count the hops. Identify where the chain could be shortened without losing functionality.

### Flow 2: Turn Processing -> Summarisation -> Headspace Update
From a turn being detected through to a headspace snapshot being persisted:
turn detection -> TaskLifecycleManager -> SummarisationService -> InferenceService -> InferenceCache -> InferenceRateLimiter -> OpenRouterClient
then: frustration score -> HeadspaceMonitor -> HeadspaceSnapshot persistence

### Flow 3: Priority Scoring
From trigger to card update:
trigger -> PriorityScoringService -> InferenceService (batch) -> CardState -> Broadcaster

### Flow 4: Session Registration
From first hook to agent appearing on dashboard:
hook -> SessionCorrelator (5-strategy cascade) -> SessionRegistry -> Agent creation -> CardState -> Broadcaster

For each flow:
- List every service/function hop as a numbered chain
- Annotate hops where the indirection adds no value (just passes data through)
- Identify where error handling is duplicated across layers
- Note where assumptions between services could silently diverge

## Step 5: Apply Complexity Patterns

Scan the codebase for each complexity pattern the user selected. For each finding:

### Pattern: Abstraction Without Payoff
Look for:
- Classes that wrap a single function or another class with minimal transformation
- Registry/factory patterns where there's only one registered implementation
- Abstract base classes with a single concrete subclass
- Service classes with one public method that could be a plain function

### Pattern: Deep Call Chains
Look for:
- Flows where data passes through 4+ service boundaries before producing an outcome
- Services that are pure pass-throughs (receive input, call another service, return its result)
- Error handling that catches and re-raises at multiple layers without adding information

### Pattern: Parallel Mechanisms
Look for:
- File watcher AND hooks monitoring the same state changes
- In-memory registries AND database tables tracking the same entities
- Multiple services that detect the same condition (e.g., session end)
- Polling AND event-driven mechanisms for the same data

### Pattern: State Management Sprawl
Look for:
- The same logical state stored in multiple places (memory + DB + computed)
- Caches that can diverge from their source of truth
- State that requires manual synchronisation between locations
- "Last seen" / "last updated" timestamps maintained independently in multiple tables

### Pattern: Defensive Complexity
Look for:
- Try/except blocks around code that cannot raise the caught exception
- None-checks on values that are always present at that point in the flow
- Fallback logic for configurations that always have a value
- Validation of internal data that was already validated upstream

### Pattern: Configuration-Driven Indirection
Look for:
- Config lookups that always resolve to the same value
- Strategy/plugin patterns with only one implementation
- Feature flags that are never toggled
- Model selection logic where only one model is ever used in practice

## Step 6: Assess Background Threads

For each background thread (agent reaper, activity aggregator, commander availability, file watcher):
- What does it do?
- How often does it run?
- Could this be done on-demand instead of continuously?
- What happens if it fails silently? Would anyone notice?
- Does it share state with the main thread in thread-unsafe ways?

## Step 7: Produce the Report

Write the report to `docs/reviews_remediation/complexity-audit-YYYY-MM-DD.md` (using today's date).

Use this structure:

```markdown
# Complexity Audit Report

**Date:** YYYY-MM-DD
**Scope:** [what was scanned]
**Depth:** [quick scan / deep audit]
**Focus patterns:** [which patterns were checked]

## Executive Summary

[2-3 paragraphs: overall complexity assessment, biggest systemic issues, and the estimated "complexity tax" — how much harder is this codebase to modify and debug than it needs to be. Be direct and specific, not vague.]

## Service Dependency Graph

[Table of all services with their dependency count, dependent count, line count, and complexity flags]

| Service | Lines | Deps | Dependents | Flags |
|---------|-------|------|------------|-------|
| ... | ... | ... | ... | thin wrapper / hub / orphan / state holder |

## Critical Path Analysis (deep audit only)

For each traced flow:
### Flow N: [name]
1. [hop] — [annotation]
2. [hop] — [annotation]
...
**Hops:** N | **Could be:** M | **Savings:** [what gets simpler]

## Findings

For each finding, sorted by impact (highest first):

### [PATTERN] Finding title

- **Files:** [paths with line numbers]
- **Impact:** [how this complexity manifests as real problems — bugs, confusion, fragility, cascading failures]
- **Current state:** [what it does now, concretely]
- **Simpler alternative:** [what it would look like simplified — not "simplify this" but describe the target state]
- **Risk:** [what could break, how to mitigate]
- **Effort:** low / medium / high

## Complexity Scores

Rate each major subsystem on a simple scale:

| Subsystem | Complexity | Justified? | Notes |
|-----------|-----------|------------|-------|
| Hook processing | high/med/low | yes/partially/no | ... |
| State management | ... | ... | ... |
| Intelligence/inference | ... | ... | ... |
| Real-time (SSE) | ... | ... | ... |
| Monitoring | ... | ... | ... |
| Session management | ... | ... | ... |

## Recommended Simplification Sequence

Ordered list of simplification efforts. Each item:
1. **[Name]** — [what to do] | Effort: [low/med/high] | Unblocks: [what becomes easier]

Sequence to minimise risk and maximise early wins. Note dependencies between items.

## Leave Alone

Modules or patterns that look complex but earn their complexity. Briefly explain why the abstraction is justified so future audits don't re-flag them.
```

## Step 8: Present to User

After writing the report, give the user a brief summary:
- Number of findings by effort level
- Top 3 highest-impact simplification opportunities
- The recommended first move
- The report file path

Ask if they want to drill deeper into any specific finding or subsystem.
