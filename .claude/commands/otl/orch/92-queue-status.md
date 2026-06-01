---
name: '92: queue-status'
description: 'Display current queue and orchestration status'
---

# Queue Status

Display the current PRD orchestration status.

---

## Get Status

```bash
ruby orch/orchestrator.rb status
```

```bash
ruby orch/orchestrator.rb state show
```

```bash
ruby orch/orchestrator.rb queue status
```

---

## Display

```
═══════════════════════════════════════════
  PRD ORCHESTRATION STATUS
═══════════════════════════════════════════

CURRENT STATE
─────────────
Phase:      [phase or "idle"]
Change:     [change_name or "none"]
Branch:     [branch or "N/A"]
Mode:       [Bulk / Default / N/A]

QUEUE
─────
Pending:     [N]
In Progress: [N]
Completed:   [N]
Failed:      [N]
───────────────
Total:       [N]

NEXT UP
───────
[List pending PRDs, or "Queue is empty"]

═══════════════════════════════════════════
```

---

## Suggested Next Action

Based on status:

- If a phase is active: "Orchestration in progress"
- If pending PRDs exist and nothing in progress: "Run `/otl:orch:20-start-queue-process` to start"
- If queue is empty: "Run `/otl:orch:10-queue-add` to add PRDs"
