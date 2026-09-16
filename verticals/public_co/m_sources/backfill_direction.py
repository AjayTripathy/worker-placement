"""Heuristic backfill of `direction` field on legacy pilot tuples.

Pilots scored BEFORE the V3 prompt (2026-05-26 release) have tuples
without a `direction` field. Re-scoring all of them is expensive
(~$300+ for the full corpus). This module provides a heuristic that
infers `direction` from the existing tuple text — accurate-enough
to compute approximate recovery_composite values on legacy data.

DIRECTION-INFERENCE RULES (in priority order):

1. severity == RED_FLAG_NEGATIVE → negative
2. severity == SEVERE_UNDERDELIVERY → negative
3. severity == MODERATE_UNDERDELIVERY → negative
4. severity in (PASS, UNVERIFIABLE):
   a. Strong-positive keyword matches → positive
      ("open-market PURCHASE", "code P", "extended maturity",
       "auditor signed off", "remediated", "directors bought",
       "P:S ratio", "post-bad-news buy", "lender concession",
       "lower spread", "released subsidiary guarantor", ...)
   b. Strong-negative keyword matches (PASS-but-honestly-bad) → negative
      ("honestly disclosed", "going concern", "substantial doubt",
       "absence of insider buying", "zero P-buys", ...)
   c. Otherwise → neutral

Run:
  python3 -m verticals.public_co.m_sources.backfill_direction <pilot.json>
  python3 -m verticals.public_co.m_sources.backfill_direction --all   # scan corpus
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "helper",
    "summary": "Heuristic direction backfill for legacy pilot tuples; infra for backtests, never dispatched.",
}

import argparse
import json
import re
import sys
from pathlib import Path


POSITIVE_PATTERNS = [
    r'\bcode\s+P\b(?!\s*\d{3})',
    r'\bP[\s-]code',
    r'\bopen[\s-]market\s+(?:purchas|buy)',
    r'(?:CEO|CFO|Chairman|director|founder|officer)s?\s+(?:bought|purchas|acquir|added\b)',
    r'cluster\s+of\s+(?:insider\s+)?(?:purchas|buy)',
    r'insider(?:s)?\s+(?:are|were)\s+(?:net\s+)?buy',
    r'extended\s+(?:the\s+)?(?:maturity|termination\s+date|term)',
    r'(?:maturity|termination\s+date)\s+extended',
    r'spread\s+(?:was\s+)?(?:cut|reduced|repriced\s+down|stepped\s+down)',
    r'lender\s+concession',
    r'released\s+(?:a\s+|the\s+)?(?:subsidiary\s+guarantor|lien|security)',
    r'(?:remediated|cured|resolved)\s+(?:the\s+)?material\s+weakness',
    r'auditor\s+(?:signed\s+off|attested|validated)\s+(?:on\s+)?remediation',
    r'unqualified\s+(?:audit\s+|ICFR\s+)?opinion(?:\s+restored|\s+post-?cure)',
    r'on[\s-]time\s+(?:filing\s+)?streak',
    r'no\s+NT\s+(?:10-K|10-Q|filing)',
    r'reciprocity[_\s]?confirmed',
    r'bidirectional(?:ly)?\s+confirmed',
    r'counterparty.{0,20}(?:confirms?|verifies?)',
    r'P:S\s+ratio\s+[\d.]+(?:x|:1)(?:[^,]{0,30}positive|[^,]{0,30}buy)',
    r'(?:textbook|clean)\s+(?:honest|recovery|insider-aligned)',
]

NEGATIVE_PATTERNS_PASS = [
    # These flip a PASS into "honestly disclosed bad news" → negative direction
    r'honestly\s+disclos(?:ed|ing)?\s+(?:bad|adverse|distress)',
    r'going\s+concern',
    r'substantial\s+doubt',
    r'(?:zero|no|absence\s+of)\s+(?:insider\s+|open[\s-]market\s+)?(?:purchas|buy|P[\s-]?code)',
    r'no\s+code-?P\s+(?:purchas|buy)',
    r'insider\s+(?:posture|behavior)\s+is\s+(?:net\s+)?(?:sell|bearish|negative)',
    r'NT\s+10-?[KQ]',
    r'late\s+(?:filing|10-?[KQ])',
    r'material\s+weakness\s+(?:present|current|persists?|disclosed)',
    r'ADVERSE\s+(?:audit\s+|ICFR\s+)?opinion',
    r'covenant\s+(?:tightened|amend.{0,20}(?:up|tighter|raised))',
    r'spread\s+(?:was\s+|stepped\s+)?(?:up|raised|increased)',
    r'collateral\s+(?:added|new)',
    r'FILO\s+(?:tranche|facility)',
    r'forbearance',
    r'clustered.{0,30}sell',
]


def infer_direction(tup: dict) -> tuple[str, str]:
    """Return (direction, reason). Reason is a short string for debugging."""
    sev = tup.get("severity") or "PASS"
    if sev == "RED_FLAG_NEGATIVE":
        return ("negative", "severity=RED_FLAG_NEGATIVE")
    if sev == "SEVERE_UNDERDELIVERY":
        return ("negative", "severity=SEVERE_UNDERDELIVERY")
    if sev == "MODERATE_UNDERDELIVERY":
        return ("negative", "severity=MODERATE_UNDERDELIVERY")

    # PASS / UNVERIFIABLE — look at text
    bits = []
    for k in ("R", "f", "M_value", "interpretation"):
        v = tup.get(k, "")
        if isinstance(v, str): bits.append(v)
    text = " ".join(bits)

    for pat in POSITIVE_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return ("positive", f"matched POSITIVE pattern: {m.group(0)[:50]!r}")

    for pat in NEGATIVE_PATTERNS_PASS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return ("negative", f"matched NEGATIVE pattern: {m.group(0)[:50]!r}")

    return ("neutral", "no pattern match")


def backfill_pilot(pilot_path: Path, write: bool = False) -> dict:
    """Read pilot JSON, backfill direction on tuples that lack it. Optionally
    write the result back to disk (overwriting the file)."""
    pilot = json.loads(pilot_path.read_text())
    counts = {"positive": 0, "neutral": 0, "negative": 0, "already_tagged": 0}
    for tup in pilot.get("rfm_tuples") or []:
        if tup.get("direction") in ("positive", "neutral", "negative"):
            counts["already_tagged"] += 1
            continue
        d, reason = infer_direction(tup)
        tup["direction"] = d
        tup["_direction_backfilled"] = reason
        counts[d] += 1
    if write:
        pilot_path.write_text(json.dumps(pilot, indent=2))
    return {"pilot": str(pilot_path), "counts": counts}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pilot_path", nargs="?")
    ap.add_argument("--all", action="store_true", help="scan + backfill the full pilot corpus")
    ap.add_argument("--write", action="store_true", help="write changes back to disk")
    args = ap.parse_args()

    if args.all:
        globs = [
            "verticals/public_co/data/_backtest/*/scores/pilot_*.json",
            "verticals/public_co/data/_forward_test/*/scores/pilot_*.json",
            "verticals/public_co/data/_forward_test/forward_2026_05_25/rescores/pilot_*.json",
        ]
        for g in globs:
            for p in sorted(Path(".").glob(g)):
                r = backfill_pilot(p, write=args.write)
                c = r["counts"]
                print(f"  {p.name:30}  pos={c['positive']:>2}  neu={c['neutral']:>2}  neg={c['negative']:>2}  tagged={c['already_tagged']:>2}")
        return

    if not args.pilot_path:
        ap.error("Provide pilot_path or --all")

    r = backfill_pilot(Path(args.pilot_path), write=args.write)
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()
