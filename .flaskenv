# Flask CLI app discovery for CityLab.
#
# Without this, the `flask` CLI may pick up a FLASK_APP exported by the shell
# profile (e.g. another project's app), causing `flask backfill`, `flask db`,
# etc. to run against the wrong application. Auto-loaded by Flask when
# python-dotenv is installed (a declared dependency in pyproject.toml /
# requirements.txt).
FLASK_APP=citylab:create_app
