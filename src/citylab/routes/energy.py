"""Energy market dashboard — server-rendered, login-required UI at /energy.

Consumes the read-side query services in-process (energy_query, weather_query,
solar_query) — the same data the agent API serves, but with no token / no HTTP
round-trip. Each panel is an HTMX partial that the dashboard page polls.
"""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, render_template
from flask_login import login_required

from citylab.services import energy_query as eq
from citylab.services import solar_query as sq
from citylab.services import weather_query as wq

energy_bp = Blueprint("energy", __name__, url_prefix="/energy")

REGION = "VIC1"

# Minutes after a dispatch interval first appears during which the source may
# still revise it — the hero price is flagged "preliminary" within this window.
PRICE_PRELIM_WINDOW_MIN = 10

# --- Generation fuel-type aggregation -------------------------------------

# Fuel buckets + colours + the raw->bucket mapping are the shared source of
# truth in energy_query (FR8/SC9). Alias them here for local use.
_FUEL_BUCKETS = eq.FUEL_BUCKETS
_bucket_for = eq.bucket_for


def _aggregate_generation(generation_mix: list[dict]) -> dict:
    """Aggregate raw fuel rows into the display buckets.

    Returns labels/colours/values (charge shown as positive magnitude) plus
    total output (excluding charging) and a capacity-utilisation indicator.
    """
    sums: dict[str, float] = {}
    cap_sums: dict[str, float] = {}
    for row in generation_mix:
        bucket = _bucket_for(row.get("fuel_type", ""))
        sums[bucket] = sums.get(bucket, 0.0) + (row.get("output_mw") or 0.0)
        if row.get("capacity_mw"):
            cap_sums[bucket] = cap_sums.get(bucket, 0.0) + row["capacity_mw"]

    rows = []
    for key, label, colour in _FUEL_BUCKETS:
        val = sums.get(key)
        if val is None:
            continue
        rows.append((label, colour, round(abs(val), 1)))
    rows.sort(key=lambda r: r[2], reverse=True)
    labels = [r[0] for r in rows]
    colours = [r[1] for r in rows]
    outputs = [r[2] for r in rows]

    # Total generation = sum of all positive outputs excluding battery charging.
    total_output = round(
        sum(v for k, v in sums.items() if k != "battery_charging" and v > 0), 1
    )
    total_capacity = round(sum(cap_sums.values()), 1) if cap_sums else None
    utilisation = (
        round(100 * total_output / total_capacity, 1)
        if total_capacity
        else None
    )

    return {
        "labels": labels,
        "colours": colours,
        "outputs": outputs,
        "total_output_mw": total_output,
        "total_capacity_mw": total_capacity,
        "utilisation_pct": utilisation,
    }


# --- Price view-model ------------------------------------------------------

def _price_colour_state(price: float | None) -> str:
    if price is None:
        return "unknown"
    if price > 300:
        return "spike"
    if price > 150:
        return "high"
    if price >= 50:
        return "amber"
    return "low"


