"""
DD data-room column-completeness audit.

Takes any xlsx and produces a per-column report flagging:

  - **HEADER_PROMISE_VIOLATED**: header advertises something (address, URL, email,
    phone, date, ID) that the cells don't deliver.
  - **EXPECTED_HYPERLINKS_MISSING**: header contains "link" / "url" but no
    hyperlinks exist in the column.
  - **IDENTIFIER_NOT_UNIQUE**: column whose header implies a per-row identifier
    (address, id, key) has many duplicate values — common sign that the
    column was stripped or replaced with a placeholder.
  - **LOW_POPULATION**: <50% of rows populated for a column the rest of the
    sheet seems to care about.
  - **SUSPECT_REDACTION**: cell pattern suggests trailing data was removed
    (e.g., "Atlanta, GA 30314" in an Address column → city + zip only;
    "***-**-1234" in an SSN column; "@..." truncated emails).

Usage:
    python3 audit_xlsx.py <path-to-xlsx> [--sheet SHEET] [--json]

The intended workflow is: run this FIRST on any data-room xlsx, before any
analytic content review. If HEADER_PROMISE_VIOLATED fires, the data room
itself is non-verifiable and that should be the top of the DD report.

Built after the Reawaken Capital DD (2026-05-22) where a pipeline xlsx
column titled "Address (Zillow Link)" was populated with city + ZIP only,
making the entire pipeline unverifiable. Took a user prompt to catch.
This script catches it in seconds.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import openpyxl

# Header-keyword → expected content pattern.
# Each entry: keywords (lowercased substrings) → (predicate, friendly description)
# Predicate takes a string and returns True if it looks like valid content for that header.
EXPECTATIONS: dict[tuple[str, ...], tuple[callable, str]] = {
    ("address", "street"): (
        lambda v: bool(re.search(r"\d+\s+\w+", v or "")) and any(  # street number + word
            t in (v or "").lower()
            for t in (" st", " street", " ave", " avenue", " rd", " road",
                      " dr", " drive", " blvd", " ln", " lane", " way",
                      " ct", " court", " pl", " place", " pkwy", " hwy",
                      " circle", " cir", " ter", " terrace", " trail")
        ),
        "street-level address (number + street suffix)",
    ),
    ("link", "url", "website", "zillow"): (
        lambda v: bool(re.match(r"https?://", (v or "").strip())),
        "URL (http/https)",
    ),
    ("email",): (
        lambda v: bool(re.search(r"\S+@\S+\.\S+", v or "")),
        "email address",
    ),
    ("phone", "telephone"): (
        lambda v: bool(re.search(r"\d{3}[\s\-.]?\d{3}[\s\-.]?\d{4}", v or "")),
        "phone number (10-digit)",
    ),
    ("date", "filed", "filing"): (
        lambda v: bool(re.search(r"\d{4}[\-/]\d{1,2}[\-/]\d{1,2}|\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4}", v or "")),
        "date (ISO or M/D/Y)",
    ),
    ("ein", "tax id", "tin"): (
        lambda v: bool(re.search(r"\d{2}-\d{7}", v or "")),
        "EIN (XX-XXXXXXX)",
    ),
    ("ssn", "social"): (
        lambda v: bool(re.search(r"\d{3}-\d{2}-\d{4}", v or "")),
        "SSN (XXX-XX-XXXX)",
    ),
    ("cik",): (
        lambda v: bool(re.search(r"\d{4,10}", v or "")),
        "CIK (numeric)",
    ),
    ("ticker", "symbol"): (
        lambda v: bool(re.match(r"^[A-Z]{1,5}(\.|-)?[A-Z]?$", (v or "").strip())),
        "stock ticker (1-5 caps)",
    ),
}


# Headers whose values should typically be unique per row
IDENTIFIER_HEADER_TOKENS = {
    "address", "street", "id", "key", "accession", "uuid", "guid",
    "cik", "ein", "ssn", "deal", "transaction", "case", "claim_id",
}


def _norm(s) -> str:
    if s is None: return ""
    return str(s).strip()


def _matches_keyword(header: str, keywords: tuple[str, ...]) -> bool:
    """Match keyword against header on word boundaries to avoid false positives
    like 'expenses' matching 'ein'.
    """
    h = header.lower()
    for k in keywords:
        if re.search(rf"\b{re.escape(k)}\b", h):
            return True
    return False


def audit_column(header: str, values: list, hyperlinks_count: int,
                  n_rows: int) -> dict:
    """Return audit dict for one column."""
    non_empty = [_norm(v) for v in values if _norm(str(v) if v is not None else "")]
    n_pop = len(non_empty)
    pop_rate = n_pop / n_rows if n_rows else 0
    unique_vals = set(non_empty)
    n_unique = len(unique_vals)

    flags: list[str] = []

    # 1. Header promises content type — check cells match
    matched_keywords = None
    expectation_desc = None
    expectation_pred = None
    for keywords, (pred, desc) in EXPECTATIONS.items():
        if _matches_keyword(header, keywords):
            matched_keywords = keywords
            expectation_pred = pred
            expectation_desc = desc
            break

    if expectation_pred and n_pop:
        # Sample up to 50 non-empty values
        sample = non_empty[:50]
        n_match = sum(1 for v in sample if expectation_pred(v))
        match_rate = n_match / len(sample) if sample else 0
        if match_rate < 0.5:
            flags.append({
                "code": "HEADER_PROMISE_VIOLATED",
                "header_promised": expectation_desc,
                "match_rate": f"{match_rate:.0%}",
                "sample_values": list(unique_vals)[:5],
            })

    # 2. Header has link/url keyword but no hyperlinks
    if _matches_keyword(header, ("link", "url", "website", "zillow")):
        if hyperlinks_count == 0 and n_pop > 0:
            flags.append({
                "code": "EXPECTED_HYPERLINKS_MISSING",
                "msg": f"Header advertises link/URL; column has {n_pop} populated rows but zero hyperlinks",
            })

    # 3. Identifier header but high duplicate rate
    is_identifier = any(t in header.lower() for t in IDENTIFIER_HEADER_TOKENS)
    if is_identifier and n_pop >= 10:
        uniqueness = n_unique / n_pop
        if uniqueness < 0.5:
            most_common = Counter(non_empty).most_common(3)
            flags.append({
                "code": "IDENTIFIER_NOT_UNIQUE",
                "uniqueness": f"{uniqueness:.0%}",
                "msg": f"Header implies per-row identifier; {n_unique} unique / {n_pop} populated ({uniqueness:.0%})",
                "most_common": [{"value": v, "count": c} for v, c in most_common],
            })

    # 4. Low population (only flag if header looks meaningful)
    if pop_rate < 0.5 and n_rows >= 10 and header.strip():
        flags.append({
            "code": "LOW_POPULATION",
            "pop_rate": f"{pop_rate:.0%}",
            "n_populated": n_pop,
            "n_rows": n_rows,
        })

    # 5. Suspect redaction patterns
    if n_pop:
        sample = non_empty[:100]
        # All-same-zip-code pattern (e.g., "Atlanta, GA 30314" repeated)
        # If header is address-like AND values look like just city/zip
        if _matches_keyword(header, ("address", "street", "location")):
            zip_only_pattern = re.compile(r"^[^,]+,?\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?$")
            zip_only_count = sum(1 for v in sample if zip_only_pattern.match(v))
            if zip_only_count / len(sample) > 0.7:
                flags.append({
                    "code": "SUSPECT_REDACTION",
                    "pattern": "city_state_zip_only_in_address_column",
                    "msg": f"{zip_only_count}/{len(sample)} cells match 'City, ST ZIP' pattern only — street addresses likely stripped",
                })
        # Redacted-style patterns (****, XXX-, ...)
        redacted_pattern = re.compile(r"^[*xX_-]{3,}")
        n_redacted = sum(1 for v in sample if redacted_pattern.search(v))
        if n_redacted > 2:
            flags.append({
                "code": "SUSPECT_REDACTION",
                "pattern": "asterisk_or_dash_runs",
                "msg": f"{n_redacted}/{len(sample)} cells contain ***/XXX/--- runs — likely partially redacted",
            })

    return {
        "header": header,
        "n_populated": n_pop,
        "pop_rate": round(pop_rate, 3),
        "n_unique": n_unique,
        "hyperlinks": hyperlinks_count,
        "sample_values": list(unique_vals)[:5],
        "flags": flags,
    }


def audit_sheet(ws) -> dict:
    n_rows_total = ws.max_row - 1  # excluding header
    n_cols = ws.max_column

    # Read header row
    headers = []
    for col in range(1, n_cols + 1):
        headers.append(_norm(ws.cell(row=1, column=col).value or ""))

    # Pre-count hyperlinks per column
    hyperlinks_per_col = [0] * n_cols
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            if cell.hyperlink:
                hyperlinks_per_col[cell.column - 1] += 1

    # First pass: read all column values
    all_values: list[list] = []
    for col_idx in range(n_cols):
        values = []
        for row_num in range(2, ws.max_row + 1):
            values.append(ws.cell(row=row_num, column=col_idx + 1).value)
        all_values.append(values)

    # Determine "effective" row count = max populated count across columns.
    # This handles xlsx files where the source has tons of trailing blank rows
    # — without this fix, every column would falsely flag LOW_POPULATION.
    effective_pop = 0
    for values in all_values:
        n_pop = sum(1 for v in values if _norm(v))
        if n_pop > effective_pop:
            effective_pop = n_pop
    # If the gap between total rows and effective rows is >20%, trust effective_pop
    n_rows = effective_pop if effective_pop and (n_rows_total - effective_pop) / max(n_rows_total, 1) > 0.2 else n_rows_total

    # Second pass: audit each column
    columns: list[dict] = []
    for col_idx, header in enumerate(headers):
        result = audit_column(header, all_values[col_idx], hyperlinks_per_col[col_idx], n_rows)
        columns.append(result)

    # Sheet-level summary
    n_flagged = sum(1 for c in columns if c["flags"])
    flag_counts = Counter()
    for c in columns:
        for f in c["flags"]:
            flag_counts[f["code"]] += 1

    return {
        "sheet_name": ws.title,
        "n_rows": n_rows,
        "n_rows_total": n_rows_total,
        "n_cols": n_cols,
        "n_columns_with_flags": n_flagged,
        "flag_summary": dict(flag_counts),
        "columns": columns,
    }


def render_report(audit: dict, sheet_path: str, sheet_name: str | None = None) -> str:
    """Render a markdown report from the audit."""
    L = []
    L.append(f"# Column Audit — {Path(sheet_path).name}")
    L.append("")
    n_total = audit.get("n_rows_total", audit["n_rows"])
    if n_total and n_total != audit["n_rows"]:
        L.append(f"*Sheet: `{audit['sheet_name']}`  |  {audit['n_rows']} data rows × {audit['n_cols']} cols  ({n_total - audit['n_rows']} trailing blank rows ignored)*")
    else:
        L.append(f"*Sheet: `{audit['sheet_name']}`  |  {audit['n_rows']} rows × {audit['n_cols']} cols*")
    L.append("")
    L.append("## Summary")
    L.append(f"- Columns flagged: **{audit['n_columns_with_flags']} / {audit['n_cols']}**")
    if audit["flag_summary"]:
        for code, n in sorted(audit["flag_summary"].items(), key=lambda kv: -kv[1]):
            L.append(f"- `{code}`: {n}")
    else:
        L.append("- No flags raised (column structure appears clean).")
    L.append("")
    # Flagged columns first, then clean
    flagged = [c for c in audit["columns"] if c["flags"]]
    clean = [c for c in audit["columns"] if not c["flags"]]

    if flagged:
        L.append("## 🚩 Flagged columns")
        L.append("")
        for c in flagged:
            L.append(f"### `{c['header']}`")
            L.append(f"- Populated: {c['n_populated']}/{audit['n_rows']} ({c['pop_rate']:.0%})  |  "
                     f"unique values: {c['n_unique']}  |  hyperlinks: {c['hyperlinks']}")
            sample = c["sample_values"]
            if sample:
                sample_str = ", ".join(f"`{repr(v)[:40]}`" for v in sample)
                L.append(f"- Sample: {sample_str}")
            for f in c["flags"]:
                L.append(f"- **{f['code']}** — {f.get('msg', '')}")
                for k, v in f.items():
                    if k in ("code", "msg"): continue
                    L.append(f"  - `{k}`: {v}")
            L.append("")

    if clean:
        L.append("## ✓ Clean columns")
        L.append("")
        L.append(f"{len(clean)} columns passed all checks:")
        L.append(", ".join(f"`{c['header']}`" for c in clean if c["header"]))
        L.append("")

    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="Path to .xlsx file")
    ap.add_argument("--sheet", help="Sheet name (defaults to first sheet)")
    ap.add_argument("--json", action="store_true", help="Output raw JSON instead of markdown")
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"ERROR: file not found: {p}", file=sys.stderr)
        sys.exit(2)

    wb = openpyxl.load_workbook(p, data_only=True)
    sheet_name = args.sheet or wb.sheetnames[0]
    if sheet_name not in wb.sheetnames:
        print(f"ERROR: sheet {sheet_name!r} not in workbook. Available: {wb.sheetnames}", file=sys.stderr)
        sys.exit(2)
    ws = wb[sheet_name]
    audit = audit_sheet(ws)

    if args.json:
        print(json.dumps(audit, indent=2, default=str))
    else:
        print(render_report(audit, str(p)))

    # Exit non-zero if any column was flagged — useful for CI / sentinel checks
    sys.exit(1 if audit["n_columns_with_flags"] > 0 else 0)


if __name__ == "__main__":
    main()
