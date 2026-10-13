"""Hydrogen yield and energy chain.

DF output follows H2_DF = eta_DF x Y_Th x C_cap, with eta_DF anchored to the pilot-derived
constant (Methods). PF output depends on the volatile fatty acids passed from DF and the
photo-fermentation conditions, not on eta_DF (whydt.case_study). Facility screening scales the
Gabal El-Asfar (GEA) reference by the surrogate's relative response (DF stage) and by reactor
volume (both stages), with the GEA design basis held fixed (substrate throughput is not
rescaled with OLR).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from . import parameters as P
from .surrogate import anchored_eta


def thauer_m3_per_kg_cod() -> float:
    """Thauer yield in volume terms, m3 H2 kg-1 COD (0.467)."""
    from .bounds import thauer_yield_kg_per_kg_cod
    return thauer_yield_kg_per_kg_cod() / P.H2_DENSITY


def pilot_specific_yield_m3_per_kg_cod() -> float:
    """Pilot specific yield, m3 H2 kg-1 COD (0.163; volumetric reading, Methods)."""
    return P.PILOT_YIELD_M3_PER_M3 / P.PILOT_COD_KG_M3


def pilot_eta() -> float:
    """Pilot-derived eta_DF: pilot specific yield / Thauer yield (0.349)."""
    return pilot_specific_yield_m3_per_kg_cod() / thauer_m3_per_kg_cod()


def df_output_m3d(eta_df: float = P.REF_ETA_DF, captured_cod_kg_d: float = P.REF_CAPTURED_COD_KGD) -> float:
    """Closed-form DF output, eta_DF x Y_Th x C_cap (m3 H2 d-1)."""
    return eta_df * thauer_m3_per_kg_cod() * captured_cod_kg_d


def volumetric_productivity(h2_m3d: float, reactor_m3: float = P.REF_REACTOR_M3) -> float:
    """m3 H2 m-3 reactor d-1."""
    return h2_m3d / reactor_m3


@dataclass
class EnergyChain:
    h2_m3d: float
    h2_kg_d: float
    h2_kg_yr: float
    gross_mwh_d: float
    fc_mwh_d: float
    parasitic_mwh_d: float
    net_mwh_d: float
    leverage_ratio: float
    parasitic_kwh_per_kg: float

    def as_dict(self) -> dict:
        return asdict(self)


def energy_chain(h2_m3d: float, parasitic_mwh_d: float = P.PARASITIC_REF_MWH_D) -> EnergyChain:
    kg_d = h2_m3d * P.H2_DENSITY
    gross = kg_d * P.LHV_H2_MJ_KG / 3600.0
    fc = gross * P.FC_EFFICIENCY
    net = max(0.0, fc - parasitic_mwh_d)
    return EnergyChain(
        h2_m3d=h2_m3d, h2_kg_d=kg_d, h2_kg_yr=kg_d * P.DAYS_PER_YEAR,
        gross_mwh_d=gross, fc_mwh_d=fc, parasitic_mwh_d=parasitic_mwh_d, net_mwh_d=net,
        leverage_ratio=(net / parasitic_mwh_d) if parasitic_mwh_d > 0 else float("inf"),
        parasitic_kwh_per_kg=(parasitic_mwh_d * 1000.0 / kg_d) if kg_d > 0 else float("inf"),
    )


def gea_attainment() -> dict:
    """GEA output relative to the Thauer yield on the captured COD (attainment of the DF
    stoichiometric benchmark) and the COD recovered in hydrogen (8 kg COD kg-1 H2).
    Attainment is not a COD mass balance."""
    cap = thauer_m3_per_kg_cod() * P.REF_CAPTURED_COD_KGD
    kg_d = P.REF_H2_M3D * P.H2_DENSITY
    return {"attainment_df": P.REF_H2_DF_M3D / cap,
            "attainment_pf": P.REF_H2_PF_M3D / cap,
            "attainment_total": P.REF_H2_M3D / cap,
            "total_to_df": P.REF_H2_M3D / P.REF_H2_DF_M3D,
            "pf_share": P.REF_H2_PF_M3D / P.REF_H2_M3D,
            "df_share": P.REF_H2_DF_M3D / P.REF_H2_M3D,
            "cod_in_h2_share": kg_d * P.H2_COD_EQUIVALENT / P.REF_CAPTURED_COD_KGD,
            "specific_yield_ml_per_g_cod": P.REF_H2_M3D * 1000.0 / (P.REF_CAPTURED_COD_KGD * 1000.0),
            "stage_sum_m3d": P.REF_H2_DF_M3D + P.REF_H2_PF_M3D}


def pumping_sensitivity() -> dict:
    """Disclosed sensitivity (Methods): the pumping specific energy applied to the full diluted
    DF influent instead of the raw primary sludge."""
    from .lca import carbon_intensity
    ref = energy_chain(P.REF_H2_M3D)
    load = P.PUMPING_KWH_PER_M3 * P.DF_EFFLUENT_M3D / 1000.0          # MWh d-1
    net = ref.fc_mwh_d - load
    extra_kwh_per_kg = (load - P.PARASITIC_REF_MWH_D) * 1000.0 / ref.h2_kg_d
    return {"parasitic_mwh_d": load, "net_mwh_d": net, "leverage_ratio": net / load,
            "carbon_intensity": carbon_intensity() + extra_kwh_per_kg * P.GRID_EF_EGYPT,
            "lcoh_add": extra_kwh_per_kg * P.ILLUSTRATIVE_TARIFF}


@dataclass
class ScreeningResult:
    eta_df: float
    relative_response: float
    h2_df_m3d: float
    h2_pf_m3d: float
    h2_m3d: float
    energy: EnergyChain


def screen(olr: float, nh4: float, alk: float,
           reactor_m3: float = P.REF_REACTOR_M3) -> ScreeningResult:
    """Facility screening: anchored efficiency, integrated output and energy chain.

    The GEA cost and process structure is scaled with reactor volume; the parasitic load
    (0.8 MWh d-1 at the reference volume) scales with it, since pumping and mixing scale
    with the reactor.
    """
    eta = anchored_eta(olr, nh4, alk)
    rel = eta / P.REF_ETA_DF
    scale = reactor_m3 / P.REF_REACTOR_M3
    h2_df = P.REF_H2_DF_M3D * rel * scale
    h2_pf = P.REF_H2_PF_M3D * scale
    chain = energy_chain(h2_df + h2_pf, P.PARASITIC_REF_MWH_D * scale)
    return ScreeningResult(eta_df=eta, relative_response=rel, h2_df_m3d=h2_df,
                           h2_pf_m3d=h2_pf, h2_m3d=h2_df + h2_pf, energy=chain)
