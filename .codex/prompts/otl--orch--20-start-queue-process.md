---
description: Persistent team lead — orchestrates PRD processing by spawning foreground
  workers
---

# PRD Orchestration Lead

You are the persistent orchestration lead. You manage the full PRD processing pipeline by spawning foreground worker agents via the `Task` tool for each phase, handling all checkpoints, and maintaining state recovery via the Ruby YAML backend.

**Key principles:**
- You spawn workers using `Task(subagent_type="general-purpose")` — NOT `TeamCreate`
- You handle ALL checkpoints (user interaction). Workers never interact with the user.
- You manage ALL phase state transitions. Workers report results; you update state.
- You handle ALL notifications via `ruby orch/notifier.rb`.
- **You are the exclusive owner of the canonical TodoWrite plan.** Workers MUST NOT call TodoWrite — sub-agents spawned via `Task` fire hooks on a session Headspace cannot correlate, so any sub-agent TodoWrite call is invisible and would pollute the visible plan. See "Canonical Orchestration Plan" below.

---

## Progress Message Format (mandatory)

Every message you emit during the pipeline MUST include: (1) the PRD/change name, and (2) the phase position as N/8. The operator monitors progress via the Headspace dashboard — messages without these two identifiers are useless noise.

**Template:** `[change_name] Phase N/8: Phase-Name — action`

**Examples:**
```
[voice-bridge-auth] Phase 1/8: Proposal — spawning worker
[voice-bridge-auth] Phase 1/8: Proposal — completed, OpenSpec files created. Progressing to Build.
[voice-bridge-auth] Phase 2/8: Build — spawning worker
[voice-bridge-auth] Phase 2/8: Build — completed, 11/11 tasks passed. Progressing to Compliance.
[voice-bridge-auth] Phase 3/8: Compliance — spawning worker (attempt 1)
[voice-bridge-auth] Phase 3/8: Compliance — non-compliant, spawning fix agent then retry
[voice-bridge-auth] Phase 4/8: Simplify — no changes needed, progressing to Test
[voice-bridge-auth] Phase 8/8: Post-merge — complete. Queue: 2 PRDs remaining.
```

**Rules:**
- Use the `change_name` from the queue item, not the filename or PRD path.
- Phase numbers are fixed: 1=Proposal, 2=Build, 3=Compliance, 4=Simplify, 5=Test, 6=Smoke, 7=Finalize, 8=Post-merge.
- On retry, keep the same phase number: `Phase 2/7: Compliance (retry)`.
- On error/failure, include the phase number: `[voice-bridge-auth] Phase 5/7: Smoke — FAILED after 2 attempts. Pipeline stopped.`
- When processing multiple PRDs, include queue position at phase transitions: `Queue: 3 of 5 PRDs, processing [change_name]`.
- NEVER emit bare messages like "Spawning Compliance worker" or "Updating state and progressing to Compliance" — those are invisible without the PRD name and phase number.

---

## Canonical Orchestration Plan (TodoWrite contract)

This lead is the **only** session allowed to emit TodoWrite for the orchestration pipeline. Headspace mirrors the lead's TodoWrite into the agent card plan strip. The contract is fixed and load-bearing — do not improvise phase names, order, or markers.

### Phase labels (exactly these eight, in this order)

1. `Proposal`
2. `Build`
3. `Compliance`
4. `Simplify`
5. `Test`
6. `Smoke`
7. `Finalize`
8. `Post-merge`

Labels mirror the CLI worker command filenames. Do not abbreviate, pluralise, or retitle.

### TodoWrite status mapping

| Lifecycle state | TodoWrite `content` | TodoWrite `status` |
|---|---|---|
| Phase not yet reached | `Proposal` (etc.) | `pending` |
| Phase currently running | `Proposal` (etc.) | `in_progress` |
| Phase finished successfully | `Proposal` (etc.) | `completed` |
| Phase retrying after failure | `Proposal (retry)` | `in_progress` |
| Phase terminally failed (pipeline stopped here) | `Proposal (failed)` | `in_progress` |

The `(retry)` and `(failed)` suffixes on the `content` field are the markers the Headspace handler normalises into the `retry` / `failed` render-layer glyphs. Keep the parenthetical exactly as shown.

### When to emit TodoWrite

- **At the start of every new PRD** (Step 6a): emit the canonical 8-phase plan with `Proposal` as `in_progress` and all other phases as `pending`.
- **At every phase boundary** (alongside each `ruby orch/orchestrator.rb state set --key phase --value X_complete`): emit a TodoWrite that flips the just-completed phase to `completed` and the next phase to `in_progress`.
- **On any retry** (Compliance attempt 1 non-compliant, Smoke retest spawn): emit a TodoWrite that flips the retrying phase's `content` to the `(retry)` suffix, `status: in_progress`.
- **On any terminal failure** (HARD STOP paths: 2×non-compliant, smoke retest fail, worker error, finalize not_compliant abort): emit a TodoWrite that flips the active phase's `content` to the `(failed)` suffix, `status: in_progress`. Remaining phases stay `pending`. Emit this **before** the notifier/queue fail/STOP sequence.

### Worker prohibition

Workers (`30-proposal`, `35-build`, `40-compliance`, `45-simplify`, `50-test`, `55-smoke`, `60-finalize`, `91-notify`) MUST NOT call TodoWrite under any circumstance. Their preambles document this. Sub-agent TodoWrite calls are invisible to Headspace and silently corrupt nothing — but they also do nothing useful, so they are forbidden to preserve the single-owner invariant.

---

## Step 0: Verify Agent Identity (REQUIRED before any Ruby invocation)

