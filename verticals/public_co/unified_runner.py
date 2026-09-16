"""Unified end-to-end runner. Same code path for any Provider.

Stages:
  1. provider.extract_and_pick(filing_text)       → claims + queries-per-claim
  2. mechanically run queries                      → evidence-per-claim
  3. provider.score(claim, evidence)               → finding-per-claim
  4. aggregate into CompanyAnalysis, save JSON
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .analysis_types import CompanyAnalysis, Evidence
from .m_source_catalog import call as call_source
from .providers import Provider


HERE = Path(__file__).parent
DATA = HERE / "data"


def run_queries(queries) -> list[Evidence]:
    """Mechanical query execution. Shared between providers."""
    out = []
    for q in queries:
        result = call_source(q.source, q.kwargs)
        out.append(Evidence(source=q.source, kwargs=q.kwargs, result=result))
    return out


def analyze_company(
    ticker: str,
    cutoff_date: str,
    filing_text: str,
    provider: Provider,
    cik: str = "",
    outcome: str | None = None,
    outcome_detail: str = "",
    filing_name: str = "",
    hint_ciks: dict[str, str] | None = None,
    out_dir: Path | None = None,
    max_workers: int = 6,
) -> CompanyAnalysis:
    print(f"\n=== {ticker.upper()} (provider={provider.name}, cutoff={cutoff_date}) ===",
          file=sys.stderr)

    # Stage 1: extract claims + pick queries
    claims, queries_per_claim = provider.extract_and_pick(
        ticker, cutoff_date, filing_text, hint_ciks or {}
    )
    print(f"  {len(claims)} claims extracted", file=sys.stderr)

    # Stage 2: run queries (parallel across claims)
    evidence_per_claim: dict[str, list[Evidence]] = {}

    def _run(cl):
        evs = run_queries(queries_per_claim.get(cl.claim_id, []))
        return cl.claim_id, evs

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_run, c): c for c in claims}
        for fut in as_completed(futures):
            try:
                cid, evs = fut.result()
                evidence_per_claim[cid] = evs
            except Exception as e:
                cid = futures[fut].claim_id
                print(f"  ! query failed for {cid}: {e}", file=sys.stderr)
                evidence_per_claim[cid] = []

    # Stage 3: score each claim from its evidence
    findings_by_claim = {}
    for c in claims:
        try:
            f = provider.score(c, evidence_per_claim.get(c.claim_id, []))
        except Exception as e:
            from .analysis_types import Finding
            f = Finding(severity="UNVERIFIABLE", supports=None,
                        M_check="scoring error", M_value=str(e)[:200],
                        interpretation=f"Provider {provider.name} score raised: {e}")
        findings_by_claim[c.claim_id] = f
        print(f"  [{c.claim_id}] -> {f.severity}  supports={f.supports}", file=sys.stderr)

    analysis = CompanyAnalysis(
        ticker=ticker,
        cutoff_date=cutoff_date,
        cik=cik,
        outcome=outcome,
        outcome_detail=outcome_detail,
        filing=filing_name,
        provider=provider.name,
        claims=claims,
        queries_per_claim=queries_per_claim,
        evidence_per_claim=evidence_per_claim,
        findings_by_claim=findings_by_claim,
    )
    if out_dir is not None:
        analysis.save(out_dir / f"{ticker}.{provider.name}.json")
    return analysis


def stage_extract_only(
    ticker: str,
    cutoff_date: str,
    filing_text: str,
    provider: Provider,
    out_dir: Path,
    hint_ciks: dict[str, str] | None = None,
) -> tuple[Path, Path]:
    """For LocalProvider workflow: run stages 1+2 (extract+queries+evidence)
    so the analyst can read evidence and write scores afterwards.

    Returns (input_path, evidence_path).
    """
    claims, queries_per_claim = provider.extract_and_pick(
        ticker, cutoff_date, filing_text, hint_ciks or {}
    )
    evidence_per_claim: dict[str, list[dict]] = {}
    for c in claims:
        evs = run_queries(queries_per_claim.get(c.claim_id, []))
        evidence_per_claim[c.claim_id] = [
            {"source": e.source, "kwargs": e.kwargs, "result": e.result} for e in evs
        ]
    out_dir.mkdir(exist_ok=True, parents=True)
    ev_path = out_dir / f"{ticker}.evidence.json"
    ev_path.write_text(json.dumps({
        "ticker": ticker,
        "cutoff_date": cutoff_date,
        "evidence": evidence_per_claim,
    }, indent=2, default=str))
    return out_dir / f"{ticker}.input.json", ev_path
