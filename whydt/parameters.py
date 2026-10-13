"""Fixed parameters of the W-HyDT screening framework.

Every constant below is the value reported in the manuscript (main text, Methods)
or its Supplementary Information. Section references are given next to each value.
Values marked "case study" are outputs of `whydt.case_study.run()` (n = 500, seed 42),
held here so that the tool does not need the training data; `tests/test_case_study.py`
checks that they match.
"""

# ---------------------------------------------------------------------------
# Three-sensor screening surrogate (Supplementary Note S14b; ml/train_surrogate.py)
# Ridge regression (alpha = 10) on logit(eta), eta = synthetic efficiency index rescaled to
# the 0.55 mesophilic ceiling; z-scored inputs; Medium training envelope (n = 400 training rows).
# eta(x) = min(ETA_CAP, 1 / (1 + exp(-(intercept + sum(beta * z)))))
# ---------------------------------------------------------------------------
RIDGE_ALPHA = 10.0
RIDGE_INTERCEPT = -1.2223
BETA = {"OLR": 0.5548, "NH4": 0.0049, "ALK": 0.0026}
SCALER = {                      # (mean, standard deviation) of the training inputs
    "OLR": (2.9304, 1.1671),    # kg COD m-3 d-1
    "NH4": (51.426, 15.954),    # mg N L-1
    "ALK": (1829.9, 358.74),    # mg CaCO3 L-1
}
ETA_CAP = 0.55                  # mesophilic stoichiometric ceiling (55% of Thauer)

# Domain of the deployed surrogate = its training envelope (Supplementary Table 13, Medium)
DOMAIN = {
    "OLR": (1.0, 5.0),          # kg COD m-3 d-1
    "NH4": (25.0, 80.0),        # mg N L-1
    "ALK": (1200.0, 2500.0),    # mg CaCO3 L-1
    "T":   (20.0, 38.0),        # deg C (mesophilic)
}
NH4_INHIBITION_ONSET = 800.0    # mg L-1 (Supplementary Table 40)
NH4_SEVERE = 1500.0             # mg L-1 (Supplementary Table 40)
MIN_FLOW_SCREENING = 100_000.0  # m3 d-1 (Supplementary Table 41, node 2)

# Held-out performance of the deployed model (ml/results/surrogate_metrics.json)
SURROGATE_TEST_RMSE = 0.067     # eta units
SURROGATE_CV_R2 = 0.71

# ---------------------------------------------------------------------------
# Pilot-derived constant (Methods): El-Kebeer et al. pilot, volumetric reading
# 6.48 m3 H2 m-3 at 39.7 kg COD m-3 -> 0.163 m3 H2 kg-1 COD -> 0.349 of the Thauer yield
# ---------------------------------------------------------------------------
PILOT_YIELD_M3_PER_M3 = 6.48
PILOT_COD_KG_M3 = 39.7
PILOT_VS_KG_M3 = 14.2
ETA_DF_SD = 0.067               # s.d. of eta_DF in the Monte Carlo (= surrogate held-out RMSE)

# ---------------------------------------------------------------------------
# Gabal El-Asfar (GEA) design basis and case-study reference (Methods; Supplementary Note S11)
# ---------------------------------------------------------------------------
REF_INPUTS = {"OLR": 1.0, "NH4": 50.0, "ALK": 1800.0}   # design reactor OLR; NH4 and ALK at
                                                         # the training-envelope means (rounded)
REF_REACTOR_M3 = 82_500.0       # DF reactor volume (6 CSTRs x 13,750 m3; HRT 2 d)
REF_INFLUENT_M3D = 503_500.0    # GEA study phase influent flow
REF_CAPTURED_COD_KGD = 82_792.0 # primary-sludge COD captured (0.59 capture)
REF_ETA_DF = 0.349              # pilot-derived eta_DF (case study: 0.3494)
REF_H2_DF_M3D = 13_514.0        # DF stage, case study
REF_H2_PF_M3D = 2_881.0         # PF stage, case study
REF_H2_M3D = 16_395.0           # integrated DF-PF output, case study mean
REF_H2_P5_M3D = 11_785.0        # case study 5th percentile
REF_H2_P95_M3D = 21_420.0       # case study 95th percentile
PF_FACTOR = 1.21                # total-to-DF ratio, case study (1.213)
H2_COD_EQUIVALENT = 8.0         # kg COD per kg H2 (electron equivalent)

