"""Consequential life cycle assessment (Methods; Supplementary Note S16).

Core deterministic baseline:
    CI = electricity + embodied - fossil transport fuel credit
       = (2.20 MWh d-1 / daily H2) x 0.461 + 9,420 t / (20 yr x annual H2) - 0.120 GJ kg-1 x 94.0 g MJ-1
The LCA-boundary electricity (2.20 MWh d-1) and the embodied carbon (9,420 t) are fixed by the
plant and its throughput, so both are expressed per kg of the reference hydrogen output.
The avoided sludge-management credit is a parametric scenario and is excluded from the baseline.
"""
from __future__ import annotations

from . import parameters as P
from .process import energy_chain


def annual_h2_kg(h2_m3d: float = P.REF_H2_M3D) -> float:
    return energy_chain(h2_m3d).h2_kg_yr


def daily_h2_kg(h2_m3d: float = P.REF_H2_M3D) -> float:
    return energy_chain(h2_m3d).h2_kg_d


def lca_electricity_kwh_per_kg(h2_m3d: float = P.REF_H2_M3D) -> float:
    return P.LCA_ELECTRICITY_MWH_D * 1000.0 / daily_h2_kg(h2_m3d)


def electricity_burden(grid_ef: float = P.GRID_EF_EGYPT, h2_m3d: float = P.REF_H2_M3D) -> float:
    """kg CO2-eq kg-1 H2."""
    return lca_electricity_kwh_per_kg(h2_m3d) * grid_ef


def embodied_burden(h2_kg_yr: float | None = None) -> float:
    """Annualised embodied carbon, kg CO2-eq kg-1 H2."""
    h2_kg_yr = annual_h2_kg() if h2_kg_yr is None else h2_kg_yr
    return P.EMBODIED_TOTAL_T * 1000.0 / (P.PROJECT_LIFE_YR * h2_kg_yr)


def annual_embodied_t() -> float:
    return P.EMBODIED_TOTAL_T / P.PROJECT_LIFE_YR


def fossil_credit() -> float:
    """RED II Annex V comparator on a 1:1 LHV basis, kg CO2-eq kg-1 H2 (positive number)."""
    return P.LHV_H2_GJ_KG * P.RED_II_COMPARATOR_G_MJ


def sludge_cod_per_kg_h2() -> float:
    """Captured COD per kg of hydrogen (kg COD kg-1 H2)."""
    return P.REF_CAPTURED_COD_KGD / daily_h2_kg()


def carbon_intensity(grid_ef: float = P.GRID_EF_EGYPT, include_fossil_credit: bool = True,
                     sludge_ef: float | None = None, burden_scale: float = 1.0) -> float:
    """Net carbon intensity at the reference output, kg CO2-eq kg-1 H2.

    burden_scale multiplies the electricity and embodied terms; use it to hold annual
    burdens fixed while hydrogen output changes (low-yield bound).
    """
    ci = (electricity_burden(grid_ef) + embodied_burden()) * burden_scale
    if include_fossil_credit:
        ci -= fossil_credit()
    if sludge_ef is not None:
        ci -= sludge_cod_per_kg_h2() * sludge_ef
    return ci


def facility_carbon_intensity(h2_kg_d: float, scale: float = 1.0, grid_ef: float = P.GRID_EF_EGYPT) -> float:
    """Deterministic carbon intensity for a screened facility: the GEA LCA-boundary electricity
    and embodied carbon scaled with reactor volume (scale) and divided by that facility's output."""
    elec = P.LCA_ELECTRICITY_MWH_D * scale * 1000.0 * grid_ef / h2_kg_d
    emb = P.EMBODIED_TOTAL_T * scale * 1000.0 / (P.PROJECT_LIFE_YR * h2_kg_d * P.DAYS_PER_YEAR)
    return elec + emb - fossil_credit()


def sludge_credit_range() -> tuple[float, float]:
    lo, hi = P.SLUDGE_EF_RANGE
    return sludge_cod_per_kg_h2() * lo, sludge_cod_per_kg_h2() * hi


def sludge_scenario_range() -> tuple[float, float]:
    lo, hi = P.SLUDGE_EF_RANGE
    return carbon_intensity(sludge_ef=lo), carbon_intensity(sludge_ef=hi)


def red_ii_saving(ci_kg_per_kg: float) -> float:
    """Greenhouse-gas saving relative to the RED II fossil comparator (fraction)."""
    ci_g_mj = ci_kg_per_kg * 1000.0 / (P.LHV_H2_GJ_KG * 1000.0)
    return (P.RED_II_COMPARATOR_G_MJ - ci_g_mj) / P.RED_II_COMPARATOR_G_MJ


