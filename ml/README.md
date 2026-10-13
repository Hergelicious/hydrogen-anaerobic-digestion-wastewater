# ml/

Synthetic training data and the scripts that train and screen the surrogate.

```
data/DF_training_low.csv      Low envelope (OLR 0.5–1.0 kg COD m-3 d-1), 500 rows
data/DF_training_medium.csv   Medium envelope (OLR 1.0–5.0 kg COD m-3 d-1), 500 rows
train_surrogate.py            deployed three-sensor surrogate and its metrics
screen_models.py              eleven-algorithm screening (Supplementary Tables 14 and 19)
results/                      surrogate_metrics.json, deployed_surrogate.json,
                              model_screening_<envelope>.csv, case_study.json,
                              case_study_rows.csv (500 Monte Carlo rows of the case study)
```

Each data file holds the eight surrogate inputs (DF feed temperature, pH, HRT, OLR, pretreatment
severity, ammonium, sulfate, alkalinity) and `eta_DF`, the synthetic efficiency index as generated
for that envelope (parameter ranges in Supplementary Table 13). Before fitting, the index is
rescaled to the 0.55 mesophilic ceiling by dividing by its maximum in the envelope; because absolute
efficiency in the framework is set by the pilot-derived constant, this rescaling affects only the
shape of the predicted response.

`train_surrogate.py`: 80/20 random split (seed 42); alpha by five-fold RidgeCV on the training rows
for the eight-feature model, used for both models; held-out R2, RMSE and MAE and five-fold CV-R2 on
the efficiency scale. The deployed surrogate is the Medium envelope three-feature model, whose
training range contains the Gabal El-Asfar design OLR. Its coefficients and scaler are copied into
`whydt/parameters.py`; `tests/test_framework.py` checks that they match `results/deployed_surrogate.json`.

`screen_models.py` reproduces the eleven-algorithm screening of Supplementary Tables 14 and 19 (raw
index, Ridge alpha 1.0, CV on the full dataset). XGBoost and CatBoost rows need those packages
(`pip install xgboost catboost`); XGBoost results vary slightly with the library version.

The High envelope dataset (OLR 5–20 kg COD m-3 d-1; Supplementary Tables 24–27) is not part of the
deployed surrogate or of any reported case-study, LCA, TEA or bound result.
