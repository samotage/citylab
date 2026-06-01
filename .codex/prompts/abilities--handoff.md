---
description: Hand off to another agent when the work requires a specialist or the
  operator asks to be connected. Use when you need expertise outside your domain.
---

# Agent Handoff

## Procedure

When the work requires a specialist you are not, or when the operator asks to be connected to another agent, launch and brief them directly.

**Launch:**
```bash
cli-headspace agents create --persona <slug> --project "<project>"
```

**Brief:**
```bash
cli-headspace agents send <id> "<message>"
```

**Fire-once rule:** `agents create` is non-idempotent — each call creates a new agent.  Never retry without first checking:
```bash
cli-headspace agents list --persona <slug> --project "<project>"
```

### Methodology

1. Identify the target persona and project
2. Launch via `cli-headspace agents create` — capture the agent ID from `data.agent_id` in the JSON response
3. Send a context brief via `cli-headspace agents send <id>` — include what the operator needs, relevant context from your conversation, and decisions already made.  The target starts cold; your brief is their only context
4. Call the switchboard endpoint (invoke `/abilities:switchboard`) to connect the operator

If the operator didn't explicitly ask to be connected, tell them the agent is ready and offer to patch through.

### Triggers

- The operator asks to talk to another agent
- The work crosses into another persona's domain and you can't resolve it yourself

### Anti-Triggers

- You can answer the question yourself
- The operator is just mentioning another agent in conversation — that is not a handoff request

## Anti-Convergence

- **Launching without briefing** — running `cli-headspace agents create` without following up with `cli-headspace agents send`.  The target starts cold — without your brief, the operator has to repeat everything
- **Retrying agent creation without checking** — `agents create` is non-idempotent.  Always check `cli-headspace agents list --persona <slug>` before retrying

## Alignment Signals

- Launching a specialist agent, briefing with conversation context, then signalling switchboard — complete handoff sequence (correct)
- Launching an agent without sending a context brief — target starts cold, operator repeats everything (drift)

## Quality Definitions

- [ ] Agent handoff includes context brief before switchboard signal — target never starts without context
