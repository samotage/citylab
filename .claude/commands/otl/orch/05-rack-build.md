---
name: '05: rack-build'
description: 'Validate PRDs, clean the repo, and queue for orchestration build — the pre-build prep sequence'
---

# 05: Rack Build

**Command name:** `05: rack-build`

**Purpose:** Bundle the repeating pre-orchestration prep into one command: identify PRDs, validate them, ensure a clean repo, and queue for build.

---

## Step 1: Identify PRDs

**Try conversation context first.**

Check the current conversation for PRDs that have been discussed, workshopped, or created in this session. Look for:
- PRD file paths mentioned in prior messages
- PRDs created or modified during this conversation
- PRDs referenced from a recent `/otl:prds:10-workshop` run

**If PRDs found in context**, present them:

```
PRDs identified from this session:

1. docs/prds/{subsystem}/{prd-name}.md
2. docs/prds/{subsystem}/{prd-name}.md

Are these the PRDs to build? [y/n]
```

Wait for confirmation.

**If the user says no, or no PRDs found in context**, fall back:

```
No PRDs in conversation context. Scanning the system...
```

Run the PRD list scan:

```bash
find docs/prds -mindepth 2 -name "*.md" -type f | grep -v "/done/" | sort
```

For each PRD found, read the file to extract a one-line summary and check validation status:

```bash
ruby orch/prd_validator.rb status --prd-path [prd-path]
```

Present the list and ask the user to confirm which PRDs to build:

```
Pending PRDs:

1. [✓ Valid] docs/prds/core/my-feature-prd.md — "one-line summary"
2. [⊗ Unvalidated] docs/prds/events/another-prd.md — "one-line summary"

Which PRDs should be queued? (comma-separated numbers, or 'all')
```

Wait for selection.

---

## Step 2: Validate All Selected PRDs

For each selected PRD, run validation:

```bash
ruby orch/prd_validator.rb status --prd-path [prd-path]
```

**If already `valid`:** skip re-validation, note it passed.

**If `unvalidated` or `invalid`:** run the full validation sequence as per `/otl:prds:30-validate` — perform all 7 checks (format compliance, gap detection, requirement focus, conflict detection, scope assessment, ambiguity check, orchestration readiness).

Update frontmatter with results:

```bash
# On PASS
ruby orch/prd_validator.rb update --prd-path [prd-path] --status valid

# On FAIL
ruby orch/prd_validator.rb update --prd-path [prd-path] --status invalid --errors "Error 1,Error 2"
```

**EXIT CONDITION:** If ANY PRD fails validation (FAIL or BLOCKED status), stop and report:

```
VALIDATION FAILED — cannot proceed.

Failed PRDs:
- docs/prds/{subsystem}/{prd}.md — [reason]

Remediation:
  /otl:prds:10-workshop [prd-path]   (guided fix)
  Edit manually, then re-run /otl:orch:05-rack-build
```

Do NOT continue to Step 3. The command exits here.

---

## Step 3: Clean the Repo

All PRDs validated. Now ensure the working tree is clean before queuing.

Run `/otl:util:commit-push` — this stages all changes, generates a commit message from the diff, commits, and pushes. No approval checkpoint.

**If commit-push reports "No changes to commit":** the repo is already clean. Continue.

**If commit-push fails:** report the error and stop. Do not proceed with a dirty tree.

---

## Step 4: Queue for Build

All PRDs validated, repo clean. Add to the orchestration queue.

For each validated PRD path, run:

```bash
ruby orch/orchestrator.rb queue add --prd-path "[prd-path]"
```

If multiple PRDs:

```bash
ruby orch/orchestrator.rb queue add --paths "[comma-separated-paths]"
```

Then show queue status:

```bash
ruby orch/orchestrator.rb queue status
```

---

## Step 5: Summary

```
Rack Build Complete
───────────────────
Validated: [N] PRDs (all passed)
Committed: [commit hash] — [commit subject]
Queued:    [N] PRDs added to orchestration queue

Next: /otl:orch:20-start-queue-process
```

---

## Notes

- This command wraps validate + commit-push + queue-add into one flow
- It does NOT start the orchestration build itself — that remains a separate step (`/otl:orch:20-start-queue-process`)
- The validation gate is strict: one failure stops the entire run
- Already-valid PRDs are not re-validated (trust the frontmatter timestamp)
