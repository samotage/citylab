---
description: Launch a stealth browser session for browsing bot-protected sites. Use
  when regular browsing gets blocked by Cloudflare, reCAPTCHA, or fingerprint detection.
---

# Cloak Browser

## When to Use

Use cloak browser when you need to browse a site that blocks automated access:
- Cloudflare Turnstile or challenge pages
- reCAPTCHA gates
- Sites returning bot-block pages instead of content
- Fingerprint detection services blocking your requests
- Any external site where `WebFetch` or regular `agent-browser` returns blocked/empty content

## When NOT to Use

- Internal sites (Headspace dashboard, Kenwood, localhost services) — use regular `agent-browser`
- Sites that respond normally to `WebFetch` — no stealth needed
- Sites you control or have auth for — use `agent-browser --auto-connect` or `--cdp 9222`

## Procedure

### Resolve the binary path

```bash
CLOAK_BIN=$(python3 -c "import cloakbrowser; print(cloakbrowser.binary_info()['binary_path'])")
```

### Option A: Direct agent-browser with Cloak (preferred)

```bash
CLOAK_BIN=$(python3 -c "import cloakbrowser; print(cloakbrowser.binary_info()['binary_path'])")
agent-browser --executable-path "$CLOAK_BIN" --args "--no-sandbox,$(python3 -c "import cloakbrowser; print(','.join(cloakbrowser.get_default_stealth_args()[1:]))")" open "<url>"
```

Then interact normally (same session persists):

```bash
agent-browser snapshot
agent-browser click @e2
agent-browser screenshot
```

### Option B: CDP mode (persistent session across commands)

Launch Cloak Browser with CDP, then connect agent-browser separately:

```bash
CLOAK_BIN=$(python3 -c "import cloakbrowser; print(cloakbrowser.binary_info()['binary_path'])")
STEALTH_ARGS=$(python3 -c "import cloakbrowser; print(' '.join(cloakbrowser.get_default_stealth_args()))")

"$CLOAK_BIN" $STEALTH_ARGS --remote-debugging-port=9333 --user-data-dir=/tmp/cloak-debug-profile &
sleep 3

# Verify
curl -s http://localhost:9333/json/version > /dev/null && echo 'Cloak browser running' || echo 'FAILED'

# Connect
agent-browser --cdp 9333 open "<url>"
agent-browser --cdp 9333 snapshot
```

Uses port 9333 (not 9222) to avoid collision with regular Chrome debug instances.

### Option C: Python script (for scraping/extraction pipelines)

```python
from cloakbrowser import launch

browser = launch(headless=True, humanize=True, geoip=True)
page = browser.new_page()
page.goto("https://target-site.com")
content = page.content()
browser.close()
```

Key args: `headless=True/False`, `humanize=True` (Bezier mouse, keystroke timing), `geoip=True` (auto locale from proxy exit), `proxy=ProxySettings(server="socks5://host:port")`.

## Keeping Sessions Alive (authenticated browsing)

When the operator logs in manually and you need to keep that session for subsequent commands:

**Use `--headed` + `--profile` to persist cookies across commands:**

```bash
CLOAK_BIN=$(python3 -c "import cloakbrowser; print(cloakbrowser.binary_info()['binary_path'])")
agent-browser --executable-path "$CLOAK_BIN" --args "--no-sandbox,$(python3 -c "import cloakbrowser; print(','.join(cloakbrowser.get_default_stealth_args()[1:]))")" --headed --profile /tmp/cloak-session open "<url>"
```

The `--profile` flag persists all cookies, localStorage, and session data to disk. Subsequent commands with the same `--profile` path reuse the authenticated state — the browser won't reset to a logged-out page.

**Or use `--session-name` for named state persistence:**

```bash
agent-browser --executable-path "$CLOAK_BIN" --args "..." --headed --session-name ahrefs open "https://app.ahrefs.com"
```

**Critical:** Do NOT call `agent-browser close` between commands if you need the session to stay alive for operator interaction. The browser daemon keeps the window open between your commands automatically.

**CDP mode persistence:** If using CDP (Option B), the `--user-data-dir` already persists cookies — but the browser process must stay running. Do NOT re-launch the binary between commands.

## Limitations

- Does NOT solve CAPTCHAs — it prevents them from appearing. Hard challenges still need a separate solver
- Proxy rotation not bundled — bring your own proxy if rotating IPs
- Binary is ~200MB cached at `~/.cloakbrowser/`
- Not needed for sites that don't run bot detection

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: cloakbrowser` | Package not installed in this venv — `pip install cloakbrowser` |
| Binary not found | Run `python3 -c "import cloakbrowser; cloakbrowser.ensure_binary()"` to re-download |
| Still getting blocked | Add `--proxy` with a residential proxy. Datacenter IPs get blocked regardless of fingerprint |
| Port 9333 in use | Check `lsof -i :9333` and kill stale process |
| Chromium version mismatch | Run `python3 -c "import cloakbrowser; cloakbrowser.check_for_update()"` |
