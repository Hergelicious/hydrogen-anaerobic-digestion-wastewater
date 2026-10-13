"""Three-sensor screening surrogate for dark-fermentation efficiency (eta_DF).

The deployed surrogate is a Ridge regression (alpha = 10) fitted to logit(eta), where eta is
the synthetic efficiency index rescaled to the 0.55 mesophilic ceiling, with z-scored OLR,
ammonium and alkalinity inputs (Supplementary Note S14b; ml/train_surrogate.py). Its inverse
transform is eta(x) = min(0.55, 1 / (1 + exp(-lp))).

Absolute efficiency is set by the one pilot-derived constant (eta_pilot = 0.349), assigned to
the Gabal El-Asfar design state (REF_INPUTS). The surrogate's contribution is the relative
response of eta_DF to the three sensor inputs: eta_DF(x) = min(0.55, eta_pilot x eta(x) / eta(ref)).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import parameters as P


def _z(name: str, value: float) -> float:
    mean, sd = P.SCALER[name]
    return (value - mean) / sd


def logit_prediction(olr: float, nh4: float, alk: float) -> float:
    """Linear predictor in logit space."""
    return (P.RIDGE_INTERCEPT
            + P.BETA["OLR"] * _z("OLR", olr)
            + P.BETA["NH4"] * _z("NH4", nh4)
            + P.BETA["ALK"] * _z("ALK", alk))


def surrogate_eta(olr: float, nh4: float, alk: float) -> float:
    """Point prediction of the (rescaled) efficiency index, bounded at ETA_CAP."""
    return min(P.ETA_CAP, 1.0 / (1.0 + math.exp(-logit_prediction(olr, nh4, alk))))


def relative_response(olr: float, nh4: float, alk: float) -> float:
    """Ratio of the surrogate prediction to its value at the design-state reference inputs."""
    ref = P.REF_INPUTS
    return surrogate_eta(olr, nh4, alk) / surrogate_eta(ref["OLR"], ref["NH4"], ref["ALK"])


def anchored_eta(olr: float, nh4: float, alk: float) -> float:
    """Pilot-derived efficiency scaled by the surrogate's relative response, bounded at ETA_CAP."""
    return min(P.ETA_CAP, P.REF_ETA_DF * relative_response(olr, nh4, alk))


@dataclass
class DomainCheck:
    in_domain: bool
    flags: list[str] = field(default_factory=list)
    advisories: list[str] = field(default_factory=list)


def check_domain(olr: float, nh4: float, alk: float,
                 temperature: float | None = None,
                 influent_flow: float | None = None) -> DomainCheck:
    """Apply the domain rules of the deployed surrogate (Methods; Supplementary Tables 40, 41).

    Inputs outside the training envelope of the deployed surrogate raise a High-Variance
    Domain flag: site-specific calibration is required rather than surrogate deployment.
    """
    flags, adv = [], []
    lo, hi = P.DOMAIN["OLR"]
    if not lo <= olr <= hi:
        flags.append(f"OLR {olr:g} outside the surrogate domain {lo:g}-{hi:g} kg COD m-3 d-1")
    lo, hi = P.DOMAIN["NH4"]
    if not lo <= nh4 <= hi:
        flags.append(f"Ammonium {nh4:g} mg L-1 outside the surrogate domain {lo:g}-{hi:g} mg L-1")
    if nh4 > P.NH4_SEVERE:
        adv.append("Ammonium above 1,500 mg L-1: severe inhibition")
    elif nh4 > P.NH4_INHIBITION_ONSET:
        adv.append("Ammonium above 800 mg L-1: onset of inhibition")
    lo, hi = P.DOMAIN["ALK"]
    if not lo <= alk <= hi:
        flags.append(f"Alkalinity {alk:g} mg CaCO3 L-1 outside the surrogate domain {lo:g}-{hi:g}")
    if temperature is not None:
        lo, hi = P.DOMAIN["T"]
        if not lo <= temperature <= hi:
            flags.append(f"Temperature {temperature:g} C outside the mesophilic range {lo:g}-{hi:g} C")
    if influent_flow is not None and influent_flow < P.MIN_FLOW_SCREENING:
        adv.append("Influent flow below 100,000 m3 d-1: below the screening scale "
                   "(Supplementary Table 41)")
    if P.REF_ETA_DF * relative_response(olr, nh4, alk) >= P.ETA_CAP:
        adv.append("Efficiency at the 0.55 mesophilic ceiling: the surrogate response is "
                   "extrapolated beyond the pilot anchor")
    return DomainCheck(in_domain=not flags, flags=flags, advisories=adv)
