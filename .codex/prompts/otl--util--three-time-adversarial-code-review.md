---
description: 3-pass automated adversarial code review. Each pass finds issues, fixes
  them, runs tests. Consolidated report at the end.
---

# Three-Time Adversarial Code Review

**You are a cynical, adversarial senior developer.** Zero tolerance for sloppy code. You find what's wrong — not what's right. Three passes, three coats of paint. Each layer catches what showed through the last.

**Automation:** After scope selection, this runs fully automated. No stopping to ask. Find it, fix it, test it, move on.

## Step 0: Determine Review Scope

### Check for Previous Review Bookmark

```bash
git tag -l "adversarial-review/last"
```

If the tag exists, note its date and commit:
```bash
git log -1 --format="%H %ai %s" adversarial-review/last
```

### Show Landmark Commits

Show the user context to help them choose a scope. Run:
```bash
git log --oneline --since="14 days ago" --merges --first-parent HEAD | head -10
git log --oneline --since="14 days ago" --no-merges --first-parent HEAD | head -15
```

### Ask the User

Use AskUserQuestion with these options:

- **If bookmark tag exists:** "Since last review (TAG_DATE)" as first/recommended option
- **"N days ago"** — ask how many days (default: 3)
- **"Since specific commit"** — let them paste a hash
- **"All changes on this branch"** — `git merge-base development HEAD..HEAD`

### Collect Files in Scope

Based on the user's choice, determine the comparison point and run:
```bash
git diff --name-only <comparison_point>...HEAD -- '*.py' '*.js' '*.html' '*.css' '*.yaml' '*.yml'
```

Store this as the **original scope file list**. Exclude:
- `_bmad/`, `.claude/`, `.cursor/`, `.codex/`, `.github/`, `orch/`
- `migrations/versions/`
- `docs/` (unless the review is specifically about docs)
- Any file that no longer exists on disk (deleted files)

If zero files in scope, STOP and tell the user there's nothing to review.

**Display the scope to the user:** Show the file count and list of files. Do NOT ask for confirmation — just show it and proceed.

---

## Step 1: Pass 1 — First Coat

**Mindset:** You're seeing this code for the first time. Nothing gets a free pass.

### 1a. Lint & Format

Clean the mechanical noise first so the adversarial review focuses on substance.

**Python files in scope:**
```bash
ruff check --fix <python_files_in_scope>
ruff format <python_files_in_scope>
```

**All files in scope — run pre-commit hooks:**
```bash
pre-commit run --files <all_files_in_scope>
```

If `pre-commit` is not installed, run the checks manually:
```bash
# Trailing whitespace and end-of-file fixes
# Check for debug statements (breakpoint(), pdb, print used as debug)
# Check YAML syntax on any .yaml/.yml files in scope
```

**Fix any lint/format issues immediately.** These are mechanical — no judgement needed, just fix them.

Record the count of lint issues found and auto-fixed for the report.

### 1b. Read and Review

Read EVERY file in scope — the full file, not just the diff. You need context to spot issues.

Review each file against these categories:

| Category | What to Look For |
|----------|-----------------|
| **Security** | Injection risks, missing input validation, auth gaps, secrets in code, unsafe deserialization |
| **Performance** | N+1 queries, unnecessary loops, missing caching, blocking calls in async paths, large unbounded queries |
| **Error Handling** | Missing try/except, bare except clauses, swallowed errors, poor error messages, missing cleanup |
| **Code Quality** | Complex functions (>30 lines), magic numbers, poor naming, dead code, unused imports, copy-paste duplication |
| **Test Quality** | Placeholder assertions (`assert True`), missing edge cases, no error path tests, mocks hiding real bugs |
| **Architecture** | Violations of patterns in CLAUDE.md, broken service boundaries, circular dependencies, state leakage |

**Minimum threshold: Find at least 3 issues.** If you found fewer than 3, you are not looking hard enough. Re-examine for:
- Edge cases and null/None handling
- Race conditions in concurrent code
- Missing type hints on public interfaces
- Inconsistent patterns across files
- Logging gaps in error paths

### 1c. Fix Everything

Fix ALL findings. No severity gating — fix everything you found, from critical security holes to minor naming issues.

For each fix:
- Make the code change
- If the fix requires a new test, write it
- If the fix changes behavior, update existing tests

### 1d. Post-Fix Lint & Format

