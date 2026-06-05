# Orchestration Reference

Complete reference for the PRD-driven orchestration engine. For the 3-command quick start, see [orchestration-quickstart.md](orchestration-quickstart.md).

## How It Works

The orchestration engine takes a PRD (Product Requirement Document) and processes it through an automated 5-phase pipeline. A lead orchestrator agent reads the PRD and spawns specialist worker agents for each phase. Each phase produces artifacts on a feature branch, and the final result is a merged PR to master.

```
PRD → Propose → Build → Test → Smoke → Ship → Merge PR
```

This is a hackathon-optimised version of the production pipeline. No Ruby state management, no OpenSpec, no compliance checks. Speed over ceremony.

## All Commands

Commands are organized in three groups. Each has a Claude Code invocation (slash command) and a Codex equivalent (prompt file in `.codex/prompts/`).

### PRD Management

| # | Command | Claude Code | Codex Prompt | Purpose |
|---|---------|------------|--------------|---------|
| 05 | Sprint Prompts | `/otl:prds:05-sprint-prompts` | `otl--prds--05-sprint-prompts.md` | Generate PRD workshop prompts from a roadmap epic/sprint |
| 10 | PRD Workshop | `/otl:prds:10-workshop` | `otl--prds--10-workshop.md` | Create or remediate PRDs interactively |
| 20 | PRD List | `/otl:prds:20-list` | `otl--prds--20-list.md` | Show pending PRDs awaiting build |
| 30 | PRD Validate | `/otl:prds:30-validate` | `otl--prds--30-validate.md` | Quality gate — pass/fail before orchestration |
| 40 | PRD Sequence | `/otl:prds:40-sequence` | `otl--prds--40-sequence.md` | Recommend build order based on dependencies |
| 70 | Review PRD Set | `/otl:prds:70-review-prd-set` | `otl--prds--70-review-prd-set.md` | Adversarial cross-PRD review for batch alignment |

### Orchestration Pipeline

| # | Command | Claude Code | Codex Prompt | Purpose |
|---|---------|------------|--------------|---------|
| 05 | Rack Build | `/otl:orch:05-rack-build` | `otl--orch--05-rack-build.md` | Validate PRDs, clean repo, queue for build |
| 10 | Queue Add | `/otl:orch:10-queue-add` | `otl--orch--10-queue-add.md` | Add validated PRDs to the processing queue |
| 20 | Start Pipeline | `/otl:orch:20-start-queue-process` | `otl--orch--20-start-queue-process.md` | Run the 5-phase automated build pipeline |
| 30 | Propose (worker) | `/otl:orch:30-proposal` | `otl--orch--30-proposal.md` | Read PRD, create branch, decompose tasks |
| 35 | Build (worker) | `/otl:orch:35-build` | `otl--orch--35-build.md` | Implement all tasks from the proposal |
| 50 | Test (worker) | `/otl:orch:50-test` | `otl--orch--50-test.md` | Run tests, fix failures (2 attempts max) |
| 55 | Smoke (worker) | `/otl:orch:55-smoke` | `otl--orch--55-smoke.md` | Start app, verify demo script works |
| 60 | Ship (worker) | `/otl:orch:60-finalize` | `otl--orch--60-finalize.md` | Commit, push, open PR to master |
| 91 | Notify | `/otl:orch:91-notify` | `otl--orch--91-notify.md` | Send notifications |
| 92 | Queue Status | `/otl:orch:92-queue-status` | `otl--orch--92-queue-status.md` | Display queue status |
| 93 | Live Status | `/otl:orch:93-live-status` | `otl--orch--93-live-status.md` | Live pipeline status display |

Worker commands (30-60) are spawned by the lead orchestrator. You don't invoke them directly unless debugging.

### SOPs (Standard Operating Procedures)

Step-by-step procedures for common development operations. Use these when you need a structured approach to a specific task.

| SOP | Claude Code | Codex Prompt | Purpose |
|-----|------------|--------------|---------|
| Workshop | `/otl:sop:sop-01-workshop` | `otl--sop--sop-01-workshop.md` | Structured design workshop |
| Preflight | `/otl:sop:sop-10-preflight` | `otl--sop--sop-10-preflight.md` | Pre-work checks |
| Start Work Unit | `/otl:sop:sop-20-start-work-unit` | `otl--sop--sop-20-start-work-unit.md` | Begin a discrete unit of work |
| Pre-build Snapshot | `/otl:sop:sop-30-prebuild-shapshot` | `otl--sop--sop-30-prebuild-shapshot.md` | Capture state before building |
| Review Current Diff | `/otl:sop:sop-60-review-current-diff` | `otl--sop--sop-60-review-current-diff.md` | Review uncommitted changes |
| Targeted Tests | `/otl:sop:sop-70-targeted-tests` | `otl--sop--sop-70-targeted-tests.md` | Run tests relevant to your changes |
| Archive and Commit | `/otl:sop:sop-80-archive-and-commit` | `otl--sop--sop-80-archive-and-commit.md` | Archive completed work and commit |
| Rollback | `/otl:sop:sop-99-rollback-the-alamo` | `otl--sop--sop-99-rollback-the-alamo.md` | Emergency rollback procedure |

