"""Algorithm screening on the synthetic training envelopes (Supplementary Tables 14 and 19).

    python ml/screen_models.py            (from the repository root)

Protocol: raw synthetic efficiency index as target;
pipeline mean imputer -> StandardScaler -> regressor; 80/20 random split (seed 42) for train and
test R2, RMSE and MAE; five-fold cross-validated R2 on the full envelope dataset. XGBoost and
CatBoost rows are computed when those packages are installed and skipped otherwise.
Writes ml/results/model_screening_<envelope>.csv.
"""
from __future__ import annotations

import os

import pandas as pd
from sklearn.ensemble import (AdaBoostRegressor, ExtraTreesRegressor, GradientBoostingRegressor,
                              RandomForestRegressor)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

HERE = os.path.dirname(os.path.abspath(__file__))
F8 = ["DF_feed_T_degC", "DF_feed_pH", "DF_HRT_days", "DF_OLR_kgCOD_m3_day",
      "Pretreatment_severity_pct", "NH4_mg_L", "SO4_mg_L", "Alkalinity_mgCaCO3_L"]


def models() -> dict:
    m = {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0),
        "Lasso Regression": Lasso(alpha=0.001),
        "KNN Regressor": KNeighborsRegressor(n_neighbors=5),
        "Random Forest": RandomForestRegressor(n_estimators=300, random_state=42),
        "Extra Trees": ExtraTreesRegressor(n_estimators=300, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(random_state=42),
        "AdaBoost": AdaBoostRegressor(random_state=42),
        "SVR (RBF)": SVR(kernel="rbf", C=10, epsilon=0.01),
    }
    try:
        from xgboost import XGBRegressor
        m["XGBoost"] = XGBRegressor(n_estimators=300, learning_rate=0.05, random_state=42, verbosity=0)
    except ImportError:
        pass
    try:
        from catboost import CatBoostRegressor
        m["CatBoost"] = CatBoostRegressor(iterations=300, depth=6, learning_rate=0.05, verbose=0, allow_writing_files=False,
                                          random_state=42)
    except ImportError:
        pass
    return m


def screen(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    X, y = df[F8], df["eta_DF"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    rows = []
    for name, est in models().items():
        p = Pipeline([("imp", SimpleImputer()), ("sc", StandardScaler()), ("m", est)]).fit(Xtr, ytr)
        pte = p.predict(Xte)
        rows.append({"Model": name, "R2 Train": r2_score(ytr, p.predict(Xtr)), "R2 Test": r2_score(yte, pte),
                     "CV R2 Mean": cross_val_score(p, X, y, cv=5, scoring="r2").mean(),
                     "RMSE": mean_squared_error(yte, pte) ** 0.5, "MAE": mean_absolute_error(yte, pte)})
    return pd.DataFrame(rows).sort_values("R2 Test", ascending=False)


def main() -> int:
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    for env in ("low", "medium"):
        t = screen(os.path.join(HERE, "data", f"DF_training_{env}.csv"))
        t.to_csv(os.path.join(HERE, "results", f"model_screening_{env}.csv"), index=False, float_format="%.4f")
        print(f"\n{env} envelope\n" + t.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
