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

# OpenNEM moved to the OpenElectricity v4 API. The legacy host 301-redirects and
# the old /stats path 404s, so we default to v4 and auto-heal stored base_urls
# that still point at the dead legacy host.
DEFAULT_API_BASE = "https://api.openelectricity.org.au/v4"
_LEGACY_HOSTS = ("api.opennem.org.au",)


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

# OpenElectricity v4 `fueltech_group` labels -> our canonical fuel_type set.
# VIC coal is brown; v4 only exposes aggregate `gas`/`solar` groups (lower
# granularity than the synthetic mix, but real). The aggregate `battery` group
# is deliberately omitted — it nets charging/discharging and would double-count
# the explicit battery_charging / battery_discharging groups.
V4_FUELTECH_MAP = {
    "coal": "brown_coal",
    "gas": "gas_ccgt",
    "solar": "solar_utility",
    "wind": "wind",
    "hydro": "hydro",
    "battery_charging": "battery_charging",
    "battery_discharging": "battery_discharging",
    "bioenergy": "biomass",
    "biomass": "biomass",
    "distillate": "distillate",
}


class OpenNEMFetcher(BaseFetcher):
    """Fetch Victorian market data from OpenNEM (+ AEMO for forecasts/bids)."""

    source_type = "opennem"
    # Gap-fill threshold base: NEM dispatch is 5-min; gap-fill triggers >10min.
    normal_interval_seconds = 600

    def fetch(self):
        """Fetch the live OpenElectricity v4 snapshot.

        Synthetic data is a failure mode: a market monitor that fabricates
        prices when the API is down is worse than one that shows a gap. By
        default any live-fetch failure is raised so ``run()`` records
        ``last_fetch_status = "error"`` and writes nothing — the dashboard
        reflects reality. Synthetic fallback is only used when explicitly
        enabled via ``config.allow_synthetic_fallback`` (off by default).

        Returns a dict with keys: prices, demand, generation, interconnectors,
        submissions, forecasts, source ("live"|"synthetic"), as_of.
        """
        backfill = self.data_source.last_fetch_at is None
        if not self.config.get("allow_synthetic_fallback", False):
            # Honest path: fail loud, never fabricate.
            return self._fetch_live(backfill=backfill)
        try:
            return self._fetch_live(backfill=backfill)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "OpenElectricity live fetch unavailable (%s); synthetic "
                "fallback ENABLED via config — data will be FABRICATED", exc
            )
            return self._synthetic(backfill=backfill)

    def _api_base(self) -> str:
        """Resolve the API base, auto-healing dead legacy OpenNEM URLs to v4."""
        base = (self.data_source.base_url or "").rstrip("/")
        if not base or any(host in base for host in _LEGACY_HOSTS):
            return DEFAULT_API_BASE
        return base

    def _api_headers(self) -> dict:
        headers = {"Accept": "application/json"}
        api_key = self.config.get("api_key")
        if api_key and not str(api_key).startswith("${"):
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _fetch_live(self, backfill: bool):
        """Live OpenElectricity v4 fetch + parse. Raises on any failure.

        Two endpoints make the snapshot:
          - market/network/NEM  -> price + demand (metrics repeated as params)
          - data/network/NEM    -> power, grouped by fueltech_group

        Any HTTP or parse failure propagates so ``run()`` records an honest
        ``error`` status rather than silently storing fabricated data.
        """
        market = self._get_v4(
            "market/network/NEM",
            {
                "metrics": ["price", "demand"],
                "interval": "5m",
                "network_region": REGION,
                "primary_grouping": "network_region",
            },
        )
        power = self._get_v4(
            "data/network/NEM",
            {
                "metrics": "power",
                "interval": "5m",
                "network_region": REGION,
                "secondary_grouping": "fueltech_group",
            },
        )
        snap = self._parse_v4(market, power)
        snap["source"] = "live"
        logger.info(
            "OpenElectricity v4 parse OK: %s prices, %s demand, %s gen rows",
            len(snap["prices"]), len(snap["demand"]), len(snap["generation"]),
        )
        return snap

    def _get_v4(self, path: str, params: dict) -> dict:
        """GET an OpenElectricity v4 endpoint and return the parsed JSON.

        Raises on HTTP error or on an ``success: false`` envelope.
        """
        import requests

        url = f"{self._api_base()}/{path}"
        timeout = self.config.get("timeout_seconds", 8)
        resp = requests.get(
            url, headers=self._api_headers(), params=params, timeout=timeout
        )
        resp.raise_for_status()
        payload = resp.json()
        if not isinstance(payload, dict):
            raise ValueError("Unexpected v4 payload shape (not an object)")
        if payload.get("success") is False:
            raise ValueError(f"v4 API error for {path}: {payload.get('error')}")
        return payload

    # ------------------------------------------------------------------
    # OpenElectricity v4 response parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _v4_points(result: dict) -> list[tuple]:
        """Expand a v4 result block's ``data`` into [(timestamp, value), ...].

        v4 carries inline timestamps: data = [[iso_ts, value], ...].
        """
        out = []
        for row in result.get("data") or []:
            if not isinstance(row, (list, tuple)) or len(row) < 2:
                continue
            ts, v = _parse_iso(row[0]), row[1]
            if ts is None or v is None:
                continue
            out.append((ts, v))
        return out

    def _parse_v4(self, market: dict, power: dict) -> dict:
        """Parse v4 market (price/demand) + data (power) payloads.

        Each top-level ``data`` entry is one metric series with a ``results``
        list; each result holds inline [timestamp, value] rows.
        """
        prices: list[dict] = []
        demand: list[dict] = []
        generation: list[dict] = []
        latest_ts = None

        for series in market.get("data") or []:
            if not isinstance(series, dict):
                continue
            metric = (series.get("metric") or "").lower()
            for result in series.get("results") or []:
                for ts, v in self._v4_points(result):
                    latest_ts = max(latest_ts or ts, ts)
                    if metric == "price":
                        prices.append(
                            {
                                "region": REGION,
                                "interval_start": ts,
                                "interval_end": ts + timedelta(minutes=5),
                                "interval_type": "5min",
                                "price_aud_mwh": round(float(v), 2),
                            }
                        )
                    elif metric == "demand":
                        demand.append(
                            {
                                "region": REGION,
                                "interval_start": ts,
                                "demand_mw": round(float(v), 1),
                                "demand_type": "actual",
                            }
                        )

        for series in power.get("data") or []:
            if not isinstance(series, dict):
                continue
            if (series.get("metric") or "").lower() != "power":
                continue
            for result in series.get("results") or []:
                group = (result.get("columns") or {}).get("fueltech_group")
                fuel = V4_FUELTECH_MAP.get(str(group).lower())
                if fuel is None:
                    # Unknown / aggregate group (e.g. net `battery`) — skip to
                    # avoid double-counting or storing junk fuel labels.
                    continue
                for ts, v in self._v4_points(result):
                    latest_ts = max(latest_ts or ts, ts)
                    generation.append(
                        {
                            "region": REGION,
                            "interval_start": ts,
                            "fuel_type": fuel,
                            "output_mw": round(float(v), 1),
                            "capacity_mw": None,
                        }
                    )

        if not prices and not demand and not generation:
            raise ValueError("OpenElectricity v4 payload had no parseable data")

        return {
            "source": "live",
            "as_of": latest_ts or datetime.now(timezone.utc),
            "prices": prices,
            "demand": demand,
            "generation": generation,
            # Interconnector flows, bid submissions and pre-dispatch forecasts
            # are not exposed by these v4 endpoints; left empty rather than
            # fabricated.
            "interconnectors": [],
            "submissions": [],
            "forecasts": [],
        }

    # ------------------------------------------------------------------
    # Historical date-range fetching (FR8)
    # ------------------------------------------------------------------

    def fetch_range(self, start, end, progress=None):
        """Fetch VIC1 data for [start, end).

        Tries the OpenNEM date-range query; on any HTTP/parse failure falls back
        to a synthetic snapshot covering the range so backfill/gap-fill still
        produce continuous data for the demo (D7). Returns one snapshot payload
        covering the whole range.
        """
        start = _parse_iso(start)
        end = _parse_iso(end)
        if start is None or end is None or start >= end:
            if self.config.get("allow_synthetic_fallback", False):
                return self._synthetic_range(start, end)
            raise ValueError(f"Invalid range for fetch_range: {start}..{end}")

        if not self.config.get("allow_synthetic_fallback", False):
            # Honest path: real history or nothing — never fabricate backfill.
            return self._fetch_range_live(start, end)
        try:
            return self._fetch_range_live(start, end)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "OpenElectricity range fetch unavailable (%s); synthetic "
                "fallback ENABLED via config — data will be FABRICATED "
                "%s..%s", exc, start.date(), end.date(),
            )
            return self._synthetic_range(start, end)

    def _fetch_range_live(self, start, end):
        """Live v4 date-range query (market + data), parsed via _parse_v4."""
        params_common = {
            "interval": "5m",
            "network_region": REGION,
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
        }
        market = self._get_v4(
            "market/network/NEM",
            {**params_common, "metrics": ["price", "demand"],
             "primary_grouping": "network_region"},
        )
        power = self._get_v4(
            "data/network/NEM",
            {**params_common, "metrics": "power",
             "secondary_grouping": "fueltech_group"},
        )
        snap = self._parse_v4(market, power)
        # Clip to the requested window.
        snap = self._clip_range(snap, start, end)
        snap["source"] = "live"
        return snap

    @staticmethod
    def _clip_range(snap: dict, start, end) -> dict:
        def keep(ts):
            return start <= ts < end

        snap["prices"] = [p for p in snap["prices"] if keep(p["interval_start"])]
        snap["demand"] = [d for d in snap["demand"] if keep(d["interval_start"])]
        snap["generation"] = [
            g for g in snap["generation"] if keep(g["interval_start"])
        ]
        return snap

    def _synthetic_range(self, start, end) -> dict:
        """Synthetic VIC1 snapshot covering [start, end) at 5-min resolution."""
        if start is None or end is None or start >= end:
            return {
                "source": "synthetic",
                "as_of": datetime.now(timezone.utc),
                "prices": [], "demand": [], "generation": [],
                "interconnectors": [], "submissions": [], "forecasts": [],
            }
        # Align start to 5-min boundary.
        s = start.replace(second=0, microsecond=0)
        s = s - timedelta(minutes=s.minute % 5)
        intervals = []
        t = s
        # Cap volume defensively (e.g. one day = 288 intervals).
        max_intervals = 7 * 24 * 12
        while t < end and len(intervals) < max_intervals:
            intervals.append(t)
            t += timedelta(minutes=5)

        prices = [self._price_at(t) for t in intervals]
        demand = [self._demand_at(t) for t in intervals]
        generation = []
        interconnectors = []
        for t in intervals:
            generation.extend(self._generation_at(t))
            interconnectors.extend(self._interconnectors_at(t))

        return {
            "source": "synthetic",
            "as_of": intervals[-1] if intervals else end,
            "prices": prices,
            "demand": demand,
            "generation": generation,
            "interconnectors": interconnectors,
            "submissions": [],
            "forecasts": [],
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