### Utilities

| Utility | Claude Code | Codex Prompt | Purpose |
|---------|------------|--------------|---------|
| Commit & Push | `/commit-push` | `commit-push.md` | Auto-commit and push (no approval) |
| Available Magic | `/otl:util:available-magic` | `otl--util--available-magic.md` | List all available commands |
| Project Review | `/otl:util:project-review` | `otl--util--project-review.md` | Review project state |
| Commit PR to Main | `/otl:util:commit-pr-to-main` | `otl--util--commit-pr-to-main.md` | Create PR and merge to main |
| Complexity Audit | `/otl:util:complexity-audit` | `otl--util--complexity-audit.md` | Audit code complexity |
| Code Review (3x) | `/otl:util:three-time-adversarial-code-review` | `otl--util--three-time-adversarial-code-review.md` | Triple adversarial code review |
| PRD Compliance | `/otl:util:prd-compliance-check` | `otl--util--prd-compliance-check.md` | Check build matches PRD |
| Spec Audit | `/otl:util:bidirectional-specification-audit` | `otl--util--bidirectional-specification-audit.md` | Bidirectional spec compliance audit |
| Log Watch | `/otl:util:log-watch` | `otl--util--log-watch.md` | Watch application logs |
| Generate Codex | `/otl:util:generate-codex` | `otl--util--generate-codex.md` | Regenerate .codex from .claude source |
| Generate Magic | `/otl:util:generate-magic` | `otl--util--generate-magic.md` | Generate AVAILABLE_MAGIC.md |
| Fix Permissions | `/otl:util:unfuck-permissions` | `otl--util--unfuck-permissions.md` | Fix .claude/settings.json permissions |
| Chrome Debug | `/otl:util:start-chrome-debug` | `otl--util--start-chrome-debug.md` | Launch Chrome with CDP debugging |
| Connect Browser | `/otl:util:connect-agent-browser` | `otl--util--connect-agent-browser.md` | Connect agent-browser to Chrome |
| Cloak Browser | `/otl:util:start-cloak-browser` | `otl--util--start-cloak-browser.md` | Launch stealth browser |

### OpenSpec Change Management

| Command | Claude Code | Codex Prompt | Purpose |
|---------|------------|--------------|---------|
| New | `/opsx:new` | `opsx--new.md` | Create a new change |
| Apply | `/opsx:apply` | `opsx--apply.md` | Apply a change |
| Explore | `/opsx:explore` | `opsx--explore.md` | Explore change details |
| Continue | `/opsx:continue` | `opsx--continue.md` | Continue work on a change |
| Verify | `/opsx:verify` | `opsx--verify.md` | Verify a change |
| Archive | `/opsx:archive` | `opsx--archive.md` | Archive a completed change |
| Bulk Archive | `/opsx:bulk-archive` | `opsx--bulk-archive.md` | Archive multiple changes |
| Sync | `/opsx:sync` | `opsx--sync.md` | Sync change state |
| Fast Forward | `/opsx:ff` | `opsx--ff.md` | Fast-forward a change |
| Onboard | `/opsx:onboard` | `opsx--onboard.md` | Onboard to the OpenSpec system |

## Pipeline Details

### Phase 1: Propose

The proposal worker reads the PRD and creates:
- A feature branch (`feature/hack-{name}`)
- A `TASKS.md` file on the branch with decomposed implementation tasks
- Each task has clear scope, files to touch, and acceptance criteria

### Phase 2: Build

The build worker implements every task in `TASKS.md`:
- Reads each task and implements it
- Commits at milestones (not one giant commit at the end)
- Marks tasks complete in `TASKS.md` as it goes

### Phase 3: Test (Ralph Loop)

The test worker runs the test suite and fixes failures:
- **Attempt 1:** Run `pytest`, fix any failures, commit fixes
- **Attempt 2:** If attempt 1 had fixes, re-run to verify. If still failing, log and advance.
- Tests target the `citylab_test` database (enforced by `conftest.py`)

### Phase 4: Smoke

The smoke worker verifies the feature works in the running app:
- Starts the server via `./restart_server.sh`
- Follows the demo script from the PRD
- Takes screenshots or verifies API responses
- Same 2-attempt Ralph loop as Test

### Phase 5: Ship

