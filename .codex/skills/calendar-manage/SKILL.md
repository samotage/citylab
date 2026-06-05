---
name: calendar-manage
description: "Manage Sam's Google Calendar — create, reschedule, cancel, RSVP to events, check availability. MUST be invoked before any calendar tool call. Encodes: AEST timezone conversion, modality classification (in-person/video/phone), pre-flight confirmation gate for external attendees, availability check before proposing times, description composition in Sam's voice, post-execution response audit."
allowed-tools:
  - mcp__claude_ai_Google_Calendar__list_events
  - mcp__claude_ai_Google_Calendar__create_event
  - mcp__claude_ai_Google_Calendar__update_event
  - mcp__claude_ai_Google_Calendar__delete_event
  - mcp__claude_ai_Google_Calendar__respond_to_event
  - mcp__claude_ai_Google_Calendar__suggest_time
  - mcp__claude_ai_Google_Calendar__get_event
  - mcp__claude_ai_Google_Calendar__list_calendars
  - Read
version: 1.0.0
---

# Calendar Manage

Every calendar operation goes through this skill.  No exceptions.

## Timezone Rule

All Google Calendar API timestamps are UTC.  **Convert to AEST (UTC+10) or AEDT (UTC+11) before any output or action.**  Run `date "+%Z"` to determine which offset is active.

- Never present raw UTC timestamps to Sam
- Never compose event times without confirming the local offset first
- All readback times include the timezone abbreviation: "2:00pm AEST"

This is a tool-surface rule, not a persona-specific rule.

## Reading the Calendar

1. Run `date "+%Y-%m-%dT%H:%M:%S%z"` to anchor "now"
2. Call `gcal_list_events` with `timeMin` = now, `timeMax` = end of target range
3. Convert all returned timestamps to local time before presenting
4. For each event: time (local), summary, key attendees, prep notes if any

## Creating / Modifying Events

### Step 1 — Modality classification

Classify from Sam's request before composing the payload:

| Modality | Trigger phrases | `addGoogleMeetUrl` | `location` |
|---|---|---|---|
| **In-person** | lunch, coffee, breakfast, dinner, drinks, brunch, face-to-face, in person, on-site, drop in, swing by, meet at, [venue name] | `false` | as Sam named, else blank |
| **Video** | Google Meet, Meet, Zoom, Teams, video call, video chat, online meeting, remote, dial in, jump on a call, virtual, screen-share | `true` | blank |
| **Phone** | phone call, give me a call, ring me, call me, on the phone, dial | `false` | blank |
| **Ambiguous** | meeting, catch up, chat, sync, get together, see [name], schedule [name] (no other signal) | ASK first | ASK first |

**Trap:** "Google Calendar" is NOT a video trigger.  "Google Meet" is.  The word "Meet" carries the modality, not "Google."  This is the canonical Georgina failure — a Meet link on a lunch.

**Solo events skip modality.**  No external attendees (time-blocks, focus time, reminders) — default `addGoogleMeetUrl: false`, `location` as specified or blank.  No lexicon lookup, no pre-flight gate.

**Location:** if Sam named a venue, set verbatim.  If not, leave blank — never ask, never invent.

### Step 2 — Availability check

Before proposing any meeting time:
- `gcal_find_my_free_time` for Sam's availability
- `gcal_find_meeting_times` when coordinating with multiple attendees
- Filter for sensible hours (default 9am–5pm AEST unless Sam specifies otherwise)
- Flag conflicts or back-to-back sequences

### Step 3 — Description composition

Events with external attendees need a description.  Load `otl_support/claude_headspace/data/references/sam-writing-style.md` Ghost-writing Register if not loaded this cycle.

| Context | Style |
|---------|-------|
| Casual (lunch, coffee, drinks) | One line.  "Lunch — looking forward to catching up." |
| Business (demo, partner call) | One short paragraph: purpose + any prep needed. |
| Internal (1:1, recurring sync) | One line stating purpose. |

No email footer in calendar descriptions.  Avoid banned phrases from writing style reference.

### Step 4 — Pre-flight confirmation gate

**Fires when:** event has external (non-Sam) attendees AND operation is create, reschedule, or cancel.

**Does NOT fire:** solo events, RSVPs, cosmetic-only updates on unattended events.

Read back the full payload:

```
About to <create | reschedule | cancel>:

  Title:        [event title]
  When:         [day, date, time range — AEST/AEDT]
  Attendees:    [list] (and you)
  Modality:     [In-person | Video | Phone]
  Location:     [venue or blank]
  Meet link:    [Yes | No]
  Description:  [full text]
  Notification: ALL attendees

Should I proceed?
```

**Approval is explicit.**  "Yes" / "send" / "go ahead" / "proceed" / "do it".  Anything else is NOT approval.  If Sam edits, re-compose, re-read back, wait again.

### Step 5 — Post-execution audit

After every `gcal_create_event` or `gcal_update_event`, inspect the API response:

- `addGoogleMeetUrl` was `false` but response has `conferenceUrl` → **failure**.  Do NOT confirm success.  Route to Sam: "Invite went out with a Meet link despite requesting none.  Remove manually in Google Calendar — the update tool can't strip conference data."
- `addGoogleMeetUrl` was `true` but no `conferenceUrl` → flag: "Meet link wasn't attached.  Add manually in Google Calendar."
- Response matches request → proceed to confirmation.

If the audit found a discrepancy, the failure message IS the response.  No success confirmation until resolved.

### Step 6 — Confirmation

Only after audit passes: "Booked.  Lunch with Georgina, Thursday 2pm AEST — in-person, no Meet link, attendee notified."

## Quick Self-Check

Before any calendar tool call:

- [ ] Timestamps converted to AEST/AEDT (run `date "+%Z"` to confirm offset)
- [ ] Modality classified from Sam's request (not guessed)
- [ ] Solo event? → skip gate, execute directly
- [ ] External attendees? → pre-flight readback delivered, approval received
- [ ] Availability checked before proposing times
- [ ] Description composed in Sam's voice (external attendees only)
- [ ] Post-execution audit completed before confirming success

## Reference

- **Writing style:** `otl_support/claude_headspace/data/references/sam-writing-style.md`
- **Email hardening (shared gate patterns):** `otl_support/claude_headspace/data/references/email-hardening.md`
