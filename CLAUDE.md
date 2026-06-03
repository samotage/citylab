# CityLab

Agent-operable Flask application for the What the Hack hackathon. Victorian energy market monitoring platform with data ingestion, scheduled tasks, and a browser-based dashboard.

## Quick Start

```bash
# Server (port 15099)
./restart_server.sh              # start/restart (the ONLY permitted method)
curl http://127.0.0.1:15099/health   # verify

# Database
flask db upgrade                 # apply migrations
flask seed-admin                 # seed admin user (needs CITYLAB_ADMIN_EMAIL + CITYLAB_ADMIN_PASSWORD)
flask seed-data-sources          # seed DataSource rows + weather/solar locations from config.yaml

# CLI (agent-facing, hits the REST API)
cli-citylab app status
cli-citylab energy summary --region VIC1
cli-citylab data sources
cli-citylab data verify --region VIC1
```

## Architecture

Flask app factory (`src/citylab/__init__.py:create_app`) with:
- **PostgreSQL** via SQLAlchemy 2.0 + Flask-Migrate (Alembic)
- **APScheduler** (BackgroundScheduler, 1 worker) for cron-driven ingestion and agent tasks
- **Redis** for future use (configured, not yet critical-path)
- **Gunicorn** for production (workers=1 due to APScheduler constraint)

### Two Auth Layers

| Surface | Auth | Audience |
|---------|------|----------|
| Browser UI (`/`, `/energy`, `/login`) | Flask-Login session cookie | Humans |
| REST API (`/api/v1/*`) | Bearer token (`Authorization: Bearer <token>`) | Agents / CLI |

API token is set in `config.yaml` under `api.token` or via `CITYLAB_API_TOKEN` env var.

### Configuration Cascade

Three tiers, later wins: `DEFAULTS` (in `src/citylab/config.py`) -> `config.yaml` -> environment variables. Env var mappings are in `ENV_MAPPINGS`. The `data_sources` section resolves `${VAR}` references against env vars for credentials.

## Project Layout

```
src/citylab/
  __init__.py          # app factory
  config.py            # 3-tier config cascade
  extensions.py        # db, migrate, login_manager, csrf
  models/              # SQLAlchemy models (User, ScheduledTask, DataSource, Energy*, Weather*, Solar*)
  routes/
    main.py            # / (dashboard, login-required)
    auth.py            # /login, /logout
    energy.py          # /energy dashboard + HTMX partials
    health.py          # /health (no auth)
    api_v1/            # REST API (Bearer token auth)
      app.py           # /api/v1/app/*
      auth.py          # require_api_token decorator
      data.py          # /api/v1/data/*
      energy.py        # /api/v1/energy/*
      weather.py       # /api/v1/weather/*
      solar.py         # /api/v1/solar/*
      schedules.py     # /api/v1/schedules/*
  services/
    scheduler.py       # APScheduler init + job sync
    energy_query.py    # read-side energy queries
    weather_query.py   # read-side weather queries
    solar_query.py     # read-side solar queries
    data_verify.py     # data quality verification
    headspace_client.py# agent trigger via Headspace API
    ingestion/
      base.py          # BaseFetcher (fetch/transform/store + retry)
      registry.py      # fetcher registry (source_type -> class)
      seed.py          # seed DataSource + location rows from config
      opennem.py       # OpenNEM Victorian NEM data (live + synthetic fallback)
      bom.py           # BOM weather forecasts + observations
      solcast.py       # Solcast solar forecasts
  cli/
    commands.py        # Flask CLI: seed-admin, seed-data-sources
  cli_wrapper/         # Click CLI (cli-citylab) that hits the REST API
    commands_app.py    # cli-citylab app status
    commands_data.py   # cli-citylab data {sources,status,fetch,market-intelligence,verify}
    commands_energy.py # cli-citylab energy {summary,prices,generation,interconnectors,forecasts}
    commands_weather.py# cli-citylab weather {summary,outlook,forecasts,observations}
    commands_solar.py  # cli-citylab solar {summary,outlook,forecasts}
    commands_schedules.py # cli-citylab schedules {list,create,delete}
    client.py          # HTTP client with Bearer auth
    config.py          # config discovery for CLI

templates/             # Jinja2 (base.html + auth/ + energy/ + errors/)
static/
  css/src/input.css    # Tailwind source (the file to edit)
  css/main.css         # compiled output (never edit directly)
  vendor/              # htmx.min.js, chart.min.js
```

## Data Ingestion

Three registered fetchers, each a `BaseFetcher` subclass with `fetch() -> transform() -> store()` and retry/backoff:

| Source | Type | Cron | What |
|--------|------|------|------|
| OpenNEM | `opennem` | `*/5 * * * *` | VIC1 prices, demand, generation mix, interconnectors, bids, forecasts |
| BOM | `bom` | `0 */3 * * *` | Weather forecasts + observations for energy-relevant locations |
| Solcast | `solcast` | `0 * * * *` | Solar irradiance forecasts for VIC/SA sites |

All fetchers have synthetic fallback data so the demo works without live API access.

## Database

PostgreSQL database `citylab` (test: `citylab_test`). Four migration files cover:
1. Users + scheduled tasks
2. Energy market tables (EnergyPrice, EnergyDemand, GenerationOutput, InterconnectorFlow, GeneratorSubmission, PriceForecast)
3. Weather tables (WeatherLocation, WeatherForecast, WeatherObservation)
4. Solar tables (SolarLocation, SolarForecast)

## Energy Dashboard

Server-rendered at `/energy` with HTMX polling partials:
- Price panel (current price, trend, forecast direction)
- Generation mix (fuel-type stacked bar via Chart.js)
- Interconnector flows (5 VIC corridors: Basslink, Heywood, Murraylink, VNI, VNI West)
- Weather conditions (wind, solar irradiance, rain, temperature)
- Price forecast chart (actuals vs forecast overlay)
- Source health (staleness detection per data source)

Region is hardcoded to `VIC1`.

## Frontend

- Tailwind CSS v3 with custom `citylab` colour palette
- HTMX for partial updates
- Chart.js for charts
- Build: `npx tailwindcss -i static/css/src/input.css -o static/css/main.css`
- NEVER use `npx @tailwindcss/cli` (v4) - this project uses v3

## Testing

```bash
pytest                                    # all tests minus e2e/agent_driven
pytest tests/test_health.py               # targeted (preferred)
pytest tests/data/test_opennem_fetcher.py  # specific fetcher
```

Test database: `citylab_test` (enforced by `_force_test_database` fixture in `tests/conftest.py`).

## CRITICAL: Server & URL Rules

- `./restart_server.sh` is the ONLY way to start/restart the server
- NEVER run `python run_citylab.py` directly or kill processes manually
- Server listens on `127.0.0.1:15099` (behind nginx at `https://smac.griffin-blenny.ts.net:5059`)
- Flask debug reloader handles most Python file changes automatically

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `CITYLAB_ADMIN_EMAIL` | Admin user email for seeding |
| `CITYLAB_ADMIN_PASSWORD` | Admin user password for seeding |
| `CITYLAB_API_TOKEN` | Override API token |
| `CITYLAB_DB_NAME` | Override database name |
| `DATABASE_URL` | Full PostgreSQL URI override |
| `OPENNEM_API_KEY` | OpenNEM API key (optional, public endpoints work without) |
| `SOLCAST_API_KEY` | Solcast API key (optional, synthetic fallback if missing) |
| `SECRET_KEY` | Flask secret key |
