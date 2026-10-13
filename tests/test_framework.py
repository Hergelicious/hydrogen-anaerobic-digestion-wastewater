import json
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from whydt import parameters as P  # noqa: E402
from whydt import surrogate, process  # noqa: E402
from reproduce_manuscript_values import checks  # noqa: E402


@pytest.mark.parametrize("label,computed,reported,tol,unit", checks())
def test_manuscript_value(label, computed, reported, tol, unit):
    assert abs(computed - reported) <= tol, f"{label}: {computed} vs {reported} {unit}"


def test_reference_case_is_anchored():
    ref = P.REF_INPUTS
    r = process.screen(ref["OLR"], ref["NH4"], ref["ALK"])
    assert r.eta_df == pytest.approx(P.REF_ETA_DF)
    assert r.h2_m3d == pytest.approx(P.REF_H2_M3D)
    assert r.energy.parasitic_mwh_d == pytest.approx(P.PARASITIC_REF_MWH_D)


def test_parameters_match_trained_model():
    with open(os.path.join(ROOT, "ml", "results", "deployed_surrogate.json")) as f:
        m = json.load(f)
    names = {"OLR": "DF_OLR_kgCOD_m3_day", "NH4": "NH4_mg_L", "ALK": "Alkalinity_mgCaCO3_L"}
    assert P.RIDGE_INTERCEPT == pytest.approx(m["intercept"], abs=5e-5)
    for k, col in names.items():
        assert P.BETA[k] == pytest.approx(m["coef"][col], abs=5e-5)
        assert P.SCALER[k][0] == pytest.approx(m["scaler_mean"][col], rel=1e-4)
        assert P.SCALER[k][1] == pytest.approx(m["scaler_sd"][col], rel=1e-4)
        lo, hi = m["input_range"][col]
        assert P.DOMAIN[k][0] <= lo + 0.06 * (hi - lo) and P.DOMAIN[k][1] >= hi - 0.06 * (hi - lo)


def test_surrogate_bounds_and_direction():
    assert 0 < surrogate.surrogate_eta(1.0, 25, 1200) <= P.ETA_CAP
    assert surrogate.surrogate_eta(4.0, 50, 1800) > surrogate.surrogate_eta(2.0, 50, 1800)
    assert surrogate.anchored_eta(5.0, 50, 1800) <= P.ETA_CAP


def test_output_scales_with_reactor_volume():
    ref = P.REF_INPUTS
    a = process.screen(ref["OLR"], ref["NH4"], ref["ALK"], reactor_m3=P.REF_REACTOR_M3)
    b = process.screen(ref["OLR"], ref["NH4"], ref["ALK"], reactor_m3=P.REF_REACTOR_M3 / 2)
    assert b.h2_m3d == pytest.approx(a.h2_m3d / 2)
    assert b.energy.leverage_ratio == pytest.approx(a.energy.leverage_ratio)


def test_pf_stage_independent_of_df_efficiency():
    a = process.screen(1.0, 50, 1800)
    b = process.screen(1.5, 50, 1800)
    assert b.h2_df_m3d > a.h2_df_m3d
    assert b.h2_pf_m3d == pytest.approx(a.h2_pf_m3d)


def test_domain_flags():
    assert surrogate.check_domain(1.0, 50, 1800, temperature=30).in_domain
    assert not surrogate.check_domain(0.5, 50, 1800).in_domain
    assert not surrogate.check_domain(6.0, 50, 1800).in_domain
    assert not surrogate.check_domain(2.0, 120, 1800).in_domain
    assert not surrogate.check_domain(2.0, 50, 1000).in_domain
    assert not surrogate.check_domain(2.0, 50, 1800, temperature=55).in_domain
    assert surrogate.check_domain(4.0, 50, 1800).advisories   # at the 0.55 ceiling


def test_attainment_is_not_a_mass_balance():
    a = process.gea_attainment()
    assert a["stage_sum_m3d"] == pytest.approx(P.REF_H2_M3D)
    assert a["cod_in_h2_share"] == pytest.approx(a["attainment_total"] * 0.042 * 8, abs=1e-3)
    assert a["attainment_total"] < 1.0
