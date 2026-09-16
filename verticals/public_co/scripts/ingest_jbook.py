"""
Pentagon J-Book → programs.json ingester.

Parses DoD R-2 RDT&E and P-1 Procurement budget-justification PDFs and
emits/updates entries in `verticals/public_co/data/_jbook_data/programs.json`
for the pentagon_jbook M-source.

USAGE
    python3 -m verticals.public_co.scripts.ingest_jbook PATH_TO_JBOOK.pdf \
        --type rdte \
        --service "Space Force" \
        --document "FY 2027 RDT&E J-Book Vol. 1" \
        --document-date 2026-04 \
        [--limit 500] [--print-only] [--out programs.json]

R-2 EXHIBIT FORMAT (the assumption set)
DoD R-2 exhibits follow a consistent header structure. Per page (or
per multi-page block):

  Exhibit R-2, RDT&E Budget Item Justification: PB <YYYY> <Service>     Date: <Mon YYYY>
  Appropriation/Budget Activity: <activity number>
  R-1 Program Element (Number/Name): PE <PE> | <Title>
  COST ($ in Millions)   Prior Years | FY <N-1> | FY <N> Base | FY <N> OCO | FY <N> Total | FY <N+1> | FY <N+2> | FY <N+3> | FY <N+4> | Cost To Complete | Total Cost
  <Program Element Total>    <numbers>...

The parser finds each "Exhibit R-2" page, regex-extracts the PE number
and title, and parses the first numeric funding row (typically "Program
Element Total" or the PE name itself). Funding numbers can be `0`,
`0.000`, or absent (blank/dash); all are normalized to None or 0.

P-1 EXHIBITS work similarly but with "Exhibit P-1, Procurement Program"
headers and slightly different column shapes. The parser supports both.

FUNDING EXTRACTION (v2 — structure-aware, mirrors sec_tables)
Funding is read PRIMARILY from pdfplumber's table GRID (_funding_from_tables):
find the funding table by its header row (Prior Years / FY YYYY columns), map each
column to an (FY, qualifier), and read the aggregate value row ("Total Program
Element" / "Net Procurement"). This correctly handles the FY Base/OOC/Total triplet
(take the Total column) and blank '-' cells (own grid cell) — which the old positional
regex mis-aligned. The text-regex paths (Program Change Summary / Net-Procurement row)
remain as fallbacks. P-40 line items are detected via the stable "P-1 Line Item Number
/ Title:" field when the inline pattern misses. Golden-master: tests/_golden harness
(_jbook_parser_golden.py); per-PE funding coverage went ~0% → 59-100% on procurement
books, 100% on RDT&E, with zero regressions.

MULTI-PAGE + LIN HANDLING (v3)
- ingest() borrows the funding grid from the CONTINUATION page when a block's own page
  lacks it, guarded by _page_lineitem_or_pe so it never adopts a different exhibit's
  table (Aircraft 59% -> 94% funded; the residual are genuinely fundless sub-items).
- P-40 line-item detection handles variable LIN lengths (Navy 4-digit '1160' through
  Army 10-char '9670A00005'); WPN_Book went 0% -> 100% funded.

LIMITATIONS (v3)
- Project-level granularity below PE is captured only as a free-text description.
- O&M (OP-5/OP-32) and P-1/R-1 SUMMARY exhibits are DELIBERATELY not parsed: OP-32 is
  object-class rows (labor/travel/supplies by code) and OP-5 is activity-group/personnel
  detail — neither maps to the program -> contractor -> ticker model pentagon_jbook uses,
  so ingesting them would add ticker-unmatched noise. Procurement (P-40) + RDT&E (R-2)
  are the contractor-program exhibits and are the parser's scope.
- Classified line items (BA-3, BA-6 with PE_classified flag) are
  reported with status=NOT_FOUND_IN_TIMERANGE and a note.
- The script ONLY appends to programs.json (no overwrite of curated
  entries). Run with --print-only to preview the proposed additions
  without writing.

EXTENDING
- Add new R-2/P-1 column variations to `_FUNDING_HEADER_PATTERNS` if
  encountered in newer J-Books.
- Service-specific PE-number suffixes (SF, AF, A, N, DW, MC) are
  preserved verbatim from the PDF.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import pdfplumber
except ImportError:
    print("pdfplumber required. Install: pip3 install --user pdfplumber",
          file=sys.stderr)
    sys.exit(1)

HERE = Path(__file__).parent.parent / "data" / "_jbook_data"
DEFAULT_OUT = HERE / "programs.json"

# R-2 / P-1 exhibit header detection
_EXHIBIT_HEADER_RE = re.compile(
    r"Exhibit\s+(R-2|R-2A|P-1|P-40)\s*[,:]?\s*"
    r"(RDT&E|Procurement)\s*",
    re.IGNORECASE,
)
# Program Element number patterns:
#   PE 1206410SF, PE 0604411F, PE0604411F, PE 0601101E (DARPA)
_PE_NUMBER_RE = re.compile(
    r"\b(?:PE\s+)?(\d{7,8}[A-Z]{1,3})\b",
    re.IGNORECASE,
)
# PE + title combined pattern — matches the DARPA layout where the cell shows
# "PE 0601101E / DEFENSE RESEARCH SCIENCES" with no colon prefix:
_PE_TITLE_COMBINED_RE = re.compile(
    r"\bPE\s*(\d{7,8}[A-Z]{1,3})\s*[/|\\\-]\s*([A-Z][A-Z0-9 &/\-,'.]{3,120})",
    re.IGNORECASE,
)
# P-40 procurement line-item pattern. Example:
#   "BSA 1: Strategic B02100 / B-21 Raider"
#   "BSA 2: ABC123 / Aircraft Replacement"
# Line Item Number is 5-6 alphanumerics (sometimes starts with a letter),
# followed by " / " and a title.
_P40_LINE_ITEM_RE = re.compile(
    r"\b([A-Z]\d{4,6}|[A-Z]{2}\d{3,5}|\d{5,6}[A-Z]{1,2}|D\d{5})\s*/\s*"
    r"([A-Z][A-Za-z0-9 &/\-,'.]{2,80})",
)
# Procurement funding-table row. Captures values from
#   "Net Procurement (P-1) ($ in Millions) 1,358.431 1,562.693 1,878.868 ..."
_P40_FUNDING_RE = re.compile(
    r"Net\s+Procurement\s*\(P-1\)\s*\(\$\s*in\s*Millions\)\s*"
    r"((?:[\d,.\-]+\s*){4,12})",
)
# The columns we expect from a standard P-40 funding row:
# Prior Years | FY YYYY | FY YYYY | FY YYYY Base | FY YYYY OOC | FY YYYY Total | FY+1 | FY+2 | FY+3 | FY+4 | To Complete | Total
_P40_HEADER_FY_RE = re.compile(r"FY\s*(\d{4})", re.IGNORECASE)
# Funding-summary section header — DARPA format:
#   B. Program Change Summary ($ in Millions) FY 2024 FY 2025 FY 2026 Base FY 2026 OOC FY 2026 Total
_FUNDING_SECTION_RE = re.compile(
    r"(?:Program\s+Change\s+Summary|Cost\s+Summary)\s*\(\$\s*in\s*Millions\)?\s*"
    r"((?:FY\s*\d{4}(?:\s+(?:Base|OOC|Total))?\s*)+)",
    re.IGNORECASE,
)
# Funding line within the summary — pattern matches "Current President's Budget 280.494 293.145 0.000 - 332.425"
_FUNDING_LINE_RE = re.compile(
    r"(?:Current\s+President[’']s\s+Budget|Current\s+Budget\s+Estimate|"
    r"Total\s+Program\s+Element|FY\s*\d{4}\s+President)\s+"
    r"([-\d,.\s]+)",
    re.IGNORECASE,
)
# Funding-table headers we recognize
_FUNDING_HEADER_PATTERNS = [
    r"Prior\s+Years",
    r"FY\s+\d{4}\s+Base",
    r"FY\s+\d{4}\s+Total",
    r"Cost\s+to\s+Complete",
    r"Total\s+Cost",
]
# Funding-row label patterns (the aggregate row, first numeric line)
_TOTAL_ROW_LABELS = (
    "program element total", "total program element",
    "subtotal", "program element",
)
# Money cell pattern: e.g. "1,234.567", "0.000", "0", "-", "Continuing"
_MONEY_RE = re.compile(r"^(?:(\d{1,3}(?:,\d{3})*(?:\.\d+)?)|0(?:\.0+)?|0|-|Continuing)$")


def _extract_money(s: str) -> Optional[float]:
    """Parse a money cell. Returns float (millions) or None for blank/dash/Continuing."""
    s = (s or "").strip().replace(",", "")
    if not s or s in ("-", "Continuing", "Cont"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _normalize_pe(s: str) -> str:
    """Strip 'PE ' prefix, normalize whitespace."""
    return re.sub(r"^\s*PE\s+", "", (s or "").strip(), flags=re.IGNORECASE)


def _parse_funding_from_text(text: str) -> dict[int, Optional[float]]:
    """Parse per-FY funding amounts from R-2 text. DARPA-style format:

        B. Program Change Summary ($ in Millions) FY 2024 FY 2025 FY 2026 Base FY 2026 OOC FY 2026 Total
        Previous President's Budget                311.531  303.830 332.425    -     332.425
        Current President's Budget                 280.494  293.145   0.000    -       0.000
        Total Adjustments                          -31.037  -10.685 -332.425    -    -332.425

    Returns {fy_year: funded_M_current_request}. Uses the *Current Budget*
    line as the authoritative current request — for forward-looking
    funding-status this is the right number (Previous would be the prior
    year's plan that may now be revised).
    """
    out: dict[int, Optional[float]] = {}
    if not text:
        return out

    # Find the funding-summary header
    sec = _FUNDING_SECTION_RE.search(text)
    if not sec:
        return out

    # The header captures: "FY 2024 FY 2025 FY 2026 Base FY 2026 OOC FY 2026 Total"
    header_str = sec.group(1)
    # Extract just unique FY years in column order
    years_in_order: list[int] = []
    seen = set()
    # Process the header as a sequence of "FY YYYY" with optional qualifier
    for m in re.finditer(r"FY\s*(\d{4})\s*(Base|OOC|Total)?", header_str, re.IGNORECASE):
        y = int(m.group(1))
        qual = (m.group(2) or "").upper()
        # When a year has Base/OOC/Total triplet, only take "Total" as the canonical column
        # When a year appears with no qualifier, take it
        if qual in ("BASE", "OOC"):
            continue
        if y in seen:
            continue
        years_in_order.append(y)
        seen.add(y)

    # Find the "Current President's Budget" line (or fallback to "Total Program Element")
    section_text = text[sec.end():sec.end() + 1500]  # look ~1500 chars beyond header
    cur_match = re.search(
        r"Current\s+President[’']?s\s+Budget\s+([-\d,.\s]+?)(?=\n|$)",
        section_text,
        re.IGNORECASE,
    )
    if not cur_match:
        # Fallback: "Total Program Element" or similar
        cur_match = re.search(
            r"(?:Total\s+Program\s+Element|Subtotal)\s+([-\d,.\s]+?)(?=\n|$)",
            section_text,
            re.IGNORECASE,
        )
    if not cur_match:
        return out

    # Parse the numeric run
    nums_str = cur_match.group(1).strip()
    raw_tokens = nums_str.split()
    parsed_nums: list[Optional[float]] = []
    for tok in raw_tokens:
        if tok == "-":
            parsed_nums.append(None)
        else:
            try:
                parsed_nums.append(float(tok.replace(",", "")))
            except ValueError:
                parsed_nums.append(None)

    # Align to years_in_order. If we have Base/OOC/Total triplets in source,
    # the text line will also have 3 numbers per year. We need to pick "Total".
    # Re-walk the header to figure out which numeric index = Total for each year.
    # Strategy: for the header tokens, track which numeric position each year
    # contributes; for "Base" + "OOC" + "Total" within the same year, take Total.
    header_tokens = re.findall(r"FY\s*(\d{4})\s*(Base|OOC|Total)?", header_str, re.IGNORECASE)
    pos = 0  # position in parsed_nums
    year_to_num: dict[int, Optional[float]] = {}
    for y_str, qual in header_tokens:
        y = int(y_str)
        qual_u = (qual or "").upper()
        val = parsed_nums[pos] if pos < len(parsed_nums) else None
        if qual_u in ("", "TOTAL"):
            # Take this number as the authoritative year value
            year_to_num[y] = val
        # advance by 1 token per header position
        pos += 1

    return year_to_num


def _funding_from_tables(page) -> dict[int, Optional[float]]:
    """Structure-aware funding extraction via pdfplumber's table grid (the robust
    primary path; the text-regex methods are fallbacks). Mirrors sec_tables: find the
    funding table by its header row (Prior Years / FY YYYY columns), map each column to
    an (FY, qualifier), then read the aggregate value row ("Total Program Element" /
    "Net Procurement" / first numeric row). Correctly handles the FY Base/OOC/Total
    triplet (each is its own column — take Total) and blank '-' cells (own grid cell),
    which the positional regex got wrong."""
    try:
        tables = page.extract_tables() or []
    except Exception:
        return {}
    _VAL_LABELS = ("total program element", "program element total", "net procurement",
                   "total procurement", "subtotal")
    for tbl in tables:
        if not tbl or len(tbl) < 2:
            continue
        # locate the header row (Prior Years, or >=2 FY YYYY columns)
        hdr_i = None
        for i, row in enumerate(tbl[:6]):
            joined = " ".join((c or "") for c in row)
            if re.search(r"Prior\s*Years", joined, re.I) or len(re.findall(r"FY\s*\d{4}", joined)) >= 2:
                hdr_i = i
                break
        if hdr_i is None:
            continue
        header = tbl[hdr_i]
        col_year: dict[int, tuple[int, str]] = {}
        for ci, cell in enumerate(header):
            m = re.search(r"FY\s*(\d{4})", cell or "")
            if not m:
                continue
            qual = ("TOTAL" if re.search(r"Total", cell, re.I) else
                    "BASE" if re.search(r"Base", cell, re.I) else
                    "OOC" if re.search(r"OOC|OCO", cell, re.I) else "")
            col_year[ci] = (int(m.group(1)), qual)
        if not col_year:
            continue
        # find the aggregate value row
        val_row = None
        for row in tbl[hdr_i + 1:]:
            label = (row[0] or "").strip().lower()
            if any(k in label for k in _VAL_LABELS):
                val_row = row
                break
        if val_row is None:  # fallback: first row with >=2 parseable money cells
            for row in tbl[hdr_i + 1:]:
                money = sum(1 for c in row[1:] if _MONEY_RE.match((c or "").strip()))
                if money >= 2:
                    val_row = row
                    break
        if val_row is None:
            continue
        out: dict[int, Optional[float]] = {}
        for ci, (year, qual) in col_year.items():
            if qual in ("BASE", "OOC"):
                continue  # the per-year Total column is the canonical one
            if year in out and qual != "TOTAL":
                continue  # a TOTAL already won this year
            out[year] = _extract_money(val_row[ci]) if ci < len(val_row) else None
        if any(v is not None for v in out.values()):
            return out
    return {}


def _p40_line_item_from_header(text: str) -> tuple[Optional[str], Optional[str]]:
    """Robust P-40 line-item via the stable 'P-1 Line Item Number / Title:' field.
    The data line is 'Appropriation / BA xx / BSA xx <LIN> / <Title>' — the LIN/Title is
    the LAST '/'-separated pair (e.g. '9670A00005 / MQ-1 UAV'). LIN formats vary
    (9670A00005, B02100, AC1234…), so anchor structurally rather than enumerate."""
    m = re.search(r"Line Item Number\s*/\s*Title:\s*\n?(.+)", text, re.I)
    if not m:
        return None, None
    line = m.group(1).split("\n")[0]
    # LIN length varies: Navy 4-digit (1160), Army 10-char (9670A00005), etc.
    segs = re.findall(r"([A-Z0-9][A-Z0-9\-]{3,14})\s*/\s*([A-Z0-9][A-Za-z0-9 &/\-,'.]{1,70})", line)
    if not segs:
        return None, None
    lin, title = segs[-1]
    return lin.strip(), title.strip()[:80]


def _parse_p40_page(page) -> list[dict]:
    """Extract a P-40 procurement line-item block from one PDF page."""
    text = page.extract_text() or ""
    if "Exhibit P-40" not in text:
        return []
    # Extract Line Item Number + title (legacy inline pattern, else the header field)
    li_match = _P40_LINE_ITEM_RE.search(text)
    if li_match:
        line_item = li_match.group(1).strip()
        title = li_match.group(2).strip().split("\n")[0][:80]
    else:
        line_item, title = _p40_line_item_from_header(text)
        if not line_item:
            return []

    # Funding: structure-aware table grid first; Net-Procurement regex as fallback
    funding_year_map: dict[int, Optional[float]] = _funding_from_tables(page)
    notes = []
    fund_match = None if funding_year_map else _P40_FUNDING_RE.search(text)
    if fund_match:
        # Find the FY year sequence from the resource-summary header
        # ("Prior Years FY 2024 FY 2025 FY 2026 Base FY 2026 OOC FY 2026 Total FY 2027 ...")
        # The values in the funding row align positionally.
        years = _P40_HEADER_FY_RE.findall(text)
        years_seen = []
        for y in years:
            yi = int(y)
            if yi not in years_seen:
                years_seen.append(yi)
        # Parse the value tokens
        raw_vals = fund_match.group(1).strip().split()
        vals = []
        for v in raw_vals:
            v_clean = v.replace(",", "")
            if v_clean in ("-", "—"):
                vals.append(0.0)
                continue
            try:
                vals.append(float(v_clean))
            except ValueError:
                continue
        # Align: vals[0] = Prior Years; vals[1..] correspond to years_seen[0..]
        # In the FY 2026 OOC layout there are 3 columns for FY YYYY Base / OOC / Total.
        # We keep only the Total column (3rd of each FY YYYY triple) for the FY year.
        # For simplicity: pair vals[1:] with years_seen one-to-one for the first
        # few entries; this is approximate.
        for i, y in enumerate(years_seen):
            idx = i + 1  # skip Prior Years
            if idx < len(vals):
                funding_year_map[y] = vals[idx]
        if not funding_year_map:
            notes.append("could_not_parse_p40_funding_row")
    elif not funding_year_map:
        notes.append("no_p40_funding_row_found")

    return [{
        "pe_number":         line_item,  # store as if it were a PE
        "pe_title":          title,
        "funding_year_map":  funding_year_map,
        "page_no":           page.page_number,
        "notes":             notes + ["procurement_p40"],
        "raw_text_excerpt":  text[:600],
        "_budget_activity":  "procurement",
    }]


def _parse_page_blocks(page) -> list[dict]:
    """Extract candidate R-2/P-1 funding blocks from one PDF page.

    Strategy for DARPA-style J-Books:
      1. Check page for R-2 exhibit header
      2. Extract PE number + title via _PE_TITLE_COMBINED_RE
         (DARPA format: 'PE 0601101E / DEFENSE RESEARCH SCIENCES')
      3. Parse 'Program Change Summary' section in text:
         'Current President's Budget' row gives per-FY current request
      4. Build funding_year_map from that text
      5. If R-2 not found but P-40 is, fall through to P-40 parser.
    """
    text = page.extract_text() or ""
    if not _EXHIBIT_HEADER_RE.search(text):
        # Try P-40 procurement format
        return _parse_p40_page(page)

    # If it IS a P-40, use the procurement parser
    if "Exhibit P-40" in text:
        return _parse_p40_page(page)

    # PE number + title (combined regex; first match wins)
    title_match = _PE_TITLE_COMBINED_RE.search(text)
    if title_match:
        pe_number = title_match.group(1).upper()
        pe_title = title_match.group(2).strip()
        # Strip trailing common tokens that bleed in from layout
        pe_title = re.sub(r"\s*(?:Project|R-1.*$|Date:.*$).*$", "", pe_title).strip()
        # Sometimes the title captures multiple words including project info;
        # take the first <= 80-char chunk before a newline
        pe_title = pe_title.split("\n")[0][:80].strip()
    else:
        pe_match = _PE_NUMBER_RE.search(text)
        if not pe_match:
            return []
        pe_number = _normalize_pe(pe_match.group(0)).upper()
        pe_title = None

    # structure-aware table grid first (primary); text-regex (Program Change Summary) fallback
    funding_year_map = _funding_from_tables(page) or _parse_funding_from_text(text)
    notes = []
    if not funding_year_map:
        notes.append("could_not_parse_funding_table")

    return [{
        "pe_number":         pe_number,
        "pe_title":          pe_title,
        "funding_year_map":  funding_year_map,
        "page_no":           page.page_number,
        "notes":             notes,
        "raw_text_excerpt":  text[:600],
    }]


def _block_to_program_entry(block: dict, service: str, document: str,
                             document_date: str) -> dict:
    """Convert a parsed block into a programs.json entry."""
    fyhist = {}
    for year, val in sorted(block["funding_year_map"].items()):
        fyhist[f"FY{year}"] = {"funded_M": val,
                                "note": "auto-extracted from J-Book"}

    pe = block["pe_number"]
    title = block["pe_title"] or f"PE {pe}"
    # Slugified program_id
    slug = re.sub(r"[^A-Za-z0-9]+", "-", title.lower()).strip("-")[:60]
    if not slug:
        slug = f"pe-{pe.lower()}"

    return {
        "program_id":          slug,
        "program_name":        title,
        "synonyms":            [],
        "pe_number":           pe,
        "service":             service,
        "agency":              None,
        "description":         f"Auto-extracted from {document}. {block.get('raw_text_excerpt', '')[:300]}",
        "funding_history":     fyhist,
        "status":              None,  # let pentagon_jbook derive from funding_history
        "primary_contractors": [],
        "documented_in":       [document],
        "source_urls":         [],
        "_provenance":         f"Auto-ingested from {document} ({document_date}) page {block['page_no']}",
        "_parse_notes":        block.get("notes", []),
    }


def _page_lineitem_or_pe(text: str) -> Optional[str]:
    """The line-item (P-40) or PE (R-2) a page declares — used to guard multi-page
    funding borrowing so we never adopt a different exhibit's table."""
    li, _ = _p40_line_item_from_header(text)
    if li:
        return li
    m = _PE_TITLE_COMBINED_RE.search(text)
    if m:
        return m.group(1).upper()
    m = _PE_NUMBER_RE.search(text)
    if m:
        return _normalize_pe(m.group(0)).upper()
    return None


