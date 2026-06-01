---
name: Start Chrome Debug
description: Launch Chrome with CDP debugging port for agent-browser connection
category: Util
tags: [browser, debug, cdp]
---

Start Google Chrome with remote debugging enabled on port 9222 using a separate profile (so your main Chrome stays open).

**Run this command:**

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-profile &
```

**After launching, verify Chrome is accessible:** `sleep 2 && curl -s http://localhost:9222/json/version > /dev/null && echo 'Chrome started successfully' || echo 'ERROR: Chrome failed to start'`. **If verification fails, report the error — do not assume Chrome is running.**

**Notes:**
- Opens a **separate Chrome instance** - your main Chrome windows stay untouched
- Use `/otl/util/connect-agent-browser` to connect agent-browser
- This debug instance won't have your logged-in sessions (it's a fresh profile)
- The profile persists in `/tmp/chrome-debug-profile` until system restart
