"""Provider interface — both LocalProvider and ApiProvider implement this.

Stage 1 (extract_and_pick): given a filing, return claims and which queries to
run for each. Local: read pre-written JSON. API: call Claude.

Stage 2 (score): given a claim and the evidence from running its queries,
return a Finding. Local: read pre-written JSON (or default UNVERIFIABLE if
the analyst hasn't filled it in yet). API: call Claude.
"""
from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path
from typing import Protocol

from .analysis_types import Claim, Evidence, Finding, MQuery


class Provider(Protocol):
    name: str

    def extract_and_pick(
        self,
        ticker: str,
        cutoff_date: str,
        filing_text: str,
        hint_ciks: dict[str, str],
    ) -> tuple[list[Claim], dict[str, list[MQuery]]]:
        ...

    def score(self, claim: Claim, evidence: list[Evidence]) -> Finding:
        ...


# ============================================================================
# LocalProvider — reads JSON files I write by hand
# ============================================================================

class LocalProvider:
    """Reads `data/_local/<ticker>.input.json` for claims+queries, and
    `data/_local/<ticker>.scores.json` for analyst scoring.

    Workflow:
      1. Analyst writes <ticker>.input.json by reading the filing
      2. Runner runs queries, saves evidence
      3. Analyst reads evidence, writes <ticker>.scores.json
      4. Runner assembles into the final CompanyAnalysis
    """

    name = "local"

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(exist_ok=True, parents=True)
        self._current_ticker: str | None = None
        self.score_binding = None
        self._claims = {}

    def _input_path(self, ticker: str) -> Path:
        return self.root / f"{ticker}.input.json"

    def _scores_path(self, ticker: str) -> Path:
        return self.root / f"{ticker}.scores.json"

    def extract_and_pick(self, ticker, cutoff_date, filing_text, hint_ciks):
        self._current_ticker = ticker
        self.score_binding, self._claims = None, {}
        path = self._input_path(ticker)
        if not path.exists():
            raise FileNotFoundError(
                f"LocalProvider expects {path}; write claims+queries there first."
            )
        data = json.loads(path.read_text(encoding='utf-8'))
        self.score_binding = binding(ticker, cutoff_date, data, filing_text)
        claims = []
        queries: dict[str, list[MQuery]] = {}
        for c in data["claims"]:
            cl = Claim(
                claim_id=c["claim_id"],
                claim_text=c["claim_text"],
                subject=c.get("subject", ""),
                predicate=c.get("predicate", ""),
                object_value=c.get("object_value"),
                source_quote=c.get("source_quote", ""),
                category=c.get("category", "other"),
            )
            claims.append(cl)
            queries[cl.claim_id] = [
                MQuery(source=q["source"], kwargs=q["kwargs"], rationale=q.get("rationale", ""))
                for q in c.get("queries", [])
            ]
        self._claims = {c.claim_id: c.claim_text for c in claims}
        return claims, queries

    def score(self, claim: Claim, evidence: list[Evidence]) -> Finding:
        # An unbound historical score is not evidence for today's input. In
        # particular, claim IDs such as c1 are not globally unique identities.
        if self._current_ticker and self._claims.get(claim.claim_id) == claim.claim_text:
            try:
                data = json.loads(self._scores_path(self._current_ticker).read_text(encoding='utf-8'))
            except (OSError, ValueError):
                data = {}
            if isinstance(data, dict) and isinstance(data.get('scores'), list) and data.get('binding') == self.score_binding:
                matches = [s for s in data.get('scores', []) if isinstance(s, dict) and s.get('claim_id') == claim.claim_id]
                if len(matches) == 1:
                    s = matches[0]
                    if s.get('severity') in {'RED_FLAG_NEGATIVE', 'SEVERE_UNDERDELIVERY', 'MODERATE_UNDERDELIVERY', 'UNVERIFIABLE', 'PASS'} and type(s.get('supports')) in {bool, type(None)}:
                        return Finding(severity=s['severity'], supports=s.get('supports'),
                            M_check=s.get('M_check', ''), M_value=s.get('M_value', ''), interpretation=s.get('interpretation', ''))
        return Finding(
            severity="UNVERIFIABLE",
            supports=None,
            M_check="awaiting analyst score",
            M_value="evidence saved; scoring not yet provided",
            interpretation="No uniquely identified score matches this ticker, claim, cutoff and input/source digest. Review the evidence and save the exact score_binding with the ticker's scores; unbound legacy scores require review.",
        )


def binding(ticker, cutoff_date, inputs, filing_text):
    """Persist this alongside newly reviewed scores; never infer it retroactively."""
    return {'v': 2, 'ticker': ticker, 'cutoff_date': cutoff_date,
            'input_sha256': hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest(),
            'source_sha256': hashlib.sha256(filing_text.encode()).hexdigest()}


# ============================================================================
# ApiProvider — calls Claude (SDK if API key file present, else CLI subprocess)
# ============================================================================

class ApiProvider:
    name = "api"

    def __init__(self):
        # Defer import so LocalProvider works without anthropic SDK installed
        from . import llm_pipeline as lp
        self._lp = lp

    def extract_and_pick(self, ticker, cutoff_date, filing_text, hint_ciks):
        claims_raw = self._lp.extract_claims(ticker, filing_text, cutoff_date=cutoff_date)
        # claims_raw is list[lp.Claim]; convert to shared types
        claims = [
            Claim(
                claim_id=c.claim_id,
                claim_text=c.claim_text,
                subject=c.subject,
                predicate=c.predicate,
                object_value=c.object_value,
                source_quote=c.source_quote,
                category=c.category,
            )
            for c in claims_raw
        ]
        queries: dict[str, list[MQuery]] = {}
        for cl_raw, cl in zip(claims_raw, claims):
            mqs = self._lp.pick_m_queries(cl_raw, cutoff_date, hint_ciks=hint_ciks)
            queries[cl.claim_id] = [
                MQuery(source=q.source, kwargs=q.kwargs, rationale=q.rationale)
                for q in mqs
            ]
        return claims, queries

    def score(self, claim: Claim, evidence: list[Evidence]) -> Finding:
        from .llm_pipeline import Claim as LpClaim
        cl = LpClaim(
            claim_id=claim.claim_id,
            claim_text=claim.claim_text,
            subject=claim.subject,
            predicate=claim.predicate,
            object_value=claim.object_value,
            source_quote=claim.source_quote,
            category=claim.category,
        )
        evidence_dicts = [
            {"source": e.source, "kwargs": e.kwargs, "rationale": "", "result": e.result}
            for e in evidence
        ]
        f = self._lp.score_claim(cl, evidence_dicts)
        return Finding(
            severity=f.severity,
            supports=f.M_supports_claim,
            M_check=f.M_check,
            M_value=f.M_value,
            interpretation=f.interpretation,
        )
