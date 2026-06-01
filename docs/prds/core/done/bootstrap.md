---
validation:
  status: valid
  validated_at: '2026-06-01T14:22:52+10:00'
---

# CityLab — Project Bootstrap

## Problem

We need a fully scaffolded, agent-operable Flask application for the What the Hack hackathon. The app must support human users via a web UI and remote AI agents via CLI → REST API → HTTP endpoints. No domain features yet — this PRD delivers the skeleton that every subsequent feature PRD assumes exists.

## Approach

Bootstrap from the proven otageLabs Flask architecture (Kenwood pattern). Ten layers, all day-one:

### 1. App Factory + Config

- `src/citylab/__init__.py` with `create_app()` — standard initialization order: config → logging → database → auth → scheduler → blueprints → CLI
- `src/citylab/config.py` — three-tier cascade: DEFAULTS → `config.yaml` → env vars. `ENV_MAPPINGS` dict for all env overrides. `build_database_uri()` with `DATABASE_URL` override support for test isolation
- `config.yaml` at project root — server (host: 127.0.0.1, port: 5099, debug: true), logging, database (name: citylab), redis, api token, headspace config
- `.env.example` documenting all env vars

### 2. Database Layer

- `src/citylab/extensions.py` — SQLAlchemy 2.0 instance with `DeclarativeBase`, naming convention for constraints, Flask-Migrate instance
- `src/citylab/models/base.py` — `BaseModel` (id, created_at, updated_at) abstract base
- PostgreSQL via psycopg2-binary, connection pool config (pool_size=5, pool_pre_ping=True)
- `flask db init` / `flask db migrate` / `flask db upgrade` working out of the box
- Alembic `migrations/` directory initialized

### 3. Auth

- `src/citylab/models/user.py` — User model with email (unique), password_hash (Werkzeug PBKDF2), is_active. Inherits BaseModel
- Flask-Login with `@login_required` on UI routes, login_view pointing to login page
- Login page at `/login` — email + password form, Flask-WTF CSRF, POST validates and creates session
- Logout at `/logout` — clears session, redirects to login
- Admin seeding from `CITYLAB_ADMIN_EMAIL` / `CITYLAB_ADMIN_PASSWORD` env vars at startup
- Session config: 30-day lifetime, cookie name `session_citylab`, HttpOnly, SameSite=Lax
- CSRF protection globally, exempted on API blueprint

### 4. Route Structure

- `src/citylab/routes/` — blueprint directory
- `src/citylab/routes/main.py` — index route (`/`), login_required, renders dashboard template
- `src/citylab/routes/auth.py` — `/login`, `/logout`
- `src/citylab/routes/health.py` — `GET /health` (no auth), returns JSON with database, redis, scheduler status
- `src/citylab/routes/api_v1/__init__.py` — API blueprint factory at `/api/v1`
- `src/citylab/routes/api_v1/auth.py` — `@require_api_token` decorator, Bearer token validation from `api.token` config
- `src/citylab/routes/api_v1/app.py` — `GET /api/v1/app/status` returns app health + scheduler summary. This is the proof-of-concept endpoint the CLI calls
- `src/citylab/routes/api_v1/schedules.py` — CRUD for scheduled tasks: list, create, update, delete
- Standard JSON envelope: `{ "ok": true, "data": {...} }` / `{ "ok": false, "error": "...", "code": "..." }`
- Error handlers: 404, 500 returning JSON for API, HTML for UI

### 5. CLI Surface

- `src/citylab/cli_wrapper/` — Click-based CLI wrapping the REST API
- `src/citylab/cli_wrapper/client.py` — HTTP client with Bearer token auth, error mapping (exit codes 1/2/3)
- `src/citylab/cli_wrapper/config.py` — config discovery (finds config.yaml, reads api.token)
- Entry point in pyproject.toml: `cli-citylab = "citylab.cli_wrapper:main"`
- Command groups registered but empty (feature PRDs fill these in), plus:
  - `cli-citylab app status` — calls `GET /api/v1/app/status`, prints result
  - `cli-citylab schedules list` — calls `GET /api/v1/schedules`
  - `cli-citylab schedules create --name X --cron "*/5 * * * *" --persona Y --action Z` — calls `POST /api/v1/schedules`
  - `cli-citylab schedules delete --id N` — calls `DELETE /api/v1/schedules/{id}`
- Flask CLI commands (internal, not agent-facing):
  - `flask db upgrade/migrate/downgrade` (Flask-Migrate, automatic)
  - `flask seed-admin` — seeds admin user from env vars

### 6. Template + Static Foundation

