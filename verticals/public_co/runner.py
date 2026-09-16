"""Run a backtest end-to-end given a config module name.

Usage:
    python -m verticals.public_co.runner nkla
    python -m verticals.public_co.runner ride

Each phase can be run alone by passing --phase pull|claims|m|score.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from types import ModuleType

from . import edgar
from .scoring import print_summary, write_findings


HERE = Path(__file__).parent
DATA = HERE / "data"


def load_config(ticker: str) -> ModuleType:
    return importlib.import_module(f".configs.{ticker}", package="verticals.public_co")


def out_dir_for(cfg: ModuleType) -> Path:
    p = DATA / cfg.TICKER
    p.mkdir(exist_ok=True, parents=True)
    return p


def phase_pull(cfg: ModuleType) -> None:
    edgar.pull(
        cik=cfg.CIK,
        cutoff_date=cfg.CUTOFF_DATE,
        priority_forms=cfg.PRIORITY_FORMS,
        out_dir=out_dir_for(cfg),
    )


def phase_claims(cfg: ModuleType) -> None:
    out = out_dir_for(cfg) / "claims.json"
    out.write_text(json.dumps(cfg.CLAIMS, indent=2))
    print(f"Wrote {len(cfg.CLAIMS)} claims to {out}", file=sys.stderr)


def phase_m(cfg: ModuleType) -> None:
    out = out_dir_for(cfg)
    evidence: dict = {}
    for key, fn, kwargs in cfg.M_QUERIES:
        print(f"Running M query: {key}...", file=sys.stderr)
        # Allow kwargs to be a callable for late binding (e.g. resolve a path
        # that depends on the filings index existing).
        kw = kwargs(out) if callable(kwargs) else dict(kwargs)
        try:
            evidence[key] = fn(**kw)
        except Exception as e:
            evidence[key] = {"error": f"unhandled: {e}"}
            print(f"  ! {key} failed: {e}", file=sys.stderr)
    (out / "M_evidence.json").write_text(json.dumps(evidence, indent=2, default=str))
    print(f"Saved M-side evidence to {out / 'M_evidence.json'}", file=sys.stderr)


def phase_score(cfg: ModuleType) -> None:
    out = out_dir_for(cfg)
    claims = json.loads((out / "claims.json").read_text())
    evidence = json.loads((out / "M_evidence.json").read_text())
    by_id = {c["claim_id"]: c for c in claims}

    findings: list[dict] = []
    for claim_id, scorer in cfg.SCORERS.items():
        if claim_id not in by_id:
            print(f"  ! scorer for unknown claim_id {claim_id}", file=sys.stderr)
            continue
        f = scorer(evidence, by_id[claim_id])
        # Boilerplate fields the scorer doesn't have to repeat
        f.setdefault("claim_id", claim_id)
        f.setdefault("claim_text", by_id[claim_id]["claim_text"])
        f.setdefault("filing_date", by_id[claim_id].get("filing_date"))
        f.setdefault("knowable_at_filing_date", True)
        # Severity may be passed as Severity enum or string; normalize
        sev = f.get("severity")
        if hasattr(sev, "value"):
            f["severity"] = sev.value
        findings.append(f)

    write_findings(findings, out / "divergence_findings.json")
    print_summary(findings, cfg.CUTOFF_DATE, cfg.TICKER.upper())


PHASES = {
    "pull": phase_pull,
    "claims": phase_claims,
    "m": phase_m,
    "score": phase_score,
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker", help="config module name (e.g. nkla, ride)")
    ap.add_argument("--phase", choices=list(PHASES) + ["all"], default="all")
    args = ap.parse_args()

    cfg = load_config(args.ticker)
    phases = list(PHASES) if args.phase == "all" else [args.phase]
    for ph in phases:
        print(f"\n>>> phase: {ph}", file=sys.stderr)
        PHASES[ph](cfg)


if __name__ == "__main__":
    main()
