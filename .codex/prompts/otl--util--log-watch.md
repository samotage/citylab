---
description: Scan application logs for errors, check server health, and report findings
  with fix recommendations
---

# Log Watch

You are performing a comprehensive health check and log analysis of the Claude Headspace application. Your goal is to find errors, categorise them, separate signal from noise, and report actionable findings.

**This is a read-only analysis.** Do not modify any code unless the user explicitly asks for fixes after reviewing the report.

---

## Phase 1: Server Health (parallel)

Run all of the following checks in parallel:

1. **Process check** — verify the server is running:
   ```bash
   ps aux | grep -E "run\.py" | grep -v grep
   ```

2. **Health endpoint** — hit the health API:
   ```bash
   curl -sk https://smac.griffin-blenny.ts.net:5055/health
   ```
   Report: overall status, database connectivity, background thread status (alive/dead), SSE connection count.

3. **Uptime** — check when the server was last started:
   ```bash
   grep "Serving Flask app\|Running on\|Database connected" /Users/samotage/dev/otagelabs/claude_headspace/logs/app.log | tail -5
   ```

If the server is not running, report that immediately and skip to Phase 5 (Recommendations).

---

## Phase 2: Log Scan

### 2a. Identify all log sources

The application has these log locations:
- **Primary:** `/Users/samotage/dev/otagelabs/claude_headspace/logs/app.log` (active, rotating)
- **Rotated:** `app.log.1` through `app.log.5` (if they exist)
- **Server output:** `/tmp/claude_headspace.log` (stdout/stderr from startup)

### 2b. Error extraction (parallel across all log files that exist)

For each log file, run:
```bash
grep -c "ERROR\|CRITICAL" <log_file>
```

Focus analysis on files with errors > 0.

### 2c. Error categorisation

For each log file with errors, categorise by frequency:
```bash
grep "ERROR\|CRITICAL" <log_file> | sed 's/^[0-9T:.+-]* - //' | sort | uniq -c | sort -rn | head -30
```

### 2d. Separate signal from noise

**Test-generated errors (IGNORE):** Errors from route/unit tests use the logger prefix `src.claude_headspace.routes.*` or `src.claude_headspace.services.*` (the `src.` prefix distinguishes test imports from production). These are expected error-path tests and should be reported as "test noise" but not flagged as issues.

**Real application errors (REPORT):** Errors from `claude_headspace.services.*` or `claude_headspace.routes.*` (no `src.` prefix) are production errors.

### 2e. Timeline analysis

For real errors, determine:
- When they started (first occurrence timestamp)
- When they stopped (last occurrence timestamp), or if they're **still occurring**
- Whether they're clustered (burst during restart) or continuous (ongoing issue)

```bash
# First and last error timestamps
grep "ERROR" <log_file> | grep -v "^.*src\." | head -1 | awk '{print $1}'
grep "ERROR" <log_file> | grep -v "^.*src\." | tail -1 | awk '{print $1}'
```

### 2f. Traceback extraction

For the top 3 most frequent real error categories, extract a representative traceback:
```bash
grep -B 2 -A 20 "<error_message>" <log_file> | tail -25
```

Identify the **root cause** from each traceback (e.g., `UndefinedTable`, `OperationalError`, `ConnectionRefusedError`).

---

## Phase 3: Database & Connection Health

1. **Check PostgreSQL connection count:**
   ```bash
   psql -d claude_headspace -c "SELECT count(*) as total_connections, state FROM pg_stat_activity GROUP BY state ORDER BY total_connections DESC;" 2>&1
   ```

2. **Check for connection pool pressure:**
   ```bash
   psql -d claude_headspace -c "SELECT count(*) as total FROM pg_stat_activity WHERE datname = 'claude_headspace';" 2>&1
   ```

3. **Check max_connections vs current usage:**
   ```bash
   psql -c "SHOW max_connections;" 2>&1
   ```

---

## Phase 4: Recent Activity Check

Check for warning signs in the last 10 minutes of logs:
```bash
grep "WARNING\|ERROR\|CRITICAL" <log_file> | awk -v cutoff="$(date -v-10M '+%Y-%m-%dT%H:%M:%S')" '$1 >= cutoff'
```

If there are recent warnings, include them in the report.

---

## Phase 5: Report

Generate a structured report with these sections:

### Server Status
- Running: yes/no
- Uptime: when last started
- Health: healthy/degraded/down
- Background threads: list status of each
- SSE connections: count

### Error Summary Table

| # | Error Category | Count | Source | Timeframe | Status | Root Cause |
|---|---------------|-------|--------|-----------|--------|------------|
| 1 | ... | ... | app.log | 22:13-22:14 | Resolved | UndefinedTable |
| 2 | ... | ... | app.log.1 | 21:30-21:41 | Recurring | Connection pool |

- **Status** values: `Active` (still occurring), `Resolved` (stopped), `Recurring` (happened multiple times historically), `Test noise` (from test runs)
- **Source**: which log file(s)
- **Root Cause**: the underlying exception/issue

### Active Issues (errors in the last 30 minutes)
List any errors that are currently happening with full context.

### Historical Issues (resolved but worth noting)
List resolved errors with timestamps and whether they could recur.

### Test Noise (acknowledged, no action needed)
Count of test-generated errors, listed for completeness.

### Database Health
- Connection count vs max_connections
- Pool pressure assessment

### Recommendations
For each active or recurring issue, provide:
1. **What's happening** — one-sentence description
2. **Root cause** — the underlying technical issue
3. **Fix** — specific code change or operational action needed
4. **Files involved** — exact file paths
5. **Priority** — Critical (actively breaking) / High (will recur) / Low (cosmetic)

---

## Rules

- **Do NOT modify any files** unless the user explicitly asks for fixes
- **Do NOT restart the server** — this is read-only analysis
- **Maximise parallelism** — run independent checks concurrently
- **Be precise about timestamps** — always report when errors occurred, not just that they exist
- **Distinguish test noise** — never flag test-generated errors as production issues
- **Check ALL log files** — don't stop at app.log, check rotated logs too
- **Report clean results** — if logs are clean, say so clearly: "Logs are clean. Zero errors since [timestamp]."
