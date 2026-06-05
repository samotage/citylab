"""Solcast fetcher — REAL solar irradiance + weather from the Solcast API.

For every tracked SolarLocation this pulls actual Solcast data:
  - forecast (now -> +14 days) ->  GET /data/forecast/radiation_and_weather
  - live     (last 7 days)     ->  GET /data/live/radiation_and_weather

There is NO synthetic fallback. If the API key is missing or a request fails,
fetch() raises and run() records the error — the fetcher never fabricates data.

Budget discipline (the reason this fetcher is manual, not scheduled):
  The Solcast "New User Evaluation" plan grants a small, ONE-OFF (non-resetting)
  request budget per endpoint — 10 forecast + 10 live radiation/weather requests
  total. To avoid blowing it:
    * the fetcher is NOT scheduled (config `scheduled: false`); it runs only via
      `flask solcast-refresh`
    * retries are disabled (max_attempts = 1) so one refresh makes at most one
      call per endpoint per location
    * a persisted per-endpoint counter (data_source.config) hard-stops before
      the configured budget is exhausted, and is written back after every
      successful call so a later failure can never undercount real usage

One request returns the whole window's series, so a single forecast call yields
the full 14-day forecast and a single live call the full last-7-day actuals.

Row mapping into SolarForecast:
  - forecast rows:  issued_at = fetch time, forecast_for = period_end
  - live rows:      issued_at = forecast_for = period_end   (an "actual")
  ghi/dni/dhi/cloud_opacity/air_temp come straight from Solcast;
  estimated_pv_output_kw is a transparent linear estimate from the location's
  reference PV capacity (cap * ghi / 1000).
"""

import logging
import re
from datetime import datetime, timezone

from citylab.services.ingestion.base import BaseFetcher
from citylab.services.ingestion.registry import register_fetcher

logger = logging.getLogger(__name__)

# Default Solcast output parameters we request (and map into our schema).
DEFAULT_OUTPUT_PARAMETERS = ["ghi", "dni", "dhi", "air_temp", "cloud_opacity"]

# Solcast ISO8601 period (PTxxM) -> our forecast_period label.
_PERIOD_LABELS = {
    "PT5M": "5min",
    "PT10M": "10min",
    "PT15M": "15min",
    "PT20M": "20min",
    "PT30M": "30min",
    "PT60M": "60min",
    "PT1H": "60min",
}


