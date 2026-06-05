"""Demand response engine — curtailment waterfall for controllable loads.

Evaluated after each dispatch cycle (post-dispatch hook). Reads the dispatch
engine's battery state to compose decisions: dispatch handles the battery,
DR handles the loads.
"""

import logging
from datetime import datetime, timezone

from citylab.config import load_config
from citylab.extensions import db
from citylab.models.battery import BatteryAsset
from citylab.models.demand_response import ControllableLoad, DemandResponseEvent
from citylab.models.energy import EnergyDemand, EnergyPrice, GenerationOutput

logger = logging.getLogger(__name__)


def _load_dr_config() -> dict:
    cfg = load_config().get("demand_response", {}) or {}
    return {
        "price_threshold": cfg.get("price_threshold_aud_mwh", 300),
        "recovery_period_min": cfg.get("recovery_period_min", 15),
        "max_simultaneous": cfg.get("max_simultaneous_curtailments", 4),
    }


def _latest_spot_price(region: str) -> float | None:
    row = (
        db.session.query(EnergyPrice)
        .filter(EnergyPrice.region == region)
        .order_by(EnergyPrice.interval_start.desc())
        .first()
    )
    return row.price_aud_mwh if row else None


def _latest_demand(region: str) -> float | None:
    row = (
        db.session.query(EnergyDemand)
        .filter(EnergyDemand.region == region)
        .order_by(EnergyDemand.interval_start.desc())
        .first()
    )
    return row.demand_mw if row else None


def _latest_total_generation(region: str) -> float | None:
    from sqlalchemy import func

    latest_ts = (
        db.session.query(func.max(GenerationOutput.interval_start))
        .filter(GenerationOutput.region == region)
        .scalar()
    )
    if not latest_ts:
        return None

    total = (
        db.session.query(func.sum(GenerationOutput.output_mw))
        .filter(
            GenerationOutput.region == region,
            GenerationOutput.interval_start == latest_ts,
            GenerationOutput.output_mw > 0,
        )
        .scalar()
    )
    return float(total) if total else None


def _available_battery_discharge(region: str) -> float:
    """Total MW of discharge capacity available from batteries in this region."""
    batteries = (
        db.session.query(BatteryAsset)
        .filter(BatteryAsset.region == region)
        .all()
    )
    total = 0.0
    for b in batteries:
        if b.current_soc_pct > b.min_soc_pct and b.status != "charging":
            total += b.max_power_mw
    return total


def _battery_committed(region: str) -> bool:
    """True if all batteries are discharging or holding for contingency."""
    batteries = (
        db.session.query(BatteryAsset)
        .filter(BatteryAsset.region == region)
        .all()
    )
    if not batteries:
        return True
    return all(b.status in ("discharging", "holding") for b in batteries)


def _log_event(
    load: ControllableLoad,
    now: datetime,
    action: str,
    trigger: str,
    reason: str,
    market_price: float | None,
) -> DemandResponseEvent:
    event = DemandResponseEvent(
        load_id=load.id,
        timestamp=now,
        action=action,
        capacity_mw=load.capacity_mw,
        trigger=trigger,
        reason=reason,
        market_price=market_price,
    )
    db.session.add(event)
    return event


def evaluate_region(region: str, commit: bool = True) -> list[dict]:
    """Run DR evaluation for a region. Returns list of decision dicts."""
    cfg = _load_dr_config()
    now = datetime.now(timezone.utc)
    spot_price = _latest_spot_price(region)
    demand = _latest_demand(region)
    generation = _latest_total_generation(region)
    battery_mw = _available_battery_discharge(region)
    battery_committed = _battery_committed(region)

    loads = (
        db.session.query(ControllableLoad)
        .filter(ControllableLoad.region == region)
        .order_by(ControllableLoad.curtailment_cost.asc())
        .all()
    )

    results = []

    supply_deficit = _check_supply_deficit(demand, generation, battery_mw)
    price_spike = _check_price_spike(spot_price, cfg["price_threshold"], battery_committed)

    if supply_deficit is not None or price_spike:
        results.extend(
            _activate_loads(
                loads, now, supply_deficit, price_spike,
                spot_price, cfg, commit,
            )
        )

    results.extend(
        _release_loads(
            loads, now, supply_deficit, price_spike,
            spot_price, cfg, commit,
        )
    )

    results.extend(
        _recover_loads(loads, now, cfg, commit)
    )

    if commit:
        db.session.commit()

    return results