# ---------------------------------------------------------------------------
# Physical constants and energy chain (Methods; Supplementary Table 35)
# ---------------------------------------------------------------------------
H2_DENSITY = 0.0899             # kg m-3 at 0 deg C, 1 atm
LHV_H2_MJ_KG = 120.0            # MJ kg-1
FC_EFFICIENCY = 0.50            # PEM fuel cell
PARASITIC_REF_MWH_D = 0.8       # direct process parasitic load at the reference volume
DAYS_PER_YEAR = 365

# ---------------------------------------------------------------------------
# Consequential LCA (Methods; Supplementary Note S16; Supplementary Table 8)
# ---------------------------------------------------------------------------
LCA_ELECTRICITY_MWH_D = 2.20         # LCA-boundary electricity at the reference volume
GRID_EF_EGYPT = 0.461                # kg CO2-eq kWh-1
GRID_EF_2035 = (0.30, 0.35)          # Egypt 2035 renewable target
EMBODIED_TOTAL_T = 9_420.0           # t CO2-eq over the project life
PROJECT_LIFE_YR = 20
RED_II_COMPARATOR_G_MJ = 94.0        # RED II Annex V fossil fuel comparator
LHV_H2_GJ_KG = 0.120
RED_II_SAVING_THRESHOLDS = (0.65, 0.70)
SLUDGE_EF_RANGE = (0.0100, 0.0350)   # kg CO2-eq kg-1 COD, parametric scenario
CONSERVATIVE_COUNTERFACTUAL = 4.2    # kg CO2-eq kg-1 H2 (Supplementary Note S4)

# ---------------------------------------------------------------------------
# Techno-economic analysis (Methods; Supplementary Notes S1, S11, S17)
# ---------------------------------------------------------------------------
WACC = 0.07
CAPEX_INCREMENTAL = 24.4e6           # US$, direct-allocation boundary (reported LCOH)
CAPEX_SHARED = 37.5e6                # US$, shared-facility allocation
CAPEX_FULL = 50.0e6                  # US$, full system boundary
OPEX = 2.2e6                         # US$ yr-1
DIESEL_PRICE_REF = 0.57              # US$ L-1, Egypt retail
DIESEL_BUS_L_PER_100KM = 40.0
FC_BUS_KG_PER_100KM = 8.0            # central assumption -> 5 L diesel per kg H2
FC_BUS_KG_PER_100KM_RANGE = (7.0, 10.25)  # reported fleet range (refs 47, 48)
OFFTAKE_PRICE = 5.00                 # US$ kg-1 H2, screening offtake value
GREY_H2_PRICE = (1.0, 2.5)           # US$ kg-1
SMR_CI_UPSTREAM = 10.25              # kg CO2-eq kg-1 H2, SMR incl. upstream (abatement-cost denominator, Methods)
LCCA_COMPARATORS = {                 # (LCOH US$ kg-1, carbon intensity kg CO2-eq kg-1)
    "SMR": (1.75, 10.0),
    "Blue H2": (2.50, 2.5),
    "Green electrolysis": (4.50, 1.0),
}
DOWNSTREAM_COST = (0.8, 2.1)         # US$ kg-1 purification, compression, storage
TEA_SENSITIVITY = {"capex": 0.25, "wacc": (0.05, 0.12), "yield": 0.35}   # one at a time (Supplementary Note S1)
TEA_MC = {"capex": 0.30, "wacc": (0.05, 0.10), "n": 500, "seed": 42}     # Supplementary Note S13

