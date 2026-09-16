"""Candidate m-source logging + aggregation.

Agents can declare a novel m-source they invented during scoring by using:
  M_source: "candidate:<short_kebab_name>"

The tuple must include a `candidate_meta` field with:
  - data_source: human-readable source name (URL, dataset name, API)
  - method: how the agent queried/computed the signal
  - raw_evidence_url: link to source, if any
  - raw_evidence_excerpt: short verbatim excerpt of the evidence
  - classification_rule: how the agent mapped raw evidence → signal
  - limitations: known constraints

This module walks pilot JSON directories, extracts candidate tuples,
groups them by candidate name, and writes a JSONL log for review.

Multi-pilot convergence (same candidate name appearing in 3+ pilots
independently) is the strongest signal that the candidate should be
promoted to a formal m-source module.

Usage:
  python3 -m verticals.public_co.m_sources.candidate_log
    [--pilots-glob '<glob>']      # default: all data/_*/_*/scores/pilot_*.json
    [--out <jsonl>]                # default: data/_candidate_m_sources.jsonl
    [--min-convergence 1]          # report only candidates seen >= N times
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "helper",
    "summary": "Aggregates agent-invented candidate m-sources from pilot runs; Ring-2 promotion bookkeeping.",
}

import argparse
import json
from collections import defaultdict
from pathlib import Path


DEFAULT_GLOBS = [
    "verticals/public_co/data/_backtest/*/scores/pilot_*.json",
    "verticals/public_co/data/_forward_test/*/scores/pilot_*.json",
    "verticals/public_co/data/_forward_test/forward_2026_05_25/rescores/pilot_*.json",
]
DEFAULT_OUT = Path("verticals/public_co/data/_candidate_m_sources.jsonl")


def extract_candidates(pilot_path: Path) -> list[dict]:
    """Return list of candidate-m-source tuples found in this pilot."""
    try:
        d = json.loads(pilot_path.read_text())
    except Exception as e:
        return []
    out = []
    pilot_meta = {
        "pilot_file": str(pilot_path),
        "ticker": d.get("ticker"),
        "cik": d.get("cik"),
        "filing_date": d.get("filing_date"),
        "cutoff": d.get("cutoff"),
        "sector": d.get("sector"),
    }
    for tup in d.get("rfm_tuples", []) or []:
        ms = tup.get("M_source") or ""
        if not isinstance(ms, str):
            continue
        if not ms.startswith("candidate:"):
            continue
        cand_name = ms.split("candidate:", 1)[1].strip()
        out.append({
            **pilot_meta,
            "candidate_name": cand_name,
            "claim_id": tup.get("claim_id"),
            "severity": tup.get("severity"),
            "direction": tup.get("direction"),
            "R": (tup.get("R") or "")[:300],
            "M_value": (tup.get("M_value") or "")[:500],
            "interpretation": (tup.get("interpretation") or "")[:400],
            "candidate_meta": tup.get("candidate_meta", {}),
        })
    return out


def aggregate(pilot_globs: list[str]) -> tuple[list[dict], dict[str, list[dict]]]:
    """Walk pilot files and aggregate candidate tuples.

    Returns:
      flat_list: every candidate tuple encountered
      grouped: dict mapping candidate_name → list of tuples
    """
    flat = []
    for g in pilot_globs:
        for p in sorted(Path(".").glob(g)):
            flat.extend(extract_candidates(p))

    grouped: dict[str, list[dict]] = defaultdict(list)
    for entry in flat:
        grouped[entry["candidate_name"]].append(entry)
    return flat, grouped


def report(grouped: dict[str, list[dict]], min_convergence: int = 1) -> list[dict]:
    """Build a convergence report. Candidates with >= min_convergence
    occurrences are returned, sorted by convergence (high first)."""
    summary = []
    for name, entries in grouped.items():
        if len(entries) < min_convergence:
            continue
        # Convergence is by distinct (cik, filing_date) — same pilot
        # re-using the same candidate doesn't count.
        unique_pilots = {(e.get("cik"), e.get("pilot_file")) for e in entries}
        summary.append({
            "candidate_name": name,
            "n_occurrences": len(entries),
            "n_unique_pilots": len(unique_pilots),
            "sectors": sorted(set(e.get("sector") or "" for e in entries)),
            "tickers": sorted(set(e.get("ticker") or "" for e in entries)),
            "example_data_source": (entries[0].get("candidate_meta") or {}).get("data_source"),
            "example_method": (entries[0].get("candidate_meta") or {}).get("method"),
            "example_classification_rule": (entries[0].get("candidate_meta") or {}).get("classification_rule"),
        })
    summary.sort(key=lambda r: -r["n_unique_pilots"])
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilots-glob", action="append", default=None,
                    help="repeatable; glob(s) to scan. Default: backtest + forward_test pilots.")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--min-convergence", type=int, default=1)
    args = ap.parse_args()

    globs = args.pilots_glob or DEFAULT_GLOBS
    flat, grouped = aggregate(globs)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(json.dumps(e) + "\n" for e in flat))

    rep = report(grouped, min_convergence=args.min_convergence)
    print(f"Scanned {len(flat)} candidate tuples across {len(grouped)} distinct candidate names.")
    print(f"Wrote {out_path}")
    print()
    print(f"Convergence report (candidates with >= {args.min_convergence} unique-pilot occurrences):")
    print(f"{'candidate_name':50}  {'occ':>4}  {'pilots':>6}  sectors  / tickers")
    print("-" * 110)
    for r in rep:
        secs = ",".join(r["sectors"][:3])
        tks = ",".join(r["tickers"][:5])
        print(f"{r['candidate_name'][:50]:50}  {r['n_occurrences']:>4}  {r['n_unique_pilots']:>6}  {secs:30}  {tks}")

    return rep


if __name__ == "__main__":
    main()
