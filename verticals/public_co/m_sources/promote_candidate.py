"""Candidate-m-source promotion review tool.

For a given candidate name, surfaces:
  - all occurrences across pilots
  - unique pilot count (the convergence signal)
  - sector distribution (does it generalize?)
  - example tuples with verbatim evidence excerpts
  - whether the data source is SEC-EDGAR (durable) or external API (fragile)

Then generates a skeleton Python module for the candidate, ready for
human review + filling in the real logic.

PROMOTION CRITERIA (judgment, not hard rules)
  ≥ 3 unique pilots independently using the candidate → strong promotion signal
  ≥ 2 sectors → generalizes beyond a single industry
  SEC-EDGAR-backed → durable; external-API-backed → fragile but possibly promotable
  Classification rule is repeatable → promotable
  Raw evidence consistently quoted → promotable

USAGE
  python3 -m verticals.public_co.m_sources.promote_candidate <candidate_name>
  python3 -m verticals.public_co.m_sources.promote_candidate --list  # list all candidates
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "helper",
    "summary": "Ring-2 promotion review: surfaces candidate m-source convergence and generates the skeleton module.",
}

import argparse
import re
import sys
from pathlib import Path

from .candidate_log import DEFAULT_GLOBS, aggregate


SKELETON_TEMPLATE = '''"""{name} — promoted from candidate m-source.

PROMOTED FROM
  Original candidate appearances: {n_pilots} pilots / {n_occurrences} tuples
  Sectors: {sectors}
  Tickers: {tickers}

ORIGINAL DATA SOURCE (from candidate_meta)
  {data_source}

ORIGINAL METHOD
  {method}

ORIGINAL CLASSIFICATION RULE
  {classification_rule}

TODO: FILL THIS IN
  - Implement query_{snake_name}(cik, cutoff_date, ...) — the primary function
  - Map raw evidence → categorical signal returned in the dict
  - Add severity + direction mapping rules to AGENT_PROMPT_V3.md
  - Add to the m-source inventory in AGENT_PROMPT_V3.md