def _price_view_model() -> dict:
    snap = eq.current_snapshot(REGION)
    latest = snap.get("latest_price")
    demand = snap.get("latest_demand")
    nearest = snap.get("nearest_forecast")

    current_price = latest.get("price_aud_mwh") if latest else None

    # Trend vs ~1h ago: pull recent prices and find the one nearest now-60min.
    trend = "flat"
    prev_price = None
    if latest and latest.get("interval_start"):
        now_iv = eq._parse_dt(latest["interval_start"])
        target = now_iv - timedelta(minutes=60)
        recent = eq.query_prices(REGION, limit=60)
        # recent is desc; find row with interval_start closest to target.
        best = None
        best_delta = None
        for r in recent:
            riv = eq._parse_dt(r["interval_start"])
            if riv is None:
                continue
            d = abs((riv - target).total_seconds())
            if best_delta is None or d < best_delta:
                best_delta = d
                best = r
        if best:
            prev_price = best.get("price_aud_mwh")
    if current_price is not None and prev_price is not None:
        if current_price > prev_price * 1.02:
            trend = "up"
        elif current_price < prev_price * 0.98:
            trend = "down"

    next_price = nearest.get("price_aud_mwh") if nearest else None
    next_dir = "flat"
    if current_price is not None and next_price is not None:
        if next_price > current_price * 1.02:
            next_dir = "up"
        elif next_price < current_price * 0.98:
            next_dir = "down"

    range_low = None
    range_high = None
    recent_24h = eq.query_prices(
        REGION, dt_from=datetime.now(timezone.utc) - timedelta(hours=24), limit=500
    )
    prices_24h = [
        r["price_aud_mwh"] for r in recent_24h if r.get("price_aud_mwh") is not None
    ]
    if prices_24h:
        range_low = round(min(prices_24h), 0)
        range_high = round(max(prices_24h), 0)

    # Preliminary vs settled: the leading dispatch interval is republished and
    # revised by the market for a few minutes after it first appears (we watched
    # one interval move $104 -> $15 -> $46 before settling). Flag the hero price
    # as preliminary while it's inside that revision window so the dashboard
    # never silently disagrees with AEMO's settled price.
    price_status = None
    if latest and latest.get("interval_start"):
        iv = eq._parse_dt(latest["interval_start"])
        if iv is not None:
            age = datetime.now(timezone.utc) - iv
            price_status = (
                "preliminary"
                if age < timedelta(minutes=PRICE_PRELIM_WINDOW_MIN)
                else "settled"
            )

    return {
        "price": current_price,
        "colour_state": _price_colour_state(current_price),
        "trend": trend,
        "prev_price": prev_price,
        "demand_mw": demand.get("demand_mw") if demand else None,
        "interval_start": latest.get("interval_start") if latest else None,
        "price_status": price_status,
        "next_price": next_price,
        "next_direction": next_dir,
        "next_forecast_for": nearest.get("forecast_for") if nearest else None,
        "range_low": range_low,
        "range_high": range_high,
    }


# --- Interconnector view-model --------------------------------------------

# Maps raw interconnector_id -> friendly corridor name + the region/state it
# trades with, so we can describe flow direction relative to Victoria.
_CORRIDORS = {
    "T-V-MNSP1": {"name": "Basslink", "partner": "Tas"},
    "V-SA": {"name": "Heywood", "partner": "SA"},
    "V-S-MNSP1": {"name": "Murraylink", "partner": "SA"},
    "VIC1-NSW1": {"name": "VNI", "partner": "NSW"},
    "VNI-WEST": {"name": "VNI West", "partner": "NSW"},
}


def _interconnector_view_model() -> dict:
    snap = eq.current_snapshot(REGION)
    rows = snap.get("interconnectors", [])
    corridors = []
    vic_net = 0.0  # positive = net import into VIC

    for ic_id, meta in _CORRIDORS.items():
        row = next((r for r in rows if r["interconnector_id"] == ic_id), None)
        if not row:
            corridors.append(
                {
                    "name": meta["name"],
                    "partner": meta["partner"],
                    "available": False,
                }
            )
            continue

        flow = row.get("flow_mw") or 0.0
        cap = row.get("capacity_mw") or row.get("limit_mw")
        from_region = row.get("from_region")
        # Flow is defined from_region -> to_region (positive). Determine sign
        # relative to Victoria.
        if row.get("to_region") == "VIC1":
            vic_signed = flow  # importing into VIC when flow positive
        elif from_region == "VIC1":
            vic_signed = -flow  # exporting out of VIC when flow positive
        else:
            vic_signed = 0.0
        vic_net += vic_signed

        importing = vic_signed >= 0
        util = (
            round(100 * abs(flow) / cap, 1) if cap else None
        )
        if util is None:
            state = "normal"
        elif util >= 95:
            state = "constrained"
        elif util >= 75:
            state = "high"
        else:
            state = "normal"

        corridors.append(
            {
                "name": meta["name"],
                "partner": meta["partner"],
                "available": True,
                "flow_mw": round(abs(vic_signed), 1),
                "raw_flow_mw": round(flow, 1),
                "direction": "import" if importing else "export",
                "capacity_mw": round(cap, 1) if cap else None,
                "utilisation_pct": util,
                "state": state,
            }
        )

    return {
        "corridors": corridors,
        "net_mw": round(abs(vic_net), 1),
        "net_direction": "import" if vic_net >= 0 else "export",
    }