The Ruby orchestrator hard-fails at boot if `OTL_AGENT_SLUG` and `OTL_AGENT_ID` are not set. These two env vars stamp every commit the orchestrator creates with an `Agent: <slug>` / `Agent-Id: <id>` trailer so we can attribute commits to the agent and session that produced them.

**Identity env vars are injected automatically by Headspace at session-start.** Verify they are present before proceeding:

```bash
echo "OTL_AGENT_SLUG=$OTL_AGENT_SLUG"
echo "OTL_AGENT_ID=$OTL_AGENT_ID"
```

If both values are populated, proceed to Step 1. Every worker spawned via `Task` inherits the parent process env, so workers do not need to re-export.

**If either var is empty or unset**, identity injection failed. STOP and surface to the operator with this message: "Identity env-var injection failed — OTL_AGENT_SLUG and/or OTL_AGENT_ID are not set. Please check Headspace session-start hook processing." Do NOT default to a placeholder, do NOT use a generic value like `orch-lead`. Unattributed commits defeat the forensic trail this work is designed to produce.

**Hard rules:**
- These vars MUST be set in the same session where you run the Ruby orchestrator. Setting them in a sub-agent's context is too late — workers inherit env from this lead at spawn time.
- The orchestrator will refuse to start (with a clear error message) if either var is unset or empty. That is the system working as designed.

## Step 1: Resume Detection

**Run both commands now — do not use cached state from a previous invocation.**

```bash
ruby orch/orchestrator.rb state show
```

```bash
ruby orch/orchestrator.rb queue status
```

### Evaluate state:

**If state phase is `idle` or `complete` (or no phase set) AND no `in_progress` queue items:**
- Proceed to Step 2 (fresh start)

**If state has an active phase AND queue has an `in_progress` item:**

Previous run was interrupted. Extract: `change_name`, `phase`, `bulk_mode`, `branch`

Map to resume point:

| Phase in state | Resume from |
|---|---|
| `prepare`, `proposal`, `proposal_review`, `prebuild` | PROPOSAL phase (step 6b) |
| `proposal_complete`, `build` | BUILD phase (step 6b2) |
| `build_complete`, `compliance` | COMPLIANCE phase (step 6c) |
| `compliance_complete`, `simplify` | SIMPLIFY phase (step 6d) |
| `simplify_complete`, `test` | TEST phase (step 6e) |
| `test_complete`, `smoke` | SMOKE phase (step 6f) |
| `smoke_complete`, `validate`, `finalize` | FINALIZE phase (step 6g) |
| `validate_complete`, `finalize_complete` | POST-MERGE (step 6h) |
| `merge_complete` | POST-MERGE (step 6h) — skip merge, continue from checkout |

Display resume banner:

```
═══════════════════════════════════════════
  RESUMING ORCHESTRATION
═══════════════════════════════════════════
Change:  [change_name]
Phase:   [phase]
Mode:    [Default/Bulk]

Resuming from: [phase name]
═══════════════════════════════════════════
```

Skip mode selection — `bulk_mode` is already in state. Jump to the mapped phase.

---

## Step 2: Queue Check

```bash
ruby orch/orchestrator.rb queue next
```

If `queue_empty: true`:

```
Queue is empty. Nothing to process.
```

STOP here.

---

## Step 3: Mode Selection

**Bulk mode is the default. Do not ask — just set it.**

```bash
ruby orch/orchestrator.rb state set --key bulk_mode --value true
```

Manual mode is only used when the operator explicitly passes `--manual` or says "manual mode" in the invocation context. If manual mode was requested:

```bash
ruby orch/orchestrator.rb state set --key bulk_mode --value false
```

---

## Step 4: Batch Validation

**Run this step — do not skip it.** Check every pending PRD for two things: completed-PRD status AND validation status.

Get all pending PRDs:

```bash
ruby orch/orchestrator.rb queue list
```

### 4a. Completed PRD Check

For each pending PRD, check if its path contains `/done/`. A PRD in `done/` was already processed by a prior orchestration run — re-processing it creates ghost branches with stale commits.

Display table:

```
| # | PRD | Status |
|---|-----|--------|
| 1 | docs/prds/events/done/feature-prd.md | ⊗ Already completed (in done/) |
| 2 | docs/prds/persona/other-prd.md | ✓ Active |
```

**If any PRDs are in `done/`:** Remove them from the queue immediately:

```bash
ruby orch/orchestrator.rb queue fail --prd-path "[prd_path]" --reason "PRD already completed — path is in done/ directory"
```

Report which PRDs were removed and why. Continue with remaining active PRDs.

**If no active PRDs remain after removal:** STOP — queue is effectively empty.

### 4b. Validation Check

For each remaining (active) pending PRD:

```bash
ruby orch/prd_validator.rb status --prd-path [prd_path]
```

Display table:

```
| # | PRD | Validation Status |
|---|-----|-------------------|
| 1 | feature-prd.md | ✓ Valid (Feb 20) |
| 2 | other-prd.md | ⊗ Unvalidated |
```

**If all valid:** Skip to Step 5.

**If some need validation, use AskUserQuestion:**
- Options: "Validate unvalidated/invalid only", "Re-validate all", "Skip validation", "Remove invalid from queue"

Handle each option accordingly. For validation, spawn `30: prd-validate` via Skill tool for each PRD needing it.

---

## Step 5: Initialize Usage Tracking

```bash
ruby orch/orchestrator.rb usage start --prd-path "[first_prd_path]"
```

Display:

```
═══════════════════════════════════════════
  ORCHESTRATION STARTED
═══════════════════════════════════════════
Mode: [Default/Bulk]
═══════════════════════════════════════════
```

---

## Step 6: PRD Processing Loop

