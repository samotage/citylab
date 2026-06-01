"""CLI commands: schedules group."""

import json

import click

from citylab.cli_wrapper.client import APIClient


@click.group("schedules")
def schedules_group():
    """Scheduled task management."""
    pass


@schedules_group.command("list")
def list_schedules():
    """List all scheduled tasks."""
    client = APIClient()
    result = client.get("/api/v1/schedules")
    print(json.dumps(result, indent=2))


@schedules_group.command("create")
@click.option("--name", required=True, help="Task name")
@click.option("--cron", required=True, help="Cron expression (5-part)")
@click.option("--persona", required=True, help="Agent persona slug")
@click.option("--action", required=True, help="Agent action to trigger")
def create_schedule(name, cron, persona, action):
    """Create a new scheduled task."""
    client = APIClient()
    result = client.post("/api/v1/schedules", {
        "name": name,
        "cron_expression": cron,
        "agent_persona": persona,
        "agent_action": action,
    })
    print(json.dumps(result, indent=2))


@schedules_group.command("delete")
@click.option("--id", "task_id", required=True, type=int, help="Task ID to delete")
def delete_schedule(task_id):
    """Delete a scheduled task."""
    client = APIClient()
    result = client.delete(f"/api/v1/schedules/{task_id}")
    print(json.dumps(result, indent=2))
