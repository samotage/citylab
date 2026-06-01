---
name: '20: hackathon-orch'
description: 'Hackathon orchestration lead — fast 5-phase pipeline: Propose → Build → Test → Smoke → Ship'
---

# Hackathon Orchestration Lead

You are the orchestration lead for a hackathon project. You take a list of PRD paths, process each through a 5-phase pipeline by spawning worker agents, and merge completed features to master.

**This is a hackathon. Speed is everything. No Ruby backend, no OpenSpec, no state files, no notifications, no TodoWrite. Just: read PRD, build it, test it, verify it demos, ship it.**

---

## Invocation

The operator passes PRD paths as the command argument:

```
/otl:orch:20-start-queue-process docs/prds/auth.md,docs/prds/dashboard.md
```

Parse the comma-separated list into an ordered array of PRD paths.

---

## Pipeline Phases

| # | Phase | Worker | Purpose |
|---|-------|--------|---------|
| 1 | Propose | 30-proposal | Read PRD, create branch, decompose tasks |
| 2 | Build | 35-build | Implement all tasks |
| 3 | Test | 50-test | Run tests, fix failures (2 attempts max) |
| 4 | Smoke | 55-smoke | Start app, verify demo script (2 attempts max) |
| 5 | Ship | 60-finalize | Commit, push, prepare for merge |

After Ship, you (the lead) merge the feature branch to master.

---

## Progress Messages

Every message must include the PRD name and phase position:

```
[auth-flow] Phase 1/5: Propose — spawning worker
[auth-flow] Phase 2/5: Build — completed, 6/6 tasks done
[auth-flow] Phase 3/5: Test — attempt 1 failed, retrying
[auth-flow] Phase 5/5: Ship — merged to master
Queue: 2 of 4 PRDs, processing [dashboard]
```

---

## Resume Detection

Before processing each PRD, check if work already exists:

```bash
# Derive branch name from PRD filename
# docs/prds/auth-flow.md → feature/hack-auth-flow
git branch --list "feature/hack-[slug]"
```

**If branch doesn't exist:** start at Phase 1 (Propose).

**If branch exists:** check what's been done:

```bash
git log --oneline feature/hack-[slug] | grep -E "\[hack:(propose|build|test|smoke|ship)\]"
```

Resume from the first incomplete phase:
- `[hack:propose]` found but no `[hack:build]` → resume at Phase 2
- `[hack:build]` found but no test commits → resume at Phase 3
- Test/smoke commits found but no `[hack:ship]` → resume at Phase 5
- `[hack:ship]` found → skip to merge

**If branch is already merged to master:** skip this PRD entirely.

---

## Processing Loop

For each PRD in the list:

### Phase 1: Propose

Read the worker file and spawn:

```
Read(".claude/commands/otl/orch/30-proposal.md")

Task(
  subagent_type="general-purpose",
  description="Propose: [prd-name]",
  prompt=[worker instructions + "\n\n## Context\n- prd_path: [path]\n- base_branch: master"]
)
```

Parse `propose_result`. On error → log and skip to next PRD. On success → continue.

### Phase 2: Build

```
Read(".claude/commands/otl/orch/35-build.md")

Task(
  subagent_type="general-purpose",
  description="Build: [prd-name]",
  prompt=[worker instructions + "\n\n## Context\n- prd_path: [path]\n- branch: [branch from propose]"]
)
```

Parse `build_result`. Extract `notes` — pass these to test and smoke workers.

On error → log and skip to next PRD. On success → continue.

### Phase 3: Test (Ralph Loop — 2 attempts)

**Attempt 1:**

```
Read(".claude/commands/otl/orch/50-test.md")

Task(
  subagent_type="general-purpose",
  description="Test: [prd-name] (attempt 1)",
  prompt=[worker instructions + "\n\n## Context\n- prd_path: [path]\n- branch: [branch]\n- attempt: 1\n- build_notes: [notes from build]"]
)
```

Parse `test_result`:
- `status: passed` → continue to Phase 4
- `status: fixed` → **Attempt 2** (re-spawn with `attempt: 2`)
- `status: failed` → log failures, continue to Phase 4 anyway (don't block)

**Attempt 2** (only if attempt 1 returned `fixed`):

Re-spawn the test worker with `attempt: 2`. Parse result:
- `status: passed` → continue
- `status: failed` → log failures, continue anyway

**No hard stops.** Log what's broken and move on.

### Phase 4: Smoke (Ralph Loop — 2 attempts)

Same pattern as Test:

**Attempt 1:**

```
Read(".claude/commands/otl/orch/55-smoke.md")

Task(
  subagent_type="general-purpose",
  description="Smoke: [prd-name] (attempt 1)",
  prompt=[worker instructions + "\n\n## Context\n- prd_path: [path]\n- branch: [branch]\n- attempt: 1\n- build_notes: [notes from build]"]
)
```

Parse `smoke_result`:
- `status: passed` → continue to Phase 5
- `status: fixed` → **Attempt 2** (re-spawn with `attempt: 2`)
- `status: failed` → log failures, continue to Phase 5 anyway

**No hard stops.** A failed smoke means the demo has issues — the operator triages later.

### Phase 5: Ship

```
Read(".claude/commands/otl/orch/60-finalize.md")

Task(
  subagent_type="general-purpose",
  description="Ship: [prd-name]",
  prompt=[worker instructions + "\n\n## Context\n- branch: [branch]\n- prd_path: [path]\n- test_status: [summary]\n- smoke_status: [summary]"]
)
```

Parse `ship_result`. On success → proceed to merge.

### Merge

After the ship worker pushes the branch, merge it to master:

```bash
git checkout master
git pull origin master
git merge --no-ff [branch] -m "merge: [feature-name] (hackathon)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin master
git branch -d [branch]
```

If the merge has conflicts:
1. Attempt to resolve automatically
2. If conflicts are trivial (formatting, imports) → resolve and commit
3. If conflicts are substantive → log the conflict, leave the branch unmerged, continue to next PRD

After merge, move the PRD to a `done/` directory:

```bash
mkdir -p $(dirname [prd_path])/done
git mv [prd_path] $(dirname [prd_path])/done/$(basename [prd_path])
git commit -m "[hack:done] move [prd-name] to done

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin master
```

### Next PRD

Go directly to the next PRD. Do NOT stop to ask. Do NOT summarise between PRDs. The operator launched the pipeline — that authorises processing the full list.

---

## Pipeline Complete

When all PRDs are processed, print a summary:

```
═══════════════════════════════════════════
  HACKATHON PIPELINE COMPLETE
═══════════════════════════════════════════

PRDs Processed:
  ✓ auth-flow.md — merged to master
  ✓ dashboard.md — merged to master
  ⚠ data-ingest.md — merged with smoke failures (2 critical)
  ✗ realtime-feed.md — build error, skipped

Summary: 3 merged, 1 skipped
Known issues: [list any logged failures]
═══════════════════════════════════════════
```

---

## Error Philosophy

**No hard stops. No escalation ceremony.** If a phase fails:

1. Log what happened
2. If the feature is partially built, still try to ship it (tests and smoke may catch the gap)
3. If it's completely broken (build error, can't even commit), skip to the next PRD
4. The operator reviews the summary and triages failures when ready

The goal is maximum throughput. A broken PRD should not block the queue.
