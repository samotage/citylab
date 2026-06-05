#!/usr/bin/env python3
"""Run CityLab development server."""

# Load .env (secrets: SECRET_KEY, SOLCAST_API_KEY, admin creds, ...) before the
# app reads os.environ. The flask CLI auto-loads .env; this covers the server
# entrypoint. .env is gitignored — never commit it.
from dotenv import load_dotenv

load_dotenv()

from citylab import create_app  # noqa: E402
from citylab.config import load_config  # noqa: E402

app = create_app()
config = load_config()

if __name__ == "__main__":
    server = config.get("server", {})
    app.run(
        host=server.get("host", "127.0.0.1"),
        port=server.get("port", 15099),
        debug=server.get("debug", True),
    )
