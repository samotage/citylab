"""OpenNEM fetcher — NEM-wide market data (all 5 regions).

Primary source: OpenNEM API (https://api.opennem.org.au). Where OpenNEM lacks a
dataset (pre-dispatch forecasts, detailed generator submissions) AEMO is used as
a secondary source within this same fetcher — AEMO is an implementation detail,
not a separate DataSource.

Each NEM region (NSW1, QLD1, SA1, TAS1, VIC1) gets its own DataSource row and
fetcher instance. The region is read from DataSource.config["region"].

Hackathon resilience: live API calls are attempted, but if the network/API is
unavailable the fetcher falls back to a synthetic-but-realistic market snapshot
so the demo always has data to reason on. The fallback is clearly flagged in logs.
"""

import logging
import math
import random
from datetime import datetime, timedelta, timezone

from citylab.services.ingestion.base import BaseFetcher
from citylab.services.ingestion.registry import register_fetcher

logger = logging.getLogger(__name__)

NEM_REGIONS = ["NSW1", "QLD1", "SA1", "TAS1", "VIC1"]

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

FUEL_TYPES = [
    "brown_coal",
    "black_coal",
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

# All NEM interconnectors — covers every corridor.
INTERCONNECTORS = [
    {"id": "T-V-MNSP1", "name": "Basslink", "from": "TAS1", "to": "VIC1", "capacity": 478},
    {"id": "V-SA", "name": "Heywood", "from": "VIC1", "to": "SA1", "capacity": 650},
    {"id": "V-S-MNSP1", "name": "Murraylink", "from": "VIC1", "to": "SA1", "capacity": 220},
    {"id": "VIC1-NSW1", "name": "VNI", "from": "NSW1", "to": "VIC1", "capacity": 1900},
    {"id": "VNI-WEST", "name": "VNI West", "from": "NSW1", "to": "VIC1", "capacity": 1900},
    {"id": "N-Q-MNSP1", "name": "Directlink", "from": "NSW1", "to": "QLD1", "capacity": 180},
    {"id": "QNI", "name": "QNI", "from": "NSW1", "to": "QLD1", "capacity": 600},
]

OPENNEM_FUEL_MAP = {
    "coal_brown": "brown_coal",
    "coal_black": "black_coal",
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

# Base v4 fueltech map — coal type resolved per-region at parse time.
_V4_FUELTECH_MAP_BASE = {
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

# Region-specific synthetic generation profiles.
# Each fuel entry: (base_mw, peak_adder_mw).
_REGION_PROFILES = {
    "VIC1": {
        "base_demand": 4200, "demand_range": 2600,
        "base_price": 45, "price_range": 90,
        "mix": {
            "brown_coal": (3000, 400),
            "gas_ccgt": (200, 500),
            "gas_ocgt": (50, 300),
            "gas_recip": (10, 30),
            "gas_steam": (20, 0),
            "solar_utility": (900, 0),
            "solar_rooftop": (1400, 0),
            "wind": (1800, 0),
            "hydro": (150, 400),
            "battery_discharging": (250, 0),
            "battery_charging": (-180, 0),
            "biomass": (30, 0),
            "distillate": (5, 0),
        },
    },
    "NSW1": {
        "base_demand": 6000, "demand_range": 3500,
        "base_price": 50, "price_range": 100,
        "mix": {
            "black_coal": (6000, 800),
            "gas_ccgt": (500, 600),
            "gas_ocgt": (100, 400),
            "gas_recip": (5, 20),
            "gas_steam": (30, 0),
            "solar_utility": (1200, 0),
            "solar_rooftop": (2000, 0),
            "wind": (1200, 0),
            "hydro": (800, 1200),
            "battery_discharging": (200, 0),
            "battery_charging": (-150, 0),
            "biomass": (40, 0),
            "distillate": (5, 0),
        },
    },
    "QLD1": {
        "base_demand": 5000, "demand_range": 2800,
        "base_price": 42, "price_range": 85,
        "mix": {
            "black_coal": (4500, 600),
            "gas_ccgt": (800, 400),
            "gas_ocgt": (200, 300),
            "gas_recip": (10, 20),
            "gas_steam": (50, 0),
            "solar_utility": (1500, 0),
            "solar_rooftop": (2500, 0),
            "wind": (600, 0),
            "hydro": (300, 200),
            "battery_discharging": (100, 0),
            "battery_charging": (-80, 0),
            "biomass": (100, 0),
            "distillate": (5, 0),
        },
    },
    "SA1": {
        "base_demand": 1200, "demand_range": 600,
        "base_price": 55, "price_range": 120,
        "mix": {
            "gas_ccgt": (300, 200),
            "gas_ocgt": (200, 300),
            "gas_recip": (20, 30),
            "gas_steam": (10, 0),
            "solar_utility": (500, 0),
            "solar_rooftop": (800, 0),
            "wind": (2000, 0),
            "battery_discharging": (200, 0),
            "battery_charging": (-150, 0),
            "biomass": (10, 0),
            "distillate": (10, 0),
        },
    },
    "TAS1": {
        "base_demand": 900, "demand_range": 300,
        "base_price": 40, "price_range": 60,
        "mix": {
            "hydro": (1800, 400),
            "wind": (500, 0),
            "gas_ocgt": (50, 100),
            "solar_utility": (50, 0),
            "solar_rooftop": (80, 0),
            "biomass": (10, 0),
        },
    },
}

_REGION_STATIONS = {
    "VIC1": [
        ("Loy Yang A", "LYA1", "brown_coal"),
        ("Yallourn W", "YWPS1", "brown_coal"),
        ("Newport", "NPS1", "gas_steam"),
        ("Mortlake", "MORTLK11", "gas_ocgt"),
        ("Bald Hills Wind", "BALDHWF1", "wind"),
    ],
    "NSW1": [
        ("Eraring", "ER01", "black_coal"),
        ("Bayswater", "BW01", "black_coal"),
        ("Tumut 3", "TUMUT3", "hydro"),
        ("Tallawarra", "TALLAWB1", "gas_ccgt"),
        ("Silverton Wind", "STWF1", "wind"),
    ],
    "QLD1": [
        ("Gladstone", "GLAD1", "black_coal"),
        ("Callide B", "CPP_3", "black_coal"),
        ("Swanbank E", "SWAN_E", "gas_ccgt"),
        ("Coopers Gap Wind", "CPGWF1", "wind"),
        ("Sun Metals Solar", "SMCSF1", "solar_utility"),
    ],
    "SA1": [
        ("Torrens Island A", "TORRA1", "gas_steam"),
        ("Pelican Point", "PPCCGT", "gas_ccgt"),
        ("Hornsdale Wind", "HDWF1", "wind"),
        ("Hornsdale Battery", "HPRG1", "battery_discharging"),
        ("Bungala Solar", "BNGSF1", "solar_utility"),
    ],
    "TAS1": [
        ("Gordon", "GORDON", "hydro"),
        ("John Butters", "JBT01", "hydro"),
        ("Musselroe Wind", "MUSSWF1", "wind"),
        ("Tamar Valley", "TVPP104", "gas_ccgt"),
        ("Woolnorth Wind", "WOOLNTH1", "wind"),
    ],
}


class OpenNEMFetcher(BaseFetcher):
    """Fetch NEM market data from OpenNEM (+ AEMO for forecasts/bids).

    Region is read from DataSource.config["region"] — one instance per region.
    """

    source_type = "opennem"
    normal_interval_seconds = 600

    @property
    def region(self):
        return self.config.get("region", "VIC1")

    @property
    def _profile(self):
        return _REGION_PROFILES.get(self.region, _REGION_PROFILES["VIC1"])

    def _v4_fueltech_map(self):
        """Region-aware fueltech mapping — coal type depends on region."""
        coal_type = "brown_coal" if self.region == "VIC1" else "black_coal"
        return {**_V4_FUELTECH_MAP_BASE, "coal": coal_type}

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
            return self._fetch_live(backfill=backfill)
        try:
            return self._fetch_live(backfill=backfill)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "OpenElectricity live fetch unavailable (%s) for %s; synthetic "
                "fallback ENABLED via config — data will be FABRICATED",
                exc, self.region,
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
        """Live OpenElectricity v4 fetch + parse. Raises on any failure."""
        market = self._get_v4(
            "market/network/NEM",
            {
                "metrics": ["price", "demand"],
                "interval": "5m",
                "network_region": self.region,
                "primary_grouping": "network_region",
            },
        )
        power = self._get_v4(
            "data/network/NEM",
            {
                "metrics": "power",
                "interval": "5m",
                "network_region": self.region,
                "secondary_grouping": "fueltech_group",
            },
        )
        snap = self._parse_v4(market, power)
        snap["source"] = "live"
        logger.info(
            "OpenElectricity v4 parse OK (%s): %s prices, %s demand, %s gen rows",
            self.region, len(snap["prices"]), len(snap["demand"]),
            len(snap["generation"]),
        )
        return snap

    def _get_v4(self, path: str, params: dict) -> dict:
        """GET an OpenElectricity v4 endpoint and return the parsed JSON."""
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
        """Expand a v4 result block's ``data`` into [(timestamp, value), ...]."""
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
        """Parse v4 market (price/demand) + data (power) payloads."""
        region = self.region
        fueltech_map = self._v4_fueltech_map()
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
                                "region": region,
                                "interval_start": ts,
                                "interval_end": ts + timedelta(minutes=5),
                                "interval_type": "5min",
                                "price_aud_mwh": round(float(v), 2),
                            }
                        )
                    elif metric == "demand":
                        demand.append(
                            {
                                "region": region,
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
                fuel = fueltech_map.get(str(group).lower())
                if fuel is None:
                    continue
                for ts, v in self._v4_points(result):
                    latest_ts = max(latest_ts or ts, ts)
                    generation.append(
                        {
                            "region": region,
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
            "interconnectors": [],
            "submissions": [],
            "forecasts": [],
        }

    # ------------------------------------------------------------------
    # Historical date-range fetching (FR8)
    # ------------------------------------------------------------------

    def fetch_range(self, start, end, progress=None):
        """Fetch region data for [start, end)."""
        start = _parse_iso(start)
        end = _parse_iso(end)
        if start is None or end is None or start >= end:
            if self.config.get("allow_synthetic_fallback", False):
                return self._synthetic_range(start, end)
            raise ValueError(f"Invalid range for fetch_range: {start}..{end}")

        if not self.config.get("allow_synthetic_fallback", False):
            return self._fetch_range_live(start, end)
        try:
            return self._fetch_range_live(start, end)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "OpenElectricity range fetch unavailable (%s) for %s; synthetic "
                "fallback ENABLED via config — data will be FABRICATED "
                "%s..%s", exc, self.region, start.date(), end.date(),
            )
            return self._synthetic_range(start, end)

    def _fetch_range_live(self, start, end):
        """Live v4 date-range query (market + data), parsed via _parse_v4."""
        params_common = {
            "interval": "5m",
            "network_region": self.region,
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
        """Synthetic snapshot covering [start, end) at 5-min resolution."""
        if start is None or end is None or start >= end:
            return {
                "source": "synthetic",
                "as_of": datetime.now(timezone.utc),
                "prices": [], "demand": [], "generation": [],
                "interconnectors": [], "submissions": [], "forecasts": [],
            }
        s = start.replace(second=0, microsecond=0)
        s = s - timedelta(minutes=s.minute % 5)
        intervals = []
        t = s
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
    # Synthetic snapshot — region-aware market data
    # ------------------------------------------------------------------

    def _synthetic(self, backfill: bool) -> dict:
        """Generate a realistic snapshot for this region."""
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        now = now - timedelta(minutes=now.minute % 5)

        if backfill:
            intervals = [now - timedelta(minutes=5 * i) for i in range(7 * 24 * 12)]
        else:
            since = self.data_source.last_fetch_at
            count = 12
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
        p = self._profile
        base = p["base_price"] + p["price_range"] * factor
        price = round(base + random.uniform(-15, 25), 2)
        return {
            "region": self.region,
            "interval_start": t,
            "interval_end": t + timedelta(minutes=5),
            "interval_type": "5min",
            "price_aud_mwh": price,
        }

    def _demand_at(self, t: datetime) -> dict:
        factor = self._daily_factor(t)
        p = self._profile
        demand = round(p["base_demand"] + p["demand_range"] * factor + random.uniform(-150, 150), 1)
        return {
            "region": self.region,
            "interval_start": t,
            "demand_mw": demand,
            "demand_type": "actual",
        }

    def _generation_at(self, t: datetime) -> list[dict]:
        factor = self._daily_factor(t)
        h = t.hour + t.minute / 60.0
        solar = max(0.0, math.sin((h - 6) / 12 * math.pi)) if 6 <= h <= 18 else 0.0
        wind_factor = 0.3 + 0.5 * random.random()
        charging = solar * (h < 15)
        discharging = factor * (h >= 17 or h < 7)

        profile_mix = self._profile["mix"]
        rows = []
        for fuel, (base, peak_add) in profile_mix.items():
            if fuel in ("solar_utility", "solar_rooftop"):
                mw = base * solar
            elif fuel == "wind":
                mw = base * wind_factor
            elif fuel == "battery_discharging":
                mw = base * discharging
            elif fuel == "battery_charging":
                mw = base * charging
            elif fuel == "distillate":
                mw = base * (factor > 0.85)
            else:
                mw = base + peak_add * factor
            rows.append(
                {
                    "region": self.region,
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
            if ic["from"] != self.region and ic["to"] != self.region:
                continue
            direction = 1 if ic["to"] == self.region else -1
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
        stations = _REGION_STATIONS.get(self.region, _REGION_STATIONS["VIC1"])
        rows = []
        for station, unit, fuel in stations:
            for band in range(1, 4):
                rows.append(
                    {
                        "station_name": station,
                        "unit_id": unit,
                        "fuel_type": fuel,
                        "region": self.region,
                        "interval_start": t,
                        "bid_band": band,
                        "price_aud_mwh": round(-50 + band * 60 + random.uniform(-10, 10), 2),
                        "volume_mw": round(50 + random.uniform(0, 250), 1),
                    }
                )
        return rows

    def _forecasts_at(self, t: datetime) -> list[dict]:
        p = self._profile
        rows = []
        for i in range(1, 9):
            target = t + timedelta(minutes=30 * i)
            factor = self._daily_factor(target)
            rows.append(
                {
                    "region": self.region,
                    "forecast_issued_at": t,
                    "forecast_for": target,
                    "price_aud_mwh": round(
                        p["base_price"] + p["price_range"] * factor + random.uniform(-10, 20), 2
                    ),
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
                from citylab.extensions import db

                for inst in instances:
                    db.session.add(inst)
                db.session.flush()
                total += len(instances)
                continue
            total += upsert_records(model, rows, conflict)
        return total


register_fetcher("opennem", OpenNEMFetcher)
