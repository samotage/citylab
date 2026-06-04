"""BOM fetcher — Bureau of Meteorology forecasts + observations.

Primary source: BOM public API (https://api.weather.bom.gov.au). BOM has
historically been inconsistent about API stability, so — exactly like the
OpenNEM fetcher — live calls are attempted but any failure falls back to a
synthetic-but-realistic per-location snapshot so the demo always has data to
reason on. The fallback is clearly flagged in logs.

Synthetic data is region-plausible: Tas/Snowy hydro catchments are wetter, SA
and Western-Vic wind corridors are windier, Melbourne carries demand-driven
temperatures. This is what makes the rain-in-Tas → Basslink → softer-prices
correlation narrative land in the demo.

transform() builds:
  - short-range forecasts: 3-hourly out to 3 days
  - medium-range forecasts: daily out to 7 days
  - observations: one current observation per location
for every seeded WeatherLocation.
"""

import logging
import math
import random
from datetime import datetime, timedelta, timezone

from citylab.services.ingestion.base import BaseFetcher
from citylab.services.ingestion.registry import register_fetcher

logger = logging.getLogger(__name__)

# Per-region-relevance climate bias used to make synthetic data plausible.
# (base_temp_c, temp_amplitude, base_wind_kmh, wind_amplitude, rain_propensity)
_RELEVANCE_CLIMATE = {
    "hydro_catchment": {
        "base_temp": 8.0,
        "temp_amp": 6.0,
        "base_wind": 18.0,
        "wind_amp": 12.0,
        "rain_propensity": 0.75,  # wet — drives hydro
    },
    "wind_corridor": {
        "base_temp": 16.0,
        "temp_amp": 9.0,
        "base_wind": 35.0,
        "wind_amp": 25.0,
        "rain_propensity": 0.25,  # windy, drier
    },
    "demand_centre": {
        "base_temp": 14.0,
        "temp_amp": 8.0,
        "base_wind": 15.0,
        "wind_amp": 10.0,
        "rain_propensity": 0.35,
    },
    "solar_region": {
        "base_temp": 18.0,
        "temp_amp": 10.0,
        "base_wind": 12.0,
        "wind_amp": 8.0,
        "rain_propensity": 0.20,
    },
}

