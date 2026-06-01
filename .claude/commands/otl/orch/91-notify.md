---
name: '91: notify'
description: 'Utility: manually send Slack notifications'
---

# Notify (Utility)

Send a manual Slack notification for debugging or utility purposes.

**DO NOT call `TodoWrite`.** The orchestration plan strip in Headspace is rendered exclusively from the lead orchestrator's TodoWrite calls. Worker TodoWrite calls are invisible to Headspace under the sub-agent visibility constraint (Workshop #170, decision D7) and would break the single-owner invariant. This is a hard rule — no exceptions.

**Input:**
- `{{type}}` — notification type: `decision_needed`, `error`, `complete`
- `{{message}}` — message to send

---

## Send Notification

### decision_needed

```bash
ruby orch/notifier.rb decision_needed --message "{{message}}" --change-name "[change name]" --checkpoint "[type]" --action "[what to do]"
```

### error

```bash
ruby orch/notifier.rb error --message "{{message}}" --change-name "[change name]" --phase "[phase]" --resolution "[fix]"
```

### complete

```bash
ruby orch/notifier.rb complete --message "{{message}}" --change-name "[change name]"
```

---

If `SLACK_WEBHOOK_URL` is not set, the notification will be skipped with a warning.
