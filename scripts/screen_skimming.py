"""Command-line comparison of hydrogen skimming ahead of digestion with digestion alone.

Example (Gabal El-Asfar, higher reading, Egypt 2025-26 inputs):
    python scripts/screen_skimming.py --flow 503500 --cod 278 --reading pilot --grid 0.563 --diesel 0.39
A measured yield (mL H2 per g COD fed) can be given instead of a reading with --yield-ml.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from whydt import parameters as P  # noqa: E402
from whydt import allocation  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="W-HyDT: hydrogen skimming against digestion alone")
    ap.add_argument("--flow", type=float, required=True, help="influent flow, m3 d-1")
    ap.add_argument("--cod", type=float, default=278.0, help="influent COD, mg L-1")
    ap.add_argument("--reading", choices=["pilot", "literature"], default="pilot", help="reading of the pilot yield: pilot = higher (163 mL g-1 COD), literature = lower (23)")
    ap.add_argument("--yield-ml", type=float, default=None, help="measured yield, mL H2 per g COD fed (overrides --reading)")
    ap.add_argument("--no-digesters", action="store_true", help="the plant does not digest its sludge")
    ap.add_argument("--grid", type=float, default=P.COUNTRY_INPUTS["EGY"][1], help="kg CO2-eq kWh-1")
    ap.add_argument("--diesel", type=float, default=P.COUNTRY_INPUTS["EGY"][2], help="US$ L-1")
    ap.add_argument("--electricity", type=float, default=P.ELECTRICITY_PRICE, help="US$ kWh-1")
    a = ap.parse_args()

    eta = (a.yield_ml / 1000.0 / (0.042 / P.H2_DENSITY)) if a.yield_ml else allocation.eta_scenarios()[a.reading]
    if eta > 1.0:
        raise SystemExit("yield exceeds the Thauer limit (467 mL H2 per g COD)")
    kw = dict(eta=eta, captured_cod_kg_d=P.CAPTURE * a.flow * a.cod / 1000.0, digesting=not a.no_digesters,
              grid_ef=a.grid, diesel_price=a.diesel, elec_price=a.electricity)
    bus = allocation.configuration("C1", "bus", **kw)
    fc = allocation.configuration("C1", "fc", **kw)
    t65, t70 = allocation.threshold_kg(0.65), allocation.threshold_kg(0.70)
    rows = [
        ("Fermentative yield (fraction of Thauer)", f"{eta:.3f}"),
        ("Captured COD (kg d-1)", f"{kw['captured_cod_kg_d']:,.0f}"),
        ("Hydrogen (kg d-1)", f"{bus.h2_kg_d:,.0f}"),
        ("COD diverted from digesters (kg d-1)", f"{bus.cod_diverted_kg_d:,.0f}"),
        ("CHP electricity forgone (MWh d-1)", f"{bus.chp_forgone_mwh_d:,.1f}"),
        ("Net electricity, hydrogen in fuel cells (MWh d-1)", f"{fc.net_electricity_mwh_d:+,.1f}"),
        ("Diesel displaced in buses (L d-1)", f"{bus.diesel_l_d:,.0f}"),
        ("Emissions change, buses (t CO2-eq yr-1)", f"{bus.co2_t_yr:+,.0f}"),
        ("Attributional intensity (kg CO2-eq kg-1 H2)", f"{bus.ci_attributional:.2f}"),
        ("Consequential intensity (kg CO2-eq kg-1 H2)", f"{bus.ci_consequential:.2f}  (thresholds {t65:.2f} / {t70:.2f})"),
        ("Net value before capital, buses (US$ yr-1)", f"{bus.value_usd_yr:,.0f}"),
        ("Net value before capital, fuel cells (US$ yr-1)", f"{fc.value_usd_yr:,.0f}"),
        ("Capital the net value could service (US$)", f"{max(bus.allowable_capex_usd, 0.0):,.0f}"),
    ]
    # screening rule (Fig. 6): break-even prices do not depend on plant size; the grid and yield limits are for the
    # consequential intensity with bus use against the 70% saving threshold
    base = {k: v for k, v in kw.items() if k not in ("eta", "digesting", "grid_ef")}
    cross = allocation.grid_crossover(eta=eta, threshold=t70, digesting=kw["digesting"], **base)
    eta_min = allocation.min_yield_for_threshold(threshold=t70, grid_ef=a.grid, digesting=kw["digesting"], **base)
    ml_per_eta = 0.042 / P.H2_DENSITY * 1000.0
    rows += [
        ("Break-even diesel price, buses (US$ L-1)",
         f"{allocation.break_even_diesel_price(eta=eta, digesting=kw['digesting'], grid_ef=a.grid, **base):.2f}"),
        ("Break-even hydrogen sales price (US$ kg-1)",
         f"{allocation.break_even_h2_price(eta=eta, digesting=kw['digesting'], grid_ef=a.grid, **base):.2f}"),
        ("Grid intensity meeting the 70% saving (kg CO2-eq kWh-1)",
         f"below {cross:.2f}" if cross > 0 else "not met on any grid"),
        ("Yield meeting the 70% saving on this grid (mL H2 g-1 COD)",
         f"at least {eta_min * ml_per_eta:.0f}" if eta_min == eta_min else "not met at any yield"),
    ]
    w = max(len(k) for k, _ in rows)
    for k, v in rows:
        print(f"{k:<{w}}  {v}")


if __name__ == "__main__":
    main()
