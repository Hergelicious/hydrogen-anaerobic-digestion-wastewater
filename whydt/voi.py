"""Which input decides whether hydrogen skimming is worthwhile (Supplementary Note S23).

Variance-based global sensitivity (Sobol indices) of hydrogen skimming ahead of digestion
(configuration C1, fuel-cell bus end use) at a digesting plant of the Gabal El-Asfar size. Two
outputs: the net annual value (US$ yr-1, before capital) and the net change in emissions
(t CO2-eq yr-1). Inputs are sampled uniformly over the ranges below. First-order indices use the
Saltelli (2010) estimator and total-order indices the Jansen estimator, on N base samples.
"""
from __future__ import annotations

import numpy as np

from . import parameters as P
from .allocation import configuration, eta_scenarios

_e = eta_scenarios()
_ef = [v[1] for v in P.COUNTRY_INPUTS.values()]
_price = [v[2] for v in P.COUNTRY_INPUTS.values()]

RANGES = {
    "eta": (_e["literature"], _e["pilot"]),              # the two readings of the pilot yield
    "diesel_price": (min(_price), P.DIESEL_PRICE_WORLD_AVG),
    "elec_price": P.ELECTRICITY_PRICE_RANGE,
    "downstream": P.DOWNSTREAM_COST,
    "grid_ef": P.SOBOL_GRID_EF_RANGE,
    "chp": P.CHP_ELEC_EFF_RANGE,
    "f_ch4": P.CH4_CONVERSION_RANGE,
    "fc_bus_kg": P.FC_BUS_KG_PER_100KM_RANGE,
    "ch4_loss": P.DIGESTER_CH4_LOSS_RANGE,
    "h2_leak": P.H2_LEAK_RANGE,
    "h2_comp_kwh": P.H2_COMPRESSION_KWH_PER_KG,
    "skim_lca_mwh_d": (P.PARASITIC_REF_MWH_D, P.LCA_ELECTRICITY_MWH_D),
    "embodied_t": (0.0, P.EMBODIED_TOTAL_T),
}
LABELS = {
    "eta": "Fermentative yield", "diesel_price": "Diesel price",
    "elec_price": "Electricity price", "downstream": "Hydrogen conditioning cost",
    "grid_ef": "Grid carbon intensity", "chp": "CHP electrical efficiency",
    "f_ch4": "Methane yield of diverted COD", "fc_bus_kg": "Fuel-cell bus consumption",
    "ch4_loss": "Digester methane losses", "h2_leak": "Hydrogen leakage",
    "h2_comp_kwh": "Hydrogen compression energy", "skim_lca_mwh_d": "Process electricity",
    "embodied_t": "Embodied carbon",
}


def _outputs(x: np.ndarray, names: list[str]) -> np.ndarray:
    out = np.empty((len(x), 2))
    for i, row in enumerate(x):
        kw = dict(zip(names, row))
        eta = kw.pop("eta")
        c = configuration("C1", "bus", eta=eta, **kw)
        out[i] = (c.value_usd_yr, c.co2_t_yr)
    return out


def sobol(n: int = 4096, seed: int = 42, ranges: dict | None = None) -> dict:
    """First- and total-order Sobol indices for value and emissions (ranges: optional override of RANGES)."""
    R = RANGES if ranges is None else ranges
    names = list(R)
    k = len(names)
    lo = np.array([R[v][0] for v in names])
    hi = np.array([R[v][1] for v in names])
    rng = np.random.default_rng(seed)
    a = lo + (hi - lo) * rng.random((n, k))
    b = lo + (hi - lo) * rng.random((n, k))
    fa, fb = _outputs(a, names), _outputs(b, names)
    var = np.var(np.vstack([fa, fb]), axis=0, ddof=1)
    s1 = np.empty((k, 2))
    st = np.empty((k, 2))
    for i in range(k):
        abi = a.copy()
        abi[:, i] = b[:, i]
        fabi = _outputs(abi, names)
        s1[i] = np.mean(fb * (fabi - fa), axis=0) / var
        st[i] = 0.5 * np.mean((fa - fabi) ** 2, axis=0) / var
    res = {}
    for j, out in enumerate(("value", "co2")):
        res[out] = {names[i]: {"S1": float(s1[i, j]), "ST": float(st[i, j])} for i in range(k)}
        res[out + "_mean"] = float(np.mean(np.concatenate([fa[:, j], fb[:, j]])))
        res[out + "_p5_p95"] = tuple(float(q) for q in np.percentile(np.concatenate([fa[:, j], fb[:, j]]), [5, 95]))
        res[out + "_share_positive"] = float(np.mean(np.concatenate([fa[:, j], fb[:, j]]) > 0))
    res["n"] = n
    res["evaluations"] = n * (k + 2)
    return res


def conditional_on_yield(n: int = 20000, seed: int = 7, ranges: dict | None = None) -> dict:
    """Distribution of value and emissions with the yield fixed at each reading and all other
    inputs sampled over their ranges."""
    R = RANGES if ranges is None else ranges
    names = [v for v in R if v != "eta"]
    lo = np.array([R[v][0] for v in names])
    hi = np.array([R[v][1] for v in names])
    rng = np.random.default_rng(seed)
    x = lo + (hi - lo) * rng.random((n, len(names)))
    out = {}
    for reading, eta in eta_scenarios().items():
        y = np.empty((n, 2))
        for i, row in enumerate(x):
            c = configuration("C1", "bus", eta=eta, **dict(zip(names, row)))
            y[i] = (c.value_usd_yr, c.co2_t_yr)
        out[reading] = {"value_p5_p50_p95": tuple(float(q) for q in np.percentile(y[:, 0], [5, 50, 95])),
                        "co2_p5_p50_p95": tuple(float(q) for q in np.percentile(y[:, 1], [5, 50, 95])),
                        "share_value_positive": float(np.mean(y[:, 0] > 0)),
                        "share_co2_saving": float(np.mean(y[:, 1] < 0))}
    return out
