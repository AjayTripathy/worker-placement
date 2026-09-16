"""
test_bdc_soi.py — unit tests for the BDC Schedule-of-Investments parser + re-mark (A-5).

Run: python3 engine/test_bdc_soi.py   (from the frontrun_engine dir)

Locked ARCC unit test (spec §4 of the A-5 task):
  1. Parse the latest 10-Q SoI.
  2. Fair-value tie-out: sum(holdings FV) ties the balance-sheet total investments (<1%).
  3. L3% ~ the Phase-1 XBRL figure (~97.8%).
  4. NAV reconstruction: net_assets / shares reproduces the filed NAV/share (<$0.02).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import bdc_soi

ARCC_PHASE1_L3_PCT = 97.8       # universe_classified.json -> ARCC l3_pct_invest
ARCC_FILED_NAVPS = 19.59        # arcc-20260331 10-Q, NetAssetValuePerShare


def test_arcc_soi():
    p = bdc_soi.fetch_parse_soi('ARCC')
    assert p['n_holdings'] > 1000, f"too few holdings parsed: {p['n_holdings']}"

    # (2) fair-value tie-out
    pct = abs(p['tie_out']['pct_diff'])
    assert pct < 1.0, f"FV tie-out off by {pct:.2f}% (>1%)"

    # (3) L3% vs Phase-1
    assert abs(p['l3_pct_invest'] - ARCC_PHASE1_L3_PCT) < 0.5, \
        f"L3% {p['l3_pct_invest']:.2f} != Phase-1 {ARCC_PHASE1_L3_PCT}"

    # (4) NAV reconstruction
    recon = p['net_assets'] / p['shares_outstanding']
    nav_err = abs(recon - ARCC_FILED_NAVPS)
    assert nav_err < 0.02, f"NAV reconstruction error ${nav_err:.4f} (>$0.02)"

    print(f"  [PASS] ARCC SoI: {p['n_holdings']} holdings, "
          f"FV ${p['total_fair_value']/1e9:.2f}B ties BS to {pct:.2f}%, "
          f"L3={p['l3_pct_invest']:.2f}% (Phase-1 {ARCC_PHASE1_L3_PCT}%), "
          f"NAV recon ${recon:.4f} vs filed ${ARCC_FILED_NAVPS} (err ${nav_err:.4f})")
    return p


def test_arcc_remark_flat_carry(p=None):
    """Zero-driver re-mark must reproduce the filed NAV/share exactly (bookkeeping
    consistency — the official-carry default)."""
    out = bdc_soi.remark_book(p, loan_index_bp_change=0.0, name_events=None)
    derived = out['derived_nav_per_share']
    filed = out['filed_nav_per_share']
    err = abs(derived - filed)
    assert err < 0.02, f"flat-carry NAV mismatch: derived {derived:.4f} vs filed {filed:.4f}"
    print(f"  [PASS] ARCC flat-carry re-mark: derived NAV ${derived:.4f} == filed "
          f"${filed:.4f} (residual non-investment ${out['residual_non_investment']/1e9:+.2f}B)")
    return out


def demo_arcc_credit_widening(p=None):
    """Illustrative re-mark: a +100 bp leveraged-loan-spread widening since the filing."""
    out = bdc_soi.remark_book(p, loan_index_bp_change=100.0, spread_duration_yrs=2.5,
                              smoothing=0.5)
    print(f"  [DEMO] ARCC +100bp credit widening -> derived NAV "
          f"${out['derived_nav_per_share']:.2f} vs filed ${out['filed_nav_per_share']:.2f} "
          f"(surprise {out['surprise_pct']:+.1f}%); "
          f"credit px factor {out['drivers']['credit_px_factor']:.4f}")
    print("         (driver illustrative; Phase-2 sources the index move + per-name events "
          "from primary data)")


if __name__ == '__main__':
    print("BDC SoI PARSER + RE-MARK UNIT TESTS (amendment A-5)")
    p = test_arcc_soi()
    test_arcc_remark_flat_carry(p)
    demo_arcc_credit_widening(p)
    print("ALL TESTS PASSED")
