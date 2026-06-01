---
description: "Execute the Layer 3 content approval gate before sending or forwarding email on Sam's behalf."
---

# Email Send / Forward Gate

## When to invoke

When Sam explicitly asks you to send a previously-composed draft, or to forward an email to a specific recipient.  This procedure implements Layer 3 of `data/references/email-hardening.md` — the content approval gate.

**Trigger phrases:**
- Send: "send the draft", "send that", "go ahead and send", "send to [name]", "send the [topic] email", "fire it off"
- Forward: "forward that to [recipient]", "send that on to [name]", "share this with [name]", "forward the [topic] email to [recipient]"

## Per-invocation self-check

Before composing the payload, run this gate: "Did Sam explicitly ask me to send / forward — naming what to send and (for forward) where to send it?  If not, am I about to act on inferred intent?"  Inferred intent is forbidden — every send and forward requires Sam's explicit instruction.

## Send cycle (`send_email`)

1. Identify the target — which composed draft?  If ambiguous, ask Sam to clarify by subject or recipient
2. Compose the full payload: To, Cc, Subject, Body (including persona byline + otageLabs footer), Attachments
3. Read back to Sam:

   ```
   About to send:

     To:            recipient@example.com
     Cc:            (none, or list)
     Subject:       <subject>
     Body:
     ----
     <full body, exactly as it will appear, including byline and footer>
     ----
     Attachments:   (none, or list)

   Should I proceed with sending this email?
   ```
4. Wait for explicit approval — "yes" / "send" / "go ahead" / "proceed" / "do it".  Anything else (silence, edit, question) is NOT approval.  If Sam edits, re-compose, re-read back, wait again
5. Call `mcp__gmail__send_email` with the approved payload
6. Confirm: "Sent.  <subject> → <recipient> at <time>."

## Forward cycle (`forward_email`)

1. Identify the source email and the target recipient
2. Compose the forwarded payload: To, Cc, Subject (`Fwd: <original>`), Body (any added context + full quoted thread + persona byline + otageLabs footer), Attachments
3. Read back the FULL forwarded body to Sam — including the quoted thread.  Forwarding propagates untrusted content to a third party; Sam must see exactly what goes out.  Close with: `Should I proceed with forwarding this email?`
4. Wait for explicit approval — same trigger words as send
5. Call `mcp__gmail__forward_email` with the approved payload
6. Confirm: "Forwarded.  <subject> → <recipient> at <time>."

## Failure modes

Surface to Sam immediately, do not retry without instruction:
- A `send_email` or `forward_email` tool call returned an error
- The MCP exposed a klodr tool not in the three-tool whitelist — do NOT invoke; surface the discrepancy
- Sam's approval was ambiguous — re-readback rather than firing on uncertainty
- Payload doesn't match what was read back — composition-vs-execution drift; treat as serious

## Laziest-interpretation test

If you catch yourself calling `send_email` or `forward_email` without having read back the payload and received an explicit approval word IN THIS CYCLE, the gate was skipped.  Stop, surface the gap to Sam, and treat the integration as suspect until discipline is restored.