# --- Weather view-model ----------------------------------------------------

def _wind_band(kmh: float | None) -> str:
    if kmh is None:
        return "unknown"
    if kmh >= 40:
        return "strong"
    if kmh >= 20:
        return "moderate"
    return "light"


def _solar_band(ghi: float | None) -> str:
    if ghi is None:
        return "unknown"
    if ghi >= 600:
        return "sunny"
    if ghi >= 250:
        return "partly cloudy"
    return "overcast"


def _rain_band(mm: float | None) -> str:
    if mm is None:
        return "unknown"
    if mm >= 15:
        return "heavy"
    if mm >= 5:
        return "moderate"
    if mm > 0.2:
        return "light"
    return "dry"


def _weather_view_model() -> dict:
    # Wind across SA + Vic corridors.
    wind = wq.outlook("wind")
    wind_peaks = [
        loc["headline"].get("peak_wind_kmh")
        for loc in wind.get("locations", [])
        if loc["headline"].get("peak_wind_kmh") is not None
    ]
    wind_peak = max(wind_peaks) if wind_peaks else None

    # Rain across hydro catchments (Tas + Snowy) — use rain outlook totals.
    rain = wq.outlook("rain")
    rain_totals = [
        loc["headline"].get("total_rainfall_mm")
        for loc in rain.get("locations", [])
        if loc["headline"].get("total_rainfall_mm") is not None
    ]
    rain_total = max(rain_totals) if rain_totals else None

    # Temperature — Melbourne current + forecast max.
    temp = wq.outlook("temperature")
    mel = next(
        (
            loc
            for loc in temp.get("locations", [])
            if "melbourne" in loc["location"]["name"].lower()
        ),
        None,
    )
    temp_now = None
    temp_max = None
    if mel:
        temp_max = mel["headline"].get("max_temp_c")
        if mel.get("series"):
            temp_now = mel["series"][0].get("temperature_c")

    # Solar irradiance from solar summary (peak GHI across groups).
    solar = sq.summary()
    solar_peaks = [
        g.get("group_peak_ghi_wm2")
        for g in solar.get("groups", {}).values()
        if g.get("group_peak_ghi_wm2") is not None
    ]
    solar_peak = max(solar_peaks) if solar_peaks else None

    return {
        "wind": {"band": _wind_band(wind_peak), "peak_kmh": wind_peak},
        "solar": {"band": _solar_band(solar_peak), "peak_ghi": solar_peak},
        "rain": {"band": _rain_band(rain_total), "total_mm": rain_total},
        "temperature": {"now_c": temp_now, "max_c": temp_max},
    }


# --- Forecast view-model ---------------------------------------------------

def _hhmm(dt: datetime) -> str:
    """Format a UTC datetime as local-ish HH:MM (AEST, UTC+10) for axis labels."""
    local = dt.astimezone(timezone(timedelta(hours=10)))
    return local.strftime("%H:%M")


def _forecast_view_model() -> dict:
    """Build a category-axis series: a sorted union of timestamps over the
    next 24h (forecast) plus the last 12h (actuals), with each series aligned
    to that shared label axis so a plain category line chart can overlay them.
    """
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(hours=24)

    forecasts = eq.query_forecasts(REGION)
    fc = {}
    for f in forecasts:
        ff = eq._parse_dt(f.get("forecast_for"))
        if ff is None or ff < now - timedelta(hours=1) or ff > horizon:
            continue
        fc[ff] = f.get("price_aud_mwh")

    actuals_raw = eq.query_prices(
        REGION, dt_from=now - timedelta(hours=12), limit=200
    )
    ac = {}
    for r in actuals_raw:
        riv = eq._parse_dt(r["interval_start"])
        if riv is None:
            continue
        ac[riv] = r.get("price_aud_mwh")

    all_times = sorted(set(fc) | set(ac))
    labels = [_hhmm(t) for t in all_times]
    forecast_series = [fc.get(t) for t in all_times]
    actual_series = [ac.get(t) for t in all_times]

    return {
        "labels": labels,
        "forecast_series": forecast_series,
        "actual_series": actual_series,
    }


