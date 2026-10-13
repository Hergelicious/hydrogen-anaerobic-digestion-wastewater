import pytest

from whydt import case_study as cs
from whydt import parameters as P


def test_units_of_pf_bridge():
    chk = cs.pf_feed_check()
    assert chk["m_vfa_kgd"] == pytest.approx(41_396.0)
    # 41,396 kg COD d-1 at 3,000 mg L-1 (= 3 kg m-3) is ~13,800 m3 d-1
    assert chk["pf_flow_m3d"] == pytest.approx(13_798.7, rel=1e-4)


def test_constants():
    assert cs.Y_TH_M3_PER_KG_COD == pytest.approx(0.4672, abs=1e-4)
    assert cs.ETA_PILOT == pytest.approx(0.349, abs=5e-4)


def test_reproducible_moment_matched_and_closed_form_df():
    a = cs.run(); b = cs.run()
    assert a.h2_m3d == b.h2_m3d
    assert a.eta_df_mean == pytest.approx(cs.ETA_PILOT, abs=1e-12)
    assert a.h2_df_m3d == pytest.approx(cs.ETA_PILOT * cs.Y_TH_M3_PER_KG_COD * cs.C_CAP_KGD)
    assert a.h2_m3d == pytest.approx(a.h2_df_m3d + a.h2_pf_m3d)


def test_parameters_hold_case_study_values():
    r = cs.run()
    assert P.REF_H2_M3D == pytest.approx(r.h2_m3d, abs=0.5)
    assert P.REF_H2_DF_M3D == pytest.approx(r.h2_df_m3d, abs=0.5)
    assert P.REF_H2_PF_M3D == pytest.approx(r.h2_pf_m3d, abs=0.5)
    assert P.REF_H2_P5_M3D == pytest.approx(r.h2_m3d_p5, abs=0.5)
    assert P.REF_H2_P95_M3D == pytest.approx(r.h2_m3d_p95, abs=0.5)
    assert P.PF_FACTOR == pytest.approx(r.total_to_df, abs=0.005)
    assert P.REF_ETA_DF == pytest.approx(r.eta_df_mean, abs=5e-4)


def test_pf_within_literature_enhancement():
    # two-stage DF-PF on sludge/food waste: up to ~35% over DF alone (Methods)
    assert 1.0 < cs.run().total_to_df < 1.35
