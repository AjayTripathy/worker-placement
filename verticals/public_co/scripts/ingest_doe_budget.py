"""
DOE Office of Science Congressional Budget Justification → programs corpus.

Unlike Pentagon J-Books (R-2 exhibit format, regex-parseable), DOE budget
volumes are narrative chapters per program area with embedded funding
tables. We use LLM extraction (Haiku) instead of a regex parser.

Workflow:
  1. Walk the PDF; collect all pages whose text mentions one of our
     target program areas (ASCR, BES, BER, FES, HEP, NP + QIS keywords)
     OR a funding table.
  2. Cluster pages into program sections (10-50 contiguous pages each).
  3. For each section, send the text to Claude with a strict
     extraction schema. Extract:
        program_name, parent_office, fy_funding{FY2024, FY2025, FY2026},
        named_subprograms, named_contractors, qis_relevant (bool).
  4. Write to data/_doe_data/programs.json with the same fields
     pentagon_jbook expects (program_name, pe_number (=DOE program code),
     funding_history, primary_contractors, status=None for derived).

Usage:
    python3 -m verticals.public_co.scripts.ingest_doe_budget \\
        ~/Desktop/jbooks_fy26/doe/FY-2026-Office-of-Science-Budget-Request.pdf
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import pdfplumber

DATA = Path("verticals/public_co/data/_doe_data")
DATA.mkdir(parents=True, exist_ok=True)
OUT = DATA / "programs.json"

_MODEL = os.environ.get("DOE_INGEST_MODEL", "claude-haiku-4-5-20251001")
_KEY_FILE = Path("~/.anthropic_api_key").expanduser()


def _get_client():
    from anthropic import Anthropic
    return Anthropic(api_key=_KEY_FILE.read_text().strip())


_SYSTEM = """You extract structured program entries from a DOE Office of Science Congressional Budget Justification chapter.

INPUT: a contiguous chunk of text from a DOE budget document covering one program area (e.g., "Advanced Scientific Computing Research" or "Basic Energy Sciences").

OUTPUT: strict JSON, no markdown. A list of program entries. Each entry:
{
  "program_name":     "Quantum Information Science Research Centers",
  "parent_office":    "ASCR",
  "doe_program_code": "ASCR-QIS" (or null if no formal code),
  "fy_funding": {
    "FY2024": 245.0,   // ALL VALUES in millions of dollars
    "FY2025": 215.0,
    "FY2026": 180.0
  },
  "subprograms":      ["Argonne Q-NEXT", "Brookhaven C2QA", ...] (named subcenters / awardees if listed),
  "named_contractors": ["IonQ", "Rigetti", "D-Wave"] (commercial vendors/awardees mentioned in narrative),
  "qis_relevant":     true | false,
  "narrative_snippet": "one-sentence excerpt showing why this is QIS-relevant",
  "evidence_quote":   "one verbatim phrase from the text that supports the funding numbers"
}

RULES:
- ONLY extract programs that have explicit FY-by-FY funding numbers. If text doesn't include a dollar table, skip.
- DOE often shows "FY 2024 Enacted / FY 2025 Enacted / FY 2026 Request" — capture all three.
- Convert dollars-in-thousands to millions (divide by 1000).
- qis_relevant = true if the program funds quantum information science, quantum computing, quantum networks, quantum sensors, or names commercial quantum vendors.
- DO NOT fabricate. If a number isn't clearly stated, omit that FY.

