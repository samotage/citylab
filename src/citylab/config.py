"""
CityLab configuration — three-tier cascade: DEFAULTS → config.yaml → env vars.
"""

import os
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULTS = {
    "server": {
        "host": "127.0.0.1",
        "port": 15099,
        "debug": True,
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    },
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "citylab",
        "user": "postgres",
        "password": "",
    },
    "redis": {
        "url": "redis://localhost:6379/0",
    },
    "api": {
        "token": "dev-token-changeme",
    },
    "headspace": {
        "url": "http://127.0.0.1:5001",
        "api_token": "",
    },
    "session": {
        "lifetime_days": 30,
        "cookie_name": "session_citylab",
    },
}

# ---------------------------------------------------------------------------
# Env-var overrides: ENV_NAME -> config path
# ---------------------------------------------------------------------------

ENV_MAPPINGS = {
    "CITYLAB_HOST": ("server", "host"),
    "CITYLAB_PORT": ("server", "port"),
    "CITYLAB_DEBUG": ("server", "debug"),
    "CITYLAB_LOG_LEVEL": ("logging", "level"),
    "CITYLAB_DB_HOST": ("database", "host"),
    "CITYLAB_DB_PORT": ("database", "port"),
    "CITYLAB_DB_NAME": ("database", "name"),
    "CITYLAB_DB_USER": ("database", "user"),
    "CITYLAB_DB_PASSWORD": ("database", "password"),
    "CITYLAB_REDIS_URL": ("redis", "url"),
    "CITYLAB_API_TOKEN": ("api", "token"),
    "HEADSPACE_URL": ("headspace", "url"),
    "HEADSPACE_API_TOKEN": ("headspace", "api_token"),
}


def _find_config_yaml() -> Path | None:
    """Walk up from this file to find config.yaml."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        candidate = current / "config.yaml"
        if candidate.exists():
            return candidate
        current = current.parent
    return None


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _apply_env_overrides(config: dict) -> dict:
    """Apply environment variable overrides."""
    for env_name, path in ENV_MAPPINGS.items():
        value = os.environ.get(env_name)
        if value is not None:
            # Navigate to the parent dict
            d = config
            for key in path[:-1]:
                d = d.setdefault(key, {})
            # Cast port to int, debug to bool
            final_key = path[-1]
            if final_key == "port":
                value = int(value)
            elif final_key == "debug":
                value = value.lower() in ("1", "true", "yes")
            d[final_key] = value
    return config


def build_database_uri(config: dict) -> str:
    """Build a PostgreSQL URI from config, respecting DATABASE_URL override."""
    override = os.environ.get("DATABASE_URL")
    if override:
        return override
    db = config.get("database", {})
    host = db.get("host", "localhost")
    port = db.get("port", 5432)
    name = db.get("name", "citylab")
    user = db.get("user", "postgres")
    password = db.get("password", "")
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    return f"postgresql://{user}@{host}:{port}/{name}"


def _resolve_env_refs(value):
    """Recursively resolve ${VAR} references against os.environ.

    Unset vars resolve to None so callers can detect missing credentials.
    """
    import re

    if isinstance(value, dict):
        return {k: _resolve_env_refs(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_refs(v) for v in value]
    if isinstance(value, str):
        m = re.fullmatch(r"\$\{([A-Z0-9_]+)\}", value.strip())
        if m:
            return os.environ.get(m.group(1))
    return value


def load_config() -> dict:
    """Load configuration with three-tier cascade: DEFAULTS → config.yaml → env."""
    config = DEFAULTS.copy()
    config = {k: (v.copy() if isinstance(v, dict) else v) for k, v in config.items()}

    # Deep copy nested dicts
    for key in config:
        if isinstance(config[key], dict):
            config[key] = config[key].copy()

    # Layer 2: config.yaml
    yaml_path = _find_config_yaml()
    if yaml_path:
        with open(yaml_path) as f:
            yaml_config = yaml.safe_load(f) or {}
        config = _deep_merge(config, yaml_config)

    # Layer 3: env vars
    config = _apply_env_overrides(config)

    # Resolve ${VAR} references in the data_sources section (credentials)
    if "data_sources" in config:
        config["data_sources"] = _resolve_env_refs(config["data_sources"])

    return config
