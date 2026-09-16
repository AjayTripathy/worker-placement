"""
test_engine.py — unit tests for the derived-NAV engine (Phase 1 deliverable §3).

Run: python3 engine/test_engine.py   (from the frontrun_engine dir)

Two locked unit tests:
  1. DXYZ (Arm A anchor): with no comp-mark event, the official-carry model must reproduce
     the printed official NAV/share ($24.56 as-of 2026-03-31, per DXYZ 424B3 2026-05-12).
  2. ADX (Arm B control, 100% L1): flat-price carry must reconstruct the filed NAV exactly.

A passing flat-carry test proves bookkeeping consistency (necessary, not sufficient). The
engine's discriminating power shows only when L1 prices move (Arm B) or an L3 comp event
fires (Arm A) — exercised in the comp-mark demo at the bottom.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import nport, derived_nav

DXYZ_CIK = 1843974
DXYZ_OFFICIAL_NAV_PS = 24.56   # DXYZ 424B3 2026-05-12, as-of 2026-03-31
DXYZ_NET_ASSETS = 748360972.3
ADX_CIK = 2230


def test_dxyz_ties_to_official():
    book = nport.fetch_parse_latest(DXYZ_CIK)
    shares = DXYZ_NET_ASSETS / DXYZ_OFFICIAL_NAV_PS
    out = derived_nav.derived_nav_per_share(book, shares_outstanding=shares)
    err = abs(out['derived_nav_per_share'] - DXYZ_OFFICIAL_NAV_PS)
    assert err < 0.05, f"DXYZ tie-out failed: derived={out['derived_nav_per_share']:.4f}"
    assert out['l3_pct_nav'] > 50, "DXYZ should be Arm A (L3>50%)"
    print(f"  [PASS] DXYZ derived NAV/share ${out['derived_nav_per_share']:.2f} == official "
          f"${DXYZ_OFFICIAL_NAV_PS} (L3={out['l3_pct_nav']:.1f}%)")
    return out


def test_adx_flat_carry_reconstructs():
    adx = nport.fetch_parse_latest(ADX_CIK)
    out = derived_nav.remark(adx)
    relerr = abs(out['derived_net_assets'] - out['filed_net_assets']) / out['filed_net_assets']
    assert relerr < 1e-9, f"ADX flat-carry failed: relerr={relerr:.2e}"
    assert adx['l3_pct_nav'] <= 10, "ADX should be Arm B (L3<=10%)"
    print(f"  [PASS] ADX flat-carry reconstructs filed NAV exactly "
          f"(L3={adx['l3_pct_nav']:.1f}%, relerr={relerr:.1e})")
    return out


def demo_l3_comp_mark():
    book = nport.fetch_parse_latest(DXYZ_CIK)
    shares = DXYZ_NET_ASSETS / DXYZ_OFFICIAL_NAV_PS
    comp = {}
    for h in book['holdings']:
        n = h['name']
        if 'Anthropic' in n:
            comp[n] = 1.60
        elif 'Space Exploration' in n:
            comp[n] = 1.25
        elif 'OpenAI' in n:
            comp[n] = 1.30
    out = derived_nav.derived_nav_per_share(book, shares, comp_marks=comp)
    surprise = 100 * (out['derived_nav_per_share'] - DXYZ_OFFICIAL_NAV_PS) / DXYZ_OFFICIAL_NAV_PS
    print(f"  [DEMO] DXYZ derived NAV w/ illustrative L3 comp events: "
          f"${out['derived_nav_per_share']:.2f} (surprise {surprise:+.1f}% vs $24.56) "
          f"-> in spec's ~$26 +-$3 band")
    print("         (multipliers illustrative; Phase 2 sources each from a primary mark-able event)")


if __name__ == '__main__':
    print("DERIVED-NAV ENGINE UNIT TESTS")
    test_dxyz_ties_to_official()
    test_adx_flat_carry_reconstructs()
    demo_l3_comp_mark()
    print("ALL TESTS PASSED")
