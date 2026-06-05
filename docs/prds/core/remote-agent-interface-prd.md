---
validation:
  status: valid
  validated_at: '2026-06-05T11:19:59+10:00'
---

## Product Requirements Document (PRD) — Remote Agent Interface

**Project:** CityLab
**Scope:** Embed a Headspace remote agent (Ray) into CityLab using the Kenwood Mission Control pattern — chat panel iframe, agent session lifecycle, and conversational interaction with energy market data via `cli-citylab`.
**Author:** Robbo
**Status:** Draft

---

## Executive Summary

CityLab is an energy market monitoring platform built for the Watt The Hack hackathon (Grid Guardian track). It ingests Victorian NEM data, weather forecasts, and solar irradiance into a dashboard. What it lacks is an operational agent — an AI that can interpret and act on this data conversationally.

This PRD specifies a remote agent interface that embeds a Headspace agent (Ray, NEM energy market analyst) directly into the CityLab UI. The pattern is borrowed wholesale from Kenwood's Mission Control: an iframe-based chat panel alongside the dashboard, backed by agent session lifecycle management. Ray's only instrument panel is `cli-citylab` — every query goes through the REST API surface, never through Flask internals or direct database access.

The result: an operator can ask Ray "what's the current energy price?", "what's the generation mix look like?", "any weather impacts coming?" and get answers grounded in live CityLab data. This conversational market intelligence is the hackathon differentiator — it transforms a passive dashboard into an agent-operated energy monitoring system.

---

## 1. Context & Purpose

### 1.1 Context

CityLab has a complete data pipeline (OpenNEM, BOM, Solcast) and a rich CLI wrapper (`cli-citylab`) exposing energy, weather, solar, data, and schedule commands. It has a dashboard at `/energy` that visualises this data. What's missing is the agent layer — an AI that lives inside the application, queries the data conversationally, and provides market intelligence on demand.

The Kenwood and Beans applications in the otageLabs portfolio have proven remote agent patterns. Kenwood embeds the agent in its Mission Control UI (chat panel iframe, session lifecycle, skill injection). Beans has the most mature backend infrastructure (RemoteAgent/RemoteAgentSession models, HeadspaceClient, service layer with audit). This PRD combines Kenwood's UI integration pattern with Beans' backend maturity, adapted for CityLab's energy domain.

Ray (energy-market-analyst-ray-50) already exists as a Headspace persona — a NEM domain specialist who provides market analysis. He doesn't write code; he interprets market conditions. His levers in CityLab are the `cli-citylab` commands.

### 1.2 Target User

The hackathon demo audience and judges. The operator (Sam) interacting with Ray during the live demo to show AI-driven energy market operations.

### 1.3 Success Moment

The operator opens CityLab's energy dashboard, sees Ray's chat panel alongside the market data, and asks "What's the current spot price and where is it heading?" Ray queries `cli-citylab energy summary`, interprets the result, and responds with a market-aware answer — all visible to the audience in real time.

---

## 2. Scope

### 2.1 In Scope

- Agent configuration model for storing available agent personas (Ray as the initial and default agent)
- Agent session model for tracking running sessions (Headspace agent ID, embed URL, session token, status)
- HeadspaceClient with full lifecycle operations (create, check alive, shutdown, send message), replacing the existing `trigger_agent()` stub
- Agent service layer encapsulating session lifecycle business logic (resume-or-create, health check, graceful shutdown)
- Agent API routes for the UI chat panel (init, shutdown, status, send message)
- Chat panel UI embedded in the energy dashboard — Headspace iframe with session controls
- Agent CLI commands for operator management (start, stop, status, check, list, message, add-config, set-default)
- Database migration for agent configuration and session tables
- Config.yaml headspace section update with persona configuration (slug, name, role)
- Conversation-first startup: agent greets the operator and waits for questions rather than dumping an orientation data wall

### 2.2 Out of Scope

