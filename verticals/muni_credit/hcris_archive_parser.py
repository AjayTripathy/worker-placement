"""Parse CMS HCRIS bulk archive (Form 2552-10) for historical hospital cost reports.

Files in each yearly ZIP:
  HOSP10_YYYY_rpt.csv    — Report header: rpt_rec_num, provider, dates
  HOSP10_YYYY_nmrc.csv   — Numeric values: rpt_rec_num, wksht_cd, line, col, value
  HOSP10_YYYY_alpha.csv  — Alpha values (we don't need)

KEY HCRIS FIELD ADDRESSES (Form 2552-10):
  Worksheet G-3 ("Statement of Revenues and Expenses"):
    Line 1, Col 1  → Total Operating Revenue / Net Patient Service Revenue
    Line 4, Col 1  → Total Operating Expense (used; some forms put this elsewhere)
    Line 28, Col 1 → Net Income
    Line 29, Col 1 → Total Other Income (investment income, etc.)
  Worksheet G ("Balance Sheet"):
    Line 1, Col 1  → Cash on Hand and in Banks
    Line 2, Col 1  → Temporary Investments
    Line 13, Col 1 → Total Current Assets

Worksheet codes in NMRC are formatted as "S200001", "G300000", etc.
G-3 = "G300000" (6-char alphanumeric).
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from collections import defaultdict

HERE = Path(__file__).parent
ARCHIVE_DIR = HERE / "data" / "hcris_archive"

# Worksheet code mapping (NMRC uses 6-character codes)
WKSHT_G3 = "G300000"   # Statement of Revenues and Expenses
WKSHT_G  = "G000000"   # Balance Sheet
WKSHT_S3 = "S300001"   # Patient days breakdown (Part 1)

# (Worksheet, Line, Column) → friendly name
# CORRECTED 2026-05-27 after empirical comparison to CMS Open Data API:
#   Line 1 = GROSS patient revenue (charges, before allowances)
#   Line 2 = LESS: contractual allowances
#   Line 3 = NET PATIENT REVENUE (Line 1 - Line 2)
#   Line 4 = LESS: total operating expenses
#   Line 5 = NET INCOME FROM SERVICE TO PATIENTS (Line 3 - Line 4)
#   Line 28 = NET INCOME (bottom line, includes non-operating)
WANTED_FIELDS = {
    (WKSHT_G3, "00100", "00100"): "gross_patient_revenue",        # Line 1 (gross charges)
    (WKSHT_G3, "00200", "00100"): "contractual_allowances",       # Line 2 (deduction)
    (WKSHT_G3, "00300", "00100"): "net_patient_revenue",          # Line 3 ← NPR (matches API "Net Patient Revenue")
    (WKSHT_G3, "00400", "00100"): "total_operating_expense",      # Line 4 ← OpEx (matches API "Less Total Operating Expense")
    (WKSHT_G3, "00500", "00100"): "net_income_from_service",      # Line 5 (operating income)
    (WKSHT_G3, "02500", "00100"): "total_other_income",
    (WKSHT_G3, "02800", "00100"): "net_income",                    # Line 28 ← Total net income (matches API "Net Income")
    (WKSHT_G,  "00100", "00100"): "cash",
    (WKSHT_G,  "00200", "00100"): "temp_investments",
    (WKSHT_G,  "01000", "00100"): "investments_lt",
}


def parse_rpt(rpt_csv_path: Path) -> dict[str, dict]:
    """Parse the RPT header file → {rpt_rec_num: {ccn, fy_bgn, fy_end, ...}}."""
    out = {}
    with rpt_csv_path.open() as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 8: continue
            rpt_rec = row[0]
            ccn = row[2].strip()
            fy_bgn = row[5]
            fy_end = row[6]
            out[rpt_rec] = {
                "ccn": ccn.zfill(6) if ccn else None,
                "fy_bgn": fy_bgn,
                "fy_end": fy_end,
            }
    return out


def parse_nmrc_targeted(nmrc_csv_path: Path, target_rpt_recs: set[str]) -> dict[str, dict]:
    """Parse NMRC, filtering to only the rpt_rec_nums we care about.

    Returns {rpt_rec_num: {field_name: value}}.
    """
    out: dict[str, dict] = defaultdict(dict)
    n_lines = 0
    n_hits = 0
    with nmrc_csv_path.open() as f:
        reader = csv.reader(f)
        for row in reader:
            n_lines += 1
            if len(row) < 5: continue
            rpt_rec = row[0]
            if rpt_rec not in target_rpt_recs: continue
            wksht_cd, line_num, col_num, value = row[1], row[2], row[3], row[4]
            key = (wksht_cd, line_num, col_num)
            if key in WANTED_FIELDS:
                try:
                    v = float(value)
                except ValueError:
                    continue
                out[rpt_rec][WANTED_FIELDS[key]] = v
                n_hits += 1
    print(f"  Parsed {n_lines:,} NMRC rows, {n_hits:,} field hits for {len(out)} reports",
          file=sys.stderr)
    return dict(out)


def extract_year(fy: int) -> dict[str, dict]:
    """Extract financial metrics for all hospitals in a given fiscal year.

    Returns {ccn: {fy_end, npr, opex, net_income, cash, investments, ...}}
    """
    rpt_path = ARCHIVE_DIR / f"HOSP10_{fy}_rpt.csv"
    nmrc_path = ARCHIVE_DIR / f"HOSP10_{fy}_nmrc.csv"
    if not rpt_path.exists() or not nmrc_path.exists():
        raise FileNotFoundError(f"Missing FY{fy} archive files in {ARCHIVE_DIR}")

    print(f"Parsing RPT for FY{fy}...", file=sys.stderr)
    rpt_index = parse_rpt(rpt_path)
    print(f"  {len(rpt_index)} hospital cost reports", file=sys.stderr)

    target_recs = set(rpt_index.keys())
    print(f"Parsing NMRC for FY{fy} (filtered to {len(target_recs)} reports)...", file=sys.stderr)
    field_data = parse_nmrc_targeted(nmrc_path, target_recs)

    # Build CCN-keyed output
    out: dict[str, dict] = {}
    for rpt_rec, fields in field_data.items():
        meta = rpt_index.get(rpt_rec, {})
        ccn = meta.get("ccn")
        if not ccn: continue
        # Keep most recent FY end per CCN
        if ccn not in out or (meta.get("fy_end") or "") > (out[ccn].get("fy_end") or ""):
            out[ccn] = {**meta, **fields}
    return out


def operating_margin(facility: dict) -> float | None:
    """Compute operating margin = (NPR - OpEx) / NPR using Line 3 + Line 4."""
    npr = facility.get("net_patient_revenue")
    opex = facility.get("total_operating_expense")
    ni = facility.get("net_income")
    if npr and npr > 0 and opex is not None:
        return (npr - opex) / npr * 100
    if npr and npr > 0 and ni is not None:
        return ni / npr * 100
    return None


def days_cash(facility: dict) -> float | None:
    """Compute days cash = (Cash + Investments) / (OpEx / 365)."""
    cash = facility.get("cash") or 0
    inv  = facility.get("investments_lt") or 0
    ti   = facility.get("temp_investments") or 0
    opex = facility.get("total_operating_expense")
    if not opex or opex <= 0: return None
    return (cash + inv + ti) / (opex / 365)


if __name__ == "__main__":
    import sys
    fy = int(sys.argv[1]) if len(sys.argv) > 1 else 2022
    data = extract_year(fy)
    # Print sample
    print(f"\nFY{fy}: {len(data)} hospitals with extracted data\n")
    for ccn in sorted(data.keys())[:10]:
        f = data[ccn]
        m = operating_margin(f)
        dc = days_cash(f)
        print(f"  CCN {ccn} FY {f.get('fy_end'):<10} "
              f"NPR={f.get('total_operating_revenue', 0)/1e6:>7.1f}M "
              f"OpEx={f.get('total_operating_expense', 0)/1e6:>7.1f}M "
              f"NI={f.get('net_income', 0)/1e6:>+7.1f}M "
              f"margin={f'{m:+.2f}%' if m else 'n/a':<8} "
              f"dayscash={f'{dc:.0f}' if dc else 'n/a'}")