def _check_supply_deficit(
    demand: float | None, generation: float | None, battery_mw: float
) -> float | None:
    """Returns deficit MW if demand exceeds supply + battery, else None."""
    if demand is None or generation is None:
        return None
    surplus = generation + battery_mw - demand
    if surplus < 0:
        return abs(surplus)
    return None


def _check_price_spike(
    spot_price: float | None, threshold: float, battery_committed: bool
) -> bool:
    if spot_price is None:
        return False
    return spot_price > threshold and battery_committed


def _activate_loads(
    loads: list[ControllableLoad],
    now: datetime,
    deficit: float | None,
    price_spike: bool,
    spot_price: float | None,
    cfg: dict,
    commit: bool,
) -> list[dict]:
    results = []
    currently_curtailed = sum(1 for ld in loads if ld.status == "curtailed")
    remaining_deficit = deficit if deficit else 0.0

    for load in loads:
        if load.status != "available":
            continue
        if currently_curtailed >= cfg["max_simultaneous"]:
            break

        should_activate = False
        trigger = ""
        reason = ""

        if deficit is not None and remaining_deficit > 0:
            should_activate = True
            trigger = "supply_deficit"
            reason = (
                f"Supply deficit of {deficit:.0f} MW after battery dispatch "
                f"— curtailing {load.name} ({load.capacity_mw:.0f} MW)"
            )
            remaining_deficit -= load.capacity_mw
        elif price_spike:
            should_activate = True
            trigger = "price_spike"
            reason = (
                f"Price at ${spot_price:.0f}/MWh with battery committed "
                f"— activating {load.name} ({load.capacity_mw:.0f} MW)"
            )

        if should_activate:
            if commit:
                load.status = "curtailed"
                load.curtailed_since = now
                _log_event(load, now, "curtail", trigger, reason, spot_price)
            currently_curtailed += 1
            results.append({
                "load": load.name,
                "action": "curtail",
                "capacity_mw": load.capacity_mw,
                "trigger": trigger,
                "reason": reason,
            })
            logger.info("DR curtail: %s (%s)", load.name, trigger)

    return results


def _release_loads(
    loads: list[ControllableLoad],
    now: datetime,
    deficit: float | None,
    price_spike: bool,
    spot_price: float | None,
    cfg: dict,
    commit: bool,
) -> list[dict]:
    """Release curtailed loads when conditions normalise. Most expensive first."""
    if deficit is not None or price_spike:
        return []

    results = []
    curtailed = [ld for ld in loads if ld.status == "curtailed"]
    curtailed.sort(key=lambda ld: ld.curtailment_cost, reverse=True)

    for load in curtailed:
        if load.curtailed_since:
            elapsed_min = (now - load.curtailed_since).total_seconds() / 60
            if elapsed_min < load.min_duration_min:
                results.append({
                    "load": load.name,
                    "action": "hold",
                    "capacity_mw": load.capacity_mw,
                    "trigger": "min_duration",
                    "reason": (
                        f"Holding {load.name} — {elapsed_min:.0f}/{load.min_duration_min} min "
                        f"minimum duration not met"
                    ),
                })
                if commit:
                    _log_event(
                        load, now, "hold", "min_duration",
                        f"Holding — minimum duration not met ({elapsed_min:.0f}/{load.min_duration_min} min)",
                        spot_price,
                    )
                continue

        reason = f"Conditions normalised — releasing {load.name} ({load.capacity_mw:.0f} MW)"
        if commit:
            load.status = "recovering"
            load.curtailed_since = now
            _log_event(load, now, "release", "normalised", reason, spot_price)

        results.append({
            "load": load.name,
            "action": "release",
            "capacity_mw": load.capacity_mw,
            "trigger": "normalised",
            "reason": reason,
        })
        logger.info("DR release: %s", load.name)

    return results


def _recover_loads(
    loads: list[ControllableLoad],
    now: datetime,
    cfg: dict,
    commit: bool,
) -> list[dict]:
    """Transition recovering loads back to available after recovery period."""
    results = []
    recovery_min = cfg["recovery_period_min"]

    for load in loads:
        if load.status != "recovering":
            continue
        if not load.curtailed_since:
            if commit:
                load.status = "available"
                load.curtailed_since = None
            continue

        elapsed_min = (now - load.curtailed_since).total_seconds() / 60
        if elapsed_min >= recovery_min:
            if commit:
                load.status = "available"
                load.curtailed_since = None
            results.append({
                "load": load.name,
                "action": "recovered",
                "capacity_mw": load.capacity_mw,
                "trigger": "recovery_complete",
                "reason": f"{load.name} recovery complete — available",
            })
            logger.info("DR recovered: %s", load.name)

    return results
