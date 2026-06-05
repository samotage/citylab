"""Scenario analysis engine — 'what if' modelling over live NEM data.

Two scenario types:
  1. Interconnector failure — zero out a link, recompute supply balance
  2. Generation loss — remove N MW of a fuel type from a region

Uses a static merit-order fuel-cost ladder for price estimation.
No new DB tables — computes on the fly from stored actuals.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from citylab.extensions import db
from citylab.models.energy import (
    EnergyDemand,
    EnergyPrice,
    GenerationOutput,
    InterconnectorFlow,
)
from citylab.services.ingestion.opennem import INTERCONNECTORS, NEM_REGIONS

# Static merit-order fuel-cost ladder ($/MWh marginal cost).
# Directionally correct for the NEM — not bid-stack accurate.
MERIT_ORDER = [
    ("wind", 0),
    ("solar_utility", 0),
    ("solar_rooftop", 0),
    ("brown_coal", 25),
    ("black_coal", 40),
    ("hydro", 50),
    ("biomass", 60),
    ("gas_ccgt", 70),
    ("battery_discharging", 90),
    ("gas_ocgt", 120),
    ("gas_recip", 130),
    ("gas_steam", 140),
    ("distillate", 200),
]

FUEL_COST = {fuel: cost for fuel, cost in MERIT_ORDER}


class ScenarioEngine:
    """Run hypothetical scenarios against stored NEM actuals."""

    def run(self, scenario: dict) -> dict:
        """Execute a scenario and return projected impacts.

        scenario = {
            "type": "interconnector_failure" | "generation_loss",
            "params": { ... },
            "time_window_minutes": 60  (optional, default 60)
        }

        Returns {ok, scenario_type, baseline, projected, impacts}.
        """
        stype = scenario.get("type")
        params = scenario.get("params", {})
        window = int(scenario.get("time_window_minutes", 60))

        if stype == "interconnector_failure":
            return self._interconnector_failure(params, window)
        elif stype == "generation_loss":
            return self._generation_loss(params, window)
        else:
            return {"ok": False, "error": f"Unknown scenario type: {stype}"}

    def _get_baseline(self, window_minutes: int) -> dict:
        """Snapshot the most recent NEM state across all regions."""
        now = datetime.now(timezone.utc)
        since = now - timedelta(minutes=window_minutes)

        generation = {}
        for region in NEM_REGIONS:
            latest_ts = (
                db.session.query(func.max(GenerationOutput.interval_start))
                .filter(
                    GenerationOutput.region == region,
                    GenerationOutput.interval_start >= since,
                )
                .scalar()
            )
            if not latest_ts:
                continue
            rows = (
                db.session.query(GenerationOutput)
                .filter(
                    GenerationOutput.region == region,
                    GenerationOutput.interval_start == latest_ts,
                )
                .all()
            )
            generation[region] = {
                r.fuel_type: r.output_mw for r in rows if r.output_mw
            }

        demand = {}
        for region in NEM_REGIONS:
            row = (
                db.session.query(EnergyDemand)
                .filter(
                    EnergyDemand.region == region,
                    EnergyDemand.interval_start >= since,
                )
                .order_by(EnergyDemand.interval_start.desc())
                .first()
            )
            if row:
                demand[region] = row.demand_mw

        prices = {}
        for region in NEM_REGIONS:
            row = (
                db.session.query(EnergyPrice)
                .filter(
                    EnergyPrice.region == region,
                    EnergyPrice.interval_start >= since,
                )
                .order_by(EnergyPrice.interval_start.desc())
                .first()
            )
            if row:
                prices[region] = row.price_aud_mwh

        latest_ic_ts = (
            db.session.query(func.max(InterconnectorFlow.interval_start))
            .filter(InterconnectorFlow.interval_start >= since)
            .scalar()
        )
        flows = {}
        if latest_ic_ts:
            ic_rows = (
                db.session.query(InterconnectorFlow)
                .filter(InterconnectorFlow.interval_start == latest_ic_ts)
                .all()
            )
            for r in ic_rows:
                flows[r.interconnector_id] = {
                    "interconnector_id": r.interconnector_id,
                    "from_region": r.from_region,
                    "to_region": r.to_region,
                    "flow_mw": r.flow_mw,
                    "capacity_mw": r.capacity_mw,
                }

        return {
            "generation": generation,
            "demand": demand,
            "prices": prices,
            "flows": flows,
        }

    @staticmethod
    def _total_supply(gen_mix: dict) -> float:
        return sum(v for v in gen_mix.values() if v > 0)

    @staticmethod
    def _estimate_price(
        gen_mix: dict, demand_mw: float, net_import_mw: float,
        baseline_price: float,
    ) -> float:
        """Estimate spot price using merit-order floor + scarcity multiplier.

        Pure merit-order understates impact because the baseline synthetic price
        already includes scarcity/demand effects. This model uses supply
        utilisation to scale the baseline, floored by the marginal fuel cost.
        """
        if gen_mix.get("unserved_energy", 0) > 0:
            return 16600.0

        supply = sum(v for v in gen_mix.values() if v > 0) + net_import_mw
        if supply <= 0:
            return 16600.0

        active = [
            (fuel, mw) for fuel, mw in gen_mix.items()
            if mw > 0 and fuel in FUEL_COST
        ]
        if active:
            active.sort(key=lambda x: FUEL_COST.get(x[0], 999), reverse=True)
            marginal = float(FUEL_COST.get(active[0][0], 300))
        else:
            marginal = 300.0

        utilisation = demand_mw / supply if supply > 0 else 2.0
        if utilisation > 1.0:
            price = baseline_price * (utilisation ** 3)
        elif utilisation > 0.85:
            scarcity = (utilisation - 0.85) / 0.15
            price = baseline_price * (1 + scarcity * 2)
        else:
            price = baseline_price

        return max(price, marginal)

    @staticmethod
    def _net_import(flows: dict, region: str) -> float:
        """Net MW flowing into a region across all interconnectors."""
        net = 0.0
        for ic in flows.values():
            if ic["to_region"] == region:
                net += ic["flow_mw"]
            elif ic["from_region"] == region:
                net -= ic["flow_mw"]
        return net

    def _interconnector_failure(self, params: dict, window: int) -> dict:
        ic_id = params.get("interconnector_id")
        reduced_capacity = float(params.get("reduced_capacity_mw", 0))

        ic_def = None
        for ic in INTERCONNECTORS:
            if ic["id"] == ic_id or ic["name"].lower() == str(ic_id).lower():
                ic_def = ic
                break
        if not ic_def:
            return {"ok": False, "error": f"Unknown interconnector: {ic_id}"}

        baseline = self._get_baseline(window)
        if not baseline["generation"]:
            return {"ok": False, "error": "No baseline data available"}

        projected_flows = {}
        for fid, fdata in baseline["flows"].items():
            projected_flows[fid] = dict(fdata)

        original_flow = 0.0
        if ic_def["id"] in projected_flows:
            original_flow = projected_flows[ic_def["id"]]["flow_mw"]
            if reduced_capacity == 0:
                projected_flows[ic_def["id"]]["flow_mw"] = 0.0
            else:
                capped = max(-reduced_capacity, min(reduced_capacity, original_flow))
                projected_flows[ic_def["id"]]["flow_mw"] = capped

        affected_regions = {ic_def["from"], ic_def["to"]}
        projected_prices = dict(baseline["prices"])
        projected_supply = {}
        projected_deficit = {}

        for region in NEM_REGIONS:
            gen_mix = dict(baseline["generation"].get(region, {}))
            demand_mw = baseline["demand"].get(region, 0)
            supply = self._total_supply(gen_mix)
            net_import = self._net_import(projected_flows, region)
            balance = supply + net_import - demand_mw

            projected_supply[region] = round(supply + net_import, 1)
            projected_deficit[region] = round(balance, 1)

            if region in affected_regions:
                base_price = baseline["prices"].get(region, 0)
                if balance < 0:
                    gen_mix_with_ramp = self._ramp_up(gen_mix, abs(balance))
                    projected_prices[region] = round(
                        self._estimate_price(
                            gen_mix_with_ramp, demand_mw, net_import, base_price
                        ), 2
                    )
                else:
                    projected_prices[region] = round(
                        self._estimate_price(
                            gen_mix, demand_mw, net_import, base_price
                        ), 2
                    )

        return {
            "ok": True,
            "scenario_type": "interconnector_failure",
            "interconnector": {
                "id": ic_def["id"],
                "name": ic_def["name"],
                "from": ic_def["from"],
                "to": ic_def["to"],
                "original_flow_mw": round(original_flow, 1),
                "reduced_capacity_mw": reduced_capacity,
            },
            "baseline": {
                "prices": baseline["prices"],
                "demand": baseline["demand"],
            },
            "projected": {
                "prices": projected_prices,
                "supply_mw": projected_supply,
                "surplus_deficit_mw": projected_deficit,
                "flows": {
                    k: {"flow_mw": round(v["flow_mw"], 1)}
                    for k, v in projected_flows.items()
                },
            },
            "impacts": self._price_impacts(baseline["prices"], projected_prices),
        }

    def _generation_loss(self, params: dict, window: int) -> dict:
        region = params.get("region", "VIC1")
        fuel_type = params.get("fuel_type")
        loss_mw = float(params.get("loss_mw", 0))

        if region not in NEM_REGIONS:
            return {"ok": False, "error": f"Unknown region: {region}"}
        if not fuel_type:
            return {"ok": False, "error": "fuel_type is required"}
        if loss_mw <= 0:
            return {"ok": False, "error": "loss_mw must be positive"}

        baseline = self._get_baseline(window)
        if not baseline["generation"]:
            return {"ok": False, "error": "No baseline data available"}

        gen_mix = dict(baseline["generation"].get(region, {}))
        current_output = gen_mix.get(fuel_type, 0)
        actual_loss = min(loss_mw, max(current_output, 0))
        gen_mix[fuel_type] = max(0, current_output - actual_loss)

        demand_mw = baseline["demand"].get(region, 0)
        supply = self._total_supply(gen_mix)
        net_import = self._net_import(baseline["flows"], region)
        deficit = demand_mw - supply - net_import

        projected_prices = dict(baseline["prices"])
        base_price = baseline["prices"].get(region, 0)
        if deficit > 0:
            ramped = self._ramp_up(gen_mix, deficit)
            projected_prices[region] = round(
                self._estimate_price(ramped, demand_mw, net_import, base_price), 2
            )
        else:
            projected_prices[region] = round(
                self._estimate_price(gen_mix, demand_mw, net_import, base_price), 2
            )

        return {
            "ok": True,
            "scenario_type": "generation_loss",
            "params": {
                "region": region,
                "fuel_type": fuel_type,
                "requested_loss_mw": loss_mw,
                "actual_loss_mw": round(actual_loss, 1),
                "remaining_output_mw": round(gen_mix[fuel_type], 1),
            },
            "baseline": {
                "prices": baseline["prices"],
                "demand": baseline["demand"],
                "generation_mw": {
                    region: baseline["generation"].get(region, {})
                },
            },
            "projected": {
                "prices": projected_prices,
                "supply_mw": round(supply, 1),
                "net_import_mw": round(net_import, 1),
                "deficit_mw": round(max(deficit, 0), 1),
                "modified_generation_mw": {
                    k: round(v, 1) for k, v in gen_mix.items() if v != 0
                },
            },
            "impacts": self._price_impacts(baseline["prices"], projected_prices),
        }

    _NON_DISPATCHABLE = {"wind", "solar_utility", "solar_rooftop"}

    @classmethod
    def _ramp_up(cls, gen_mix: dict, needed_mw: float) -> dict:
        """Simulate ramping up dispatchable generation to fill a deficit."""
        result = dict(gen_mix)
        remaining = needed_mw
        for fuel, _cost in MERIT_ORDER:
            if remaining <= 0:
                break
            if fuel in cls._NON_DISPATCHABLE:
                continue
            current = result.get(fuel, 0)
            if current <= 0:
                headroom = 500.0
            else:
                headroom = current * 0.3
            ramp = min(remaining, headroom)
            result[fuel] = current + ramp
            remaining -= ramp
        if remaining > 0:
            result["unserved_energy"] = round(remaining, 1)
        return result

    @staticmethod
    def _price_impacts(baseline_prices: dict, projected_prices: dict) -> dict:
        impacts = {}
        for region in set(baseline_prices) | set(projected_prices):
            base = baseline_prices.get(region, 0)
            proj = projected_prices.get(region, 0)
            change = proj - base
            pct = (change / base * 100) if base else 0
            impacts[region] = {
                "baseline_price": round(base, 2),
                "projected_price": round(proj, 2),
                "change_aud_mwh": round(change, 2),
                "change_pct": round(pct, 1),
            }
        return impacts
