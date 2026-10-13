"""Recompute the screening-framework values reported in the manuscript and compare them
with the reported figures.

Run from the repository root:
    python scripts/reproduce_manuscript_values.py

Exit status is non-zero if any value falls outside its tolerance. Tolerances reflect
the rounding of the reported values. The Gabal El-Asfar case study is recomputed here
(whydt.case_study, n = 500, seed 42); surrogate metrics are read from
ml/results/surrogate_metrics.json, written by ml/train_surrogate.py.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from whydt import parameters as P  # noqa: E402
from whydt import process, lca, tea, bounds  # noqa: E402


def checks():
    import json
    from whydt import case_study as cs
    ref = process.energy_chain(P.REF_H2_M3D)
    case = cs.run()
    att = process.gea_attainment()
    pump = process.pumping_sensitivity()
    det = bounds.benchmark()
    alloc = bounds.energy_allocation()
    gatt = bounds.gea_attainment()
    caps = tea.capex_boundaries()
    oat = tea.one_at_a_time()
    lmc = tea.lcoh_monte_carlo()
    sl_lo, sl_hi = lca.sludge_scenario_range()
    sc_lo, sc_hi = lca.sludge_credit_range()
    bus_lo, bus_hi = tea.diesel_credit_bus_range()
    nb_lo, nb_hi = tea.net_lcoh_bus_range()
    ab_lo, ab_hi = tea.abatement_cost_range()
    dl_lo, dl_hi = tea.delivered_lcoh_range()
    dg_lo, dg_hi = tea.delivered_lcoh_range(gross=True)
    no_credit = lca.carbon_intensity(include_fossil_credit=False)
    si = lca.site_integration()
    alt = lca.alternative_reading()
    seas = cs.seasonal_light_modulation()
    with open(os.path.join(os.path.dirname(__file__), "..", "ml", "results", "surrogate_metrics.json")) as f:
        sm = json.load(f)
    dep, low = sm["medium"], sm["low"]
    rows = [
        # label, computed, reported, tolerance, unit
        # --- pilot-derived constant and case study (whydt.case_study; n = 500, seed 42)
        ("Pilot specific yield", process.pilot_specific_yield_m3_per_kg_cod() * 1000, 163, 0.5, "mL H2 g-1 COD"),
        ("Pilot-derived eta_DF", process.pilot_eta(), 0.349, 0.0005, "-"),
        ("Thauer yield, volume basis", process.thauer_m3_per_kg_cod(), 0.467, 0.0005, "m3 kg-1 COD"),
        ("Alternative reading, eta_DF", cs.alternative_reading_eta(), 0.050, 0.0005, "-"),
        ("Alternative reading, fold lower", cs.ETA_PILOT / cs.alternative_reading_eta(), 7.04, 0.005, "-"),
        ("Case study mean eta_DF", case.eta_df_mean, 0.349, 0.0005, "-"),
        ("Case study DF output", case.h2_df_m3d, P.REF_H2_DF_M3D, 0.5, "m3 d-1"),
        ("Case study PF output", case.h2_pf_m3d, P.REF_H2_PF_M3D, 0.5, "m3 d-1"),
        ("Case study total output", case.h2_m3d, P.REF_H2_M3D, 0.5, "m3 d-1"),
        ("Case study 5th percentile", case.h2_m3d_p5, P.REF_H2_P5_M3D, 0.5, "m3 d-1"),
        ("Case study 95th percentile", case.h2_m3d_p95, P.REF_H2_P95_M3D, 0.5, "m3 d-1"),
        ("Case study mean PF efficiency", case.eta_pf_mean, 0.199, 0.0005, "-"),
        ("DF output, closed form", process.df_output_m3d(cs.ETA_PILOT), 13514, 0.5, "m3 d-1"),
        ("Total output", P.REF_H2_M3D, 16400, 10, "m3 d-1"),
        ("H2 mass", ref.h2_kg_d, 1474, 0.5, "kg d-1"),
        ("Annual H2 (TEA/LCA basis)", ref.h2_kg_yr, 537977, 1, "kg yr-1"),
        ("Gross chemical energy (LHV)", ref.gross_mwh_d, 49.1, 0.05, "MWh d-1"),
        ("Fuel-cell electricity (50%)", ref.fc_mwh_d, 24.6, 0.05, "MWh d-1"),
        ("Net usable electricity", ref.net_mwh_d, 23.8, 0.05, "MWh d-1"),
        ("Operational leverage ratio", ref.leverage_ratio, 29.7, 0.05, "-"),
        ("Parasitic electricity per kg", ref.parasitic_kwh_per_kg, 0.543, 0.0005, "kWh kg-1"),
        ("PF share of output", att["pf_share"], 0.18, 0.005, "-"),
        ("DF share of output (DF-only option)", att["df_share"], 0.82, 0.005, "-"),
        ("Total-to-DF ratio", att["total_to_df"], 1.21, 0.005, "-"),
        ("DF attainment (captured COD)", 100 * att["attainment_df"], 34.9, 0.05, "%"),
        ("PF attainment (captured COD)", 100 * att["attainment_pf"], 7.4, 0.05, "%"),
        ("Total attainment (captured COD)", 100 * att["attainment_total"], 42.4, 0.05, "%"),
        ("COD recovered in hydrogen", 100 * att["cod_in_h2_share"], 14.2, 0.05, "%"),
        ("Specific yield, DF-PF", att["specific_yield_ml_per_g_cod"] * 1000, 198, 0.5, "mL H2 g-1 COD"),
        ("Volumetric productivity, DF", process.volumetric_productivity(P.REF_H2_DF_M3D), 0.16, 0.005, "m3 m-3 d-1"),
        ("Volumetric productivity, DF-PF", process.volumetric_productivity(P.REF_H2_M3D), 0.20, 0.005, "m3 m-3 d-1"),
        ("DF yield, mol H2 per mol glucose", P.REF_ETA_DF * 4, 1.40, 0.005, "mol mol-1"),
        ("Pumping sensitivity: parasitic load", pump["parasitic_mwh_d"], 8.25, 0.005, "MWh d-1"),
        ("Pumping sensitivity: net electricity", pump["net_mwh_d"], 16.3, 0.05, "MWh d-1"),
        ("Pumping sensitivity: leverage ratio", pump["leverage_ratio"], 2.0, 0.05, "-"),
        ("Pumping sensitivity: carbon intensity", pump["carbon_intensity"], -7.4, 0.05, "kg CO2-eq kg-1"),
        ("Pumping sensitivity: added LCOH", pump["lcoh_add"], 0.25, 0.005, "US$ kg-1"),
        # --- life cycle assessment
        ("LCA-boundary electricity per kg", lca.lca_electricity_kwh_per_kg(), 1.493, 0.0005, "kWh kg-1"),
        ("Electricity burden", lca.electricity_burden(), 0.688, 0.0005, "kg CO2-eq kg-1"),
        ("Embodied burden", lca.embodied_burden(), 0.876, 0.0005, "kg CO2-eq kg-1"),
        ("Annual embodied carbon", lca.annual_embodied_t(), 471, 0.5, "t CO2-eq yr-1"),
        ("Fossil transport fuel credit", lca.fossil_credit(), 11.28, 0.005, "kg CO2-eq kg-1"),
        ("Net carbon intensity (baseline)", lca.carbon_intensity(), -9.72, 0.005, "kg CO2-eq kg-1"),
        ("Captured COD per kg H2", lca.sludge_cod_per_kg_h2(), 56.17, 0.005, "kg COD kg-1"),
        ("Sludge credit, low EF", sc_lo, 0.56, 0.005, "kg CO2-eq kg-1"),
        ("Sludge credit, high EF", sc_hi, 1.97, 0.005, "kg CO2-eq kg-1"),
        ("With sludge credit (low EF)", sl_lo, -10.28, 0.005, "kg CO2-eq kg-1"),
        ("With sludge credit (high EF)", sl_hi, -11.68, 0.005, "kg CO2-eq kg-1"),
        ("Without fossil credit", no_credit, 1.56, 0.005, "kg CO2-eq kg-1"),
        ("RED II saving without credit", lca.red_ii_saving(no_credit), 0.86, 0.005, "-"),
        ("Grid 2035 (0.30 kg kWh-1)", lca.carbon_intensity(grid_ef=0.30), -9.96, 0.005, "kg CO2-eq kg-1"),
        ("Grid 2035 (0.35 kg kWh-1)", lca.carbon_intensity(grid_ef=0.35), -9.88, 0.005, "kg CO2-eq kg-1"),
        ("Annual net mitigation", lca.annual_mitigation_t(), 5230, 5, "t CO2-eq yr-1"),
        ("Carbon payback", lca.carbon_payback_yr(), 1.80, 0.005, "yr"),
        ("Mitigation, conservative counterfactual", lca.conservative_mitigation_t(), 2260, 5, "t CO2-eq yr-1"),
        ("Carbon payback, conservative", lca.conservative_payback_yr(), 4.2, 0.05, "yr"),
        ("LCA uncertainty proxy (1 sigma)", lca.uncertainty_proxy(), 1.8, 0.05, "kg CO2-eq kg-1"),
        ("Low-yield bound (x1/7.04)", lca.low_yield_bound(7.04), -0.3, 0.05, "kg CO2-eq kg-1"),
        ("Alternative reading: total output", alt["h2_m3d"], 4800, 1, "m3 d-1"),
        ("Alternative reading: fold lower, total", alt["fold_lower_total"], 3.4, 0.05, "-"),
        ("Alternative reading: carbon intensity, PF unchanged", alt["ci_pf_unchanged"], -5.9, 0.05, "kg CO2-eq kg-1"),
        ("Case study 90% interval, annual low", P.REF_H2_P5_M3D * P.H2_DENSITY * 365, 386700, 50, "kg yr-1"),
        ("Case study 90% interval, annual high", P.REF_H2_P95_M3D * P.H2_DENSITY * 365, 702900, 50, "kg yr-1"),
        ("Case study s.d. of total output", case.h2_m3d_sd, 2842, 0.5, "m3 d-1"),
        ("Deployment threshold flow (LCOH 7.50)", tea.deployment_threshold_flow(), 195000, 500, "m3 d-1"),
        ("Carbon parity price vs grey (US$1.75)", tea.carbon_parity_price(), 388, 0.5, "US$ t-1"),
        ("City LCOH at 3,500 m3 d-1 (Supp. Table 3)", tea.scaled_net_lcoh_by_output(3500), 9.2, 0.05, "US$ kg-1"),
        ("City LCOH at 4,000 m3 d-1 (Supp. Table 3)", tea.scaled_net_lcoh_by_output(4000), 8.8, 0.05, "US$ kg-1"),
        ("City LCOH at 8,500 m3 d-1 (Supp. Table 3)", tea.scaled_net_lcoh_by_output(8500), 6.8, 0.05, "US$ kg-1"),
        ("City LCOH at 9,500 m3 d-1 (Supp. Table 3)", tea.scaled_net_lcoh_by_output(9500), 6.6, 0.05, "US$ kg-1"),
        ("Fleet: refuse trucks at 8 kg d-1", ref.h2_kg_d / 8.0, 184, 0.5, "trucks"),
        ("Diesel displaced, 1:1 LHV (3.35 L kg-1)", ref.h2_kg_d * 120.0 / 35.8, 4940, 10, "L d-1"),
        ("Fossil CO2 displaced, RED II basis", ref.h2_kg_yr * lca.fossil_credit() / 1000, 6068, 1, "t yr-1"),
        # --- techno-economic analysis
        ("Capital recovery factor", tea.crf(), 0.0944, 0.00005, "-"),
        ("Gross LCOH", tea.gross_lcoh(), 8.37, 0.005, "US$ kg-1"),
        ("Diesel displaced per kg H2", tea.diesel_litres_per_kg_h2(), 5.0, 0.005, "L kg-1"),
        ("Diesel credit", tea.diesel_credit(), 2.85, 0.005, "US$ kg-1"),
        ("Annual avoided diesel expenditure", tea.annual_diesel_savings() / 1e6, 1.533, 0.0005, "US$ M yr-1"),
        ("Offtake revenue (alternative)", tea.offtake_revenue() / 1e6, 2.69, 0.005, "US$ M yr-1"),
        ("Net-effective LCOH", tea.net_lcoh(), 5.52, 0.005, "US$ kg-1"),
        ("Diesel credit, bus range low", bus_lo, 2.22, 0.005, "US$ kg-1"),
        ("Diesel credit, bus range high", bus_hi, 3.26, 0.005, "US$ kg-1"),
        ("Net LCOH, bus range low", nb_lo, 5.11, 0.005, "US$ kg-1"),
        ("Net LCOH, bus range high", nb_hi, 6.15, 0.005, "US$ kg-1"),
        ("Gross LCOH, shared boundary", caps["shared"]["gross"], 10.67, 0.005, "US$ kg-1"),
        ("Net LCOH, shared boundary", caps["shared"]["net"], 7.82, 0.005, "US$ kg-1"),
        ("Gross LCOH, full boundary", caps["full"]["gross"], 12.86, 0.005, "US$ kg-1"),
        ("Net LCOH, full boundary", caps["full"]["net"], 10.01, 0.005, "US$ kg-1"),
        ("Net LCOH, CAPEX -25%", oat["capex"][0], 4.45, 0.005, "US$ kg-1"),
        ("Net LCOH, CAPEX +25%", oat["capex"][1], 6.59, 0.005, "US$ kg-1"),
        ("Net LCOH, WACC 5%", oat["wacc"][0], 4.88, 0.005, "US$ kg-1"),
        ("Net LCOH, WACC 12%", oat["wacc"][1], 7.31, 0.005, "US$ kg-1"),
        ("Net LCOH, yield +35%", oat["yield"][0], 3.35, 0.005, "US$ kg-1"),
        ("Net LCOH, yield -35%", oat["yield"][1], 10.03, 0.005, "US$ kg-1"),
        ("Propagated LCOH, median", lmc["median"], 5.7, 0.05, "US$ kg-1"),
        ("Propagated LCOH, 5th pct", lmc["p5"], 3.5, 0.05, "US$ kg-1"),
        ("Propagated LCOH, 95th pct", lmc["p95"], 9.4, 0.05, "US$ kg-1"),
        ("LCOH variance share, yield", lmc["variance_share"]["hydrogen yield"], 0.78, 0.005, "-"),
        ("LCOH variance share, CAPEX", lmc["variance_share"]["CAPEX"], 0.16, 0.005, "-"),
        ("LCOH variance share, WACC", lmc["variance_share"]["WACC"], 0.07, 0.005, "-"),
        ("Carbon-adjusted LCOH, US$25 t-1", tea.carbon_adjusted_lcoh(25), 5.28, 0.005, "US$ kg-1"),
        ("Carbon-adjusted LCOH, US$50 t-1", tea.carbon_adjusted_lcoh(50), 5.03, 0.005, "US$ kg-1"),
        ("Carbon-adjusted LCOH, US$100 t-1", tea.carbon_adjusted_lcoh(100), 4.55, 0.005, "US$ kg-1"),
        ("SMR carbon-intensity differential", tea.smr_ci_differential(), 20.0, 0.05, "kg CO2-eq kg-1"),
        ("Abatement cost, low", ab_lo, 151, 0.5, "US$ t-1"),
        ("Abatement cost, high", ab_hi, 226, 0.5, "US$ t-1"),
        ("LCCA vs SMR", tea.lcca("SMR"), 191, 0.5, "US$ t-1"),
        ("LCCA vs blue H2", tea.lcca("Blue H2"), 247, 0.5, "US$ t-1"),
        ("LCCA vs green electrolysis", tea.lcca("Green electrolysis"), 95, 0.5, "US$ t-1"),
        ("Delivered LCOH, low", dl_lo, 6.32, 0.005, "US$ kg-1"),
        ("Delivered LCOH, high", dl_hi, 7.62, 0.005, "US$ kg-1"),
        ("Delivered LCOH, producer gate, low", dg_lo, 9.17, 0.005, "US$ kg-1"),
        ("Delivered LCOH, producer gate, high", dg_hi, 10.47, 0.005, "US$ kg-1"),
        # --- model-independent bound
        ("Thauer yield", bounds.thauer_yield_kg_per_kg_cod() * 1000, 42.0, 0.05, "g H2 kg-1 COD"),
        ("Electron-balance limit", bounds.electron_balance_yield_kg_per_kg_cod() * 1000, 126, 0.5, "g H2 kg-1 COD"),
        ("Global COD flux, low", det["global_cod_mt"][0], 106, 0.5, "Mt yr-1"),
        ("Global COD flux, high", det["global_cod_mt"][1], 228, 0.5, "Mt yr-1"),
        ("DF benchmark H2, low", det["benchmark_h2_mt"][0], 4.4, 0.05, "Mt H2 yr-1"),
        ("DF benchmark H2, high", det["benchmark_h2_mt"][1], 9.6, 0.05, "Mt H2 yr-1"),
        ("DF energy at benchmark", alloc["MJ_per_kg_COD"]["DF"], 5.04, 0.005, "MJ kg-1 COD"),
        ("AD energy", alloc["MJ_per_kg_COD"]["AD"], 12.53, 0.005, "MJ kg-1 COD"),
        ("AD-to-DF energy ratio", alloc["AD_to_DF_ratio"], 2.5, 0.05, "-"),
        ("DF share of thermal", alloc["share_of_thermal"]["DF"], 0.36, 0.005, "-"),
        ("AD share of thermal", alloc["share_of_thermal"]["AD"], 0.90, 0.005, "-"),
        ("Thermal global energy, low", alloc["global_EJ"]["thermal"][0], 1.47, 0.005, "EJ yr-1"),
        ("Thermal global energy, high", alloc["global_EJ"]["thermal"][1], 3.17, 0.005, "EJ yr-1"),
        ("AD global energy, low", alloc["global_EJ"]["AD"][0], 1.32, 0.005, "EJ yr-1"),
        ("AD global energy, high", alloc["global_EJ"]["AD"][1], 2.86, 0.005, "EJ yr-1"),
        ("DF global energy, low", alloc["global_EJ"]["DF"][0], 0.53, 0.005, "EJ yr-1"),
        ("DF global energy, high", alloc["global_EJ"]["DF"][1], 1.15, 0.005, "EJ yr-1"),
        ("GEA yield on captured COD", gatt["kg_h2_per_kg_cod"], 0.0178, 0.00005, "kg kg-1"),
        ("GEA share of DF benchmark", gatt["fraction_of_benchmark"], 0.424, 0.0005, "-"),
        # --- site integration at Gabal El-Asfar (Supplementary Note S16b; one at a time)
        ("COD leaving as hydrogen", si["cod_to_h2_kg_d"], 11800, 50, "kg COD d-1"),
        ("Methane forgone (upper bound)", si["biogas_forgone_ch4_mwh_d"], 41.0, 0.05, "MWh d-1"),
        ("CHP electricity forgone, low", si["biogas_forgone_elec_mwh_d"][0], 14.4, 0.05, "MWh d-1"),
        ("CHP electricity forgone, high", si["biogas_forgone_elec_mwh_d"][1], 18.1, 0.05, "MWh d-1"),
        ("Added carbon intensity, biogas, low", si["biogas_forgone_added_ci"][0], 4.5, 0.05, "kg CO2-eq kg-1"),
        ("Added carbon intensity, biogas, high", si["biogas_forgone_added_ci"][1], 5.6, 0.05, "kg CO2-eq kg-1"),
        ("Carbon intensity with biogas forgone, 35% CHP", si["biogas_forgone_ci"][0], -5.2, 0.05, "kg CO2-eq kg-1"),
        ("Carbon intensity with biogas forgone, 44% CHP", si["biogas_forgone_ci"][1], -4.1, 0.05, "kg CO2-eq kg-1"),
        ("Net electricity gain with biogas forgone, low", si["biogas_forgone_net_elec_gain_mwh_d"][1], 6, 0.5, "MWh d-1"),
        ("Net electricity gain with biogas forgone, high", si["biogas_forgone_net_elec_gain_mwh_d"][0], 9, 0.5, "MWh d-1"),
        ("VFA concentration electricity, 5 bar", si["concentration_mwh_d"][0], 7, 0.5, "MWh d-1"),
        ("VFA concentration electricity, 15 bar", si["concentration_mwh_d"][1], 21, 0.5, "MWh d-1"),
        ("Added carbon intensity, concentration, 5 bar", si["concentration_added_ci"][0], 2.2, 0.05, "kg CO2-eq kg-1"),
        ("Added carbon intensity, concentration, 15 bar", si["concentration_added_ci"][1], 6.7, 0.05, "kg CO2-eq kg-1"),
        ("Carbon intensity with concentration, 5 bar", si["concentration_ci"][0], -7.5, 0.05, "kg CO2-eq kg-1"),
        ("Carbon intensity with concentration, 15 bar", si["concentration_ci"][1], -3.0, 0.05, "kg CO2-eq kg-1"),
        ("Net electricity with concentration, 15 bar", si["concentration_net_elec_mwh_d"][1], 2, 0.5, "MWh d-1"),
        ("Net electricity with concentration, 5 bar", si["concentration_net_elec_mwh_d"][0], 17, 0.5, "MWh d-1"),
        # --- surrogate (ml/train_surrogate.py; deployed = Medium envelope, three features)
        ("Surrogate k=3 held-out R2", dep["k3"]["test_r2"], 0.67, 0.005, "-"),
        ("Surrogate k=3 held-out RMSE (eta)", dep["k3"]["test_rmse"], 0.067, 0.0005, "-"),
        ("Surrogate k=3 held-out MAE (eta)", dep["k3"]["test_mae"], 0.052, 0.0005, "-"),
        ("Surrogate k=3 CV-R2", dep["k3"]["cv_r2_mean"], 0.71, 0.005, "-"),
        ("Surrogate k=8 held-out R2", dep["k8"]["test_r2"], 0.68, 0.005, "-"),
        ("Surrogate k=8 held-out RMSE (eta)", dep["k8"]["test_rmse"], 0.066, 0.0005, "-"),
        ("Surrogate k=8 CV-R2", dep["k8"]["cv_r2_mean"], 0.71, 0.005, "-"),
        ("Surrogate CV-R2 s.d.", dep["k3"]["cv_r2_sd"], 0.03, 0.005, "-"),
        ("k=3 retention of k=8 CV-R2", dep["k3_retention_cv"], 1.00, 0.005, "-"),
        ("Low envelope k=3 CV-R2", low["k3"]["cv_r2_mean"], 0.42, 0.005, "-"),
        ("Low envelope k=8 CV-R2", low["k8"]["cv_r2_mean"], 0.42, 0.005, "-"),
        ("Ridge alpha", dep["alpha"], 10.0, 1e-9, "-"),
        ("Deployed OLR coefficient", dep["k3"]["coef"]["DF_OLR_kgCOD_m3_day"], P.BETA["OLR"], 0.00005, "-"),
        ("Deployed NH4 coefficient", dep["k3"]["coef"]["NH4_mg_L"], P.BETA["NH4"], 0.00005, "-"),
        ("Deployed ALK coefficient", dep["k3"]["coef"]["Alkalinity_mgCaCO3_L"], P.BETA["ALK"], 0.00005, "-"),
        ("Deployed intercept", dep["k3"]["intercept"], P.RIDGE_INTERCEPT, 0.00005, "-"),
        ("Sensor noise +/-30%: mean bias", sm["noise_test_deployed"]["mean_bias"], 0.010, 0.0005, "-"),
        ("Sensor noise +/-30%: CV", sm["noise_test_deployed"]["cv"], 0.18, 0.005, "-"),
        ("Winter PF reduction, low", seas["pf_reduction"][0], 0.17, 0.005, "-"),
        ("Winter PF reduction, high", seas["pf_reduction"][1], 0.32, 0.005, "-"),
        ("Winter integrated reduction, low", seas["total_reduction"][0], 0.03, 0.005, "-"),
        ("Winter integrated reduction, high", seas["total_reduction"][1], 0.06, 0.005, "-"),
    ]
    rows += comparison_checks()
    return rows


def comparison_checks():
    """Values of the comparison of hydrogen and methane (main text; Supplementary Notes S21-S23)."""
    import itertools
    from whydt import allocation as A, facilities as F, voi as V
    E = A.eta_scenarios()
    pk = A.per_kg_cod()
    corners = [A.per_kg_cod(f_ch4=a, chp=b, fc_bus_kg=c, slip=d) for a, b, c, d in itertools.product(
        P.CH4_CONVERSION_RANGE, P.CHP_ELEC_EFF_RANGE, P.FC_BUS_KG_PER_100KM_RANGE, P.UPGRADING_CH4_SLIP_RANGE)]
    lo = lambda k, g: min(r[k][g] for r in corners)
    hi = lambda k, g: max(r[k][g] for r in corners)
    rr = A.per_kg_cod_ranges()
    gp, gl = A.gea_table(eta=E["pilot"]), A.gea_table(eta=E["literature"])
    rp, rl = A.gea_ranges(eta=E["pilot"]), A.gea_ranges(eta=E["literature"])
    bio = A.biocng_alternative()
    nd = {u: A.configuration("C1", u, digesting=False) for u in ("fc", "bus")}
    cx70 = A.grid_crossover(); cx65 = A.grid_crossover(threshold=A.threshold_kg(0.65))
    grid = {"f_ch4": P.CH4_CONVERSION_RANGE, "chp": P.CHP_ELEC_EFF_RANGE, "h2_comp_kwh": P.H2_COMPRESSION_KWH_PER_KG,
            "ch4_loss": P.DIGESTER_CH4_LOSS_RANGE, "h2_leak": P.H2_LEAK_RANGE,
            "skim_lca_mwh_d": (P.PARASITIC_REF_MWH_D, P.LCA_ELECTRICITY_MWH_D), "embodied_t": (0.0, P.EMBODIED_TOTAL_T)}
    cxs = [A.grid_crossover(**dict(zip(grid, c))) for c in itertools.product(*grid.values())]
    q = P.REF_CAPTURED_COD_KGD / P.SKIM_FEED_COD_KG_M3
    heat = [q * 4.18 * (t - 25) * 0.3 / 3.6 / 1000 for t in (70, 90)]
    df_all = F.load_plants(global_south=False); gs = df_all[~df_all["high_income"]]
    top7 = gs["iso"].value_counts()
    fs = F.summary()
    df35 = F.load_plants(global_south=False, max_abs_lat=P.LATITUDE_SENSITIVITY_DEG); gs35 = df35[~df35["high_income"]]
    fs35 = F.summary(gs35)
    ranges82 = dict(V.RANGES, grid_ef=(min(v[1] for v in P.COUNTRY_INPUTS.values()), max(v[1] for v in P.COUNTRY_INPUTS.values())))
    sb82 = V.sobol(n=16384, seed=42, ranges=ranges82)
    be = {r: A.break_even_diesel_price(eta=e) for r, e in E.items()}
    bh = {r: A.break_even_h2_price(eta=e) for r, e in E.items()}
    beg = {"downstream": P.DOWNSTREAM_COST, "elec_price": P.ELECTRICITY_PRICE_RANGE, "fc_bus_kg": P.FC_BUS_KG_PER_100KM_RANGE,
           "f_ch4": P.CH4_CONVERSION_RANGE, "chp": P.CHP_ELEC_EFF_RANGE}
    be_all = [A.break_even_diesel_price(eta=e, **dict(zip(beg, c))) for e in E.values() for c in itertools.product(*beg.values())]
    lit = [k for k in fs if isinstance(fs[k], dict) and k.startswith("literature")]
    bb = A.battery_bus_alternative()
    ge = A.grid_electricity_per_kg()
    fc_vals = [A.configuration("C1", "fc", f_ch4=a_, chp=b_).value_usd_yr
               for a_ in P.CH4_CONVERSION_RANGE for b_ in P.CHP_ELEC_EFF_RANGE]
    bus_world = min(A.configuration("C1", "bus", diesel_price=1.56, downstream=d_).value_usd_yr for d_ in P.DOWNSTREAM_COST)
    sb = V.sobol(n=16384, seed=42)
    cd = V.conditional_on_yield(n=20000, seed=7)
    mex = A.configuration("C1", "bus", diesel_price=P.COUNTRY_INPUTS["MEX"][2]).value_usd_yr
    return [
        # --- per kg of COD turned into hydrogen (Fig. 1b; Supplementary Note S21.1)
        ("Hydrogen energy per kg COD", pk["energy_MJ"]["H2"], 15.0, 0.05, "MJ"),
        ("Methane energy per kg COD, low", lo("energy_MJ", "CH4"), 10.0, 0.05, "MJ"),
        ("Methane energy per kg COD, high", hi("energy_MJ", "CH4"), 12.5, 0.05, "MJ"),
        ("Hydrogen electricity per kg COD", pk["electricity_kWh"]["H2"], 2.08, 0.005, "kWh"),
        ("Methane electricity per kg COD, low", lo("electricity_kWh", "CH4"), 0.97, 0.005, "kWh"),
        ("Methane electricity per kg COD, high", hi("electricity_kWh", "CH4"), 1.53, 0.005, "kWh"),
        ("Electricity ratio, low", rr["electricity_kWh"][0], 1.36, 0.005, "-"),
        ("Electricity ratio, high", rr["electricity_kWh"][1], 2.14, 0.005, "-"),
        ("Hydrogen diesel per kg COD, low", lo("diesel_L", "H2"), 0.49, 0.005, "L"),
        ("Hydrogen diesel per kg COD, high", hi("diesel_L", "H2"), 0.71, 0.005, "L"),
        ("Biomethane diesel per kg COD, low", lo("diesel_L", "CH4"), 0.19, 0.005, "L"),
        ("Biomethane diesel per kg COD, high", hi("diesel_L", "CH4"), 0.24, 0.005, "L"),
        ("Diesel ratio, low", rr["diesel_L"][0], 2.04, 0.005, "-"),
        ("Diesel ratio, high", rr["diesel_L"][1], 3.80, 0.005, "-"),
        ("Energy ratio, low", rr["energy_MJ"][0], 1.20, 0.005, "-"),
        ("Energy ratio, high", rr["energy_MJ"][1], 1.50, 0.005, "-"),
        ("Energy ratio with 15% purification loss, low", 0.85 * rr["energy_MJ"][0], 1.02, 0.005, "-"),
        ("Electricity ratio with 15% loss, low", 0.85 * rr["electricity_kWh"][0], 1.16, 0.005, "-"),
        ("Diesel ratio with 15% loss, low", 0.85 * rr["diesel_L"][0], 1.73, 0.005, "-"),
        ("Share of COD as hydrogen, Thauer", 100 * A.skim_share(1.0), 33.6, 0.05, "%"),
        ("Share of COD as hydrogen, higher reading", 100 * A.skim_share(E["pilot"]), 11.7, 0.05, "%"),
        ("Share of COD as hydrogen, lower reading", 100 * A.skim_share(E["literature"]), 1.7, 0.05, "%"),
        ("Higher reading, specific yield", E["pilot"] * 0.042 / P.H2_DENSITY * 1000, 163, 0.5, "mL H2 g-1 COD"),
        ("Lower reading, specific yield", E["literature"] * 0.042 / P.H2_DENSITY * 1000, 23, 0.5, "mL H2 g-1 COD"),
        ("Chemical energy gain, Thauer, f = 1", 100 * A.chemical_energy_gain(1.0, 1.0), 6.6, 0.05, "%"),
        ("Chemical energy gain, Thauer, f = 0.8", 100 * A.chemical_energy_gain(1.0, 0.8), 13.3, 0.05, "%"),
        ("Chemical energy gain, pilot, f = 1", 100 * A.chemical_energy_gain(E["pilot"], 1.0), 2.3, 0.05, "%"),
        ("Chemical energy gain, pilot, f = 0.8", 100 * A.chemical_energy_gain(E["pilot"], 0.8), 4.7, 0.05, "%"),
        ("Thermal conversion energy per kg COD", P.THORNTON_MJ_PER_KG_COD, 13.9, 0.05, "MJ"),
        # --- configurations at Gabal El-Asfar (Fig. 2; Supplementary Table 45)
        ("Skimming reactor volume", A.skim_reactor_m3(), 4171, 0.5, "m3"),
        ("Skimming reactor share of design volume", A.skim_reactor_m3() / (P.REF_REACTOR_M3 + 20625), 0.04, 0.005, "-"),
        ("Skimmed H2, higher reading", gp["C1_bus"]["h2_kg_d"], 1215, 0.5, "kg d-1"),
        ("Skimmed H2, lower reading", gl["C1_bus"]["h2_kg_d"], 173, 0.5, "kg d-1"),
        ("COD diverted by skimming, pilot", gp["C1_bus"]["cod_diverted_kg_d"], 9720, 0.5, "kg COD d-1"),
        ("Photo-fermentation H2", gp["C2_bus"]["h2_kg_d"] - gp["C1_bus"]["h2_kg_d"], 259, 0.5, "kg d-1"),
        ("Fatty-acid COD diverted by the cascade", gp["C2_bus"]["cod_diverted_kg_d"] - gp["C1_bus"]["cod_diverted_kg_d"], 41396, 0.5, "kg COD d-1"),
        ("CHP forgone, skimming, low", rp["C1_fc"]["chp_forgone_mwh_d"][0], 9.5, 0.05, "MWh d-1"),
        ("CHP forgone, skimming, high", rp["C1_fc"]["chp_forgone_mwh_d"][1], 14.9, 0.05, "MWh d-1"),
        ("Net electricity, skimming, fuel cells, low", rp["C1_fc"]["net_electricity_mwh_d"][0], 4.6, 0.05, "MWh d-1"),
        ("Net electricity, skimming, fuel cells, high", rp["C1_fc"]["net_electricity_mwh_d"][1], 10.0, 0.05, "MWh d-1"),
        ("CHP forgone, cascade, low", rp["C2_fc"]["chp_forgone_mwh_d"][0], 50, 0.5, "MWh d-1"),
        ("CHP forgone, cascade, high", rp["C2_fc"]["chp_forgone_mwh_d"][1], 78, 0.5, "MWh d-1"),
        ("Net electricity, cascade, low", rp["C2_fc"]["net_electricity_mwh_d"][0], -76, 0.5, "MWh d-1"),
        ("Net electricity, cascade, high", rp["C2_fc"]["net_electricity_mwh_d"][1], -33, 0.5, "MWh d-1"),
        ("Net electricity, cascade returned, low", rp["C2r_fc"]["net_electricity_mwh_d"][0], -15, 0.5, "MWh d-1"),
        ("Net electricity, cascade returned, high", rp["C2r_fc"]["net_electricity_mwh_d"][1], 5, 0.5, "MWh d-1"),
        ("Net electricity, skimming, literature, low", rl["C1_fc"]["net_electricity_mwh_d"][0], 0.0, 0.05, "MWh d-1"),
        ("Net electricity, skimming, literature, high", rl["C1_fc"]["net_electricity_mwh_d"][1], 0.7, 0.05, "MWh d-1"),
        ("Cascade loss at lower reading, smallest", -rl["C2r_fc"]["net_electricity_mwh_d"][1], 4, 0.05, "MWh d-1"),
        ("Cascade loss at lower reading, largest", -rl["C2_fc"]["net_electricity_mwh_d"][0], 80, 0.5, "MWh d-1"),
        ("Emissions, skimming, buses (central)", gp["C1_bus"]["co2_t_yr"], -1700, 50, "t CO2-eq yr-1"),
        ("Emissions, skimming, buses, low", rp["C1_bus"]["co2_t_yr"][0], -3800, 50, "t CO2-eq yr-1"),
        ("Emissions, skimming, buses, high", rp["C1_bus"]["co2_t_yr"][1], 0, 50, "t CO2-eq yr-1"),
        ("Emissions, cascade, buses (central)", gp["C2_bus"]["co2_t_yr"], 6900, 50, "t CO2-eq yr-1"),
        ("Emissions, cascade, buses, low", rp["C2_bus"]["co2_t_yr"][0], -400, 50, "t CO2-eq yr-1"),
        ("Emissions, cascade, buses, high", rp["C2_bus"]["co2_t_yr"][1], 15500, 50, "t CO2-eq yr-1"),
        ("Emissions, cascade returned, low", rp["C2r_bus"]["co2_t_yr"][0], -2500, 50, "t CO2-eq yr-1"),
        ("Emissions, cascade returned, high", rp["C2r_bus"]["co2_t_yr"][1], 4100, 50, "t CO2-eq yr-1"),
        ("Value of skimmed hydrogen as electricity, low", rp["C1_fc"]["value_usd_yr"][0] / 1e6, 0.08, 0.005, "US$ M yr-1"),
        ("Value of skimmed hydrogen as electricity, high", rp["C1_fc"]["value_usd_yr"][1] / 1e6, 0.18, 0.005, "US$ M yr-1"),
        ("Diesel displaced by skimmed hydrogen", bio["h2_diesel_l_d"], 6100, 50, "L d-1"),
        ("Diesel displaced by biomethane alternative", bio["biocng_diesel_l_d"], 2100, 50, "L d-1"),
        ("Hydrogen-to-biomethane diesel ratio", bio["ratio"], 2.9, 0.05, "-"),
        ("Net value, skimming, buses, Egypt, low", rp["C1_bus"]["value_usd_yr"][0] / 1e6, -0.06, 0.005, "US$ M yr-1"),
        ("Net value, skimming, buses, Egypt, high", rp["C1_bus"]["value_usd_yr"][1] / 1e6, 0.03, 0.005, "US$ M yr-1"),
        ("Net value, skimming, buses, Mexico diesel price", mex / 1e6, 2.4, 0.05, "US$ M yr-1"),
        ("Net value, skimming, buses, Mexico diesel price, lower reading", A.configuration("C1", "bus", eta=E["literature"], diesel_price=P.COUNTRY_INPUTS["MEX"][2]).value_usd_yr / 1e6, 0.3, 0.05, "US$ M yr-1"),
        ("Operating-to-capital cost ratio", P.OPEX_TO_CAPEX, 0.090, 0.0005, "yr-1"),
        ("High-income plants excluded", len(df_all) - len(gs), 490, 0, "plants"),
        ("High-income economies among the large plants", df_all.loc[df_all["high_income"], "iso"].nunique(), 41, 0, "-"),
        ("Pretreatment heat, 70 C", heat[0], 33, 0.5, "MWh_th d-1"),
        ("Pretreatment heat, 90 C", heat[1], 47, 0.5, "MWh_th d-1"),
        ("Pretreatment heat share of CHP heat, low", 100 * heat[0] / 180, 18, 0.5, "%"),
        ("Pretreatment heat share of CHP heat, high", 100 * heat[1] / 180, 26, 0.5, "%"),
        # --- carbon intensity (Fig. 3; Supplementary Note S21.5)
        ("Threshold, 65% saving", A.threshold_kg(0.65), 3.95, 0.005, "kg CO2-eq kg-1"),
        ("Threshold, 70% saving", A.threshold_kg(0.70), 3.38, 0.005, "kg CO2-eq kg-1"),
        ("Attributional intensity, buses, pilot, low", rp["C1_bus"]["ci_attributional"][0], 1.50, 0.005, "kg CO2-eq kg-1"),
        ("Attributional intensity, buses, pilot, high", rp["C1_bus"]["ci_attributional"][1], 3.27, 0.005, "kg CO2-eq kg-1"),
        ("Consequential intensity, buses, pilot, low", rp["C1_bus"]["ci_consequential"][0], 2.66, 0.005, "kg CO2-eq kg-1"),
        ("Consequential intensity, buses, pilot, high", rp["C1_bus"]["ci_consequential"][1], 11.30, 0.005, "kg CO2-eq kg-1"),
        ("Consequential intensity, buses, pilot (central)", gp["C1_bus"]["ci_consequential"], 7.39, 0.005, "kg CO2-eq kg-1"),
        ("Grid crossover, 70%", cx70, 0.29, 0.005, "kg CO2-eq kWh-1"),
        ("Grid crossover, 70%, low", min(cxs), 0.12, 0.005, "kg CO2-eq kWh-1"),
        ("Grid crossover, 70%, high", max(cxs), 0.63, 0.005, "kg CO2-eq kWh-1"),
        ("Grid crossover, 65%", cx65, 0.33, 0.005, "kg CO2-eq kWh-1"),
        ("Consequential intensity without digesters, fuel cells", nd["fc"].ci_consequential, 2.2, 0.05, "kg CO2-eq kg-1"),
        ("Consequential intensity without digesters, buses", nd["bus"].ci_consequential, 3.9, 0.05, "kg CO2-eq kg-1"),
        ("Attributional intensity, buses, literature, low", rl["C1_bus"]["ci_attributional"][0], 3.7, 0.05, "kg CO2-eq kg-1"),
        ("Attributional intensity, buses, literature, high", rl["C1_bus"]["ci_attributional"][1], 9.4, 0.05, "kg CO2-eq kg-1"),
        # --- facility-resolved analysis (Fig. 4; Supplementary Note S22), all latitudes
        ("Plants >= 100,000 m3 d-1", len(df_all), 854, 0, "plants"),
        ("Plants outside high-income economies", len(gs), 364, 0, "plants"),
        ("Countries outside high-income economies", gs["iso"].nunique(), 17, 0, "-"),
        ("Flow of the 364 plants", gs["flow_m3d"].sum() / 1e6, 84.2, 0.05, "Mm3 d-1"),
        ("Flow of the 854 plants", df_all["flow_m3d"].sum() / 1e6, 214.3, 0.05, "Mm3 d-1"),
        ("Annual flow of the 364 plants", fs["flow_km3_yr"], 30.7, 0.05, "km3 yr-1"),
        ("Share of global municipal wastewater", 100 * fs["flow_km3_yr"] / 380, 8, 0.5, "%"),
        ("Estimated flows among the 364", fs["n_estimated_flow"], 90, 0, "plants"),
        ("Plants in China", top7["CHN"], 172, 0, "plants"), ("Plants in India", top7["IND"], 52, 0, "plants"),
        ("Plants in Egypt", top7["EGY"], 42, 0, "plants"), ("Plants in Indonesia", top7["IDN"], 27, 0, "plants"),
        ("Plants in Mexico", top7["MEX"], 19, 0, "plants"), ("Plants in Brazil", top7["BRA"], 15, 0, "plants"),
        ("Plants in South Africa", top7["ZAF"], 13, 0, "plants"),
        ("Share of the seven largest countries", 100 * top7.iloc[:7].sum() / len(gs), 93, 0.5, "%"),
        ("H2 at all plants, pilot, 278 mg L-1", fs["pilot_278_digesting"]["h2_kt_yr"], 74, 0.5, "kt yr-1"),
        ("H2 at all plants, pilot, 600 mg L-1", fs["pilot_600_digesting"]["h2_kt_yr"], 160, 0.5, "kt yr-1"),
        ("H2 at all plants, literature, 278 mg L-1", fs["literature_278_digesting"]["h2_kt_yr"], 11, 0.5, "kt yr-1"),
        ("H2 at all plants, literature, 600 mg L-1", fs["literature_600_digesting"]["h2_kt_yr"], 23, 0.5, "kt yr-1"),
        ("Share of global demand, low", 100 * fs["literature_278_digesting"]["h2_kt_yr"] / 1e5, 0.01, 0.005, "%"),
        ("Share of global demand, high", 100 * fs["pilot_600_digesting"]["h2_kt_yr"] / 1e5, 0.16, 0.005, "%"),
        ("Diesel displaced at all plants, low", fs["literature_278_digesting"]["diesel_ML_yr"], 53, 0.5, "ML yr-1"),
        ("Diesel displaced at all plants, high", fs["pilot_600_digesting"]["diesel_ML_yr"], 798, 0.5, "ML yr-1"),
        ("Emissions avoided, pilot, digesting, low", -fs["pilot_278_digesting"]["co2_kt_yr"] / 1e3, 0.31, 0.005, "Mt yr-1"),
        ("Emissions avoided, pilot, digesting, high", -fs["pilot_600_digesting"]["co2_kt_yr_low_burden"] / 1e3, 0.93, 0.005, "Mt yr-1"),
        ("Emissions avoided, pilot, non-digesting, low", -fs["pilot_278_nondigesting"]["co2_kt_yr"] / 1e3, 0.55, 0.005, "Mt yr-1"),
        ("Emissions avoided, pilot, non-digesting, high", -fs["pilot_600_nondigesting"]["co2_kt_yr_low_burden"] / 1e3, 1.46, 0.005, "Mt yr-1"),
        ("Emissions change, literature, largest saving", min(fs[k]["co2_kt_yr_low_burden"] for k in lit) / 1e3, -0.16, 0.005, "Mt yr-1"),
        ("Emissions change, literature, largest increase", max(fs[k]["co2_kt_yr"] for k in lit) / 1e3, 0.19, 0.005, "Mt yr-1"),
        ("Plants with positive value, digesting", fs["pilot_278_digesting"]["n_positive_value"], 322, 0, "plants"),
        ("Plants servicing >= US$10 M, pilot, low", fs["pilot_278_digesting"]["n_allowable_ge_10M"], 13, 0, "plants"),
        ("Plants servicing >= US$10 M, pilot, high", fs["pilot_600_nondigesting"]["n_allowable_ge_10M"], 58, 0, "plants"),
        ("Plants servicing >= US$10 M, literature, high", fs["literature_600_nondigesting"]["n_allowable_ge_10M"], 1, 0, "plants"),
        ("Plants meeting 70% (consequential), digesting", fs["pilot_278_digesting"]["n_ci_cons_below_threshold"], 18, 0, "plants"),
        ("Plants meeting 70% (consequential), non-digesting", fs["pilot_278_nondigesting"]["n_ci_cons_below_threshold"], 23, 0, "plants"),
        ("Plants meeting 70% (attributional), pilot", fs["pilot_278_digesting"]["n_ci_attr_below_threshold"], 363, 0, "plants"),
        ("Plants meeting 70% (attributional), literature", fs["literature_278_digesting"]["n_ci_attr_below_threshold"], 15, 0, "plants"),
        # --- sensitivity: plants restricted to within +/-35 degrees latitude (Supplementary Table 48)
        ("+/-35 deg: plants >= 100,000 m3 d-1", len(df35), 405, 0, "plants"),
        ("+/-35 deg: plants outside high-income economies", len(gs35), 304, 0, "plants"),
        ("+/-35 deg: flow of the 304 plants", gs35["flow_m3d"].sum() / 1e6, 72.3, 0.05, "Mm3 d-1"),
        ("+/-35 deg: H2, pilot, 278", fs35["pilot_278_digesting"]["h2_kt_yr"], 63, 0.5, "kt yr-1"),
        ("+/-35 deg: H2, pilot, 600", fs35["pilot_600_digesting"]["h2_kt_yr"], 137, 0.5, "kt yr-1"),
        ("+/-35 deg: H2, literature, 278", fs35["literature_278_digesting"]["h2_kt_yr"], 9, 0.5, "kt yr-1"),
        ("+/-35 deg: H2, literature, 600", fs35["literature_600_digesting"]["h2_kt_yr"], 19, 0.5, "kt yr-1"),
        ("+/-35 deg: emissions avoided, pilot, digesting, low", -fs35["pilot_278_digesting"]["co2_kt_yr"] / 1e3, 0.26, 0.005, "Mt yr-1"),
        ("+/-35 deg: emissions avoided, pilot, digesting, high", -fs35["pilot_600_digesting"]["co2_kt_yr_low_burden"] / 1e3, 0.79, 0.005, "Mt yr-1"),
        ("+/-35 deg: plants meeting 70% (consequential), digesting", fs35["pilot_278_digesting"]["n_ci_cons_below_threshold"], 18, 0, "plants"),
        ("+/-35 deg: plants meeting 70% (consequential), non-digesting", fs35["pilot_278_nondigesting"]["n_ci_cons_below_threshold"], 22, 0, "plants"),
        ("+/-35 deg: plants servicing >= US$10 M, pilot, low", fs35["pilot_278_digesting"]["n_allowable_ge_10M"], 12, 0, "plants"),
        ("+/-35 deg: plants servicing >= US$10 M, pilot, high", fs35["pilot_600_nondigesting"]["n_allowable_ge_10M"], 47, 0, "plants"),
        ("+/-35 deg: net value, all plants, pilot, 278, digesting", fs35["pilot_278_digesting"]["value_MUSD_yr"], 164, 0.5, "US$ M yr-1"),
        ("+/-35 deg: net value, all plants, literature, 600, digesting", fs35["literature_600_digesting"]["value_MUSD_yr"], 46, 0.5, "US$ M yr-1"),
        # --- screening rule (Fig. 6) and robustness of the sensitivity ranking
        ("Break-even diesel price, higher reading", be["pilot"], 0.40, 0.005, "US$ L-1"),
        ("Break-even diesel price, lower reading", be["literature"], 0.44, 0.005, "US$ L-1"),
        ("Break-even diesel price over the bounds, low", min(be_all), 0.18, 0.005, "US$ L-1"),
        ("Break-even diesel price over the bounds, high", max(be_all), 1.06, 0.005, "US$ L-1"),
        ("Break-even hydrogen sales price, higher reading", bh["pilot"], 2.0, 0.05, "US$ kg-1"),
        ("Break-even hydrogen sales price, lower reading", bh["literature"], 2.2, 0.05, "US$ kg-1"),
        ("Grid crossover 70%, higher reading, plant without digesters", A.grid_crossover(digesting=False), 0.46, 0.005, "kg CO2-eq kWh-1"),
        ("Grid crossover 70%, lower reading, digesting (negative: never met)", A.grid_crossover(eta=E["literature"]), -0.08, 0.005, "kg CO2-eq kWh-1"),
        ("Grid crossover 70%, lower reading, no digesters (negative: never met)", A.grid_crossover(eta=E["literature"], digesting=False), -0.27, 0.005, "kg CO2-eq kWh-1"),
        ("Serviceable capital at world-average diesel, higher reading", A.configuration("C1", "bus", diesel_price=P.DIESEL_PRICE_WORLD_AVG).allowable_capex_usd / 1e6, 14, 0.5, "US$ M"),
        ("Serviceable capital at world-average diesel, lower reading", A.configuration("C1", "bus", eta=E["literature"], diesel_price=P.DIESEL_PRICE_WORLD_AVG).allowable_capex_usd / 1e6, 2, 0.5, "US$ M"),
        ("Serviceable capital without the operating-cost ratio: factor", (tea.crf() + P.OPEX_TO_CAPEX) / tea.crf(), 1.96, 0.005, "-"),
        ("Serviceable capital at world-average diesel without the operating-cost ratio, higher reading", A.configuration("C1", "bus", diesel_price=P.DIESEL_PRICE_WORLD_AVG).allowable_capex_usd / 1e6 * (tea.crf() + P.OPEX_TO_CAPEX) / tea.crf(), 27, 0.5, "US$ M"),
        ("Serviceable capital at world-average diesel without the operating-cost ratio, lower reading", A.configuration("C1", "bus", eta=E["literature"], diesel_price=P.DIESEL_PRICE_WORLD_AVG).allowable_capex_usd / 1e6 * (tea.crf() + P.OPEX_TO_CAPEX) / tea.crf(), 3.8, 0.05, "US$ M"),
        ("Process electricity in the net value, Gabal El-Asfar scale", P.PARASITIC_REF_MWH_D * 1000 * P.DAYS_PER_YEAR * P.ELECTRICITY_PRICE, 15000, 500, "US$ yr-1"),
        ("Smallest yield meeting 70% on a carbon-free grid, digesting", A.min_yield_for_threshold() * A.thauer_yield_kg_per_kg_cod() / P.H2_DENSITY * 1000, 32, 0.5, "mL H2 g-1 COD"),
        ("Sobol S_T, emissions, grid range to 0.82: yield", sb82["co2"]["eta"]["ST"], 0.50, 0.005, "-"),
        ("Sobol S_T, emissions, grid range to 0.82: grid", sb82["co2"]["grid_ef"]["ST"], 0.50, 0.005, "-"),
        ("Sobol S_T, value, grid range to 0.82: diesel price", sb82["value"]["diesel_price"]["ST"], 0.65, 0.005, "-"),
        # --- global sensitivity (Fig. 5; Supplementary Note S23)
        ("Sobol S_T, value: diesel price", sb["value"]["diesel_price"]["ST"], 0.65, 0.005, "-"),
        ("Sobol S_T, value: yield", sb["value"]["eta"]["ST"], 0.35, 0.005, "-"),
        ("Sobol S_T, value: largest technical input", max(sb["value"][k]["ST"] for k in V.RANGES if k not in ("diesel_price", "eta")), 0.07, 0.01, "-"),
        ("Sobol S_T, emissions: yield", sb["co2"]["eta"]["ST"], 0.61, 0.005, "-"),
        ("Sobol S_T, emissions: grid", sb["co2"]["grid_ef"]["ST"], 0.37, 0.005, "-"),
        ("Sobol S_T, emissions: methane losses", sb["co2"]["ch4_loss"]["ST"], 0.05, 0.005, "-"),
        ("Sobol model evaluations", sb["evaluations"], 245760, 0, "-"),
        ("Higher reading, emissions 5th pct", cd["pilot"]["co2_p5_p50_p95"][0], -4900, 50, "t yr-1"),
        ("Higher reading, emissions 95th pct", cd["pilot"]["co2_p5_p50_p95"][2], -1100, 50, "t yr-1"),
        ("Lower reading, emissions 5th pct", cd["literature"]["co2_p5_p50_p95"][0], -490, 5, "t yr-1"),
        ("Lower reading, emissions 95th pct", cd["literature"]["co2_p5_p50_p95"][2], 440, 5, "t yr-1"),
        # --- battery-electric buses, grid content of the intensity, value totals
        ("Battery-bus diesel per kg COD, low", bb["battery_bus_L"][0], 0.22, 0.005, "L"),
        ("Battery-bus diesel per kg COD, high", bb["battery_bus_L"][1], 0.44, 0.005, "L"),
        ("Diesel ratio vs battery bus, low", bb["ratio"][0], 1.1, 0.05, "-"),
        ("Diesel ratio vs battery bus, high", bb["ratio"][1], 3.2, 0.05, "-"),
        ("Diesel ratio vs battery bus with 15% loss, low", bb["ratio_with_loss"][0], 0.93, 0.005, "-"),
        ("Grid electricity per kg skimmed H2 (consequential)", ge["kwh_per_kg"], 14.7, 0.05, "kWh kg-1"),
        ("Forgone CHP output per kg skimmed H2", ge["chp_forgone_kwh_per_kg"], 9.9, 0.05, "kWh kg-1"),
        ("Intensity change per 0.1 kg CO2-eq kWh-1 of grid", 0.1 * ge["kwh_per_kg"], 1.5, 0.05, "kg CO2-eq kg-1"),
        ("Bus value at world-average diesel / fuel-cell value, lowest", bus_world / max(fc_vals), 12.6, 0.05, "-"),
        ("Net value, all plants, pilot, 278, digesting", fs["pilot_278_digesting"]["value_MUSD_yr"], 194, 0.5, "US$ M yr-1"),
        ("Net value, all plants, pilot, 600, digesting", fs["pilot_600_digesting"]["value_MUSD_yr"], 419, 0.5, "US$ M yr-1"),
        ("Net value, all plants, literature, 278, digesting", fs["literature_278_digesting"]["value_MUSD_yr"], 26, 0.5, "US$ M yr-1"),
        ("Net value, all plants, literature, 600, digesting", fs["literature_600_digesting"]["value_MUSD_yr"], 55, 0.5, "US$ M yr-1"),
    ]


def main() -> int:
    rows = checks()
    width = max(len(r[0]) for r in rows)
    fails = 0
    print(f"{'Quantity':<{width}}  {'computed':>14}  {'reported':>12}  status  unit")
    for label, comp, rep, tol, unit in rows:
        ok = abs(comp - rep) <= tol
        fails += not ok
        print(f"{label:<{width}}  {comp:>14,.4f}  {rep:>12,}  {'ok' if ok else 'CHECK':>6}  {unit}")
    print(f"\n{len(rows) - fails} of {len(rows)} values within tolerance.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
