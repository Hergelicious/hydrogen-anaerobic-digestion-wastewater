"""Gabal El-Asfar (GEA) case study: pilot-anchored dark fermentation with photo-fermentation.

Every GEA output reported in the paper is generated here from documented equations and
inputs (seeded Monte Carlo, n = 500).

Pilot-derived constant
    The El-Kebeer et al. pilot reports 6.48 m3 H2 per m3 of thermally pretreated GEA sludge at
    39.7 kg COD m-3 (volumetric reading; Methods), i.e. 0.163 m3 H2 kg-1 COD, which is
    eta_pilot = 0.163 / 0.467 = 0.349 of the Thauer yield. This is the framework's one
    pilot-derived constant; it is assigned to the GEA design state (reactor OLR
    1.0 kg COD m-3 d-1).

Dark fermentation (DF)
    H2_DF = eta_DF x Y_Th x C_cap
    C_cap  captured primary-sludge COD, 82,792 kg COD d-1 (59% capture)
    Y_Th   Thauer yield, 42.0 g H2 kg-1 COD = 0.467 m3 H2 kg-1 COD at 0.0899 kg m-3

Photo-fermentation (PF)
    m_VFA  = f_VFA x C_cap                    f_VFA = 0.50 (Supplementary Note S11)
    S      = PF feed after membrane concentration of the DF effluent, 3,000 mg COD L-1
    eta_PF = clip(eta_max S/(K_S+S) . 1/(1+NH4/K_NH4) . 1/(1+SO4/K_SO4)
                  . PAR/(K_L+PAR) . theta^(T-30) + e, 0.05, 0.85),  e ~ N(0, 0.02)
             constants from Supplementary Table 30 (K_L in umol photons m-2 s-1)
    H2_PF  = m_VFA x Y_PF x eta_PF             Y_PF = 0.35 m3 H2 kg-1 VFA-COD

Monte Carlo (n = 500, seed 42)
    eta_DF  normal, mean eta_pilot, s.d. 0.067 (the held-out RMSE of the screening surrogate,
            ml/train_surrogate.py), moment-matched so that the sample mean and s.d. equal these
            values; this represents uncertainty in transferring the pilot efficiency to full scale
    NH4, SO4  the 500 rows of the deployed surrogate's training envelope
            (ml/data/DF_training_medium.csv)
    PAR ~ U(100, 800) umol m-2 s-1, T ~ U(20, 35) degC (Supplementary Table 32)

The central estimate is the Monte Carlo mean; because eta_DF is moment-matched, its DF part
equals the closed form eta_pilot x Y_Th x C_cap exactly.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from . import parameters as P

# --------------------------------------------------------------------------- constants
C_CAP_KGD = P.REF_CAPTURED_COD_KGD           # 82,792 kg COD d-1
Y_TH_M3_PER_KG_COD = 0.042 / P.H2_DENSITY     # 0.467 m3 H2 kg-1 COD
PILOT_YIELD_M3_PER_M3 = P.PILOT_YIELD_M3_PER_M3   # 6.48 m3 H2 m-3 sludge
PILOT_COD_KG_M3 = P.PILOT_COD_KG_M3               # 39.7 kg COD m-3
ETA_PILOT = PILOT_YIELD_M3_PER_M3 / PILOT_COD_KG_M3 / Y_TH_M3_PER_KG_COD   # 0.349
ETA_SD = P.ETA_DF_SD                          # 0.067
F_VFA = 0.50
PF_FEED_MG_L = 3_000.0
Y_PF_M3_PER_KG_VFA = 0.35
PF_KIN = {"eta_max": 0.85, "K_S": 800.0, "K_NH4": 150.0, "K_SO4": 150.0,
          "K_L": 300.0, "theta": 1.07, "noise_sd": 0.02, "lo": 0.05, "hi": 0.85}
PAR_RANGE = (100.0, 800.0)
T_RANGE = (20.0, 35.0)
N_ROWS = 500
SEED = 42
ENVELOPE_FILE = Path(__file__).resolve().parent.parent / "ml" / "data" / "DF_training_medium.csv"


def pilot_eta() -> float:
    return ETA_PILOT


def pf_efficiency(S, nh4, so4, par, temp, rng):
    k = PF_KIN
    eta = (k["eta_max"] * S / (k["K_S"] + S) / (1 + nh4 / k["K_NH4"]) / (1 + so4 / k["K_SO4"])
           * par / (k["K_L"] + par) * k["theta"] ** (temp - 30.0))
    eta = eta + rng.normal(0.0, k["noise_sd"], np.shape(par))
    return np.clip(eta, k["lo"], k["hi"])


def envelope_rows(path: str | Path = ENVELOPE_FILE, n: int = N_ROWS):
    import pandas as pd
    df = pd.read_csv(path).iloc[:n]
    return df["NH4_mg_L"].to_numpy(float), df["SO4_mg_L"].to_numpy(float)


def moment_matched_normal(rng, mean: float, sd: float, n: int) -> np.ndarray:
    z = rng.normal(0.0, 1.0, n)
    return mean + sd * (z - z.mean()) / z.std(ddof=1)


@dataclass
class CaseResult:
    n: int
    eta_df_mean: float
    eta_pf_mean: float
    h2_df_m3d: float
    h2_pf_m3d: float
    h2_m3d: float
    h2_m3d_p5: float
    h2_m3d_p95: float
    h2_m3d_sd: float
    h2_df_m3d_p5: float
    h2_df_m3d_p95: float
    total_to_df: float
    pf_share: float

    def as_dict(self) -> dict:
        return asdict(self)


def simulate(n: int = N_ROWS, seed: int = SEED, eta_mean: float = ETA_PILOT,
             eta_sd: float = ETA_SD, c_cap: float = C_CAP_KGD, envelope=ENVELOPE_FILE):
    """Row-wise Monte Carlo; returns the per-row arrays."""
    rng = np.random.default_rng(seed)
    nh4, so4 = envelope_rows(envelope, n)
    n = len(nh4)
    eta = np.clip(moment_matched_normal(rng, eta_mean, eta_sd, n), 0.0, 1.0)
    par = rng.uniform(*PAR_RANGE, n)
    temp = rng.uniform(*T_RANGE, n)
    eta_pf = pf_efficiency(np.full(n, PF_FEED_MG_L), nh4, so4, par, temp, rng)
    h2_df = eta * Y_TH_M3_PER_KG_COD * c_cap
    h2_pf = F_VFA * c_cap * Y_PF_M3_PER_KG_VFA * eta_pf
    return {"eta_df": eta, "eta_pf": eta_pf, "nh4": nh4, "so4": so4, "par": par, "temp": temp,
            "h2_df": h2_df, "h2_pf": h2_pf, "h2": h2_df + h2_pf}


def run(**kw) -> CaseResult:
    s = simulate(**kw)
    tot, df, pf = s["h2"], s["h2_df"], s["h2_pf"]
    return CaseResult(
        n=int(len(tot)), eta_df_mean=float(s["eta_df"].mean()), eta_pf_mean=float(s["eta_pf"].mean()),
        h2_df_m3d=float(df.mean()), h2_pf_m3d=float(pf.mean()), h2_m3d=float(tot.mean()),
        h2_m3d_p5=float(np.percentile(tot, 5)), h2_m3d_p95=float(np.percentile(tot, 95)),
        h2_m3d_sd=float(tot.std(ddof=1)),
        h2_df_m3d_p5=float(np.percentile(df, 5)), h2_df_m3d_p95=float(np.percentile(df, 95)),
        total_to_df=float(tot.mean() / df.mean()), pf_share=float(pf.mean() / tot.mean()))


def pf_feed_check() -> dict:
    """Unit check of the DF-to-PF bridge (mass flow / concentration = flow)."""
    m_vfa = F_VFA * C_CAP_KGD                      # kg COD d-1
    q_pf = m_vfa * 1000.0 / PF_FEED_MG_L           # m3 d-1 (kg -> g, g/m3 = mg/L)
    return {"m_vfa_kgd": m_vfa, "pf_feed_mg_l": PF_FEED_MG_L, "pf_flow_m3d": q_pf}


def alternative_reading_eta() -> float:
    """eta_DF under the alternative reading of the pilot yield (64.8 mL H2 g-1 VS):
    64.8 mL g-1 VS x 14.2 g VS L-1 / 39.7 g COD L-1 = ~23 mL H2 g-1 COD."""
    ml_per_g_cod = 64.8 * P.PILOT_VS_KG_M3 / PILOT_COD_KG_M3
    return ml_per_g_cod / 1000.0 / Y_TH_M3_PER_KG_COD


def seasonal_light_modulation(winter_par=(148.0, 162.0), peak_par=(220.0, 285.0)) -> dict:
    """Winter reduction of PF output from the light term PAR/(K_L + PAR) (Supplementary Note S5:
    December-February monthly means 148-162 umol m-2 s-1 against 220-285 in peak months), and
    the corresponding reduction of integrated output at the case-study PF share."""
    f = lambda par: par / (PF_KIN["K_L"] + par)
    pf = (1.0 - f(winter_par[1]) / f(peak_par[0]), 1.0 - f(winter_par[0]) / f(peak_par[1]))
    share = run().pf_share
    return {"pf_reduction": pf, "total_reduction": (share * pf[0], share * pf[1])}
