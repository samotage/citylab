#!/usr/bin/env python3
"""Run CityLab development server."""

from citylab import create_app
from citylab.config import load_config

app = create_app()
config = load_config()

if __name__ == "__main__":
    server = config.get("server", {})
    app.run(
        host=server.get("host", "127.0.0.1"),
        port=server.get("port", 15099),
        debug=server.get("debug", True),
    )
