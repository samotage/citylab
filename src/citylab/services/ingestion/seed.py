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
    "opennem_nsw1": "opennem",
    "opennem_qld1": "opennem",
    "opennem_sa1": "opennem",
    "opennem_tas1": "opennem",
    "bom": "bom",
    "solcast": "solcast",
}

# The 10 forecast locations whose weather drives Victorian energy price.
# region_relevance: hydro_catchment | wind_corridor | demand_centre | solar_region
_WEATHER_LOCATIONS = [
    # Victoria — direct demand + local generation
    {
        "name": "Melbourne",
        "bom_station_id": "086338",
        "bom_forecast_area_id": "VIC_PT042",
        "latitude": -37.8136,
        "longitude": 144.9631,
        "state": "VIC",
        "region_relevance": "demand_centre",
    },
    {
        "name": "Western Victoria (Ballarat-Ararat)",
        "bom_station_id": "089002",
        "bom_forecast_area_id": "VIC_PT015",
        "latitude": -37.2858,
        "longitude": 143.0500,
        "state": "VIC",
        "region_relevance": "wind_corridor",
    },
    {
        "name": "Gippsland",
        "bom_station_id": "085072",
        "bom_forecast_area_id": "VIC_PT062",
        "latitude": -38.1800,
        "longitude": 146.5400,
        "state": "VIC",
        "region_relevance": "demand_centre",
    },
    # Tasmania — hydro catchments feeding Basslink
    {
        "name": "Western Tasmania (Strahan-Queenstown)",
        "bom_station_id": "097072",
        "bom_forecast_area_id": "TAS_PT109",
        "latitude": -42.0833,
        "longitude": 145.3333,
        "state": "TAS",
        "region_relevance": "hydro_catchment",
    },
    {
        "name": "Central Highlands (Tas)",
        "bom_station_id": "096033",
        "bom_forecast_area_id": "TAS_PT021",
        "latitude": -42.0000,
        "longitude": 146.5000,
        "state": "TAS",
        "region_relevance": "hydro_catchment",
    },
    # South Australia — wind corridors feeding Heywood/Murraylink
    {
        "name": "Mid-North SA (Port Augusta-Clare)",
        "bom_station_id": "021133",
        "bom_forecast_area_id": "SA_PT042",
        "latitude": -32.4900,
        "longitude": 137.7600,
        "state": "SA",
        "region_relevance": "wind_corridor",
    },
    {
        "name": "Yorke Peninsula / Adelaide Hills",
        "bom_station_id": "022823",
        "bom_forecast_area_id": "SA_PT091",
        "latitude": -34.5800,
        "longitude": 137.6200,
        "state": "SA",
        "region_relevance": "wind_corridor",
    },
    # Snowy / NSW — hydro catchment + interconnector context
    {
        "name": "Snowy Mountains",
        "bom_station_id": "071032",
        "bom_forecast_area_id": "NSW_PT131",
        "latitude": -36.4300,
        "longitude": 148.2700,
        "state": "NSW",
        "region_relevance": "hydro_catchment",
    },
    {
        "name": "Southern NSW",
        "bom_station_id": "070351",
        "bom_forecast_area_id": "NSW_PT248",
        "latitude": -35.3100,
        "longitude": 149.2000,
        "state": "NSW",
        "region_relevance": "demand_centre",
    },
    {
        "name": "Adelaide Hills",
        "bom_station_id": "023842",
        "bom_forecast_area_id": "SA_PT003",
        "latitude": -34.9700,
        "longitude": 138.7000,
        "state": "SA",
        "region_relevance": "wind_corridor",
    },
    # Queensland — coal + solar + demand centres
    {
        "name": "Brisbane",
        "bom_station_id": "040913",
        "bom_forecast_area_id": "QLD_PT254",
        "latitude": -27.4698,
        "longitude": 153.0251,
        "state": "QLD",
        "region_relevance": "demand_centre",
    },
    {
        "name": "Central Queensland (Gladstone)",
        "bom_station_id": "039083",
        "bom_forecast_area_id": "QLD_PT058",
        "latitude": -23.8490,
        "longitude": 151.2600,
        "state": "QLD",
        "region_relevance": "demand_centre",
    },
    {
        "name": "North Queensland (Townsville)",
        "bom_station_id": "032040",
        "bom_forecast_area_id": "QLD_PT219",
        "latitude": -19.2500,
        "longitude": 146.7700,
        "state": "QLD",
        "region_relevance": "solar_region",
    },
    # NSW — Sydney demand centre
    {
        "name": "Sydney",
        "bom_station_id": "066062",
        "bom_forecast_area_id": "NSW_PT131",
        "latitude": -33.8688,
        "longitude": 151.2093,
        "state": "NSW",
        "region_relevance": "demand_centre",
    },
]


def seed_weather_locations() -> list[dict]:
    """Create the tracked weather locations. Idempotent (matched by name)."""
    from citylab.extensions import db
    from citylab.models.weather import WeatherLocation

    results = []
    for spec in _WEATHER_LOCATIONS:
        existing = (
            db.session.query(WeatherLocation).filter_by(name=spec["name"]).first()
        )
        if existing:
            for k, v in spec.items():
                setattr(existing, k, v)
            db.session.commit()
            results.append(existing.to_dict())
        else:
            loc = WeatherLocation(**spec)
            db.session.add(loc)
            db.session.commit()
            logger.info("Seeded weather location: %s", spec["name"])
            results.append(loc.to_dict())

    return results