def ingest(pdf_path: Path, *, service: str, document: str, document_date: str,
            limit: Optional[int] = None) -> list[dict]:
    """Parse a J-Book PDF and return a list of program entries."""
    entries: list[dict] = []
    seen_pes = set()
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages):
            if limit and len(entries) >= limit:
                break
            try:
                blocks = _parse_page_blocks(page)
            except Exception as e:
                print(f"  [page {i+1}] parse error: {e}", file=sys.stderr)
                continue
            # Multi-page: a block whose funding table flows to the next (continuation)
            # page. Borrow the next page's grid, but ONLY when that page does not start a
            # different line-item/PE (else we would steal another exhibit's funding).
            nxt = pdf.pages[i + 1] if i + 1 < len(pdf.pages) else None
            for b in blocks:
                if b["funding_year_map"] or nxt is None:
                    continue
                nxt_text = nxt.extract_text() or ""
                nxt_id = _page_lineitem_or_pe(nxt_text)
                if nxt_id and nxt_id != b["pe_number"]:
                    continue
                nf = _funding_from_tables(nxt)
                if nf:
                    b["funding_year_map"] = nf
                    b["notes"] = [n for n in b["notes"]
                                  if "could_not" not in n and not n.startswith("no_")]
                    b["notes"].append("funding_from_next_page")
            for b in blocks:
                pe = b["pe_number"]
                if pe in seen_pes:
                    # Multi-page R-2 — keep the one with more funding data
                    existing = next((e for e in entries if e["pe_number"] == pe), None)
                    if existing and not existing["funding_history"] and b["funding_year_map"]:
                        # Replace the empty one
                        entries.remove(existing)
                    else:
                        continue
                seen_pes.add(pe)
                entries.append(_block_to_program_entry(
                    b, service=service, document=document, document_date=document_date,
                ))
                if (len(entries) % 25) == 0:
                    print(f"  parsed {len(entries)} programs (page {i+1}/{len(pdf.pages)})",
                          file=sys.stderr)
    return entries


