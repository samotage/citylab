---
name: diagnose-headspace
description: Diagnose this Headspace instance — run all system checks (infrastructure, services, config, features, connectors, organisation) and guided self-heal. Use after running configure, when something seems broken, when the operator asks about Headspace system status, or when an agent hits a system-level failure. Presents findings and works through fixes one at a time with operator approval.
allowed-tools: Bash(cli-headspace *), Bash(flask headspace *), Bash(source *), Bash(./restart_server.sh), Bash(bash bin/*), Bash(curl *), Bash(cat *), Bash(grep *), Read, Edit
---

# System Diagnostics and Self-Heal

You are running system diagnostics on a Headspace instance and guiding the operator
through fixes for any non-green items.

## Phase 1: Diagnose

Run the diagnostics command. Choose the right surface based on context:

- **Server is running:** `cli-headspace diagnostics --json`
- **During bootstrap (server may not be running):** `source venv/bin/activate && flask headspace status --json-output`

Parse the JSON output. You need: `overall_status`, `summary` (counts by status, tier,
priority), and the full `categories` object with individual check results.

If `overall_status` is green, report healthy and stop. No further action needed.

## Phase 2: Present findings

Show the operator the full picture before starting any fixes:

```
System health: [overall_status]
[N] issues found: [X] critical, [Y] standard
  [A] auto-fixable, [B] guided (need your input), [C] manual (need your action)

Critical issues:
  [red] Check name — detail
  [amber] Check name — detail

Standard issues:
  [red] Check name — detail
  [amber] Check name — detail
```

Then ask: "Ready to work through these one at a time?"

## Phase 3: Fix loop

Work through non-green items in strict priority order:
1. Critical reds
2. Critical ambers
3. Standard reds
4. Standard ambers

Within each priority band, follow category order: Infrastructure, Filesystem,
Core Services, Intelligence/LLM, Features, Connectors, Organisation, Orchestration,
Config Completeness.

### For each item, follow this sequence:

**1. Explain the problem.**
State the check name, what it found, and why it matters. One or two sentences.

**2. Propose the fix.**
Route by tier:

- **Auto tier:** "I can fix this by running [fix_steps]. Approve?"
- **Guided tier:** "I need [required_inputs description] to fix this. [prompt for value]"
- **Manual tier:** "This requires action outside this session: [remediation_prompt].
  Let me know when you've done it and I'll re-check."

**3. Get approval.**
Wait for operator confirmation before executing anything. If they say skip,
move to the next item.

**4. Execute the fix.**
Run the fix_steps from the diagnostic result. For guided items, substitute the
operator-provided value into the fix command.

Do NOT invent fix commands. Use only the fix_steps from the diagnostic output
or the remediation_prompt text. If neither provides a concrete command, explain
the situation and ask the operator what to do.

**5. Verify.**
Re-run the specific check to confirm it's now green:
`cli-headspace diagnostics --json --category "[category name]"`

If still non-green after the fix:
- Report what happened
- Offer to retry (up to 3 attempts per item)
- After 3 failures, mark as unresolved and move to the next item

**6. Move to next item.**

### Per-user connector checks

For connector checks (email, calendar), drill into `user_results`:
- If the current operator's connector is broken: present the manual remediation
  steps for their re-auth
- If another user's connector is broken: "User [email]'s [connector] needs
  re-authentication. They'll need to do this in their browser. Moving on."

### Distinguishing "not configured yet" from "broken"

Connector checks with zero `user_results` (no integrations registered at all)
are an expected initial state, not a failure. Present as: "Email connectors not
yet configured for any user. This is expected on a new install — configure when
ready." Do not treat this as urgent.

## Phase 4: Summary

After working through all items (or when the operator stops), present the final state:

```
Diagnostics complete.
  Fixed: [N] items
  Skipped: [N] items
  Unresolved: [N] items (list them)
  Remaining: [N] items still non-green

[If any unresolved:] Re-run /diagnose-headspace after addressing the manual items above.
```

## Rules

1. Never batch fixes. One item at a time, approve, execute, verify.
2. Never skip the consent gate. Every fix requires explicit operator approval.
3. Never execute fix_steps for manual-tier items. Explain only.
4. Never assume a fix worked. Always re-check.
5. Never invent remediation commands. Use only what the diagnostic output provides.
6. Never fix standard-priority items before all critical items are resolved or
   acknowledged (skipped/unresolved).
7. Critical items with status red are always presented first, regardless of tier.
8. If the operator says stop at any point, stop immediately. Present the summary
   of what was done and what remains.
