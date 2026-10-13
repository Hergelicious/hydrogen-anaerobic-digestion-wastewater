"""Generate the Gabal El-Asfar case-study outputs (Supplementary Tables 33 and 33b).

    python scripts/generate_case_study.py [--out case_study.json] [--rows case_study_rows.csv]

Pilot-anchored Monte Carlo (n = 500, seed 42; whydt.case_study). The optional CSV holds the
500 rows (eta_DF, eta_PF, NH4, SO4, PAR, temperature and the stage outputs).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from whydt import case_study as cs  # noqa: E402
from whydt import process  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--rows", default=None)
    a = ap.parse_args()
    res = {"case": cs.run().as_dict(), "eta_pilot": cs.ETA_PILOT,
           "alternative_reading_eta": cs.alternative_reading_eta(),
           "attainment": process.gea_attainment(), "pf_feed": cs.pf_feed_check()}
    txt = json.dumps(res, indent=2)
    print(txt)
    if a.out:
        with open(a.out, "w") as f:
            f.write(txt + "\n")
    if a.rows:
        import pandas as pd
        s = cs.simulate()
        pd.DataFrame({"eta_DF": s["eta_df"], "eta_PF": s["eta_pf"], "NH4_mg_L": s["nh4"],
                      "SO4_mg_L": s["so4"], "PAR_umol_m2_s": s["par"], "T_degC": s["temp"],
                      "H2_DF_m3_d": s["h2_df"], "H2_PF_m3_d": s["h2_pf"],
                      "H2_total_m3_d": s["h2"]}).to_csv(a.rows, index=False, float_format="%.6g")
    return 0


if __name__ == "__main__":
    sys.exit(main())
