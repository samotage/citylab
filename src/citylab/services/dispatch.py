"""Storage dispatch engine — 6-rule decision tree for battery BESS assets.

Evaluated on every ingestion cycle (5-min cron, after OpenNEM data lands) or
on-demand via API. First matching rule wins; SoC is updated and a DispatchEvent
is logged.
"""

import logging
from datetime import datetime, timedelta, timezone

from citylab.config import load_config
from citylab.extensions import db
from citylab.models.battery import BatteryAsset, DispatchEvent
from citylab.models.energy import (
    EnergyPrice,
    InterconnectorFlow,
    PriceForecast,
)
from citylab.models.solar import SolarForecast, SolarLocation
from citylab.models.weather import WeatherForecast, WeatherLocation, WeatherObservation

logger = logging.getLogger(__name__)

INTERVAL_MINUTES = 5

_REGION_TO_STATE = {
    "VIC1": "VIC",
    "NSW1": "NSW",
    "QLD1": "QLD",
    "SA1": "SA",
    "TAS1": "TAS",
}


def _load_thresholds() -> dict:
    cfg = load_config().get("dispatch", {}) or {}
    return {
        "discharge_threshold": cfg.get("discharge_threshold_aud_mwh", 150),
        "charge_threshold": cfg.get("charge_threshold_aud_mwh", 40),
        "ic_stress_pct": cfg.get("interconnector_stress_pct", 85),
        "solar_cloud_trigger": cfg.get("solar_cloud_opacity_trigger_pct", 60),
        "wind_drop_trigger": cfg.get("wind_drop_trigger_pct", 30),
        "pre_position_ceiling": cfg.get("pre_position_soc_ceiling_pct", 70),
    }


def _latest_spot_price(region: str) -> float | None:
    row = (
        db.session.query(EnergyPrice)
        .filter(EnergyPrice.region == region)
        .order_by(EnergyPrice.interval_start.desc())
        .first()
    )
    return row.price_aud_mwh if row else None


def _latest_forecast_price(region: str) -> float | None:
    now = datetime.now(timezone.utc)
    row = (
        db.session.query(PriceForecast)
        .filter(
            PriceForecast.region == region,
            PriceForecast.forecast_for >= now,
        )
        .order_by(PriceForecast.forecast_for.asc())
        .first()
    )
    return row.price_aud_mwh if row else None


def _check_interconnector_stress(region: str, threshold_pct: float) -> tuple[bool, str | None]:
    """Rule 1: any interconnector touching this region at >threshold% capacity."""
    latest_ts = (
        db.session.query(InterconnectorFlow.interval_start)
        .filter(
            (InterconnectorFlow.from_region == region)
            | (InterconnectorFlow.to_region == region)
        )
        .order_by(InterconnectorFlow.interval_start.desc())
        .first()
    )
    if not latest_ts:
        return False, None

    flows = (
        db.session.query(InterconnectorFlow)
        .filter(
            InterconnectorFlow.interval_start == latest_ts[0],
            (InterconnectorFlow.from_region == region)
            | (InterconnectorFlow.to_region == region),
        )
        .all()
    )

    for f in flows:
        if f.capacity_mw and f.capacity_mw > 0:
            utilisation = abs(f.flow_mw) / f.capacity_mw * 100
            if utilisation > threshold_pct:
                return True, (
                    f"{f.interconnector_id} at {utilisation:.0f}% capacity "
                    f"({abs(f.flow_mw):.0f}/{f.capacity_mw:.0f} MW) — "
                    f"holding reserve for contingency headroom"
                )
    return False, None


def _check_solar_pre_position(region: str, threshold_cloud: float) -> tuple[bool, str | None]:
    """Rule 2: cloud opacity >threshold in 10-16h window, next 2h forecasts."""
    now = datetime.now(timezone.utc)
    # Melbourne is UTC+10/+11; approximate local hour
    local_hour = (now + timedelta(hours=10)).hour
    if local_hour < 10 or local_hour > 16:
        return False, None

    state = _REGION_TO_STATE.get(region)
    if not state:
        return False, None

    location_ids = [
        r[0]
        for r in db.session.query(SolarLocation.id)
        .filter(SolarLocation.state == state)
        .all()
    ]
    if not location_ids:
        return False, None

    horizon = now + timedelta(hours=2)
    forecasts = (
        db.session.query(SolarForecast)
        .filter(
            SolarForecast.location_id.in_(location_ids),
            SolarForecast.forecast_for >= now,
            SolarForecast.forecast_for <= horizon,
            SolarForecast.cloud_opacity_pct.isnot(None),
        )
        .all()
    )

    if not forecasts:
        return False, None

    opacities = [f.cloud_opacity_pct for f in forecasts]
    avg_opacity = sum(opacities) / len(opacities)

    if avg_opacity > threshold_cloud:
        return True, (
            f"Cloud band forecast (avg opacity {avg_opacity:.0f}%) — "
            f"pre-charging before solar output drops"
        )
    return False, None


