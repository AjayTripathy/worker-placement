"""
Extended J-Book ingestion for P-40 procurement and O&M / OP-5 services books.

Extends programs.json with:
  - P-40 procurement line items (per-service P-1 Line Item Number / Title)
  - O&M / OP-5 services activity groups (per-agency line items in O&M books)

The existing `ingest_jbook.py` handles R-2 (RDT&E) and a narrow P-40 format
but doesn't match SOCOM-style line items (e.g., "1000CV2200" — 4 digits + 2
alpha + 4 digits) or services-budget entries. This script uses broader
regex and tags entries with `exhibit_type` so downstream queries can filter.

USAGE
    # Ingest a P-40 procurement book
    python3 -m verticals.public_co.scripts.ingest_jbook_p40_om \\
        verticals/public_co/data/_jbook_pdfs_p40/PROC_SOCOM_PB_2027.pdf \\
        --type p40 --service SOCOM \\
        --document "FY 2027 SOCOM Procurement" --document-date 2026-04

    # Ingest an O&M / OP-5 book
    python3 -m verticals.public_co.scripts.ingest_jbook_p40_om \\
        verticals/public_co/data/_jbook_pdfs_p40/SOCOM_OP-5.pdf \\
        --type om --service SOCOM \\
        --document "FY 2027 SOCOM Operation and Maintenance" \\
        --document-date 2026-04

OUTPUT
    Appends to data/_jbook_data/programs.json with exhibit_type set to
    "P-40" or "OP-5". pentagon_jbook.query_program_funding will return
    these alongside R-2 entries.

LIMITATIONS
    - P-40 procurement: line-item granularity, funding aggregated as
      "Net Procurement (P-1)" totals; per-unit costs not extracted
    - O&M: activity-group granularity (e.g., "BA 01: Operating Forces"
      → individual subactivities). Contractor attribution is best-effort
      via narrative text mining; many O&M items are direct service costs.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import pdfplumber
except ImportError:
    print("pdfplumber required. pip3 install --user pdfplumber", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).parent.parent
DEFAULT_OUT = ROOT / "data" / "_jbook_data" / "programs.json"


# ---------- P-40 PROCUREMENT PARSING ----------

# Matches P-1 line items across multiple service formats:
#   SOCOM:  "BSA 1000CV2200 / CV-22 MODIFICATION"
#   Navy:   "BSA 2: 1250 / TRIDENT II Mods"
#   Army:   "BSA 1: A14000 / Unmanned Aircraft Systems (UAS)"
#   AF:     "BSA 1: B02100 / B-21 Raider"
# Strategy: find the LAST `<code> / <Title>` pair before the title becomes
# a real program name. Codes are 3-15 alphanumerics; titles start with
# capital letter.
_P40_LINEITEM_RE = re.compile(
    r"(?:BSA\s+\d+\s*:\s*|BSA\s+)?"  # optional BSA prefix
    r"([A-Z0-9]{3,15})\s*/\s*"        # the line-item code
    r"([A-Z][A-Za-z0-9 &/\-,'.()]{2,100})",  # the title
)

# Funding row variants in P-40 — different services format differently.
_P40_FUNDING_RE = re.compile(
    r"(?:Net|Total)\s+Procurement\s*\(P-1\)\s*\(\$\s*in\s*Millions\)\s*"
    r"((?:[\d,.\-]+\s+){3,12}[\d,.\-]+)",
)

# Header row showing which FYs are in which columns
_P40_FY_HEADER_RE = re.compile(r"FY\s*(\d{4})", re.IGNORECASE)

# The "Secondary Distribution" table is the cleanest funding source.
# Header pattern: "Secondary Distribution FY YYYY FY YYYY Base OOC Total FY YYYY FY YYYY FY YYYY FY YYYY"
# Data row pattern: "Total Obligation Authority <9 numbers>"
_P40_SECONDARY_HEADER_RE = re.compile(
    r"Secondary\s+Distribution\s+"
    r"FY\s*(?P<fy1>\d{4})\s+FY\s*(?P<fy2>\d{4})\s+"
    r"Base\s+OOC\s+Total\s+"
    r"FY\s*(?P<fy_next>\d{4})\s+FY\s*\d{4}\s+FY\s*\d{4}\s+FY\s*\d{4}",
    re.IGNORECASE,
)
_P40_SECONDARY_DATA_RE = re.compile(
    r"Total\s+Obligation\s+Authority\s+"
    r"((?:[\d,.\-]+\s+){8}[\d,.\-]+)",
)


def parse_p40_pdf(pdf_path: Path, service: str, document: str,
                   document_date: str) -> list[dict]:
    """Extract P-40 procurement entries from a justification PDF."""
    entries = []
    seen_codes = set()
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if "Exhibit P-40" not in text:
                continue

            # Find the line item code + title
            m = _P40_LINEITEM_RE.search(text)
            if not m:
                continue
            line_code, title = m.group(1), m.group(2).strip()
            if line_code in seen_codes:
                continue
            seen_codes.add(line_code)

            # Extract funding from the cleaner "Secondary Distribution" table.
            # Header structure: FY-Prior | FY-Prior+1 | FY-Current Base | OOC | Total | FY-Next | FY+1 | FY+2 | FY+3
            # Data row: 9 numbers matching the above columns.
            funding_history = {}
            hdr = _P40_SECONDARY_HEADER_RE.search(text)
            data = _P40_SECONDARY_DATA_RE.search(text)
            if hdr and data:
                fy_prior_minus_1 = int(hdr.group("fy1"))   # e.g., 2025
                fy_prior         = int(hdr.group("fy2"))   # e.g., 2026
                fy_current       = int(hdr.group("fy_next")) - 1  # e.g., 2027 (next is 2028)
                # Numeric extraction
                raw_nums = re.findall(r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\-)",
                                       data.group(1))
                def _to_float(n):
                    if n in ("-", ""): return None
                    try: return float(n.replace(",", ""))
                    except ValueError: return None
                nums = [_to_float(n) for n in raw_nums]
                if len(nums) >= 9:
                    # Column order: FY-1, FY0, FY+1_Base, FY+1_OOC, FY+1_Total, FY+2, FY+3, FY+4, FY+5
                    funding_history[f"FY{fy_prior_minus_1}"] = {"funded_M": nums[0], "note": "P-40 actual"}
                    funding_history[f"FY{fy_prior}"]         = {"funded_M": nums[1], "note": "P-40 enacted"}
                    funding_history[f"FY{fy_current}"]       = {"funded_M": nums[4], "note": "P-40 request (Base+OOC Total)"}
                    funding_history[f"FY{fy_current+1}"]     = {"funded_M": nums[5], "note": "P-40 outyear"}
                    funding_history[f"FY{fy_current+2}"]     = {"funded_M": nums[6], "note": "P-40 outyear"}
                    funding_history[f"FY{fy_current+3}"]     = {"funded_M": nums[7], "note": "P-40 outyear"}
                    funding_history[f"FY{fy_current+4}"]     = {"funded_M": nums[8], "note": "P-40 outyear"}
            else:
                # Fallback: parse "Net Procurement (P-1)" row directly. Handle
                # the canonical 12-column P-40 header structure:
                #   Prior Years | FY-1 | FY 0 | FY+1 Base | FY+1 OOC | FY+1 Total |
                #   FY+2 | FY+3 | FY+4 | FY+5 | To Complete | Total Cost
                # Key insight: when the page header contains "Base OOC Total"
                # alongside the current FY, the funding row has the triple
                # column expansion and we must skip Base+OOC and use Total.
                fund_match = _P40_FUNDING_RE.search(text)
                if fund_match:
                    raw_nums = re.findall(r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\-)",
                                           fund_match.group(1))
                    num_floats = []
                    for n in raw_nums:
                        if n == "-":
                            num_floats.append(None)
                        else:
                            try: num_floats.append(float(n.replace(",", "")))
                            except ValueError: num_floats.append(None)

                    # Detect 12-column triple-FY structure
                    has_triple = bool(re.search(r"Base\s+OOC\s+Total", text, re.IGNORECASE))

                    # Infer the budget year from the document marker (most reliable)
                    pb_match = re.search(r"PB\s*(\d{4})|Fiscal\s+Year\s*\(?FY\)?\s*(\d{4})", text)
                    budget_fy = None
                    if pb_match:
                        budget_fy = int(pb_match.group(1) or pb_match.group(2))

                    # If we have the budget FY, build the canonical 7-year sequence
                    # [FY-2, FY-1, FY (budget), FY+1, FY+2, FY+3, FY+4]
                    if has_triple and budget_fy:
                        fy_years_ordered = [budget_fy - 2, budget_fy - 1, budget_fy,
                                             budget_fy + 1, budget_fy + 2, budget_fy + 3, budget_fy + 4]
                    else:
                        # Fall back to scanning the page text for FY mentions
                        fy_seq_with_dupes = re.findall(r"FY\s*(\d{4})", text)
                        seen = []
                        for y in fy_seq_with_dupes:
                            if y not in seen: seen.append(y)
                        fy_years_ordered = [int(y) for y in seen]

                    if has_triple and len(num_floats) >= 12 and len(fy_years_ordered) >= 6:
                        # Map: skip Prior Years (idx 0), then FY-1, FY 0, skip Base+OOC, take Total at idx 5, then outyears
                        # The header order should be [FY-1, FY 0, FY+1 (triple), FY+2, FY+3, FY+4, FY+5]
                        # which means fy_years_ordered are [FY-1, FY 0, FY+1, FY+2, FY+3, FY+4, FY+5]
                        # And num indices are: 0=Prior, 1=FY-1, 2=FY 0, 3=Base, 4=OOC, 5=Total, 6=FY+2, 7=FY+3, 8=FY+4, 9=FY+5, 10=ToComplete, 11=TotalCost
                        try:
                            mapping = [
                                (fy_years_ordered[0], num_floats[1]),  # FY-1 actual
                                (fy_years_ordered[1], num_floats[2]),  # FY 0 enacted
                                (fy_years_ordered[2], num_floats[5]),  # FY+1 request (Total)
                                (fy_years_ordered[3], num_floats[6]),  # FY+2
                                (fy_years_ordered[4], num_floats[7]),  # FY+3
                                (fy_years_ordered[5], num_floats[8]),  # FY+4
                            ]
                            if len(fy_years_ordered) > 6 and len(num_floats) > 9:
                                mapping.append((fy_years_ordered[6], num_floats[9]))
                            for fy, val in mapping:
                                funding_history[f"FY{fy}"] = {
                                    "funded_M": val,
                                    "note": "P-40 12-col triple-FY",
                                }
                        except IndexError:
                            pass
                    else:
                        # Simple format: one FY per column. Skip Prior Years if present.
                        for i, fy in enumerate(sorted(set(fy_years_ordered))[:6]):
                            if i + 1 < len(num_floats):
                                funding_history[f"FY{fy}"] = {
                                    "funded_M": num_floats[i + 1],
                                    "note": "P-40 simple one-col-per-FY",
                                }

            # Derive status from funding trajectory
            status = _derive_status_from_funding(funding_history)

            entry = {
                "program_id": _slugify(title),
                "program_name": title.strip(),
                "synonyms": [],
                "pe_number": line_code,
                "project": None,
                "service": service,
                "agency": service,
                "description": f"P-40 procurement line item {line_code}: {title}. "
                                f"Page {page_idx+1} of {pdf_path.name}.",
                "funding_history": funding_history,
                "replacement_program": None,
                "replacement_pe": None,
                "replacement_sole_source": None,
                "primary_contractors": [],
                "status": status,
                "termination_announced": False,
                "exhibit_type": "P-40",
                "documented_in": [document],
                "source_urls": [],
                "_provenance": {
                    "ingested_by": "ingest_jbook_p40_om.py",
                    "document": document,
                    "document_date": document_date,
                    "pdf_page": page_idx + 1,
                },
            }
            entries.append(entry)

    return entries


# ---------- O&M / OP-5 SERVICES PARSING ----------

# OP-5 exhibits identify activity groups. Pattern examples:
#   "Activity Group: Operating Forces"
#   "Budget Activity 01: Operating Forces"
#   "Sub-Activity Group: LOGCAP V" — these are the named services contracts
_OM_ACTIVITY_RE = re.compile(
    r"(?:Sub-?Activity\s+Group|Activity\s+Group|Budget\s+(?:Sub-?)?Activity)"
    r"\s*[:\-]?\s*([A-Z0-9 &/\-,'.()]{4,100})",
    re.IGNORECASE,
)

# OP-5 funding totals appear as:
#   "Total OPERATIONAL FORCES 1,234.5 1,567.8 ..."
#   "FY 2026 Actual: 123.4   FY 2027 Estimate: 145.6"
_OM_FUNDING_LINE_RE = re.compile(
    r"(?:Total|Budget\s+Authority|Subactivity\s+Total)\s+"
    r"([A-Z][A-Z &/\-]{3,60}?)\s+"
    r"((?:[\d,.\-]+\s+){2,8}[\d,.\-]+)",
)


def parse_om_pdf(pdf_path: Path, service: str, document: str,
                 document_date: str) -> list[dict]:
    """Extract O&M / OP-5 services activity-group entries.

    OP-5 PDFs use positional text rather than structured tables. Strategy:
      1. Identify pages whose top has the SAG header pattern
         "<CODE> - <ActivityName>" — anchored to early lines only
      2. Verify the page is an OP-5 page (has FY column headers nearby)
      3. Parse data rows: "<line_code> <description> <FY25> <PG> <ProgG>
         <FY26> <PG> <ProgG> <FY27>" — 7 numeric columns after the desc
      4. Sum funding by FY across all rows on the page to get activity total
      5. Derive status from FY25 → FY26 → FY27 trajectory
    """
    entries = []
    seen_activities = set()

    # OP-5 exhibit header marker — only pages with this are real exhibit pages.
    # The structure is "Exhibit OP-5, Detail by Subactivity Group: <ACTIVITY NAME>"
    op5_header_re = re.compile(
        r"Exhibit\s+OP-5[^\n]*?(?:Subactivity\s+Group|Activity\s+Group|Operations?\s+Description)"
        r"[^\n]*?[:\-]\s*([A-Z][A-Z0-9 &/\-,'.()]{4,80})",
        re.IGNORECASE,
    )
    # Alternative format: title appears alone on a line as ALL CAPS or Title Case
    # next to "Exhibit OP-5" — look for it nearby.

    # SOCOM-format SAG header (own line: "1PLM - Management/Op HQ")
    sag_header_socom_re = re.compile(
        r"^\s*([0-9][A-Z]{2,4}|[A-Z]{1,3}\d{1,4}|[0-9]{2,3}[A-Z]{0,2})"
        r"\s*[\-–]\s*"
        r"([A-Z][A-Za-z0-9 &/\-,'.()]{4,80})\s*$"
    )
    # Army-format SAG header — "Detail by Subactivity Group 114: Theater Level Assets"
    sag_header_army_re = re.compile(
        r"Detail\s+by\s+Subactivity\s+Group\s+([0-9]{2,4}[A-Z]?)\s*[:\-]\s*"
        r"([A-Z][A-Za-z0-9 &/\-,'.()]{4,80})",
        re.IGNORECASE,
    )
    # Navy/USMC SAG header — "Detail by Subactivity Group: Air Systems Support"
    # (no numeric code; the SAG is identified only by name)
    sag_header_navy_re = re.compile(
        r"Detail\s+by\s+Subactivity\s+Group\s*[:\-]\s*"
        r"([A-Z][A-Za-z0-9 &/\-,'.()]{4,80})",
        re.IGNORECASE,
    )
    # SOCOM data row: 3-4 digit line code + description + 7 numeric columns
    data_row_socom_re = re.compile(
        r"^(\d{3,4})\s+(.+?)\s+"
        r"((?:-?[\d,]+(?:\.\d+)?\s+){6}-?[\d,]+(?:\.\d+)?)\s*$"
    )
    # Army data row: 3-4 digit line code + description + 11 numeric columns
    # (FC Rate $diff, FC Rate %, Price Growth, Program Growth between FYs)
    # Columns may include percent signs.
    data_row_army_re = re.compile(
        r"^(\d{3,4})\s+(.+?)\s+"
        r"((?:-?[\d,]+(?:\.\d+)?%?\s+){10}-?[\d,]+(?:\.\d+)?%?)\s*$"
    )
    # OP-5 marker
    om_marker_re = re.compile(r"Operation\s+and\s+Maintenance|Exhibit\s+OP-5", re.IGNORECASE)
    # SOCOM column header: "FY YYYY Price Program FY YYYY Price Program FY YYYY"
    fy_socom_header_re = re.compile(
        r"FY\s*(\d{4})\s+Price\s+Program\s+FY\s*(\d{4})\s+Price\s+Program\s+FY\s*(\d{4})",
        re.IGNORECASE,
    )
    # Army column header: "FY YYYY FC Rate Growth Price Program FY YYYY FC Rate Growth Price Program FY YYYY"
    fy_army_header_re = re.compile(
        r"FY\s*(\d{4})\s+FC\s+Rate\s+Growth\s+Price\s+Program\s+FY\s*(\d{4})\s+FC\s+Rate\s+Growth\s+Price\s+Program\s+FY\s*(\d{4})",
        re.IGNORECASE,
    )
    # Navy/USMC column header is split across multiple lines:
    #   "VII.OP-32 Line Items as Applicable (Dollars in Thousands)"
    #   "Change from FY YYYY to FY YYYY Change from FY YYYY to FY YYYY"
    #   "Inflation Categories FY YYYY For Price Prog FY For Price Prog FY"
    #   "Actuals Curr Growth Growth YYYY Curr Growth Growth YYYY"
    # Detect the format with a multi-line DOTALL match, then collect 3 FYs
    # from "Change from FY YYYY to FY YYYY Change from FY YYYY to FY YYYY".
    fy_navy_header_re = re.compile(
        r"Change\s+from\s+FY\s*(\d{4})\s+to\s+FY\s*(\d{4})\s+"
        r"Change\s+from\s+FY\s*\d{4}\s+to\s+FY\s*(\d{4})\s*"
        r"\n.{0,500}Inflation\s+Categories",
        re.IGNORECASE | re.DOTALL,
    )
    # Navy data row: 3-digit OP-32 code + description + 9 numeric columns
    # (FY_a | For Curr | Price | Prog | FY_b | For Curr | Price | Prog | FY_c)
    data_row_navy_re = re.compile(
        r"^(\d{3})\s+(.+?)\s+"
        r"((?:-?[\d,]+(?:\.\d+)?%?\s+){8}-?[\d,]+(?:\.\d+)?%?)\s*$"
    )

    # Per-SAG accumulator. Each SAG (Sub-Activity Group) may span multiple
    # pages — we want the financial-summary page (with data rows) and skip
    # the narrative pages.
    sag_data = {}  # activity -> {sag_code, fy_a, fy_b, fy_c, totals, row_count, pages}

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if not om_marker_re.search(text):
                continue
            lines = text.split("\n")

            # Detect format by column header (most specific first).
            fmt = None
            fy_hdr = fy_army_header_re.search(text)
            if fy_hdr:
                fmt = "army"
            if not fy_hdr:
                fy_hdr = fy_navy_header_re.search(text)
                if fy_hdr: fmt = "navy"
            if not fy_hdr:
                fy_hdr = fy_socom_header_re.search(text)
                if fy_hdr: fmt = "socom"
            if not fy_hdr:
                continue
            fy_a = int(fy_hdr.group(1))
            fy_b = int(fy_hdr.group(2))
            fy_c = int(fy_hdr.group(3))

            # Find SAG header per format.
            activity = None
            sag_code = None
            if fmt == "army":
                head_text = "\n".join(lines[:10])
                m = sag_header_army_re.search(head_text)
                if m:
                    sag_code = m.group(1).strip()
                    activity = m.group(2).strip().rstrip(":,.")
            elif fmt == "navy":
                head_text = "\n".join(lines[:10])
                # Try Army-style (with code) first — some Navy pages also include
                # numeric codes; fall back to Navy-only (no code) if that misses.
                m = sag_header_army_re.search(head_text)
                if m:
                    sag_code = m.group(1).strip()
                    activity = m.group(2).strip().rstrip(":,.")
                else:
                    m = sag_header_navy_re.search(head_text)
                    if m:
                        sag_code = "—"
                        activity = m.group(1).strip().rstrip(":,.")
            else:  # socom
                for ln in lines[:6]:
                    m = sag_header_socom_re.match(ln)
                    if m:
                        sag_code = m.group(1).strip()
                        activity = m.group(2).strip().rstrip(":,.")
                        break
            if not activity or len(activity) < 5:
                continue

            # Sum data rows on this page using format-specific regex.
            #   Army:  11 numeric cols, FY25@0, FY26@5, FY27@10
            #   Navy:   9 numeric cols, FY25@0, FY26@4, FY27@8
            #   SOCOM:  7 numeric cols, FY25@0, FY26@3, FY27@6
            if fmt == "army":
                data_row_re = data_row_army_re
                n_cols = 11; i_a, i_b, i_c = 0, 5, 10
            elif fmt == "navy":
                data_row_re = data_row_navy_re
                n_cols = 9; i_a, i_b, i_c = 0, 4, 8
            else:
                data_row_re = data_row_socom_re
                n_cols = 7; i_a, i_b, i_c = 0, 3, 6

            page_totals = {fy_a: 0.0, fy_b: 0.0, fy_c: 0.0}
            page_rows = 0
            for ln in lines:
                m = data_row_re.match(ln.strip())
                if not m:
                    continue
                desc_upper = m.group(2).upper()
                if "GRAND TOTAL" in desc_upper or desc_upper.strip().startswith("TOTAL "):
                    continue
                # Extract numbers; ignore percent signs
                nums_raw = re.findall(r"-?[\d,]+(?:\.\d+)?", m.group(3))
                if len(nums_raw) < n_cols:
                    continue
                try:
                    vals = [float(n.replace(",", "")) for n in nums_raw[:n_cols]]
                except ValueError:
                    continue
                page_totals[fy_a] += vals[i_a]
                page_totals[fy_b] += vals[i_b]
                page_totals[fy_c] += vals[i_c]
                page_rows += 1

            if page_rows == 0:
                continue

            # Accumulate by SAG
            if activity not in sag_data:
                sag_data[activity] = {
                    "sag_code": sag_code,
                    "fy_a": fy_a, "fy_b": fy_b, "fy_c": fy_c,
                    "totals": {fy_a: 0.0, fy_b: 0.0, fy_c: 0.0},
                    "row_count": 0,
                    "pages": [],
                }
            agg = sag_data[activity]
            for fy in (fy_a, fy_b, fy_c):
                agg["totals"][fy] += page_totals[fy]
            agg["row_count"] += page_rows
            agg["pages"].append(page_idx + 1)

    # Build one entry per SAG
    for activity, agg in sag_data.items():
        funding_history = {
            f"FY{fy}": {
                "funded_M": round(amt / 1000.0, 3),
                "note": f"OP-5 activity total ($ M, sum of {agg['row_count']} line items)",
            }
            for fy, amt in agg["totals"].items()
        }
        status = _derive_status_from_funding(funding_history)
        entries.append({
            "program_id": _slugify(f"{service} {activity}"),
            "program_name": activity[:80],
            "synonyms": [],
            "pe_number": None,
            "project": agg["sag_code"],
            "service": service,
            "agency": service,
            "description": f"O&M services activity ({agg['sag_code']}): {activity}. "
                            f"Page(s) {agg['pages']} of {pdf_path.name}.",
            "funding_history": funding_history,
            "replacement_program": None,
            "replacement_pe": None,
            "replacement_sole_source": None,
            "primary_contractors": [],
            "status": status,
            "termination_announced": False,
            "exhibit_type": "OP-5",
            "documented_in": [document],
            "source_urls": [],
            "_provenance": {
                "ingested_by": "ingest_jbook_p40_om.py v3 (per-SAG accumulator)",
                "document": document,
                "document_date": document_date,
                "pdf_pages": agg["pages"],
            },
        })

    return entries


# ---------- HELPERS ----------

def _slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:80]


def _derive_status_from_funding(funding: dict) -> str:
    """Return derived status string. Same vocabulary as existing corpus."""
    if not funding:
        return "NOT_FOUND_IN_TIMERANGE"
    fys = sorted(funding.keys())
    amts = [funding[fy].get("funded_M") for fy in fys]
    # Strip Nones for last-two analysis
    recent = [a for a in amts[-3:] if a is not None]
    if not recent or all(a == 0 for a in recent):
        return "UNFUNDED_TWO_PLUS_YEARS"
    if recent[-1] == 0:
        return "UNFUNDED_THIS_YEAR"
    if len(recent) >= 2 and recent[-1] < recent[-2] * 0.5:
        return "FUNDED_SHRINKING"
    if len(recent) >= 2 and recent[-1] > recent[-2] * 1.5:
        return "FUNDED_GROWING"
    return "FUNDED_STEADY"


def merge_into_corpus(new_entries: list[dict], out_path: Path) -> tuple[int, int]:
    if not new_entries:
        return 0, 0
    if not out_path.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)
        doc = {"_meta": {}, "programs": []}
    else:
        doc = json.loads(out_path.read_text())
    existing_ids = {p.get("program_id") for p in doc.get("programs", [])}
    n_added = 0
    n_skipped = 0
    for e in new_entries:
        if e["program_id"] in existing_ids:
            n_skipped += 1
            continue
        doc["programs"].append(e)
        existing_ids.add(e["program_id"])
        n_added += 1
    doc["_meta"]["last_updated"] = "2026-05-23"
    out_path.write_text(json.dumps(doc, indent=2, default=str))
    return n_added, n_skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", help="Path to PDF")
    ap.add_argument("--type", choices=["p40", "om"], required=True)
    ap.add_argument("--service", required=True)
    ap.add_argument("--document", required=True)
    ap.add_argument("--document-date", required=True)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--print-only", action="store_true")
    args = ap.parse_args()

    pdf = Path(args.pdf)
    if not pdf.exists():
        print(f"ERROR: PDF not found: {pdf}", file=sys.stderr)
        sys.exit(2)

    print(f"Parsing {pdf.name} (type={args.type}, service={args.service})...",
          file=sys.stderr)
    if args.type == "p40":
        entries = parse_p40_pdf(pdf, args.service, args.document, args.document_date)
    else:
        entries = parse_om_pdf(pdf, args.service, args.document, args.document_date)

    print(f"Extracted {len(entries)} entries.", file=sys.stderr)
    if entries:
        print(f"Sample entry: {entries[0]['program_name']} (status={entries[0]['status']})",
              file=sys.stderr)

    if args.print_only:
        print(json.dumps([{"id": e["program_id"], "name": e["program_name"],
                            "type": e["exhibit_type"], "status": e["status"]}
                           for e in entries], indent=2))
        return

    added, skipped = merge_into_corpus(entries, Path(args.out))
    print(f"Added {added} new programs, skipped {skipped} duplicates.", file=sys.stderr)


if __name__ == "__main__":
    main()
