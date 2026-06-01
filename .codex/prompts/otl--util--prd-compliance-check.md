---
description: Focused PRD-to-implementation compliance check. Verifies requirements
  were built correctly, OpenSpec artifacts align, and no scope creep occurred. Run
  after build, before merge — kills the remediation PRD cycle.
---

# PRD Compliance Check

**You are performing a focused compliance check of a specific PRD against its implementation.** This is not a broad codebase audit — it is a targeted verification that what was specified is what was built, nothing more, nothing less.

**Purpose:** Catch implementation drift BEFORE merge so remediation PRDs are never needed.

**This is a read-only analysis.** Do not modify any code or specifications. Produce actionable findings for human review.

---

## Input

The user provides:
- **PRD path** (required) — the PRD file to check against
- **Change name** (optional) — the OpenSpec change name. If not provided, attempt to derive it from the PRD filename or ask.
- **Branch** (optional) — the feature branch. If not provided, use the current branch.

If the PRD path is not provided, ask for it:

```bash
find docs/prds -name "*.md" -not -path "*/done/*" | sort
```

---

## Step 1: Read the PRD — Build the Requirements Inventory

Read the full PRD:

```bash
cat [prd_path]
```

Extract EVERY discrete requirement into a flat checklist. For each requirement, capture:

- **ID** — sequential number (R1, R2, R3...)
- **Requirement** — what must be true
- **Source section** — where in the PRD it appears
- **Type** — functional, constraint, acceptance criterion, scope boundary, or explicit exclusion
- **Signal** — MUST/SHOULD/MAY if stated, otherwise infer from context

**Be exhaustive.** Every acceptance criterion, every functional requirement, every constraint, every explicit scope item. If the PRD says "status transitions follow exactly this 5-state flow," that's a requirement. If it says "do NOT modify the existing X," that's a constraint.

Also extract:
- **Explicit scope boundaries** — what's in scope AND what's explicitly out of scope
- **Constraints** — hard rules that must not be violated
- **Non-functional requirements** — performance, security, compatibility if specified

Display the inventory:

```
Requirements Inventory ([N] items from [prd_filename]):
  R1  [MUST]  [functional]   Status field added to model          (Section: Requirements)
  R2  [MUST]  [constraint]   No direct IDEA→PUBLISHED transition  (Section: Constraints)
  R3  [MUST]  [acceptance]   API returns new field in response     (Section: Acceptance Criteria)
  ...
```

---

## Step 2: Check OpenSpec Artifacts

If an OpenSpec change exists for this PRD, verify the spec artifacts are faithful to the PRD.

```bash
ls openspec/changes/[change_name]/ 2>/dev/null || ls openspec/changes/archive/[change_name]/ 2>/dev/null
```

### 2a. Proposal Alignment

Read `proposal.md`. For each requirement in the inventory:
- Is it addressed in the proposal?
- Is the proposed approach consistent with the requirement?
- Were any requirements reinterpreted, softened, or dropped during proposal?

### 2b. Task Coverage

Read `tasks.md`. For each requirement:
- Is there a task that implements this requirement?
- Are there tasks that don't trace to any PRD requirement? (scope creep in task decomposition)

### 2c. Spec Accuracy

Read `spec.md` and any files under `specs/`. Verify:
- ADDED items match PRD additions
- MODIFIED items match PRD changes
- REMOVED items match PRD removals
- No spec items that aren't in the PRD

### 2d. Compliance Report (if exists)

Read `compliance-report.md` if it exists. Note any issues flagged during finalize.

Record findings:

```
OpenSpec Alignment:
  proposal.md:  [N/N requirements addressed, M reinterpreted]
  tasks.md:     [N/N requirements covered, M orphan tasks]
  spec.md:      [N/N deltas accurate, M mismatches]
```

---

## Step 3: Check Implementation Against PRD

This is the core check. For EACH requirement in the inventory:

### 3a. Trace to Code

1. Identify where this requirement should be implemented (model, service, route, template, JS, migration)
2. Read the actual code
3. Assess:

| Status | Meaning |
|--------|---------|
| **PASS** | Requirement is fully implemented as specified |
| **PARTIAL** | Some aspects implemented, others missing |
| **FAIL** | Not implemented, or implemented differently than specified |
| **VIOLATED** | A constraint that was explicitly broken |
| **N/A** | Requirement doesn't apply (e.g., out-of-scope item correctly excluded) |

4. For PARTIAL, FAIL, and VIOLATED — document exactly what's wrong:
   - What the PRD says
   - What the code does
   - The specific file and line where the divergence occurs

### 3b. Verify Wiring

For implemented requirements, verify the code is actually reachable:
- Service registered in `app.extensions`?
- Route blueprint registered?
- Function called from somewhere?
- Template rendered?
- JS loaded and invoked?

