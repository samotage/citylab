"""Flask CLI commands — seed-admin, etc."""

import os

import click


def register_cli_commands(app):
    """Register CLI commands with the Flask app."""

    @app.cli.command("seed-admin")
    def seed_admin():
        """Seed admin user from environment variables."""
        from citylab.extensions import db
        from citylab.models.user import User

        email = os.environ.get("CITYLAB_ADMIN_EMAIL")
        password = os.environ.get("CITYLAB_ADMIN_PASSWORD")

        if not email or not password:
            click.echo("Error: CITYLAB_ADMIN_EMAIL and CITYLAB_ADMIN_PASSWORD must be set.")
            return

        existing = db.session.query(User).filter_by(email=email).first()
        if existing:
            click.echo(f"Admin user {email} already exists.")
            return

        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin user {email} created.")
