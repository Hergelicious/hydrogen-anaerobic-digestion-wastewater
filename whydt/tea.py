"""Screening-level techno-economic analysis (Methods; Supplementary Notes S1, S11, S13, S17)."""
from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr

from . import parameters as P
from .lca import annual_h2_kg, carbon_intensity


def crf(rate: float = P.WACC, years: int = P.PROJECT_LIFE_YR) -> float:
    """Capital recovery factor."""
    f = (1.0 + rate) ** years
    return rate * f / (f - 1.0)


def gross_lcoh(capex: float = P.CAPEX_INCREMENTAL, opex: float = P.OPEX,
               h2_kg_yr: float | None = None, rate: float = P.WACC) -> float:
    h2_kg_yr = annual_h2_kg() if h2_kg_yr is None else h2_kg_yr
    return (capex * crf(rate) + opex) / h2_kg_yr


def diesel_litres_per_kg_h2() -> float:
    """Diesel displaced per kg H2 on a vehicle-kilometre basis: a fuel-cell bus using
    8 kg H2 per 100 km replaces a diesel bus using 40 L per 100 km (5 L kg-1)."""
    return P.DIESEL_BUS_L_PER_100KM / P.FC_BUS_KG_PER_100KM


def diesel_credit(diesel_price: float = P.DIESEL_PRICE_REF) -> float:
    """Avoided diesel expenditure, US$ kg-1 H2."""
    return diesel_litres_per_kg_h2() * diesel_price


def annual_diesel_savings(diesel_price: float = P.DIESEL_PRICE_REF) -> float:
    """US$ yr-1 at the reference output."""
    return diesel_credit(diesel_price) * annual_h2_kg()


def offtake_revenue() -> float:
    """Third-party sale at the offtake price, US$ yr-1 (alternative to the diesel credit)."""
    return P.OFFTAKE_PRICE * annual_h2_kg()


def diesel_credit_bus_range(diesel_price: float = P.DIESEL_PRICE_REF) -> tuple[float, float]:
    """Credit range from reported fuel-cell bus consumption (7-10.25 kg H2 per 100 km)
    against a 40 L per 100 km diesel bus."""
    lo_kg, hi_kg = P.FC_BUS_KG_PER_100KM_RANGE
    return (P.DIESEL_BUS_L_PER_100KM / hi_kg * diesel_price,
            P.DIESEL_BUS_L_PER_100KM / lo_kg * diesel_price)


def net_lcoh(capex: float = P.CAPEX_INCREMENTAL, h2_kg_yr: float | None = None,
             diesel_price: float = P.DIESEL_PRICE_REF, rate: float = P.WACC) -> float:
    return gross_lcoh(capex, h2_kg_yr=h2_kg_yr, rate=rate) - diesel_credit(diesel_price)


def net_lcoh_bus_range() -> tuple[float, float]:
    lo, hi = diesel_credit_bus_range()
    g = gross_lcoh()
    return g - hi, g - lo


def capex_boundaries() -> dict:
    out = {}
    for name, capex in (("incremental", P.CAPEX_INCREMENTAL), ("shared", P.CAPEX_SHARED),
                        ("full", P.CAPEX_FULL)):
        out[name] = {"capex": capex, "gross": gross_lcoh(capex), "net": net_lcoh(capex)}
    return out


def one_at_a_time() -> dict:
    """Net-effective LCOH sensitivity (Supplementary Note S1). The diesel credit is per kg of hydrogen, so it
    scales with output in the yield case."""
    s = P.TEA_SENSITIVITY
    h = annual_h2_kg()
    c = P.CAPEX_INCREMENTAL
    return {
        "capex": (net_lcoh(capex=c * (1 - s["capex"])), net_lcoh(capex=c * (1 + s["capex"]))),
        "wacc": (net_lcoh(rate=s["wacc"][0]), net_lcoh(rate=s["wacc"][1])),
        "yield": (net_lcoh(h2_kg_yr=h * (1 + s["yield"])), net_lcoh(h2_kg_yr=h * (1 - s["yield"]))),
    }


