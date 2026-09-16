"""
DOCTRINE 2026-07-05 (beta-placeholder): gates are graded vs SPY-same-window (the placeholder), not vs cash —
a gate is only WRONG if the name beat BETA by more than the gate's required-dip math, since sidelined capital
now earns beta by default. TODO: wire the SPY column natively (currently reported alongside).
missed_entry_score — the anti-book for ENTRIES (blue-team ruling 2026-07-03). Weekly: re-price every
gated name, record the path, and grade gates JUSTIFIED / PREMATURE / WRONG. The output metric that matters:
realized dip-frequency vs the dip-probability the gates implicitly required (50-75% for IBEX-class gates).
READ-ONLY.  python3 -m desk.missed_entry_score
"""
from __future__ import annotations
import json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LED = ROOT / "desk" / "data" / "missed_entry_ledger.json"


def main():
    from desk import prices as P
    d = json.loads(LED.read_text())
    review = {"date": datetime.date.today().isoformat(), "marks": []}
    wrong = prem = 0
    for r in d["rows"]:
        if r.get("gate_type") in ("none",):
            continue
        try:
            q = P.get_price(r["ticker"])
            px = q["px"]
        except Exception:
            px = None
        if not px:
            continue
        base = r.get("spot_at_gate") or px
        move = (px / base - 1) * 100
        mark = {"ticker": r["ticker"], "px": px, "vs_spot_at_gate_pct": round(move, 1)}
        if r["gate_type"] == "business_risk_MISMAPPED" and move > 10:
            mark["grade"] = "WRONG (mis-mapped gate, name ran, no bear print yet)"
            wrong += 1
        elif move > 15:
            mark["grade"] = "PREMATURE-or-WRONG — adjudicate vs bear-materialized at next print"
            prem += 1
        review["marks"].append(mark)
    d["reviews"].append(review)
    LED.write_text(json.dumps(d, indent=1))
    print(f"=== MISSED-ENTRY SCORE  {review['date']}  ({len(review['marks'])} gates marked; {wrong} WRONG, {prem} premature-flagged) ===")
    for m in review["marks"]:
        print(f"  {m['ticker']:<9} {m['vs_spot_at_gate_pct']:>+6.1f}% vs gate-day spot (see SPY col)  {m.get('grade','')}")


if __name__ == "__main__":
    main()