def annual_mitigation_t(ci: float | None = None) -> float:
    ci = carbon_intensity() if ci is None else ci
    return -ci * annual_h2_kg() / 1000.0


def carbon_payback_yr(annual_t: float | None = None) -> float:
    annual_t = annual_mitigation_t() if annual_t is None else annual_t
    return P.EMBODIED_TOTAL_T / annual_t


def conservative_mitigation_t() -> float:
    return P.CONSERVATIVE_COUNTERFACTUAL * annual_h2_kg() / 1000.0


def conservative_payback_yr() -> float:
    """Payback under the conservative counterfactual (Supplementary Note S4)."""
    return P.EMBODIED_TOTAL_T / conservative_mitigation_t()


def uncertainty_proxy() -> float:
    """Effective 1-sigma proxy used in Supplementary Note S13: a third of the spread between the
    deterministic baseline and the conservative counterfactual."""
    return (-carbon_intensity() - P.CONSERVATIVE_COUNTERFACTUAL) / 3.0


def alternative_reading() -> dict:
    """Alternative reading of the pilot yield (64.8 mL H2 g-1 VS, ~23 mL g-1 COD): DF output
    falls by the ratio of the two readings; the PF stage is unchanged in the model. Carbon
    intensity with annual burdens held fixed, for this case and for a 7-fold fall of total output."""
    from .case_study import ETA_PILOT, alternative_reading_eta
    ratio = ETA_PILOT / alternative_reading_eta()
    df = P.REF_H2_DF_M3D / ratio
    total = df + P.REF_H2_PF_M3D
    return {"eta_df": alternative_reading_eta(), "fold_lower_df": ratio, "h2_df_m3d": df,
            "h2_m3d": total, "fold_lower_total": P.REF_H2_M3D / total,
            "ci_pf_unchanged": carbon_intensity(burden_scale=P.REF_H2_M3D / total),
            "ci_total_fold": low_yield_bound(ratio)}


def low_yield_bound(yield_ratio: float) -> float:
    """Carbon intensity if output were lower by `yield_ratio` with annual burdens fixed."""
    return carbon_intensity(burden_scale=yield_ratio)


def site_integration() -> dict:
    """Supplementary Note S16b: site-integration sensitivities at Gabal El-Asfar, each applied
    one at a time to the deterministic baseline.

    Biogas forgone: the COD leaving as hydrogen (8 kg COD per kg H2) would otherwise reach the
    existing digesters; upper bound at the stoichiometric methane yield, converted to electricity
    at the CHP efficiency range and replaced from the grid.
    VFA concentration: pump work for membrane concentration of the DF effluent ahead of PF.
    """
    chain = energy_chain(P.REF_H2_M3D)
    h2_kg_d, net = chain.h2_kg_d, chain.net_mwh_d
    cod_h2 = h2_kg_d * P.H2_COD_EQUIVALENT
    ch4_mwh = cod_h2 * P.CH4_NM3_PER_KG_COD * P.CH4_DENSITY * P.CH4_LHV_MJ_KG / 3600.0
    per_kg = lambda mwh: mwh * 1000.0 * P.GRID_EF_EGYPT / h2_kg_d
    base = carbon_intensity()
    elec = [ch4_mwh * e for e in P.CHP_ELEC_EFF_RANGE]
    permeate = P.DF_EFFLUENT_M3D - P.PF_FEED_M3D
    sec = [bar * 0.1 / (P.MEMBRANE_PUMP_EFF * P.MEMBRANE_RECOVERY) / 3.6 for bar in P.MEMBRANE_BAR_RANGE]
    conc = [permeate * k / 1000.0 for k in sec]
    return {
        "cod_to_h2_kg_d": cod_h2,
        "cod_to_h2_share_captured": cod_h2 / P.REF_CAPTURED_COD_KGD,
        "biogas_forgone_ch4_mwh_d": ch4_mwh,
        "biogas_forgone_elec_mwh_d": tuple(elec),
        "biogas_forgone_added_ci": tuple(per_kg(e) for e in elec),
        "biogas_forgone_ci": tuple(base + per_kg(e) for e in elec),
        "biogas_forgone_net_elec_gain_mwh_d": tuple(net - e for e in elec),
        "concentration_permeate_m3d": permeate,
        "concentration_kwh_per_m3_permeate": tuple(sec),
        "concentration_mwh_d": tuple(conc),
        "concentration_added_ci": tuple(per_kg(c) for c in conc),
        "concentration_ci": tuple(base + per_kg(c) for c in conc),
        "concentration_net_elec_mwh_d": tuple(net - c for c in conc),
    }
