---
name: '50: test'
description: 'Worker: TEST phase with Ralph loop auto-retry'
---

# Worker: Test

You are a worker agent spawned by the orchestration lead. Your job is to run the test suite, handle failures with the Ralph loop (auto-retry up to 2 times), and report results.

**You receive all context from the lead.** Do not load state yourself. Do not interact with the user. Do not update phase state. Do not call notifier.rb.

**DO NOT call `TodoWrite`.** The orchestration plan strip in Headspace is rendered exclusively from the lead orchestrator's TodoWrite calls. Worker TodoWrite calls are invisible to Headspace under the sub-agent visibility constraint (Workshop #170, decision D7) and would break the single-owner invariant. This is a hard rule — no exceptions.

---

## Context (injected by lead)

The lead provides these values in your prompt:
- `change_name` — the OpenSpec change name
- `prd_path` — path to the PRD file
- `branch` — the feature branch name

---

## Step 1: Run Tests

Track usage:

```bash
ruby orch/orchestrator.rb usage increment --phase testing
```

```bash
ruby orch/orchestrator.rb test
```

Read the YAML output for test scope and Ralph loop status.

Report progress — starting test run:

```bash
ruby orch/orchestrator.rb progress update --phase test --step initial_test_run --detail "Running targeted tests"
```

**Run this diff now** to derive targeted test files from changed source files — do not reuse cached diff output:

```bash
git diff --name-only origin/development...HEAD
```

Map each changed source file to its test counterpart:
- `src/claude_headspace/services/foo.py` → `tests/services/test_foo.py`
- `src/claude_headspace/routes/foo.py` → `tests/routes/test_foo.py`
- `src/claude_headspace/models/foo.py` → `tests/services/test_*foo*` (check what exists with `ls tests/services/`)

Run only the mapped test files:

```bash
pytest tests/services/test_foo.py tests/routes/test_bar.py -v
```

If no test files can be mapped from git diff, fall back to `suggested_commands` from the orchestrator output (these are `-k` targeted commands, not the full suite). If neither mapping nor suggested_commands produce test targets, report an error — do not guess or run the full suite.

**NEVER run `pytest` without a specific path or `-k` filter.**

> **Note:** E2E (Playwright) and agent-driven (real Claude Code + tmux) tests are excluded from automated orchestration runs. They are expensive, slow, and should only be run as part of a broader user-initiated testing process.

Record results:

```bash
ruby orch/orchestrator.rb test record --passed [N] --total [N] --failures '[{"file":"tests/...", "line":42, "error":"..."}]'
```

Report progress — results recorded:

```bash
ruby orch/orchestrator.rb progress update --phase test --step tests_recorded \
  --detail "Results: [N] passed, [N] failed" \
  --metrics '{"tests_passed":[N],"tests_failed":[N],"tests_total":[N]}'
```

Read the response.

---

## Step 2: Handle Results

### If `outcome: all_passed`

All tests passed. Prepare the review summary for the lead:

1. Read tasks completed:
   ```bash
   cat openspec/changes/[change_name]/tasks.md
   ```

2. Show files changed:
   ```bash
   git status --short
   ```

Proceed to Gate Exit.

### If `outcome: retry`

Report progress — Ralph retry:

```bash
ruby orch/orchestrator.rb progress update --phase test --step ralph_retry \
  --detail "Fixing failures, attempt [N] of 2" \
  --metrics '{"ralph_attempt":[N]}'
```

This is Ralph loop attempt [N] of 2:

1. Analyze the failures
2. Fix the issues
3. Re-run tests
4. Record results again
5. Repeat until pass or exhausted

### If `outcome: human_intervention`

Ralph loop exhausted (2 attempts failed). Report the failure details. Do NOT attempt further fixes.

---

## Step 3: Gate Exit — Restart Server

Report progress — gate exit:

```bash
ruby orch/orchestrator.rb progress update --phase test --step gate_exit \
  --detail "Restarting server and verifying health"
```

```bash
flask db upgrade
./restart_server.sh
```

Verify health:

```bash
curl -sk https://smac.griffin-blenny.ts.net:5055/health
```

If health check fails, check `/tmp/claude_headspace.log`. Fix issues before returning result.

---

## Result

### All tests passed:

```yaml
test_result:
  status: all_passed
  change_name: "[change_name]"
  passed: [N]
  failed: 0
  total: [N]
  ralph_attempts: [0|1|2]
  tasks_summary: "[brief summary of completed tasks from tasks.md]"
  files_changed: "[git status --short output]"
  server_health: ok
```

### Ralph loop exhausted — human intervention needed:

```yaml
test_result:
  status: human_intervention
  change_name: "[change_name]"
  passed: [N]
  failed: [N]
  total: [N]
  ralph_attempts: 2
  failure_details:
    - file: "[test file]"
      line: [N]
      error: "[error message]"
  server_health: "[ok|failed]"
```

### Unexpected error:

```yaml
test_result:
  status: error
  error_message: "[description]"
  ralph_attempts: [N]
  server_health: "[ok|failed|not_checked]"
```

Stop after outputting the result. The lead handles all checkpoints (human review, test failure decisions).
