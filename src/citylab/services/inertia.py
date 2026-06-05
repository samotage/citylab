"""Grid inertia proxy derivation.

Pure derivation module — no new database tables. Estimates grid inertia from the
generation mix already ingested in ``GenerationOutput``.

The grid carries no frequency sensor we can read, but each fuel type maps to a
known inertia constant H. Synchronous plant (coal, gas, hydro, biomass,
distillate) stores rotational kinetic energy that buffers frequency after a
contingency; inverter-coupled sources (wind, solar, batteries) contribute none.

Two headline metrics per interval:

1. **Synchronous fraction** = ``sync_mw / total_mw`` — a within-VIC relative
   indicator, less sensitive to the MVA-vs-MW proxy caveat because it is a ratio.
2. **E_proxy (MWs)** = ``Σ (sync_output_mw × H)`` — stored-energy estimate that
   feeds the payoff metric.

Payoff — reference-contingency RoCoF::

    E_total = E_proxy + EXTERNAL_INERTIA_MWS
    RoCoF (Hz/s) = (ΔP_ref × system_freq) / (2 × E_total)

VIC is synchronously coupled to the mainland NEM through interconnectors, so the
inertia buffering a VIC contingency is the whole mainland pool, not VIC alone.
``EXTERNAL_INERTIA_MWS`` represents that mainland inertia VIC sees through its
interconnectors. Without it, RoCoF runs 3–5× too hot and every interval reads
"brittle".

**Central caveat — MVA vs MW.** Inertia depends on MVA *spinning*, not MW
*produced*. A coal unit backed off to 40% load still delivers near-full inertia,
but this proxy only sees MW output, so it *understates* inertia whenever
synchronous plant is online but backed off. High-renewable midday periods read
more brittle than reality. This is inherent to the MW-output proxy.
"""

from datetime import datetime

from sqlalchemy import func

from citylab.extensions import db
from citylab.models.energy import GenerationOutput

DEFAULT_REGION = "VIC1"

# --- Inertia constants -----------------------------------------------------
#
# fuel_type -> H (inertia constant, seconds). Inverter-coupled sources (wind,
# solar, batteries) provide no rotational inertia and are omitted — they default
# to 0 via SYNC_H_MAP.get(fuel_type, 0.0), which also covers any unknown fuel.
SYNC_H_MAP: dict[str, float] = {
    "brown_coal": 4.0,
    "black_coal": 4.0,
    "gas_ccgt": 3.0,
    "gas_ocgt": 3.0,
    "gas_recip": 3.0,
    "gas_steam": 3.0,
    "hydro": 3.0,
    "biomass": 3.5,
    "distillate": 2.5,
}

# Mainland NEM inertia (MWs) VIC sees through its interconnectors. Static default
# is sufficient for the hackathon; could be reduced dynamically on an
# interconnector-trip contingency using flow data we already ingest.
EXTERNAL_INERTIA_MWS = 35000.0

SYSTEM_FREQUENCY_HZ = 50.0

# ΔP_ref presets — the largest credible VIC contingency.
REFERENCE_CONTINGENCY_MW = 650.0  # Heywood trip (default)
CONTINGENCY_PRESETS: dict[str, float] = {
    "heywood": 650.0,       # largest interconnector contingency
    "loy_yang_a": 560.0,    # largest single-generator contingency in VIC
}

# State bands (NEM-typical VIC). Sync fraction is the SOLE state driver — it has
# real dynamic range (swings 30–80% across a day) and is the honest "VIC exposure
# within the mainland pool" metric.
#   Comfortable: sync >= 0.50
#   Watch:       sync 0.30–0.50
#   Brittle:     sync < 0.30
SYNC_COMFORTABLE = 0.50
SYNC_WATCH = 0.30

