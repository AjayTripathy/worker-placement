"""mft_forward — the MFT sleeve's PROSPECTIVE calibration harness (paper first).

Two-layer forward test (design 2026-07-08; the fix for 'two names isn't enough'):
  LAYER 1 (nowcast accuracy, MONTHLY cadence = fast n): before each monthly
    state/company datapoint posts, freeze our prediction; grade when it posts.
    Calibrates 'can we nowcast the operating metric' ~12x/yr/name.
  LAYER 2 (trading edge, quarterly): before each print, freeze P(beat consensus)
    + P(favorable [print,print+5] price move); grade at the print. The money
    question, 4x/yr/name.

NO REAL MONEY until Layer 2 shows edge NET OF ST TAX across adequate n. This is
a research ledger — freezes are paper predictions, graded into a Brier curve
SEPARATE from the main book (different question).

Ledger: desk/data/mft_forward_ledger.jsonl (append-only; a row gets an outcome
on resolution, never edited otherwise). Cohort: desk/data/mft_cohort.json.

    python3 -m desk.mft_forward              # report: due-to-freeze + to-grade + running calibration
    python3 -m desk.mft_forward freeze ...   # (desk records a prediction)
READ-ONLY on markets.
"""
from __future__ import annotations
import json, datetime, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COHORT = ROOT / "desk" / "data" / "mft_cohort.json"
LEDGER = ROOT / "desk" / "data" / "mft_forward_ledger.jsonl"

def _rows():
    if not LEDGER.exists(): return []
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]

def _brier(rows, pkey):
    graded = [r for r in rows if r.get("outcome") is not None and r.get(pkey) is not None]
    if not graded: return None
    b = sum((r[pkey] - r["outcome"]) ** 2 for r in graded) / len(graded)
    coin = sum((0.5 - r["outcome"]) ** 2 for r in graded) / len(graded)
    return {"n": len(graded), "brier": round(b, 4), "coin": round(coin, 4),
            "beats_coin": b < coin}

def main():
    cohort = json.loads(COHORT.read_text())["names"] if COHORT.exists() else {}
    rows = _rows()
    today = datetime.date.today()
    # upcoming events needing a freeze (within 10d, not yet frozen)
    frozen_keys = {(r["name"], r["event_date"], r["layer"]) for r in rows}
    due = []
    for name, cfg in cohort.items():
        for ev in cfg.get("events", []):
            try:
                dd = (datetime.date.fromisoformat(ev["date"]) - today).days
            except Exception:
                continue
            if 0 <= dd <= 10 and (name, ev["date"], ev["layer"]) not in frozen_keys:
                due.append((dd, name, ev["date"], ev["layer"], ev.get("what", "")))
    # frozen but past event_date, ungraded
    to_grade = [r for r in rows if r.get("outcome") is None
                and r.get("event_date", "9999") < today.isoformat()]

    print(f"[mft_forward] cohort {len(cohort)} names | ledger {len(rows)} freezes")
    print(f"  LAYER-1 (nowcast) calibration: {_brier([r for r in rows if r['layer']=='nowcast'], 'our_p')}")
    print(f"  LAYER-2 (price)   calibration: {_brier([r for r in rows if r['layer']=='price'], 'our_p')}")
    if due:
        print("  DUE TO FREEZE (<=10d):")
        for dd, n, d, l, w in sorted(due): print(f"    in {dd}d  {n} {d} [{l}] {w}")
    if to_grade:
        print("  AWAITING GRADE:", [(r['name'], r['event_date'], r['layer']) for r in to_grade])
    if not cohort:
        print("  cohort empty — populate desk/data/mft_cohort.json (the scout does this)")

def freeze(name, layer, event_date, our_p, estimate=None, consensus=None, data_used="", note=""):
    row = {"name": name, "layer": layer, "event_date": event_date,
           "freeze_date": datetime.date.today().isoformat(), "our_p": our_p,
           "estimate": estimate, "consensus": consensus, "data_used": data_used,
           "note": note, "outcome": None}
    with open(LEDGER, "a") as f: f.write(json.dumps(row) + "\n")
    print(f"[mft_forward] FROZEN {name} {layer} {event_date} p={our_p}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "freeze":
        freeze(*sys.argv[2:])
    else:
        main()
