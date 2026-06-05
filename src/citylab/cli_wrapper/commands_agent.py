"""CLI commands: agent group — session lifecycle + config management.

Hits the Bearer-authed `/api/v1/agent/*` routes via the shared APIClient. All
output is JSON for agent-friendliness (NFR4). Covers session commands (start,
stop, status, check, message — FR22/FR24) and config commands (list,
add-config, set-default — FR23).
"""

import json

import click

from citylab.cli_wrapper.client import APIClient


@click.group("agent")
def agent_group():
    """Remote agent session and configuration management."""
    pass


# --- session lifecycle (FR22, FR24) ---------------------------------------


@agent_group.command("start")
@click.option("--persona", default=None, help="Persona slug (defaults to the default agent)")
@click.option("--prompt", "initial_prompt", default=None, help="Optional initial prompt")
def start(persona, initial_prompt):
    """Start (resume-or-create) an agent session."""
    client = APIClient()
    body = {}
    if persona:
        body["persona"] = persona
    if initial_prompt:
        body["initial_prompt"] = initial_prompt
    result = client.post("/api/v1/agent/init", body)
    print(json.dumps(result, indent=2))


@agent_group.command("stop")
@click.option("--persona", default=None, help="Persona slug to stop")
@click.option("--session-id", default=None, type=int, help="Specific session id to stop")
def stop(persona, session_id):
    """Stop the active agent session."""
    client = APIClient()
    body = {}
    if persona:
        body["persona"] = persona
    if session_id:
        body["session_id"] = session_id
    result = client.post("/api/v1/agent/shutdown", body)
    print(json.dumps(result, indent=2))


@agent_group.command("status")
@click.option("--persona", default=None, help="Filter to this persona")
def status(persona):
    """Show the active session status (with live liveness check)."""
    client = APIClient()
    path = "/api/v1/agent/status"
    if persona:
        path += f"?persona={persona}"
    result = client.get(path)
    print(json.dumps(result, indent=2))


@agent_group.command("check")
@click.option("--persona", default=None, help="Filter to this persona")
def check(persona):
    """Alias for status — run a liveness probe on the active session."""
    client = APIClient()
    path = "/api/v1/agent/status"
    if persona:
        path += f"?persona={persona}"
    result = client.get(path)
    print(json.dumps(result, indent=2))


@agent_group.command("message")
@click.argument("text")
@click.option("--persona", default=None, help="Target persona")
@click.option("--session-id", default=None, type=int, help="Target session id")
def message(text, persona, session_id):
    """Send a message to the active agent session."""
    client = APIClient()
    body = {"message": text}
    if persona:
        body["persona"] = persona
    if session_id:
        body["session_id"] = session_id
    result = client.post("/api/v1/agent/message", body)
    print(json.dumps(result, indent=2))


# --- config management (FR23) ---------------------------------------------


@agent_group.command("list")
@click.option("--all", "show_all", is_flag=True, help="Include inactive configs")
def list_configs(show_all):
    """List configured agent personas."""
    client = APIClient()
    path = "/api/v1/agent/configs"
    if show_all:
        path += "?all=1"
    result = client.get(path)
    print(json.dumps(result, indent=2))


@agent_group.command("add-config")
@click.option("--name", required=True, help="Display name")
@click.option("--persona", "persona_slug", required=True, help="Persona slug")
@click.option("--description", default=None, help="What the agent does")
@click.option("--default", "is_default", is_flag=True, help="Set as the default agent")
def add_config(name, persona_slug, description, is_default):
    """Add a new agent config."""
    client = APIClient()
    result = client.post(
        "/api/v1/agent/configs",
        {
            "name": name,
            "persona_slug": persona_slug,
            "description": description,
            "is_default": is_default,
        },
    )
    print(json.dumps(result, indent=2))


@agent_group.command("set-default")
@click.option("--persona", "persona_slug", required=True, help="Persona slug to make default")
def set_default(persona_slug):
    """Set the default agent config."""
    client = APIClient()
    result = client.post("/api/v1/agent/configs/default", {"persona_slug": persona_slug})
    print(json.dumps(result, indent=2))
