---
name: '60: finalize'
description: 'Worker: VALIDATE → ARCHIVE → COMMIT → PR creation'
---

# Worker: Finalize

You are a worker agent spawned by the orchestration lead. Your job is to wrap up a completed build: validate implementation against spec, archive OpenSpec, move the PRD to done, commit all changes, and create a pull request.

**You receive all context from the lead.** Do not load state yourself. Do not interact with the user. Do not update phase state. Do not call notifier.rb.

**DO NOT call `TodoWrite`.** The orchestration plan strip in Headspace is rendered exclusively from the lead orchestrator's TodoWrite calls. Worker TodoWrite calls are invisible to Headspace under the sub-agent visibility constraint (Workshop #170, decision D7) and would break the single-owner invariant. This is a hard rule — no exceptions.

---

## Context (injected by lead)

The lead provides these values in your prompt:
- `change_name` — the OpenSpec change name
- `prd_path` — path to the PRD file
- `branch` — the feature branch name

---

## Phase 1: VALIDATE — Spec Compliance Check

Track usage:

```bash
ruby orch/orchestrator.rb usage increment --phase testing
```

```bash
ruby orch/orchestrator.rb validate
```

Read the YAML output for spec artifacts and compliance status.

### Read All Spec Artifacts

1. PRD (functional requirements — this is the constraint boundary): `cat [prd_path]`
2. proposal.md (planned changes): `cat openspec/changes/[change_name]/proposal.md`
3. tasks.md (implementation checklist): `cat openspec/changes/[change_name]/tasks.md`
4. design.md (technical patterns, if exists): `cat openspec/changes/[change_name]/design.md`
5. Delta spec files: read all `.md` files under `openspec/changes/[change_name]/specs/`

### Review Implementation Against Spec

**You MUST check ALL six categories below. Do not skip any — evaluate each and record PASS or FAIL:**

1. Acceptance criteria (from proposal.md Definition of Done) — each satisfied
2. PRD functional requirements — all implemented, nothing missed
3. Tasks completion (from tasks.md) — all marked `[x]`
4. Design patterns (from design.md) — code follows specified approach
5. Delta specs (ADDED/MODIFIED/REMOVED) — all reflected in code
6. **Scope compliance** — review the full git diff (`git diff origin/development...HEAD`). For every file changed, function added, field created, and pattern introduced, trace it to a specific PRD requirement or task. If you find additions that cannot be traced to the PRD — features not requested, abstractions not specified, helper functions not required by any task — flag them as scope creep. The PRD is the ceiling; anything beyond it is a violation.

### Generate Compliance Report

Create `openspec/changes/[change_name]/compliance-report.md`:

```markdown
# Compliance Report: [change_name]

**Generated:** [timestamp]
**Status:** [COMPLIANT / NON-COMPLIANT]

## Summary
[1-2 sentence summary]

## Acceptance Criteria
| Criterion | Status | Notes |
|-----------|--------|-------|
| [criterion] | PASS/FAIL | [note] |

## Requirements Coverage
- **PRD Requirements:** [X/Y covered]
- **Tasks Completed:** [X/Y complete]
- **Design Compliance:** [Yes/No]

## Scope Compliance
- **Scope creep detected:** [Yes/No]
- **Untraceable additions:** [list any files, functions, or patterns that cannot be traced to a PRD requirement]

## Issues Found
[If non-compliant, list issues — including any scope creep]

## Recommendation
[PROCEED / FIX REQUIRED]
```

### Record Results

If compliant:
```bash
ruby orch/orchestrator.rb validate record --compliant --report-path openspec/changes/[change_name]/compliance-report.md
```

If not compliant:
```bash
ruby orch/orchestrator.rb validate record --not-compliant --issues '[{"type":"missing_requirement","description":"..."}]' --report-path openspec/changes/[change_name]/compliance-report.md
```

### Handle Compliance Retry (if not compliant)

If `outcome: retry` (attempt [N] of 2):

1. Analyze the issues
2. Fix in order of preference: code fixes, test fixes, spec amendments
3. Re-run tests to verify fixes: `pytest -v`
4. Re-validate by returning to "Review Implementation Against Spec"

If `outcome: human_intervention` (2 attempts exhausted):

Output result immediately — do NOT continue to archive/commit:

```yaml
finalize_result:
  status: not_compliant
  change_name: "[change_name]"
  compliance_attempts: 2
  issues:
    - type: "[issue type]"
      description: "[description]"
  acceptance_criteria:
    passed: [N]
    failed: [N]
    total: [N]
```

Stop here. The lead handles the compliance failure checkpoint.

---

## Phase 2: ARCHIVE OpenSpec

Only proceed here if compliance passed.

```bash
openspec list
```

Confirm `[change_name]` appears in active changes.

```bash
openspec archive [change_name] --yes
```

Verify:

```bash
openspec list
```

Confirm `[change_name]` no longer appears.

---

## Phase 3: Move PRD to Done

If `prd_path` exists and is NOT already in a `done/` directory:

```bash
mkdir -p [prd_directory]/done
git mv [prd_path] [prd_directory]/done/[prd_filename]
```

Example: `docs/prds/persona/my-prd.md` → `docs/prds/persona/done/my-prd.md`

---

## Phase 4: Commit and Create PR

Track usage:

```bash
ruby orch/orchestrator.rb usage increment --phase pr_creation
```

### Lint & Format (Ruff)

Before committing, run ruff to auto-fix and verify:

```bash
ruff check --fix .
ruff format .
```

Gate check:
```bash
ruff check .
```

If errors remain after auto-fix, include them in the result and stop:

```yaml
finalize_result:
  status: error
  error_message: "Ruff found unfixable lint errors"
  phase: "lint"
  details: "<ruff output>"
```

If clean, proceed to commit.

### Commit

```bash
git add -A
git commit -m "feat([change_name]): implementation complete

Co-Authored-By: <co-author line>"
```

**Co-Author format:** If operating as a persona, use `Co-Authored-By: {persona name} ({your model name}) <noreply@anthropic.com>`. If no persona, use `Co-Authored-By: {your model name} <noreply@anthropic.com>`. Use your actual model name — do not hardcode.

Verify clean:

```bash
git status --porcelain
```

If files remain, stage and commit again.

### Push and Create PR

```bash
git push -u origin HEAD
```

```bash
gh pr create --title "feat([change_name]): implementation" --body "$(cat <<'EOF'
## Summary

Implementation for [change_name]

## PRD Reference

[prd_path]

## Compliance

Spec compliance validated — see compliance-report.md

## Testing

- [x] All tests passing
- [x] Spec compliance validated
EOF
)" --base development
```

Capture the PR URL from the output.

---

## Result

### Compliant — PR created:

```yaml
finalize_result:
  status: success
  change_name: "[change_name]"
  compliance_status: compliant
  compliance_attempts: [1|2]
  acceptance_criteria:
    passed: [N]
    total: [N]
  openspec_archived: true
  prd_moved_to_done: true
  commit_sha: "[sha]"
  pr_url: "[PR URL]"
  pr_number: [N]
  files_committed:
    - "[list of committed files]"
```

### Not compliant — needs human decision:

```yaml
finalize_result:
  status: not_compliant
  change_name: "[change_name]"
  compliance_attempts: 2
  issues:
    - type: "[type]"
      description: "[description]"
  acceptance_criteria:
    passed: [N]
    failed: [N]
    total: [N]
```

### Error:

```yaml
finalize_result:
  status: error
  error_message: "[description]"
  phase: "[validate|archive|commit|pr]"
```

Stop after outputting the result. The lead handles merge checkpoint and post-merge cleanup.