# Single tracked solar point: Melbourne CBD. Real data only — historical
# irradiance backfilled from the ICU SolarCam, live + forecast from Solcast.
# (The 5 synthetic regional points were removed; this is a demo, one real point.)
# NOTE: keep the name exactly as-is — re-seeding matches by name, and changing
# it would orphan the existing location row + its real ICU history.
_SOLAR_LOCATIONS = [
    {
        "name": "Melbourne Metro (rooftop PV)",
        "latitude": -37.8136,
        "longitude": 144.9631,
        "state": "VIC",
        "region_relevance": "rooftop_aggregate",
        "reference_pv_capacity_kw": 1800000.0,
    },
    {
        "name": "Sydney Metro (rooftop PV)",
        "latitude": -33.8688,
        "longitude": 151.2093,
        "state": "NSW",
        "region_relevance": "rooftop_aggregate",
        "reference_pv_capacity_kw": 2500000.0,
    },
    {
        "name": "Brisbane Metro (rooftop PV)",
        "latitude": -27.4698,
        "longitude": 153.0251,
        "state": "QLD",
        "region_relevance": "rooftop_aggregate",
        "reference_pv_capacity_kw": 3000000.0,
    },
    {
        "name": "Adelaide Metro (rooftop PV)",
        "latitude": -34.9285,
        "longitude": 138.6007,
        "state": "SA",
        "region_relevance": "rooftop_aggregate",
        "reference_pv_capacity_kw": 1200000.0,
    },
    {
        "name": "Northern Tasmania (rooftop PV)",
        "latitude": -41.4332,
        "longitude": 147.1441,
        "state": "TAS",
        "region_relevance": "rooftop_aggregate",
        "reference_pv_capacity_kw": 200000.0,
    },
]


def seed_solar_locations() -> list[dict]:
    """Create the tracked solar locations. Idempotent (matched by name)."""
    from citylab.extensions import db
    from citylab.models.solar import SolarLocation

    results = []
    for spec in _SOLAR_LOCATIONS:
        existing = (
            db.session.query(SolarLocation).filter_by(name=spec["name"]).first()
        )
        if existing:
            for k, v in spec.items():
                setattr(existing, k, v)
            db.session.commit()
            results.append(existing.to_dict())
        else:
            loc = SolarLocation(**spec)
            db.session.add(loc)
            db.session.commit()
            logger.info("Seeded solar location: %s", spec["name"])
            results.append(loc.to_dict())

    return results


def seed_battery_assets(config: dict | None = None) -> list[dict]:
    """Create/update BatteryAsset rows from config. Idempotent (matched by name)."""
    from citylab.config import load_config
    from citylab.extensions import db
    from citylab.models.battery import BatteryAsset

    if config is None:
        config = load_config()

    specs = config.get("battery_assets", []) or []
    results = []

    for spec in specs:
        if not isinstance(spec, dict):
            continue
        name = spec.get("name")
        if not name:
            continue

        existing = db.session.query(BatteryAsset).filter_by(name=name).first()
        if existing:
            existing.region = spec.get("region", existing.region)
            existing.capacity_mwh = spec.get("capacity_mwh", existing.capacity_mwh)
            existing.max_power_mw = spec.get("max_power_mw", existing.max_power_mw)
            existing.roundtrip_eff = spec.get("roundtrip_eff", existing.roundtrip_eff)
            existing.min_soc_pct = spec.get("min_soc_pct", existing.min_soc_pct)
            existing.max_soc_pct = spec.get("max_soc_pct", existing.max_soc_pct)
            existing.reserve_soc_pct = spec.get("reserve_soc_pct", existing.reserve_soc_pct)
            db.session.commit()
            logger.info("Updated battery asset: %s", name)
            results.append(existing.to_dict())
        else:
            asset = BatteryAsset(
                name=name,
                region=spec.get("region", "VIC1"),
                capacity_mwh=spec["capacity_mwh"],
                max_power_mw=spec["max_power_mw"],
                roundtrip_eff=spec.get("roundtrip_eff", 0.85),
                min_soc_pct=spec.get("min_soc_pct", 10.0),
                max_soc_pct=spec.get("max_soc_pct", 95.0),
                reserve_soc_pct=spec.get("reserve_soc_pct", 30.0),
                current_soc_pct=spec.get("initial_soc_pct", 50.0),
                status="idle",
            )
            db.session.add(asset)
            db.session.commit()
            logger.info("Seeded battery asset: %s", name)
            results.append(asset.to_dict())

    return results


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
        # `scheduled: false` (e.g. Solcast) seeds the source inactive so the
        # scheduler never runs it on cron — it runs on demand only.
        scheduled = bool(spec.get("scheduled", True))

        # Everything except the recognised scheduling/url fields goes into
        # config JSONB — including resolved credentials.
        reserved = {"name", "base_url", "cron_expression", "scheduled"}
        ds_config = {k: v for k, v in spec.items() if k not in reserved}

        # Runtime-only keys that the fetcher persists into config (e.g. metered
        # request counters) must survive re-seeding on every app startup.
        _runtime_keys = ("forecast_requests_used", "live_requests_used")

        existing = db.session.query(DataSource).filter_by(name=name).first()
        if existing:
            preserved = {
                k: (existing.config or {}).get(k)
                for k in _runtime_keys
                if existing.config and k in existing.config
            }
            existing.source_type = source_type
            existing.base_url = base_url
            existing.cron_expression = cron
            existing.config = {**ds_config, **preserved}
            existing.is_active = scheduled
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
                is_active=scheduled,
                last_fetch_status="pending",
            )
            db.session.add(ds)
            db.session.commit()
            logger.info("Seeded data source: %s", name)
            results.append(ds.to_dict())

    return results
