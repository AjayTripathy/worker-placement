"""
LLM-backfill primary_contractors for J-Book programs that have empty
contractor lists (typical for auto-parsed DARPA / Air Force PEs whose
parser only extracted PE + title + funding).

For each unattributed program:
  1. Compose a context block: program_name, PE, agency, description,
     plus any other narrative the parser captured.
  2. Ask Claude Haiku to enumerate the prime contractors / performers
     named in that text — distinguish "primary contractor" (lead on
     the contract) from "subcontractor" / "performer university" /
     "transition partner" where the text supports it.
  3. Strict JSON output schema.
  4. Merge results into programs.json (filling primary_contractors)
     and re-emit by_entity.json.

If the LLM can't find any named contractors with confidence, it returns
an empty list — we don't fabricate. Confidence is hedged with the
`_extracted_via` provenance tag.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

DATA = Path("verticals/public_co/data/_jbook_data")
PROGRAMS_PATH = DATA / "programs.json"

_MODEL = os.environ.get("BACKFILL_MODEL", "claude-haiku-4-5-20251001")
_KEY_FILE = Path("~/.anthropic_api_key").expanduser()


def _get_client():
    if not _KEY_FILE.exists():
        raise RuntimeError(f"No API key at {_KEY_FILE}")
    from anthropic import Anthropic
    key = _KEY_FILE.read_text().strip()
    return Anthropic(api_key=key)


_SYSTEM = """You are extracting prime contractor names from Pentagon J-Book program text.

A "primary contractor" / "prime" is a private company that has been awarded the actual contract for the program (not a subcontractor, not a performer university, not a transition partner — those are different).

Sources you can use:
- explicit mentions like "Prime contractor: X", "X is the primary performer", "Awarded to X"
- contract numbers like "FA8650-23-C-1234 — Lockheed Martin"
- if the text only names performers, subs, or partners (no clear prime), return them in the `other_named_parties` list, NOT in `primary_contractors`

Output strict JSON only. NO other text. NO markdown.
{
  "primary_contractors": ["Contractor A", "Contractor B"],
  "other_named_parties": [{"name": "X", "role": "subcontractor"|"performer"|"university"|"transition_partner"|"unclear"}],
  "confidence": "high" | "medium" | "low" | "none",
  "evidence_quote": "one short verbatim phrase from the input that supports the extraction, OR empty if confidence=none"
}

If the input text contains no recognizable contractor mention, return:
{"primary_contractors":[],"other_named_parties":[],"confidence":"none","evidence_quote":""}

Do NOT guess from the program type ("AFRL quantum programs are usually awarded to X"). Only extract names that literally appear in the input text."""


def _build_context(p: dict) -> str:
    parts = [
        f"PROGRAM NAME: {p.get('program_name','')}",
        f"PE NUMBER:    {p.get('pe_number','')}",
        f"AGENCY:       {p.get('agency','')}",
    ]
    if p.get("service"):
        parts.append(f"SERVICE:      {p['service']}")
    if p.get("description"):
        parts.append(f"\nDESCRIPTION:\n{p['description']}")
    # narrative_text is what extract_pe_narratives.py emits (full per-PE body)
    body = p.get("narrative_text") or p.get("narrative") or ""
    if body:
        # Truncate at 12k chars to stay well under Haiku's context cap while
        # keeping enough Performer/Contract Info pages
        parts.append(f"\nFULL PE NARRATIVE (extracted from source PDF):\n"
                      f"{body[:12000]}")
    if p.get("program_change_summary"):
        parts.append(f"\nPROGRAM CHANGE SUMMARY:\n{p['program_change_summary'][:1500]}")
    return "\n".join(parts)


def _parse_json(text: str) -> dict:
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```\s*$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def extract_contractors_for_program(client, program: dict) -> dict:
    ctx = _build_context(program)
    backoffs = [0, 2, 5]
    last_err = None
    for delay in backoffs:
        if delay:
            time.sleep(delay)
        try:
            resp = client.messages.create(
                model=_MODEL,
                max_tokens=400,
                system=_SYSTEM,
                messages=[{"role": "user", "content": ctx}],
            )
            text = resp.content[0].text if resp.content else ""
            return _parse_json(text)
        except Exception as e:
            last_err = str(e)
            continue
    return {"primary_contractors": [], "other_named_parties": [],
            "confidence": "none", "evidence_quote": "",
            "error": last_err}


def main():
    corpus = json.loads(PROGRAMS_PATH.read_text())
    programs = corpus["programs"]

    targets = [p for p in programs if not (p.get("primary_contractors") or [])]
    print(f"Programs needing backfill: {len(targets)} / {len(programs)}",
          file=sys.stderr)

    if not targets:
        print("Nothing to do.", file=sys.stderr)
        return

    client = _get_client()

    n_updated = 0
    n_empty = 0
    for i, p in enumerate(targets, 1):
        pid = p.get("program_id") or p.get("pe_number")
        print(f"\n[{i}/{len(targets)}] {pid}: {p.get('program_name','')[:60]}",
              file=sys.stderr)
        t0 = time.time()
        result = extract_contractors_for_program(client, p)
        dt = time.time() - t0
        pcs = result.get("primary_contractors") or []
        others = result.get("other_named_parties") or []
        conf = result.get("confidence", "?")
        print(f"   contractors: {pcs}  others: {len(others)}  conf: {conf}  ({dt:.1f}s)",
              file=sys.stderr)
        if result.get("error"):
            print(f"   ! error: {result['error']}", file=sys.stderr)
            continue
        if pcs:
            p["primary_contractors"] = pcs
            p["_extracted_via"] = f"llm_backfill:{_MODEL}"
            p["_extraction_evidence"] = result.get("evidence_quote", "")
            p["_extraction_confidence"] = conf
            n_updated += 1
        else:
            n_empty += 1
        if others:
            p["other_named_parties"] = others

    PROGRAMS_PATH.write_text(json.dumps(corpus, indent=2, default=str))
    print(f"\nBackfilled {n_updated} programs; {n_empty} had no extractable contractor.",
          file=sys.stderr)
    print(f"Wrote {PROGRAMS_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
