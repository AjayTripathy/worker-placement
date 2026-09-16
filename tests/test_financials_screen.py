"""Tests for the financials-specific value scorer.

Covers the load-bearing pure functions: ROE-consistency (volatility penalty + trend), the valuation
IDENTITY check (the ADR lesson — ROE/PB must ~= 1/PE), the structural gates (neg-equity / neg-TBV /
unprofitable), and the court-open surfacing (combined-ratio / PYD for insurers, CET1/NIM for banks).

The insurer combined-ratio gate and the PYD KILL-flag are court-STAGE (they live in the 10-K loss-
development triangle, not in frames) — so what the SCORER owns is: (a) surfacing them as open court
items on every insurer, and (b) the release-funded pattern being nameable.  We test the surfacing here
and assert the insurer buckets carry the PYD kill item.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from verticals.deep_value.financials_screen import (
    roe_series, roe_consistency, valuation_identity, score_name, rank,
    INSURER_BUCKETS, BANK_BUCKETS,
)


# ───────────────────────────────────────────────────────── ROE consistency ──
def test_roe_series_uses_average_equity():
    # NI 100 on equity that went 900->1100 => denom = avg(1000) => 10%
    eq = {2023: 900, 2024: 1100}
    ni = {2024: 100}
    roes = roe_series(eq, ni)
    assert len(roes) == 1
    assert abs(roes[0] - 0.10) < 1e-9


def test_steady_beats_volatile_same_average():
    # both average 20% ROE, but one is steady and one swings 5->35
    steady = roe_consistency([0.20, 0.20, 0.20, 0.20, 0.20])
    volatile = roe_consistency([0.05, 0.35, 0.05, 0.35, 0.20])
    assert abs(steady["avg"] - volatile["avg"]) < 1e-9        # same average
    assert steady["consistency_roe"] > volatile["consistency_roe"]   # steadier wins
    assert volatile["std"] > steady["std"]


def test_trend_bonus_rewards_improving_book():
    improving = roe_consistency([0.08, 0.10, 0.12, 0.14, 0.16])
    declining = roe_consistency([0.16, 0.14, 0.12, 0.10, 0.08])
    # same avg + same std; the improving book scores higher via the trend bonus
    assert abs(improving["avg"] - declining["avg"]) < 1e-9
    assert improving["consistency_roe"] > declining["consistency_roe"]


def test_empty_roe_is_none_not_crash():
    c = roe_consistency([])
    assert c["consistency_roe"] is None and c["n"] == 0


# ─────────────────────────────────────────── valuation identity (ADR lesson) ──
def test_identity_holds_when_consistent():
    # ROE 12%, P/B 1.5 => implied P/E 12.5; reported 12.5 => holds
    r = valuation_identity(pb=1.5, roe_avg=0.12, pe=12.5)
    assert r["flag"] is False
    assert abs(r["implied_pe"] - 12.5) < 0.11


def test_identity_break_flags_adr_style_distortion():
    # the CIB/BCH pattern: yfinance P/B says 9.5 but ROE 16% => implied P/E ~59 while reported P/E is 6
    r = valuation_identity(pb=9.5, roe_avg=0.16, pe=6.0)
    assert r["flag"] is True
    assert "identity BREAK" in r["reason"]


def test_identity_screens_on_implied_when_no_reported_pe():
    r = valuation_identity(pb=1.2, roe_avg=0.10, pe=None)
    assert r["flag"] is False
    assert r["implied_pe"] == 12.0            # 1.2 / 0.10


def test_identity_insufficient_inputs():
    assert valuation_identity(pb=None, roe_avg=0.1, pe=10)["implied_pe"] is None
    assert valuation_identity(pb=1.0, roe_avg=0, pe=10)["implied_pe"] is None


# ───────────────────────────────────────────────── structural gates + surfacing ──
def _base(bucket="insurer_pc", **kw):
    row = {"sym": "TEST", "cik": 1, "bucket": bucket, "mktcap": 1_000e6,
           "equity": 800e6, "ni": 100e6, "goodwill": 0.0, "intangibles": 0.0,
           "equity_hist": {2021: 600e6, 2022: 650e6, 2023: 700e6, 2024: 750e6, 2025: 800e6},
           "ni_hist": {2021: 72e6, 2022: 78e6, 2023: 88e6, 2024: 95e6, 2025: 100e6}}
    row.update(kw)
    return row


def test_insurer_court_open_carries_pyd_kill_and_release_pattern():
    r = score_name(_base(bucket="insurer_specialty"))
    joined = " ".join(r["court_open"])
    assert "PYD=kill" in joined                       # adverse prior-year development = the KILL flag
    assert "release_funded" in joined                 # the RLI release-funded-combined-ratio pattern
    assert "combined_ratio<=100" in joined


def test_bank_court_open_carries_cet1_npa_nim():
    r = score_name(_base(bucket="bank"))
    joined = " ".join(r["court_open"])
    assert "CET1" in joined and "NPA_trend" in joined and "NIM_durability" in joined


def test_negative_tbv_flagged_and_gated():
    # all book is goodwill -> TBV negative -> P/TBV meaningless -> hard gate in rank()
    r = score_name(_base(goodwill=900e6))
    assert r["neg_tbv"] is True
    ranked = rank([r])
    assert ranked[0]["score"] is None                 # gated out (sorts last)


def test_unprofitable_gated():
    r = score_name(_base(ni=-50e6, ni_hist={2024: -50e6, 2023: 10e6}))
    assert r["unprofitable"] is True
    ranked = rank([r])
    assert ranked[0]["score"] is None


def test_pb_disagreement_flag_the_adr_ambiguity():
    # our computed P/B 1.25 vs yfinance 3.0 -> >40% disagreement -> flag for court
    r = score_name(_base(pb_yf=3.0))
    assert r["pb_disagree"] is True


def test_clean_compounder_scores_and_identity_holds():
    r = score_name(_base())
    assert "score" not in r                            # score is assigned in rank(), not score_name
    assert r["roe_avg"] is not None and r["roe_n"] == 5
    assert r["neg_equity"] is False and r["neg_tbv"] is False and r["unprofitable"] is False
    ranked = rank([r])
    assert ranked[0]["score"] is not None             # a clean profitable name is scored


def test_identity_gate_fires_through_score_name_when_pe_present():
    # the MBIN pattern: 5yr-avg ROE ~17% makes P/B 0.94 look cheap (implied P/E ~5.6x), but the reported
    # trailing P/E is 12.3x (EPS collapsed) -> a large identity BREAK that score_name must surface.
    # roe_avg here ~ (16+17+18+17+16)/5 = 16.8%; pb = 940/1000 = 0.94; implied ~5.6x vs reported 12.3x.
    r = score_name(_base(sym="MBINLIKE", mktcap=940e6,
                         equity_hist={2021: 600e6, 2022: 700e6, 2023: 800e6, 2024: 900e6, 2025: 1000e6},
                         ni_hist={2021: 100e6, 2022: 128e6, 2023: 135e6, 2024: 161e6, 2025: 100e6},
                         pe=12.3))
    assert r["identity_flag"] is True                  # book/earnings basis suspect -> court reconciles
    assert r["identity_gap"] is not None and r["identity_gap"] < -0.35

    # the clean case: implied ~= reported -> no flag.  _base() P/B = 1200/800 = 1.5, roe_avg ~13.1%
    # (72/78/88/95/100 on 600->800 equity) -> implied P/E ~11.5x; a reported 11.5x reconciles.
    clean = score_name(_base(sym="CLEAN", mktcap=1200e6, pe=11.5))
    assert clean["identity_flag"] is False and abs(clean["identity_gap"]) <= 0.35


def test_common_earnings_gap_flags_preferred_drag():
    # the MBIN tell: total NI 100 but NI-available-to-common only 60 (preferred drag) -> the frames-avg
    # ROE (off total NI) overstates ROE-to-common -> flag for the court to re-rank on NI-to-common.
    r = score_name(_base(ni=100e6, ni_common=60e6))
    assert r["common_earnings_gap"] is True
    assert r["ni_common"] == 60e6
    # no gap when common ~= total (no preferred, or de minimis)
    r2 = score_name(_base(ni=100e6, ni_common=99e6))
    assert r2["common_earnings_gap"] is False
    # no flag when the concept isn't tagged (ni_common absent) -> silent, not a false fire
    r3 = score_name(_base(ni=100e6))
    assert r3["common_earnings_gap"] is False and r3["ni_common"] is None


def test_rank_orders_cheaper_steadier_first():
    cheap_steady = score_name(_base(sym="CHEAP", mktcap=800e6))   # P/B 1.0, steady ROE
    dear_volatile = score_name(_base(sym="DEAR", mktcap=2000e6,   # P/B 2.5
                                     ni_hist={2021: 40e6, 2022: 130e6, 2023: 30e6,
                                              2024: 140e6, 2025: 100e6}))
    ranked = rank([dear_volatile, cheap_steady])
    assert ranked[0]["sym"] == "CHEAP"                # cheaper + steadier sorts first


if __name__ == "__main__":
    import subprocess
    raise SystemExit(subprocess.call(["python3", "-m", "pytest", __file__, "-v"]))
