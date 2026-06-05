"""One-time backfill of REAL measured solar irradiance from the ICU OneTouch
SolarCam (admin stream 1108) into CityLab's solar_forecasts table.

Source: scraped from https://onetouch.icusolarcam.com/admin/streams/1108/data
        (the page renders the full 30-min series in the DOM; captured to
        data/icu_stream_1108_irradiance.json).

Unlike the Solcast fetcher's fetch_range — which *synthesises* a plausible
series — this loads the actual sensor GHI readings. Each reading becomes a
SolarForecast "actual" (issued_at == forecast_for, period "30min") attached to
the Melbourne Metro (rooftop PV) location, matching the established historical
record shape. ghi_wm2 is the measured value; estimated_pv_output_kw is a
deterministic linear estimate from the location's reference PV capacity; the
unmeasured fields (dni/dhi/cloud/air_temp) are left NULL.

Idempotent: re-running upserts on the natural key
(location_id, issued_at, forecast_for, forecast_period), so real readings
overwrite any synthetic actuals in the overlapping window.

Usage:
    PYTHONPATH=src python3 scripts/backfill_icu_irradiance.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "icu_stream_1108_irradiance.json"
LOCATION_NAME = "Melbourne Metro"  # ilike match -> "Melbourne Metro (rooftop PV)"
PERIOD = "30min"


def _parse_row(row: dict):
    """('2026-06-12 08:30:00 +1000', '48.0') -> (aware datetime, float ghi)."""
    dt = datetime.strptime(row["date"].strip(), "%Y-%m-%d %H:%M:%S %z")
    raw = (row.get("value") or "").strip()
    if raw == "":
        return None
    return dt, float(raw)


def main() -> int:
    from citylab import create_app
    from citylab.extensions import db
    from citylab.models.solar import SolarForecast, SolarLocation
    from citylab.services.ingestion.upsert import upsert_records

    payload = json.loads(DATA_FILE.read_text())
    rows_in = payload["rows"]

    app = create_app()
    with app.app_context():
        loc = (
            db.session.query(SolarLocation)
            .filter(SolarLocation.name.ilike(f"%{LOCATION_NAME}%"))
            .order_by(SolarLocation.id)
            .first()
        )
        if loc is None:
            print(f"ERROR: no SolarLocation matching '{LOCATION_NAME}'")
            return 1
        cap = loc.reference_pv_capacity_kw or 0.0
        print(f"Target location: #{loc.id} {loc.name} (cap {cap:.0f} kW)")

        records = []
        skipped = 0
        for r in rows_in:
            parsed = _parse_row(r)
            if parsed is None:
                skipped += 1
                continue
            ts, ghi = parsed
            pv = round(cap * (ghi / 1000.0), 1) if cap else None
            records.append(
                {
                    "location_id": loc.id,
                    "issued_at": ts,
                    "forecast_for": ts,
                    "forecast_period": PERIOD,
                    "ghi_wm2": ghi,
                    "dni_wm2": None,
                    "dhi_wm2": None,
                    "cloud_opacity_pct": None,
                    "air_temp_c": None,
                    "estimated_pv_output_kw": pv,
                }
            )

        # Dedupe on the natural key (keep last) in case the source repeats a ts.
        by_key = {}
        for rec in records:
            by_key[(rec["location_id"], rec["issued_at"], rec["forecast_for"],
                    rec["forecast_period"])] = rec
        deduped = list(by_key.values())

        conflict = ["location_id", "issued_at", "forecast_for", "forecast_period"]
        n = upsert_records(SolarForecast, deduped, conflict)
        db.session.commit()

        ts_list = sorted(rec["forecast_for"] for rec in deduped)
        print(
            f"Upserted {n} measured-irradiance rows "
            f"({len(rows_in)} read, {skipped} blank, "
            f"{len(records) - len(deduped)} dup-collapsed)."
        )
        if ts_list:
            print(f"Span: {ts_list[0]} -> {ts_list[-1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
