"""Command-line facility screening.

Example (Gabal El-Asfar design state):
    python scripts/screen_facility.py --olr 1.0 --nh4 50 --alk 1800 --reactor 82500
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from whydt import parameters as P  # noqa: E402
from whydt import lca, process, surrogate, tea  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="W-HyDT pre-feasibility screening")
    ap.add_argument("--olr", type=float, default=P.REF_INPUTS["OLR"], help="kg COD m-3 d-1")
    ap.add_argument("--nh4", type=float, default=P.REF_INPUTS["NH4"], help="mg L-1")
    ap.add_argument("--alk", type=float, default=P.REF_INPUTS["ALK"], help="mg CaCO3 L-1")
    ap.add_argument("--temperature", type=float, default=None, help="deg C")
    ap.add_argument("--flow", type=float, default=P.REF_INFLUENT_M3D, help="influent m3 d-1")
    ap.add_argument("--reactor", type=float, default=P.REF_REACTOR_M3, help="DF reactor volume m3")
    ap.add_argument("--diesel", type=float, default=P.DIESEL_PRICE_REF, help="diesel price US$ L-1")
    a = ap.parse_args()

    dom = surrogate.check_domain(a.olr, a.nh4, a.alk, a.temperature, a.flow)
    r = process.screen(a.olr, a.nh4, a.alk, a.reactor)
    e = r.energy
    ci = lca.facility_carbon_intensity(e.h2_kg_d, a.reactor / P.REF_REACTOR_M3)
    cost = tea.screening_lcoh(e.h2_kg_yr, a.reactor, a.diesel)

    print("Domain:", "within the surrogate domain" if dom.in_domain else "HIGH-VARIANCE DOMAIN")
    for f in dom.flags:
        print("  flag:", f)
    for x in dom.advisories:
        print("  note:", x)
    print(f"eta_DF (anchored)           {r.eta_df:8.3f}   (relative response {r.relative_response:.3f})")
    print(f"H2 output                   {e.h2_m3d:10,.0f} m3 d-1  ({e.h2_kg_d:,.0f} kg d-1; "
          f"DF {r.h2_df_m3d:,.0f}, PF {r.h2_pf_m3d:,.0f})")
    print(f"Gross chemical energy (LHV) {e.gross_mwh_d:8.1f} MWh d-1")
    print(f"Fuel-cell electricity       {e.fc_mwh_d:8.1f} MWh d-1")
    print(f"Net usable electricity      {e.net_mwh_d:8.1f} MWh d-1  (leverage ratio {e.leverage_ratio:.1f})")
    print(f"Avoided fossil fuel         {e.h2_kg_d * lca.fossil_credit():10,.0f} kg CO2-eq d-1")
    print(f"Annual net mitigation       {-ci * e.h2_kg_yr / 1000:10,.0f} t CO2-eq yr-1  (at {ci:.2f} kg kg-1)")
    print(f"LCOH, gross / net-effective {cost['gross']:8.2f} / {cost['net']:.2f} US$ kg-1 "
          "(GEA cost structure scaled with reactor volume)")


if __name__ == "__main__":
    main()
