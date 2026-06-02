"""Seed DataSource rows from the config.yaml `data_sources` section.

Credentials referenced via env vars in config are resolved by load_config()
and injected into DataSource.config JSONB here. Idempotent: existing sources
are updated in place (matched by name), not duplicated.
"""

import logging

logger = logging.getLogger(__name__)

# Maps the config.yaml key under data_sources -> source_type enum value.
_SOURCE_TYPE_BY_KEY = {
    "opennem": "opennem",
    "bom": "bom",
    "solcast": "solcast",
}


def seed_data_sources(config: dict | None = None) -> list[dict]:
    """Create/update DataSource rows from config. Returns list of to_dict()."""
    from citylab.config import load_config
    from citylab.extensions import db
    from citylab.models.data_source import DataSource

    if config is None:
        config = load_config()

    sources_cfg = config.get("data_sources", {}) or {}
    results = []

    for key, spec in sources_cfg.items():
        if not isinstance(spec, dict):
            continue
        source_type = _SOURCE_TYPE_BY_KEY.get(key, "custom")
        name = spec.get("name", f"{key} source")
        base_url = spec.get("base_url")
        cron = spec.get("cron_expression", "*/5 * * * *")

        # Everything except the recognised scheduling/url fields goes into
        # config JSONB — including resolved credentials.
        reserved = {"name", "base_url", "cron_expression"}
        ds_config = {k: v for k, v in spec.items() if k not in reserved}

        existing = db.session.query(DataSource).filter_by(name=name).first()
        if existing:
            existing.source_type = source_type
            existing.base_url = base_url
            existing.cron_expression = cron
            existing.config = ds_config
            existing.is_active = True
            db.session.commit()
            logger.info("Updated data source: %s", name)
            results.append(existing.to_dict())
        else:
            ds = DataSource(
                name=name,
                source_type=source_type,
                base_url=base_url,
                cron_expression=cron,
                config=ds_config,
                is_active=True,
                last_fetch_status="pending",
            )
            db.session.add(ds)
            db.session.commit()
            logger.info("Seeded data source: %s", name)
            results.append(ds.to_dict())

    return results