# ---------------------------------------------------------------------------
# Model-independent bound (Methods, thermodynamic bound)
# ---------------------------------------------------------------------------
GLOBAL_WASTEWATER_M3_YR = 380e9
INFLUENT_COD_RANGE_MG_L = (278.0, 600.0)
THAUER_MOL_H2_PER_MOL_GLUCOSE = 4.0
ELECTRON_BALANCE_MOL_H2_PER_MOL_GLUCOSE = 12.0
GLUCOSE_COD_G_PER_MOL = 191.99
H2_MOLAR_MASS = 2.016
CAPTURE = 0.59                       # share of influent COD captured by primary settling (Gabal El-Asfar)
CH4_NM3_PER_KG_COD = 0.35
CH4_DENSITY = 0.716                  # kg Nm-3
CH4_LHV_MJ_KG = 50.0
THORNTON_MJ_PER_KG_COD = 13.9

# Site integration at Gabal El-Asfar (Supplementary Note S16b): one-at-a-time sensitivities
CHP_ELEC_EFF_RANGE = (0.35, 0.44)    # existing biogas CHP; 2024 units ~44% electrical (14.6 MWe, 7.5 MWth, 65.9% total)
DF_EFFLUENT_M3D = 41_250.0           # DF effluent to the VFA concentration step
PF_FEED_M3D = 13_750.0               # PF feed after concentration (1 -> 3 g VFA L-1)
MEMBRANE_BAR_RANGE = (5.0, 15.0)     # nanofiltration to low-pressure reverse osmosis
MEMBRANE_PUMP_EFF = 0.80
MEMBRANE_RECOVERY = 2.0 / 3.0
PUMPING_KWH_PER_M3 = 0.2             # specific energy of sludge pumping and mixing (Supplementary Table 35)
ILLUSTRATIVE_TARIFF = 0.05           # US$ kWh-1

# ---------------------------------------------------------------------------
# Allocation of captured COD between hydrogen and methane (Supplementary Note S21)
# The comparison is made per kg of COD that fermentation turns into hydrogen (8 kg COD per kg H2),
# against the methane the existing digesters would obtain from the same COD.
# ---------------------------------------------------------------------------
CH4_CONVERSION_RANGE = (0.8, 1.0)        # share of the theoretical 0.35 Nm3 kg-1 COD the digesters
                                         # would obtain from diverted, readily degradable COD
DIESEL_LHV_MJ_L = 35.78                  # 9.94 kWh L-1 (Methods, ref. 42)
DIESEL_WTW_KG_PER_L = RED_II_COMPARATOR_G_MJ * DIESEL_LHV_MJ_L / 1000.0   # 3.36 kg CO2-eq L-1
CNG_BUS_ENERGY_FACTOR = 1.46             # CNG bus energy per km relative to a diesel bus (CIVITAS)
BEB_KWH_PER_KM_RANGE = (1.38, 1.75)      # battery-electric 12 m buses in service, including charging losses
                                         # (Zhou et al., Energy 96, 603-613, 2016)
CBG_CONDITIONING_KWH_PER_KG = (1.2, 1.4) # upgrading and compression to 250 bar, kWh kg-1 biomethane (VALORGAS)
UPGRADING_CH4_SLIP_RANGE = (0.001, 0.02) # methane slip of upgrading technologies (Persson, IEA Bioenergy Task 37)
H2_COMPRESSION_KWH_PER_KG = (2.0, 4.0)   # compression for 350 bar fills (US DOE Hydrogen Program Record 9013)
H2_GWP100 = 11.6                         # Sand et al. 2023
H2_LEAK_RANGE = (0.002, 0.05)            # gaseous value chain; published estimates span 0.2-20% (Esquivel-Elizondo et al. 2023)
CH4_GWP100 = 27.0                        # non-fossil methane, IPCC AR6 WGI Table 7.15
DIGESTER_CH4_LOSS_RANGE = (0.01, 0.075)  # share of produced methane lost; 7.5% = mean of measured WWTP biogas plants (Scheutz & Fredenslund 2019)
LOW_CARBON_SAVING = 0.70                 # EU low-carbon hydrogen: 70% below the 94 g CO2-eq MJ-1 comparator
LOW_CARBON_THRESHOLD_KG = RED_II_COMPARATOR_G_MJ * (1 - LOW_CARBON_SAVING) * LHV_H2_GJ_KG   # 3.38 kg CO2-eq kg-1 H2
OPEX_TO_CAPEX = OPEX / CAPEX_INCREMENTAL # 0.09 yr-1, design-case ratio used for allowable capital
ELECTRICITY_PRICE = ILLUSTRATIVE_TARIFF  # US$ kWh-1 (central)
ELECTRICITY_PRICE_RANGE = (0.03, 0.12)

