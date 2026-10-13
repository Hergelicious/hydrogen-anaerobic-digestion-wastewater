"""Model-independent stoichiometric bound (Methods).

The Thauer limit (4 mol H2 per mol glucose) bounds dark fermentation and is used as a
DF-referenced benchmark; photo-fermentation of residual volatile fatty acids can in
principle exceed it, up to the electron-balance limit of 12 mol H2 per mol glucose.
"""
from __future__ import annotations

import numpy as np
from . import parameters as P


def thauer_yield_kg_per_kg_cod() -> float:
    """Dark-fermentation (Thauer) yield, kg H2 kg-1 COD (0.0420)."""
    return P.THAUER_MOL_H2_PER_MOL_GLUCOSE * P.H2_MOLAR_MASS / P.GLUCOSE_COD_G_PER_MOL


def electron_balance_yield_kg_per_kg_cod() -> float:
    """Complete electron-balance limit, kg H2 kg-1 COD (0.126)."""
    return P.ELECTRON_BALANCE_MOL_H2_PER_MOL_GLUCOSE * P.H2_MOLAR_MASS / P.GLUCOSE_COD_G_PER_MOL


def global_cod_mt(cod_mg_l):
    """Global municipal COD flux, Mt COD yr-1."""
    return P.GLOBAL_WASTEWATER_M3_YR * np.asarray(cod_mg_l) / 1000.0 / 1e9


def benchmark_h2_mt(cod_mg_l):
    return global_cod_mt(cod_mg_l) * thauer_yield_kg_per_kg_cod()


def benchmark(cod_range=P.INFLUENT_COD_RANGE_MG_L) -> dict:
    """Global COD flux and dark-fermentation benchmark over the influent-strength range."""
    lo, hi = cod_range
    return {"global_cod_mt": (float(global_cod_mt(lo)), float(global_cod_mt(hi))),
            "benchmark_h2_mt": (float(benchmark_h2_mt(lo)), float(benchmark_h2_mt(hi)))}


def energy_allocation() -> dict:
    """Chemical-energy access per kg COD for DF (Thauer), AD and direct thermal routes."""
    df = thauer_yield_kg_per_kg_cod() * P.LHV_H2_MJ_KG
    ad = P.CH4_NM3_PER_KG_COD * P.CH4_DENSITY * P.CH4_LHV_MJ_KG
    th = P.THORNTON_MJ_PER_KG_COD
    lo, hi = P.INFLUENT_COD_RANGE_MG_L
    cod = (float(global_cod_mt(lo)), float(global_cod_mt(hi)))   # Mt = 1e9 kg
    ej = lambda mj: (cod[0] * mj / 1000.0, cod[1] * mj / 1000.0)  # Mt x MJ/kg -> EJ
    return {"MJ_per_kg_COD": {"DF": df, "AD": ad, "thermal": th},
            "share_of_thermal": {"DF": df / th, "AD": ad / th},
            "AD_to_DF_ratio": ad / df,
            "global_EJ": {"thermal": ej(th), "AD": ej(ad), "DF": ej(df)}}


def gea_attainment() -> dict:
    """GEA yield on captured COD relative to the DF benchmark."""
    from .lca import annual_h2_kg
    per_cod = annual_h2_kg() / (P.REF_CAPTURED_COD_KGD * P.DAYS_PER_YEAR)
    return {"kg_h2_per_kg_cod": per_cod,
            "fraction_of_benchmark": per_cod / thauer_yield_kg_per_kg_cod()}