# RoCoF display bands — informational only, NOT a state driver. With
# EXTERNAL_INERTIA_MWS buffering VIC, RoCoF's achievable range is narrow
# (~0.29–0.46 Hz/s for Heywood), so it cannot discriminate state. Calibrated to
# that window: Low < 0.33, Moderate 0.33–0.40, Elevated > 0.40.
ROCOF_LOW = 0.33
ROCOF_MODERATE = 0.40

_STATE_SEVERITY = {"Comfortable": 0, "Watch": 1, "Brittle": 2}

# Inherent proxy limitation, surfaced in API responses so consumers can flag it.
MVA_CAVEAT = (
    "Proxy uses MW output, not MVA spinning. Synchronous plant backed off but "
    "still online is understated, so high-renewable periods read more brittle "
    "than reality."
)


def resolve_contingency(contingency) -> tuple[str, float]:
    """Resolve a contingency selector to ``(label, mw)``.

    Accepts a preset key (``"heywood"``, ``"loy_yang_a"``), a numeric MW value,
    or a numeric string (custom MW). Falls back to the Heywood default.
    """
    if isinstance(contingency, (int, float)) and not isinstance(contingency, bool):
        return "custom", float(contingency)
    if isinstance(contingency, str):
        key = contingency.strip().lower()
        if key in CONTINGENCY_PRESETS:
            return key, CONTINGENCY_PRESETS[key]
        try:
            return "custom", float(key)
        except ValueError:
            pass
    return "heywood", CONTINGENCY_PRESETS["heywood"]


def _sync_band(sync_fraction: float) -> str:
    if sync_fraction >= SYNC_COMFORTABLE:
        return "Comfortable"
    if sync_fraction >= SYNC_WATCH:
        return "Watch"
    return "Brittle"


def rocof_label(rocof_hz_s: float) -> str:
    """Informational RoCoF band — display only, NOT a state driver.

    Calibrated to the narrow achievable window VIC sees through the mainland
    pool: Low < 0.33, Moderate 0.33–0.40, Elevated > 0.40 Hz/s.
    """
    if rocof_hz_s < ROCOF_LOW:
        return "Low"
    if rocof_hz_s <= ROCOF_MODERATE:
        return "Moderate"
    return "Elevated"


def classify_state(sync_fraction: float) -> str:
    """Inertia state from sync fraction alone — the only indicator with real
    dynamic range. RoCoF is buffered too narrow to discriminate state."""
    return _sync_band(sync_fraction)


def compute_inertia(generation_rows, contingency_preset="heywood") -> dict:
    """Derive inertia metrics from a generation mix.

    ``generation_rows`` is a list of ``{"fuel_type", "output_mw"}`` dicts — the
    same shape ``current_snapshot()`` returns in ``generation_mix``. Only
    positive generation counts toward totals (battery charging is load, not
    generation, and is excluded).

    Returns ``{sync_mw, total_mw, sync_fraction, e_proxy_mws, e_total_mws,
    rocof_hz_s, rocof_label, inertia_state, contingency_label, contingency_mw}``.
    """
    contingency_label, contingency_mw = resolve_contingency(contingency_preset)

    sync_mw = 0.0
    total_mw = 0.0
    e_proxy_mws = 0.0
    for row in generation_rows:
        mw = row.get("output_mw")
        if mw is None or mw <= 0:
            continue  # charging / offline — not generation
        total_mw += mw
        h = SYNC_H_MAP.get(row.get("fuel_type"), 0.0)
        if h > 0:
            sync_mw += mw
            e_proxy_mws += mw * h

    sync_fraction = sync_mw / total_mw if total_mw > 0 else 0.0
    e_total_mws = e_proxy_mws + EXTERNAL_INERTIA_MWS
    rocof_hz_s = (contingency_mw * SYSTEM_FREQUENCY_HZ) / (2 * e_total_mws)
    inertia_state = classify_state(sync_fraction)

    return {
        "sync_mw": round(sync_mw, 1),
        "total_mw": round(total_mw, 1),
        "sync_fraction": round(sync_fraction, 4),
        "e_proxy_mws": round(e_proxy_mws, 1),
        "e_total_mws": round(e_total_mws, 1),
        "rocof_hz_s": round(rocof_hz_s, 4),
        "rocof_label": rocof_label(rocof_hz_s),
        "inertia_state": inertia_state,
        "contingency_label": contingency_label,
        "contingency_mw": contingency_mw,
    }


