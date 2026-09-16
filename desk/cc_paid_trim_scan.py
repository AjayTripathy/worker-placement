"""cc_paid_trim_scan — flag positions whose court sell-ladders are close enough for a PAID trim.

TEMPLATE 3 (ratified 2026-08-21): a covered call is a paid trim order, eligible only on COMPLETED
positions at ladder strikes (six gates in desk/data/csp_shadow_ledger.json _cc_template_ruling).
This scan automates the WHEN: it flags names whose price sits within PROXIMITY_PCT of a resting
sell level, because that is when the free ladder is worth converting to a paid one — far-OTM
ladders pay dust and are correctly left free.

HONEST LIMITS, stated: it reads sell levels from open-order snapshots and ledger entry text, so a
ladder that lives only in a court artifact is invisible; completeness (gate 1) is inferred from
the ABSENCE of resting buys on the same name — verify by hand before proposing; VRP (gate 3) and
qualified-strike (gate 6) checks happen at proposal time via the options surface, not here.

    python3 -m desk.cc_paid_trim_scan
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROXIMITY_PCT = 0.15


def run(verbose: bool = True) -> list[dict]:
    from desk.broken_print_radar import batch_history
    # sell levels from the latest gateway open-order snapshot if present, else ledger text
    sells: dict[str, list[tuple[float, int]]] = {}
    buys: set[str] = set()
    snap = ROOT / "desk/data/open_orders_snapshot.json"
    if snap.exists():
        try:
            for o in json.loads(snap.read_text()):
                t = o.get("symbol", "")
                if o.get("side") == "SELL" and o.get("sec_type", "STK") == "STK":
                    sells.setdefault(t, []).append((float(o["limit_price"]), int(o["quantity"])))
                if o.get("side") == "BUY":
                    buys.add(t)
        except Exception:
            pass
    if not sells:
        rl = json.loads((ROOT / "desk/data/research_ledger.json").read_text())
        for n in rl.get("names", []):
            txt = str(n.get("entry", "")) + str(n.get("conviction", ""))
            for m in re.finditer(r"[Ss]ell\s+(\d+)\s*(?:sh)?\s*@?\s*\$?([0-9]+(?:\.[0-9]+)?)", txt):
                sells.setdefault(n["ticker"], []).append((float(m.group(2)), int(m.group(1))))
            if re.search(r"(BUY|rung|add).{0,20}(rest|GTC|staged)", txt, re.I):
                buys.add(n["ticker"])
    if not sells:
        print("[cc_paid_trim_scan] no sell ladders found in snapshot or ledger — nothing to scan")
        return []
    bars = batch_history(sorted(sells), period="5d", batch=40, retries=2, pause=0.8, verbose=False)
    out = []
    for t, rungs in sells.items():
        b = bars.get(t)
        if not b:
            continue
        cl = [c for c in b["close"] if c is not None]
        if not cl:
            continue
        px = cl[-1]
        for lvl, qty in rungs:
            if px < lvl <= px * (1 + PROXIMITY_PCT):
                out.append({"ticker": t, "px": px, "ladder": lvl, "qty": qty,
                            "distance_pct": round(100 * (lvl / px - 1), 1),
                            "has_resting_buys": t in buys,
                            "note": ("INELIGIBLE gate 1 — resting buys present" if t in buys else
                                     "candidate — run gates 3/6 on the chain before proposing")})
    if verbose:
        if out:
            for r in sorted(out, key=lambda x: x["distance_pct"]):
                print(f"[cc_paid_trim_scan] {r['ticker']:6s} px {r['px']:.2f} ladder {r['ladder']:.2f} "
                      f"({r['distance_pct']:+.1f}%) x{r['qty']} — {r['note']}")
        else:
            print("[cc_paid_trim_scan] no ladders within 15% — the template correctly pays nothing today")
    return out


if __name__ == "__main__":
    run()