def merge_into_corpus(new_entries: list[dict], out_path: Path,
                      preserve_curated: bool = True) -> dict:
    """Append new entries to programs.json without overwriting curated ones.

    Returns {n_new, n_skipped_existing, n_total}."""
    if out_path.exists():
        corpus = json.loads(out_path.read_text())
    else:
        corpus = {
            "_meta": {"description": "Auto-ingested + curated programs.",
                       "schema_version": 1},
            "programs": [],
        }

    # Identity = (pe_number, program-title) — NOT pe_number alone. P-1 procurement LINs
    # ('0145', '0178', ...) are only unique WITHIN an appropriation+service, so dedup by
    # LIN alone false-collides FA-18 (Navy LIN 0145) with an Army LIN 0145. Pairing the
    # LIN with the title disambiguates without relying on a (sometimes-missing) service.
    def _ident(p: dict) -> tuple[str, str]:
        return ((p.get("pe_number") or "").upper(),
                re.sub(r"\s+", " ", (p.get("program_name") or "")).strip().lower()[:40])

    existing_idents = {_ident(p) for p in corpus["programs"]}
    existing_ids = {p.get("program_id") for p in corpus["programs"]}

    n_new = 0
    n_skip = 0
    for entry in new_entries:
        if preserve_curated and _ident(entry) in existing_idents:
            n_skip += 1
            continue
        # De-dup the program_id (storage key must be globally unique)
        base_id = entry["program_id"]
        unique_id = base_id
        suffix = 2
        while unique_id in existing_ids:
            unique_id = f"{base_id}-{suffix}"
            suffix += 1
        entry["program_id"] = unique_id
        corpus["programs"].append(entry)
        existing_idents.add(_ident(entry))
        existing_ids.add(unique_id)
        n_new += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(corpus, indent=2, default=str))
    return {"n_new": n_new, "n_skipped_existing": n_skip,
            "n_total": len(corpus["programs"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", help="Path to the J-Book PDF")
    ap.add_argument("--type", choices=["rdte", "procurement"], default="rdte")
    ap.add_argument("--service", default="(unspecified)",
                     help="Army / Navy / Air Force / Space Force / Defense")
    ap.add_argument("--document", default=None,
                     help='Citation label, e.g. "FY 2027 RDT&E J-Book Vol. 1"')
    ap.add_argument("--document-date", default="",
                     help="When the J-Book was published, e.g. '2026-04'")
    ap.add_argument("--limit", type=int, default=None,
                     help="Stop after N programs parsed (sanity-cap)")
    ap.add_argument("--print-only", action="store_true",
                     help="Print the parsed entries; do not write to programs.json")
    ap.add_argument("--out", default=str(DEFAULT_OUT),
                     help="Output programs.json path")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    document = args.document or pdf_path.stem
    print(f"Parsing {pdf_path.name} (service={args.service}, type={args.type})...",
          file=sys.stderr)
    entries = ingest(pdf_path, service=args.service,
                      document=document, document_date=args.document_date,
                      limit=args.limit)
    print(f"Parsed {len(entries)} program entries.", file=sys.stderr)

    if args.print_only:
        print(json.dumps(entries[:5], indent=2, default=str))
        print(f"... ({len(entries)} total; --print-only suppresses write)",
              file=sys.stderr)
        return

    out_path = Path(args.out)
    summary = merge_into_corpus(entries, out_path)
    print(f"Wrote {out_path}: {summary['n_new']} new, "
          f"{summary['n_skipped_existing']} skipped (PE already in corpus), "
          f"{summary['n_total']} total programs.", file=sys.stderr)


if __name__ == "__main__":
    main()