**Maintain a PRD results manifest** throughout the loop. For each PRD processed, record its `prd_path`, final status (completed/failed), `pr_number`, and `pr_url` (from finalize_result) or failure reason. This manifest is used in the Step 7 completion summary.

### CRITICAL: Phase Dispatch Table

**After EVERY phase completes, consult this table to determine the next phase. Do NOT rely on reading forward through the document — use this table.**

| Current state | Next action |
|---|---|
| `proposal_complete` | → Step 6b2 BUILD |
| `build_complete` | → Step 6c COMPLIANCE |
| `compliance_complete` | → Step 6d SIMPLIFY |
| `simplify_complete` | → Step 6e TEST |
| `test_complete` | → Step 6f SMOKE |
| `smoke_complete` | → Step 6g FINALIZE |
| `finalize_complete` | → Step 6h POST-MERGE |
| post-merge complete | → Step 6a QUEUE NEXT (**NOT** Step 7) |

**Step 7 is ONLY reachable from Step 6a when `queue_empty: true`.** There is no other path to Step 7. If you find yourself at Step 7 without having seen `queue_empty: true` from a `queue next` command, you have skipped phases — stop and re-check the dispatch table.

---

### 6a. Initialize

```bash
ruby orch/orchestrator.rb queue next
```

If `queue_empty: true` → jump to Step 7 (Pipeline Complete).

**Completed PRD guard (runtime check):** Before starting the PRD, check if its path contains `/done/`. This catches PRDs that were moved to `done/` between queue-add time and processing time (e.g., completed by a parallel session). If the path contains `/done/`:

```bash
ruby orch/orchestrator.rb queue fail --prd-path "[prd_path]" --reason "PRD already completed — path is in done/ directory (detected at initialize)"
```

Log: "Skipping [prd_path] — already in done/ directory." Return to top of Step 6a (`queue next`).

**If path is active (not in `done/`):** proceed normally:

```bash
ruby orch/orchestrator.rb queue start --prd-path "[prd_path]"
```

Extract: `change_name`, `prd_path`, `branch`

**Emit the canonical 8-phase TodoWrite (mandatory — see "Canonical Orchestration Plan" above):**

```
TodoWrite(todos=[
  {"content": "Proposal", "status": "in_progress", "activeForm": "Running Proposal"},
  {"content": "Build", "status": "pending", "activeForm": "Running Build"},
  {"content": "Compliance", "status": "pending", "activeForm": "Running Compliance"},
  {"content": "Simplify", "status": "pending", "activeForm": "Running Simplify"},
  {"content": "Test", "status": "pending", "activeForm": "Running Test"},
  {"content": "Smoke", "status": "pending", "activeForm": "Running Smoke"},
  {"content": "Finalize", "status": "pending", "activeForm": "Running Finalize"},
  {"content": "Post-merge", "status": "pending", "activeForm": "Running Post-merge"}
])
```

This emission is mandatory, not optional. Headspace's plan strip shows nothing until it fires.

---

### 6b. PROPOSAL Phase

Read the worker instructions:

```
Read(".claude/commands/otl/orch/30-proposal.md")
```

Spawn the worker and **wait for it to complete before continuing** — do not proceed until the Task returns its result:

```
Task(
  subagent_type="general-purpose",
  description="Proposal for [change_name]",
  prompt=[worker instructions + "\n\n## Context\n- change_name: [change_name]\n- prd_path: [prd_path]\n- branch: [branch]\n- bulk_mode: [true/false]"]
)
```

Parse the `proposal_result` YAML from the worker output. If the worker produced no YAML result block, treat as `status: error`.

**If `status: error`:**

```bash
ruby orch/notifier.rb error --change-name "[change_name]" --message "[error_message]" --phase "proposal" --resolution "Fix the issue and re-run"
```

```bash
ruby orch/orchestrator.rb queue fail --prd-path "[prd_path]" --reason "[error_type]: [error_message]"
```

STOP.

**If `status: clarification_needed`:**

Inspect `decision_type` to choose the surfacing path:

- **`decision_type: dirty_tree`** — `development` had uncommitted changes when the worker tried to prepare and we are NOT in bulk mode. The worker has stopped without creating the feature branch. Use AskUserQuestion to present the operator with explicit choices, including the `dirty_files` list from the worker result:
  - `commit_all_to_development` — stage and commit everything to `development`, push, then re-run prepare. (User confirms this is the safe path; the orchestration sweeps and proceeds.)
  - `stop_for_manual_triage` — abort the queue item; operator handles the dirty tree by hand and re-queues later.
  - `stash_and_proceed` — stash everything, proceed with feature branch creation, leave the stash for the operator to recover.

  This checkpoint ALWAYS stops in non-bulk mode regardless of any other flag. If the user picks `commit_all_to_development`, run the same sweep the worker would run in bulk mode, then re-spawn the proposal worker. If the user picks `stop_for_manual_triage`, fail the queue item with a clear reason. If the user picks `stash_and_proceed`, run `git stash push -u -m "pre-orch stash for [change_name]"` then re-spawn the worker.

- **All other `decision_type` values (or no `decision_type`)** — treat as PRD/proposal clarification:
  ```bash
  ruby orch/notifier.rb decision_needed --change-name "[change_name]" --message "Clarification needed before proposal" --checkpoint "awaiting_clarification" --action "Answer questions or update PRD"
  ```
  Use AskUserQuestion to present the gaps/conflicts/questions. This checkpoint ALWAYS stops (even in bulk mode). If user provides answers → re-spawn proposal worker with answers included in context. If user says "stop" → fail the queue item and STOP.

**If `status: success`:**

Clear worker progress and update state:

```bash
ruby orch/orchestrator.rb progress clear
```

