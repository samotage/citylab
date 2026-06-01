---
name: '05: rack-build'
description: 'Validate PRDs, then queue and launch the hackathon orchestration pipeline'
---

# Hackathon Rack Build

Prep-and-go entry point: validate PRDs have the required sections, then launch the orchestration pipeline.

**Usage:**

```
/otl:orch:05-rack-build docs/prds/core/bootstrap.md
/otl:orch:05-rack-build docs/prds/core/bootstrap.md,docs/prds/features/dashboard.md
```

---

## Steps

### 1. Parse PRD list

Split the argument on commas. For each path, verify the file exists:

```bash
test -f [prd_path] && echo "OK: [prd_path]" || echo "MISSING: [prd_path]"
```

If any PRD is missing, report which ones and STOP.

### 2. Validate PRD format

For each PRD, check that all four required sections exist:

```bash
grep -c "^## Problem\|^## Approach\|^## Done When\|^## Demo Script" [prd_path]
```

Expected: 4 matches. If fewer:

```
⚠ [prd_path] is missing sections:
  ✗ Problem (missing)
  ✓ Approach
  ✗ Done When (missing)
  ✓ Demo Script
```

**Missing sections are a warning, not a blocker.** The bootstrap PRD and other complex PRDs may use different heading structures. Report what's missing but continue unless the file is empty or unreadable.

### 3. Check for already-completed PRDs

For each PRD, check if it's already in a `done/` directory:

```bash
echo "[prd_path]" | grep -q "/done/" && echo "DONE" || echo "ACTIVE"
```

Remove any `done/` PRDs from the list with a warning. If no active PRDs remain, STOP.

### 4. Check repo state

```bash
git status --short
git branch --show-current
```

Report any uncommitted changes. The pipeline creates feature branches, so a dirty working tree should be committed or stashed first. If there are uncommitted changes, ask the operator: commit them, stash them, or abort.

### 5. Display summary and launch

```
═══════════════════════════════════════════
  HACKATHON RACK BUILD
═══════════════════════════════════════════

PRDs to process:
  1. docs/prds/core/bootstrap.md ✓
  2. docs/prds/features/dashboard.md ✓

Repo: clean, on master
Pipeline: 5-phase (Propose → Build → Test → Smoke → Ship)

Launching orchestration...
═══════════════════════════════════════════
```

### 6. Launch the pipeline

Invoke the orchestration lead with the validated PRD list:

```
Skill("otl:orch:20-start-queue-process", args="[comma-separated-prd-paths]")
```
