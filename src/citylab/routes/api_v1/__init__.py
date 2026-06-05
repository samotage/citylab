"""API v1 blueprint factory."""

from flask import Blueprint, jsonify


def create_api_v1_blueprint() -> Blueprint:
    """Create and configure the API v1 blueprint."""
    api_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

    # JSON error handlers for the API
    @api_bp.errorhandler(404)
    def not_found(e):
        return jsonify({"ok": False, "error": "Not found", "code": "NOT_FOUND"}), 404

    @api_bp.errorhandler(500)
    def server_error(e):
        return jsonify({"ok": False, "error": "Internal server error", "code": "SERVER_ERROR"}), 500

    # Register API sub-modules
    from citylab.routes.api_v1.app import app_api_bp
    from citylab.routes.api_v1.schedules import schedules_api_bp
    from citylab.routes.api_v1.data import data_api_bp
    from citylab.routes.api_v1.energy import energy_api_bp
    from citylab.routes.api_v1.weather import weather_api_bp
    from citylab.routes.api_v1.solar import solar_api_bp
    from citylab.routes.api_v1.agent import agent_api_bp
    from citylab.routes.api_v1.dispatch import dispatch_api_bp
    from citylab.routes.api_v1.demand_response import dr_api_bp
    from citylab.routes.api_v1.hero import hero_api_bp

    api_bp.register_blueprint(app_api_bp)
    api_bp.register_blueprint(schedules_api_bp)
    api_bp.register_blueprint(data_api_bp)
    api_bp.register_blueprint(energy_api_bp)
    api_bp.register_blueprint(weather_api_bp)
    api_bp.register_blueprint(solar_api_bp)
    api_bp.register_blueprint(agent_api_bp)
    api_bp.register_blueprint(dispatch_api_bp)
    api_bp.register_blueprint(dr_api_bp)
    api_bp.register_blueprint(hero_api_bp)

    return api_bp
