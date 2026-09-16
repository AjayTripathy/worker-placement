"""
Appropriations Committee Report → earmarks.json ingester (best-effort).

Targets the canonical Senate/House Appropriations Defense Subcommittee
committee reports — the documents accompanying annual defense
appropriations bills that contain the "Committee Recommended Adjustments"
or "Program Increases" tables.

USAGE
    python3 -m verticals.public_co.scripts.ingest_committee_report \
        PATH_TO_REPORT.pdf \
        --chamber Senate \
        --fy 2025 \
        --citation "Senate Approps Cmte Rpt 118-100" \
        [--print-only] [--out earmarks.json]

WHAT IT DOES
1. Extracts text from each PDF page via pdfplumber.
2. Looks for funding-adjustment tables — typically formatted as:

   PE NUMBER  TITLE                  Budget   Cmte    Change   Notes
                                     Request  Recom.
   1206410SF  Space Development...   500.0    1000.0  +500.0   Program increase
   ...

3. Extracts (PE, requested, enacted, add) tuples.
4. For each row where add > 0 (congressional add): emit a candidate
   earmark entry.

LIMITATIONS (v1)
- Committee report formats vary year-over-year and across House/Senate.
  This parser handles the "Program Increases" table format common
  since FY 2022. Older reports may not parse cleanly.
- Lawmaker attribution is the hardest part: committee reports rarely
  name the sponsoring member of an individual program add. Real
  attribution often requires cross-referencing:
    (a) Member earmark request disclosure forms (filed under House
        Rule XXIII or Senate transparency rules)
    (b) "Items of Special Interest" sections that sometimes attribute
        adds by district / state
    (c) Third-party trackers (Citizens Against Government Waste's
        Pig Book, OpenSecrets earmark databases)
  This parser does NOT attempt automated lawmaker attribution. It
  flags the PE as a candidate earmark with empty sponsors[] and a
  note for the analyst to complete.
- Conference committee reports often combine House + Senate adds with
  modifications. This parser handles single-chamber reports cleanly;
  conference reports need additional logic.

EXTENDING
- Add new chamber-specific table-shape recognizers to
  `_PROGRAM_INCREASE_PATTERNS`.
- Add lawmaker attribution by parsing "Items of Special Interest"
  sections (look for "Senator X requested..." / "Representative Y
  inserted..." language patterns).
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

HERE = Path(__file__).parent.parent / "data" / "_earmark_data"
DEFAULT_OUT = HERE / "earmarks.json"

_EXHIBIT_HEADER_RE = re.compile(
    r"(Program\s+(Increases?|Adjustments?)|"
    r"Congressional\s+Adjustment[s]?|"
    r"Committee\s+Recommended\s+Adjustment[s]?)",
    re.IGNORECASE,
)
_PE_NUMBER_RE = re.compile(
    r"\b(?:PE\s+)?(\d{7,8}[A-Z]{1,3})\b",
    re.IGNORECASE,
)
# Money cell regex — handles "1,234.5", "0", "0.000", "-", "Continuing"
_MONEY_CELL_RE = re.compile(
    r"^\s*((?:-?\d{1,3}(?:,\d{3})*(?:\.\d+)?)|0(?:\.0+)?|-|Cont\.?|Continuing)\s*$"
)


def _extract_money(s: str) -> Optional[float]:
    s = (s or "").strip().replace(",", "")
    if not s or s in ("-", "Continuing", "Cont", "Cont."):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _looks_like_program_increase_table(rows: list[list[str]]) -> bool:
    """Heuristic: does this look like a committee adjustments table?
    Looks for header row with 'Budget Request', 'Committee Recommended',
    'Change' / 'Adjustment' / 'Increase'."""
    if not rows or not rows[0]:
        return False
    hdr = " ".join((c or "") for c in rows[0]).lower()
    triggers = [
        ("budget" in hdr and "request" in hdr),
        ("committee" in hdr and ("recom" in hdr or "mark" in hdr)),
        ("change" in hdr or "adjustment" in hdr or "increase" in hdr),
    ]
    return sum(triggers) >= 2


def _identify_columns(header_row: list[str]) -> dict:
    """From a header row, find which columns are PE, title, request, recom, change."""
    cols = {}
    for i, h in enumerate(header_row or []):
        h_low = (h or "").lower()
        if any(k in h_low for k in ("pe number", "p.e.", "line item",
                                      "program element")):
            cols["pe"] = i
        elif any(k in h_low for k in ("title", "program", "description")) and "pe" not in cols.get("title", []):
            cols.setdefault("title", i)
        elif "request" in h_low or "pres budget" in h_low or "fy" in h_low and "request" in h_low:
            cols["request"] = i
        elif "committee" in h_low or "recom" in h_low or "mark" in h_low:
            cols["recom"] = i
        elif "change" in h_low or "adjustment" in h_low or "increase" in h_low:
            cols["change"] = i
    return cols


def _parse_page(page) -> list[dict]:
    """Extract candidate earmark rows from one PDF page.

    Returns list of dicts: {pe_number, title, requested_M, enacted_M,
    add_M, page_no, raw_row}."""
    text = page.extract_text() or ""
    if not _EXHIBIT_HEADER_RE.search(text):
        return []

    tables = page.extract_tables() or []
    out = []
    for tbl in tables:
        if not tbl or not _looks_like_program_increase_table(tbl):
            continue
        cols = _identify_columns(tbl[0])
        if "pe" not in cols and "title" not in cols:
            continue

        for row in tbl[1:]:
            if not row:
                continue
            pe_cell = row[cols["pe"]] if "pe" in cols and cols["pe"] < len(row) else ""
            title_cell = row[cols["title"]] if "title" in cols and cols["title"] < len(row) else ""
            req_cell = row[cols.get("request", -1)] if cols.get("request", -1) < len(row) else ""
            recom_cell = row[cols.get("recom", -1)] if cols.get("recom", -1) < len(row) else ""
            change_cell = row[cols.get("change", -1)] if cols.get("change", -1) < len(row) else ""

            pe_match = _PE_NUMBER_RE.search(pe_cell or "") or _PE_NUMBER_RE.search(title_cell or "")
            pe = pe_match.group(1) if pe_match else None

            requested_M = _extract_money(req_cell)
            enacted_M = _extract_money(recom_cell)
            change_M = _extract_money(change_cell)
            if change_M is None and requested_M is not None and enacted_M is not None:
                change_M = enacted_M - requested_M

            # Only emit if there's a positive add and we have at least a name or PE
            if change_M is None or change_M <= 0:
                continue
            if not pe and not (title_cell or "").strip():
                continue

            out.append({
                "pe_number":     pe,
                "title":         (title_cell or "").strip(),
                "requested_M":   requested_M,
                "enacted_M":     enacted_M,
                "add_M":         change_M,
                "page_no":       page.page_number,
                "raw_row":       row,
            })
    return out


def ingest(pdf_path: Path, chamber: str, fy: int, citation: str) -> list[dict]:
    """Parse a committee report PDF; return candidate earmark entries.

    Each entry follows the earmarks.json schema, with empty sponsors[]
    and a `_needs_attribution` flag for the analyst to complete."""
    with pdfplumber.open(str(pdf_path)) as pdf:
        all_rows = []
        for page in pdf.pages:
            try:
                rows = _parse_page(page)
            except Exception as e:
                print(f"  page {page.page_number}: parse error: {e}", file=sys.stderr)
                continue
            all_rows.extend(rows)

    # Group by PE number (or by title if no PE)
    grouped: dict[str, dict] = {}
    for r in all_rows:
        key = r["pe_number"] or r["title"][:80]
        existing = grouped.get(key)
        if not existing:
            grouped[key] = r
        else:
            # Same PE on multiple pages — take the larger add
            if (r.get("add_M") or 0) > (existing.get("add_M") or 0):
                grouped[key] = r

    entries = []
    for key, r in grouped.items():
        slug_base = (r["pe_number"] or re.sub(r"[^A-Za-z0-9]+", "-", r["title"].lower()))[:50]
        slug = f"{slug_base}-fy{fy}-{chamber.lower()}".strip("-")
        fy_key = f"FY{fy}"
        entry = {
            "earmark_id":     slug,
            "program_id":     None,  # operator should link to programs.json after review
            "program_name":   r["title"],
            "pe_number":      r["pe_number"],
            "agency":         None,
            "sponsoring_lawmakers": [],
            "annual_history": {
                fy_key: {
                    "requested_M": r["requested_M"],
                    "enacted_M":   r["enacted_M"],
                    "add_M":       r["add_M"],
                    "source":      citation,
                }
            },
            "earmark_type":   "auto-extracted-add",
            "sponsors_currently_in_power": None,
            "active_in_current_fy":         True,
            "active_in_most_recent_year":   True,
            "_provenance":    f"Auto-parsed from {citation} (page {r['page_no']})",
            "_needs_attribution": True,
            "_needs_program_link": True,
        }
        entries.append(entry)
    return entries


def merge_into_corpus(new_entries: list[dict], out_path: Path) -> dict:
    """Append new candidate earmarks to earmarks.json; preserve curated entries."""
    if out_path.exists():
        corpus = json.loads(out_path.read_text())
    else:
        corpus = {
            "_meta": {"description": "Earmarks corpus.", "schema_version": 1},
            "earmarks": [],
        }

    existing_ids = {e.get("earmark_id") for e in corpus.get("earmarks", [])}
    n_new = 0
    n_skip = 0
    for entry in new_entries:
        if entry["earmark_id"] in existing_ids:
            n_skip += 1
            continue
        corpus["earmarks"].append(entry)
        existing_ids.add(entry["earmark_id"])
        n_new += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(corpus, indent=2, default=str))
    return {"n_new": n_new, "n_skipped_existing": n_skip,
            "n_total": len(corpus["earmarks"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", help="Path to the committee report PDF")
    ap.add_argument("--chamber", choices=["Senate", "House", "Conference"],
                     required=True)
    ap.add_argument("--fy", type=int, required=True,
                     help="Fiscal year this report appropriates")
    ap.add_argument("--citation", required=True,
                     help='Human-readable citation, e.g. "Senate Approps Cmte Rpt 118-100"')
    ap.add_argument("--print-only", action="store_true")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {pdf_path.name} ({args.chamber} FY{args.fy})...", file=sys.stderr)
    entries = ingest(pdf_path, chamber=args.chamber, fy=args.fy, citation=args.citation)
    print(f"Found {len(entries)} candidate congressional adds.", file=sys.stderr)
    print(f"NOTE: each needs analyst review to (a) link to a pentagon_jbook "
          f"program_id, (b) fill in sponsoring_lawmakers. Look for "
          f"_needs_attribution / _needs_program_link flags.", file=sys.stderr)

    if args.print_only:
        print(json.dumps(entries[:5], indent=2, default=str))
        print(f"... ({len(entries)} total; --print-only suppresses write)",
              file=sys.stderr)
        return

    summary = merge_into_corpus(entries, Path(args.out))
    print(f"Wrote {args.out}: {summary['n_new']} new, "
          f"{summary['n_skipped_existing']} skipped, "
          f"{summary['n_total']} total earmarks.", file=sys.stderr)


if __name__ == "__main__":
    main()
