"""Allocation of captured sludge COD between hydrogen and methane (Supplementary Note S21).

Hydrogen and methane compete for the same COD. Every kg of hydrogen carries 8 kg of COD that the
existing digesters would otherwise convert to methane, so the comparison is made on the COD that
fermentation turns into hydrogen, and plant configurations are compared with digestion alone (C0):

    C1   hydrogen skimming: dark fermentation (DF) of the pretreated sludge at the pilot feed
         strength, effluent (volatile fatty acids and solids) to the existing digesters
    C2   the design-case DF-PF cascade: DF effluent volatile fatty acids to photo-fermentation (PF)
         after membrane concentration; PF residues leave the digesters (as designed)
    C2r  as C2, with the PF residues returned to the digesters (best case for PF)

Each configuration is evaluated for two end uses of the hydrogen: on-site fuel-cell electricity
("fc") and fuel-cell buses replacing diesel buses ("bus"). Methane forgone is valued at the CHP
electrical efficiency and replaced from the grid. Carbon follows the consequential design-case
LCA (1:1 lower-heating-value diesel credit under the RED II comparator), with the methane losses
the digesters would have had on the diverted COD, hydrogen leakage, and embodied carbon added.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from . import parameters as P
from .bounds import thauer_yield_kg_per_kg_cod

KWH_PER_MJ = 1.0 / 3.6
H2_KWH_PER_KG = P.LHV_H2_MJ_KG * KWH_PER_MJ                          # 33.3
CH4_KG_PER_KG_COD = P.CH4_NM3_PER_KG_COD * P.CH4_DENSITY              # 0.2506
CH4_MJ_PER_KG_COD = CH4_KG_PER_KG_COD * P.CH4_LHV_MJ_KG               # 12.53
DIESEL_L_PER_KG_H2 = P.DIESEL_BUS_L_PER_100KM / P.FC_BUS_KG_PER_100KM  # 5.0 (vehicle-km basis)
DIESEL_L_PER_KG_CH4 = P.CH4_LHV_MJ_KG / (P.DIESEL_LHV_MJ_L * P.CNG_BUS_ENERGY_FACTOR)   # 0.957
FOSSIL_CREDIT_KG_PER_KG_H2 = P.LHV_H2_GJ_KG * P.RED_II_COMPARATOR_G_MJ  # 11.28 (1:1 LHV)


def mid(r):
    return 0.5 * (r[0] + r[1])


CENTRAL = {
    "f_ch4": mid(P.CH4_CONVERSION_RANGE),        # 0.90
    "chp": mid(P.CHP_ELEC_EFF_RANGE),            # 0.395
    "fc": P.FC_EFFICIENCY,                       # 0.50
    "fc_bus_kg": P.FC_BUS_KG_PER_100KM,          # 8 kg per 100 km
    "beb_kwh_km": mid(P.BEB_KWH_PER_KM_RANGE),   # 1.565 kWh per km (battery-electric bus)
    "h2_comp_kwh": mid(P.H2_COMPRESSION_KWH_PER_KG),
    "cbg_kwh": mid(P.CBG_CONDITIONING_KWH_PER_KG),
    "slip": mid(P.UPGRADING_CH4_SLIP_RANGE),
    "ch4_loss": mid(P.DIGESTER_CH4_LOSS_RANGE),
    "h2_leak": 0.01,
    "grid_ef": P.COUNTRY_INPUTS["EGY"][1],       # 0.563 (Ember 2025)
    "diesel_price": P.COUNTRY_INPUTS["EGY"][2],  # US$0.39 L-1
    "elec_price": P.ELECTRICITY_PRICE,           # US$0.05 kWh-1
    "downstream": mid(P.DOWNSTREAM_COST),        # US$1.45 kg-1 purification, compression, storage
    "skim_parasitic_mwh_d": P.PARASITIC_REF_MWH_D,   # per GEA captured COD (value)
    "skim_lca_mwh_d": P.LCA_ELECTRICITY_MWH_D,       # per GEA captured COD (carbon; upper bound)
    "membrane_mwh_d": mid(P.MEMBRANE_MWH_D_RANGE),
    "embodied_t": P.EMBODIED_TOTAL_T,
}


def params(**kw) -> dict:
    p = dict(CENTRAL)
    unknown = set(kw) - set(p)
    if unknown:
        raise KeyError(f"unknown parameter(s): {sorted(unknown)}")
    p.update(kw)
    return p


# ---------------------------------------------------------------------------
# Per kg of COD turned into hydrogen (independent of the fermentation yield)
# ---------------------------------------------------------------------------
def per_kg_cod(**kw) -> dict:
    """Services delivered by 1 kg COD as hydrogen (0.125 kg H2) and as digester methane."""
    p = params(**kw)
    h2 = 1.0 / P.H2_COD_EQUIVALENT
    ch4 = p["f_ch4"] * CH4_KG_PER_KG_COD
    diesel_per_kg_h2 = P.DIESEL_BUS_L_PER_100KM / p["fc_bus_kg"]
    out = {
        "h2_kg": h2, "ch4_kg": ch4,
        "energy_MJ": {"H2": h2 * P.LHV_H2_MJ_KG, "CH4": ch4 * P.CH4_LHV_MJ_KG},
        "electricity_kWh": {"H2": h2 * H2_KWH_PER_KG * p["fc"],
                            "CH4": ch4 * P.CH4_LHV_MJ_KG * KWH_PER_MJ * p["chp"]},
        "diesel_L": {"H2": h2 * diesel_per_kg_h2,
                     "CH4": ch4 * (1.0 - p["slip"]) * DIESEL_L_PER_KG_CH4},
        "conditioning_kWh": {"H2": h2 * p["h2_comp_kwh"], "CH4": ch4 * p["cbg_kwh"]},
    }
    out["ratio"] = {k: out[k]["H2"] / out[k]["CH4"] for k in ("energy_MJ", "electricity_kWh", "diesel_L")}
    # methane burned in CHP and the electricity used in battery-electric buses (alternative to biomethane)
    out["diesel_L_battery_bus"] = (out["electricity_kWh"]["CH4"] / p["beb_kwh_km"]
                                   * P.DIESEL_BUS_L_PER_100KM / 100.0)
    out["ratio"]["diesel_L_battery_bus"] = out["diesel_L"]["H2"] / out["diesel_L_battery_bus"]
    return out


def battery_bus_alternative(purification_loss: float = 0.15) -> dict:
    """Diesel displaced per kg COD by hydrogen in fuel-cell buses and by the CHP electricity from the same
    COD as methane in battery-electric buses, over all corners of the parameter bounds."""
    import itertools
    keys = {"f_ch4": P.CH4_CONVERSION_RANGE, "chp": P.CHP_ELEC_EFF_RANGE,
            "fc_bus_kg": P.FC_BUS_KG_PER_100KM_RANGE, "beb_kwh_km": P.BEB_KWH_PER_KM_RANGE}
    rows = [per_kg_cod(**dict(zip(keys, c))) for c in itertools.product(*keys.values())]
    h2 = [r["diesel_L"]["H2"] for r in rows]
    bb = [r["diesel_L_battery_bus"] for r in rows]
    ratio = [r["ratio"]["diesel_L_battery_bus"] for r in rows]
    return {"h2_L": (min(h2), max(h2)), "battery_bus_L": (min(bb), max(bb)), "ratio": (min(ratio), max(ratio)),
            "ratio_with_loss": (min(ratio) * (1 - purification_loss), max(ratio) * (1 - purification_loss)),
            "central_battery_bus_L": per_kg_cod()["diesel_L_battery_bus"]}


def per_kg_cod_ranges() -> dict:
    """Ranges of the hydrogen-to-methane ratios over the parameter bounds (all corners)."""
    import itertools
    keys = {"f_ch4": P.CH4_CONVERSION_RANGE, "chp": P.CHP_ELEC_EFF_RANGE,
            "fc_bus_kg": P.FC_BUS_KG_PER_100KM_RANGE, "slip": P.UPGRADING_CH4_SLIP_RANGE}
    vals = {"energy_MJ": [], "electricity_kWh": [], "diesel_L": []}
    for combo in itertools.product(*keys.values()):
        r = per_kg_cod(**dict(zip(keys, combo)))["ratio"]
        for k in vals:
            vals[k].append(r[k])
    return {k: (min(v), max(v)) for k, v in vals.items()}


def skim_share(eta: float) -> float:
    """Share of the captured COD that leaves as hydrogen (kg COD in H2 per kg COD captured)."""
    return eta * thauer_yield_kg_per_kg_cod() * P.H2_COD_EQUIVALENT


def chemical_energy_gain(eta: float, f_ch4: float = 1.0) -> float:
    """Change in chemical energy recovered per kg captured COD when hydrogen is skimmed ahead of
    digestion, as a share of the theoretical methane energy of that COD (12.53 MJ kg-1)."""
    h2_mj = eta * thauer_yield_kg_per_kg_cod() * P.LHV_H2_MJ_KG
    lost = skim_share(eta) * f_ch4 * CH4_MJ_PER_KG_COD
    return (h2_mj - lost) / CH4_MJ_PER_KG_COD


# ---------------------------------------------------------------------------
# Plant configurations (Gabal El-Asfar by default)
# ---------------------------------------------------------------------------
@dataclass
class Config:
    name: str
    end_use: str
    h2_kg_d: float
    cod_diverted_kg_d: float        # COD the digesters no longer receive
    ch4_forgone_kg_d: float
    chp_forgone_mwh_d: float
    process_mwh_d: float            # value boundary (direct parasitic, membranes, compression)
    lca_mwh_d: float                # carbon boundary
    fc_mwh_d: float
    net_electricity_mwh_d: float    # change against digestion alone (value boundary)
    diesel_l_d: float
    co2_t_yr: float                 # change in emissions against digestion alone (negative = saving)
    ci_attributional: float         # kg CO2-eq kg-1 H2, plant gate, sludge as zero-burden waste
    ci_consequential: float         # production intensity with forgone biogas, losses, leakage, embodied
    avoided_kg_per_kg: float        # consequential avoided emissions per kg H2 (bus use)
    value_usd_yr: float
    allowable_capex_usd: float


def _annuity(rate: float = P.WACC, years: int = P.PROJECT_LIFE_YR) -> float:
    f = (1.0 + rate) ** years
    return rate * f / (f - 1.0)


def configuration(name: str, end_use: str = "bus", eta: float | None = None,
                  captured_cod_kg_d: float = P.REF_CAPTURED_COD_KGD, digesting: bool = True,
                  **kw) -> Config:
    """Evaluate one configuration against digestion alone."""
    from .case_study import ETA_PILOT
    p = params(**kw)
    eta = ETA_PILOT if eta is None else eta
    scale = captured_cod_kg_d / P.REF_CAPTURED_COD_KGD
    y_th = thauer_yield_kg_per_kg_cod()
    df_h2 = eta * y_th * captured_cod_kg_d
    pf_h2 = P.REF_H2_PF_M3D * P.H2_DENSITY * scale
    vfa = 0.5 * captured_cod_kg_d
    if name == "C1":
        h2, diverted = df_h2, df_h2 * P.H2_COD_EQUIVALENT
        proc = p["skim_parasitic_mwh_d"] * scale
        lca = p["skim_lca_mwh_d"] * scale
    elif name == "C2":
        h2, diverted = df_h2 + pf_h2, df_h2 * P.H2_COD_EQUIVALENT + vfa
        proc = (P.PARASITIC_REF_MWH_D + p["membrane_mwh_d"]) * scale
        lca = (P.LCA_ELECTRICITY_MWH_D + p["membrane_mwh_d"]) * scale
    elif name == "C2r":
        h2, diverted = df_h2 + pf_h2, (df_h2 + pf_h2) * P.H2_COD_EQUIVALENT
        proc = (P.PARASITIC_REF_MWH_D + p["membrane_mwh_d"]) * scale
        lca = (P.LCA_ELECTRICITY_MWH_D + p["membrane_mwh_d"]) * scale
    else:
        raise ValueError(name)
    if not digesting:
        diverted = 0.0
    ch4 = diverted * p["f_ch4"] * CH4_KG_PER_KG_COD
    chp = ch4 * P.CH4_LHV_MJ_KG * KWH_PER_MJ * p["chp"] / 1000.0         # MWh d-1
    fc = h2 * H2_KWH_PER_KG * p["fc"] / 1000.0 if end_use == "fc" else 0.0
    comp = h2 * p["h2_comp_kwh"] / 1000.0 if end_use == "bus" else 0.0
    net_e = fc - chp - proc - comp
    diesel = h2 * P.DIESEL_BUS_L_PER_100KM / p["fc_bus_kg"] if end_use == "bus" else 0.0

    d = P.DAYS_PER_YEAR
    h2_yr = h2 * d
    ef = p["grid_ef"]
    elec_t = (chp + lca + comp - fc) * 1000.0 * ef / 1000.0 * d                # t yr-1
    loss_credit_t = ch4 * p["ch4_loss"] * P.CH4_GWP100 / 1000.0 * d
    leak_t = h2 * p["h2_leak"] / (1.0 - p["h2_leak"]) * P.H2_GWP100 / 1000.0 * d
    embodied_t = p["embodied_t"] * scale / P.PROJECT_LIFE_YR
    fossil_t = h2_yr * FOSSIL_CREDIT_KG_PER_KG_H2 / 1000.0 if end_use == "bus" else 0.0
    co2 = elec_t - loss_credit_t + leak_t + embodied_t - fossil_t

    # production intensities (per kg H2, before any use credit)
    ci_attr = (lca + comp) * 1000.0 * ef / h2 if h2 else float("nan")
    ci_cons = ci_attr + (chp * 1000.0 * ef - ch4 * p["ch4_loss"] * P.CH4_GWP100
                         + h2 * p["h2_leak"] / (1.0 - p["h2_leak"]) * P.H2_GWP100) / h2 \
        + embodied_t * 1000.0 / h2_yr
    avoided = FOSSIL_CREDIT_KG_PER_KG_H2 - ci_cons

    if end_use == "bus":
        value = h2_yr * (diesel / h2 * p["diesel_price"] - p["downstream"]) \
            - (chp + proc) * 1000.0 * p["elec_price"] * d
    else:
        value = net_e * 1000.0 * p["elec_price"] * d
    allowable = value / (_annuity() + P.OPEX_TO_CAPEX)
    return Config(name, end_use, h2, diverted, ch4, chp, proc + comp, lca + comp, fc, net_e, diesel,
                  co2, ci_attr, ci_cons, avoided, value, allowable)


def gea_table(eta: float | None = None, **kw) -> dict:
    """All configurations and end uses at Gabal El-Asfar."""
    out = {}
    for name in ("C1", "C2", "C2r"):
        for use in ("fc", "bus"):
            out[f"{name}_{use}"] = asdict(configuration(name, use, eta=eta, **kw))
    return out


def gea_ranges(eta: float | None = None) -> dict:
    """Low-high bounds of the key outputs over the parameter ranges that drive them."""
    import itertools
    grid = {"f_ch4": P.CH4_CONVERSION_RANGE, "chp": P.CHP_ELEC_EFF_RANGE,
            "membrane_mwh_d": P.MEMBRANE_MWH_D_RANGE, "h2_comp_kwh": P.H2_COMPRESSION_KWH_PER_KG,
            "ch4_loss": P.DIGESTER_CH4_LOSS_RANGE, "h2_leak": P.H2_LEAK_RANGE}
    res = {}
    for name in ("C1", "C2", "C2r"):
        g = dict(grid)
        if name == "C1":   # skimming burdens: direct process loads only and no embodied carbon, up to the design case
            g.update(skim_lca_mwh_d=(P.PARASITIC_REF_MWH_D, P.LCA_ELECTRICITY_MWH_D), embodied_t=(0.0, P.EMBODIED_TOTAL_T))
        for use in ("fc", "bus"):
            rows = [configuration(name, use, eta=eta, **dict(zip(g, c))) for c in itertools.product(*g.values())]
            res[f"{name}_{use}"] = {k: (min(getattr(r, k) for r in rows), max(getattr(r, k) for r in rows))
                                   for k in ("net_electricity_mwh_d", "chp_forgone_mwh_d", "co2_t_yr",
                                             "ci_consequential", "ci_attributional", "value_usd_yr",
                                             "avoided_kg_per_kg")}
    return res


def biocng_alternative(eta: float | None = None, **kw) -> dict:
    """Diesel displaced if the methane forgone by skimming were instead upgraded to biomethane
    for CNG buses, against the skimmed hydrogen in fuel-cell buses (per day)."""
    p = params(**kw)
    c1 = configuration("C1", "bus", eta=eta, **kw)
    ch4 = c1.ch4_forgone_kg_d
    cng_diesel = ch4 * (1.0 - p["slip"]) * DIESEL_L_PER_KG_CH4
    return {"h2_diesel_l_d": c1.diesel_l_d, "biocng_diesel_l_d": cng_diesel,
            "ratio": c1.diesel_l_d / cng_diesel,
            "h2_conditioning_mwh_d": c1.h2_kg_d * p["h2_comp_kwh"] / 1000.0,
            "biocng_conditioning_mwh_d": ch4 * p["cbg_kwh"] / 1000.0}


def threshold_kg(saving: float) -> float:
    """Production intensity (kg CO2-eq kg-1 H2) that meets a saving against the 94 g MJ-1 comparator."""
    return P.RED_II_COMPARATOR_G_MJ * (1.0 - saving) * P.LHV_H2_GJ_KG


def grid_crossover(eta: float | None = None, threshold: float = P.LOW_CARBON_THRESHOLD_KG,
                   end_use: str = "bus", **kw) -> float:
    """Grid carbon intensity (kg CO2-eq kWh-1) below which the consequential production intensity
    of skimmed hydrogen at a digesting plant meets the low-carbon threshold."""
    a = configuration("C1", end_use, eta=eta, **dict(kw, grid_ef=1.0)).ci_consequential
    b = configuration("C1", end_use, eta=eta, **dict(kw, grid_ef=0.0)).ci_consequential
    slope = a - b
    return (threshold - b) / slope if slope > 0 else float("inf")


def grid_electricity_per_kg(eta: float | None = None, end_use: str = "bus", **kw) -> dict:
    """Grid electricity carried by 1 kg of skimmed hydrogen in the consequential intensity at a digesting
    plant (kWh kg-1 H2; the slope of the intensity against the grid factor), and the part of it that is
    forgone CHP output."""
    a = configuration("C1", end_use, eta=eta, **dict(kw, grid_ef=1.0))
    b = configuration("C1", end_use, eta=eta, **dict(kw, grid_ef=0.0))
    return {"kwh_per_kg": a.ci_consequential - b.ci_consequential,
            "chp_forgone_kwh_per_kg": 1000.0 * a.chp_forgone_mwh_d / a.h2_kg_d}


def break_even_diesel_price(eta: float | None = None, **kw) -> float:
    """Retail diesel price (US$ L-1) at which skimming with bus use has zero net value before capital.
    Independent of plant size, because hydrogen, forgone CHP and process loads all scale with captured COD."""
    v0 = configuration("C1", "bus", eta=eta, **dict(kw, diesel_price=0.0)).value_usd_yr
    v1 = configuration("C1", "bus", eta=eta, **dict(kw, diesel_price=1.0)).value_usd_yr
    return -v0 / (v1 - v0)


def break_even_h2_price(eta: float | None = None, **kw) -> float:
    """Price (US$ kg-1 H2) at which a utility selling the hydrogen, rather than using it in its own buses,
    breaks even before capital: conditioning cost plus forgone CHP electricity and process load per kg."""
    p = params(**{k: v for k, v in kw.items() if k not in ("captured_cod_kg_d", "digesting")})
    c = configuration("C1", "bus", eta=eta, **kw)
    return p["downstream"] + (c.chp_forgone_mwh_d + c.process_mwh_d - c.h2_kg_d * p["h2_comp_kwh"] / 1000.0) \
        * 1000.0 * p["elec_price"] / c.h2_kg_d


def min_yield_for_threshold(threshold: float = P.LOW_CARBON_THRESHOLD_KG, grid_ef: float = 0.0,
                            digesting: bool = True, **kw) -> float:
    """Smallest fraction of the Thauer yield at which the consequential intensity (bus use) meets the threshold
    on a grid of the given intensity (bisection; the intensity falls as fixed loads are spread over more hydrogen)."""
    f = lambda e: configuration("C1", "bus", eta=e, digesting=digesting, **dict(kw, grid_ef=grid_ef)).ci_consequential - threshold
    lo, hi = 1e-4, 1.0
    if f(hi) > 0:
        return float("nan")
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
    return hi


def decision_map(etas, values, kind: str = "value", digesting: bool = True, **kw) -> np.ndarray:
    """Screening maps for a digesting plant of Gabal El-Asfar's size with bus use (Fig. 6).
    kind="value": net annual value before capital (US$ yr-1) over yield (rows) x diesel price (columns);
    kind="intensity": consequential intensity (kg CO2-eq kg-1 H2) over yield x grid intensity."""
    key = {"value": "diesel_price", "intensity": "grid_ef"}[kind]
    out = np.empty((len(etas), len(values)))
    for i, e in enumerate(etas):
        for j, v in enumerate(values):
            c = configuration("C1", "bus", eta=float(e), digesting=digesting, **dict(kw, **{key: float(v)}))
            out[i, j] = c.value_usd_yr if kind == "value" else c.ci_consequential
    return out


def skim_reactor_m3(captured_cod_kg_d: float = P.REF_CAPTURED_COD_KGD) -> float:
    """Working volume of the skimming reactor at the pilot feed strength and 2 d HRT."""
    return captured_cod_kg_d / P.SKIM_FEED_COD_KG_M3 * P.SKIM_HRT_D


def eta_scenarios() -> dict:
    """The two readings of the pilot yield used throughout (Methods)."""
    from .case_study import ETA_PILOT, alternative_reading_eta
    return {"pilot": ETA_PILOT, "literature": alternative_reading_eta()}