def _trunc_expr(column, interval: str):
    """date_trunc bucketing expression for an interval ('1h'/'1d')."""
    unit = "hour" if interval == "1h" else "day"
    return func.date_trunc(unit, column)


def inertia_timeseries(
    region, dt_from, dt_to, interval: str = "1h", contingency_preset="heywood"
) -> list[dict]:
    """Inertia metrics per interval over a window.

    Queries ``GenerationOutput``, groups by interval, and runs
    ``compute_inertia`` per bucket. Returns ``[{timestamp, sync_mw, total_mw,
    sync_fraction, e_proxy_mws, rocof_hz_s, inertia_state}]`` ordered ascending.
    """
    if interval == "5min":
        time_expr = GenerationOutput.interval_start
    else:
        time_expr = _trunc_expr(GenerationOutput.interval_start, interval)

    rows = (
        db.session.query(
            time_expr.label("b"),
            GenerationOutput.fuel_type,
            func.avg(GenerationOutput.output_mw),
        )
        .filter(
            GenerationOutput.region == region,
            GenerationOutput.interval_start >= dt_from,
            GenerationOutput.interval_start <= dt_to,
        )
        .group_by("b", GenerationOutput.fuel_type)
        .order_by("b")
        .all()
    )

    # bucket timestamp -> list of generation rows
    by_ts: dict[str, list[dict]] = {}
    order: list[str] = []
    for ts, fuel_type, val in rows:
        if val is None:
            continue
        ts_iso = ts.isoformat()
        if ts_iso not in by_ts:
            by_ts[ts_iso] = []
            order.append(ts_iso)
        by_ts[ts_iso].append({"fuel_type": fuel_type, "output_mw": float(val)})

    order.sort()
    series = []
    for ts_iso in order:
        m = compute_inertia(by_ts[ts_iso], contingency_preset)
        series.append(
            {
                "timestamp": ts_iso,
                "sync_mw": m["sync_mw"],
                "total_mw": m["total_mw"],
                "sync_fraction": m["sync_fraction"],
                "e_proxy_mws": m["e_proxy_mws"],
                "rocof_hz_s": m["rocof_hz_s"],
                "inertia_state": m["inertia_state"],
            }
        )
    return series


def current_inertia(region: str = DEFAULT_REGION, contingency_preset="heywood") -> dict:
    """Latest-interval inertia snapshot for a region.

    Returns the ``compute_inertia`` dict plus ``region`` and ``as_of``. Empty
    (zeroed) snapshot if no generation data exists.
    """
    latest_interval = (
        db.session.query(func.max(GenerationOutput.interval_start))
        .filter(GenerationOutput.region == region)
        .scalar()
    )
    if not latest_interval:
        snapshot = compute_inertia([], contingency_preset)
        snapshot["region"] = region
        snapshot["as_of"] = None
        return snapshot

    gen_rows = (
        db.session.query(GenerationOutput.fuel_type, GenerationOutput.output_mw)
        .filter(
            GenerationOutput.region == region,
            GenerationOutput.interval_start == latest_interval,
        )
        .all()
    )
    generation_rows = [{"fuel_type": ft, "output_mw": mw} for ft, mw in gen_rows]
    snapshot = compute_inertia(generation_rows, contingency_preset)
    snapshot["region"] = region
    snapshot["as_of"] = (
        latest_interval.isoformat()
        if isinstance(latest_interval, datetime)
        else str(latest_interval)
    )
    return snapshot
