---
description: "Connect the operator to another agent by name. Use when they say 'patch me through to X', 'connect me to Y', or any equivalent phrasing."
---

# Voice Switchboard

## Procedure

When the operator asks to be connected to another agent — "patch me through to Robbo", "connect me to Mick", "put me through to Liv", or any equivalent natural phrasing — you are a switchboard operator.

### Methodology

1. **Identify the target** from the agent roster in your system context.  Match by name, persona name, or slug.  If ambiguous, ask: "I'm not sure who you mean — could you give me their name?"
2. **Extract project context** if the operator specifies one ("Robbo in Kenwood", "Nell in Beans").  If no project is named, omit the `project` field — the endpoint resolves across all projects.
3. **Speak a brief confirmation** in natural language: "Connecting you to [Name]."
4. **Call the switchboard endpoint** to trigger the voice session rebind:
   ```bash
   curl -sk -X POST https://smac.griffin-blenny.ts.net:5055/api/voice/switchboard \
     -H "Content-Type: application/json" \
     -d '{"target": "<name>", "project": "<project-or-omit>", "agent_id": '$OTL_AGENT_ID'}'
   ```

**Examples:**
- "Patch me through to Robbo" → `{"target": "Robbo", "agent_id": ...}` (no project — endpoint picks the active one)
- "Patch me through to Robbo in Kenwood" → `{"target": "Robbo", "project": "Kenwood", "agent_id": ...}` (project-scoped)

### Rules

- Only trigger on **explicit connection requests**.  Discussing another agent ("Robbo said...") is NOT a switch request.
- Use the target's display name (e.g., "Robbo", "Mick", "Liv"), not their slug.
- If you cannot identify the target, ask for clarification — never guess.
- The verbal confirmation ("Connecting you to Robbo") is spoken via TTS as your normal response.  The endpoint call happens separately as a tool action.

### Target not found

**Always call the switchboard endpoint first.**  The endpoint resolves targets across all projects — do not pre-check with a project-scoped `cli-headspace agents list`.

If the endpoint returns an error indicating the target was not found:
1. Ask Sam which project the target is in — do not guess.
2. Launch and brief the target via `/abilities:handoff` using the project Sam provides.
3. Call the switchboard endpoint again after the target is running.
