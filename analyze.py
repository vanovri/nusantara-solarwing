"""Reproduce the Natuna September 2025 solar screening used in the paper.

Input: cached NASA POWER hourly GHI, UTC, 4.0 N 108.0 E.
The model is a concept screen, not measured aircraft performance.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "nasa_power_natuna_2025_09_raw.json"
OUT = ROOT / "data" / "natuna_september_2025.json"
WEB = ROOT / "data" / "natuna_september_2025.js"

MASS_KG = 13.8
WING_M2 = 1.82
SPAN_M = 5.2
SPEED_MS = 13.5
RHO = 1.18
CD0 = 0.022
OSWALD = 0.82
DRIVE_EFF = 0.82 * 0.88 * 0.95
PAYLOAD_W = 14.5
PV_AREA_M2 = 1.65
PV_EFF = 0.24
MPPT_EFF = 0.965
PACK_WH = 6 * 12 * 3.6 * 3.45


def cruise_power_w() -> float:
    from math import pi

    aspect = SPAN_M**2 / WING_M2
    lift_coefficient = 2 * MASS_KG * 9.81 / (RHO * SPEED_MS**2 * WING_M2)
    drag_coefficient = CD0 + lift_coefficient**2 / (pi * aspect * OSWALD)
    drag_n = 0.5 * RHO * SPEED_MS**2 * WING_M2 * drag_coefficient
    return drag_n * SPEED_MS / DRIVE_EFF + PAYLOAD_W


def simulate(hours: list[float], start: int = 8, end: int = 16,
             initial_soc: float = 0.9, reserve_soc: float = 0.2,
             load_w: float | None = None) -> dict:
    """Hourly energy screen. Charge/discharge efficiency is an assumption."""
    load_w = cruise_power_w() if load_w is None else load_w
    energy_wh = PACK_WH * initial_soc
    floor_wh = PACK_WH * reserve_soc
    minimum_wh = energy_wh
    trace = []
    for hour in range(start, end):
        ghi = max(0, hours[hour])
        solar_w = ghi * PV_AREA_M2 * PV_EFF * MPPT_EFF
        balance_w = solar_w - load_w
        energy_wh = max(0, min(PACK_WH, energy_wh + balance_w * (0.95 if balance_w >= 0 else 1 / 0.95)))
        minimum_wh = min(minimum_wh, energy_wh)
        trace.append(round(energy_wh / PACK_WH * 100, 2))
    return {
        "minimum_soc_pct": round(minimum_wh / PACK_WH * 100, 2),
        "end_soc_pct": round(energy_wh / PACK_WH * 100, 2),
        "passes_reserve": minimum_wh >= floor_wh,
        "trace_soc_pct": trace,
    }


def main() -> None:
    source = json.loads(RAW.read_text(encoding="utf-8"))
    assert source["parameters"]["ALLSKY_SFC_SW_DWN"]["units"] == "Wh/m^2"
    hourly = source["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    days: dict[str, list[float | None]] = defaultdict(lambda: [None] * 24)
    for stamp, value in hourly.items():
        local = datetime.strptime(stamp, "%Y%m%d%H") + timedelta(hours=7)
        if local.strftime("%Y%m") == "202509":
            days[local.date().isoformat()][local.hour] = value

    if len(days) != 30 or any(len(v) != 24 or any(x is None or x < 0 for x in v) for v in days.values()):
        raise ValueError("NASA POWER data has missing or invalid September hours")

    records = []
    for date, hours in sorted(days.items()):
        total = sum(hours)
        records.append({
            "date": date,
            "ghi_wh_m2": round(total, 2),
            "hours_wh_m2": [round(v, 2) for v in hours],
            "mission": simulate(hours),
        })
    totals = [r["ghi_wh_m2"] for r in records]
    pv_factor = PV_AREA_M2 * PV_EFF * MPPT_EFF
    result = {
        "source_url": "https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude=108.0&latitude=4.0&start=20250831&end=20251001&format=JSON&time-standard=UTC",
        "location": "4.0 N, 108.0 E near Natuna; NASA POWER 1 degree solar grid; UTC shifted +7 h to WIB",
        "period": "2025-09-01 to 2025-09-30 WIB",
        "assumptions": {
            "cruise_load_w": round(cruise_power_w(), 2),
            "pv_area_m2": PV_AREA_M2,
            "pv_efficiency": PV_EFF,
            "mppt_efficiency": MPPT_EFF,
            "pack_nominal_wh": round(PACK_WH, 2),
            "initial_soc_pct": 90,
            "reserve_soc_pct": 20,
            "charge_discharge_efficiency": 0.95,
            "sortie_hours_wib": "08:00-16:00",
        },
        "summary": {
            "days": len(records),
            "daily_ghi_median_wh_m2": round(median(totals), 2),
            "daily_ghi_min_wh_m2": round(min(totals), 2),
            "daily_ghi_max_wh_m2": round(max(totals), 2),
            "modeled_sortie_pass_days": sum(r["mission"]["passes_reserve"] for r in records),
            "median_24h_energy_deficit_wh": round(median(totals) * pv_factor - cruise_power_w() * 24, 2),
        },
        "days": records,
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    WEB.write_text("window.NATUNA_DATA = " + json.dumps(result, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
