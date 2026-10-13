# W-HyDT: wastewater hydrogen screening (v1.6.0)

Code accompanying:

> Hassan, H. H. & Hassan, A. H. *Hydrogen from municipal wastewater should complement anaerobic
> digestion, not compete with it* (2026).

Hydrogen and methane compete for the same sludge carbon: every kilogram of hydrogen carries 8 kg of
COD that a digester would otherwise convert to methane. W-HyDT compares the two on equal terms:

- per kilogram of COD;
- for plant configurations at the Gabal El-Asfar plant in Cairo (503,500 m³ d⁻¹), evaluated
  against digestion alone;
- at the 364 plants that treat at least 100,000 m³ d⁻¹ outside high-income economies (HydroWASTE).

It also identifies which inputs decide whether hydrogen skimming is worthwhile.

The package also contains the design-case framework of the dark- and photo-fermentation (DF–PF)
cascade:

- its Monte Carlo case study;
- a three-sensor surrogate trained on synthetic data;
- its techno-economic analysis and life cycle assessment.

These are documented in Supplementary Notes S1–S20 of the paper.

Outputs are screening-level estimates for pre-feasibility decisions. They are not design values
or operational predictions.

## Repository layout

```
whydt/                 Python package
  parameters.py        every fixed value, with its source
  allocation.py        hydrogen against methane: per kg COD, configurations C1/C2/C2r, carbon, value
  facilities.py        facility-resolved analysis of the 364 large plants
  voi.py               global (Sobol) sensitivity of skimming
  bounds.py            Thauer benchmark, electron-balance limit, energy per kg COD
  case_study.py        design-case DF–PF Monte Carlo at Gabal El-Asfar (n = 500, seed 42)
  surrogate.py         three-sensor Ridge surrogate (design case), anchoring and domain checks
  process.py           hydrogen yield and energy chain of the design case
  lca.py               design-case life cycle assessment and site integration
  tea.py               design-case techno-economic analysis
data/
  hydrowaste_large_plants.csv   854 HydroWASTE plants >= 100,000 m3 d-1 (income and +/-35 deg flags)
ml/                    surrogate training data, training and model-screening scripts, results
web/whydt.html         interactive screening tool, a single HTML file that runs offline in any browser
scripts/
  screen_skimming.py              command-line comparison of skimming with digestion alone
  screen_facility.py              command-line design-case screening
  build_plant_list.py             rebuilds data/hydrowaste_large_plants.csv from HydroWASTE
  generate_case_study.py          writes the design-case summary and its 500 rows
  reproduce_manuscript_values.py  recomputes the reported values and checks them
tests/                 automated checks (pytest)
```

## Installation

Python 3.9 or later.

```bash
pip install -r requirements.txt
```

## Usage

```bash
python scripts/screen_skimming.py --flow 503500 --cod 278 --reading pilot --grid 0.563 --diesel 0.39
python scripts/screen_skimming.py --flow 300000 --cod 400 --yield-ml 40 --diesel 1.10 --grid 0.11
python scripts/reproduce_manuscript_values.py   # recomputes and checks the reported values
pytest
python ml/train_surrogate.py                    # surrogate metrics -> ml/results/
```

`screen_skimming.py` compares skimming with digestion alone for any plant and reports the break-even
diesel and hydrogen prices and the grid intensity and yield at which the 70% saving is met. The
interactive tool `web/whydt.html` needs no installation. `reproduce_manuscript_values.py` recomputes
357 reported quantities, each compared with the reported value at a tolerance set by its rounding.

## The comparison of hydrogen and methane

**Two readings of the yield.** The only published pilot on Gabal El-Asfar sludge (El-Kebeer et
al.) reports its yield in inconsistent units. Every result is given for both readings:

| Reading | Basis | Yield | Fraction of the Thauer yield |
|---|---|---|---|
| Higher (code key `pilot`) | 6.48 m³ H₂ per m³ of sludge at 39.7 kg COD m⁻³ | 163 mL H₂ g⁻¹ COD | η = 0.349 |
| Lower (code key `literature`) | 64.8 mL g⁻¹ VS | 23 mL H₂ g⁻¹ COD | η = 0.050 |

The higher reading lies 5–8 times above published sewage-sludge yields and is the optimistic case; the lower reading agrees with them.

**Per kg COD that ends up as hydrogen (0.125 kg H₂).** Hydrogen against digester methane at 80–100%
of 0.35 Nm³ kg⁻¹ COD:

| Service | Hydrogen | Methane | Ratio (H₂ : CH₄) |
|---|---|---|---|
| Chemical energy | 15.0 MJ | 10.0–12.5 MJ | 1.20–1.50 |
| Electricity (fuel cell 50%; CHP 35–44%) | 2.08 kWh | 0.97–1.53 kWh | 1.36–2.14 |
| Diesel displaced in buses | 0.49–0.71 L | 0.19–0.24 L | 2.04–3.80 |
| Diesel displaced, methane as CHP electricity in battery-electric buses | 0.49–0.71 L | 0.22–0.44 L | 1.10–3.21 |

The bus comparison sets a fuel-cell bus (7–10.25 kg H₂ per 100 km) against biomethane in a CNG bus
using 46% more energy per kilometre than a 40 L per 100 km diesel bus. The electric alternative charges a battery-electric
bus (1.38–1.75 kWh km⁻¹ including charging losses) with the CHP electricity from the same methane.

