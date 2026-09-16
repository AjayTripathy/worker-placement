"""Blinded manual decomposition harness.

Bypass the LLM. I (Claude) read the filing slice and produce claims +
M-source queries + scoring directly. Same connectors, same scoring scale —
just the LLM stages replaced by my own reading.

Discipline: I commit to NOT looking at the cohort outcome labels while writing
the per-company analyses. I look at outcomes only when computing the final
confusion matrix.

Per-company input: a list of (claim, [(source, kwargs)], severity, supports,
interpretation) tuples. Runner executes the queries and persists findings.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from .m_source_catalog import call as call_source
from .scoring import Severity

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from core.firewall import confusion_matrix


HERE = Path(__file__).parent
DATA = HERE / "data"
BLINDED_OUT = DATA / "_blinded_manual"
BLINDED_OUT.mkdir(exist_ok=True, parents=True)

SEV_WEIGHT = {
    "RED_FLAG_NEGATIVE": 4.0,
    "SEVERE_UNDERDELIVERY": 3.0,
    "MODERATE_UNDERDELIVERY": 1.5,
    "UNVERIFIABLE": 0.0,
    "PASS": 0.0,
}


@dataclass
class BlindedClaim:
    cid: str
    claim: str
    queries: list[tuple[str, dict]]   # [(source, kwargs), ...]
    # Scoring is filled in AFTER queries run, by reading the evidence
    severity: str | None = None
    supports: bool | None = None
    interp: str | None = None


def run_company(ticker: str, claims: list[BlindedClaim],
                outcome: str | None = None, detail: str = "") -> dict:
    """Execute queries for each claim. Returns aggregated result."""
    print(f"\n=== {ticker.upper()} ===", file=sys.stderr)
    findings: list[dict] = []
    evidence_all: dict = {}

    for c in claims:
        print(f"  [{c.cid}] {c.claim[:80]}", file=sys.stderr)
        ev_for_claim = []
        for source, kwargs in c.queries:
            print(f"    -> {source}({kwargs})", file=sys.stderr)
            r = call_source(source, kwargs)
            ev_for_claim.append({"source": source, "kwargs": kwargs, "result": r})
        evidence_all[c.cid] = ev_for_claim
        findings.append({
            "claim_id": c.cid,
            "claim": c.claim,
            "queries": [{"source": s, "kwargs": k} for s, k in c.queries],
            "severity": c.severity,
            "M_supports_claim": c.supports,
            "interpretation": c.interp,
        })

    # Aggregate
    score = sum(SEV_WEIGHT.get(f["severity"] or "", 0) for f in findings)
    n = len(findings)
    contra = sum(1 for f in findings if f["M_supports_claim"] is False)
    counts: dict[str, int] = {}
    for f in findings:
        s = f["severity"] or "NONE"
        counts[s] = counts.get(s, 0) + 1

    out = {
        "ticker": ticker,
        "outcome": outcome,
        "detail": detail,
        "n_claims": n,
        "n_contradicted": contra,
        "severity_score": round(score, 1),
        "score_per_claim": round(score / n, 2) if n else 0.0,
        "counts": counts,
        "claims": [
            {
                "cid": c.cid, "claim": c.claim,
                "queries": [{"source": s, "kwargs": k} for s, k in c.queries],
                "evidence": evidence_all[c.cid],
                "severity": c.severity,
                "supports": c.supports,
                "interp": c.interp,
            }
            for c in claims
        ],
    }
    out_path = BLINDED_OUT / f"{ticker}.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"  saved → {out_path.name}: score_per_claim={out['score_per_claim']}, contra={contra}", file=sys.stderr)
    return out


def confusion_matrix_print(rows: list[dict]) -> None:
    print()
    print("=" * 100)
    print(f"{'Ticker':<8} {'Outcome':<10} {'Claims':<7} {'Contra':<7} {'Score':<7} {'/claim':<7} {'Counts'}")
    print("-" * 100)
    for r in sorted(rows, key=lambda x: -x["score_per_claim"]):
        cstr = ", ".join(f"{k.split('_')[0][:4]}={v}" for k, v in sorted(r["counts"].items()))
        print(f"{r['ticker'].upper():<8} {r['outcome'] or '?':<10} {r['n_claims']:<7} "
              f"{r['n_contradicted']:<7} {r['severity_score']:<7} {r['score_per_claim']:<7} {cstr}")
    print("=" * 100)
    for thr in [0.5, 1.0, 1.5]:
        for label, pos in [("Strict (FRAUD)", {"FRAUD"}),
                           ("Loose (FRAUD+BANKRUPT)", {"FRAUD", "BANKRUPT"})]:
            cm = confusion_matrix(
                (r["score_per_claim"] >= thr, r["outcome"] in pos) for r in rows
            )
            c = cm["confusion"]
            print(f"  thr={thr}/claim {label}: TP={c['TP']} FP={c['FP']} TN={c['TN']} FN={c['FN']}  "
                  f"P={cm['precision']:.0%}  R={cm['recall']:.0%}  Sp={cm['specificity']:.0%}")