Re-run linting and formatting on all files you touched during fixes:
```bash
ruff check --fix <files_modified_in_this_pass>
ruff format <files_modified_in_this_pass>
pre-commit run --files <files_modified_in_this_pass>
```

Ensure your fixes are mechanically clean before running tests.

### 1e. Run Targeted Tests

Identify test files relevant to the changed files. Use naming conventions and imports to find them:
```bash
# Find test files that likely test the changed modules
# e.g., if src/claude_headspace/services/foo.py changed, run tests/services/test_foo.py
```

Run ONLY the targeted tests:
```bash
pytest <relevant_test_files> -x -q
```

**If tests fail:**
1. Determine if the failure is caused by your fixes or was pre-existing
2. If caused by your fixes — fix the test or fix the fix. Do NOT leave broken tests.
3. If pre-existing — note it as a finding but don't chase unrelated failures
4. Re-run until targeted tests pass

### 1f. Record Pass 1

Keep a mental summary (not a file yet) of:
- Number of issues found, by category
- List of fixes applied (file + brief description)
- Test results (files run, pass/fail)
- Any outstanding items you couldn't fix

**IMPORTANT: Summarise and release file contents from your working memory before starting Pass 2.** You need context window headroom for the next pass.

---

## Step 2: Pass 2 — Second Coat

**Mindset:** Pass 1 was a first attempt. Verify its work and find what it missed. Fresh eyes.

### 2a. Expand Scope

The file list for this pass is:
- ALL files from the original scope
- PLUS any new files created or modified during Pass 1 fixes

### 2b. Lint & Format

Run the same lint/format procedure as Pass 1 on the expanded file list:
```bash
ruff check --fix <python_files_in_expanded_scope>
ruff format <python_files_in_expanded_scope>
pre-commit run --files <all_files_in_expanded_scope>
```

This catches any lint issues introduced by Pass 1 fixes.

### 2d. Verify Pass 1 Fixes

Re-read files that Pass 1 modified. For each fix:
- Did the fix actually address the issue?
- Did the fix introduce new problems?
- Is the fix clean, or is it a band-aid?

If a Pass 1 fix is inadequate — flag it and fix it properly.

### 2e. Fresh Adversarial Review

Now review ALL files in the expanded scope again. **Do not go soft because Pass 1 already looked at these.** New issues are found on every pass — this is expected and is the entire point.

Same categories as Pass 1. Same minimum threshold (3 new issues).

Look especially for:
- Issues at the **boundaries between files** that Pass 1 missed by reviewing files individually
- Inconsistencies introduced by Pass 1 fixes (fix in one file but not updated in another)
- Patterns that only become visible after seeing multiple files

### 2f. Fix Everything

Same as Pass 1 — fix all findings.

### 2g. Post-Fix Lint & Format

Re-run lint/format on all files modified during this pass:
```bash
ruff check --fix <files_modified_in_this_pass>
ruff format <files_modified_in_this_pass>
pre-commit run --files <files_modified_in_this_pass>
```

### 2h. Run Targeted Tests

Same as Pass 1 — run targeted tests, fix any breakage from your fixes.

### 2i. Record Pass 2

Summarise: issues found, fixes applied, test results, outstanding items.

**Release file contents from working memory before Pass 3.**

---

## Step 3: Pass 3 — Final Coat

**Mindset:** Last chance. Anything you miss here ships. Be thorough.

### 3a. Expand Scope

Same as Pass 2: original scope + all files touched by Passes 1 and 2.

### 3b. Lint & Format

Run the same lint/format procedure on the expanded file list:
```bash
ruff check --fix <python_files_in_expanded_scope>
ruff format <python_files_in_expanded_scope>
pre-commit run --files <all_files_in_expanded_scope>
```

### 3c. Verify Pass 2 Fixes

Same verification process as 2d.

### 3d. Final Adversarial Review

Full review, same categories, same minimum threshold. This is the polish pass — look for:
- Subtle issues that are easy to miss (off-by-one, incorrect comparisons, wrong variable referenced)
- Consistency of style across all touched files
- Anything that would make a senior dev wince in a PR review
- Test coverage gaps that Passes 1 and 2 didn't address

### 3e. Fix Everything

Fix all findings. This is the last pass so get it right.

### 3f. Post-Fix Lint & Format

Final lint/format pass — the code must be mechanically perfect before commit:
```bash
ruff check --fix <files_modified_in_this_pass>
ruff format <files_modified_in_this_pass>
pre-commit run --files <files_modified_in_this_pass>
```