_WIND_DIRS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Backfill window for forecasts on first run (PRD: 3 days vs energy's 7).
BACKFILL_DAYS = 3

# Geohash base-32 alphabet (BOM uses 6-char geohashes to address locations).
_GEOHASH_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def geohash_encode(lat: float, lon: float, precision: int = 6) -> str:
    """Encode a lat/lon to a geohash string.

    BOM's v1 location endpoints are keyed by a ~6-char geohash. This is the
    standard geohash algorithm (Niemeyer); precision 6 ~= 1.2km cell, which is
    what BOM uses for its location ids.
    """
    lat_interval = [-90.0, 90.0]
    lon_interval = [-180.0, 180.0]
    geohash = []
    bits = [16, 8, 4, 2, 1]
    bit = 0
    ch = 0
    even = True
    while len(geohash) < precision:
        if even:
            mid = (lon_interval[0] + lon_interval[1]) / 2
            if lon > mid:
                ch |= bits[bit]
                lon_interval[0] = mid
            else:
                lon_interval[1] = mid
        else:
            mid = (lat_interval[0] + lat_interval[1]) / 2
            if lat > mid:
                ch |= bits[bit]
                lat_interval[0] = mid
            else:
                lat_interval[1] = mid
        even = not even
        if bit < 4:
            bit += 1
        else:
            geohash.append(_GEOHASH_BASE32[ch])
            bit = 0
            ch = 0
    return "".join(geohash)


def location_geohash(loc) -> str | None:
    """Resolve the BOM geohash for a WeatherLocation.

    Prefers an explicit bom_forecast_area_id (used as the geohash if set);
    otherwise derives it from lat/lon. Returns None if neither is available.
    """
    explicit = getattr(loc, "bom_forecast_area_id", None)
    if explicit:
        return str(explicit)
    if loc.latitude is not None and loc.longitude is not None:
        return geohash_encode(loc.latitude, loc.longitude, precision=6)
    return None


def _bom_parse_time(s):
    """Parse a BOM ISO timestamp (e.g. '2025-06-01T00:00:00Z')."""
    if not s:
        return None
    txt = str(s).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(txt)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class BOMFetcher(BaseFetcher):
    """Fetch BOM forecasts + observations for all seeded weather locations."""

    source_type = "bom"
    # BOM issues forecasts ~3-hourly; gap-fill triggers when gap > 6h (FR5).
    normal_interval_seconds = 6 * 3600

    def fetch(self):
        """Attempt live BOM fetch; fall back to synthetic snapshot on failure.

        Returns a dict: {source, as_of, locations: [{location, forecasts,
        observation}, ...]}.
        """
        backfill = self.data_source.last_fetch_at is None
        try:
            return self._fetch_live(backfill=backfill)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "BOM live fetch unavailable (%s); using synthetic snapshot", exc
            )
            return self._synthetic(backfill=backfill)

    def _locations(self):
        from citylab.extensions import db
        from citylab.models.weather import WeatherLocation

        return db.session.query(WeatherLocation).order_by(WeatherLocation.id).all()

    def _api_base(self) -> str:
        return (
            self.data_source.base_url or "https://api.weather.bom.gov.au"
        ).rstrip("/")

    def _fetch_live(self, backfill: bool):
        """Live BOM API call + real parsing. Raises on failure -> fallback.

        For each seeded WeatherLocation we resolve a geohash and pull the daily
        + 3-hourly forecasts and current observation, parsing temperature, wind,
        rainfall, humidity, cloud cover. Any HTTP/parse failure raises so
        fetch() falls back to the synthetic snapshot (D7).
        """
        import requests

        base = self._api_base()
        timeout = self.config.get("timeout_seconds", 8)
        session = requests.Session()
        locations = self._locations()
        if not locations:
            raise RuntimeError("no weather locations seeded")

        out_locations = []
        parsed_any = False
        for loc in locations:
            geohash = location_geohash(loc)
            if not geohash:
                continue
            forecasts = []
            observation = None
            # Daily forecasts
            try:
                r = session.get(
                    f"{base}/v1/locations/{geohash}/forecasts/daily",
                    timeout=timeout,
                )
                r.raise_for_status()
                forecasts.extend(self._parse_daily(loc, r.json()))
                parsed_any = True
            except Exception as exc:  # noqa: BLE001
                logger.debug("BOM daily forecast failed for %s: %s", loc.name, exc)
            # 3-hourly forecasts
            try:
                r = session.get(
                    f"{base}/v1/locations/{geohash}/forecasts/3-hourly",
                    timeout=timeout,
                )
                r.raise_for_status()
                forecasts.extend(self._parse_hourly(loc, r.json()))
                parsed_any = True
            except Exception as exc:  # noqa: BLE001
                logger.debug("BOM 3-hourly failed for %s: %s", loc.name, exc)
            # Observations
            try:
                r = session.get(
                    f"{base}/v1/locations/{geohash}/observations",
                    timeout=timeout,
                )
                r.raise_for_status()
                observation = self._parse_observation(loc, r.json())
                if observation:
                    parsed_any = True
            except Exception as exc:  # noqa: BLE001
                logger.debug("BOM observation failed for %s: %s", loc.name, exc)

            out_locations.append(
                {
                    "location_id": loc.id,
                    "forecasts": forecasts,
                    "observation": observation,
                }
            )

        if not parsed_any:
            raise RuntimeError("BOM returned no parseable data for any location")

        return {"source": "live", "as_of": datetime.now(timezone.utc),
                "locations": out_locations}

    # ------------------------------------------------------------------
    # Real BOM response parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _rain_amount(rain: dict):
        """Best-effort mid-point rainfall (mm) from a BOM rain block."""
        if not isinstance(rain, dict):
            return None
        amount = rain.get("amount") or {}
        lo = amount.get("min")
        hi = amount.get("max")
        vals = [v for v in (lo, hi) if isinstance(v, (int, float))]
        if not vals:
            return None
        return round(sum(vals) / len(vals), 1)

    def _parse_daily(self, loc, payload: dict) -> list[dict]:
        issued = datetime.now(timezone.utc)
        rows = []
        for d in (payload or {}).get("data", []) or []:
            target = _bom_parse_time(d.get("date") or d.get("time"))
            if target is None:
                continue
            rain = d.get("rain") or {}
            rows.append(
                {
                    "location_id": loc.id,
                    "issued_at": issued,
                    "forecast_for": target,
                    "forecast_period": "daily",
                    "temperature_min_c": d.get("temp_min"),
                    "temperature_max_c": d.get("temp_max"),
                    "rainfall_mm": self._rain_amount(rain),
                    "rainfall_probability_pct": rain.get("chance"),
                    "weather_description": d.get("short_text")
                    or d.get("extended_text"),
                }
            )
        return rows

    def _parse_hourly(self, loc, payload: dict) -> list[dict]:
        issued = datetime.now(timezone.utc)
        rows = []
        for h in (payload or {}).get("data", []) or []:
            target = _bom_parse_time(h.get("time"))
            if target is None:
                continue
            wind = h.get("wind") or {}
            rain = h.get("rain") or {}
            rows.append(
                {
                    "location_id": loc.id,
                    "issued_at": issued,
                    "forecast_for": target,
                    "forecast_period": "3hourly",
                    "temperature_c": h.get("temp"),
                    "wind_speed_kmh": wind.get("speed_kilometre"),
                    "wind_direction": wind.get("direction"),
                    "wind_gust_kmh": (h.get("wind_gust") or {}).get(
                        "speed_kilometre"
                    ),
                    "rainfall_mm": self._rain_amount(rain),
                    "rainfall_probability_pct": rain.get("chance"),
                    "humidity_pct": h.get("relative_humidity"),
                }
            )
        return rows

    def _parse_observation(self, loc, payload: dict):
        data = (payload or {}).get("data") or {}
        if not data:
            return None
        observed = _bom_parse_time(data.get("time")) or datetime.now(timezone.utc)
        wind = data.get("wind") or {}
        gust = data.get("gust") or {}
        return {
            "location_id": loc.id,
            "observed_at": observed,
            "temperature_c": data.get("temp"),
            "wind_speed_kmh": wind.get("speed_kilometre"),
            "wind_direction": wind.get("direction"),
            "wind_gust_kmh": gust.get("speed_kilometre"),
            "rainfall_since_9am_mm": data.get("rain_since_9am"),
            "humidity_pct": data.get("humidity"),
            "pressure_hpa": data.get("pressure"),
        }

    # ------------------------------------------------------------------
    # Historical observation backfill (FR10, D5 — observations only)
    # ------------------------------------------------------------------

    def fetch_range(self, start, end, progress=None):
        """Backfill historical observations for [start, end) (D5: obs only).

        BOM's public v1 observations endpoint returns only recent observations,
        so deep history isn't reachable live. We synthesise hourly observations
        across the requested range (region-plausible) so the demo has a
        continuous observation series, and log the coverage produced. Forecasts
        are NOT backfilled (you can't retrieve a stale forecast).
        """
        start = _bom_parse_time(start)
        end = _bom_parse_time(end)
        if start is None or end is None or start >= end:
            return {"source": "synthetic", "as_of": datetime.now(timezone.utc),
                    "locations": []}

        locations = self._locations()
        # Cap volume: hourly steps, max ~ 12 months.
        max_steps = 366 * 24
        out_locations = []
        total_obs = 0
        for loc in locations:
            obs_rows = []
            t = start.replace(minute=0, second=0, microsecond=0)
            steps = 0
            while t < end and steps < max_steps:
                obs_rows.append(self._observation_for(loc, t))
                t += timedelta(hours=1)
                steps += 1
            total_obs += len(obs_rows)
            out_locations.append(
                {"location_id": loc.id, "forecasts": [], "observations": obs_rows}
            )

        months = round((end - start).days / 30.0, 1)
        logger.info(
            "BOM backfill: synthesised %s months of hourly observations "
            "(%s rows across %s locations); requested %s..%s",
            months, total_obs, len(locations), start.date(), end.date(),
        )
        return {"source": "synthetic", "as_of": end, "locations": out_locations}

    # ------------------------------------------------------------------
    # Synthetic snapshot — realistic per-location weather
    # ------------------------------------------------------------------

    def _synthetic(self, backfill: bool) -> dict:
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        locations = self._locations()

        out_locations = []
        for loc in locations:
            forecasts = self._forecasts_for(loc, now, backfill=backfill)
            observation = self._observation_for(loc, now)
            out_locations.append(
                {
                    "location_id": loc.id,
                    "forecasts": forecasts,
                    "observation": observation,
                }
            )

        return {
            "source": "synthetic",
            "as_of": now,
            "locations": out_locations,
        }

    def _climate(self, loc):
        return _RELEVANCE_CLIMATE.get(
            loc.region_relevance, _RELEVANCE_CLIMATE["demand_centre"]
        )

    @staticmethod
    def _diurnal(t: datetime) -> float:
        """0..1 temperature curve peaking mid-afternoon."""
        h = t.hour + t.minute / 60.0
        return 0.5 + 0.5 * math.sin((h - 9) / 24 * 2 * math.pi)

    def _forecasts_for(self, loc, issued_at: datetime, backfill: bool) -> list[dict]:
        """3-hourly short-range (3 days) + daily medium-range (7 days).

        On first run (backfill) we also stamp the prior BACKFILL_DAYS of issued
        forecasts so there's history; otherwise just the current issue.
        """
        climate = self._climate(loc)
        rows = []

        issue_times = [issued_at]
        if backfill:
            issue_times = [
                issued_at - timedelta(days=d) for d in range(BACKFILL_DAYS, 0, -1)
            ] + [issued_at]

        # Use only the latest issue for the full horizon to keep volume sane;
        # backfilled issues get a short 1-day short-range slice for history.
        for issued in issue_times:
            is_latest = issued == issued_at
            rows.extend(
                self._short_range(loc, climate, issued, full=is_latest)
            )
            if is_latest:
                rows.extend(self._medium_range(loc, climate, issued))
        return rows

    def _short_range(self, loc, climate, issued, full: bool) -> list[dict]:
        rows = []
        horizon_hours = 72 if full else 24
        for h in range(0, horizon_hours, 3):
            target = issued + timedelta(hours=h)
            diurnal = self._diurnal(target)
            temp = round(
                climate["base_temp"]
                + climate["temp_amp"] * diurnal
                + random.uniform(-1.5, 1.5),
                1,
            )
            wind = round(
                max(0.0, climate["base_wind"] + climate["wind_amp"]
                    * random.uniform(0.3, 1.0)),
                1,
            )
            rain_prob = round(
                min(100.0, max(0.0, climate["rain_propensity"] * 100
                    * random.uniform(0.5, 1.3))),
                0,
            )
            rain = round(
                climate["rain_propensity"] * random.uniform(0, 8)
                if random.random() < climate["rain_propensity"]
                else 0.0,
                1,
            )
            rows.append(
                {
                    "location_id": loc.id,
                    "issued_at": issued,
                    "forecast_for": target,
                    "forecast_period": "3hourly",
                    "temperature_c": temp,
                    "wind_speed_kmh": wind,
                    "wind_direction": random.choice(_WIND_DIRS),
                    "wind_gust_kmh": round(wind * random.uniform(1.2, 1.6), 1),
                    "rainfall_mm": rain,
                    "rainfall_probability_pct": rain_prob,
                    "cloud_cover_pct": round(min(100.0, rain_prob * random.uniform(0.6, 1.1)), 0),
                    "humidity_pct": round(50 + climate["rain_propensity"] * 40
                                          + random.uniform(-10, 10), 0),
                    "weather_description": self._describe(rain_prob, wind),
                }
            )
        return rows

    def _medium_range(self, loc, climate, issued) -> list[dict]:
        rows = []
        for d in range(1, 8):  # daily out to 7 days
            day = (issued + timedelta(days=d)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            tmin = round(climate["base_temp"] - climate["temp_amp"] * 0.5
                         + random.uniform(-2, 2), 1)
            tmax = round(climate["base_temp"] + climate["temp_amp"]
                         + random.uniform(-2, 2), 1)
            wind = round(
                max(0.0, climate["base_wind"] + climate["wind_amp"]
                    * random.uniform(0.3, 1.0)),
                1,
            )
            rain_prob = round(
                min(100.0, max(0.0, climate["rain_propensity"] * 100
                    * random.uniform(0.5, 1.3))),
                0,
            )
            rain = round(
                climate["rain_propensity"] * random.uniform(0, 15)
                if random.random() < climate["rain_propensity"] + 0.1
                else 0.0,
                1,
            )
            rows.append(
                {
                    "location_id": loc.id,
                    "issued_at": issued,
                    "forecast_for": day,
                    "forecast_period": "daily",
                    "temperature_min_c": tmin,
                    "temperature_max_c": tmax,
                    "wind_speed_kmh": wind,
                    "wind_direction": random.choice(_WIND_DIRS),
                    "wind_gust_kmh": round(wind * random.uniform(1.2, 1.6), 1),
                    "rainfall_mm": rain,
                    "rainfall_probability_pct": rain_prob,
                    "cloud_cover_pct": round(min(100.0, rain_prob * random.uniform(0.6, 1.1)), 0),
                    "humidity_pct": round(50 + climate["rain_propensity"] * 40
                                          + random.uniform(-10, 10), 0),
                    "weather_description": self._describe(rain_prob, wind),
                }
            )
        return rows

    def _observation_for(self, loc, now: datetime) -> dict:
        climate = self._climate(loc)
        diurnal = self._diurnal(now)
        temp = round(
            climate["base_temp"] + climate["temp_amp"] * diurnal
            + random.uniform(-1.5, 1.5),
            1,
        )
        wind = round(
            max(0.0, climate["base_wind"] + climate["wind_amp"]
                * random.uniform(0.3, 1.0)),
            1,
        )
        rain_since_9 = round(
            climate["rain_propensity"] * random.uniform(0, 6)
            if random.random() < climate["rain_propensity"]
            else 0.0,
            1,
        )
        return {
            "location_id": loc.id,
            "observed_at": now,
            "temperature_c": temp,
            "wind_speed_kmh": wind,
            "wind_direction": random.choice(_WIND_DIRS),
            "wind_gust_kmh": round(wind * random.uniform(1.2, 1.6), 1),
            "rainfall_since_9am_mm": rain_since_9,
            "humidity_pct": round(50 + climate["rain_propensity"] * 40
                                  + random.uniform(-10, 10), 0),
            "pressure_hpa": round(1013 + random.uniform(-12, 12), 1),
        }

    @staticmethod
    def _describe(rain_prob: float, wind: float) -> str:
        parts = []
        if rain_prob >= 70:
            parts.append("Rain likely")
        elif rain_prob >= 40:
            parts.append("Showers possible")
        else:
            parts.append("Mostly dry")
        if wind >= 45:
            parts.append("strong winds")
        elif wind >= 25:
            parts.append("breezy")
        return ", ".join(parts)

    # ------------------------------------------------------------------
    # transform / store
    # ------------------------------------------------------------------

    def transform(self, raw):
        from citylab.models.weather import WeatherForecast, WeatherObservation

        records = []
        for loc_block in raw["locations"]:
            for f in loc_block.get("forecasts", []):
                records.append(WeatherForecast(**f))
            # Single current observation (forward path) ...
            obs = loc_block.get("observation")
            if obs:
                records.append(WeatherObservation(**obs))
            # ... or a list of backfilled observations (fetch_range path).
            for o in loc_block.get("observations", []) or []:
                records.append(WeatherObservation(**o))
        return records

    # Natural-key conflict targets (must match migration eb3b9c51c3f5).
    _CONFLICT_KEYS = {
        "WeatherForecast": [
            "location_id",
            "issued_at",
            "forecast_for",
            "forecast_period",
        ],
        "WeatherObservation": ["location_id", "observed_at"],
    }

    def store(self, records) -> int:
        """Upsert weather forecasts + observations (idempotent — FR2)."""
        from citylab.services.ingestion.upsert import (
            instance_to_dict,
            upsert_records,
        )

        grouped: dict = {}
        for rec in records:
            grouped.setdefault(type(rec), []).append(rec)

        total = 0
        for model, instances in grouped.items():
            conflict = self._CONFLICT_KEYS.get(model.__name__)
            rows = [instance_to_dict(i) for i in instances]
            if conflict is None:
                from citylab.extensions import db

                for inst in instances:
                    db.session.add(inst)
                db.session.flush()
                total += len(instances)
                continue
            total += upsert_records(model, rows, conflict)
        return total


register_fetcher("bom", BOMFetcher)
