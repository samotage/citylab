# CityLab

Agent-operable Flask application for the What the Hack hackathon. Human users interact via web UI, remote AI agents interact via CLI and REST API.

Built fast with [Claude Code](https://claude.ai/claude-code). PRD-driven orchestration, fast-lane pipeline, no ceremony.

## Quick Start

```bash
# 1. Create database
createdb citylab

# 2. Set environment
export CITYLAB_ADMIN_EMAIL=admin@citylab.local
export CITYLAB_ADMIN_PASSWORD=changeme

# 3. Apply migrations
PYTHONPATH=src FLASK_APP=citylab flask db upgrade

# 4. Start the app
python run.py
# Running on http://127.0.0.1:5099
```

## CLI Usage

The `cli-citylab` command wraps the REST API for agent and human use:

```bash
# App health
cli-citylab app status

# Manage scheduled tasks
cli-citylab schedules list
cli-citylab schedules create --name market-scan --cron "*/5 * * * *" --persona energy-monitor --action scan-prices
cli-citylab schedules delete --id 1
```

## API

All API endpoints require Bearer token authentication (configured in `config.yaml` under `api.token`):

```
GET  /health                  — Health check (no auth)
GET  /api/v1/app/status       — App status
GET  /api/v1/schedules        — List scheduled tasks
POST /api/v1/schedules        — Create scheduled task
PUT  /api/v1/schedules/:id    — Update scheduled task
DEL  /api/v1/schedules/:id    — Delete scheduled task
POST /api/v1/schedules/sync   — Sync with APScheduler
```

## Testing

```bash
# Create test database
createdb citylab_test

# Run tests
PYTHONPATH=src pytest tests/ -v
```

## Architecture

- **App factory**: `src/citylab/__init__.py` — Flask app with config cascade, SQLAlchemy, Flask-Login, APScheduler
- **Config**: Three-tier cascade (defaults, `config.yaml`, env vars)
- **Database**: PostgreSQL via SQLAlchemy 2.0, Alembic migrations
- **Auth**: Flask-Login for UI, Bearer token for API
- **Scheduler**: APScheduler with cron jobs that trigger agent actions via Headspace API
- **CLI**: Click-based wrapper calling REST API endpoints
