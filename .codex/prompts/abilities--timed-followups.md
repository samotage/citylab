---
description: Set timed callbacks for tasks that take time or need follow-up after
  a delay. Use ScheduleWakeup so the operator is never left waiting.
---

# Timed Follow-Ups

## Procedure

When a task takes time to process, or when something needs checking after a delay — set a timed callback.

### Methodology

1. Call `ScheduleWakeup` with `delaySeconds` set to the wait duration, `reason` describing what's being waited on, and `prompt` set to the follow-up instruction so the loop resumes.
2. When the wake-up fires, continue with the follow-up action and report to the operator in chat.
3. Push a macOS notification via the notify API when the follow-up fires so the operator knows to check in.

Multiple concurrent waits: set a separate `ScheduleWakeup` for each.  Name each clearly in the `reason` field.

### Rules

- The operator should never be left waiting without a callback.  If there's a wait, there's a wake-up.
- Name each callback clearly so the operator (and you) can tell what it's for when it fires.
- Don't set unnecessarily short intervals — match the delay to what you're actually waiting for.

## Anti-Convergence

- Leaving a timed task without a `ScheduleWakeup` callback — if there's a wait, there's a wake-up
- Setting a wake-up but forgetting to push a notification when it fires — the operator may not be watching the chat

## Alignment Signals

- Long-running tasks with no `ScheduleWakeup` set (drift)

## Quality Definitions

- [ ] Timed follow-ups use `ScheduleWakeup` + notify API — never leave the operator waiting without a callback
