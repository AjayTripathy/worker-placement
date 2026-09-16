"""edge_classes — organize the book by EDGE SOURCE, and grade calibration WITHIN class.

Born 2026-07-09. The MFP trade nearly got mis-filed as an MFT (nowcast) win when it
was actually a FLOW (corporate-action) trade — a different skill. Pooling classes gives
a meaningless blended scoreboard. This module makes the classification explicit and the
grading per-class:

  edge_source  = WHY the mispricing is ours (FLOW/INFO/VALUE/CARRY/CONVEXITY/EXCLUSION).
                 The PRIMARY axis. Determines clock, exit doctrine, and calibration cohort.

Classification comes from desk/data/edge_source_map.json (curated), then a default:
verdict==AVOID -> EXCLUSION, else UNCLASSIFIED (surfaced, never silently counted).

What it does:
  1. Backfills research_ledger.json with each name's edge_source.
  2. Rolls up the POSITIONS book by class.
  3. Rolls up OPEN calibration calls by class — the per-class scoreboard. The INFO cohort
     IS the MFT forward test; a FLOW trade can never pad it.
  4. Flags UNCLASSIFIED names for review.

    python3 -m desk.edge_classes             # report + backfill
    python3 -m desk.edge_classes --no-write   # report only
READ-ONLY on markets; writes only the edge_source tag into the ledger.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "desk" / "data"
LEDGER = D / "research_ledger.json"
CALIB = D / "calibration_ledger.jsonl"
MAP = D / "edge_source_map.json"

ORDER = ["FLOW", "INFO", "VALUE", "CARRY", "CONVEXITY", "EXCLUSION", "UNCLASSIFIED"]
# self-audit meta-tickers are not trades — bucket them apart so they don't dilute a class
AUDIT = {"BOOK-SHARPE", "HONESTY-BACKTEST"}


def _map():
    return json.loads(MAP.read_text()).get("map", {})


def classify(ticker: str, verdict: str | None, m: dict) -> str:
    """Curated map wins; else AVOID -> EXCLUSION; else UNCLASSIFIED."""
    if ticker in m:
        return m[ticker]
    if (verdict or "").upper() == "AVOID":
        return "EXCLUSION"
    return "UNCLASSIFIED"


def _jsonl(p):
    out = []
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def main():
    write = "--no-write" not in sys.argv
    m = _map()
    led = json.loads(LEDGER.read_text())

    # 1) classify + backfill positions
    pos_by_class = defaultdict(list)
    unclassified = []
    for n in led["names"]:
        tk = n.get("ticker")
        cls = classify(tk, n.get("verdict"), m)
        n["edge_source"] = cls
        pos_by_class[cls].append(tk)
        if cls == "UNCLASSIFIED":
            unclassified.append(f"{tk} ({n.get('verdict')})")
    if write:
        LEDGER.write_text(json.dumps(led, indent=2, ensure_ascii=False))

    # 2) calibration cohort per class (latest OPEN record per ticker+date)
    seen = {}
    for r in _jsonl(CALIB):
        if (r.get("status") or "OPEN").upper() != "OPEN":
            continue
        seen[(r.get("ticker"), r.get("cat_date"))] = r
    calib_by_class = defaultdict(list)
    for (tk, _), r in seen.items():
        if tk in AUDIT:
            calib_by_class["_AUDIT"].append(r)
            continue
        # calibration tickers may carry venue suffixes / variants; strip to base for the map
        base = str(tk).split(".")[0]
        cls = m.get(tk) or m.get(base) or ("UNCLASSIFIED")
        calib_by_class[cls].append(r)

    # ---- report ----
    print("=" * 64)
    print("EDGE-SOURCE BOOK  —  positions & calibration, graded within class")
    print("=" * 64)
    print("\nPOSITIONS by class:")
    for c in ORDER:
        names = pos_by_class.get(c, [])
        if names:
            print(f"  {c:12} {len(names):3}  {', '.join(sorted(names)[:14])}" + (" …" if len(names) > 14 else ""))

    print("\nOPEN CALIBRATION CALLS by class (the per-class scoreboard):")
    for c in ORDER:
        rs = calib_by_class.get(c, [])
        if not rs:
            continue
        ps = [r.get("our_p") for r in rs if isinstance(r.get("our_p"), (int, float))]
        avg = f"avg p={sum(ps)/len(ps):.2f}" if ps else ""
        tag = "  <- MFT forward test" if c == "INFO" else ""
        print(f"  {c:12} {len(rs):3} calls  {avg}{tag}")
    if calib_by_class.get("_AUDIT"):
        print(f"  {'(self-audit)':12} {len(calib_by_class['_AUDIT']):3}  (BOOK-SHARPE/HONESTY — meta, not a trade class)")

    if unclassified:
        print(f"\n⚠ UNCLASSIFIED positions ({len(unclassified)}) — assign in edge_source_map.json:")
        for u in unclassified:
            print(f"    {u}")
    print("\n" + ("[backfilled research_ledger.edge_source]" if write else "[report only — no write]"))


if __name__ == "__main__":
    main()
