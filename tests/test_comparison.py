"""Checks of the comparison of hydrogen and methane (whydt.allocation, whydt.facilities, whydt.voi)."""
import itertools
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from whydt import allocation as A  # noqa: E402
from whydt import facilities as F  # noqa: E402
from whydt import parameters as P  # noqa: E402
from whydt import voi as V  # noqa: E402

E = A.eta_scenarios()
GRID = {"f_ch4": P.CH4_CONVERSION_RANGE, "chp": P.CHP_ELEC_EFF_RANGE, "membrane_mwh_d": P.MEMBRANE_MWH_D_RANGE,
        "h2_comp_kwh": P.H2_COMPRESSION_KWH_PER_KG, "ch4_loss": P.DIGESTER_CH4_LOSS_RANGE, "h2_leak": P.H2_LEAK_RANGE,
        "skim_lca_mwh_d": (P.PARASITIC_REF_MWH_D, P.LCA_ELECTRICITY_MWH_D), "embodied_t": (0.0, P.EMBODIED_TOTAL_T)}


def test_hydrogen_beats_methane_per_kg_cod_even_with_purification_loss():
    for k, (lo, hi) in A.per_kg_cod_ranges().items():
        assert 0.85 * lo > 1.0, k


def test_cod_balance_of_skimming():
    for eta in E.values():
        c = A.configuration("C1", "bus", eta=eta)
        assert c.cod_diverted_kg_d == pytest.approx(c.h2_kg_d * P.H2_COD_EQUIVALENT)
        assert c.cod_diverted_kg_d / P.REF_CAPTURED_COD_KGD == pytest.approx(A.skim_share(eta))


@pytest.mark.parametrize("reading", list(E))
def test_ordering_of_configurations_for_every_parameter_set(reading):
    eta = E[reading]
    for combo in itertools.product(*GRID.values()):
        kw = dict(zip(GRID, combo))
        kw_c = dict(kw, embodied_t=P.EMBODIED_TOTAL_T)   # the cascade always carries the design-case embodied carbon
        for use in ("fc", "bus"):
            c1 = A.configuration("C1", use, eta=eta, **kw)
            c2 = A.configuration("C2", use, eta=eta, **kw_c)
            c2r = A.configuration("C2r", use, eta=eta, **kw_c)
            assert c1.net_electricity_mwh_d > c2r.net_electricity_mwh_d > c2.net_electricity_mwh_d
            assert c1.co2_t_yr < c2r.co2_t_yr < c2.co2_t_yr


def test_no_forgone_biogas_without_digesters():
    c = A.configuration("C1", "bus", digesting=False)
    assert c.chp_forgone_mwh_d == 0 and c.ch4_forgone_kg_d == 0


def test_consequential_intensity_is_linear_in_grid_factor():
    x = [A.configuration("C1", "bus", grid_ef=g).ci_consequential for g in (0.0, 0.3, 0.6)]
    assert x[2] - x[1] == pytest.approx(x[1] - x[0])
    g = A.grid_crossover()
    assert A.configuration("C1", "bus", grid_ef=g).ci_consequential == pytest.approx(P.LOW_CARBON_THRESHOLD_KG)


def test_thresholds():
    assert A.threshold_kg(0.70) == pytest.approx(P.LOW_CARBON_THRESHOLD_KG)
    assert A.threshold_kg(0.65) > A.threshold_kg(0.70)


def test_unknown_parameter_rejected():
    with pytest.raises(KeyError):
        A.configuration("C1", "bus", diesel=1.0)


def test_plant_list():
    df = F.load_plants(global_south=False)
    assert len(df) == 854 and int((~df["high_income"]).sum()) == 364
    assert (df["flow_m3d"] >= P.PLANT_MIN_FLOW_M3D).all()
    assert set(F.load_plants()["iso"]) == set(P.COUNTRY_INPUTS)
    # the latitude-restricted subset (sensitivity) is the earlier list of 405 plants, 304 outside high income
    d35 = F.load_plants(global_south=False, max_abs_lat=P.LATITUDE_SENSITIVITY_DEG)
    assert len(d35) == 405 and int((~d35["high_income"]).sum()) == 304
    assert (d35["lat"].abs() <= 35.0).all() and d35["within_35deg"].all()


