"""CityLab CLI — Click-based wrapper for the REST API."""

import click

from citylab.cli_wrapper.commands_app import app_group
from citylab.cli_wrapper.commands_schedules import schedules_group
from citylab.cli_wrapper.commands_data import data_group
from citylab.cli_wrapper.commands_energy import energy_group
from citylab.cli_wrapper.commands_weather import weather_group
from citylab.cli_wrapper.commands_solar import solar_group
from citylab.cli_wrapper.commands_agent import agent_group
from citylab.cli_wrapper.commands_dispatch import dispatch_group


@click.group()
@click.version_option(version="0.1.0", prog_name="cli-citylab")
def main():
    """CityLab CLI — manage the agent operations hub."""
    pass


main.add_command(app_group, "app")
main.add_command(schedules_group, "schedules")
main.add_command(data_group, "data")
main.add_command(energy_group, "energy")
main.add_command(weather_group, "weather")
main.add_command(solar_group, "solar")
main.add_command(agent_group, "agent")
main.add_command(dispatch_group, "dispatch")