# Hydrogen skimming ahead of digestion (configuration C1): DF on undiluted pretreated sludge at the
# pilot feed strength, effluent to the existing digesters; process loads per kg captured COD as in
# the design case (direct parasitic 0.8 MWh d-1 for value; LCA boundary 2.20 MWh d-1 for carbon,
# an upper bound for the smaller skimming reactor). Embodied carbon of the design case (9,420 t,
# including photobioreactors) is used as an upper bound.
SKIM_FEED_COD_KG_M3 = PILOT_COD_KG_M3
SKIM_HRT_D = 2.0
MEMBRANE_MWH_D_RANGE = (7.0, 21.0)       # VFA concentration ahead of PF (Supplementary Note S16b)

# Country inputs for the facility-resolved analysis (2025 grid carbon intensity, Ember via Our World
# in Data, kg CO2-eq kWh-1; retail diesel price, GlobalPetrolPrices.com, US$ L-1 and date).
COUNTRY_INPUTS = {
    "EGY": ("Egypt", 0.563, 0.39, "2026-03-09"),
    "CHN": ("China", 0.525, 0.93, "2026-02-09"),
    "IND": ("India", 0.670, 0.98, "2026-03-09"),
    "IDN": ("Indonesia", 0.680, 0.82, "2026-01-12"),
    "MEX": ("Mexico", 0.474, 1.47, "2026-01-12"),
    "BRA": ("Brazil", 0.110, 1.11, "2025-12-08"),
    "ZAF": ("South Africa", 0.699, 1.30, "2026-02-09"),
    "THA": ("Thailand", 0.546, 0.96, "2026-02-09"),
    "PER": ("Peru", 0.238, 1.18, "2026-02-09"),
    "NIC": ("Nicaragua", 0.301, 1.18, "2026-02-09"),
    "VNM": ("Vietnam", 0.461, 0.72, "2026-02-09"),
    "ARG": ("Argentina", 0.346, 1.38, "2026-03-09"),
    "KHM": ("Cambodia", 0.499, 0.92, "2026-02-09"),
    "PAK": ("Pakistan", 0.347, 0.96, "2026-02-09"),
    "TUR": ("Turkey", 0.475, 1.32, "2026-02-09"),
    "BLR": ("Belarus", 0.309, 0.89, "2026-01-12"),
    "MNG": ("Mongolia", 0.816, 1.19, "2026-02-09"),
}
# Grid intensity: Ember via Our World in Data, 2025 (Indonesia and Nicaragua: latest reported year, 2024).
# Diesel: latest retail price on GlobalPetrolPrices.com, dated as given.
DIESEL_PRICE_WORLD_AVG = 1.56            # US$ L-1, 10 Aug 2026 (GlobalPetrolPrices.com)
# High-income economies (World Bank classification for FY2027) among the HydroWASTE plants >= 100,000 m3 d-1
HIGH_INCOME_ISO = ("AUS", "AUT", "BEL", "BGR", "BHR", "CAN", "CHE", "CHL", "CZE", "DEU", "DNK", "ESP", "EST", "FIN",
                   "FRA", "GBR", "GRC", "HKG", "HUN", "IRL", "ISL", "ISR", "ITA", "JPN", "KOR", "KWT", "LTU", "LVA",
                   "NLD", "NOR", "NZL", "POL", "PRT", "QAT", "ROU", "RUS", "SAU", "SGP", "SVK", "SWE", "USA")
PLANT_MIN_FLOW_M3D = 100_000.0           # facility analysis: all plants at least this large, at any latitude
LATITUDE_SENSITIVITY_DEG = 35.0          # sensitivity only: restrict the plants to within +/-35 degrees
SOBOL_GRID_EF_RANGE = (0.110, 0.699)    # sensitivity analysis: Brazil to South Africa, the grid intensities of 16 of the 17 countries (363 of the
                                         # 364 plants); Mongolia (0.816, one plant) lies above and is tested separately