def _check_wind_pre_position(region: str, drop_pct_threshold: float) -> tuple[bool, str | None]:
    """Rule 3: wind speed dropping >threshold% in next 3h vs current."""
    state = _REGION_TO_STATE.get(region)
    if not state:
        return False, None

    wind_locations = (
        db.session.query(WeatherLocation)
        .filter(
            WeatherLocation.state == state,
            WeatherLocation.region_relevance == "wind_corridor",
        )
        .all()
    )
    if not wind_locations:
        return False, None

    now = datetime.now(timezone.utc)
    horizon = now + timedelta(hours=3)

    for loc in wind_locations:
        current_obs = (
            db.session.query(WeatherObservation)
            .filter(WeatherObservation.location_id == loc.id)
            .order_by(WeatherObservation.observed_at.desc())
            .first()
        )
        if not current_obs or not current_obs.wind_speed_kmh:
            continue

        future_forecasts = (
            db.session.query(WeatherForecast)
            .filter(
                WeatherForecast.location_id == loc.id,
                WeatherForecast.forecast_for >= now,
                WeatherForecast.forecast_for <= horizon,
                WeatherForecast.wind_speed_kmh.isnot(None),
            )
            .order_by(WeatherForecast.forecast_for.desc())
            .first()
        )
        if not future_forecasts:
            continue

        current_speed = current_obs.wind_speed_kmh
        future_speed = future_forecasts.wind_speed_kmh
        if current_speed > 0:
            drop_pct = (current_speed - future_speed) / current_speed * 100
            if drop_pct > drop_pct_threshold:
                return True, (
                    f"Wind corridor speed dropping {drop_pct:.0f}% in next 3h "
                    f"({loc.name}: {current_speed:.0f} -> {future_speed:.0f} km/h) — "
                    f"pre-charging ahead of reduced wind generation"
                )

    return False, None


def _update_soc(battery: BatteryAsset, action: str, power_mw: float) -> float:
    """Calculate new SoC after a dispatch action over one 5-min interval.

    Charging: energy_in = power * (5/60) * sqrt(efficiency)
    Discharging: energy_out = power * (5/60) / sqrt(efficiency)
    """
    interval_hours = INTERVAL_MINUTES / 60.0

    if action == "charge":
        eff_factor = battery.roundtrip_eff ** 0.5
        energy_mwh = power_mw * interval_hours * eff_factor
        delta_pct = (energy_mwh / battery.capacity_mwh) * 100
        new_soc = battery.current_soc_pct + delta_pct
    elif action == "discharge":
        eff_factor = battery.roundtrip_eff ** 0.5
        energy_mwh = power_mw * interval_hours / eff_factor
        delta_pct = (energy_mwh / battery.capacity_mwh) * 100
        new_soc = battery.current_soc_pct - delta_pct
    else:
        new_soc = battery.current_soc_pct

    return max(battery.min_soc_pct, min(battery.max_soc_pct, round(new_soc, 2)))