def lcoh_monte_carlo(h2_m3d_rows=None) -> dict:
    """Propagated LCOH uncertainty (Supplementary Note S13): hydrogen output from the case-study
    Monte Carlo rows, CAPEX uniform +/-30% and WACC uniform 5-10%; median and 5th-95th
    percentiles of the net-effective LCOH and variance shares (squared Spearman coefficients
    normalised to their sum)."""
    m = P.TEA_MC
    if h2_m3d_rows is None:
        from .case_study import simulate
        h2_m3d_rows = simulate()["h2"]
    h2 = np.asarray(h2_m3d_rows) * P.H2_DENSITY * P.DAYS_PER_YEAR
    rng = np.random.default_rng(m["seed"])
    n = len(h2)
    capex = P.CAPEX_INCREMENTAL * rng.uniform(1 - m["capex"], 1 + m["capex"], n)
    rate = rng.uniform(*m["wacc"], n)
    f = (1.0 + rate) ** P.PROJECT_LIFE_YR
    crf_ = rate * f / (f - 1.0)
    lcoh = (capex * crf_ + P.OPEX) / h2 - diesel_credit()
    terms = {"hydrogen yield": h2, "CAPEX": capex, "WACC": rate}
    rho2 = {k: spearmanr(v, lcoh)[0] ** 2 for k, v in terms.items()}
    tot = sum(rho2.values())
    return {"median": float(np.median(lcoh)), "p5": float(np.percentile(lcoh, 5)),
            "p95": float(np.percentile(lcoh, 95)),
            "variance_share": {k: v / tot for k, v in rho2.items()}}


def carbon_adjusted_lcoh(carbon_price: float) -> float:
    """Net LCOH minus carbon revenue at the deterministic carbon intensity (US$ t-1)."""
    return net_lcoh() + carbon_intensity() * carbon_price / 1000.0


def smr_ci_differential() -> float:
    """Carbon-intensity differential relative to SMR including upstream emissions (kg kg-1)."""
    return P.SMR_CI_UPSTREAM - carbon_intensity()


def abatement_cost_range() -> tuple[float, float]:
    """Net-effective premium over grey hydrogen divided by the SMR differential (US$ t-1)."""
    lo, hi = P.GREY_H2_PRICE
    n = net_lcoh()
    dci = smr_ci_differential()
    return (n - hi) / dci * 1000.0, (n - lo) / dci * 1000.0


def lcca(comparator: str) -> float:
    """Levelised cost of carbon abatement against a comparator route (US$ t-1)."""
    price, ci_comp = P.LCCA_COMPARATORS[comparator]
    return (net_lcoh() - price) / (ci_comp - carbon_intensity()) * 1000.0


def delivered_lcoh_range(gross: bool = False) -> tuple[float, float]:
    lo, hi = P.DOWNSTREAM_COST
    n = gross_lcoh() if gross else net_lcoh()
    return n + lo, n + hi


def scaled_net_lcoh(flow_m3d: float, exponent: float = 0.6) -> float:
    """Net-effective LCOH at another influent scale (Methods): incremental CAPEX by the
    six-tenths rule; OPEX and the diesel credit proportional to hydrogen output."""
    x = flow_m3d / P.REF_INFLUENT_M3D
    h = annual_h2_kg()
    return (P.CAPEX_INCREMENTAL * crf() / h) * x ** (exponent - 1.0) + P.OPEX / h - diesel_credit()


def scaled_net_lcoh_by_output(h2_m3d: float, exponent: float = 0.6) -> float:
    """Scaled net-effective LCOH for a facility whose scale is proportional to its hydrogen
    output relative to Gabal El-Asfar (Supplementary Table 3)."""
    return scaled_net_lcoh(P.REF_INFLUENT_M3D * h2_m3d / P.REF_H2_M3D, exponent)


def deployment_threshold_flow(lcoh_max: float = 7.50, exponent: float = 0.6) -> float:
    """Smallest influent flow at which the scaled net-effective LCOH reaches lcoh_max
    (Supplementary Note S18; Supplementary Table 42)."""
    h = annual_h2_kg()
    a = P.CAPEX_INCREMENTAL * crf() / h
    b = P.OPEX / h - diesel_credit()
    return P.REF_INFLUENT_M3D * ((lcoh_max - b) / a) ** (1.0 / (exponent - 1.0))


def carbon_parity_price(grey: float = 1.75) -> float:
    """(net-effective LCOH - grey hydrogen price) / |carbon intensity| (US$ t-1)."""
    return (net_lcoh() - grey) / (-carbon_intensity()) * 1000.0


def screening_lcoh(h2_kg_yr: float, reactor_m3: float = P.REF_REACTOR_M3,
                   diesel_price: float = P.DIESEL_PRICE_REF) -> dict:
    """Facility LCOH with the GEA cost structure scaled linearly with reactor volume."""
    scale = reactor_m3 / P.REF_REACTOR_M3
    gross = (P.CAPEX_INCREMENTAL * scale * crf() + P.OPEX * scale) / h2_kg_yr
    return {"gross": gross, "net": gross - diesel_credit(diesel_price)}