```bash
ruby orch/orchestrator.rb state set --key phase --value proposal_complete
```

**Emit TodoWrite phase boundary update** (alongside the state set above — do this every time):

```
TodoWrite(todos=[
  {"content": "Proposal", "status": "completed", "activeForm": "Running Proposal"},
  {"content": "Build", "status": "in_progress", "activeForm": "Running Build"},
  {"content": "Compliance", "status": "pending", "activeForm": "Running Compliance"},
  {"content": "Simplify", "status": "pending", "activeForm": "Running Simplify"},
  {"content": "Test", "status": "pending", "activeForm": "Running Test"},
  {"content": "Smoke", "status": "pending", "activeForm": "Running Smoke"},
  {"content": "Finalize", "status": "pending", "activeForm": "Running Finalize"},
  {"content": "Post-merge", "status": "pending", "activeForm": "Running Post-merge"}
])
```

**NEXT PHASE → 6b2 BUILD.** Consult the Phase Dispatch Table.

---

### 6b2. BUILD Phase

Read the worker instructions:

```
Read(".claude/commands/otl/orch/35-build.md")
```

Spawn the worker and **wait for it to complete before continuing** — do not proceed until the Task returns its result:

```
Task(
  subagent_type="general-purpose",
  description="Build for [change_name]",
  prompt=[worker instructions + "\n\n## Context\n- change_name: [change_name]\n- prd_path: [prd_path]\n- branch: [branch]"]
)
```

Parse the `build_result` YAML from the worker output. If the worker produced no YAML result block, treat as `status: error`.

**If `status: error`:**

```bash
ruby orch/notifier.rb error --change-name "[change_name]" --message "[error_message]" --phase "build" --resolution "Fix the issue and re-run"
```

```bash
ruby orch/orchestrator.rb queue fail --prd-path "[prd_path]" --reason "[error_type]: [error_message]"
```

STOP.

**If `status: clarification_needed`:**

Inspect `decision_type`:

- **`decision_type: prior_run_complete`** — all tasks already marked complete from a prior run. Use AskUserQuestion to present the operator with choices:
  - `delete_and_recreate` — delete the branch and restart from proposal
  - `abort` — fail the queue item

- **`decision_type: scope_gap`** — the build worker found a gap between the PRD and what's needed. Use AskUserQuestion to present the gap and get operator guidance. If user provides guidance → re-spawn build worker with guidance in context. If user says "stop" → fail the queue item.

**If `status: success`:**

Verify `percentage: 100`. If not 100%, re-spawn build worker.

Clear worker progress and update state:

```bash
ruby orch/orchestrator.rb progress clear
```

```bash
ruby orch/orchestrator.rb state set --key phase --value build_complete
```

**Emit TodoWrite phase boundary update** (alongside the state set above — do this every time):

```
TodoWrite(todos=[
  {"content": "Proposal", "status": "completed", "activeForm": "Running Proposal"},
  {"content": "Build", "status": "completed", "activeForm": "Running Build"},
  {"content": "Compliance", "status": "in_progress", "activeForm": "Running Compliance"},
  {"content": "Simplify", "status": "pending", "activeForm": "Running Simplify"},
  {"content": "Test", "status": "pending", "activeForm": "Running Test"},
  {"content": "Smoke", "status": "pending", "activeForm": "Running Smoke"},
  {"content": "Finalize", "status": "pending", "activeForm": "Running Finalize"},
  {"content": "Post-merge", "status": "pending", "activeForm": "Running Post-merge"}
])
```

**NEXT PHASE → 6c COMPLIANCE.** Consult the Phase Dispatch Table.

---

### 6c. COMPLIANCE Phase (Ralph Loop — 2 attempts)

Read the worker instructions:

```
Read(".claude/commands/otl/orch/40-compliance.md")
```

**Attempt 1:** Spawn the compliance checker:

```
Task(
  subagent_type="general-purpose",
  description="Compliance check for [change_name]",
  prompt=[worker instructions + "\n\n## Context\n- change_name: [change_name]\n- prd_path: [prd_path]\n- branch: [branch]\n- attempt: 1\n- previous_findings: none"]
)
```

Parse the `compliance_result` YAML.

**If `status: compliant`:**

Clear worker progress and update state:

```bash
ruby orch/orchestrator.rb progress clear
```

```bash
ruby orch/orchestrator.rb state set --key phase --value compliance_complete
```

**Emit TodoWrite phase boundary update** (Compliance → completed, Simplify → in_progress):

```
TodoWrite(todos=[
  {"content": "Proposal", "status": "completed", "activeForm": "Running Proposal"},
  {"content": "Build", "status": "completed", "activeForm": "Running Build"},
  {"content": "Compliance", "status": "completed", "activeForm": "Running Compliance"},
  {"content": "Simplify", "status": "in_progress", "activeForm": "Running Simplify"},
  {"content": "Test", "status": "pending", "activeForm": "Running Test"},
  {"content": "Smoke", "status": "pending", "activeForm": "Running Smoke"},
  {"content": "Finalize", "status": "pending", "activeForm": "Running Finalize"},
  {"content": "Post-merge", "status": "pending", "activeForm": "Running Post-merge"}
])
```

(This emission applies to **both** the attempt-1 success path and the attempt-2 success path — any time the state flips to `compliance_complete`, emit the TodoWrite update.)

**NEXT PHASE → 6d SIMPLIFY.** Consult the Phase Dispatch Table.

**If `status: non_compliant` (attempt 1):**

**Emit TodoWrite retry marker** (flips Compliance to `(retry)` — render-layer glyph flips to ↻):

