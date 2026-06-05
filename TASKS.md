# Tasks: Remote Agent Interface (Ray)

Source PRD: docs/prds/core/remote-agent-interface-prd.md
Branch: feature/hack-remote-agent-interface-prd

## Task List

- [x] 1. **Config: headspace section** — Update `config.yaml` headspace section with `url`, `api_token`, `project_name`, and a `personas` list (each with `slug`, `name`, `role`); seed Ray (energy-market-analyst-ray-50) as default. Add the corresponding DEFAULTS / ENV_MAPPINGS entries in `src/citylab/config.py` (FR25, FR26). (Config change — show diff before applying.)

- [x] 2. **Models: agent config + session** — Add `AgentConfig` model (name, persona_slug unique, description, is_active, is_default) and `AgentSession` model (FK to config, headspace_agent_id, embed_url, session_token, status, timestamps) under `src/citylab/models/agent.py`; register in `models/__init__.py`. Provide for one default config and at-most-one active session per config (FR1, FR2, FR5, FR9).

- [x] 3. **Migration: agent tables** — Generate Alembic migration for `agent_config` and `agent_session` tables with the unique constraint on persona_slug. Run `flask db upgrade` against the `citylab` dev DB (confirm target DB first).

- [x] 4. **HeadspaceClient lifecycle** — Replace `trigger_agent()` in `src/citylab/services/headspace_client.py` with a client supporting `create_agent` (persona slug + optional initial prompt, retry once on 408/502/503), `check_alive` (session token auth), `shutdown_agent`, and `send_message`. Wrap connection/timeout errors in a domain exception carrying technical + user-friendly messages (FR10, FR11, FR12, NFR2).

- [x] 5. **Agent service layer** — Add `src/citylab/services/agent_service.py` encapsulating resume-or-create (check alive, reuse if alive else mark dead + create new), health check, graceful shutdown, send message, and config seeding from `config.yaml`. Session token handled server-side only (NFR1). (FR3, FR6, FR7, FR8)

- [ ] 6. **Agent API routes** — Add `src/citylab/routes/api_v1/agent.py` with: POST init (resume-or-create -> session id, persona, embed_url, status), POST shutdown, GET status (live liveness check for active sessions), POST send-message. Register blueprint. Never return session_token; embed_url only (FR13, FR14, FR15, FR16, NFR1, NFR3).

- [ ] 7. **CLI seed + config commands** — Add Flask CLI `seed-agents` (or extend existing seeding) to seed AgentConfig from config.yaml (FR3, FR4). Add `cli-citylab` agent config commands: list, add-config, set-default (FR23). Uses cli_wrapper REST/Bearer pattern.

- [ ] 8. **CLI session commands** — Add `src/citylab/cli_wrapper/commands_agent.py` with `cli-citylab agent` group: start (--persona), stop, status, check, message — hitting the agent API routes via the Bearer-auth client; register the group in `__main__.py` (FR22, FR24, NFR4).

- [ ] 9. **Chat panel UI** — Add the chat panel to the `/energy` dashboard (right ~33%, dashboard left ~67%, Kenwood Mission Control layout): status indicator (name + badge), Start/Stop button, Headspace iframe, empty state with "Start Agent". Wire start/stop/status to the agent API routes; resume active session on page load. Conversation-first startup — Ray greets and waits for questions, no orientation data wall (FR17, FR18, FR19, FR20, FR21).

- [ ] 10. **CSS build + responsive layout** — Add any custom chat-panel styles to `static/css/src/input.css`, rebuild with `npx tailwindcss` (v3, NOT v4). Ensure responsive stacking on narrow screens; verify key custom selectors survive the build.

- [ ] 11. **Tests** — Add targeted tests using the existing fixture system (`app`, `client`, `db_session`): HeadspaceClient (mock requests — retry + error wrapping), agent_service resume-or-create logic, agent API routes (auth required, no session_token leak in response, init/status/shutdown), and model default/active-session constraints. Run `pytest` against `citylab_test`; confirm no regressions.

## Demo Script

(No explicit Demo Script section in the PRD — synthesized from Success Moment §1.3 and Success Criteria SC1–SC7.)

1. Start the server (`./restart_server.sh`) and confirm health: `curl http://127.0.0.1:15099/health`.
2. Seed agents (`flask seed-agents` or app startup seed) and confirm Ray is present and default: `cli-citylab agent list` shows energy-market-analyst-ray-50 as default (SC7, FR4).
3. Open the energy dashboard at `/energy`. The chat panel sits on the right in its empty state with a "Start Agent" button (SC1, UI Overview §6).
4. Click "Start Agent". Ray's Headspace iframe loads and Ray greets the operator conversationally, waiting for questions — no automated data dump (FR21). Status badge shows active (SC4).
5. Ask Ray: "What's the current spot price and where is it heading?" Ray queries `cli-citylab energy summary` and answers with a market-aware interpretation (SC2, Success Moment §1.3).
6. Ask a follow-up: "What's the generation mix look like, and any weather impacts coming?" Ray uses `cli-citylab energy generation` / `weather` and responds (SC2).
7. Refresh the page — the active session resumes; the panel reconnects to the running agent rather than starting a new one (SC3, FR20).
8. Verify via CLI: `cli-citylab agent status` shows the active session and `cli-citylab agent check` confirms liveness (SC6).
9. Click "Stop" in the UI (or `cli-citylab agent stop`) — the session shuts down and the badge returns to disconnected (SC5).
