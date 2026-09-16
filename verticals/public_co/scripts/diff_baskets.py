"""
Diff a fresh forward-test prescription against a prior snapshot.

Identifies, for each cohort ticker:
  - ADDED to LONG basket (was NEUTRAL/SHORT, now LONG)
  - REMOVED from LONG basket (was LONG, now NEUTRAL/SHORT)
  - MOVED to a different bucket (e.g., LONG → NEUTRAL)
  - Composite drift (significant change while staying in same bucket)
  - NEW (no prior composite)
  - DROPPED (had prior, no current)

Output: data/_jbook_exposure_cohort/REBALANCE_DIFF.md
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

DATA = Path("verticals/public_co/data")
CURRENT_FORWARD = DATA / "_jbook_exposure_cohort" / "forward_test_FY27_FY28.json"
DEFAULT_PRIOR = CURRENT_FORWARD.with_suffix(".prior.json")

LONG_THRESHOLD  = 0.20
SHORT_THRESHOLD = 0.50


def _bucket(comp: float) -> str:
    if comp <= LONG_THRESHOLD:
        return "LONG"
    if comp >= SHORT_THRESHOLD:
        return "SHORT"
    return "NEUTRAL"


def _load_baskets(path: Path) -> dict:
    if not path.exists():
        return {}
    j = json.loads(path.read_text())
    out = {}
    for side in ("long_basket", "short_basket", "neutral"):
        for r in j.get(side, []):
            out[r["ticker"]] = {
                "composite": r["composite"],
                "bucket":    _bucket(r["composite"]),
                "vintage":   r.get("vintage", ""),
            }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", default=str(CURRENT_FORWARD))
    ap.add_argument("--prior",   default=str(DEFAULT_PRIOR),
                     help="Prior snapshot to diff against")
    ap.add_argument("--out",     default=str(DATA / "_jbook_exposure_cohort" / "REBALANCE_DIFF.md"))
    args = ap.parse_args()

    cur = _load_baskets(Path(args.current))
    pri = _load_baskets(Path(args.prior))

    all_tickers = sorted(set(cur.keys()) | set(pri.keys()))

    added       = []  # added to LONG basket
    removed     = []  # removed from LONG basket
    moved_other = []  # moved buckets (not LONG-add/remove)
    drifted     = []  # composite drift > 0.20 in same bucket
    new_t       = []  # had no prior composite
    dropped_t   = []  # was in prior but no longer
    unchanged   = []

    for tk in all_tickers:
        c = cur.get(tk)
        p = pri.get(tk)
        if c and not p:
            new_t.append((tk, c["bucket"], c["composite"]))
            continue
        if p and not c:
            dropped_t.append((tk, p["bucket"], p["composite"]))
            continue
        if c["bucket"] != p["bucket"]:
            if c["bucket"] == "LONG":
                added.append((tk, p["bucket"], p["composite"], c["composite"]))
            elif p["bucket"] == "LONG":
                removed.append((tk, c["bucket"], p["composite"], c["composite"]))
            else:
                moved_other.append((tk, p["bucket"], c["bucket"], p["composite"], c["composite"]))
        elif abs(c["composite"] - p["composite"]) > 0.20:
            drifted.append((tk, c["bucket"], p["composite"], c["composite"]))
        else:
            unchanged.append((tk, c["bucket"], c["composite"]))

    # Build diff report
    lines = []
    w = lines.append
    w(f"# J-Book Exposure — Rebalance Diff")
    w(f"")
    w(f"*Generated {datetime.utcnow().isoformat()}Z*  ")
    w(f"*Prior: `{args.prior}`*  ")
    w(f"*Current: `{args.current}`*\n")

    def _section(title, rows, cols, fmt):
        if not rows:
            w(f"## {title}\n*(none)*\n")
            return
        w(f"## {title} ({len(rows)})\n")
        w(f"| {' | '.join(cols)} |")
        w(f"|{' | '.join('---' for _ in cols)}|")
        for r in rows:
            w(fmt(r))
        w("")

    _section("ADDED to LONG basket", added,
              ["Ticker", "Was", "Old Comp", "New Comp"],
              lambda r: f"| {r[0]} | {r[1]} | {r[2]:.2f} | {r[3]:.2f} |")
    _section("REMOVED from LONG basket", removed,
              ["Ticker", "Now", "Old Comp", "New Comp"],
              lambda r: f"| {r[0]} | {r[1]} | {r[2]:.2f} | {r[3]:.2f} |")
    _section("MOVED between non-LONG buckets", moved_other,
              ["Ticker", "From", "To", "Old Comp", "New Comp"],
              lambda r: f"| {r[0]} | {r[1]} | {r[2]} | {r[3]:.2f} | {r[4]:.2f} |")
    _section("DRIFTED ≥ 0.20 within same bucket", drifted,
              ["Ticker", "Bucket", "Old Comp", "New Comp"],
              lambda r: f"| {r[0]} | {r[1]} | {r[2]:.2f} | {r[3]:.2f} |")
    _section("NEW (no prior composite)", new_t,
              ["Ticker", "Bucket", "Composite"],
              lambda r: f"| {r[0]} | {r[1]} | {r[2]:.2f} |")
    _section("DROPPED (had prior, not in current)", dropped_t,
              ["Ticker", "Was", "Old Comp"],
              lambda r: f"| {r[0]} | {r[1]} | {r[2]:.2f} |")

    w(f"## Summary\n")
    w(f"- LONG additions: {len(added)}")
    w(f"- LONG removals: {len(removed)}")
    w(f"- Bucket moves (non-LONG): {len(moved_other)}")
    w(f"- Composite drifts (≥0.20): {len(drifted)}")
    w(f"- New names: {len(new_t)}")
    w(f"- Dropped names: {len(dropped_t)}")
    w(f"- Unchanged: {len(unchanged)}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    print(f"Wrote diff to {out_path}")


if __name__ == "__main__":
    main()