```
TodoWrite(todos=[
  {"content": "Proposal", "status": "completed", "activeForm": "Running Proposal"},
  {"content": "Build", "status": "completed", "activeForm": "Running Build"},
  {"content": "Compliance (retry)", "status": "in_progress", "activeForm": "Retrying Compliance"},
  {"content": "Simplify", "status": "pending", "activeForm": "Running Simplify"},
  {"content": "Test", "status": "pending", "activeForm": "Running Test"},
  {"content": "Smoke", "status": "pending", "activeForm": "Running Smoke"},
  {"content": "Finalize", "status": "pending", "activeForm": "Running Finalize"},
  {"content": "Post-merge", "status": "pending", "activeForm": "Running Post-merge"}
])
```

Spawn a fix agent to address the findings:

```
Task(
  subagent_type="general-purpose",
  description="Fix compliance issues for [change_name]",
  prompt="You are a fix agent. Read the PRD at [prd_path] and the compliance report at openspec/changes/[change_name]/compliance-check-attempt-1.md. Fix ONLY the issues identified — do not add anything else. The PRD is your ceiling. After fixing, run: flask db upgrade && ./restart_server.sh && curl -sk https://smac.griffin-blenny.ts.net:5055/health\n\n## Context\n- change_name: [change_name]\n- prd_path: [prd_path]\n- branch: [branch]\n\n## Failures to fix:\n" + [formatted list of failures from compliance_result]
)
```

**Attempt 2:** Re-spawn the compliance checker:

```
Task(
  subagent_type="general-purpose",
  description="Compliance recheck for [change_name]",
  prompt=[worker instructions + "\n\n## Context\n- change_name: [change_name]\n- prd_path: [prd_path]\n- branch: [branch]\n- attempt: 2\n- previous_findings: [summary of attempt 1 findings and what the fix agent did]"]
)
```

Parse the `compliance_result` YAML.

**If `status: compliant` (attempt 2):**

Clear progress, update state, proceed to SIMPLIFY.

**If `status: non_compliant` (attempt 2) — HARD STOP:**

**Emit TodoWrite terminal failure marker first** (Compliance → `(failed)`, remaining phases stay `pending` — render-layer glyph flips to ✗):

```
TodoWrite(todos=[
  {"content": "Proposal", "status": "completed", "activeForm": "Running Proposal"},
  {"content": "Build", "status": "completed", "activeForm": "Running Build"},
  {"content": "Compliance (failed)", "status": "in_progress", "activeForm": "Compliance failed"},
  {"content": "Simplify", "status": "pending", "activeForm": "Running Simplify"},
  {"content": "Test", "status": "pending", "activeForm": "Running Test"},
  {"content": "Smoke", "status": "pending", "activeForm": "Running Smoke"},
  {"content": "Finalize", "status": "pending", "activeForm": "Running Finalize"},
  {"content": "Post-merge", "status": "pending", "activeForm": "Running Post-merge"}
])
```

```bash
ruby orch/notifier.rb error --change-name "[change_name]" --message "PRD compliance failed after 2 attempts" --phase "compliance" --resolution "Review compliance reports and fix manually"
```

```bash
ruby orch/orchestrator.rb queue fail --prd-path "[prd_path]" --reason "PRD compliance failed after 2 Ralph loop attempts"
```

Display the detailed error report to the user:

```
═══════════════════════════════════════════
  COMPLIANCE FAILURE — PIPELINE STOPPED
═══════════════════════════════════════════
Change:  [change_name]
PRD:     [prd_path]
Attempts: 2 (both failed)

Findings (attempt 2):
  Failed:   [N] requirements
  Partial:  [N] requirements
  Violated: [N] constraints
  Scope creep: [N] items

Specific failures:
  [list each FAIL/VIOLATED requirement with:
   - what PRD says
   - what code does
   - recommended fix]

Fix attempts made:
  [summary of what the fix agent tried on each attempt]

Reports:
  Attempt 1: openspec/changes/[change_name]/compliance-check-attempt-1.md
  Attempt 2: openspec/changes/[change_name]/compliance-check-attempt-2.md

Recommended next steps:
  1. Review the compliance reports
  2. Fix the remaining issues manually
  3. Re-run orchestration to resume from compliance phase
═══════════════════════════════════════════
```

STOP.

**If `status: error` (any attempt):**

Notify and STOP (same pattern as other phases).

---

### 6d. SIMPLIFY Phase

Read the worker instructions:

```
Read(".claude/commands/otl/orch/45-simplify.md")
```

Spawn the worker:

```
Task(
  subagent_type="general-purpose",
  description="Simplify for [change_name]",
  prompt=[worker instructions + "\n\n## Context\n- change_name: [change_name]\n- prd_path: [prd_path]\n- branch: [branch]"]
)
```

Parse the `simplify_result` YAML from the worker output.

**If `status: error`:**

Notify and STOP (same pattern as proposal/build error).

**If `status: success` or `status: no_changes`:**

Clear worker progress and update state:

```bash
ruby orch/orchestrator.rb progress clear
```

```bash
ruby orch/orchestrator.rb state set --key phase --value simplify_complete
```

**Emit TodoWrite phase boundary update** (Simplify → completed, Test → in_progress):

```
TodoWrite(todos=[
  {"content": "Proposal", "status": "completed", "activeForm": "Running Proposal"},
  {"content": "Build", "status": "completed", "activeForm": "Running Build"},
  {"content": "Compliance", "status": "completed", "activeForm": "Running Compliance"},
  {"content": "Simplify", "status": "completed", "activeForm": "Running Simplify"},
  {"content": "Test", "status": "in_progress", "activeForm": "Running Test"},
  {"content": "Smoke", "status": "pending", "activeForm": "Running Smoke"},
  {"content": "Finalize", "status": "pending", "activeForm": "Running Finalize"},
  {"content": "Post-merge", "status": "pending", "activeForm": "Running Post-merge"}
])
```

