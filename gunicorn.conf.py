"""Gunicorn configuration for CityLab.

Workers=1 is required — APScheduler runs in-process and must not be
duplicated across workers.
"""

import yaml

# Load config for bind address
try:
    with open("config.yaml") as f:
        config = yaml.safe_load(f) or {}
    server = config.get("server", {})
    host = server.get("host", "127.0.0.1")
    port = server.get("port", 15099)
except Exception:
    host = "127.0.0.1"
    port = 15099

bind = f"{host}:{port}"
workers = 1  # APScheduler constraint
preload_app = True
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"
