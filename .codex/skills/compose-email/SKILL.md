---
name: compose-email
description: "Compose, draft, send, or forward emails on Sam's behalf. MUST be invoked before any email tool call. Contains byline lookup by persona slug, otageLabs footer HTML, tool routing, and composition checklist. Use this skill every time an agent composes, drafts, sends, or forwards an email."
allowed-tools:
  - mcp__claude_ai_Gmail__create_draft
  - mcp__gmail__send_email
  - mcp__gmail__forward_email
  - mcp__gmail__draft_email
  - mcp__gmail__update_draft
  - Read
version: 1.0.0
---

# Compose Email

Every outbound email on Sam's behalf goes through this skill.  No exceptions.

## Composition Checklist

1. **Load the writing style reference.**  Read `otl_support/claude_headspace/data/references/sam-writing-style.md`, focus on the **Ghost-writing Register**.  Non-negotiable for every draft.
2. **Compose the body** in Sam's voice.  Short, direct, no contractions, no padding.  Match the inbound's length and register.  Close with "Thanks, Sam" on its own line.
3. **Run the 8-point ghost-writing self-check** from the style reference.
4. **Append the byline** from the Byline Lookup table below.  Match your persona slug to `$OTL_AGENT_SLUG`.
5. **Append the footer HTML** from the Footer section below.  Verbatim.  Never modified, never truncated, never omitted.
6. **Create the draft** using the tool from the Tool Routing table below.
7. **If sending or forwarding:** read back the full payload to Sam using the Layer 3 format below.  Wait for explicit approval before firing the tool.

## Byline Lookup

Match `$OTL_AGENT_SLUG` to select the correct byline.

| Persona Slug | Byline (plain text) | Role context |
|---|---|---|
| `personal-assistant-nell-42` | — Nell Otage, PA to Sam Sabey | Personal assistant handling routine PA comms |
| `entrepreneur-mick-19` | Sent on behalf of Sam by Mick Otage | Commercial advisor handling business comms |

**Placement:** immediately after the body sign-off ("Thanks, Sam"), separated by a blank line, before the footer HTML.

**HTML format for `personal-assistant-nell-42`:**

```html
<p style="margin-top: 12px; font-size: 13px; color: #888888; font-style: italic; font-family: Calibri, 'Trebuchet MS', Arial, sans-serif;">— Nell Otage, PA to Sam Sabey</p>
```

**HTML format for `entrepreneur-mick-19`:**

```html
<p style="margin-top: 12px; font-size: 13px; color: #888888; font-style: italic; font-family: Calibri, 'Trebuchet MS', Arial, sans-serif;">Sent on behalf of Sam by Mick Otage</p>
```

The byline is non-negotiable.  Never omitted, never modified, never abbreviated.  The body sign-off remains "Thanks, Sam" (ghost-written, Sam's voice).  The byline is a separate attribution layer below the sign-off disclosing who handled the send action.

## Footer HTML

Append this HTML verbatim to every email, immediately AFTER the byline.  Never modify, truncate, or conditionally omit.

```html
<div style="margin-top: 20px; font-family: Calibri, 'Trebuchet MS', Arial, sans-serif;">
  <div style="height: 3px; background: linear-gradient(to right, #C8914A 0%, #daa86a 60%, #ede5d8 100%); border-radius: 1px; margin-bottom: 16px;"></div>
  <table cellpadding="0" cellspacing="0" border="0" style="font-size: 13px; color: #444444; border-collapse: collapse;">
    <tbody>
      <tr>
        <td style="padding-right: 18px; vertical-align: middle;">
          <img src="https://otagelabs.com/otagelabs-logo-light-bg_v1.0.png" alt="otageLabs" width="88" style="display: block; vertical-align: middle;">
        </td>
        <td style="width: 2px; background-color: #C8914A; vertical-align: middle; padding: 0;">
          <div style="width: 2px; background-color: #C8914A; height: 56px;"></div>
        </td>
        <td style="padding-left: 18px; vertical-align: middle; line-height: 1.6;">
          <span style="font-size: 15px; font-weight: 700; color: #2a2520; display: block; margin-bottom: 3px; font-family: Calibri, 'Trebuchet MS', Arial, sans-serif;">Sam Sabey</span>
          <a href="mailto:sam@otagelabs.com" style="color: #C8914A; text-decoration: none; display: block; font-family: Calibri, 'Trebuchet MS', Arial, sans-serif;">sam@otagelabs.com</a>
          <a href="https://otagelabs.com" style="color: #C8914A; text-decoration: none; display: block; font-family: Calibri, 'Trebuchet MS', Arial, sans-serif;">otagelabs.com</a>
          <span style="color: #999999; display: block; font-family: Calibri, 'Trebuchet MS', Arial, sans-serif;">+61 403 245 139</span>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

**Maintenance:** If Maren updates the footer design, update this skill file.  One file, all sending personas.

## Tool Routing

| Action | Tool | Server | Pre-approved |
|---|---|---|---|
| Create draft | `mcp__claude_ai_Gmail__create_draft` | Managed connector | Yes (wildcard) |
| Create draft (alt) | `mcp__gmail__draft_email` | klodr | Yes |
| Update draft | `mcp__gmail__update_draft` | klodr | Yes |
| Send email | `mcp__gmail__send_email` | klodr | Yes |
| Forward email | `mcp__gmail__forward_email` | klodr | Yes |
| Mark as read | `mcp__gmail__modify_email` | klodr | Yes |

**Prohibited tools** (regardless of MCP visibility):

- `mcp__gmail__send_draft` — bypasses the Layer 3 content approval gate
- `mcp__gmail__reply_to_email` / `mcp__gmail__reply_all` — bypasses composition checklist
- All `mcp__gmail__read_*` / `mcp__gmail__search_*` / `mcp__gmail__download_*` — use managed connector reads instead (Anthropic classifier protection)

## Layer 3 — Content Approval Gate

Before calling `send_email` or `forward_email`, read back the full recipient-visible payload:

```
About to <send | forward>:

  To:            recipient@example.com
  Cc:            (none, or list)
  Subject:       <subject>
  Body:
  ----
  <full body, exactly as it will appear, including byline and footer>
  ----
  Attachments:   (none, or list)

Should I proceed?
```

**Approval is explicit.**  "Yes" / "send" / "go ahead" / "proceed" / "do it".  Anything else is NOT approval.  If Sam edits, re-compose, re-read back, wait again.

## Quick Self-Check

Before firing any email tool, verify:

- [ ] `/compose-email` skill invoked this composition cycle (you are reading this)
- [ ] Writing style reference loaded and 8-point self-check passed
- [ ] Byline appended (matched to `$OTL_AGENT_SLUG` from lookup table above)
- [ ] Footer HTML appended verbatim (the full branded block, not a plain-text substitute)
- [ ] Tool is from the routing table above (not a prohibited tool)
- [ ] If sending/forwarding: Layer 3 readback delivered and explicit approval received

## Reference

- **Writing style:** `otl_support/claude_headspace/data/references/sam-writing-style.md`
- **Email hardening (full security model):** `otl_support/claude_headspace/data/references/email-hardening.md`
- **Security layers:** tool whitelist (L1) > authority matrix (L2) > content approval (L3) > closed-world action (L4) > context boundary (L5)