Fermentation can claim at most 33.6% of the COD as hydrogen at the Thauer limit; the share is 11.7%
at the higher reading and 1.7% at the lower reading.

**Configurations** (`allocation.configuration`), evaluated against digestion alone (C0):

| Code | Configuration | COD diverted from the digesters |
|---|---|---|
| C1 | Hydrogen skimming: fermentation at the pilot feed strength, effluent to the digesters | the COD leaving as hydrogen |
| C2 | The DF–PF cascade, none of the fatty-acid COD returned | hydrogen COD plus all fatty-acid COD |
| C2r | The DF–PF cascade, residues returned to the digesters | the COD leaving as hydrogen in both stages |

How each result is computed:

- **End uses.** Each configuration is evaluated for on-site fuel cells and for fuel-cell buses.
- **Forgone methane.** Valued as CHP electricity and replaced from the grid.
- **Emissions.** These terms are summed:
  - grid electricity for the forgone CHP output, process loads and compression;
  - the digester methane losses avoided on the diverted COD, as a credit (1–7.5% of methane, GWP₁₀₀ 27.0);
  - hydrogen leakage (0.2–5%, GWP₁₀₀ 11.6);
  - embodied carbon;
  - for bus use, the RED II diesel credit of 11.28 kg CO₂-eq kg⁻¹ H₂ (1:1 energy basis).
- **Attributional intensity.** Certification-style: sludge counts as a zero-burden waste and capital goods are excluded.
- **Consequential intensity.** Adds the forgone biogas, losses, leakage and embodied carbon.
- **Thresholds.** 3.95 and 3.38 kg CO₂-eq kg⁻¹ H₂ (65% and 70% savings on 94 g CO₂-eq MJ⁻¹).
- **Net value before capital** (bus use) is hydrogen × (5 L diesel kg⁻¹ × diesel price − conditioning cost of US$0.8–2.1 kg⁻¹), minus forgone CHP electricity and process load × electricity price.
- **Serviceable capital** = value / (capital recovery factor 0.0944 + operating-to-capital ratio 0.090).

**Facilities** (`facilities.summary`):

- Influent COD is bounded at 278–600 mg L⁻¹ and captured COD is 59% of it.
- Digestion is bounded: either all plants digest their sludge or none do.
- Each plant uses its country's 2025 grid intensity (Ember; 2024 for Indonesia and Nicaragua) and latest retail
  diesel price (GlobalPetrolPrices.com).
- Plants are selected at any latitude; `load_plants(max_abs_lat=35)` repeats the analysis for the 304 plants
  within ±35° latitude (sensitivity).

**Screening rule** (`allocation.break_even_diesel_price`, `break_even_h2_price`, `min_yield_for_threshold`,
`decision_map`): the diesel price and hydrogen sales price at which skimming breaks even before capital, the
smallest yield that meets the 70% threshold, and maps of value and consequential intensity over yield, diesel
price and grid intensity. `scripts/screen_skimming.py` reports them for any plant.

**Sensitivity** (`voi.sobol`): first- and total-order Sobol indices over 13 inputs (N = 16,384;
seed 42) for the net value and the emissions change of skimming. The yield is sampled uniformly between
the two readings to rank its influence, not as a probability distribution; the grid range is 0.110–0.699
(16 of the 17 countries; `sobol(ranges=...)` tests Mongolia's 0.816).

## Design-case framework (Supplementary Notes S1–S20)

| Component | Description |
|---|---|
| Case study | DF output = η × 0.467 m³ kg⁻¹ COD × 82,792 kg COD d⁻¹ (captured primary sludge). PF output = 0.50 × 82,792 × 0.35 m³ kg⁻¹ × η_PF, with η_PF from a Monod–inhibition model (n = 500, seed 42). |
| Output | 16,395 m³ H₂ d⁻¹ (DF 13,514; PF 2,881). |
| Surrogate | Ridge (α = 10) on logit(η), Medium training envelope. Held-out RMSE 0.067 in η; CV-R² 0.71. Anchored η_DF(x) = min(0.55, 0.349 × η̂(x)/η̂(x_GEA)). |
| Accounting | The design-case LCA (−9.72 kg CO₂-eq kg⁻¹ H₂) credits displaced diesel and does not charge the forgone biogas. The TEA gives a gross LCOH of US$8.37 kg⁻¹ at an incremental CAPEX of US$24.4 M. |

At a plant that already digests its sludge, the cascade loses energy and generally raises emissions
relative to digestion alone (`allocation`, configuration C2).

## Data

`data/hydrowaste_large_plants.csv` is derived from HydroWASTE v1.0 (Ehalt Macedo et al., Earth
Syst. Sci. Data 14, 559–577, 2022; CC BY 4.0). Rebuild it from the original file with:

```bash
python scripts/build_plant_list.py HydroWASTE_v10.csv
```

## Citation

See `CITATION.cff`. Please cite the paper when using the framework.

## Licence

MIT. See `LICENSE`.

## Contact

Hagar H. Hassan (Alexandria University) · Ahmed Hassona Hassan (CEITEC, Masaryk University)