def test_break_even_prices_consistent():
    """Break-even diesel price x diesel per kg H2 equals the break-even hydrogen sales price (central case),
    and the value is zero at the break-even diesel price."""
    for e in E.values():
        bd = A.break_even_diesel_price(eta=e)
        assert A.configuration("C1", "bus", eta=e, diesel_price=bd).value_usd_yr == pytest.approx(0.0, abs=1e-6)
        assert bd * P.DIESEL_BUS_L_PER_100KM / P.FC_BUS_KG_PER_100KM == pytest.approx(A.break_even_h2_price(eta=e))
        # independent of plant size, and accepted with plant settings
        assert A.break_even_diesel_price(eta=e, captured_cod_kg_d=20_000.0) == pytest.approx(bd)
        assert A.break_even_h2_price(eta=e, captured_cod_kg_d=20_000.0) == pytest.approx(A.break_even_h2_price(eta=e))
        assert A.break_even_h2_price(eta=e, digesting=False) < A.break_even_h2_price(eta=e)


def test_screen_skimming_reports_screening_rule():
    import subprocess
    import sys
    root = __import__("os").path.dirname(__import__("os").path.dirname(__file__))
    out = subprocess.run([sys.executable, f"{root}/scripts/screen_skimming.py", "--flow", "503500"],
                         capture_output=True, text=True, check=True).stdout
    assert "Break-even diesel price, buses (US$ L-1)                   0.40" in out
    assert "below 0.29" in out


def test_decision_map_matches_configuration():
    import numpy as np
    etas, prices, grids = np.array([0.05, 0.35]), np.array([0.4, 1.5]), np.array([0.1, 0.6])
    v = A.decision_map(etas, prices, "value")
    c = A.decision_map(etas, grids, "intensity", digesting=False)
    assert v[1, 1] == pytest.approx(A.configuration("C1", "bus", eta=0.35, diesel_price=1.5).value_usd_yr)
    assert c[0, 0] == pytest.approx(A.configuration("C1", "bus", eta=0.05, grid_ef=0.1, digesting=False).ci_consequential)


def test_facility_scaling_matches_gea():
    """A plant with Gabal El-Asfar's captured COD reproduces the GEA configuration."""
    flow = P.REF_CAPTURED_COD_KGD / (P.CAPTURE * 278.0 / 1000.0)
    import pandas as pd
    one = pd.DataFrame([{"waste_id": 0, "iso": "EGY", "country": "Egypt", "lat": 30.0, "lon": 31.0, "flow_m3d": flow,
                         "flow_basis": "estimated", "high_income": False}])
    r = F.evaluate(one, eta=E["pilot"], cod_mg_l=278.0).iloc[0]
    c = A.configuration("C1", "bus")
    assert r["h2_kg_d"] == pytest.approx(c.h2_kg_d)
    assert r["co2_t_yr"] == pytest.approx(c.co2_t_yr)
    assert r["value_usd_yr"] == pytest.approx(c.value_usd_yr)


def test_sobol_small_sample_is_sane():
    s = V.sobol(n=512, seed=1)
    for out in ("value", "co2"):
        st = {k: v["ST"] for k, v in s[out].items()}
        assert all(v >= -0.05 for v in st.values())
        assert max(st, key=st.get) in ("diesel_price", "eta")


def test_battery_bus_alternative():
    """Hydrogen in fuel-cell buses against the same COD as CHP electricity in battery-electric buses."""
    from whydt import allocation as A
    b = A.battery_bus_alternative()
    assert 0.22 < b["battery_bus_L"][0] < b["battery_bus_L"][1] < 0.45
    assert 1.05 < b["ratio"][0] < 1.15 and 3.15 < b["ratio"][1] < 3.25
    # biomethane in CNG buses displaces less diesel than the same methane as electricity in battery buses
    pk = A.per_kg_cod()
    assert pk["diesel_L_battery_bus"] > pk["diesel_L"]["CH4"]


def test_grid_electricity_per_kg_is_the_crossover_slope():
    from whydt import allocation as A
    g = A.grid_electricity_per_kg()
    b = A.configuration("C1", "bus", grid_ef=0.0).ci_consequential
    assert abs(A.grid_crossover() - (A.threshold_kg(0.70) - b) / g["kwh_per_kg"]) < 1e-12
    assert 0 < g["chp_forgone_kwh_per_kg"] < g["kwh_per_kg"]