The ship worker finalises:
- Commits any remaining changes
- Pushes the feature branch
- Opens a PR to `master`

The lead orchestrator then merges the PR via `gh pr merge`.

### Resume Detection

The pipeline can resume if interrupted. Before processing a PRD, it checks:
- Does the feature branch exist?
- What commit tags (`[hack:propose]`, `[hack:build]`, etc.) are present?
- Does a PR already exist?

It resumes from the first incomplete phase rather than starting over.

## PRD Location Convention

```
docs/prds/
  {subsystem}/
    {name}.md              # Pending — ready for build
    done/
      {name}.md            # Completed — moved here after merge
```

Subsystems in this project: `core`, `energy`, `ui`, `api`, `testing`.

PRDs at the root of `docs/prds/` are ignored by orchestration.

## PRD Validation

PRDs carry validation state in YAML frontmatter:

```yaml
---
validation:
  status: valid          # valid | invalid | unvalidated
  validated_at: "2026-06-06T10:30:00Z"
  validation_errors: []  # populated when invalid
---
```

The validation checks:
1. **Format compliance** — required sections present
2. **Gap detection** — no TODOs, placeholders, or empty items
3. **Requirement focus** — WHAT not HOW
4. **Conflict detection** — no contradictions with existing code
5. **Scope assessment** — target 15-20 tasks per PRD
6. **Ambiguity check** — no vague requirements
7. **Orchestration readiness** — all fields present for the pipeline

## Hackathon vs Production Pipeline

This is a simplified pipeline optimised for hackathon speed:

| Aspect | Production | Hackathon |
|--------|-----------|-----------|
| Phases | 8 | 5 |
| State management | Ruby YAML backend | Branch-exists detection |
| Spec system | OpenSpec | TASKS.md on branch |
| Compliance check | 2-pass adversarial | None |
| Code quality pass | /simplify | None |
| Failure handling | Hard stop + escalate | Log and advance |
| Target time per PRD | 2+ hours | 20-30 minutes |

## Troubleshooting

**PRD validation fails:**
Run the workshop in remediate mode to fix issues interactively.
```
# Claude Code
/otl:prds:10-workshop docs/prds/{subsystem}/{name}.md

# Codex — paste otl--prds--10-workshop.md, include the PRD path
```

**Pipeline stuck or interrupted:**
Re-run the pipeline command with the same PRD path. Resume detection picks up where it left off.

**Tests fail repeatedly:**
Check `tests/conftest.py` for the test database fixture. All tests must run against `citylab_test`, never the development database.

**Smoke check can't start the server:**
The server must be started with `./restart_server.sh` (port 15099). Never run `python run_citylab.py` directly.

**PRD not found by rack-build:**
PRDs must be in a subsystem folder (`docs/prds/{subsystem}/`), not at the root level. Check the file exists and isn't in a `done/` directory.

**Need to see all available commands:**
```
# Claude Code
/otl:util:available-magic

# Codex — paste otl--util--available-magic.md
```

**Need to roll back a failed build:**
```
# Claude Code
/otl:sop:sop-99-rollback-the-alamo

# Codex — paste otl--sop--sop-99-rollback-the-alamo.md
```

## File Structure

```
.claude/commands/otl/           # Claude Code commands (source of truth)
  prds/                         # PRD management (workshop, validate, sequence)
  orch/                         # Pipeline orchestration (propose, build, test, smoke, ship)
  sop/                          # Standard operating procedures
  util/                         # Utilities (commit, review, audit)

.codex/prompts/                 # Codex equivalents (generated from .claude)
  otl--prds--10-workshop.md     # Path flattened with -- separators
  otl--orch--05-rack-build.md
  ...

.codex/skills/                  # Codex skills (mirrored from .claude/skills)

docs/prds/                      # PRD files organized by subsystem
  {subsystem}/
    {name}.md                   # Pending PRDs
    done/                       # Completed PRDs

AGENTS.md                       # Codex project instructions (compiled from CLAUDE.md + rules)
CLAUDE.md                       # Claude Code project instructions
```

## Using with Codex

Codex doesn't have a slash-command system like Claude Code. To use these commands with Codex:

1. Open the prompt file from `.codex/prompts/` (e.g., `otl--orch--05-rack-build.md`)
2. Paste its contents as instructions to your Codex agent
3. Include any required arguments (PRD paths, subsystem names) in your message
4. The agent follows the instructions step by step

For project context, Codex reads `AGENTS.md` at the project root. This file is compiled from `CLAUDE.md` and `.claude/rules/` and contains the same project instructions Claude Code gets.

Skills in `.codex/skills/` work the same as `.claude/skills/` — they provide domain-specific instructions the agent can reference when performing specialised tasks.