**NEXT PHASE → 6e TEST.** Consult the Phase Dispatch Table.

---

### 6e. TEST Phase

Read the worker instructions:

```
Read(".claude/commands/otl/orch/50-test.md")
```

Spawn:

```
Task(
  subagent_type="general-purpose",
  description="Test for [change_name]",
  prompt=[worker instructions + "\n\n## Context\n- change_name: [change_name]\n- prd_path: [prd_path]\n- branch: [branch]"]
)
```

Parse the `test_result` YAML.

**If `status: all_passed`:**

Handle human review checkpoint:

- **Bulk mode:** Auto-approve. Send Slack notification.
- **Default mode:** Use AskUserQuestion with tasks summary and files changed. Options: "Approved — continue", "Needs fixes — provide feedback", "Stop — fix manually", "Skip issues — proceed with warning"

  If "Needs fixes" → receive feedback, re-spawn test worker (or build worker if code fixes needed).

Clear worker progress:

```bash
ruby orch/orchestrator.rb progress clear
```

**If `status: human_intervention`:**

- **Bulk mode:** Auto-skip tests, set warning flag. Send Slack notification.
- **Default mode:** Use AskUserQuestion. Options: "Fix manually — re-run", "Skip tests — proceed", "Abort"

**If `status: error`:**

Notify and STOP.

Clear worker progress and update state:

```bash
ruby orch/orchestrator.rb progress clear
```

```bash
ruby orch/orchestrator.rb state set --key phase --value test_complete
```

**Emit TodoWrite phase boundary update** (Test → completed, Smoke → in_progress):

```
TodoWrite(todos=[
  {"content": "Proposal", "status": "completed", "activeForm": "Running Proposal"},
  {"content": "Build", "status": "completed", "activeForm": "Running Build"},
  {"content": "Compliance", "status": "completed", "activeForm": "Running Compliance"},
  {"content": "Simplify", "status": "completed", "activeForm": "Running Simplify"},
  {"content": "Test", "status": "completed", "activeForm": "Running Test"},
  {"content": "Smoke", "status": "in_progress", "activeForm": "Running Smoke"},
  {"content": "Finalize", "status": "pending", "activeForm": "Running Finalize"},
  {"content": "Post-merge", "status": "pending", "activeForm": "Running Post-merge"}
])
```

**NEXT PHASE → 6f SMOKE.** Consult the Phase Dispatch Table. Do NOT skip to FINALIZE.

---

### 6f. SMOKE Phase

Read the worker instructions:

```
Read(".claude/commands/otl/orch/55-smoke.md")
```

Spawn:

```
Task(
  subagent_type="general-purpose",
  description="Smoke test for [change_name]",
  prompt=[worker instructions + "\n\n## Context\n- change_name: [change_name]\n- prd_path: [prd_path]\n- branch: [branch]"]
)
```

Parse the `smoke_result` YAML.

**If `status: all_passed`:**

Clear worker progress and update state:

```bash
ruby orch/orchestrator.rb progress clear
```

```bash
ruby orch/orchestrator.rb state set --key phase --value smoke_complete
```

**Emit TodoWrite phase boundary update** (Smoke → completed, Finalize → in_progress):

```
TodoWrite(todos=[
  {"content": "Proposal", "status": "completed", "activeForm": "Running Proposal"},
  {"content": "Build", "status": "completed", "activeForm": "Running Build"},
  {"content": "Compliance", "status": "completed", "activeForm": "Running Compliance"},
  {"content": "Simplify", "status": "completed", "activeForm": "Running Simplify"},
  {"content": "Test", "status": "completed", "activeForm": "Running Test"},
  {"content": "Smoke", "status": "completed", "activeForm": "Running Smoke"},
  {"content": "Finalize", "status": "in_progress", "activeForm": "Running Finalize"},
  {"content": "Post-merge", "status": "pending", "activeForm": "Running Post-merge"}
])
```

(This emission applies to **both** the initial smoke-pass path and the smoke-retest-pass path — any time the state flips to `smoke_complete`, emit the TodoWrite update.)

**NEXT PHASE → 6g FINALIZE.** Consult the Phase Dispatch Table.

**If `status: failed`:**

**Emit TodoWrite retry marker** (Smoke → `(retry)` — render-layer glyph flips to ↻):

```
TodoWrite(todos=[
  {"content": "Proposal", "status": "completed", "activeForm": "Running Proposal"},
  {"content": "Build", "status": "completed", "activeForm": "Running Build"},
  {"content": "Compliance", "status": "completed", "activeForm": "Running Compliance"},
  {"content": "Simplify", "status": "completed", "activeForm": "Running Simplify"},
  {"content": "Test", "status": "completed", "activeForm": "Running Test"},
  {"content": "Smoke (retry)", "status": "in_progress", "activeForm": "Retrying Smoke"},
  {"content": "Finalize", "status": "pending", "activeForm": "Running Finalize"},
  {"content": "Post-merge", "status": "pending", "activeForm": "Running Post-merge"}
])
```

Spawn a fix agent to address the smoke test failures:

```
Task(
  subagent_type="general-purpose",
  description="Fix smoke failures for [change_name]",
  prompt="You are a fix agent. Read the PRD at [prd_path] and the smoke test report at openspec/changes/[change_name]/smoke-test-report.md. Fix ONLY the CRITICAL and MAJOR failures identified — do not add anything else. The PRD is your ceiling. After fixing, run: flask db upgrade && ./restart_server.sh && curl -sk https://smac.griffin-blenny.ts.net:5055/health\n\n## Context\n- change_name: [change_name]\n- prd_path: [prd_path]\n- branch: [branch]\n\n## Failures to fix:\n" + [formatted list of CRITICAL and MAJOR failures from smoke_result]
)
```

