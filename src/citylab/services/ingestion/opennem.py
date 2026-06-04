"""OpenNEM fetcher — Victorian (VIC1) NEM market data.

Primary source: OpenNEM API (https://api.opennem.org.au). Where OpenNEM lacks a
dataset (pre-dispatch forecasts, detailed generator submissions) AEMO is used as
a secondary source within this same fetcher — AEMO is an implementation detail,
not a separate DataSource.

Hackathon resilience: live API calls are attempted, but if the network/API is
unavailable the fetcher falls back to a synthetic-but-realistic Victorian market
snapshot so the demo always has data to reason on. The fallback is clearly
flagged in logs.
"""

import logging
import math
import random
from datetime import datetime, timedelta, timezone

from citylab.services.ingestion.base import BaseFetcher
from citylab.services.ingestion.registry import register_fetcher

logger = logging.getLogger(__name__)

REGION = "VIC1"


def _parse_iso(s):
    """Parse an ISO-8601 timestamp (tolerant of trailing Z / offsets)."""
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    if not s:
        return None
    txt = str(s).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(txt)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _interval_seconds(interval) -> int:
    """Map an OpenNEM interval string ('5m','30m','1h','1d') to seconds."""
    if not interval:
        return 300
    txt = str(interval).strip().lower()
    units = {"m": 60, "h": 3600, "d": 86400, "w": 604800}
    try:
        num = int("".join(ch for ch in txt if ch.isdigit()) or "5")
        suffix = "".join(ch for ch in txt if ch.isalpha()) or "m"
        return num * units.get(suffix[0], 60)
    except Exception:  # noqa: BLE001
        return 300

# Generation fuel types tracked for VIC1. Battery charging/discharging are
# explicit, distinct fuel types per the PRD.
FUEL_TYPES = [
    "brown_coal",
    "gas_ccgt",
    "gas_ocgt",
    "gas_recip",
    "gas_steam",
    "solar_utility",
    "solar_rooftop",
    "wind",
    "hydro",
    "battery_discharging",
    "battery_charging",
    "biomass",
    "distillate",
]

# The 5 interconnector corridors touching Victoria.
# flow_mw positive = from_region -> to_region.
INTERCONNECTORS = [
    {"id": "T-V-MNSP1", "name": "Basslink", "from": "TAS1", "to": "VIC1", "capacity": 478},
    {"id": "V-SA", "name": "Heywood", "from": "VIC1", "to": "SA1", "capacity": 650},
    {"id": "V-S-MNSP1", "name": "Murraylink", "from": "VIC1", "to": "SA1", "capacity": 220},
    {"id": "VIC1-NSW1", "name": "VNI", "from": "NSW1", "to": "VIC1", "capacity": 1900},
    {"id": "VNI-WEST", "name": "VNI West", "from": "NSW1", "to": "VIC1", "capacity": 1900},
]

# OpenNEM-style fuel labels mapped to our canonical fuel_type set.
OPENNEM_FUEL_MAP = {
    "coal_brown": "brown_coal",
    "gas_ccgt": "gas_ccgt",
    "gas_ocgt": "gas_ocgt",
    "gas_recip": "gas_recip",
    "gas_steam": "gas_steam",
    "solar_utility": "solar_utility",
    "solar_rooftop": "solar_rooftop",
    "wind": "wind",
    "hydro": "hydro",
    "battery_discharging": "battery_discharging",
    "battery_charging": "battery_charging",
    "bioenergy_biomass": "biomass",
    "distillate": "distillate",
}


