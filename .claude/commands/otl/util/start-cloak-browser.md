---
name: Start Cloak Browser
description: Launch stealth Chromium with CDP debugging port for agent-browser connection to bot-protected sites
category: Util
tags: [browser, stealth, cdp, cloak]
---

Launch Cloak Browser (stealth Chromium) with remote debugging on port 9333 for connecting agent-browser to bot-protected sites.

**When to use this instead of `/otl:util:start-chrome-debug`:** Target site has bot detection (Cloudflare, reCAPTCHA, fingerprint gates). For internal sites or sites you control, use regular Chrome on port 9222.

**Run these commands:**

```bash
CLOAK_BIN=$(python3 -c "import cloakbrowser; print(cloakbrowser.binary_info()['binary_path'])")
STEALTH_ARGS=$(python3 -c "import cloakbrowser; print(' '.join(cloakbrowser.get_default_stealth_args()))")

"$CLOAK_BIN" $STEALTH_ARGS \
  --remote-debugging-port=9333 \
  --user-data-dir=/tmp/cloak-debug-profile &
```

**Verify:** `sleep 3 && curl -s http://localhost:9333/json/version > /dev/null && echo 'Cloak browser started' || echo 'ERROR: failed to start'`

**Connect agent-browser:**

```bash
agent-browser --cdp 9333 open "https://target-site.com"
agent-browser --cdp 9333 snapshot
```

**Notes:**
- Uses port **9333** (not 9222) — can run alongside regular Chrome debug instance
- Profile persists in `/tmp/cloak-debug-profile` until system restart
- Passes Cloudflare Turnstile, FingerprintJS, BrowserScan, reCAPTCHA v3 (0.9 score)
- For proxy: add `--proxy-server=socks5://host:port` to the launch command
- Binary location: `~/.cloakbrowser/` (managed by `cloakbrowser` Python package)