- Skill injection registry (Kenwood's YAML button-to-skill mapping) — future enhancement after v1
- Multi-agent UI with tabbed chat panels for concurrent agents — one agent at a time for v1
- Agent-driven autonomous scheduled actions (Ray triggering fetches on cron) — the levers exist, agent pulls them conversationally
- Charting enhancements — separate PRD in progress
- Ray's persona skill file — already exists in Headspace
- Audit logging service — CityLab does not have one; session lifecycle is tracked via model state only

---

## 3. Success Criteria

### 3.1 Functional Success Criteria

- SC1: Ray can be started from the CityLab energy dashboard UI and appears in an embedded chat panel
- SC2: Ray can query CityLab data conversationally via `cli-citylab` commands (energy summary, prices, generation, forecasts, weather, solar, market intelligence, data verify)
- SC3: Agent session persists across page refreshes (resume-or-create pattern)
- SC4: Agent session status is visible in the UI (active / disconnected / dead)
- SC5: Agent can be shut down from the UI
- SC6: Agent can be managed via CLI commands (start, stop, status, check)
- SC7: Agent configuration (persona slug, name) is stored in the database and seedable

### 3.2 Non-Functional Success Criteria

- SC8: HeadspaceClient handles transient errors gracefully (connection failures, timeouts) without crashing the application
- SC9: Session token is never exposed to the frontend — only the embed URL is sent to the browser
- SC10: Agent interaction adds no perceptible latency to the energy dashboard rendering

---

## 4. Functional Requirements (FRs)

### Agent Configuration

- **FR1:** The system stores agent configuration records with: name, persona slug (unique), description, active/inactive flag, and default flag
- **FR2:** One agent can be marked as the default; setting a new default unsets the previous one
- **FR3:** Agent configurations are seedable from `config.yaml` via a CLI command or application startup
- **FR4:** The initial seed includes Ray (energy-market-analyst-ray-50) as the default agent

### Session Lifecycle

- **FR5:** Starting an agent creates a session via the Headspace Remote Agent API and stores the session record (Headspace agent ID, embed URL, session token, status)
- **FR6:** Resume-or-create logic: if an active session exists for the requested persona, check if the agent is alive; reuse if alive, mark dead and create new if not
- **FR7:** Agent health can be checked via a liveness probe to Headspace; dead agents are marked in the database
- **FR8:** Agent sessions can be gracefully shut down, calling Headspace shutdown and updating the local session record
- **FR9:** At most one active session per agent configuration at a time

### HeadspaceClient

- **FR10:** The HeadspaceClient supports four operations: create_agent (with persona slug and optional initial prompt), check_alive (with session token auth), shutdown_agent, and send_message
- **FR11:** The client retries once on transient errors (408, 502, 503) for create_agent
- **FR12:** The client replaces the existing `trigger_agent()` function in headspace_client.py

### Agent API Routes

- **FR13:** POST endpoint to initialise an agent session (resume-or-create), returning session ID, persona details, embed URL, and status
- **FR14:** POST endpoint to shut down an agent session
- **FR15:** GET endpoint to check agent session status (with live Headspace liveness check for active sessions)
- **FR16:** POST endpoint to send a message to a running agent session

### Chat Panel UI

- **FR17:** The energy dashboard includes an embedded chat panel displaying the Headspace agent iframe
- **FR18:** The chat panel has controls to start and stop the agent
- **FR19:** The chat panel shows the agent's status (active, connecting, disconnected)
- **FR20:** The chat panel loads existing active sessions on page load (resume across refreshes)
- **FR21:** The chat panel is conversation-first: Ray greets the operator on startup and waits for questions, rather than executing an automated orientation sequence

### Agent CLI Commands

- **FR22:** CLI commands for session management: start (with optional --persona flag), stop, status, check (alive probe)
- **FR23:** CLI commands for configuration: list available agents, add a new agent config, set default agent
- **FR24:** CLI command to send a message to the active agent session

### Configuration

- **FR25:** The `config.yaml` headspace section supports a `personas` list, each with slug, name, and role
- **FR26:** The `config.yaml` headspace section supports `project_name` for the Headspace project identifier

---

## 5. Non-Functional Requirements (NFRs)

- **NFR1:** Session tokens are stored server-side only — never returned in API responses or rendered in templates
- **NFR2:** HeadspaceClient wraps all connection and timeout errors in a domain exception with both technical and user-friendly messages
- **NFR3:** All agent API routes require authentication (consistent with existing CityLab auth model)
- **NFR4:** Agent CLI commands use the same `cli-citylab` pattern (Click groups, text/JSON output format)

---

## 6. UI Overview

The energy dashboard at `/energy` gains a chat panel on the right side (Kenwood Mission Control layout):

- **Left ~67%:** Existing energy dashboard (price hero, generation mix, interconnectors, weather, forecasts, source health)
- **Right ~33%:** Agent chat panel containing:
  - Agent status indicator (name, status badge)
  - Start/Stop button
  - Headspace iframe (the conversational interface)

The chat panel is always visible when the agent is active. When no agent is running, the panel shows an empty state with a "Start Agent" button. The layout is responsive — on narrow screens, the chat panel could collapse or stack below the dashboard.
