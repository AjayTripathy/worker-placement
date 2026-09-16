"""bdc_originations — private-credit deployment as an M&A leading indicator. Sponsor/LBO deals get
FINANCED before they're announced; BDC portfolios are where a big slice of that direct-lending supply
sits. Rising net deployment (gross portfolio growth at cost) across the big BDCs = financing flowing =
M&A supply building. Reuses the frontrun_engine BDC Schedule-of-Investments parser.

Best-effort: if a BDC's latest XBRL won't parse, it's skipped and the basket aggregate uses the rest.
This is a coarse quarterly gauge (the heaviest, least-frequent leg of the stack), not a precise number.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))

BASKET = ["ARCC", "OBDC", "BXSL", "FSK", "GBDC", "MAIN"]   # the high-moat direct lenders


def _total_cost(parsed: dict):
    """Pull invested-at-cost from a parse_soi result, tolerant of key naming."""
    if not parsed:
        return None
    for k in ("total_cost", "cost_total", "investments_at_cost", "total_amortized_cost"):
        if isinstance(parsed.get(k), (int, float)) and parsed[k]:
            return float(parsed[k])
    hs = parsed.get("holdings") or parsed.get("positions")
    if isinstance(hs, list) and hs:
        s = sum((h.get("cost") or 0) for h in hs if isinstance(h, dict))
        if s:
            return float(s)
    return None


def deployment_snapshot() -> dict:
    """Latest-quarter total cost per BDC + the prior quarter, and net deployment (QoQ change)."""
    try:
        import bdc_soi
    except Exception as e:
        return {"error": f"bdc_soi import failed: {e}", "basket": {}}
    out = {}
    for t in BASKET:
        try:
            cur = bdc_soi.fetch_parse_soi(t)
            cur_cost = _total_cost(cur)
            cur_date = (cur or {}).get("filing_date")
            prior = bdc_soi.fetch_parse_soi(t, before_date=cur_date) if cur_date else None
            pri_cost = _total_cost(prior)
            net = (cur_cost - pri_cost) if (cur_cost and pri_cost) else None
            out[t] = {"cur_cost": cur_cost, "prior_cost": pri_cost, "net_deploy": net,
                      "cur_date": cur_date, "prior_date": (prior or {}).get("filing_date")}
        except Exception as e:
            out[t] = {"error": str(e)}
    nets = [v["net_deploy"] for v in out.values() if isinstance(v.get("net_deploy"), (int, float))]
    agg = sum(nets) if nets else None
    pct = None
    if agg is not None:
        base = sum(v["prior_cost"] for v in out.values()
                   if isinstance(v.get("prior_cost"), (int, float)) and isinstance(v.get("net_deploy"), (int, float)))
        pct = (agg / base) if base else None
    return {"basket": out, "agg_net_deploy": agg, "agg_pct_qoq": pct,
            "n_parsed": len(nets), "n_basket": len(BASKET)}


def deployment_state(snap: dict | None = None) -> tuple[str, str]:
    snap = snap or deployment_snapshot()
    pct = snap.get("agg_pct_qoq")
    n = snap.get("n_parsed", 0)
    if pct is None or n < 2:
        return "UNKNOWN", f"only {n} BDCs parsed"
    if pct > 0.03:
        return "EXPANDING", f"+{pct*100:.1f}% QoQ net deployment ({n} BDCs) — financing flowing"
    if pct > 0.0:
        return "STEADY", f"+{pct*100:.1f}% QoQ ({n} BDCs)"
    return "CONTRACTING", f"{pct*100:.1f}% QoQ ({n} BDCs) — deployment shrinking"


if __name__ == "__main__":
    import json
    s = deployment_snapshot()
    print(json.dumps(s, indent=1, default=str))
    print("STATE:", *deployment_state(s))
