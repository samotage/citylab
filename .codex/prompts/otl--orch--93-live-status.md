---
description: Live orchestration status — read-only dashboard of current progress
---

# Orchestration Live Status

Display a comprehensive live status of the running orchestration, combining state, queue, worker progress, and recent log entries.

**This is a read-only command.** It does not modify any state.

---

## Step 1: Gather Data

**Run ALL four commands below — do not skip any or reuse cached output:**

```bash
ruby orch/orchestrator.rb state show
```

```bash
ruby orch/orchestrator.rb queue list
```

```bash
ruby orch/orchestrator.rb progress show
```

Check if the orchestrator log exists and read recent entries:

```bash
tail -20 orch/log/orchestrator.log 2>/dev/null || echo "No log file"
```

---

## Step 2: Compute Durations

From the state YAML:
- `started_at` — when processing began (total duration = now - started_at)
- `phase_started_at` — when current phase began (phase duration = now - phase_started_at)

From the progress YAML:
- `updated_at` — when worker last reported (staleness = now - updated_at)
- `phase_started_at` — when worker phase began

Format durations as `Xh Ym Zs` or `Ym Zs` for shorter periods.

---

## Step 3: Build Phase Timeline

Using the state YAML, determine which phases are complete, in progress, or pending.

Phase order: `PREPARE → PROPOSAL → PREBUILD → BUILD → TEST → VALIDATE → FINALIZE`

Map the current `phase` value to determine status:
- Phases before current: `✓` (complete)
- Current phase: `→` (in progress)
- Phases after current: `○` (pending)

If phase durations are available from state transitions, include them.

---

## Step 4: Display Report

Format and display the following report. Adapt sections based on available data.

```
═══════════════════════════════════════════
  ORCHESTRATION LIVE STATUS
═══════════════════════════════════════════

CURRENT CHANGE: [change_name or "none"]
──────────────────────────────────────────
Phase:      [phase] ([in progress/checkpoint])
Duration:   [phase duration] (phase) / [total duration] (total)
Mode:       [Default/Bulk]
Errors:     [count]
Checkpoint: [checkpoint or "none"]

WORKER ACTIVITY
──────────────────────────────────────────
[If progress.yaml exists:]
Step:       [step description]
Detail:     [detail]
Updated:    [time since last update] ago
[If metrics exist, display them:]
Tests:      [passed] passed, [failed] failed / [total] total
Tasks:      [completed] / [total] complete
Ralph:      Attempt [N]

[If no progress.yaml:]
No active worker progress reporting.
(Worker may be using an older command version)

PHASE TIMELINE
──────────────────────────────────────────
[✓/→/○] PREPARE     [duration or —]
[✓/→/○] PROPOSAL    [duration or —]
[✓/→/○] PREBUILD    [duration or —]
[✓/→/○] BUILD       [duration or —]
[✓/→/○] TEST        [duration or —]
[✓/→/○] VALIDATE    [duration or —]
[✓/→/○] FINALIZE    [duration or —]

QUEUE
──────────────────────────────────────────
[→/✓/✗/○] [change_name]  [status]
...

RECENT LOG (last 5 entries)
──────────────────────────────────────────
[timestamp] [message]
...

═══════════════════════════════════════════
```

---

## Fallback: No Active Orchestration

If state shows `phase: idle` and queue is empty:

```
═══════════════════════════════════════════
  ORCHESTRATION LIVE STATUS
═══════════════════════════════════════════

No active orchestration.

To start: /otl:orch:10-queue-add then /otl:orch:20-start-queue-process

═══════════════════════════════════════════
```