# --- Source health view-model ---------------------------------------------

# Expected cadence in minutes per source type (for staleness detection).
_EXPECTED_INTERVAL_MIN = {
    "opennem": 5,
    "bom": 30,
    "solcast": 60,
}

_SOURCE_LABELS = {
    "opennem": "OpenNEM",
    "bom": "BOM",
    "solcast": "Solcast",
}


def _sources_view_model() -> dict:
    from citylab.models.data_source import DataSource
    from citylab.extensions import db

    rows = db.session.query(DataSource).order_by(DataSource.name).all()
    now = datetime.now(timezone.utc)
    sources = []
    for r in rows:
        stype = r.source_type
        last = r.last_fetch_at
        stale = False
        age_min = None
        if last is not None:
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            age_min = (now - last).total_seconds() / 60
            expected = _EXPECTED_INTERVAL_MIN.get(stype, 60)
            stale = age_min > 2 * expected
        last_fetch_local = None
        if last is not None:
            last_fetch_local = last.astimezone(
                timezone(timedelta(hours=10))
            ).strftime("%H:%M AEST")
        sources.append(
            {
                "label": _SOURCE_LABELS.get(stype, r.name),
                "source_type": stype,
                "ok": r.last_fetch_status == "success" and not stale,
                "status": r.last_fetch_status,
                "last_fetch_local": last_fetch_local,
                "age_min": round(age_min) if age_min is not None else None,
                "stale": stale,
            }
        )
    return {"sources": sources}


# --- Routes ----------------------------------------------------------------

@energy_bp.route("/")
@login_required
def dashboard():
    # The chat panel calls the Bearer-authed /api/v1/agent/* endpoints
    # client-side, so hand the logged-in browser the configured API token
    # (same pattern as the charts partial). Also resolve the default agent's
    # display name for the panel header.
    cfg = current_app.config.get("CITYLAB_CONFIG", {})
    api_token = cfg.get("api", {}).get("token", "")
    default_agent = "Ray"
    personas = cfg.get("headspace", {}).get("personas", []) or []
    if personas:
        default_agent = personas[0].get("name", "Ray")
    return render_template(
        "energy/dashboard.html",
        api_token=api_token,
        default_agent=default_agent,
    )


@energy_bp.route("/partials/price")
@login_required
def partial_price():
    return render_template("energy/partials/price.html", vm=_price_view_model())


@energy_bp.route("/partials/generation")
@login_required
def partial_generation():
    snap = eq.current_snapshot(REGION)
    vm = _aggregate_generation(snap.get("generation_mix", []))
    return render_template("energy/partials/generation.html", vm=vm)


@energy_bp.route("/partials/interconnectors")
@login_required
def partial_interconnectors():
    return render_template(
        "energy/partials/interconnectors.html", vm=_interconnector_view_model()
    )


@energy_bp.route("/partials/weather")
@login_required
def partial_weather():
    return render_template(
        "energy/partials/weather.html", vm=_weather_view_model()
    )


@energy_bp.route("/partials/forecast")
@login_required
def partial_forecast():
    return render_template(
        "energy/partials/forecast.html", vm=_forecast_view_model()
    )


@energy_bp.route("/partials/sources")
@login_required
def partial_sources():
    return render_template(
        "energy/partials/sources.html", vm=_sources_view_model()
    )


@energy_bp.route("/partials/charts")
@login_required
def partial_charts():
    # The charts call the Bearer-authed timeseries API client-side, so hand the
    # logged-in browser the configured API token to use for those fetches.
    api_token = (
        current_app.config.get("CITYLAB_CONFIG", {})
        .get("api", {})
        .get("token", "")
    )
    return render_template("energy/partials/charts.html", api_token=api_token)
