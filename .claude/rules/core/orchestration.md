# PRD Orchestration System

This project includes a PRD-driven development orchestration system for managing feature development through a structured pipeline, plus an OpenSpec change management system for tracking individual changes.

## Orchestration Overview

The system uses Ruby scripts (`orch/`) with Claude Code commands (`.claude/commands/otl/`) to automate:

1. **PRD Workshop** - Create and validate PRDs
2. **Queue Management** - Batch processing of multiple PRDs
3. **Proposal Generation** - Create OpenSpec change proposals from PRDs
4. **Build Phase** - Implement changes with AI assistance
5. **Test Phase** - Run pytest with auto-retry (Ralph loop)
6. **Validation** - Verify implementation matches spec
7. **Finalize** - Commit, create PR, and merge

## Git Workflow

```
development (base) -> feature/change-name -> PR -> development
```

- Feature branches are created FROM `development`
- PRs target `development` branch
- `main` is the stable/release branch

## Key Commands

```bash
# PRD Management
/10: prd-workshop      # Create/remediate PRDs
/20: prd-list          # List pending PRDs
/30: prd-validate      # Quality gate validation

# Orchestration (from development branch)
/10: queue-add         # Add PRDs to queue
/20: prd-orchestrate   # Start queue processing

# Ruby CLI (direct access)
ruby orch/orchestrator.rb status      # Show current state
ruby orch/orchestrator.rb queue list  # List queue items
ruby orch/prd_validator.rb list-all   # List PRDs with validation status
```

## Orchestration Directories

```
orch/
+-- orchestrator.rb      # Main orchestration dispatcher
+-- state_manager.rb     # State persistence
+-- queue_manager.rb     # Queue operations
+-- prd_validator.rb     # PRD validation
+-- usage_tracker.rb     # Usage tracking
+-- config.yaml          # Orchestration config
+-- commands/            # Ruby command implementations
+-- working/             # State/queue files (gitignored)
+-- log/                 # Log files (gitignored)

openspec/
+-- config.yaml          # OpenSpec configuration
+-- specs/               # ~34 current specification files
+-- changes/
    +-- archive/         # 24 completed changes
    +-- (active changes)

.claude/commands/otl/
+-- prds/                # PRD management commands
+-- orch/                # Orchestration commands
```

## PRD Location

PRDs are stored in `docs/prds/{subsystem}/` (core, events, inference, ui, notifications, scripts, state, testing, bridge, flask, api).

## Running the Orchestration

1. Create a PRD in `docs/prds/{subsystem}/`
2. Run `/10: prd-workshop` to validate
3. Switch to `development` branch
4. Run `/10: queue-add` to add to queue
5. Run `/20: prd-orchestrate` to start processing

See `.claude/commands/otl/README.md` for detailed documentation.