def evaluate(battery: BatteryAsset, commit: bool = True) -> dict:
    """Run the 6-rule dispatch decision tree for a battery. Returns the decision.

    If commit=True, updates SoC, battery status, and logs a DispatchEvent.
    If commit=False, returns recommendation only (dry run).
    """
    t = _load_thresholds()
    now = datetime.now(timezone.utc)
    soc_before = battery.current_soc_pct
    spot_price = _latest_spot_price(battery.region)
    forecast_price = _latest_forecast_price(battery.region)

    action = "hold"
    power_mw = 0.0
    trigger = "default_hold"
    reason = f"No dispatch trigger — holding current SoC at {soc_before:.1f}%"

    # Rule 1: Interconnector stress hold
    if soc_before > battery.reserve_soc_pct:
        stressed, ic_reason = _check_interconnector_stress(
            battery.region, t["ic_stress_pct"]
        )
        if stressed:
            action = "hold"
            power_mw = 0.0
            trigger = "interconnector_stress"
            reason = ic_reason
            return _finalise(
                battery, now, action, power_mw, trigger, reason,
                soc_before, spot_price, forecast_price, commit,
            )

    # Rule 2: Solar pre-position (charge)
    if soc_before < t["pre_position_ceiling"]:
        solar_triggered, solar_reason = _check_solar_pre_position(
            battery.region, t["solar_cloud_trigger"]
        )
        if solar_triggered:
            action = "charge"
            power_mw = battery.max_power_mw
            trigger = "solar_pre_position"
            reason = solar_reason
            return _finalise(
                battery, now, action, power_mw, trigger, reason,
                soc_before, spot_price, forecast_price, commit,
            )

    # Rule 3: Wind pre-position (charge)
    if soc_before < t["pre_position_ceiling"]:
        wind_triggered, wind_reason = _check_wind_pre_position(
            battery.region, t["wind_drop_trigger"]
        )
        if wind_triggered:
            action = "charge"
            power_mw = battery.max_power_mw
            trigger = "wind_pre_position"
            reason = wind_reason
            return _finalise(
                battery, now, action, power_mw, trigger, reason,
                soc_before, spot_price, forecast_price, commit,
            )

    # Rule 4: Price arbitrage — discharge
    if forecast_price is not None and forecast_price > t["discharge_threshold"]:
        if soc_before > battery.reserve_soc_pct:
            action = "discharge"
            power_mw = battery.max_power_mw
            trigger = "price_forecast"
            reason = (
                f"Forecast price ${forecast_price:.0f}/MWh exceeds discharge "
                f"threshold — dispatching into high-price period"
            )
            return _finalise(
                battery, now, action, power_mw, trigger, reason,
                soc_before, spot_price, forecast_price, commit,
            )

    # Rule 5: Price arbitrage — charge
    if spot_price is not None and spot_price < t["charge_threshold"]:
        if soc_before < battery.max_soc_pct:
            action = "charge"
            power_mw = battery.max_power_mw
            trigger = "price_forecast"
            reason = (
                f"Spot price ${spot_price:.0f}/MWh below charge threshold — "
                f"accumulating cheap energy"
            )
            return _finalise(
                battery, now, action, power_mw, trigger, reason,
                soc_before, spot_price, forecast_price, commit,
            )

    # Rule 6: Default hold
    return _finalise(
        battery, now, action, power_mw, trigger, reason,
        soc_before, spot_price, forecast_price, commit,
    )


def _finalise(
    battery: BatteryAsset,
    timestamp: datetime,
    action: str,
    power_mw: float,
    trigger: str,
    reason: str,
    soc_before: float,
    spot_price: float | None,
    forecast_price: float | None,
    commit: bool,
) -> dict:
    """Update SoC, log the event, return the decision dict."""
    soc_after = _update_soc(battery, action, power_mw)

    status_map = {"charge": "charging", "discharge": "discharging", "hold": "holding"}

    if commit:
        battery.current_soc_pct = soc_after
        battery.status = status_map.get(action, "idle")

        event = DispatchEvent(
            battery_id=battery.id,
            timestamp=timestamp,
            action=action,
            power_mw=power_mw,
            soc_before_pct=soc_before,
            soc_after_pct=soc_after,
            trigger=trigger,
            reason=reason,
            market_price=spot_price,
            forecast_price=forecast_price,
        )
        db.session.add(event)
        db.session.commit()

        logger.info(
            "Dispatch %s: %s %.0f MW (%s) SoC %.1f->%.1f%%",
            battery.name, action, power_mw, trigger, soc_before, soc_after,
        )

    return {
        "battery_id": battery.id,
        "battery_name": battery.name,
        "timestamp": timestamp.isoformat(),
        "action": action,
        "power_mw": power_mw,
        "trigger": trigger,
        "reason": reason,
        "soc_before_pct": soc_before,
        "soc_after_pct": soc_after,
        "market_price": spot_price,
        "forecast_price": forecast_price,
    }


def evaluate_region(region: str) -> list[dict]:
    """Run dispatch evaluation for all active batteries in a region."""
    batteries = (
        db.session.query(BatteryAsset)
        .filter(BatteryAsset.region == region)
        .all()
    )
    results = []
    for battery in batteries:
        try:
            result = evaluate(battery, commit=True)
            results.append(result)
        except Exception as exc:
            logger.error("Dispatch failed for %s: %s", battery.name, exc)
    return results