Re-spawn the smoke test worker (1 retry only):

```
Task(
  subagent_type="general-purpose",
  description="Smoke retest for [change_name]",
  prompt=[worker instructions + "\n\n## Context\n- change_name: [change_name]\n- prd_path: [prd_path]\n- branch: [branch]"]
)
```

**If smoke retest passes:** Clear progress, update state, proceed to FINALIZE.

**If smoke retest fails again — HARD STOP:**

**Emit TodoWrite terminal failure marker first** (Smoke → `(failed)` — render-layer glyph flips to ✗):

```
TodoWrite(todos=[
  {"content": "Proposal", "status": "completed", "activeForm": "Running Proposal"},
  {"content": "Build", "status": "completed", "activeForm": "Running Build"},
  {"content": "Compliance", "status": "completed", "activeForm": "Running Compliance"},
  {"content": "Simplify", "status": "completed", "activeForm": "Running Simplify"},
  {"content": "Test", "status": "completed", "activeForm": "Running Test"},
  {"content": "Smoke (failed)", "status": "in_progress", "activeForm": "Smoke failed"},
  {"content": "Finalize", "status": "pending", "activeForm": "Running Finalize"},
  {"content": "Post-merge", "status": "pending", "activeForm": "Running Post-merge"}
])
```

```bash
ruby orch/notifier.rb error --change-name "[change_name]" --message "Smoke test failed after fix attempt" --phase "smoke" --resolution "Review smoke test report and fix manually"
```

```bash
ruby orch/orchestrator.rb queue fail --prd-path "[prd_path]" --reason "Smoke test failed after fix attempt"
```

Display the failure report to the user and STOP.

**If `status: error`:**

Notify and STOP (same pattern as other phases).

---

### 6g. FINALIZE Phase

Read the worker instructions:

```
Read(".claude/commands/otl/orch/60-finalize.md")
```

Spawn:

```
Task(
  subagent_type="general-purpose",
  description="Finalize [change_name]",
  prompt=[worker instructions + "\n\n## Context\n- change_name: [change_name]\n- prd_path: [prd_path]\n- branch: [branch]"]
)
```

Parse the `finalize_result` YAML.

**If `status: not_compliant`:**

This checkpoint ALWAYS stops (even in bulk mode):

```bash
ruby orch/notifier.rb decision_needed --change-name "[change_name]" --message "Spec compliance failed after 2 attempts" --checkpoint "spec_compliance_failed" --action "Review issues and decide"
```

Use AskUserQuestion with issues list. Options: "Fix manually — re-run", "Skip validation — proceed", "Abort"

If "Skip validation" → re-spawn finalize worker with instructions to skip validation and go straight to archive/commit/PR.

**If `status: success`:**

Handle merge checkpoint:

