"""
Post-hoc rescorer for legacy scores.

The original round 1-2 LLM scorer subagents applied Heuristic 7
(counterparty-disclosure threshold) aggressively, firing SEVERE or
RED on patterns like "claimed Tier-1 customer's 10-K returns 0 hits."
The newer deterministic_scorer is more conservative — it fires
MODERATE_UNDERDELIVERY in those cases because the absence of a
counterparty disclosure can be a materiality issue (focal company too
small to trigger the counterparty's disclosure threshold) rather than a
real contradiction.

This module walks existing scores.json files and, for any SEVERE / RED
entry that matches a counterparty-silence pattern, downgrades it to
MODERATE_UNDERDELIVERY while preserving the original severity for audit.

Pattern detection: claim's interpretation / M_check / M_value contains
one of the counterparty-silence markers:
  - "heuristic 7", "rule 7", "counterparty disclosure"
  - "counterparty silence", "counterparty's 10-K"
  - "0 hits", "0 mentions", "= 0", "ZERO references", "ZERO mentions"
  - "no SEC-filer corroboration", "0 of"
AND the claim's category suggests counterparty-facing
(partnership / vendor_relationship / customer_pipeline / regulatory_milestone),
OR the M_check field references an external CIK / counterparty name.

Self-disclosure findings (going concern, restatement, EPA FRS absence,
USAspending absence, internal arithmetic) are NOT downgraded — they
don't depend on the counterparty disclosure asymmetry.

Usage:
    python3 -m verticals.public_co.rescore_legacy [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"


# Pattern markers that suggest a counterparty-silence finding (Heuristic 7).
_HEURISTIC_7_MARKERS = [
    r"heuristic\s*7",
    r"rule\s*7",
    r"counterparty\s*disclosure",
    r"counterparty\s*silence",
    r"counterparty['']?s\s*10-?k",
    r"\bzero\s+(references|mentions|hits)",
    r"0\s+(hits|mentions|references)",
    r"=\s*0\b",
    r"no\s+SEC-?filer\s+corroborat",
    r"0\s+of\s+'",  # "0 of 'Iris Energy'" pattern
    r"hard\s+contradiction",  # often paired with Heuristic 7
]

# Markers that signal a NON-Heuristic-7 finding (don't downgrade these).
# Three categories:
#   (a) other heuristics being cited as the PRIMARY frame
#   (b) self-disclosure / filing-grade math findings
#   (c) interpretations that already acknowledge materiality caveat
_PROTECT_MARKERS = [
    # (a) Other heuristics
    r"heuristic\s*3\b", r"heuristic\s*5\b", r"heuristic\s*9\b",
    r"heuristic\s*10\b", r"heuristic\s*11\b",
    r"rule\s*9\b", r"rule\s*10\b",
    r"stage[- ]ladder", r"planned\s+vs\s+operational",
    r"jurisdiction",
    # (b) Self-disclosure / filing-grade
    r"going[- ]concern", r"restate", r"reverse[- ]split",
    r"material\s+weakness", r"ATM\s+(offering|program|net|equity|capacity)",
    r"backlog\s+(decline|fell)", r"epa\s+frs", r"usaspending",
    r"trapped\s+(cash|in\s+china)", r"accumulated\s+deficit",
    r"net\s+loss", r"cash\s+(burn|runway)", r"dilut", r"convertibl",
    r"ICFR", r"share\s*count", r"13D/A",
    r"weichai\s+(exit|sold|resigned)", r"loss\s+of\s+(conditional\s+)?DOE",
    r"runway", r"forfeit",
    r"wind(ing)?[- ]up", r"wound[- ]up", r"wind[- ]down",
    r"100%\s+(of|customer|concentrated)",  # explicit concentration disclosures
    r"private\s+(counterparty|company)",
    # (c) Already-acknowledged materiality caveat
    r"not\s+by\s+itself", r"immaterial", r"materiality\s+caveat",
    r"with\s+caveat", r"with\s+materiality",
]


def _matches_h7(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t, re.IGNORECASE) for p in _HEURISTIC_7_MARKERS)


def _is_protected(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t, re.IGNORECASE) for p in _PROTECT_MARKERS)


def rescore_claim(sc: dict) -> tuple[dict, bool]:
    """Return (possibly-rewritten claim, was_downgraded)."""
    sev = (sc.get("severity") or "").upper()
    if sev not in ("SEVERE_UNDERDELIVERY", "RED_FLAG_NEGATIVE"):
        return sc, False

    bundle = " || ".join([
        str(sc.get("interpretation", "")),
        str(sc.get("M_check", "")),
        str(sc.get("M_value", "")),
    ])

    if not _matches_h7(bundle):
        return sc, False

    # If the finding ALSO contains hard self-disclosure markers, it's a
    # mixed-pattern claim — protect it. The user's critique was specifically
    # about pure counterparty-silence findings.
    if _is_protected(bundle):
        return sc, False

    out = dict(sc)
    out["original_severity"] = sev
    out["severity"] = "MODERATE_UNDERDELIVERY"
    out["interpretation"] = (out.get("interpretation") or "") + (
        "  [POST-HOC: downgraded from " + sev + " to MODERATE — Heuristic 7 pattern "
        "subject to counterparty-materiality caveat: focal company may be too small "
        "to trigger counterparty's disclosure threshold, so silence isn't conclusive.]"
    )
    return out, True


def rescore_file(path: Path) -> dict:
    data = json.loads(path.read_text())
    scores = data.get("scores", [])
    downgrades = []
    new_scores = []
    for sc in scores:
        new_sc, did = rescore_claim(sc)
        new_scores.append(new_sc)
        if did:
            downgrades.append(new_sc["claim_id"])
    data["scores"] = new_scores
    return {
        "file":       str(path.name),
        "ticker":     data.get("ticker"),
        "n_scores":   len(scores),
        "downgrades": downgrades,
        "data":       data,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="*", help="restrict to specific tickers (uppercase)")
    args = ap.parse_args()

    files = sorted(LOCAL.glob("*.scores.json"))
    if args.only:
        whitelist = {t.upper() for t in args.only}
        files = [p for p in files if p.stem.replace(".scores", "").upper() in whitelist]

    total_files = 0
    total_downgrades = 0
    print(f"Scanning {len(files)} scores.json files...")
    for p in files:
        try:
            r = rescore_file(p)
        except json.JSONDecodeError:
            continue
        total_files += 1
        if not r["downgrades"]:
            continue
        total_downgrades += len(r["downgrades"])
        print(f"  {r['ticker'] or p.stem}: downgraded {len(r['downgrades'])} -> {r['downgrades']}")
        if not args.dry_run:
            p.write_text(json.dumps(r["data"], indent=2, default=str))

    print(f"\nTotal: {total_downgrades} severity downgrades across {total_files} files")
    if args.dry_run:
        print("(dry-run: no files written)")


if __name__ == "__main__":
    main()
