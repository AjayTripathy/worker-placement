#!/usr/bin/env python3
"""Batch-ingest every procurement (P-40) / RDT&E (R-2) J-Book PDF into programs.json.

Runs the hardened ingest_jbook parser over all relevant PDFs in _jbook_pdfs_p40,
merging into programs.json with preserve_curated=True (the 750 hand-curated entries are
never overwritten). O&M / MILPERS / MILCON books are SKIPPED — they're object-class /
activity / personnel data that doesn't map to the program->contractor->ticker model.

Resumable: a processed-manifest records done PDFs; programs.json + manifest are saved
after every PDF, so a kill/resume continues where it left off.

  python3 -m verticals.public_co.scripts.batch_ingest_jbook            # run / resume
  python3 -m verticals.public_co.scripts.batch_ingest_jbook --limit-per-pdf 800
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from verticals.public_co.scripts import ingest_jbook as ij  # noqa: E402

PDFS = ROOT / "verticals/public_co/data/_jbook_pdfs_p40"
CORPUS = ROOT / "verticals/public_co/data/_jbook_data/programs.json"
MANIFEST = ROOT / "verticals/public_co/data/_jbook_data/_golden/batch_ingest_manifest.json"

_SKIP = re.compile(
    r"op-?5|op-?32|\bomn\b|ommcr|_om_|milcon|milpers|operation_and_maintenance|"
    r"o_and_m|reserve_army_operation", re.I)


def infer_service(path: Path) -> str:
    p = str(path).lower()
    name = path.name.lower()
    if "socom" in p:
        return "SOCOM"
    if "army" in p:
        return "Army"
    if ("air_force" in p or "/af_" in p or "space_force" in name or
            "air_national_guard" in p or name.startswith("fy27_air")):
        return "Air Force"
    if "marine" in p:
        return "Marine Corps"
    if ("navy" in p or name.startswith(("wpn", "apn", "scn", "opn", "rpn"))):
        return "Navy"
    if "defense" in p:
        return "Defense-Wide"
    return "Unknown"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-per-pdf", type=int, default=0, help="cap entries per PDF (0=unlimited)")
    args = ap.parse_args()

    pdfs = sorted(p for p in PDFS.rglob("*.pdf") if not _SKIP.search(p.name))
    done = set(json.loads(MANIFEST.read_text())["done"]) if MANIFEST.exists() else set()
    todo = [p for p in pdfs if str(p.relative_to(PDFS)) not in done]

    start_total = len(json.loads(CORPUS.read_text())["programs"]) if CORPUS.exists() else 0
    print(f"PDFs to ingest: {len(todo)} (of {len(pdfs)} eligible; {len(done)} already done)")
    print(f"programs.json starting size: {start_total}\n", flush=True)

    for i, pdf in enumerate(todo, 1):
        rel = str(pdf.relative_to(PDFS))
        svc = infer_service(pdf)
        try:
            entries = ij.ingest(pdf, service=svc, document=pdf.stem, document_date="2026-04",
                                 limit=(args.limit_per_pdf or None))
            res = ij.merge_into_corpus(entries, CORPUS, preserve_curated=True)
            funded = sum(1 for e in entries if e["funding_history"]
                         and any(v["funded_M"] is not None for v in e["funding_history"].values()))
            print(f"[{i}/{len(todo)}] {rel[:46]:46s} svc={svc:11s} "
                  f"parsed={len(entries):4d} funded={funded:4d} new={res['n_new']:4d} "
                  f"skip_curated={res['n_skipped_existing']:3d}  total={res['n_total']}", flush=True)
        except Exception as e:
            print(f"[{i}/{len(todo)}] {rel}: ERROR {e!r}", file=sys.stderr)
            traceback.print_exc()
        done.add(rel)
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps({"done": sorted(done)}, indent=1))

    end_total = len(json.loads(CORPUS.read_text())["programs"])
    print(f"\nDONE. programs.json: {start_total} -> {end_total}  (+{end_total - start_total})")


if __name__ == "__main__":
    main()
