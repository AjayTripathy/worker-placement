"""Unit tests for the universal orphan/carry screen (v2 — gateway/EDGAR stack)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "verticals" / "deep_value"))

from orphan_screen import build_rows, coe_for, rank  # noqa: E402

CRP = {"us_mature_erp": 0.0446,
       "countries": {"United States": {"total_erp": 0.0446},
                     "Korea": {"total_erp": 0.04869},
                     "Kazakhstan": {"total_erp": 0.06299}}}
RF = 0.0423


def test_coe_known_country_and_ordering():
    coe, basis = coe_for("United States", CRP, RF)
    assert abs(coe - 0.0869) < 1e-4 and basis == "United States"
    assert coe_for("Kazakhstan", CRP, RF)[0] > coe        # country risk raises the bar


def test_coe_mapping_and_unknown_flagged():
    assert abs(coe_for("South Korea", CRP, RF)[0] - (RF + 0.04869)) < 1e-6
    coe_u, basis_u = coe_for("Atlantis", CRP, RF)
    assert abs(coe_u - (RF + 0.0446)) < 1e-6 and "not in CRP table" in basis_u


def _uni(t, mcap=100e6, last=10.0, country="United States"):
    return {"ticker": t, "name": t, "sector": "X", "country": country,
            "mcap": mcap, "lastsale": last}


def test_build_rows_gateway_remark_and_bases():
    uni = [_uni("GWX"), _uni("FBK"), _uni("TINY", mcap=5e6)]
    gw = {"GWX": {"px": 12.0}}                             # +20% vs lastsale -> mcap re-marked
    t2c = {"GWX": 1, "FBK": 2}
    ni = {1: 15e6, 2: 8e6}
    eq = {1: 100e6, 2: 80e6}
    rows = build_rows(uni, gw, ni, eq, t2c, CRP, RF)
    by = {r["ticker"]: r for r in rows}
    assert "TINY" not in by                                # mcap floor
    assert by["GWX"]["px_basis"] == "gateway" and abs(by["GWX"]["mcap"] - 120e6) < 1
    assert by["FBK"]["px_basis"] == "screener_lastsale" and by["FBK"]["mcap"] == 100e6
    assert abs(by["GWX"]["ey"] - 15e6 / 120e6) < 1e-6      # ey on the RE-MARKED mcap
    assert abs(by["GWX"]["roe"] - 0.15) < 1e-6


def test_missing_fundamentals_counted_never_ranked():
    uni = [_uni("ADR")]                                    # no CIK -> no frames
    rows = build_rows(uni, {}, {}, {}, {}, CRP, RF)
    assert rows[0]["fundamentals_missing"] is True
    assert rank(rows) == []


def test_rank_carry_spread_ordering_and_floor():
    uni = [_uni("CHEAP"), _uni("FAIR"), _uni("RICH"), _uni("LOSS")]
    t2c = {u["ticker"]: i + 1 for i, u in enumerate(uni)}
    ni = {1: 20e6, 2: 9e6, 3: 2e6, 4: -5e6}                # ey 20% / 9% / 2% / negative
    eq = {i: 100e6 for i in (1, 2, 3, 4)}
    rows = build_rows(uni, {}, ni, eq, t2c, CRP, RF)
    ranked = rank(rows)
    assert [r["ticker"] for r in ranked] == ["CHEAP", "FAIR"]    # RICH under CoE, LOSS no carry
    assert ranked[0]["carry_spread"] > ranked[1]["carry_spread"] > 0
