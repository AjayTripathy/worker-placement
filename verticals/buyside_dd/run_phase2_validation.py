"""Phase-2 conditioning-layer validation runner.

Decisive PODD test + calibration re-confirmation (SPCX/DXYZ/MVIS crowded, GROW undiscovered).
Feeds the LIVE IBKR-MCP underlying-level options data (pulled by the agent at run time) into
discovery_state via mcp_options_underlying, since the TWS per-strike socket was down at build time.
"""
import json
import sys
from connectors.discovery_state import discovery_state

# LIVE IBKR-MCP underlying-level options snapshots pulled 2026-06-24 (NOT fabricated; from
# get_price_snapshot). Only PODD pulled live here; others left None (options UNAVAILABLE → channel
# degrades honestly, which is the correct behavior to demonstrate).
MCP = {
    "PODD": {  # Insulet, get_price_snapshot 2026-06-24
        "last_price": 148.88, "annual_iv": 0.4624587789564249, "hist_vol_annual": 0.5123005304132722,
        "iv_pctile_52w": 0.7091633677482605, "call_volume": 86, "put_volume": 18,
        "avg_call_volume": 188, "avg_put_volume": 61,
    },
}

CASES = [
    # ticker, name, kwargs
    ("PODD", "Insulet", {"cusip": "45784P101", "shares_outstanding": 69_500_000}),
    ("SPCX", "SPAC of America / Spirit", {}),
    ("DXYZ", "Destiny Tech100", {}),
    ("MVIS", "MicroVision", {}),
    ("GROW", "U.S. Global Investors", {}),
]


def run_one(t, name, kw):
    mcp = MCP.get(t)
    st = discovery_state(t, asof="2026-06-24", company_name=name,
                         mcp_options_underlying=mcp, **kw)
    return st


def main():
    only = sys.argv[1].upper() if len(sys.argv) > 1 else None
    results = {}
    for t, name, kw in CASES:
        if only and t != only:
            continue
        st = run_one(t, name, kw)
        results[t] = st
        slim = {k: v for k, v in st.items() if k != "components"}
        print("=" * 78)
        print(json.dumps(slim, indent=2, default=str))
        print("regime drivers:", st["components"].get("_regime_drivers"))
        comp = st["components"]
        for ch in ("options_positioning", "analyst_coverage", "thirteenf"):
            if ch in comp:
                print(f"  {ch}:", json.dumps(comp[ch], default=str)[:400])
    out = "outputs/conditioning_phase2_validation_2026-06-24.json"
    with open(out, "w") as f:
        json.dump({t: r for t, r in results.items()}, f, indent=2, default=str)
    print("\nwrote", out)


if __name__ == "__main__":
    main()