**Squash merges drop per-commit trailers.** GitHub's squash merge replaces every feature-branch commit with a single new commit whose body comes from the `--body` arg. Per-commit `Agent:` / `Agent-Id:` trailers from the feature-branch work are NOT preserved on the squashed commit unless you put them back into the body explicitly. The merge body below carries the merging agent's identity (yours, the lead's) — that is the correct attribution since the squash commit is your action, not the worker's.

- **Bulk mode:** Auto-merge:
  ```bash
  gh pr merge [pr_number] --squash --body "$(cat <<EOF
  Auto-merged by orchestration engine (bulk mode)

  Agent: $OTL_AGENT_SLUG
  Agent-Id: $OTL_AGENT_ID
  Co-Authored-By: Claude <noreply@anthropic.com>
  EOF
  )"
  ```
  If merge fails → fall back to manual checkpoint.

- **Default mode:** Use AskUserQuestion: "PR #[pr_number] created at [pr_url]. Review the PR, then select an option below." Options: "Approve — merge and continue", "Abort"

  If "Approve — merge and continue":
  ```bash
  gh pr merge [pr_number] --squash --body "$(cat <<EOF
  Merged by orchestration engine

  Agent: $OTL_AGENT_SLUG
  Agent-Id: $OTL_AGENT_ID
  Co-Authored-By: Claude <noreply@anthropic.com>
  EOF
  )"
  ```
  If merge fails, report the error and STOP.

Clear worker progress and update state:

```bash
ruby orch/orchestrator.rb progress clear
```

```bash
ruby orch/orchestrator.rb state set --key phase --value finalize_complete
```

**Emit TodoWrite phase boundary update** (Finalize → completed, Post-merge → in_progress):

```
TodoWrite(todos=[
  {"content": "Proposal", "status": "completed", "activeForm": "Running Proposal"},
  {"content": "Build", "status": "completed", "activeForm": "Running Build"},
  {"content": "Compliance", "status": "completed", "activeForm": "Running Compliance"},
  {"content": "Simplify", "status": "completed", "activeForm": "Running Simplify"},
  {"content": "Test", "status": "completed", "activeForm": "Running Test"},
  {"content": "Smoke", "status": "completed", "activeForm": "Running Smoke"},
  {"content": "Finalize", "status": "completed", "activeForm": "Running Finalize"},
  {"content": "Post-merge", "status": "in_progress", "activeForm": "Running Post-merge"}
])
```

**NEXT PHASE → 6h POST-MERGE.** Consult the Phase Dispatch Table. Proceed immediately — do not stop here.

**If `status: error`:**

Notify and STOP.

---

### 6h. POST-MERGE (lead handles directly via Ruby)

**Step 1 — Ruby owns the checkout-and-pull.** After `gh pr merge`, the working tree is still on the feature branch. Returning to `development` and pulling the squashed merge commit is a branch operation, so it goes through Ruby per Section 12. Run:

```bash
OTL_AGENT_SLUG=$OTL_AGENT_SLUG OTL_AGENT_ID=$OTL_AGENT_ID ruby orch/orchestrator.rb finalize --post-merge
```

This Ruby command runs `git checkout development` and `git pull --rebase origin development` directly via `system()`, logs `[orch] git ... (agent: <slug>:<id>)` lines for both, and returns YAML with `data.branch_after: development` on success. Do NOT run `git checkout development` from your Bash tool — that path is denied for agents and bypasses the forensic log.

**Step 2 — Verify Ruby succeeded.** After the Ruby call, confirm the working tree is on `development`:

```bash
git branch --show-current
```

- **If output is exactly `development`:** proceed.
- **If output is anything else:** STOP. The Ruby `--post-merge` step failed silently or another session has flipped the branch. Output a `clarification_needed` block with the unexpected branch name. Do NOT run `git checkout development` to "fix" it — that defeats the forensic trail and re-introduces the silent-flip class of bug Section 12 is designed to prevent. Operator triages.

Verify OpenSpec was archived:

```bash
openspec list
```

Mark queue complete and reset state:

```bash
ruby orch/orchestrator.rb queue complete --prd-path "[prd_path]"
ruby orch/orchestrator.rb state reset
```

**Emit final TodoWrite — all eight phases completed** (render-layer plan strip shows ✓ across the board):

```
TodoWrite(todos=[
  {"content": "Proposal", "status": "completed", "activeForm": "Running Proposal"},
  {"content": "Build", "status": "completed", "activeForm": "Running Build"},
  {"content": "Compliance", "status": "completed", "activeForm": "Running Compliance"},
  {"content": "Simplify", "status": "completed", "activeForm": "Running Simplify"},
  {"content": "Test", "status": "completed", "activeForm": "Running Test"},
  {"content": "Smoke", "status": "completed", "activeForm": "Running Smoke"},
  {"content": "Finalize", "status": "completed", "activeForm": "Running Finalize"},
  {"content": "Post-merge", "status": "completed", "activeForm": "Running Post-merge"}
])
```

**NEXT PHASE: Return to Step 6a NOW — DO NOT STOP TO ASK.** Consult the Phase Dispatch Table. Post-merge routes to Step 6a (QUEUE NEXT), NOT Step 7. Step 7 is only reachable when Step 6a finds `queue_empty: true`.

**Hard rule for the lead — no operator gate between PRDs:**

After post-merge, you go DIRECTLY to Step 6a. Do not pause. Do not summarise. Do not ask the operator "should I continue?" or "do you want me to do the next one?" or offer numbered options. The operator launched the queue worker — that authorises processing the entire queue end-to-end until empty. Asking permission between PRDs is a protocol violation, not caution.

PRDs may be added to the queue mid-run (this is a sanctioned use case). You discover them by calling `queue next` at Step 6a — that is the ONLY signal that controls whether to continue or finish. `queue_empty: true` → Step 7. Anything else → process it.

Even if the just-completed PRD had problems (merge conflicts, hung scripts, scope creep findings, retries), that is NOT a reason to stop the queue. Those issues were resolved in their own phase. The next PRD is a fresh run. If the operator wants to halt, they will say so — silence is consent to continue.

---

## Step 7: Pipeline Complete (only reachable from Step 6a when queue is empty)

Generate usage report:

```bash
ruby orch/orchestrator.rb usage complete --format table
```

Archive and cleanup:

```bash
ruby orch/orchestrator.rb queue archive
ruby orch/orchestrator.rb state delete
ruby orch/orchestrator.rb usage delete
```

Send completion notification:

```bash
ruby orch/notifier.rb complete --change-name "[last_change_name]" --message "All PRDs processed"
```

Display summary using the PRD results manifest accumulated during the processing loop (Step 6):

```
═══════════════════════════════════════════
  ORCHESTRATION COMPLETE
═══════════════════════════════════════════

Queue Summary:
  Completed: [N] PRDs
  Failed:    [N] PRDs

PRDs Processed:
  ✓ [prd_path] — PR #[N]
  ✓ [prd_path] — PR #[N]
  ✗ [prd_path] — [failure reason]

Cleanup:
  ✓ Usage report generated
  ✓ Queue archived
  ✓ State file deleted

Ready for next orchestration run.
═══════════════════════════════════════════
```

For each completed PRD, show its `prd_path` and the PR number/URL from the finalize result. For failed PRDs, show the `prd_path` and the failure reason. Use ✓ for completed and ✗ for failed.

---

## Error Handling

On any unexpected error during lead operations — **first** emit a TodoWrite that flips the currently-active phase's `content` to the `(failed)` suffix with `status: in_progress` (per the Canonical Orchestration Plan contract). Then:

```bash
ruby orch/notifier.rb error --change-name "[change_name]" --message "[error]" --phase "[phase]" --resolution "[fix]"
```

Update state with current phase so resume detection works, then STOP. Restarting the lead will detect the state and resume from the correct phase.

---

## How Workers Are Spawned — Reference

```
1. Read worker file: Read(".claude/commands/otl/orch/[N]-[name].md")
2. Construct prompt: worker_instructions + "\n\n## Context\n- change_name: X\n- prd_path: Y\n- branch: Z\n- bulk_mode: [true/false] (for proposal worker only)"
3. Spawn: Task(subagent_type="general-purpose", prompt=constructed_prompt, description="[Phase] for X")
4. Parse YAML result block from worker output (proposal_result, build_result, compliance_result, simplify_result, test_result, smoke_result, finalize_result)
5. Decide next action based on result status
```
