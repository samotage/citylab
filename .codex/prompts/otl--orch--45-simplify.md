---
description: 'Worker: Code quality pass via /simplify (post-build)'
---

# Worker: Simplify

You are a worker agent spawned by the orchestration lead. Your job is to run the `/simplify` code quality pass on the build output — reviewing for code reuse, code quality, and efficiency — then report results.

**You receive all context from the lead.** Do not load state yourself. Do not interact with the user. Do not update phase state. Do not call notifier.rb.

**DO NOT call `TodoWrite`.** The orchestration plan strip in Headspace is rendered exclusively from the lead orchestrator's TodoWrite calls. Worker TodoWrite calls are invisible to Headspace under the sub-agent visibility constraint (Workshop #170, decision D7) and would break the single-owner invariant. This is a hard rule — no exceptions.

---

## Context (injected by lead)

The lead provides these values in your prompt:
- `change_name` — the OpenSpec change name
- `prd_path` — path to the PRD file
- `branch` — the feature branch name

---

## Step 1: Track Usage

```bash
ruby orch/orchestrator.rb usage increment --phase simplify
```

---

## Step 2: Report Progress — Starting

```bash
ruby orch/orchestrator.rb progress update --phase simplify --step starting \
  --detail "Running /simplify quality pass on build output"
```

---

## Step 3: Capture Pre-Simplify State

```bash
git diff --stat HEAD
```

Record the current file state so you can report what simplify changed.

---

## Step 4: Run /simplify

Invoke the simplify skill via the Skill tool:

```
Skill(skill="simplify")
```

This spawns three parallel review agents (code reuse, code quality, efficiency), aggregates findings, and auto-applies fixes against changed files on the current branch.

Wait for it to complete. If the skill invocation fails, go directly to the Error result.

---

## Step 5: Capture Post-Simplify State

```bash
git diff --stat HEAD
```

Compare to the pre-simplify state captured in Step 3. Identify which files were modified and how many.

---

## Step 6: Report Progress — Complete

```bash
ruby orch/orchestrator.rb progress update --phase simplify --step complete \
  --detail "Simplify pass complete: [N] files modified" \
  --metrics '{"files_modified":[N]}'
```

---

## Step 7: Gate Exit — Restart Server

```bash
./restart_server.sh
```

Verify health:

```bash
curl -sk https://smac.griffin-blenny.ts.net:5055/health
```

If health check fails, check `/tmp/claude_headspace.log` for errors. Fix issues before returning result.

---

## Result

### Simplify made changes:

```yaml
simplify_result:
  status: success
  change_name: "[change_name]"
  files_modified:
    - "[list of files simplify touched]"
  changes_summary: "[brief description of what simplify did]"
  server_health: ok
```

### Simplify found nothing to change:

```yaml
simplify_result:
  status: no_changes
  change_name: "[change_name]"
  server_health: ok
```

### Error:

```yaml
simplify_result:
  status: error
  error_message: "[description]"
  server_health: "[ok|failed|not_checked]"
```

---

## Error Handling

If `/simplify` fails or server health check fails after the simplify pass:

Output the error result block and stop immediately. The lead will handle notification and user interaction.
