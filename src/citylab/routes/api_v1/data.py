"""Source-agnostic data API: sources registry + cross-source intelligence."""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from citylab.extensions import db
from citylab.models.data_source import DataSource
from citylab.routes.api_v1.auth import require_api_token

data_api_bp = Blueprint("data_api", __name__)


@data_api_bp.route("/data/sources", methods=["GET"])
@require_api_token
def list_sources():
    """List registered data sources and their status."""
    sources = db.session.query(DataSource).order_by(DataSource.name).all()
    return jsonify(
        {
            "ok": True,
            "data": [s.to_dict() for s in sources],
            "data_as_of": datetime.now(timezone.utc).isoformat(),
        }
    )


@data_api_bp.route("/data/sources/<int:source_id>/status", methods=["GET"])
@require_api_token
def source_status(source_id):
    """Fetch status, last run, and error detail for one source."""
    source = db.session.get(DataSource, source_id)
    if not source:
        return (
            jsonify({"ok": False, "error": "Data source not found", "code": "NOT_FOUND"}),
            404,
        )
    return jsonify(
        {
            "ok": True,
            "data": {
                "id": source.id,
                "name": source.name,
                "source_type": source.source_type,
                "is_active": source.is_active,
                "last_fetch_at": source.last_fetch_at.isoformat()
                if source.last_fetch_at
                else None,
                "last_fetch_status": source.last_fetch_status,
                "last_error": source.last_error,
                "next_fetch_at": source.next_fetch_at.isoformat()
                if source.next_fetch_at
                else None,
            },
            "data_as_of": source.last_fetch_at.isoformat()
            if source.last_fetch_at
            else None,
        }
    )


@data_api_bp.route("/data/sources/<int:source_id>/fetch", methods=["POST"])
@require_api_token
def trigger_fetch(source_id):
    """Manually trigger an ingestion cycle for a source (demo convenience)."""
    from citylab.services.ingestion.registry import get_fetcher

    source = db.session.get(DataSource, source_id)
    if not source:
        return (
            jsonify({"ok": False, "error": "Data source not found", "code": "NOT_FOUND"}),
            404,
        )
    fetcher_cls = get_fetcher(source.source_type)
    if not fetcher_cls:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": f"No fetcher for source_type={source.source_type}",
                    "code": "NO_FETCHER",
                }
            ),
            400,
        )
    result = fetcher_cls(source).run()
    return jsonify({"ok": result["ok"], "data": result})


@data_api_bp.route("/data/market-intelligence", methods=["GET"])
@require_api_token
def market_intelligence():
    """Cross-source summary — the 'give me everything' endpoint.

    Energy-only until BOM/Solcast sources exist. Each source reports its own
    data_as_of so agents can judge freshness per source.
    """
    from citylab.services.energy_query import current_snapshot, latest_fetch_timestamp

    region = request.args.get("region", "VIC1")

    sources = db.session.query(DataSource).filter_by(is_active=True).all()
    per_source = []
    for s in sources:
        per_source.append(
            {
                "name": s.name,
                "source_type": s.source_type,
                "status": s.last_fetch_status,
                "data_as_of": s.last_fetch_at.isoformat() if s.last_fetch_at else None,
            }
        )

    energy = current_snapshot(region)

    return jsonify(
        {
            "ok": True,
            "data": {
                "region": region,
                "sources": per_source,
                "energy": energy,
                # Placeholders populated when BOM / Solcast PRDs land.
                "weather": None,
                "solar": None,
            },
            "data_as_of": latest_fetch_timestamp(),
        }
    )
