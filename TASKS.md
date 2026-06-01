# TASKS — CityLab Project Bootstrap

**Source PRD:** `docs/prds/core/bootstrap.md`
**Branch:** `feature/hack-bootstrap`

## Task List

- [x] **Task 1: Project files and dependencies** — Create `pyproject.toml` (package metadata, entry points, pytest config), `requirements.txt`, `.gitignore`, `.env.example`, `package.json`, `tailwind.config.js`. These are zero-dependency foundational files everything else imports or references.

- [x] **Task 2: Config layer** — Create `src/citylab/config.py` (three-tier cascade: DEFAULTS, config.yaml, env vars; `build_database_uri()`; `ENV_MAPPINGS`), `config.yaml` at project root (server, logging, database, redis, api token, headspace config).

- [x] **Task 3: Extensions and database models** — Create `src/citylab/extensions.py` (SQLAlchemy 2.0 `DeclarativeBase`, naming convention, Flask-Migrate), `src/citylab/models/__init__.py`, `src/citylab/models/base.py` (BaseModel with id, created_at, updated_at), `src/citylab/models/user.py` (User: email, password_hash, is_active, Flask-Login mixin), `src/citylab/models/scheduled_task.py` (ScheduledTask: name, cron_expression, agent_persona, agent_action, is_active, last_run_at, next_run_at).

- [x] **Task 4: App factory** — Create `src/citylab/__init__.py` with `create_app()`: config loading, logging setup, database init, Flask-Login init, CSRF protection, blueprint registration, CLI command registration, admin seeding, scheduler init. Also create `run.py`, `gunicorn.conf.py`, `restart_server.sh`.

- [x] **Task 5: Auth routes and templates** — Create `src/citylab/routes/__init__.py`, `src/citylab/routes/auth.py` (login/logout with Flask-Login, Flask-WTF forms), `templates/base.html` (dark mode Tailwind, sidebar layout, HTMX), `templates/auth/login.html`, `templates/errors/404.html`, `templates/errors/500.html`. Vendor `static/vendor/htmx.min.js`. Create `static/css/src/input.css` and compile `static/css/main.css`.

- [x] **Task 6: Main and health routes** — Create `src/citylab/routes/main.py` (index `/` with login_required, renders dashboard), `src/citylab/routes/health.py` (`GET /health` returning database/redis/scheduler status), `templates/index.html` (dashboard placeholder).

- [x] **Task 7: API v1 blueprint** — Create `src/citylab/routes/api_v1/__init__.py` (API blueprint factory at `/api/v1`, CSRF exempt, JSON error handlers), `src/citylab/routes/api_v1/auth.py` (`@require_api_token` decorator), `src/citylab/routes/api_v1/app.py` (`GET /api/v1/app/status`), `src/citylab/routes/api_v1/schedules.py` (CRUD for scheduled tasks + sync endpoint).

- [x] **Task 8: Scheduler service** — Create `src/citylab/services/__init__.py`, `src/citylab/services/scheduler.py` (APScheduler BackgroundScheduler with SQLAlchemyJobStore, sync loop, `trigger_agent` job function), `src/citylab/services/headspace_client.py` (HTTP client for Headspace API dispatch).

- [x] **Task 9: CLI wrapper** — Create `src/citylab/cli_wrapper/__init__.py` (Click entry point with `main` group), `src/citylab/cli_wrapper/client.py` (HTTP client with Bearer token, error mapping), `src/citylab/cli_wrapper/config.py` (config discovery), commands: `app status`, `schedules list/create/delete`.

- [x] **Task 10: Agent wiring** — Create `skill-injection-registry.yaml` with citylab-operator persona stub. Create `src/citylab/cli/commands.py` with `flask seed-admin` CLI command.

- [x] **Task 11: Database migrations** — Initialize Alembic (`flask db init`), generate initial migration from models, apply with `flask db upgrade`. Verify the migration files are correct.

- [x] **Task 12: Test infrastructure** — Create `tests/__init__.py`, `tests/conftest.py` (`_force_test_database`, `app`, `client`, `db_session` fixtures), `tests/test_health.py`, `tests/test_auth.py`, `tests/test_api_token.py`. Run `pytest tests/` and verify all pass.

- [x] **Task 13: README** — Create `README.md` with project name, quick start (create DB, flask db upgrade, python run.py), CLI usage summary.

## Demo Script

1. Start the app: `python run.py` — see "Running on http://127.0.0.1:5099"
2. Open browser to `http://127.0.0.1:5099` — redirected to login page
3. Log in with admin credentials — see the dashboard
4. In terminal: `cli-citylab app status` — see JSON response with app health
5. Create a schedule: `cli-citylab schedules create --name market-scan --cron "*/5 * * * *" --persona energy-monitor --action scan-prices`
6. List schedules: `cli-citylab schedules list` — see the market-scan entry
7. Check logs — APScheduler registered the job, next fire time visible
8. The key proof: a remote agent can call `cli-citylab` to operate this app and manage its scheduled tasks

## Ship Status

- Build: complete
- Tests: passed (8/8)
- Smoke: passed (8/8 demo steps)

### Known Issues
None
