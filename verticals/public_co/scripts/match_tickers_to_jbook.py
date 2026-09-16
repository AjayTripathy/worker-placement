"""
Match resolved ticker entities against the J-Book entity index.

Input:
  - ticker_entity_resolution.json (ticker → name_variants[])
  - by_entity.json (normalized_entity → programs[])

Output: per-ticker match summary + flat ticker→program list. Also re-runs
pentagon_jbook.query_program_funding logic for each matched program to
compute the same FUNDED_*/UNFUNDED_* signal.

Matching strategy:
  1. For each variant in name_variants, compute normalized key
     (same normalizer as build_jbook_entity_index).
  2. Look up exact normalized key in by_entity.json.
  3. For misses, try substring match across all entity keys (one-way:
     variant ⊂ entity OR entity ⊂ variant). This catches "Northrop
     Grumman" → "Northrop Grumman Innovation Systems".

For each match, surface:
  - ticker, variant_name, variant_type (federal_subsidiary, acquisition, etc)
  - matched_entity, matched_programs[] with status/funding
  - severity flag (UNFUNDED_TWO_PLUS_YEARS / FUNDED_SHRINKING are SEVERE)

Output JSON: ticker_program_matches.json.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Optional

from verticals.public_co.scripts.build_jbook_entity_index import normalize

DATA_DIR = Path("verticals/public_co/data")
ENTITY_INDEX = DATA_DIR / "_jbook_data" / "by_entity.json"
RESOLUTIONS = DATA_DIR / "_entity_resolution" / "ticker_entity_resolution.json"
OUT_PATH = DATA_DIR / "_entity_resolution" / "ticker_program_matches.json"

SEVERE_STATUSES = {
    "UNFUNDED_TWO_PLUS_YEARS", "UNFUNDED_THIS_YEAR",
    "TERMINATED", "FUNDED_SHRINKING",
}


def _matches(variant_norm: str, entity_norm: str) -> str | None:
    """Return match-type ('exact'|'variant_in_entity'|'entity_in_variant') or None."""
    if not variant_norm or not entity_norm:
        return None
    if variant_norm == entity_norm:
        return "exact"
    # Don't accept very short partial matches (avoid 'co' → 'lockheed martin')
    if len(variant_norm) < 4 or len(entity_norm) < 4:
        return None
    if variant_norm in entity_norm:
        return "variant_in_entity"
    if entity_norm in variant_norm:
        return "entity_in_variant"
    return None


def match_all() -> dict:
    idx = json.loads(ENTITY_INDEX.read_text())
    entities: dict[str, dict] = idx["entities"]
    resolutions = json.loads(RESOLUTIONS.read_text())["tickers"]

    out: dict[str, dict] = {}
    for tk, info in resolutions.items():
        variants = info.get("name_variants") or []
        ticker_matches: list[dict] = []
        seen_program_ids = set()
        for v in variants:
            vname = v.get("name", "")
            vnorm = normalize(vname)
            vtype = v.get("type", "?")
            vconf = v.get("confidence", "?")
            if not vnorm:
                continue
            for ekey, ent in entities.items():
                match_type = _matches(vnorm, ekey)
                if not match_type:
                    continue
                # Skip if this variant-entity pair is too generic
                # (e.g., "lab" matches every "laboratory" entity)
                if len(vnorm) < 5 and match_type != "exact":
                    continue
                for prog in ent["programs"]:
                    pid = prog["program_id"]
                    if pid in seen_program_ids:
                        continue
                    seen_program_ids.add(pid)
                    severe = prog.get("status") in SEVERE_STATUSES
                    ticker_matches.append({
                        "variant_name": vname,
                        "variant_type": vtype,
                        "variant_confidence": vconf,
                        "matched_entity": ", ".join(ent["display_names"]),
                        "matched_entity_norm": ekey,
                        "match_type": match_type,
                        "program_id":   prog["program_id"],
                        "pe_number":    prog["pe_number"],
                        "program_name": prog["program_name"],
                        "agency":       prog.get("agency"),
                        "status":       prog.get("status"),
                        "latest_fy":    prog.get("latest_fy"),
                        "latest_amt_M": prog.get("latest_amt_M"),
                        "severe":       severe,
                    })
        out[tk] = {
            "ticker": tk,
            "canonical_name": info.get("canonical_name") or info.get("ticker"),
            "n_variants_resolved": len(variants),
            "n_matches": len(ticker_matches),
            "n_severe_matches": sum(1 for m in ticker_matches if m["severe"]),
            "matches": ticker_matches,
        }
    return out


def main():
    matches = match_all()
    OUT_PATH.write_text(json.dumps({
        "_meta": {"n_tickers": len(matches)},
        "matches": matches,
    }, indent=2, default=str))
    print(f"Wrote {OUT_PATH}\n", file=sys.stderr)

    # Sort table by severe count desc, then total match count
    rows = list(matches.values())
    rows.sort(key=lambda r: (-r["n_severe_matches"], -r["n_matches"]))

    print(f"{'TICKER':<7} {'#VAR':>4} {'#MATCH':>6} {'#SEVERE':>7}  TOP MATCHES")
    print("=" * 110)
    for r in rows:
        top = []
        for m in r["matches"][:3]:
            sev = "*" if m["severe"] else " "
            top.append(f"{sev}{m['variant_name'][:18]}→{m['program_id'][:18]}({m['status'] or '-'})")
        print(f"{r['ticker']:<7} {r['n_variants_resolved']:>4} "
              f"{r['n_matches']:>6} {r['n_severe_matches']:>7}  {' | '.join(top)[:80]}")


if __name__ == "__main__":
    main()
