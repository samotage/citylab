"""CityLab CLI — Click-based wrapper for the REST API."""

import click

from citylab.cli_wrapper.commands_app import app_group
from citylab.cli_wrapper.commands_schedules import schedules_group


@click.group()
@click.version_option(version="0.1.0", prog_name="cli-citylab")
def main():
    """CityLab CLI — manage the agent operations hub."""
    pass


main.add_command(app_group, "app")
main.add_command(schedules_group, "schedules")
