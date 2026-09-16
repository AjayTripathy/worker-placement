"""
Rebalance toolkit — refresh the framework at a new PB cycle.

Usage:
    python3 -m verticals.public_co.scripts.rebalance \\
        --pb-date 2027-03-15 \\
        --pdf-dir ~/Desktop/jbooks_fy28 \\
        --cutoff 2027-03-15 \\
        --phase all

Phases (run individually with --phase NAME or all):

  ingest_pdfs       — Run ingest_jbook.py on each PDF in --pdf-dir.
                      Auto-detects RDT&E vs Procurement from filename.
  extract_narrative — Re-extract per-PE narratives from new source PDFs.
  backfill_contractors — LLM-extract primary_contractors on new programs.
  rebuild_index     — Rebuild data/_jbook_data/by_entity.json.
  prep_subagents    — Generate prompts for each cohort ticker at --cutoff
                      cutoff. Writes prompts to /tmp/. Does NOT launch them
                      (subagent launch requires Claude Code Agent tool).
  aggregate         — Re-run jbook_exposure_aggregate to produce
                      _jbook_exposure_cohort/PREDICTIONS.md + matrix.json.
  report            — Re-generate the forward long-basket report (md + PDF).
  diff              — Diff new prescription vs prior. Writes diff to
                      _jbook_exposure_cohort/REBALANCE_DIFF.md.

  all               — Run ingest_pdfs → extract_narrative → backfill_contractors
                      → rebuild_index → prep_subagents → STOP (subagents
                      need Claude Code session to launch). Then re-run with
                      --phase aggregate report diff after subagents complete.

The subagent-launch step is intentionally manual because subagents must be
spawned through Claude Code's Agent tool, not from a CLI. The prep_subagents
phase writes a `runbook.txt` listing the Agent.run() calls to make.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PUBLIC_CO = THIS_DIR.parent
DATA = PUBLIC_CO / "data"


def _run_module(mod: str, *args: str) -> int:
    cmd = ["python3", "-m", mod, *args]
    print(f"\n  ▶ {' '.join(cmd)}", file=sys.stderr)
    r = subprocess.run(cmd, env={**os.environ, "PYTHONPATH": "."})
    return r.returncode


def _filename_to_doc_meta(fname: str) -> dict:
    """Best-effort: derive (service, document, date, type) from PDF filename."""
    lower = fname.lower()
    if "rdte" in lower or "rdt_and_e" in lower:
        typ = "rdte"
    elif "proc" in lower or "p_40" in lower:
        typ = "procurement"
    else:
        typ = "rdte"
    if "af_" in lower or "_af_" in lower or "air_force" in lower:
        svc = "Air Force"
    elif "navy" in lower:
        svc = "Navy"
    elif "army" in lower:
        svc = "Army"
    elif "darpa" in lower:
        svc = "Defense"
    elif "mda" in lower:
        svc = "Defense"
    elif "socom" in lower:
        svc = "Defense"
    elif "osd" in lower:
        svc = "Defense"
    elif "space_force" in lower or "spaceforce" in lower:
        svc = "Space Force"
    else:
        svc = "Defense"
    # FY in name?
    import re
    m = re.search(r"fy\s*(\d{4})", lower) or re.search(r"pb\s*(\d{4})", lower)
    fy = m.group(1) if m else "2028"
    doc = Path(fname).stem
    return {"service": svc, "document": f"FY {fy} {doc}", "type": typ,
            "date_estimate": f"{int(fy)-1}-06"}


def phase_ingest_pdfs(pdf_dir: Path) -> None:
    if not pdf_dir.exists():
        print(f"  ! PDF dir not found: {pdf_dir}", file=sys.stderr)
        return
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"  ! No PDFs in {pdf_dir}", file=sys.stderr)
        return
    print(f"  Found {len(pdfs)} PDFs to ingest:", file=sys.stderr)
    for p in pdfs:
        meta = _filename_to_doc_meta(p.name)
        print(f"  ▶ {p.name}  (service={meta['service']}, type={meta['type']})",
              file=sys.stderr)
        _run_module("verticals.public_co.scripts.ingest_jbook",
                     str(p), "--service", meta["service"],
                     "--document", meta["document"],
                     "--document-date", meta["date_estimate"],
                     "--type", meta["type"])


def phase_extract_narrative() -> None:
    _run_module("verticals.public_co.scripts.extract_pe_narratives")


def phase_backfill_contractors() -> None:
    _run_module("verticals.public_co.scripts.backfill_contractors")


def phase_rebuild_index() -> None:
    _run_module("verticals.public_co.scripts.build_jbook_entity_index")


def phase_prep_subagents(cutoff: str, output_infix: str) -> None:
    """Generate per-ticker subagent prompts; write runbook for Agent.run() invocations."""
    from verticals.public_co.jbook_exposure_cohort import COHORT
    from verticals.public_co.jbook_exposure_subagent_prompt import build_prompt

    runbook_lines = [
        f"# Subagent runbook — cutoff {cutoff}, output infix {output_infix}",
        f"# Generated {datetime.utcnow().isoformat()}Z",
        "#",
        "# Launch each via Claude Code's Agent tool:",
        "#   Agent({description: 'TICKER subagent', prompt: ...,",
        "#          run_in_background: true})",
        "#",
        "# Batch 4-9 in parallel to stay under Anthropic rate limits.",
        "",
    ]
    for m in COHORT:
        tk = m.ticker
        p = build_prompt(tk, cutoff=cutoff, output_infix=output_infix)
        prompt_path = Path(f"/tmp/prompt_{tk}_{output_infix.replace('.', '_')}.txt")
        prompt_path.write_text(p)
        runbook_lines.append(f"  {tk:<7}  prompt: {prompt_path}")
    runbook_path = DATA / "_jbook_exposure_cohort" / f"runbook_{output_infix}.txt"
    runbook_path.parent.mkdir(parents=True, exist_ok=True)
    runbook_path.write_text("\n".join(runbook_lines))
    print(f"  Wrote {len(COHORT)} prompts to /tmp/, runbook at {runbook_path}",
          file=sys.stderr)
    print(f"\n  NEXT STEP: In a Claude Code session, launch the subagents:",
          file=sys.stderr)
    print(f"  for each ticker, read /tmp/prompt_<TICKER>_{output_infix.replace('.', '_')}.txt",
          file=sys.stderr)
    print(f"  and pass to Agent.run with run_in_background=true.\n", file=sys.stderr)


def phase_aggregate() -> None:
    _run_module("verticals.public_co.jbook_exposure_aggregate")


def phase_report() -> None:
    _run_module("verticals.public_co.scripts.generate_forward_report")


def phase_diff(prior_matrix: Path | None) -> None:
    _run_module("verticals.public_co.scripts.diff_baskets",
                 *(["--prior", str(prior_matrix)] if prior_matrix else []))


PHASES = {
    "ingest_pdfs":          phase_ingest_pdfs,
    "extract_narrative":    phase_extract_narrative,
    "backfill_contractors": phase_backfill_contractors,
    "rebuild_index":        phase_rebuild_index,
    "prep_subagents":       phase_prep_subagents,
    "aggregate":            phase_aggregate,
    "report":               phase_report,
    "diff":                 phase_diff,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pb-date", required=True,
                     help="Expected/actual FY28 PB release date, ISO YYYY-MM-DD")
    ap.add_argument("--pdf-dir", default="~/Desktop/jbooks_fy28",
                     help="Directory of new J-Book PDFs to ingest")
    ap.add_argument("--cutoff", default=None,
                     help="Subagent cutoff (defaults to --pb-date)")
    ap.add_argument("--output-infix", default=None,
                     help="Output file infix for new vintage runs "
                          "(default derived from cutoff, e.g., 'jbook.2027')")
    ap.add_argument("--phase", default="all",
                     help="Phase to run, or 'all' for full pre-subagent pipeline")
    ap.add_argument("--prior-matrix", default=None,
                     help="Path to prior matrix.json for diff phase")
    args = ap.parse_args()

    cutoff = args.cutoff or args.pb_date
    output_infix = args.output_infix or f"jbook.{cutoff[:4]}"
    pdf_dir = Path(os.path.expanduser(args.pdf_dir))

    if args.phase == "all":
        # Pre-subagent automation; stop before subagent launch
        phase_ingest_pdfs(pdf_dir)
        phase_extract_narrative()
        phase_backfill_contractors()
        phase_rebuild_index()
        phase_prep_subagents(cutoff, output_infix)
        print("\n" + "=" * 70, file=sys.stderr)
        print("Pre-subagent pipeline complete. Launch subagents via Claude Code,",
              file=sys.stderr)
        print("then re-run with --phase aggregate report diff", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
    elif args.phase == "prep_subagents":
        phase_prep_subagents(cutoff, output_infix)
    elif args.phase == "ingest_pdfs":
        phase_ingest_pdfs(pdf_dir)
    elif args.phase == "diff":
        prior = Path(args.prior_matrix) if args.prior_matrix else None
        phase_diff(prior)
    elif args.phase in PHASES:
        PHASES[args.phase]()
    else:
        print(f"Unknown phase: {args.phase}", file=sys.stderr)
        print(f"Available: {', '.join(PHASES.keys())} | all", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
