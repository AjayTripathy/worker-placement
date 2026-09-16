"""registry_audit — verify the price registry's symbol + currency assumptions against the live feed.

Every mismatch here is a future CBKD/VSH incident. Checks per symbol: (1) feed currency vs registry
currency (after pence normalization), (2) a quote is obtainable at all (symbol drift), (3) live px vs
sticky close (flap detector). Weekly cadence; flags surface via the generic extractor.

  python3 -m desk.registry_audit
"""
from __future__ import annotations
import json, time
from desk import prices as P

CONVERTIBLE = {("GBp", "GBP"), ("GBP", "GBp")}


def main():
    flags, ok = [], 0
    sticky = P._close_cache()
    for t, r in sorted(P.REGISTRY.items()):
        time.sleep(0.4)          # yahoo rate-limit pacing — the audit must not trip itself (MHPC false-flag)
        try:
            import yfinance as yf
            fi = yf.Ticker(r["yf"]).fast_info
            feed_ccy = fi.get("currency")
            px = fi.get("last_price")
        except Exception:
            feed_ccy, px = None, None
        if feed_ccy and feed_ccy != r["ccy"] and (feed_ccy, r["ccy"]) not in CONVERTIBLE:
            flags.append(f"{t}: registry ccy {r['ccy']} but feed reports {feed_ccy}")
        st = sticky.get(r["yf"])
        if px and st and abs(px / st["px"] - 1) > 0.15 and (time.time() - st["asof"]) < 5 * 86400:
            flags.append(f"{t}: live {px} vs sticky close {st['px']} >15% — flap or real move, verify before acting")
        if px is None and st is None:
            flags.append(f"{t}: NO quote and NO sticky close — symbol drift? ({r['yf']})")
        else:
            ok += 1
    print(f"=== REGISTRY AUDIT  ({len(P.REGISTRY)} symbols, {ok} ok, {len(flags)} flags) ===")
    for f in flags:
        print(f"  >>> FLAG REGISTRY: {f}")
    if not flags:
        print("  clean — registry currencies + symbols verified against the feed")


if __name__ == "__main__":
    main()
