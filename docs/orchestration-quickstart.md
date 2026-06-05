# Orchestration Quick Start

Build features from PRDs using a 3-command pipeline. Write what you want, validate it, and let the orchestration engine build, test, and ship it.

This project includes an AI-agent orchestration engine that processes Product Requirement Documents (PRDs) through a 5-phase automated pipeline: Propose, Build, Test, Smoke, Ship. Each phase is handled by a specialist worker agent, coordinated by a lead orchestrator.

## Prerequisites

- Claude Code or OpenAI Codex CLI installed
- Git repository cloned and on `master` branch
- Python environment active with project dependencies installed
- PostgreSQL database `citylab` running

## The Three Commands

### Step 1: Workshop a PRD

Create a PRD interactively. The workshop guides you through requirements elicitation, scope definition, gap detection, and validation.

```
# Claude Code
/otl:prds:10-workshop

# Codex — paste the contents of .codex/prompts/otl--prds--10-workshop.md
#          as instructions, then follow the workshop prompts
```

The workshop will ask you:
1. What capability you want to build (1-3 sentences)
2. Which subsystem it belongs to
3. Any existing context to consider

It then walks through Five Whys, scope boundaries, requirement focus checks, gap detection, and scope assessment. At the end it writes a validated PRD to `docs/prds/{subsystem}/{name}.md`.

**To remediate an existing PRD that failed validation:**

```
# Claude Code
/otl:prds:10-workshop docs/prds/energy/my-feature-prd.md

# Codex — paste the prompt contents and include the PRD path in your message
```

### Step 2: Validate and Queue

Validate the PRD(s), commit any outstanding changes, and add to the build queue.

```
# Claude Code
/otl:orch:05-rack-build

# Codex — paste .codex/prompts/otl--orch--05-rack-build.md as instructions
```

This command:
1. Identifies PRDs from your session or scans `docs/prds/`
2. Runs validation checks on each (format, gaps, requirement focus, conflicts, scope, ambiguity, orchestration readiness)
3. Commits and pushes any outstanding changes
4. Queues validated PRDs for the build pipeline

If any PRD fails validation, the command stops and tells you how to fix it (usually by re-running the workshop in remediate mode).

### Step 3: Run the Pipeline

Process the queued PRDs through the full build pipeline.

```
# Claude Code
/otl:orch:20-start-queue-process docs/prds/energy/my-feature-prd.md

# Codex — paste .codex/prompts/otl--orch--20-start-queue-process.md
#          as instructions, include the PRD path(s) in your message
```

Multiple PRDs (processed sequentially):

```
# Claude Code
/otl:orch:20-start-queue-process docs/prds/auth.md,docs/prds/dashboard.md

# Codex — include comma-separated paths in your message
```

The pipeline runs 5 phases per PRD:

| Phase | What happens |
|-------|-------------|
| 1. Propose | Reads the PRD, creates a feature branch, decomposes into tasks |
| 2. Build | Implements all tasks, commits at milestones |
| 3. Test | Runs pytest, fixes failures (2 attempts max) |
| 4. Smoke | Starts the app, verifies the demo works (2 attempts max) |
| 5. Ship | Commits, pushes, opens a PR to master |

After Ship, the orchestrator merges the PR. Each PRD gets its own feature branch (`feature/hack-{name}`).

**No hard stops.** If tests or smoke checks fail, the pipeline logs the issue and advances. The operator triages failures from the summary at the end.

## Example: End to End

```
# 1. Workshop a new feature
/otl:prds:10-workshop
> "I want to add a battery storage dispatch optimiser that schedules
>  charge/discharge cycles based on price forecasts. Subsystem: energy."

# ... interactive workshop creates docs/prds/energy/storage-dispatch-prd.md ...

# 2. Validate and queue
/otl:orch:05-rack-build

# 3. Build it
/otl:orch:20-start-queue-process docs/prds/energy/storage-dispatch-prd.md

# ... pipeline runs ~20-30 minutes ...
# ✓ storage-dispatch — PR #12 merged to master
```

## PRD Format

PRDs are markdown files in `docs/prds/{subsystem}/`. The workshop generates the correct format, but if writing manually, include these sections:

- **Executive Summary** — what and why
- **Scope** — in scope and explicitly out of scope
- **Success Criteria** — measurable outcomes
- **Functional Requirements** — numbered (FR1, FR2, ...), focused on WHAT not HOW
- **Non-Functional Requirements** — if applicable
- **UI Overview** — if user-facing

Requirements must be requirement-focused (what the system should do), not implementation-focused (how to build it). "Users can filter by status" is a requirement. "Create a FilterService class" is not.

## Troubleshooting

See [docs/orchestration-reference.md](orchestration-reference.md) for the full command reference, all available commands, SOPs, utilities, and detailed troubleshooting.

## Claude Code vs Codex

This project supports both Claude Code and OpenAI Codex CLI. The orchestration commands are available in both:

| Claude Code | Codex |
|------------|-------|
| Commands in `.claude/commands/` invoked as `/namespace:command` | Prompts in `.codex/prompts/` pasted as agent instructions |
| Skills in `.claude/skills/` invoked as `/skill-name` | Skills in `.codex/skills/` referenced by the agent |
| Project rules in `.claude/rules/` auto-loaded | Project rules compiled into `AGENTS.md` at project root |

**Codex users:** The `.codex/prompts/` directory contains the same commands as `.claude/commands/`, with paths flattened using `--` separators (e.g., `otl/orch/05-rack-build.md` becomes `otl--orch--05-rack-build.md`). Open the prompt file, paste its contents as instructions to your Codex agent, and provide any required arguments (like PRD paths) in your message.