"""
from __future__ import annotations

from typing import Any


def query_{snake_name}(cik: str, cutoff_date: str, **kwargs) -> dict[str, Any]:
    """TODO: implement the formal version of this candidate.

    Returns a dict with at minimum:
      signal: <categorical signal>
      _note: <free-text explanation>
    """
    return {{"signal": "NOT_IMPLEMENTED", "_note": "Stub from promote_candidate.py"}}


if __name__ == "__main__":
    import json
    print(json.dumps(query_{snake_name}("0000000000", "2026-05-26"), indent=2))
'''


def to_snake(name: str) -> str:
    """Convert a candidate name to a snake_case module name."""
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", name)
    s = re.sub(r"_+", "_", s).strip("_")
    return s.lower()


def is_sec_edgar_durable(meta: dict) -> bool:
    """Heuristic: is the candidate's data source SEC EDGAR (durable) or
    an external API (fragile)?"""
    if not meta: return False
    src = (meta.get("data_source") or "").lower()
    return any(kw in src for kw in ["edgar", "sec.gov", "sec ", "10-k", "10-q", "8-k", "form 4", "form4"])


def review(candidate_name: str, globs: list[str] = None) -> dict:
    globs = globs or DEFAULT_GLOBS
    _, grouped = aggregate(globs)
    entries = grouped.get(candidate_name)
    if not entries:
        return {"error": f"No occurrences found for {candidate_name!r}"}

    unique_pilots = {(e.get("cik"), e.get("pilot_file")) for e in entries}
    sectors = sorted(set(e.get("sector") or "" for e in entries))
    tickers = sorted(set(e.get("ticker") or "" for e in entries))
    durable_count = sum(1 for e in entries if is_sec_edgar_durable(e.get("candidate_meta") or {}))

    return {
        "candidate_name": candidate_name,
        "n_occurrences": len(entries),
        "n_unique_pilots": len(unique_pilots),
        "sectors": sectors,
        "tickers": tickers,
        "edgar_durable_count": durable_count,
        "edgar_fragile_count": len(entries) - durable_count,
        "entries": entries,
    }


def generate_skeleton(candidate_name: str, review_dict: dict) -> str:
    snake = to_snake(candidate_name)
    # Pick a representative example
    example = (review_dict["entries"][0].get("candidate_meta") or {})
    return SKELETON_TEMPLATE.format(
        name=candidate_name,
        snake_name=snake,
        n_pilots=review_dict["n_unique_pilots"],
        n_occurrences=review_dict["n_occurrences"],
        sectors=", ".join(review_dict["sectors"]),
        tickers=", ".join(review_dict["tickers"][:10]),
        data_source=example.get("data_source", "TODO"),
        method=example.get("method", "TODO"),
        classification_rule=example.get("classification_rule", "TODO"),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate_name", nargs="?",
                    help="Name of the candidate to review/promote")
    ap.add_argument("--list", action="store_true",
                    help="List all candidate names sorted by convergence")
    ap.add_argument("--generate-skeleton", action="store_true",
                    help="Write a stub module to m_sources/<snake_name>.py")
    args = ap.parse_args()

    if args.list:
        _, grouped = aggregate(DEFAULT_GLOBS)
        if not grouped:
            print("No candidate m-sources found in pilot corpus.")
            return
        items = sorted(grouped.items(), key=lambda kv: -len({(e.get("cik"), e.get("pilot_file")) for e in kv[1]}))
        print(f"{'candidate_name':50}  {'occ':>4}  {'pilots':>6}")
        print("-" * 70)
        for name, entries in items:
            unique = len({(e.get("cik"), e.get("pilot_file")) for e in entries})
            print(f"{name[:50]:50}  {len(entries):>4}  {unique:>6}")
        return

    if not args.candidate_name:
        ap.error("Provide candidate_name or --list")

    r = review(args.candidate_name)
    if "error" in r:
        print(r["error"], file=sys.stderr)
        sys.exit(1)

    print(f"Candidate: {r['candidate_name']}")
    print(f"  Occurrences: {r['n_occurrences']}")
    print(f"  Unique pilots: {r['n_unique_pilots']}")
    print(f"  Sectors: {r['sectors']}")
    print(f"  Tickers: {r['tickers']}")
    print(f"  EDGAR-durable: {r['edgar_durable_count']} / external: {r['edgar_fragile_count']}")
    print()
    print(f"PROMOTION READINESS:")
    promote_score = 0
    reasons = []
    if r["n_unique_pilots"] >= 3:
        promote_score += 1; reasons.append(f"✓ {r['n_unique_pilots']} unique pilots (≥3)")
    else:
        reasons.append(f"✗ only {r['n_unique_pilots']} unique pilots (<3)")
    if len([s for s in r["sectors"] if s]) >= 2:
        promote_score += 1; reasons.append(f"✓ {len(r['sectors'])} sectors (≥2)")
    else:
        reasons.append(f"✗ only {len(r['sectors'])} sectors (<2)")
    if r["edgar_durable_count"] >= r["edgar_fragile_count"]:
        promote_score += 1; reasons.append(f"✓ majority EDGAR-durable")
    else:
        reasons.append(f"✗ majority external-API-fragile")

    for line in reasons:
        print(f"  {line}")
    print(f"\n  Score: {promote_score} / 3")

    print()
    print("Example tuple:")
    e = r["entries"][0]
    print(f"  pilot: {e['ticker']} ({e['pilot_file']})")
    print(f"  M_value: {(e.get('M_value') or '')[:200]}")
    print(f"  interpretation: {(e.get('interpretation') or '')[:200]}")
    print(f"  candidate_meta: {e.get('candidate_meta')}")

    if args.generate_skeleton:
        snake = to_snake(args.candidate_name)
        skel_path = Path(f"verticals/public_co/m_sources/{snake}.py")
        if skel_path.exists():
            print(f"\nSkeleton already exists at {skel_path}; not overwriting.")
        else:
            skel_path.write_text(generate_skeleton(args.candidate_name, r))
            print(f"\nWrote skeleton to {skel_path}")


if __name__ == "__main__":
    main()
