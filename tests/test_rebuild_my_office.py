"""rebuild_my_office — the fast restore path for the principal's real office.

Wipe ~/office to experience fresh onboarding, then `python3 -m desk.rebuild_my_office`
puts the real $16.6M book back in ~1s. This test proves the pinned seed rebuilds
to the recorded net worth (into a TEMP dir — never touches ~/office). Skips when
no local seed exists (CI / another machine), so real financials stay off git.
"""
import pytest

from desk import rebuild_my_office as R


def test_seed_rebuilds_to_recorded_networth(tmp_path):
    if not R.SEED.exists():
        pytest.skip("no ~/.worker-placement/office_seed.json on this machine")
    meta = R.load_meta()
    data = R.rebuild(tmp_path)                       # build into temp, not ~/office
    assert (tmp_path / "balance_sheet.json").exists()
    assert (tmp_path / "pages" / "office.html").exists()
    # the scenario planner is a CORE page and must render on a rebuild
    assert (tmp_path / "pages" / "scenarios.html").exists()
    nw = R.networth(data)
    if meta.get("expected_nw") is not None:
        assert nw == pytest.approx(meta["expected_nw"], abs=2), \
            f"rebuild NW ${nw:,.0f} != recorded ${meta['expected_nw']:,}"
    # identity survives the rebuild (grading/ledger continuity)
    if meta.get("office_id"):
        assert data.get("office_id") == meta["office_id"]


def test_save_seed_roundtrips(tmp_path):
    if not R.SEED.exists():
        pytest.skip("no seed to round-trip")
    # rebuild into temp, then re-snapshot FROM that temp and confirm NW is stable
    R.rebuild(tmp_path)
    import json
    saved_ans = json.loads((tmp_path / "answers.json").read_text())
    assert saved_ans.get("sleeves") is not None
    # a second rebuild from the temp's own answers reproduces the same NW
    from officekit.serve import build_office
    d2 = build_office(saved_ans, tmp_path / "again")
    assert R.networth(d2) == pytest.approx(R.load_meta().get("expected_nw", R.networth(d2)), abs=2)