**Built-but-not-wired is a common agent failure mode.** A requirement can look "implemented" in the service layer but never actually work because nothing calls it.

---

## Step 4: Scope Creep Check

Check the implementation for things that were NOT specified.

### 4a. Diff Analysis

```bash
git diff --name-only origin/development...HEAD 2>/dev/null || git diff --name-only HEAD~10...HEAD
```

For each changed file, determine:
- Does the change trace to a specific PRD requirement?
- Is it necessary infrastructure (migration, config, test) for a PRD requirement?
- Or is it an addition the agent invented?

### 4b. Classify Additions

| Type | Action |
|------|--------|
| **Traces to PRD** | Expected — no issue |
| **Supporting infrastructure** | Expected — migration, config for a PRD requirement |
| **Test code** | Expected — tests for PRD requirements |
| **Scope creep** | Agent added features not in the PRD |
| **Adjacent "improvement"** | Agent "improved" nearby code while implementing |
| **Spec artifact** | OpenSpec files — expected |

Flag scope creep and adjacent improvements specifically.

---

## Step 5: Produce the Report

Write to `docs/reviews_remediation/prd-compliance/[change_name]-YYYY-MM-DD.md`:

```bash
mkdir -p docs/reviews_remediation/prd-compliance
```

### Report Format

```markdown
# PRD Compliance Check — [change_name]

**Date:** YYYY-MM-DD
**PRD:** [prd_path]
**Branch:** [branch]
**OpenSpec Change:** [change_name]

## Verdict: [COMPLIANT / NON-COMPLIANT / PARTIAL]

[1-2 sentence summary. Be direct — is the implementation faithful to the PRD or not?]

---

## Requirements Scorecard

| Status | Count | Percentage |
|--------|-------|------------|
| PASS | N | N% |
| PARTIAL | N | N% |
| FAIL | N | N% |
| VIOLATED | N | N% |
| N/A | N | N% |
| **Total** | **N** | |

---

## Failures and Violations

[For each FAIL or VIOLATED requirement — the critical section. These are what would have required a remediation PRD.]

### R[N]: [requirement summary]
- **PRD says:** [exact requirement]
- **Code does:** [what was actually built]
- **Location:** [file:line]
- **Impact:** [what breaks or is missing because of this]
- **Fix:** [specific action to resolve]

---

## Partial Implementations

[For each PARTIAL requirement — what's done and what's missing]

### R[N]: [requirement summary]
- **Implemented:** [what was built]
- **Missing:** [what's still needed]
- **Location:** [file:line]
- **Fix:** [specific action to complete]

---

## Scope Creep

[Additions not traceable to any PRD requirement]

| File | Change | Traces to PRD? | Classification |
|------|--------|---------------|----------------|
| path/to/file.py | Added FooHelper class | No | Scope creep — unnecessary abstraction |

---

## OpenSpec Alignment

[Summary of spec artifact accuracy]

- **Proposal:** [aligned / N reinterpretations]
- **Tasks:** [N/N covered, M orphan tasks]
- **Spec deltas:** [accurate / N mismatches]

---

## Passing Requirements

[Collapsed list — just IDs and one-line summaries for requirements that passed]

- R1: PASS — Status field added to model
- R3: PASS — API returns new field
- ...

---

## Recommended Actions

Priority-ordered list of what needs fixing:

1. **[CRITICAL]** R[N]: [requirement] — [what to do]
2. **[CRITICAL]** R[N]: [requirement] — [what to do]
3. **[MODERATE]** R[N]: [requirement] — [what to do]
4. **[CLEANUP]** Remove scope creep: [description]
```

---

## Step 6: Present Summary

After writing the report, present:

- **Verdict** — COMPLIANT / NON-COMPLIANT / PARTIAL
- **Score** — N/N requirements passing
- **Critical failures** — requirements that are FAIL or VIOLATED
- **Scope creep** — any additions not in the PRD
- **OpenSpec alignment** — any spec artifact drift
- **Report location**

**If NON-COMPLIANT:** List the specific fixes needed. These are the things that would otherwise become a remediation PRD. Fix them now, on this branch, before merge.

**Do NOT auto-fix anything.** Present findings for human review. The user decides what to act on.

---

## When to Use This Command

- **After an orchestration build** — before the finalize phase merges. Catches drift while it's still cheap to fix.
- **After manual implementation** — when an agent builds something outside the orchestration pipeline.
- **Spot-checking past work** — point it at a done PRD and the current codebase to find problems that shipped.
- **Before writing a remediation PRD** — run this first. If it identifies the specific failures, you can fix them directly instead of writing another PRD.
