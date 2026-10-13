"""Rebuild the list of large plants used in the facility-resolved analysis from HydroWASTE.

    python scripts/build_plant_list.py path/to/HydroWASTE_v10.csv

HydroWASTE v1.0 (Ehalt Macedo et al., Earth Syst. Sci. Data 14, 559-577, 2022; CC BY 4.0) is
downloaded from https://www.hydrosheds.org/products/hydrowaste. Selection (Methods): treated
wastewater discharge (WASTE_DIS) of at least 100,000 m3 d-1, at any latitude. Each plant is flagged
by World Bank income group (high-income economies are excluded from the low- and middle-income set)
and by whether it lies within +/-35 degrees latitude (used only in a sensitivity analysis).
Writes data/hydrowaste_large_plants.csv.
"""
from __future__ import annotations

import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from whydt import parameters as P  # noqa: E402

FLOW_BASIS = {1: "reported as treated", 2: "reported as design capacity",
              3: "reported, type not identified", 4: "estimated"}


def build(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="latin-1")
    sel = df[df["WASTE_DIS"] >= P.PLANT_MIN_FLOW_M3D].copy()
    out = pd.DataFrame({
        "waste_id": sel["WASTE_ID"], "country": sel["COUNTRY"], "iso": sel["CNTRY_ISO"],
        "lat": sel["LAT_WWTP"], "lon": sel["LON_WWTP"], "flow_m3d": sel["WASTE_DIS"].round(0),
        "flow_basis": sel["QUAL_WASTE"].map(FLOW_BASIS), "treatment_level": sel["LEVEL"],
        "status": sel["STATUS"], "population_served": sel["POP_SERVED"],
    })
    out["high_income"] = out["iso"].isin(P.HIGH_INCOME_ISO)
    out["within_35deg"] = out["lat"].abs() <= P.LATITUDE_SENSITIVITY_DEG
    return out.sort_values(["high_income", "iso", "flow_m3d"], ascending=[True, True, False])


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 1
    out = build(argv[1])
    dest = os.path.join(ROOT, "data", "hydrowaste_large_plants.csv")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    out.to_csv(dest, index=False)
    gs = out[~out["high_income"]]
    print(f"{len(out)} plants >= 100,000 m3 d-1 ({out['flow_m3d'].sum() / 1e6:.1f} Mm3 d-1); "
          f"{len(gs)} outside high-income economies ({gs['flow_m3d'].sum() / 1e6:.1f} Mm3 d-1) -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