class OpenNEMFetcher(BaseFetcher):
    """Fetch Victorian market data from OpenNEM (+ AEMO for forecasts/bids)."""

    source_type = "opennem"
    # Gap-fill threshold base: NEM dispatch is 5-min; gap-fill triggers >10min.
    normal_interval_seconds = 600

    def fetch(self):
        """Attempt live OpenNEM fetch; fall back to synthetic data on failure.

        Returns a dict with keys: prices, demand, generation, interconnectors,
        submissions, forecasts, source ("live"|"synthetic"), as_of.
        """
        backfill = self.data_source.last_fetch_at is None
        try:
            return self._fetch_live(backfill=backfill)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "OpenNEM live fetch unavailable (%s); using synthetic snapshot", exc
            )
            return self._synthetic(backfill=backfill)

    def _api_base(self) -> str:
        return (self.data_source.base_url or "https://api.opennem.org.au").rstrip("/")

    def _api_headers(self) -> dict:
        headers = {"Accept": "application/json"}
        api_key = self.config.get("api_key")
        if api_key and not str(api_key).startswith("${"):
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _fetch_live(self, backfill: bool):
        """Live OpenNEM API call + real parsing. Raises on failure -> fallback.

        Hits the region power/price stats endpoint and parses the time-series
        ``data`` array into our snapshot shape. Any HTTP or parse failure raises
        so fetch() falls back to the synthetic snapshot (D7).
        """
        import requests

        url = f"{self._api_base()}/stats/power/network/NEM/{REGION}"
        timeout = self.config.get("timeout_seconds", 8)
        resp = requests.get(url, headers=self._api_headers(), timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
        snap = self._parse_payload(payload)
        snap["source"] = "live"
        logger.info("OpenNEM live parse OK: %s prices, %s gen rows",
                    len(snap["prices"]), len(snap["generation"]))
        return snap

    # ------------------------------------------------------------------
    # Real OpenNEM response parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _history_points(history: dict) -> list[tuple]:
        """Expand an OpenNEM history block into [(timestamp, value), ...].

        history = {start, last, interval, data: [v0, v1, ...]} where each value
        is spaced ``interval`` apart starting at ``start``.
        """
        if not isinstance(history, dict):
            return []
        start = _parse_iso(history.get("start"))
        values = history.get("data") or []
        if start is None or not values:
            return []
        step = timedelta(seconds=_interval_seconds(history.get("interval")))
        out = []
        for i, v in enumerate(values):
            if v is None:
                continue
            out.append((start + step * i, v))
        return out

    def _parse_payload(self, payload: dict) -> dict:
        """Parse an OpenNEM stats payload into the snapshot shape.

        Tolerant of the legacy OPDM stats schema: top-level ``data`` is a list
        of series, each with a ``data_type`` / ``type`` (power|price|demand), an
        optional ``fuel_tech``, a ``history`` block and optionally a
        ``forecast`` block.
        """
        if not isinstance(payload, dict):
            raise ValueError("Unexpected OpenNEM payload shape (not an object)")
        series = payload.get("data")
        if not isinstance(series, list) or not series:
            raise ValueError("OpenNEM payload missing data series")

        prices: list[dict] = []
        demand: list[dict] = []
        generation: list[dict] = []
        forecasts: list[dict] = []

        latest_ts = None
        parsed_any = False

        for s in series:
            if not isinstance(s, dict):
                continue
            dtype = (s.get("data_type") or s.get("type") or "").lower()
            fuel_raw = s.get("fuel_tech") or s.get("fueltech") or s.get(
                "fueltech_group"
            )
            history = s.get("history") or {}
            points = self._history_points(history)
            if points:
                parsed_any = True
                latest_ts = max(latest_ts or points[-1][0], points[-1][0])

            if dtype == "price":
                for ts, v in points:
                    prices.append(
                        {
                            "region": REGION,
                            "interval_start": ts,
                            "interval_end": ts
                            + timedelta(
                                seconds=_interval_seconds(history.get("interval"))
                            ),
                            "interval_type": "5min",
                            "price_aud_mwh": round(float(v), 2),
                        }
                    )
            elif dtype == "demand":
                for ts, v in points:
                    demand.append(
                        {
                            "region": REGION,
                            "interval_start": ts,
                            "demand_mw": round(float(v), 1),
                            "demand_type": "actual",
                        }
                    )
            elif dtype == "power" and fuel_raw:
                fuel = OPENNEM_FUEL_MAP.get(str(fuel_raw).lower(), str(fuel_raw).lower())
                for ts, v in points:
                    generation.append(
                        {
                            "region": REGION,
                            "interval_start": ts,
                            "fuel_type": fuel,
                            "output_mw": round(float(v), 1),
                            "capacity_mw": None,
                        }
                    )

            # Price forecast (pre-dispatch) if a forecast block is present.
            forecast = s.get("forecast")
            if dtype == "price" and isinstance(forecast, dict):
                issued = latest_ts or datetime.now(timezone.utc)
                for ts, v in self._history_points(forecast):
                    forecasts.append(
                        {
                            "region": REGION,
                            "forecast_issued_at": issued,
                            "forecast_for": ts,
                            "price_aud_mwh": round(float(v), 2),
                            "forecast_type": "predispatch_30min",
                        }
                    )

        if not parsed_any:
            raise ValueError("OpenNEM payload had no parseable history")

        return {
            "source": "live",
            "as_of": latest_ts or datetime.now(timezone.utc),
            "prices": prices,
            "demand": demand,
            "generation": generation,
            # Interconnector flows + bid submissions aren't in the power/price
            # stats endpoint; leave empty (synthetic path covers them for demo).
            "interconnectors": [],
            "submissions": [],
            "forecasts": forecasts,
        }

    # ------------------------------------------------------------------
    # Synthetic snapshot — realistic Victorian market data
    # ------------------------------------------------------------------

    def _synthetic(self, backfill: bool) -> dict:
        """Generate a realistic VIC1 snapshot (and 7-day backfill on first run)."""
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        # Align to 5-minute boundary
        now = now - timedelta(minutes=now.minute % 5)

        if backfill:
            intervals = [now - timedelta(minutes=5 * i) for i in range(7 * 24 * 12)]
        else:
            since = self.data_source.last_fetch_at
            count = 12  # default last hour
            if since:
                delta = now - since.astimezone(timezone.utc)
                count = max(1, min(int(delta.total_seconds() // 300), 7 * 24 * 12))
            intervals = [now - timedelta(minutes=5 * i) for i in range(count)]

        intervals = sorted(intervals)

        prices = [self._price_at(t) for t in intervals]
        demand = [self._demand_at(t) for t in intervals]
        generation = []
        for t in intervals:
            generation.extend(self._generation_at(t))
        interconnectors = []
        for t in intervals:
            interconnectors.extend(self._interconnectors_at(t))

        submissions = self._submissions_at(now)
        forecasts = self._forecasts_at(now)

        return {
            "source": "synthetic",
            "as_of": now,
            "prices": prices,
            "demand": demand,
            "generation": generation,
            "interconnectors": interconnectors,
            "submissions": submissions,
            "forecasts": forecasts,
        }

    @staticmethod
    def _daily_factor(t: datetime) -> float:
        """0..1 demand/price curve peaking morning + evening."""
        h = t.hour + t.minute / 60.0
        morning = math.exp(-((h - 8) ** 2) / 6)
        evening = math.exp(-((h - 18.5) ** 2) / 5)
        return 0.4 + 0.6 * min(1.0, morning + evening)

    def _price_at(self, t: datetime) -> dict:
        factor = self._daily_factor(t)
        base = 45 + 90 * factor
        price = round(base + random.uniform(-15, 25), 2)
        return {
            "region": REGION,
            "interval_start": t,
            "interval_end": t + timedelta(minutes=5),
            "interval_type": "5min",
            "price_aud_mwh": price,
        }

    def _demand_at(self, t: datetime) -> dict:
        factor = self._daily_factor(t)
        demand = round(4200 + 2600 * factor + random.uniform(-150, 150), 1)
        return {
            "region": REGION,
            "interval_start": t,
            "demand_mw": demand,
            "demand_type": "actual",
        }

    def _generation_at(self, t: datetime) -> list[dict]:
        factor = self._daily_factor(t)
        h = t.hour + t.minute / 60.0
        solar = max(0.0, math.sin((h - 6) / 12 * math.pi)) if 6 <= h <= 18 else 0.0
        wind_factor = 0.3 + 0.5 * random.random()
        # Battery: charging midday (cheap solar), discharging evening peak
        charging = solar * (h < 15)
        discharging = factor * (h >= 17 or h < 7)

        mix = {
            "brown_coal": 3000 + 400 * factor,
            "gas_ccgt": 200 + 500 * factor,
            "gas_ocgt": 50 + 300 * factor,
            "gas_recip": 10 + 30 * factor,
            "gas_steam": 20,
            "solar_utility": 900 * solar,
            "solar_rooftop": 1400 * solar,
            "wind": 1800 * wind_factor,
            "hydro": 150 + 400 * factor,
            "battery_discharging": 250 * discharging,
            "battery_charging": -180 * charging,
            "biomass": 30,
            "distillate": 5 * (factor > 0.85),
        }
        rows = []
        for fuel, mw in mix.items():
            rows.append(
                {
                    "region": REGION,
                    "interval_start": t,
                    "fuel_type": fuel,
                    "output_mw": round(mw + random.uniform(-20, 20), 1),
                    "capacity_mw": None,
                }
            )
        return rows

    def _interconnectors_at(self, t: datetime) -> list[dict]:
        factor = self._daily_factor(t)
        rows = []
        for ic in INTERCONNECTORS:
            # Net importer into VIC at peak; mild export off-peak.
            direction = 1 if ic["to"] == "VIC1" else -1
            flow = direction * ic["capacity"] * (0.2 + 0.6 * factor) * random.uniform(0.6, 1.0)
            rows.append(
                {
                    "interconnector_id": ic["id"],
                    "from_region": ic["from"],
                    "to_region": ic["to"],
                    "interval_start": t,
                    "flow_mw": round(flow, 1),
                    "capacity_mw": float(ic["capacity"]),
                    "limit_mw": float(ic["capacity"]),
                }
            )
        return rows

    def _submissions_at(self, t: datetime) -> list[dict]:
        stations = [
            ("Loy Yang A", "LYA1", "brown_coal"),
            ("Yallourn W", "YWPS1", "brown_coal"),
            ("Newport", "NPS1", "gas_steam"),
            ("Mortlake", "MORTLK11", "gas_ocgt"),
            ("Bald Hills Wind", "BALDHWF1", "wind"),
        ]
        rows = []
        for station, unit, fuel in stations:
            for band in range(1, 4):
                rows.append(
                    {
                        "station_name": station,
                        "unit_id": unit,
                        "fuel_type": fuel,
                        "region": REGION,
                        "interval_start": t,
                        "bid_band": band,
                        "price_aud_mwh": round(-50 + band * 60 + random.uniform(-10, 10), 2),
                        "volume_mw": round(50 + random.uniform(0, 250), 1),
                    }
                )
        return rows

    def _forecasts_at(self, t: datetime) -> list[dict]:
        rows = []
        for i in range(1, 9):  # next 8 half-hour intervals (pre-dispatch sample)
            target = t + timedelta(minutes=30 * i)
            factor = self._daily_factor(target)
            rows.append(
                {
                    "region": REGION,
                    "forecast_issued_at": t,
                    "forecast_for": target,
                    "price_aud_mwh": round(48 + 95 * factor + random.uniform(-10, 20), 2),
                    "forecast_type": "predispatch_30min",
                }
            )
        return rows

    # ------------------------------------------------------------------
    # transform / store
    # ------------------------------------------------------------------

    def transform(self, raw):
        """Build ORM instances from the normalised snapshot dict."""
        from citylab.models.energy import (
            EnergyDemand,
            EnergyPrice,
            GenerationOutput,
            GeneratorSubmission,
            InterconnectorFlow,
            PriceForecast,
        )

        records = []
        for p in raw["prices"]:
            records.append(EnergyPrice(**p))
        for d in raw["demand"]:
            records.append(EnergyDemand(**d))
        for g in raw["generation"]:
            records.append(GenerationOutput(**g))
        for ic in raw["interconnectors"]:
            records.append(InterconnectorFlow(**ic))
        for s in raw["submissions"]:
            records.append(GeneratorSubmission(**s))
        for f in raw["forecasts"]:
            records.append(PriceForecast(**f))
        return records

    # Natural-key conflict targets per model (must match the UNIQUE constraints
    # in migration eb3b9c51c3f5).
    _CONFLICT_KEYS = {
        "EnergyPrice": ["region", "interval_start", "interval_type"],
        "EnergyDemand": ["region", "interval_start", "demand_type"],
        "GenerationOutput": ["region", "interval_start", "fuel_type"],
        "InterconnectorFlow": ["interconnector_id", "interval_start"],
        "GeneratorSubmission": ["unit_id", "interval_start", "bid_band"],
        "PriceForecast": [
            "region",
            "forecast_issued_at",
            "forecast_for",
            "forecast_type",
        ],
    }

    def store(self, records) -> int:
        """Upsert records grouped by model class (idempotent — FR2)."""
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
                # Fallback (shouldn't happen): naive add.
                from citylab.extensions import db

                for inst in instances:
                    db.session.add(inst)
                db.session.flush()
                total += len(instances)
                continue
            total += upsert_records(model, rows, conflict)
        return total


register_fetcher("opennem", OpenNEMFetcher)
