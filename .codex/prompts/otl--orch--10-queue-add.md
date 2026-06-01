---
description: Add PRDs to the processing queue
---

# Queue Add

Add one or more PRDs to the orchestration processing queue.

**Input:** `{{prd_paths}}` — comma-separated PRD file paths, or a single path.

---

## Step 1: Get PRD Paths

If `{{prd_paths}}` is empty or a placeholder:

Ask the user:

```
Please provide the PRD file path(s) to add to the queue.

Single:   docs/prds/persona/my-feature-prd.md
Multiple: docs/prds/persona/feature-1-prd.md,docs/prds/persona/feature-2-prd.md
```

Wait for their response.

If paths are provided, continue.

---

## Step 2: Verify Files Exist

For each path in `{{prd_paths}}` (split by comma):
- Check the file exists
- If any file is missing, report the error and ask for the correct path

---

## Step 3: Completed PRD Gate

**Check BEFORE validation — a PRD in `done/` has already been through the pipeline.**

For each path in `{{prd_paths}}`:

If the path contains `/done/` (e.g. `docs/prds/events/done/my-feature-prd.md`):

```
BLOCKED: [prd_path]

This PRD is in a done/ directory — it was already completed by a prior
orchestration run. Re-processing it will create a ghost branch with
stale commits that conflict with development.

If you need to re-run this PRD:
  1. Move it back to the active directory: docs/prds/[subsystem]/
  2. Re-run this command with the new path
```

Do NOT add it to the queue. If multiple PRDs were provided, continue checking the rest — add only those not in `done/`.

---

## Step 4: Validation Gate

**Run this check for every PRD — do not skip or assume status from memory.**

For each PRD, run:

```bash
ruby orch/prd_validator.rb status --prd-path [prd_path]
```

**BLOCKING GATE:** If any PRD has status `invalid` or `unvalidated`, do NOT add it to the queue:

```
Cannot add to queue: [prd_path]
Validation Status: [invalid/unvalidated]

Validate first:
  1. Run /otl:prds:30-validate [prd_path]
  2. If it fails, run /otl:prds:10-workshop [prd_path] to remediate
  3. After passing, re-run this command
```

Do not add invalid/unvalidated PRDs. If multiple PRDs were provided, ask if the user wants to proceed with the valid ones.

---

## Step 5: Add to Queue

For a single PRD:

```bash
ruby orch/orchestrator.rb queue add --prd-path "{{prd_paths}}"
```

For multiple PRDs:

```bash
ruby orch/orchestrator.rb queue add --paths "{{prd_paths}}"
```

---

## Step 6: Show Status

```bash
ruby orch/orchestrator.rb queue status
```

Display summary:

```
PRD Queue Updated
─────────────────
Added:   [N]
Skipped: [N] (already in queue)

Queue: [N] pending, [N] in progress, [N] completed
```