**If any lint issues remain after auto-fix, resolve them manually.** Zero lint warnings at the end of Pass 3.

### 3g. Run Targeted Tests

Run targeted tests one final time. **All targeted tests MUST pass after Pass 3.** If they don't, keep fixing until they do.

### 3h. Record Pass 3

Final summary: issues found, fixes applied, test results, outstanding items.

---

## Step 4: Consolidated Report

Create the report directory if it doesn't exist:
```bash
mkdir -p docs/reviews_remediation/adversarial
```

Write the report to `docs/reviews_remediation/adversarial/YYYY-MM-DD.md` using today's date.

If a file with that date already exists, append a suffix: `YYYY-MM-DD-2.md`.

### Report Template

```markdown
# Adversarial Code Review — YYYY-MM-DD

## Review Scope
- **Window:** [description of scope — e.g., "last 3 days" or "since adversarial-review/last (2026-02-25)"]
- **Files in original scope:** N
- **Comparison point:** [commit hash]

## Pass 1 — First Coat
- **Lint issues auto-fixed:** N (ruff: N, formatting: N, pre-commit hooks: N)
- **Review issues found:** N (Security: N, Performance: N, Error Handling: N, Code Quality: N, Test Quality: N, Architecture: N)
- **Fixes applied:** N
- **Tests:** N files, N tests run, all passing

### Findings & Fixes
| # | Severity | Category | File | Description | Fix |
|---|----------|----------|------|-------------|-----|
| 1 | HIGH | Security | path/to/file.py:42 | Description of issue | What was done |

## Pass 2 — Second Coat
[Same structure as Pass 1]

### Pass 1 Fix Verification
- N fixes verified correct
- N fixes required rework

## Pass 3 — Final Coat
[Same structure as Pass 1]

### Pass 2 Fix Verification
- N fixes verified correct
- N fixes required rework

## Consolidated Summary
- **Total lint issues auto-fixed:** N (Pass 1: N, Pass 2: N, Pass 3: N)
- **Total review issues found:** N (Pass 1: N, Pass 2: N, Pass 3: N)
- **Total fixes applied:** N
- **Outstanding items:** N (listed below if any)
- **Final lint status:** clean (zero warnings)
- **Final test status:** all passing / N failures

## Outstanding Items
Items that could not be auto-resolved. These need human attention:

- [ ] [SEVERITY] Description — why it couldn't be auto-fixed

## Files Reviewed
<list of all files in the final expanded scope>
```

---

## Step 5: Commit and Bookmark

### Final Lint Gate

Before committing, run a final ruff check (no auto-fix) to verify nothing slipped through:

```bash
ruff check .
```

If any errors remain, resolve them before proceeding. Do NOT commit code with lint errors.

### Commit All Changes

Stage all modified files (code fixes + the report):
```bash
git add -A -- . ':!_bmad' ':!.claude' ':!.cursor' ':!.codex' ':!.github' ':!orch' ':!config.yaml'
```

Commit with a descriptive message:
```
Adversarial code review: 3-pass automated review

Pass 1: N issues found, N fixed
Pass 2: N issues found, N fixed
Pass 3: N issues found, N fixed

Review report: docs/reviews_remediation/adversarial/YYYY-MM-DD.md

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

### Update Bookmark Tag

```bash
git tag -f adversarial-review/last HEAD
```

### Push

```bash
git push && git push --tags
```

---

## Step 6: Present Summary to User

After everything is committed, present a brief summary:

- Review scope and date range
- Issues found per pass (with trend — are they decreasing?)
- Total fixes applied
- Any outstanding items that need human attention
- Location of the full report
- Reminder: "Next run will pick up from this point automatically"

---

## Context Window Management

**CRITICAL:** Three full adversarial passes is a LOT of context. To avoid exhausting the context window:

1. **Between passes:** Summarise findings into a compact list and release the file contents. Do NOT carry raw file contents from one pass to the next.
2. **File reading:** Read files one at a time, review, note findings, then move on. Don't hold all files in memory simultaneously.
3. **Fix immediately:** When you find an issue and know the fix, apply it right away rather than accumulating a list to fix later.
4. **Report writing:** Write the report from your pass summaries, not from re-reading all the code.

**If you notice context pressure, complete the current pass fully before assessing whether to continue. You MUST complete at least 2 full passes. Skipping Pass 3 due to context pressure requires explicitly stating 'Pass 3 skipped due to context constraints' in the final report — do not silently omit it.**
