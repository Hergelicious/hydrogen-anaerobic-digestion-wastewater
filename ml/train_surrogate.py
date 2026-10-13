"""Train the screening surrogate and report one consistent set of metrics.

    python ml/train_surrogate.py            (from the repository root)

Protocol (Methods; Supplementary Note S14b)
    target   eta = eta_DF / max(eta_DF) x 0.55, i.e. the synthetic efficiency index rescaled to
             the mesophilic ceiling (2.2 mol H2 per mol glucose, 55% of the Thauer maximum),
             then logit-transformed
    inputs   z-scored (StandardScaler fitted on the training split)
    split    80/20 random train/test split, seed 42; the test split is not used for fitting
             or for choosing alpha
    alpha    five-fold RidgeCV on the training split over 10^-6 ... 10^6 for the eight-feature
             model; the same alpha is used for the three-feature model, so the comparison
             isolates the effect of removing five inputs
    metrics  held-out R2, RMSE and MAE, and five-fold cross-validated R2 on the training split
             (shuffled, seed 42), all on the efficiency scale after back-transformation;
             RMSE in logit units is also reported

The deployed three-sensor surrogate (OLR, ammonium, alkalinity) is the Medium envelope model
(OLR 1.0-5.0 kg COD m-3 d-1), whose training range contains the Gabal El-Asfar design OLR
(1.0 kg COD m-3 d-1). The Low envelope is fitted with the same protocol for comparison. The
High envelope dataset is not included in this release.

Also reported for the deployed model: sensitivity to sensor noise (each input multiplied by an
independent U(0.7, 1.3) factor on every training-envelope row; seed 42).

Outputs: ml/results/surrogate_metrics.json and ml/results/deployed_surrogate.json
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from scipy.special import expit, logit
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, train_test_split
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = {"low": os.path.join(HERE, "data", "DF_training_low.csv"),
        "medium": os.path.join(HERE, "data", "DF_training_medium.csv")}
OUT = os.path.join(HERE, "results")

F8 = ["DF_feed_T_degC", "DF_feed_pH", "DF_HRT_days", "DF_OLR_kgCOD_m3_day",
      "Pretreatment_severity_pct", "NH4_mg_L", "SO4_mg_L", "Alkalinity_mgCaCO3_L"]
F3 = ["DF_OLR_kgCOD_m3_day", "NH4_mg_L", "Alkalinity_mgCaCO3_L"]
ETA_CAP = 0.55
SEED = 42
ALPHAS = np.logspace(-6, 6, 13)
DEPLOYED = "medium"


def target(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, float]:
    raw_max = float(df["eta_DF"].max())
    eta = df["eta_DF"].to_numpy(float) / raw_max * ETA_CAP
    return eta, logit(np.clip(eta, 1e-5, 1 - 1e-5)), raw_max


def fit(X, z, alpha):
    sc = StandardScaler().fit(X)
    return sc, Ridge(alpha=alpha).fit(sc.transform(X), z)


def cv_r2(X, eta, z, alpha):
    kf = KFold(5, shuffle=True, random_state=SEED)
    s = []
    for a, b in kf.split(X):
        sc, m = fit(X[a], z[a], alpha)
        s.append(r2_score(eta[b], expit(m.predict(sc.transform(X[b])))))
    return float(np.mean(s)), float(np.std(s, ddof=1))


def evaluate(df: pd.DataFrame) -> dict:
    eta, z, raw_max = target(df)
    idx = np.arange(len(df))
    tr, te = train_test_split(idx, test_size=0.2, random_state=SEED)
    X8 = df[F8].to_numpy(float)
    sc8 = StandardScaler().fit(X8[tr])
    alpha = float(RidgeCV(alphas=ALPHAS, cv=5).fit(sc8.transform(X8[tr]), z[tr]).alpha_)
    out = {"n_rows": int(len(df)), "n_train": int(len(tr)), "n_test": int(len(te)),
           "eta_raw_max": raw_max, "eta_mean": float(eta.mean()), "alpha": alpha}
    for k, F in (("k8", F8), ("k3", F3)):
        X = df[F].to_numpy(float)
        sc, m = fit(X[tr], z[tr], alpha)
        pz = m.predict(sc.transform(X[te]))
        pe = expit(pz)
        cvm, cvs = cv_r2(X[tr], eta[tr], z[tr], alpha)
        out[k] = {
            "features": F,
            "test_r2": float(r2_score(eta[te], pe)),
            "test_rmse": float(mean_squared_error(eta[te], pe) ** 0.5),
            "test_mae": float(mean_absolute_error(eta[te], pe)),
            "test_rmse_logit": float(mean_squared_error(z[te], pz) ** 0.5),
            "train_r2": float(r2_score(eta[tr], expit(m.predict(sc.transform(X[tr]))))),
            "cv_r2_mean": cvm, "cv_r2_sd": cvs,
            "coef": dict(zip(F, map(float, m.coef_))), "intercept": float(m.intercept_),
            "scaler_mean": dict(zip(F, map(float, sc.mean_))),
            "scaler_sd": dict(zip(F, map(float, sc.scale_))),
            "input_range": {f: [float(df[f].min()), float(df[f].max())] for f in F},
        }
    out["k3_retention_cv"] = out["k3"]["cv_r2_mean"] / out["k8"]["cv_r2_mean"]
    out["k3_retention_test"] = out["k3"]["test_r2"] / out["k8"]["test_r2"]
    return out


def noise_test(df: pd.DataFrame, model: dict, rel: float = 0.30) -> dict:
    rng = np.random.default_rng(SEED)
    X = df[F3].to_numpy(float)
    mu = np.array([model["scaler_mean"][f] for f in F3])
    sd = np.array([model["scaler_sd"][f] for f in F3])
    b = np.array([model["coef"][f] for f in F3])

    def pred(x):
        return np.minimum(ETA_CAP, expit(model["intercept"] + ((x - mu) / sd) @ b))

    clean = pred(X)
    noisy = pred(X * rng.uniform(1 - rel, 1 + rel, X.shape))
    ratio = noisy / clean
    return {"perturbation": rel, "n": int(len(X)), "mean_bias": float(ratio.mean() - 1.0),
            "cv": float(ratio.std(ddof=1) / ratio.mean()),
            "ratio_p5": float(np.percentile(ratio, 5)), "ratio_p95": float(np.percentile(ratio, 95)),
            "input_cv": float(np.sqrt(((2 * rel) ** 2) / 12.0))}


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    res = {}
    for name, path in DATA.items():
        res[name] = evaluate(pd.read_csv(path))
    dep = res[DEPLOYED]["k3"]
    deployed = {"envelope": DEPLOYED, "features": F3, "alpha": res[DEPLOYED]["alpha"],
                "intercept": dep["intercept"], "coef": dep["coef"],
                "scaler_mean": dep["scaler_mean"], "scaler_sd": dep["scaler_sd"],
                "input_range": dep["input_range"], "eta_cap": ETA_CAP,
                "inverse_transform": "eta = min(eta_cap, 1 / (1 + exp(-(intercept + sum(coef * z)))))",
                "z": "(x - scaler_mean) / scaler_sd"}
    res["noise_test_deployed"] = noise_test(pd.read_csv(DATA[DEPLOYED]), dep)
    with open(os.path.join(OUT, "surrogate_metrics.json"), "w") as f:
        json.dump(res, f, indent=2)
    with open(os.path.join(OUT, "deployed_surrogate.json"), "w") as f:
        json.dump(deployed, f, indent=2)
    for name in DATA:
        r = res[name]
        print(f"{name}: alpha {r['alpha']:g}; eta mean {r['eta_mean']:.3f}")
        for k in ("k8", "k3"):
            m = r[k]
            print(f"  {k}: test R2 {m['test_r2']:.3f}  RMSE {m['test_rmse']:.4f}  MAE {m['test_mae']:.4f}"
                  f"  CV-R2 {m['cv_r2_mean']:.3f} +/- {m['cv_r2_sd']:.3f}  (RMSE logit {m['test_rmse_logit']:.3f})")
        print(f"  k3/k8 CV-R2 retention {100 * r['k3_retention_cv']:.1f}%")
    n = res["noise_test_deployed"]
    print(f"noise +/-30% (deployed): mean bias {100 * n['mean_bias']:+.2f}%, CV {100 * n['cv']:.1f}%, "
          f"90% of predictions within {100 * (n['ratio_p5'] - 1):+.0f}% to {100 * (n['ratio_p95'] - 1):+.0f}% "
          f"(input s.d. {100 * n['input_cv']:.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
