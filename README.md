



Hassan, H. H. & Hassan, A. H. Hydrogen from municipal wastewater should complement anaerobic digestion, not compete with it (2026).

Overview

Hydrogen production from municipal wastewater sludge competes with anaerobic digestion for the same carbon resource. W-HyDT provides a transparent framework for comparing these pathways on an equivalent basis.

The tool evaluates:

Hydrogen and methane on a per-COD basis.
Alternative sludge-management configurations at the Gabal El-Asfar wastewater treatment plant, Cairo (503,500 m³ d⁻¹).
The potential of hydrogen skimming across 364 large wastewater treatment plants identified in the HydroWASTE database.
Key parameters controlling the environmental and economic viability of hydrogen recovery.

The repository also contains the design-case framework for a dark-fermentation and photo-fermentation (DF-PF) cascade, including:

Monte Carlo simulations.
Machine-learning surrogate modelling.
Techno-economic assessment (TEA).
Life-cycle assessment (LCA).

Outputs are intended for screening and pre-feasibility evaluation only. They should not be used as design specifications or operational predictions.

Repository structure
whydt/
│
├── parameters.py
├── allocation.py
├── facilities.py
├── voi.py
├── bounds.py
├── case_study.py
├── surrogate.py
├── process.py
├── lca.py
└── tea.py

data/
└── hydrowaste_large_plants.csv

ml/
├── training data
├── training scripts
├── model screening
└── results

web/
└── whydt.html

scripts/
├── screen_skimming.py
├── screen_facility.py
├── build_plant_list.py
├── generate_case_study.py
└── reproduce_manuscript_values.py

tests/
└── automated tests

README.md
LICENSE
CITATION.cff
requirements.txt
REPRODUCIBILITY.md

Installation

Python 3.9 or later.

pip install -r requirements.txt

Quick start

Evaluate hydrogen skimming at the Gabal El-Asfar plant:

python scripts/screen_skimming.py --flow 503500 --cod 278 --reading pilot --grid 0.563 --diesel 0.39


Evaluate a custom facility:

python scripts/screen_skimming.py --flow 300000 --cod 400 --yield-ml 40 --diesel 1.10 --grid 0.11


Reproduce manuscript values:

python scripts/reproduce_manuscript_values.py


Run automated tests:

pytest


Train the surrogate model:

python ml/train_surrogate.py

Key assumptions
Hydrogen yield

The only reported pilot-scale study on Gabal El-Asfar sludge reports hydrogen production in inconsistent units. Results are therefore presented for two interpretations:

Reading	Yield	Fraction of Thauer yieldHigher (pilot)	163 mL H₂ g⁻¹ COD	0.349
Lower (literature)	23 mL H₂ g⁻¹ COD	0.050

The higher interpretation represents an optimistic scenario, whereas the lower interpretation is consistent with published sewage-sludge fermentation yields.

Configurations analysed
Code	DescriptionC0	Anaerobic digestion only
C1	Hydrogen skimming with fermentation effluent returned to digesters
C2	DF-PF cascade without residue return
C2r	DF-PF cascade with residue return

All configurations are compared against digestion alone (C0).

Assessment framework

The analysis accounts for:

Hydrogen production and utilisation.
Forgone methane generation.
CHP electricity production.
Grid electricity replacement.
Hydrogen leakage.
Methane leakage.
Process energy demand.
Embodied emissions.
Diesel displacement in transport applications.

Both attributional and consequential greenhouse-gas intensities are reported.

HydroWASTE facility analysis

The repository evaluates 364 wastewater treatment facilities treating at least 100,000 m³ d⁻¹ outside high-income economies.

Plant-specific calculations incorporate:

Country-specific grid emission factors.
Country-specific diesel prices.
Influent COD and capture assumptions.
Alternative digestion adoption scenarios.
Reproducibility

All manuscript values can be independently reproduced.

python scripts/reproduce_manuscript_values.py


The script recomputes reported results and verifies agreement within tolerances determined by reported rounding precision.

Randomised analyses use:

Seed = 42

Data

data/hydrowaste_large_plants.csv is derived from HydroWASTE v1.0:

Ehalt Macedo et al. Earth System Science Data 14, 559-577 (2022).

The dataset can be regenerated from the original HydroWASTE data using:

python scripts/build_plant_list.py HydroWASTE_v10.csv

Citation

Please cite the accompanying publication when using this repository.

See:

CITATION.cff

Licence

MIT License.

See:

LICENSE

Contact

Hagar H. Hassan
 Department of Civil Engineering, Alexandria University, Egypt
 hagar.adel@hotmail.com

Ahmed Hassona Hassan
 Central European Institute of Technology (CEITEC), Masaryk University, Czech Republic
 Ahmed.hassan@ceitec.muni.cz

