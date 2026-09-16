#!/usr/bin/env python3
"""Golden-master characterization harness for the J-Book PDF parser.

The parser (ingest_jbook._parse_page_blocks) extracts procurement/RDT&E funding
tables out of DoD budget PDFs — a structure-aware extraction problem with the same
failure modes as SEC tables (split cells, FY Base/OOC/Total triplet columns, blank-cell
drift, multi-page table flow). Before hardening it, we freeze its CURRENT output on a
fixture set spanning every code path, so the hardening can be diffed (improvements =
corrected/added funding rows; regressions = previously-extracted rows lost or changed).

  python3 -m verticals.public_co.scripts._jbook_parser_golden --tag baseline
  # ...harden the parser...
  python3 -m verticals.public_co.scripts._jbook_parser_golden --tag hardened
  python3 -m verticals.public_co.scripts._jbook_parser_golden --diff baseline hardened
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import pdfplumber  # noqa: E402
from verticals.public_co.scripts import ingest_jbook as ij  # noqa: E402

PDFS = ROOT / "verticals/public_co/data/_jbook_pdfs_p40"
GOLDEN = ROOT / "verticals/public_co/data/_jbook_data/_golden"
# Fixtures spanning every parse path: P-1/P-40 procurement (Navy/Army/AF/SOCOM),
# R-2 RDT&E (DARPA-style Program-Change-Summary), O&M (OP-5/OP-32), P-1 summary.
FIXTURES = [
    "WPN_Book.pdf", "Aircraft_Procurement_Army.pdf", "Missile_Procurement_Army.pdf",
    "PROC_SOCOM_PB_2027.pdf", "FY2027_p1.pdf", "SOCOM_OP-5.pdf", "OP-32A_Summary.pdf",
    "af_fy27/FY27_Air_Force_Space_Procurement.pdf", "navy_fy27/OMN_Book.pdf",
    "army_om/FY2027_RDTE_RDTE_-_Vol_2_-_Budget_Activity_4B.pdf",
]
PAGE_CAP = 250     # bound pages scanned per fixture
BLOCK_CAP = 60     # capture up to N parsed blocks per fixture


def capture(tag: str) -> None:
    GOLDEN.mkdir(parents=True, exist_ok=True)
    out = []
    for rel in FIXTURES:
        p = PDFS / rel
        rec = {"pdf": rel, "exists": p.exists(), "blocks": []}
        if p.exists():
            try:
                with pdfplumber.open(str(p)) as pdf:
                    for page in pdf.pages[:PAGE_CAP]:
                        try:
                            blocks = ij._parse_page_blocks(page)
                        except Exception as e:
                            rec["blocks"].append({"page": page.page_number, "error": repr(e)})
                            continue
                        for b in blocks:
                            rec["blocks"].append({
                                "page": b.get("page_no"),
                                "pe": b.get("pe_number"),
                                "title": b.get("pe_title"),
                                "funding": {str(k): v for k, v in sorted((b.get("funding_year_map") or {}).items())},
                                "notes": sorted(b.get("notes") or []),
                            })
                        if len(rec["blocks"]) >= BLOCK_CAP:
                            break
            except Exception as e:
                rec["open_error"] = repr(e)
        out.append(rec)
        print(f"  {rel}: {len([b for b in rec['blocks'] if 'pe' in b])} blocks", file=sys.stderr)
    (GOLDEN / f"parser_{tag}.json").write_text(json.dumps(out, indent=1, default=str))
    # summary
    blocks = [b for r in out for b in r["blocks"] if "pe" in b]
    nofund = sum(1 for b in blocks if not b["funding"])
    fail = sum(1 for b in blocks if any("could_not" in n or n.startswith("no_") for n in b["notes"]))
    print(f"\n[{tag}] total blocks={len(blocks)}  no-funding={nofund}  parse-fail-notes={fail}")
    print(f"wrote {GOLDEN / f'parser_{tag}.json'}")


def diff(a: str, b: str) -> None:
    da = json.loads((GOLDEN / f"parser_{a}.json").read_text())
    db = json.loads((GOLDEN / f"parser_{b}.json").read_text())
    def index(d):
        out = {}
        for rec in d:
            for blk in rec["blocks"]:
                if "pe" in blk:
                    out[(rec["pdf"], blk["page"], blk["pe"])] = blk
        return out
    ia, ib = index(da), index(db)
    added = [k for k in ib if k not in ia]
    lost = [k for k in ia if k not in ib]
    fund_changed = [k for k in ia if k in ib and ia[k]["funding"] != ib[k]["funding"]]
    notes_changed = [k for k in ia if k in ib and ia[k]["notes"] != ib[k]["notes"]]
    print(f"=== diff {a} -> {b} ===")
    print(f"  blocks: {len(ia)} -> {len(ib)}  | added={len(added)} lost(REGRESSION?)={len(lost)}")
    print(f"  funding_year_map changed: {len(fund_changed)}")
    print(f"  notes changed:            {len(notes_changed)}")
    fa = sum(1 for k in ia if any('could_not' in n or n.startswith('no_') for n in ia[k]['notes']))
    fb = sum(1 for k in ib if any('could_not' in n or n.startswith('no_') for n in ib[k]['notes']))
    print(f"  parse-fail notes: {fa} -> {fb}  ({fa-fb:+d})")
    for lab, ks in (("LOST (investigate)", lost[:8]), ("sample funding-changed", fund_changed[:8])):
        if ks:
            print(f"  {lab}:")
            for k in ks:
                print(f"    {k}: {ia[k]['funding'] if lab.startswith('LOST') else (ia[k]['funding'],'->',ib[k]['funding'])}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", help="capture current parser output under this tag")
    ap.add_argument("--diff", nargs=2, metavar=("A", "B"), help="diff two captured tags")
    args = ap.parse_args()
    if args.diff:
        diff(*args.diff)
    elif args.tag:
        capture(args.tag)
    else:
        ap.error("need --tag or --diff")


if __name__ == "__main__":
    main()
