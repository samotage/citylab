"""
CityLab — agent-operable Flask application.
"""

import logging
import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask

from citylab.config import build_database_uri, load_config

load_dotenv()


def create_app(testing: bool = False) -> Flask:
    """Application factory."""
    app = Flask(
        __name__,
        template_folder=os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates"
        ),
        static_folder=os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static"
        ),
    )

    config = load_config()

    # --- Flask config ---
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-changeme")
    app.config["SQLALCHEMY_DATABASE_URI"] = build_database_uri(config)
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 5,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_ENABLED"] = not testing

    # Session config
    session_cfg = config.get("session", {})
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
        days=session_cfg.get("lifetime_days", 30)
    )
    app.config["SESSION_COOKIE_NAME"] = session_cfg.get(
        "cookie_name", "session_citylab"
    )
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Store our config for access elsewhere
    app.config["CITYLAB_CONFIG"] = config
    app.config["TESTING"] = testing

    # --- Logging ---
    log_cfg = config.get("logging", {})
    logging.basicConfig(
        level=getattr(logging, log_cfg.get("level", "INFO")),
        format=log_cfg.get("format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s"),
    )

    # --- Extensions ---
    from citylab.extensions import csrf, db, login_manager, migrate

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    csrf.init_app(app)

    # Flask-Login user loader
    from citylab.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Blueprints ---
    from citylab.routes.auth import auth_bp
    from citylab.routes.energy import energy_bp
    from citylab.routes.health import health_bp
    from citylab.routes.main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(energy_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(main_bp)

    # API v1
    from citylab.routes.api_v1 import create_api_v1_blueprint
    from citylab.routes.api_v1.app import app_api_bp
    from citylab.routes.api_v1.schedules import schedules_api_bp
    from citylab.routes.api_v1.data import data_api_bp
    from citylab.routes.api_v1.energy import energy_api_bp
    from citylab.routes.api_v1.weather import weather_api_bp
    from citylab.routes.api_v1.solar import solar_api_bp
    from citylab.routes.api_v1.agent import agent_api_bp

    api_bp = create_api_v1_blueprint()
    csrf.exempt(api_bp)
    csrf.exempt(app_api_bp)
    csrf.exempt(schedules_api_bp)
    csrf.exempt(data_api_bp)
    csrf.exempt(energy_api_bp)
    csrf.exempt(weather_api_bp)
    csrf.exempt(solar_api_bp)
    csrf.exempt(agent_api_bp)
    app.register_blueprint(api_bp)

    # --- CLI commands ---
    from citylab.cli.commands import register_cli_commands

    register_cli_commands(app)

    # --- Admin seeding ---
    with app.app_context():
        _seed_admin(db)

    # --- Scheduler ---
    if not testing and not _is_flask_cli():
        _init_scheduler(app, config)

    return app


def _seed_admin(db):
    """Seed admin user from env vars if not exists."""
    from citylab.models.user import User

    email = os.environ.get("CITYLAB_ADMIN_EMAIL")
    password = os.environ.get("CITYLAB_ADMIN_PASSWORD")
    if not email or not password:
        return

    try:
        existing = db.session.query(User).filter_by(email=email).first()
        if not existing:
            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            logging.getLogger("citylab").info(f"Admin user seeded: {email}")
    except Exception as e:
        db.session.rollback()
        logging.getLogger("citylab").warning(f"Could not seed admin: {e}")


def _is_flask_cli() -> bool:
    """Detect if we're running under flask CLI (db migrate, etc.)."""
    import sys
    return any(
        arg in sys.argv for arg in ["db", "seed-admin", "seed-data-sources", "routes", "shell"]
    )


def _init_scheduler(app, config):
    """Initialize APScheduler if not in testing/CLI mode."""
    try:
        from citylab.services.scheduler import init_scheduler

        init_scheduler(app, config)
    except Exception as e:
        logging.getLogger("citylab").warning(f"Scheduler init failed: {e}")
