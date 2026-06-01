---
description: Connect agent-browser to Chrome via CDP and take a snapshot
---

Connect agent-browser to a running Chrome instance via CDP port 9222.

**Prerequisites:**
- Chrome must be running with `--remote-debugging-port=9222`
- **Before connecting, verify Chrome is running on port 9222:** `curl -s http://localhost:9222/json/version > /dev/null && echo 'Chrome running' || echo 'Chrome NOT running — run /otl/util/start-chrome-debug first'`. **If Chrome is not running, do NOT proceed.**
- Note: The debug Chrome uses a separate profile - you won't have your logged-in sessions
- **If the site blocks you** (Cloudflare challenge, bot detection, empty content): use `/otl:util:start-cloak-browser` instead (port 9333) or invoke `/abilities:cloak-browser`

## Instructions

1. Navigate to the provided URL:

```bash
agent-browser --cdp 9222 open "$ARGUMENTS"
```

2. Take a snapshot to see the page content:

```bash
agent-browser --cdp 9222 snapshot
```

## Other Commands

```bash
# Take accessibility snapshot of current page
agent-browser --cdp 9222 snapshot

# Interactive elements only
agent-browser --cdp 9222 snapshot -i

# Click an element by ref (from snapshot)
agent-browser --cdp 9222 click @e5

# Type into an element
agent-browser --cdp 9222 type @e3 "hello"

# Take screenshot
agent-browser --cdp 9222 screenshot
```

## Authentication

### Kenwood (pre-configured)

Kenwood requires session-based auth. A profile is saved in the agent-browser vault. Authenticate once per Chrome launch:

```bash
agent-browser --cdp 9222 auth login kenwood
```

This navigates to `/login`, fills the form with the dev credentials, and submits. The session cookie persists in the Chrome debug profile — no need to re-authenticate between commands.

### Other sites (Bearer token)

For sites that use token-based auth:

```bash
agent-browser --cdp 9222 open "$ARGUMENTS" --headers '{"Authorization":"Bearer YOUR_TOKEN_HERE"}'
```
