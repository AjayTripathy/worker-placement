"""
Shared Phase-2 (Scorer) prompt for all cohorts.

The scorer subagent receives a per-ticker plan.json (from Phase 1 +
compile) and executes the M-source queries claim-by-claim, scoring
each. It does NOT re-extract claims and does NOT propose new
connectors mid-run — those concerns belong to Phase 1.

Output: data/_local/<TK>.scores.json (same schema as the legacy inline
subagent's scores.json, so existing aggregators consume it unchanged).
"""
from __future__ import annotations

from typing import Any


PROMPT_TEMPLATE = """You are running PHASE 2 (the Scorer) of the Signal OS 3-phase pipeline on a single ticker. The plan has been built (Phase 1) and the M-source queries have ALREADY been executed deterministically (plan_executor.py). Your job is to read the pre-computed M-side results and score each claim's severity.

**You do NOT run M-source queries.** All queries already ran; their results are in `<ticker>.queries.json`. You do NOT re-extract claims. You do NOT propose new connectors.

== STRICT BLINDING DISCIPLINE ==
- No WebSearch, no WebFetch, no training-data hindsight about post-cutoff events
- No reading other tickers' plans, queries, or scores
- Treat as forward-looking from the cutoff date

== ASSIGNMENT ==
Ticker: {ticker}    Cutoff: {cutoff}
Plan:    /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.plan.json
Queries: /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.queries.json   (pre-computed M-side results)
Output (REQUIRED):
         /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.scores.json

== COHORT CONTEXT (for severity calibration) ==
{cohort_context}

== WORKFLOW ==
1. Read plan.json (the claims + per-claim M-source mapping).
2. Read queries.json (the M-side results for every claim, keyed by claim_id).
3. For each claim in plan.json, mentally score severity:
   - If `m_source_status == "MAPPED"`: the result is a list of query-execution dicts. Examine the data and assign severity (PASS/MODERATE/SEVERE/RED_FLAG/UNVERIFIABLE) per the calibration heuristics.
   - If `m_source_status == "PROPOSED"` and the proposed connector was NOT promoted: score UNVERIFIABLE with interpretation noting "proposed connector not yet built: <name>" — this is intentional coverage acknowledgement, not failure.
   - If `m_source_status == "PROPOSED"` and the connector WAS promoted (result available): treat as MAPPED — examine the data, assign severity.
   - If `m_source_status == "NONE"`: score UNVERIFIABLE.
4. **Write scores.json ONCE** with all N claims at the end. Do NOT checkpoint per-claim — execution is already pre-computed, so a single write at the end is fine.
5. Final one-line summary: "{ticker}: N claims, severity counts: PASS=x MODE=y SEVE=z RED=w UNVE=v"

== SCORE RUBRIC ==
Severity values (use CANONICAL names; the aggregator's normalizer accepts shorter forms but prefer canonical):
- **PASS** — M-side evidence corroborates the claim
- **MODERATE_UNDERDELIVERY** — claim partially supported; disclosure-quality issue
- **SEVERE_UNDERDELIVERY** — claim materially overstated vs M-side evidence
- **RED_FLAG_NEGATIVE** — hard contradiction (counterparty disclosure or registry directly contradicts the claim)
- **UNVERIFIABLE** — no adjudicating M-source (catalog miss or proposed-connector-not-yet-built or structural NONE)

Apply cohort-specific calibration:
- **Heuristic 7 (counterparty-disclosure threshold):** if a claim names a Tier-1 counterparty at material $-scale and that counterparty's 10-K returns 0 hits for the company / product, treat as RED_FLAG_NEGATIVE.
- **Stage-ladder discipline:** if a claim conflates announced vs operational at the marketing tier while financial-statement notes disclose a lower stage, MODERATE-to-SEVERE depending on the magnitude gap.
- **Going-concern fingerprints:** Form 15-12G, 25-NSE, going-concern qualifier, reverse-split history in the filings_index — elevate severity of forward-revenue claims.
- **Foreign-issuer caveat:** 20-F filers are NOT a signal in themselves; don't penalize.

Each score entry:
```
{{
  "claim_id": "...",
  "claim_text": "...",
  "severity": "PASS|MODERATE_UNDERDELIVERY|SEVERE_UNDERDELIVERY|RED_FLAG_NEGATIVE|UNVERIFIABLE",
  "supports": ["q_label_1", ...],
  "M_check": "<source_id or source_name>",
  "M_value": "<short summary of what the query returned>",
  "interpretation": "<one sentence why this severity, referencing the calibration heuristic that applied>"
}}
```

== OUTPUT SCHEMA (scores.json) ==
```
{{"ticker": "{ticker}", "scores": [...]}}
```

== START NOW ==
Be efficient. Read plan.json + queries.json -> reason through all claims -> write scores.json ONCE at the end -> one-line summary. NO Bash queries needed. NO per-claim checkpointing.
"""


def build_scorer_prompt(
    *,
    ticker: str,
    cutoff: str,
    cohort_context: str,
    catalog: dict[str, dict[str, Any]],
) -> str:
    catalog_lines = []
    for src_name, spec in catalog.items():
        catalog_lines.append(f"  - `{src_name}` — {spec.get('description','').strip()[:120]}")
    catalog_block = "\n".join(catalog_lines)
    return PROMPT_TEMPLATE.format(
        ticker=ticker,
        cutoff=cutoff,
        cohort_context=cohort_context,
        catalog_block=catalog_block,
    )


def build_scorer_prompt_for_ticker(cohort_module: str, ticker: str) -> str:
    import importlib

    from .m_source_catalog import CATALOG

    m = importlib.import_module(cohort_module)
    return build_scorer_prompt(
        ticker=ticker,
        cutoff=m.CUTOFF,
        cohort_context=m.COHORT_CONTEXT,
        catalog=CATALOG,
    )
