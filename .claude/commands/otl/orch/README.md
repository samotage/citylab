---
name: 'README'
description: 'Hackathon Orchestration — Fast 5-Phase Pipeline'
---

# Hackathon Orchestration Pipeline

Fast PRD-to-feature pipeline for hackathon development. Stripped from the production 8-phase system — no compliance, no simplification, no OpenSpec, no Ruby state management.

## Pipeline

```
PRD → Propose → Build → Test → Smoke → Ship → Merge
```

| # | Phase | Worker | What it does |
|---|-------|--------|-------------|
| 1 | Propose | `30-proposal` | Read PRD, create branch, decompose tasks |
| 2 | Build | `35-build` | Implement all tasks, commit at milestones |
| 3 | Test | `50-test` | Run tests, fix failures (2 attempts max) |
| 4 | Smoke | `55-smoke` | Start app, verify demo script works (2 attempts max) |
| 5 | Ship | `60-finalize` | Commit, push |
| — | Merge | Lead | Merge branch to master, move PRD to done |

## Quick Start

### 1. Write a PRD

Use the template at `docs/prds/_template.md`. Four fields: Problem, Approach, Done When, Demo Script.

### 2. Run the pipeline

```
/otl:orch:20-start-queue-process docs/prds/my-feature.md
```

Multiple PRDs (processed in order):

```
/otl:orch:20-start-queue-process docs/prds/auth.md,docs/prds/dashboard.md,docs/prds/polish.md
```

### 3. Monitor

The lead logs progress with phase numbers:

```
[auth-flow] Phase 2/5: Build — 4/6 tasks complete
[auth-flow] Phase 3/5: Test — all passed
```

## Design Decisions

- **No hard stops.** Failed tests/smoke log the issue and advance. The operator triages later.
- **No state file.** Resume detection uses branch-exists + commit message tags.
- **No Ruby backend.** All orchestration is in the lead command file.
- **No OpenSpec.** Tasks are tracked in `TASKS.md` on the feature branch.
- **Feature branches.** Each PRD gets `feature/hack-{name}`, merged to master via `--no-ff`.
- **2-attempt Ralph loop** for both Test and Smoke phases.

## Production Comparison

| Aspect | Production | Hackathon |
|--------|-----------|-----------|
| Phases | 8 | 5 |
| State management | Ruby YAML | Branch-exists |
| Spec system | OpenSpec | TASKS.md |
| Compliance check | 2-pass Ralph | None |
| Code quality | /simplify pass | None |
| Test retries | 2 attempts | 2 attempts |
| Smoke retries | 2 attempts | 2 attempts |
| Merge method | PR + squash | git merge --no-ff |
| Failure handling | Hard stop + escalate | Log and advance |
| Target time/PRD | 2+ hours | 20-30 minutes |

## Cut Phases (from production)

These production phases are **not used** in the hackathon pipeline:
- Compliance (40) — PRD-vs-code verification
- Simplify (45) — code quality pass
- Rack Build (05) — pre-build prep
- Queue Add (10) — Ruby queue management
- Notify (91) — Slack notifications
- Queue Status (92/93) — status displays

The production command files for these phases have been removed from this project.