def _parse_iso(s: str) -> datetime:
    """Parse a Solcast period_end (e.g. '2026-06-05T01:30:00.0000000Z')."""
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    # Python's fromisoformat accepts at most 6 fractional digits; Solcast emits 7.
    s = re.sub(r"(\.\d{6})\d+", r"\1", s)
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class SolcastFetcher(BaseFetcher):
    """Fetch REAL Solcast forecast + live radiation/weather per SolarLocation."""

    source_type = "solcast"
    # Manual/on-demand only — never retry, so one refresh == one call/endpoint.
    max_attempts = 1
    # Not scheduled, but keep a sane gap-fill interval value.
    normal_interval_seconds = 3600

    def fetch_range(self, start, end, progress=None):
        """Solcast has no historical backfill on this plan — refuse loudly.

        Raising NotImplementedError keeps gap-fill skipping Solcast (base._gap_fill
        catches it) and tells the backfill CLI to use the archive instead. The
        ICU SolarCam history is the source of truth for past irradiance.
        """
        raise NotImplementedError(
            "Solcast has no historical backfill on this plan — use the archive "
            "import (the ICU SolarCam history is the source of truth); "
            "`flask solcast-refresh` covers live + forecast going forward."
        )

    # ------------------------------------------------------------------
    # fetch
    # ------------------------------------------------------------------

    def fetch(self) -> dict:
        cfg = dict(self.data_source.config or {})
        api_key = self._require_key(cfg)
        locations = self._locations()
        if not locations:
            raise RuntimeError("no SolarLocation configured for Solcast fetch")

        budget_fc = int(cfg.get("forecast_request_budget", 10))
        budget_live = int(cfg.get("live_request_budget", 10))
        reserve = int(cfg.get("request_reserve", 0))
        used_fc = int(cfg.get("forecast_requests_used", 0))
        used_live = int(cfg.get("live_requests_used", 0))
        start_fc, start_live = used_fc, used_live

        now = datetime.now(timezone.utc)
        out_locations = []
        for loc in locations:
            forecasts = []

            if used_fc + reserve < budget_fc:
                forecasts.extend(self._fetch_forecast(loc, api_key, cfg, now))
                used_fc += 1
                self._persist_used(used_fc, used_live)  # write after each call
            else:
                logger.warning(
                    "Solcast forecast budget exhausted (%s/%s); skipping forecast",
                    used_fc, budget_fc,
                )

            if used_live + reserve < budget_live:
                forecasts.extend(self._fetch_live(loc, api_key, cfg))
                used_live += 1
                self._persist_used(used_fc, used_live)
            else:
                logger.warning(
                    "Solcast live budget exhausted (%s/%s); skipping live",
                    used_live, budget_live,
                )

            out_locations.append({"location_id": loc.id, "forecasts": forecasts})

        if used_fc == start_fc and used_live == start_live:
            raise RuntimeError(
                f"Solcast request budget exhausted "
                f"(forecast {used_fc}/{budget_fc}, live {used_live}/{budget_live}); "
                f"upgrade the Solcast plan to fetch more"
            )

        logger.info(
            "Solcast fetch: %s locations; budget used forecast %s/%s, live %s/%s",
            len(locations), used_fc, budget_fc, used_live, budget_live,
        )
        return {
            "source": "live",
            "as_of": now,
            "locations": out_locations,
            "budget": {
                "forecast_used": used_fc,
                "forecast_budget": budget_fc,
                "live_used": used_live,
                "live_budget": budget_live,
            },
        }

    # ------------------------------------------------------------------
    # API calls
    # ------------------------------------------------------------------

    def _fetch_forecast(self, loc, api_key, cfg, issued) -> list[dict]:
        data = self._request("forecast/radiation_and_weather", loc, api_key, cfg)
        return [
            self._row(loc, item, issued_at=issued)
            for item in data.get("forecasts", [])
        ]

    def _fetch_live(self, loc, api_key, cfg) -> list[dict]:
        data = self._request("live/radiation_and_weather", loc, api_key, cfg)
        # estimated_actuals -> "actual" rows (issued_at == forecast_for).
        return [
            self._row(loc, item, issued_at=None)
            for item in data.get("estimated_actuals", [])
        ]

    def _request(self, path: str, loc, api_key: str, cfg: dict) -> dict:
        import requests

        base = (
            self.data_source.base_url or "https://api.solcast.com.au"
        ).rstrip("/")
        params = cfg.get("output_parameters") or DEFAULT_OUTPUT_PARAMETERS
        if isinstance(params, str):
            params = [p.strip() for p in params.split(",") if p.strip()]
        query = {
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "output_parameters": ",".join(params),
            "period": cfg.get("period", "PT30M"),
            "format": "json",
        }
        headers = {"Authorization": f"Bearer {api_key}"}
        resp = requests.get(
            f"{base}/data/{path}",
            params=query,
            headers=headers,
            timeout=cfg.get("timeout_seconds", 15),
        )
        resp.raise_for_status()
        return resp.json()

    def _row(self, loc, item: dict, issued_at) -> dict:
        """Map one Solcast period record to a SolarForecast row dict."""
        target = _parse_iso(item["period_end"])
        ghi = item.get("ghi")
        cap = loc.reference_pv_capacity_kw or 0.0
        pv = round(cap * (ghi / 1000.0), 1) if (cap and ghi is not None) else None
        return {
            "location_id": loc.id,
            "issued_at": issued_at if issued_at is not None else target,
            "forecast_for": target,
            "forecast_period": _PERIOD_LABELS.get(
                item.get("period", "PT30M"), "30min"
            ),
            "ghi_wm2": ghi,
            "dni_wm2": item.get("dni"),
            "dhi_wm2": item.get("dhi"),
            "cloud_opacity_pct": item.get("cloud_opacity"),
            "air_temp_c": item.get("air_temp"),
            "estimated_pv_output_kw": pv,
        }

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _require_key(self, cfg: dict) -> str:
        api_key = cfg.get("api_key")
        if not api_key or str(api_key).startswith("${"):
            raise RuntimeError(
                "no Solcast API key configured (set SOLCAST_API_KEY) — refusing "
                "to fetch (no synthetic fallback)"
            )
        return str(api_key)

    def _persist_used(self, used_fc: int, used_live: int) -> None:
        """Write request counters back to data_source.config immediately.

        Reassigns the dict so SQLAlchemy detects the JSONB change; run() commits
        the DataSource, so this survives even if a later call in the same fetch
        raises (real usage is never undercounted)."""
        self.data_source.config = {
            **(self.data_source.config or {}),
            "forecast_requests_used": used_fc,
            "live_requests_used": used_live,
        }

    def _locations(self):
        from citylab.extensions import db
        from citylab.models.solar import SolarLocation

        return db.session.query(SolarLocation).order_by(SolarLocation.id).all()

    # ------------------------------------------------------------------
    # transform / store
    # ------------------------------------------------------------------

    def transform(self, raw):
        from citylab.models.solar import SolarForecast

        records = []
        for loc_block in raw["locations"]:
            for f in loc_block["forecasts"]:
                records.append(SolarForecast(**f))
        return records

    # Natural-key conflict target (must match migration eb3b9c51c3f5).
    _CONFLICT_KEYS = ["location_id", "issued_at", "forecast_for", "forecast_period"]

    def store(self, records) -> int:
        """Upsert solar forecasts (idempotent)."""
        from citylab.services.ingestion.upsert import (
            instance_to_dict,
            upsert_records,
        )

        if not records:
            return 0
        model = type(records[0])
        rows = [instance_to_dict(r) for r in records]
        return upsert_records(model, rows, self._CONFLICT_KEYS)


register_fetcher("solcast", SolcastFetcher)
