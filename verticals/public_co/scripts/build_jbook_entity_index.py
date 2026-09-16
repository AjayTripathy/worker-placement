"""
Invert programs.json (PE-keyed) → by_entity.json (contractor-keyed).

Output schema:
{
  "_meta": {
    "source": "programs.json",
    "n_entities": int,
    "n_programs_mapped": int,
    "n_programs_missing_contractors": int,
    "generated_at": iso8601,
  },
  "entities": {
    "<normalized_name>": {
      "display_names": ["Lockheed Martin", "Lockheed Martin Corporation", ...],
      "programs": [
        {
          "program_id":  "t3-transport-layer",
          "pe_number":   "1206410SF",
          "program_name":"Tranche 3 Transport Layer",
          "agency":      "Space Development Agency",
          "status":      "UNFUNDED_TWO_PLUS_YEARS",
          "latest_fy":   "FY26",
          "latest_amt":  0.0,
        }, ...
      ],
    }, ...
  },
  "unattributed_programs": [...]  // programs with no primary_contractors
}

Normalization: lowercase + strip + collapse whitespace + drop common
corporate suffixes (Corp, Inc, Ltd, LLC, Holdings, Group). This is just
the index key; display_names preserves the original casing for downstream
LLM disambiguation.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("verticals/public_co/data/_jbook_data")
IN_PATH  = DATA_DIR / "programs.json"
OUT_PATH = DATA_DIR / "by_entity.json"

_SUFFIX_RE = re.compile(
    r"\b(?:corp(?:oration)?|inc|incorporated|ltd|limited|llc|l\.l\.c\.|"
    r"holdings|group|company|co|plc|pbc|sa|nv|ag|gmbh|"
    r"technologies|systems|labs|laboratory|laboratories)\b\.?",
    re.IGNORECASE,
)
_PAREN_RE = re.compile(r"\([^)]*\)")
_PUNCT_RE = re.compile(r"[,.&/\\\-_]+")


def normalize(name: str) -> str:
    """Lowercase, strip parens/suffixes/punct, collapse whitespace."""
    s = (name or "").strip()
    s = _PAREN_RE.sub(" ", s)
    s = _PUNCT_RE.sub(" ", s)
    s = _SUFFIX_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def _latest_funding(funding_history: dict) -> tuple[str | None, float | None]:
    if not funding_history:
        return None, None
    fys = sorted(funding_history.keys())
    if not fys:
        return None, None
    latest = fys[-1]
    v = funding_history[latest]
    if isinstance(v, dict):
        amt = v.get("total") or v.get("base")
    else:
        amt = v
    try:
        amt = float(amt) if amt is not None else None
    except (TypeError, ValueError):
        amt = None
    return latest, amt


def build_index() -> dict:
    corpus = json.loads(IN_PATH.read_text())
    programs = corpus.get("programs", [])

    entities: dict[str, dict] = defaultdict(
        lambda: {"display_names": [], "programs": []}
    )
    unattributed = []

    for p in programs:
        pcs = p.get("primary_contractors") or []
        others = p.get("other_named_parties") or []

        # Filter out non-contractor "others" (government labs, universities,
        # SBIR consortia, etc. — they exist but aren't ticker-mappable as
        # commercial contractors for our screen).
        commercial_others = []
        for o in others:
            nm = (o.get("name") or "").strip() if isinstance(o, dict) else str(o).strip()
            role = (o.get("role") or "").lower() if isinstance(o, dict) else ""
            if not nm:
                continue
            # Skip clearly non-commercial entries
            lname = nm.lower()
            if any(kw in lname for kw in [
                "naval research laboratory", "afrl", "darpa", "nasa",
                "marshall space flight center", "lincoln laboratory",
                "lawrence livermore", "los alamos", "sandia",
                "ffrdc", "federally funded research",
                "university affiliated research",
                "consortium for execution",
                "u.s. ", "u.s.", "us ", "united states",
                "space force", "navy program", "air force ",
                "redstone", "white sands",
                "combat capabilities development",
                "missile defense organization",  # Israeli govt body
                "aviation and missile research",
                "small businesses",  # generic
                "universities",  # generic
            ]):
                continue
            if role in ("university", "transition_partner", "performer") and "university" in lname:
                continue
            commercial_others.append({"name": nm, "role": role or "subcontractor_or_performer"})

        if not pcs and not commercial_others:
            unattributed.append({
                "program_id":   p.get("program_id"),
                "pe_number":    p.get("pe_number"),
                "program_name": p.get("program_name"),
                "agency":       p.get("agency"),
                "description_len": len((p.get("description") or "")),
            })
            continue

        latest_fy, latest_amt = _latest_funding(p.get("funding_history") or {})
        prog_entry_base = {
            "program_id":   p.get("program_id"),
            "pe_number":    p.get("pe_number"),
            "program_name": p.get("program_name"),
            "agency":       p.get("agency"),
            "status":       p.get("status"),
            "latest_fy":    latest_fy,
            "latest_amt_M": latest_amt,
        }
        for pc in pcs:
            nm = (pc or "").strip()
            if not nm:
                continue
            k = normalize(nm)
            if not k:
                continue
            ent = entities[k]
            if nm not in ent["display_names"]:
                ent["display_names"].append(nm)
            ent["programs"].append({**prog_entry_base, "_role": "primary"})

        for o in commercial_others:
            nm = o["name"]
            k = normalize(nm)
            if not k:
                continue
            ent = entities[k]
            if nm not in ent["display_names"]:
                ent["display_names"].append(nm)
            ent["programs"].append({**prog_entry_base, "_role": o["role"]})

    out = {
        "_meta": {
            "source": str(IN_PATH),
            "n_entities": len(entities),
            "n_programs_mapped": sum(len(e["programs"]) for e in entities.values()),
            "n_programs_unattributed": len(unattributed),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "entities": dict(entities),
        "unattributed_programs": unattributed,
    }
    return out


def main():
    idx = build_index()
    OUT_PATH.write_text(json.dumps(idx, indent=2, default=str))
    m = idx["_meta"]
    print(f"Wrote {OUT_PATH}", file=sys.stderr)
    print(f"  entities: {m['n_entities']}", file=sys.stderr)
    print(f"  programs mapped: {m['n_programs_mapped']}", file=sys.stderr)
    print(f"  programs unattributed: {m['n_programs_unattributed']}",
          file=sys.stderr)
    print(f"\nTop entities:", file=sys.stderr)
    for k, v in sorted(idx["entities"].items(),
                        key=lambda x: -len(x[1]["programs"]))[:15]:
        print(f"  {len(v['programs']):2}  {k:35} ({', '.join(v['display_names'])})",
              file=sys.stderr)


if __name__ == "__main__":
    main()
