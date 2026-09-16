"""
For each program in programs.json that has empty primary_contractors,
re-open its source PDF and extract the full per-PE narrative.

A J-Book PE typically spans 4-10 pages of R-2 exhibit text:
  - Header (PE number, title, appropriation)
  - Mission Description / Justification
  - Program Change Summary
  - Performer Information (← contractors often here)
  - Other Program Funding Summary
  - Schedule / Milestones
  - Contract Information

We capture all text from the PE's first page (recorded in _provenance) up
to but not including the start of the next PE (any subsequent page whose
text begins with a new PE header).

Source PDF resolution:
  _provenance: "Auto-ingested from FY 2026 RDTE_SOCOM_PB_2026 (2025-06) page 73"
  → look in ~/Desktop/jbooks_fy26/RDTE_SOCOM_PB_2026.pdf
  → fall back to ~/Desktop/RDTE_SOCOM_PB_2026.pdf
  → fall back to ~/Desktop/<basename>.pdf

This script does NOT modify primary_contractors. It only adds a
narrative_text field. The LLM extractor pass consumes that field
separately.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional

import pdfplumber

DATA = Path("verticals/public_co/data/_jbook_data/programs.json")

# Candidate dirs for source PDFs
PDF_DIRS = [
    Path("~/Desktop/jbooks_fy26").expanduser(),
    Path("~/Desktop").expanduser(),
    Path("~/Downloads").expanduser(),
]

_PE_TITLE_RE = re.compile(
    r"\bPE\s*(\d{7,8}[A-Z]{1,3})\s*[/|\\\-]?\s*([A-Z][A-Z0-9 &/\-,'.]{3,120})",
    re.IGNORECASE,
)


def _resolve_source_pdf(provenance: str) -> Optional[Path]:
    """Parse the _provenance string for the source J-Book name, then find PDF.

    Two strategies:
    1. Exact filename match — works when ingest emitted a filename token
       (e.g., 'RDTE_SOCOM_PB_2026').
    2. Keyword set match — extract the agency/service tokens and look for
       any PDF in the candidate dirs whose stem contains all the tokens.
       Catches 'DARPA RDT&E Master Justification Book' →
       RDTE_Vol1_DARPA_MasterJustificationBook_PB_2026.pdf.
    """
    # Strategy 1: filename-token (legacy ingests use this)
    m = re.search(r"from\s+(?:FY\s*\d{4}\s+)?([\w_\-]+(?:Book|2026|PB))",
                   provenance)
    base = m.group(1) if m else None
    if base:
        for d in PDF_DIRS:
            if not d.exists():
                continue
            for ext in (".pdf",):
                p = d / f"{base}{ext}"
                if p.exists():
                    return p
            for p in d.glob("*.pdf"):
                if base in p.stem:
                    return p

    # Strategy 2: keyword-set match. Pull all distinctive tokens (agency
    # acronyms, words like 'DARPA', 'MDA', 'SOCOM', 'OSD', 'Navy', etc.)
    # and look for a PDF whose stem contains all of them (case-insensitive).
    tokens = set()
    name_match = re.search(r"from\s+(?:FY\s*\d{4}\s+)?(.+?)\s*\(", provenance)
    name = (name_match.group(1) if name_match else provenance).strip()
    for word in re.findall(r"[A-Za-z]{3,}", name):
        if word.lower() in ("from", "auto", "ingested", "the", "book",
                              "justification", "master"):
            continue
        tokens.add(word.upper())
    if tokens:
        for d in PDF_DIRS:
            if not d.exists():
                continue
            for p in d.glob("*.pdf"):
                stem_upper = p.stem.upper()
                if all(t in stem_upper for t in tokens):
                    return p
    return None


def _resolve_page(provenance: str) -> Optional[int]:
    m = re.search(r"page\s+(\d+)", provenance)
    if m:
        return int(m.group(1))
    return None


def _extract_pe_narrative(pdf: pdfplumber.PDF, start_page_1idx: int,
                           target_pe: str, max_pages: int = 12) -> str:
    """Extract narrative starting at start_page (1-indexed) until next PE."""
    parts = []
    npages = len(pdf.pages)
    target_pe_norm = target_pe.upper().strip()
    for i in range(start_page_1idx - 1, min(start_page_1idx - 1 + max_pages, npages)):
        page = pdf.pages[i]
        try:
            text = page.extract_text() or ""
        except Exception:
            continue
        # If we've moved to a different PE header, stop
        if i > start_page_1idx - 1:
            for m in _PE_TITLE_RE.finditer(text):
                pe_here = m.group(1).upper().strip()
                if pe_here and pe_here != target_pe_norm:
                    # Cut text at this point and append the slice before it
                    cut = text[:m.start()]
                    if cut.strip():
                        parts.append(cut)
                    return "\n".join(parts).strip()
        parts.append(text)
    return "\n".join(parts).strip()


def main():
    corpus = json.loads(DATA.read_text())
    programs = corpus["programs"]
    targets = [p for p in programs if not (p.get("primary_contractors") or [])]
    print(f"Programs needing backfill: {len(targets)} / {len(programs)}",
          file=sys.stderr)

    # Group by source PDF for efficient open
    by_pdf: dict[Path, list[dict]] = {}
    no_pdf = []
    for p in targets:
        prov = p.get("_provenance") or ""
        pdf_path = _resolve_source_pdf(prov)
        if not pdf_path:
            no_pdf.append(p.get("program_id"))
            continue
        by_pdf.setdefault(pdf_path, []).append(p)

    if no_pdf:
        print(f"  ! {len(no_pdf)} programs have unresolvable source PDF: "
              f"{no_pdf[:5]}{'...' if len(no_pdf) > 5 else ''}", file=sys.stderr)

    n_updated = 0
    for pdf_path, progs in by_pdf.items():
        print(f"\nOpening {pdf_path.name} ({len(progs)} PEs)...", file=sys.stderr)
        try:
            pdf = pdfplumber.open(str(pdf_path))
        except Exception as e:
            print(f"  ! could not open: {e}", file=sys.stderr)
            continue
        try:
            for p in progs:
                page = _resolve_page(p.get("_provenance") or "")
                if not page:
                    continue
                pe = p.get("pe_number") or ""
                narr = _extract_pe_narrative(pdf, page, pe)
                if narr and len(narr) > 400:  # skip if too short to be useful
                    p["narrative_text"] = narr[:15000]
                    n_updated += 1
        finally:
            pdf.close()

    DATA.write_text(json.dumps(corpus, indent=2, default=str))
    print(f"\nUpdated {n_updated} programs with narrative_text", file=sys.stderr)
    print(f"Wrote {DATA}", file=sys.stderr)


if __name__ == "__main__":
    main()