Multiple programs per chunk OK. Return [] if no program with funding numbers is extractable."""


def _parse_json(text: str):
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```\s*$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", t, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def chunk_pdf(pdf_path: Path, *, pages_per_chunk: int = 12) -> list[dict]:
    chunks = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        n = len(pdf.pages)
        for start in range(0, n, pages_per_chunk):
            end = min(start + pages_per_chunk, n)
            parts = []
            for i in range(start, end):
                try:
                    parts.append(pdf.pages[i].extract_text() or "")
                except Exception:
                    continue
            text = "\n".join(parts)
            if len(text.strip()) < 500:
                continue
            chunks.append({
                "start_page": start + 1,
                "end_page":   end,
                "text":       text,
            })
    return chunks


def extract_chunk(client, chunk: dict) -> list[dict]:
    """LLM-extract program entries from one PDF chunk."""
    backoffs = [0, 2, 5]
    for delay in backoffs:
        if delay:
            time.sleep(delay)
        try:
            resp = client.messages.create(
                model=_MODEL,
                max_tokens=1500,
                system=_SYSTEM,
                messages=[{"role": "user",
                            "content": chunk["text"][:14000]}],
            )
            txt = resp.content[0].text if resp.content else ""
            data = _parse_json(txt)
            if isinstance(data, dict):
                data = [data]
            return data or []
        except Exception as e:
            print(f"  ! LLM err: {e}", file=sys.stderr)
            continue
    return []


def _to_program_entry(ext: dict, source_doc: str, pages: tuple[int, int]) -> dict:
    """Convert LLM extraction into our standard program-entry shape."""
    fy = ext.get("fy_funding") or {}
    funding_history = {}
    for k, v in fy.items():
        if v is None:
            continue
        try:
            funding_history[k] = {
                "funded_M": float(v),
                "note":     "auto-extracted from DOE Office of Science CBR",
            }
        except (TypeError, ValueError):
            continue
    slug = re.sub(r"[^A-Za-z0-9]+", "-",
                  (ext.get("program_name") or "").lower()).strip("-")[:60]
    if not slug:
        slug = f"doe-pp-{pages[0]}"

    return {
        "program_id":          slug,
        "program_name":        ext.get("program_name") or "(unknown)",
        "synonyms":            ext.get("subprograms") or [],
        "pe_number":           ext.get("doe_program_code"),
        "service":             "DOE",
        "agency":              ext.get("parent_office"),
        "description":         (ext.get("narrative_snippet") or "")[:400],
        "funding_history":     funding_history,
        "status":              None,
        "primary_contractors": ext.get("named_contractors") or [],
        "qis_relevant":        bool(ext.get("qis_relevant")),
        "documented_in":       [f"FY 2026 DOE Office of Science Budget Request, pp.{pages[0]}-{pages[1]}"],
        "source_urls":         [],
        "_provenance":         f"Auto-ingested from {source_doc} pages {pages[0]}-{pages[1]} via LLM extraction",
        "_extraction_evidence": ext.get("evidence_quote", ""),
        "_parse_notes":        ["doe_llm_extracted"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages-per-chunk", type=int, default=10)
    ap.add_argument("--limit-chunks", type=int, default=None,
                     help="Only process this many chunks (for cost control)")
    ap.add_argument("--print-only", action="store_true")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    chunks = chunk_pdf(pdf_path, pages_per_chunk=args.pages_per_chunk)
    print(f"Chunked PDF into {len(chunks)} sections "
          f"({args.pages_per_chunk} pages each)", file=sys.stderr)

    if args.limit_chunks:
        chunks = chunks[:args.limit_chunks]
        print(f"Limiting to first {len(chunks)} chunks", file=sys.stderr)

    client = _get_client()
    all_entries: list[dict] = []
    for i, chunk in enumerate(chunks, 1):
        print(f"\n[{i}/{len(chunks)}] pp.{chunk['start_page']}-{chunk['end_page']} "
              f"({len(chunk['text'])} chars)…", file=sys.stderr)
        extracted = extract_chunk(client, chunk)
        for e in extracted:
            if not (e.get("fy_funding") or {}):
                continue
            entry = _to_program_entry(
                e, pdf_path.name,
                (chunk["start_page"], chunk["end_page"]),
            )
            all_entries.append(entry)
            print(f"     + {entry['program_name'][:50]:50}  "
                  f"FYs: {sorted((entry.get('funding_history') or {}).keys())}",
                  file=sys.stderr)

    if args.print_only:
        print(json.dumps(all_entries[:5], indent=2, default=str))
        print(f"\n...({len(all_entries)} total — print-only)", file=sys.stderr)
        return

    # Merge with existing programs.json (preserve curated entries)
    if OUT.exists():
        existing = json.loads(OUT.read_text())
    else:
        existing = {"_meta": {"description": "DOE Office of Science programs corpus."},
                     "programs": []}
    seen_slugs = {p["program_id"] for p in existing.get("programs", [])}
    n_new = 0
    for e in all_entries:
        if e["program_id"] in seen_slugs:
            continue
        existing["programs"].append(e)
        seen_slugs.add(e["program_id"])
        n_new += 1

    OUT.write_text(json.dumps(existing, indent=2, default=str))
    print(f"\nWrote {OUT}: {n_new} new programs ({len(existing['programs'])} total)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
