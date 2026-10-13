"""Facility-resolved analysis of large Global South plants (Supplementary Note S22).

Plants: HydroWASTE v1.0 plants treating at least 100,000 m3 d-1, outside high-income economies
(data/hydrowaste_large_plants.csv; scripts/build_plant_list.py). Restricting them to within +/-35
degrees latitude is available as a sensitivity (load_plants(max_abs_lat=35)).
Influent COD is not reported per plant, so two strengths bound it (278 mg L-1, the Gabal El-Asfar
value, and 600 mg L-1). Captured COD = 0.59 x flow x COD. Hydrogen skimming ahead of digestion
(configuration C1, whydt.allocation) is evaluated at each plant with its country's 2025 grid
carbon intensity and retail diesel price, under both readings of the pilot yield and two
bounding assumptions on digestion (all plants digest their sludge / none do).
"""
from __future__ import annotations

import os
from dataclasses import asdict

import numpy as np
import pandas as pd

from . import parameters as P
from .allocation import configuration, eta_scenarios

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANT_FILE = os.path.join(ROOT, "data", "hydrowaste_large_plants.csv")
COD_BOUNDS_MG_L = P.INFLUENT_COD_RANGE_MG_L          # (278, 600)


def load_plants(path: str = PLANT_FILE, global_south: bool = True, max_abs_lat: float | None = None) -> pd.DataFrame:
    df = pd.read_csv(path)
    if max_abs_lat is not None:
        df = df[df["lat"].abs() <= max_abs_lat]
    return df[~df["high_income"]].copy() if global_south else df.copy()


def captured_cod_kg_d(flow_m3d, cod_mg_l):
    return P.CAPTURE * np.asarray(flow_m3d) * cod_mg_l / 1000.0


def evaluate(df: pd.DataFrame | None = None, eta: float | None = None, cod_mg_l: float = 278.0,
             digesting: bool = True, end_use: str = "bus", **kw) -> pd.DataFrame:
    """One row per plant with hydrogen, diesel displaced, carbon and value of skimming."""
    df = load_plants() if df is None else df
    rows = []
    for r in df.itertuples(index=False):
        ef, price = P.COUNTRY_INPUTS[r.iso][1], P.COUNTRY_INPUTS[r.iso][2]
        cod = float(captured_cod_kg_d(r.flow_m3d, cod_mg_l))
        c = configuration("C1", end_use, eta=eta, captured_cod_kg_d=cod, digesting=digesting,
                          **dict(kw, grid_ef=kw.get("grid_ef", ef), diesel_price=kw.get("diesel_price", price)))
        d = asdict(c)
        d.update(waste_id=r.waste_id, iso=r.iso, country=r.country, lat=r.lat, lon=r.lon,
                 flow_m3d=r.flow_m3d, captured_cod_kg_d=cod, grid_ef=ef, diesel_price=price)
        rows.append(d)
    return pd.DataFrame(rows)


def summary(df: pd.DataFrame | None = None) -> dict:
    """Totals for both yield readings, both COD strengths and both digestion bounds."""
    df = load_plants() if df is None else df
    out = {"n_plants": int(len(df)), "flow_Mm3d": float(df["flow_m3d"].sum() / 1e6),
           "flow_km3_yr": float(df["flow_m3d"].sum() * P.DAYS_PER_YEAR / 1e9),
           "n_estimated_flow": int((df["flow_basis"] == "estimated").sum()),
           "by_country": df.groupby("iso")["flow_m3d"].agg(["size", "sum"]).rename(
               columns={"size": "n", "sum": "flow_m3d"}).sort_values("n", ascending=False).to_dict("index")}
    for reading, eta in eta_scenarios().items():
        for cod in COD_BOUNDS_MG_L:
            for dig in (True, False):
                e = evaluate(df, eta=eta, cod_mg_l=cod, digesting=dig)
                lo = evaluate(df, eta=eta, cod_mg_l=cod, digesting=dig,
                              skim_lca_mwh_d=P.PARASITIC_REF_MWH_D, embodied_t=0.0)
                key = f"{reading}_{int(cod)}_{'digesting' if dig else 'nondigesting'}"
                pos = e["value_usd_yr"] > 0
                out[key] = {
                    "h2_kt_yr": float(e["h2_kg_d"].sum() * P.DAYS_PER_YEAR / 1e6),
                    "diesel_ML_yr": float(e["diesel_l_d"].sum() * P.DAYS_PER_YEAR / 1e6),
                    "co2_kt_yr": float(e["co2_t_yr"].sum() / 1e3),
                    "co2_kt_yr_low_burden": float(lo["co2_t_yr"].sum() / 1e3),
                    "value_MUSD_yr": float(e["value_usd_yr"].sum() / 1e6),
                    "n_positive_value": int(pos.sum()),
                    "h2_share_positive": float(e.loc[pos, "h2_kg_d"].sum() / e["h2_kg_d"].sum()),
                    "allowable_capex_MUSD_positive": float(e.loc[pos, "allowable_capex_usd"].sum() / 1e6),
                    "n_allowable_ge_10M": int((e["allowable_capex_usd"] >= 10e6).sum()),
                    "n_ci_cons_below_threshold": int((e["ci_consequential"] <= P.LOW_CARBON_THRESHOLD_KG).sum()),
                    "n_ci_attr_below_threshold": int((e["ci_attributional"] <= P.LOW_CARBON_THRESHOLD_KG).sum()),
                }
    return out


def by_country(eta: float | None = None, cod_mg_l: float = 278.0, digesting: bool = True) -> pd.DataFrame:
    e = evaluate(eta=eta, cod_mg_l=cod_mg_l, digesting=digesting)
    g = e.groupby(["iso", "country"]).agg(
        plants=("waste_id", "size"), flow_m3d=("flow_m3d", "sum"), h2_kg_d=("h2_kg_d", "sum"),
        diesel_l_d=("diesel_l_d", "sum"), co2_t_yr=("co2_t_yr", "sum"), value_usd_yr=("value_usd_yr", "sum"),
        grid_ef=("grid_ef", "first"), diesel_price=("diesel_price", "first"),
        ci_cons=("ci_consequential", "first"), value_per_kg=("value_usd_yr", "sum"))
    g["value_per_kg"] = g["value_usd_yr"] / (g["h2_kg_d"] * P.DAYS_PER_YEAR)
    return g.reset_index().sort_values("plants", ascending=False)


def supply_curve(eta: float | None = None, cod_mg_l: float = 278.0, digesting: bool = True) -> pd.DataFrame:
    """Plants ordered by net value per kg of hydrogen (highest first), with cumulative hydrogen."""
    e = evaluate(eta=eta, cod_mg_l=cod_mg_l, digesting=digesting)
    e["value_per_kg"] = e["value_usd_yr"] / (e["h2_kg_d"] * P.DAYS_PER_YEAR)
    e = e.sort_values("value_per_kg", ascending=False).reset_index(drop=True)
    e["cum_h2_kt_yr"] = e["h2_kg_d"].cumsum() * P.DAYS_PER_YEAR / 1e6
    return e