- `templates/base.html` — HTML5, dark mode via Tailwind class strategy, sidebar + main content layout, HTMX loaded
- `templates/auth/login.html` — login form extending base
- `templates/index.html` — dashboard placeholder extending base, shows "CityLab" heading and app status
- `templates/errors/404.html`, `templates/errors/500.html`
- `static/css/src/input.css` — Tailwind input with custom layer
- `static/css/main.css` — compiled Tailwind output
- `static/vendor/htmx.min.js` — HTMX 2.x vendored
- `tailwind.config.js` — content paths, dark mode class, custom theme extension
- `package.json` with tailwindcss dev dependency and build script

### 7. Scheduler

- `src/citylab/models/scheduled_task.py` — `ScheduledTask` model: name (unique), cron_expression, agent_persona, agent_action, is_active (bool), last_run_at, next_run_at. Inherits BaseModel
- APScheduler `BackgroundScheduler` with `SQLAlchemyJobStore`, `ThreadPoolExecutor(5)`, coalesce=True, max_instances=1
- Sync loop: on startup and on `/api/v1/schedules/sync` POST, reads all active `ScheduledTask` rows, registers/updates/removes APScheduler jobs to match
- Each job calls `trigger_agent(persona, action)` which POSTs to the Headspace dispatch endpoint
- Scheduler gated on `testing=True` and Flask CLI context (same as Kenwood)
- Gunicorn constraint: workers=1 documented in `gunicorn.conf.py`

### 8. Agent Wiring

- `src/citylab/services/headspace_client.py` — HTTP client for Headspace API. `trigger_agent(persona, action)` method that dispatches an agent session with the specified action
- Config: `headspace.url` and `headspace.api_token` in config.yaml
- `skill-injection-registry.yaml` — YAML structure with empty persona list, ready for feature PRDs to add entries
- One example entry proving the pattern: a `citylab-operator` persona stub

### 9. Run + Deploy

- `run.py` — `create_app()` + `app.run()` with debug, host, port from config
- `gunicorn.conf.py` — workers=1, preload_app=True, bind from config, timeout=120
- `restart_server.sh` — kills existing process, restarts via run.py

### 10. Test Infrastructure

- `tests/conftest.py`:
  - `_force_test_database` — session-scoped autouse fixture, sets `DATABASE_URL` to `citylab_test`
  - `app` fixture — `create_app(testing=True)`
  - `client` fixture — `app.test_client()`
  - `db_session` fixture — transaction-scoped, rolls back after each test
- `tests/test_health.py` — one test: `GET /health` returns 200 with status=healthy
- `tests/test_auth.py` — login with valid creds returns 200, invalid returns 401
- `tests/test_api_token.py` — API endpoint without token returns 401, with valid token returns 200
- `pyproject.toml` pytest config: testpaths, markers (unit, integration, e2e, agent_driven), default addopts excluding e2e/agent_driven

### Project Files

- `pyproject.toml` — package metadata, entry points, pytest config
- `requirements.txt` — Flask, SQLAlchemy, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, psycopg2-binary, APScheduler, PyYAML, python-dotenv, requests, redis, Click, gunicorn
- `.gitignore` — standard Python + logs/, *.pyc, __pycache__, .env, node_modules/
- `README.md` — project name, quick start (create DB, flask db upgrade, python run.py), CLI usage

## Done When

- [ ] `python run.py` starts the app on port 5099, no errors
- [ ] `GET /health` returns 200 with database=connected, scheduler=running
- [ ] `/login` renders a login form; valid email+password creates a session; `/` shows dashboard when logged in
- [ ] `GET /api/v1/app/status` with valid Bearer token returns 200; without token returns 401
- [ ] `cli-citylab app status` calls the API and prints the result
- [ ] `cli-citylab schedules create --name test --cron "*/5 * * * *" --persona test --action ping` creates a scheduled task
- [ ] `cli-citylab schedules list` shows the created task
- [ ] APScheduler picks up the task and would fire on schedule (visible in logs)
- [ ] `pytest tests/` runs and passes (health, auth, API token tests)
- [ ] `flask db upgrade` applies migrations, `flask db migrate` generates new ones

## Demo Script

1. Start the app: `python run.py` — see "Running on http://127.0.0.1:5099"
2. Open browser to `http://127.0.0.1:5099` — redirected to login page
3. Log in with admin credentials — see the dashboard
4. In terminal: `cli-citylab app status` — see JSON response with app health
5. Create a schedule: `cli-citylab schedules create --name market-scan --cron "*/5 * * * *" --persona energy-monitor --action scan-prices`
6. List schedules: `cli-citylab schedules list` — see the market-scan entry
7. Check logs — APScheduler registered the job, next fire time visible
8. The key proof: a remote agent can call `cli-citylab` to operate this app and manage its scheduled tasks
