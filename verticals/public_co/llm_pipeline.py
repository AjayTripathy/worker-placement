"""LLM-driven decomposition pipeline.

End-to-end:
  Stage 1: extract_claims(filing_text) -> list[Claim]
  Stage 2: pick_m_queries(claim) -> list[(source, kwargs)]
  Stage 3: run queries (mechanical) -> evidence
  Stage 4: score(claim, evidence) -> Finding
  Stage 5: aggregate (mechanical) -> per-company severity score

Stages 1, 2, 4 use Claude. Stages 3 and 5 are deterministic.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .filing_slice import slice_filing
from .m_recipes import RECIPES, BY_ID
from .m_recipes import render_for_llm as render_recipes_for_llm
from .m_source_catalog import CATALOG, call, render_for_llm
from .scoring import Severity


MODEL = os.environ.get("BACKTEST_LLM_MODEL", "claude-sonnet-4-5")
# Hard cap so a runaway document doesn't blow up costs
MAX_INPUT_CHARS_PER_FILING = 120_000
MAX_TOKENS_OUT = 4096
LLM_TIMEOUT_SEC = 180

# SDK path: read key from a 0600 file the user manages so it never enters env
# (and never enters my conversation context).
_KEY_FILE = Path("~/.anthropic_api_key").expanduser()
_SDK_CLIENT = None
if _KEY_FILE.exists():
    try:
        from anthropic import Anthropic
        _key = _KEY_FILE.read_text().strip()
        if _key.startswith("sk-ant-"):
            _SDK_CLIENT = Anthropic(api_key=_key)
            print(f"[llm_pipeline] using SDK with key from {_KEY_FILE}", file=sys.stderr)
    except Exception as e:
        print(f"[llm_pipeline] SDK init failed ({e}); falling back to CLI", file=sys.stderr)


@dataclass
class Claim:
    claim_id: str
    claim_text: str
    subject: str
    predicate: str
    object_value: str | None
    source_quote: str
    category: str


@dataclass
class MQuery:
    source: str
    kwargs: dict
    rationale: str


@dataclass
class Finding:
    claim_id: str
    claim_text: str
    severity: str
    M_supports_claim: bool | None
    M_check: str
    M_value: str
    interpretation: str


def _llm_call_sdk(system: str, user: str, max_tokens: int) -> str:
    """SDK path with retry on 529 Overloaded. ~5x faster than CLI subprocess."""
    backoffs = [2, 5, 12, 30]
    for attempt, delay in enumerate([0] + backoffs):
        if delay:
            time.sleep(delay)
        try:
            resp = _SDK_CLIENT.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
        except Exception as e:
            msg = str(e)
            is_transient = ("529" in msg or "overloaded" in msg.lower() or
                            "rate_limit" in msg.lower() or "timeout" in msg.lower())
            if is_transient and attempt < len(backoffs):
                print(f"  [SDK retry after {delay}s+next: {msg[:100]}]", file=sys.stderr)
                continue
            raise


def _llm_call_cli(system: str, user: str, max_tokens: int) -> str:
    """CLI subprocess fallback (uses keychain credentials)."""
    proc = subprocess.run(
        ["claude", "-p", "--system-prompt", system,
         "--model", MODEL, "--output-format", "text"],
        input=user,
        capture_output=True,
        text=True,
        timeout=LLM_TIMEOUT_SEC,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed (rc={proc.returncode}): {proc.stderr[:500]}")
    return proc.stdout.strip()


def _llm_call(system: str, user: str, max_tokens: int = MAX_TOKENS_OUT) -> str:
    """Single Claude call. Uses SDK if key file present, else CLI fallback."""
    if _SDK_CLIENT is not None:
        return _llm_call_sdk(system, user, max_tokens)
    return _llm_call_cli(system, user, max_tokens)


def _extract_json(text: str) -> Any:
    """Pull a JSON object/array out of an LLM response, tolerating fences."""
    # Strip ```json fences
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to find the first {...} or [...] span
    for opener, closer in [("[", "]"), ("{", "}")]:
        i = text.find(opener)
        if i >= 0:
            depth = 0
            for j in range(i, len(text)):
                if text[j] == opener:
                    depth += 1
                elif text[j] == closer:
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[i : j + 1])
                        except json.JSONDecodeError:
                            break
    raise ValueError(f"could not parse JSON from LLM response (first 300 chars): {text[:300]!r}")


# ============================================================================
# Stage 1: extract claims from filing text
# ============================================================================

BLINDING = """BLINDING DISCIPLINE (MANDATORY): You are operating at a historical cutoff date. Treat the world as if you have no knowledge of any event after the cutoff. Do not let any post-cutoff knowledge — bankruptcies, scandals, restructurings, partnership terminations, regulatory actions, market reactions — about the issuer, its counterparties, or its industry color your work. If you find yourself reasoning "I know this company later went bankrupt, so this claim is suspicious," STOP. Score only on the cutoff-date evidence the framework retrieves. The point of this analysis is to test whether the framework can detect weak signals in public records prospectively, not to confirm what you already know about the outcome.

"""


EXTRACT_SYSTEM = BLINDING + """You are a forensic-disclosure analyst. Read an SEC filing excerpt and extract 5-8 specific FACTUAL claims that COULD be tested against external public registries.

A claim is HIGH DISCRIMINATIVE VALUE when:
- It names a specific external entity (counterparty, registry, jurisdiction, address) the framework can independently look up
- It quantifies something verifiable (count of stations, vehicles, patents, customers, employees, FDA approvals, clinical trials)
- It asserts a status that registries record (production-stage vehicle vs chassis/glider, FDA-approved drug vs clinical-stage, EPA-regulated facility vs paper claim)

A claim is LOW DISCRIMINATIVE VALUE when:
- Pure internal accounting (cash balance, share counts, convertible note details, retained earnings)
- HQ address or incorporation state alone (housekeeping)
- Subjective characterizations ("we are a leader", "industry-leading technology")
- Market-size or industry-trend claims
- Pure forward projections with NO named counterparty AND NO quantified milestone

KEY INSIGHT: forward-looking claims that include a quantified target ("we will deliver X vehicles to named customer Y by date Z" or "we operate N stations") ARE discriminative even though they're aspirational — the framework can check counterparty filings or registries to see if N stations actually exist or Y customer disclosed the order.

EXAMPLES OF GOOD EXTRACTIONS (showing the SHAPE; do not assume any specific outcome):

Filing excerpt:
"Our customer ABC Corp has placed firm orders for 12,000 units of our Model Z to be delivered between 2022 and 2025. Our manufacturing facility in Springfield, IL is operational and we currently produce at a run-rate of 200 units/month."

Good claims:
[
  {"claim_id":"C-001","claim_text":"ABC Corp has placed firm orders for 12,000 Model Z units to the company","predicate":"has_customer_order_from","object_value":"ABC Corp / 12,000 units","category":"customer_pipeline","source_quote":"Our customer ABC Corp has placed firm orders for 12,000 units"},
  {"claim_id":"C-002","claim_text":"The company operates a manufacturing facility in Springfield, IL","predicate":"operates_factory_at","object_value":"Springfield, IL","category":"physical_facility","source_quote":"Our manufacturing facility in Springfield, IL is operational"},
  {"claim_id":"C-003","claim_text":"The company produces Model Z vehicles at 200 units/month","predicate":"produces_vehicle","object_value":"Model Z / 200 units/month","category":"production_volume","source_quote":"we currently produce at a run-rate of 200 units/month"}
]

Filing excerpt:
"Our flagship product, the InfraNet, has been deployed at over 8,500 sites nationwide. We hold 41 issued patents in the areas of edge compute, network routing, and sensor fusion. Acme Inc. is our largest channel partner."

Good claims:
[
  {"claim_id":"C-001","claim_text":"The company has deployed InfraNet at 8,500+ sites nationwide","predicate":"has_deployment_count","object_value":"InfraNet / 8,500+ sites","category":"fueling_infrastructure","source_quote":"deployed at over 8,500 sites nationwide"},
  {"claim_id":"C-002","claim_text":"The company holds 41 issued patents in edge compute, network routing, and sensor fusion","predicate":"owns_patents_in","object_value":"41 patents in edge compute, network routing, sensor fusion","category":"technology","source_quote":"41 issued patents in the areas of edge compute, network routing, and sensor fusion"},
  {"claim_id":"C-003","claim_text":"Acme Inc. is the company's largest channel partner","predicate":"has_partnership_with","object_value":"Acme Inc.","category":"partnership","source_quote":"Acme Inc. is our largest channel partner"}
]

EXAMPLES OF WEAK EXTRACTIONS TO AVOID (do not produce these):

Filing excerpt: "We had cash and cash equivalents of $42,318,000 as of June 30, 2020. The Company is incorporated in Delaware. As of the filing date, we had 8,234,891 shares outstanding."

Bad: claims about cash balance, incorporation state, share counts. None are discriminative — they're accounting facts that nobody disputes.

Output JSON array only, no commentary. Each claim object MUST have all of:
- claim_id: short id like "C-001"
- claim_text: 1-sentence plain English
- subject: the issuer (usually the company name)
- predicate: e.g. "has_customer_order_from", "operates_factory_at", "owns_patents_in", "produces_vehicle", "has_fueling_stations", "has_clinical_trials_in", "has_fda_approval_for"
- object_value: the asserted value (counterparty name, address, count)
- source_quote: short verbatim quote from the filing
- category: one of [customer_pipeline, physical_facility, technology, partnership, regulatory_milestone, fueling_infrastructure, production_volume, other]

Extract 5-8 claims. Skip a slot rather than dilute with low-discriminative material."""


def extract_claims(ticker: str, filing_text: str, cutoff_date: str = "") -> list[Claim]:
    # Slice to the discriminative sections (Item 1. Business, Risk Factors,
    # MD&A, Background of Merger, etc.) up to budget. Avoids cover-page noise.
    text = slice_filing(filing_text, budget_chars=MAX_INPUT_CHARS_PER_FILING)
    cutoff_line = f"Cutoff date (your information horizon): {cutoff_date}\n" if cutoff_date else ""
    user = (
        f"Company ticker: {ticker}\n"
        f"{cutoff_line}"
        f"Filing sections (sliced to {len(text):,} chars from key business sections):\n\n{text}\n\n"
        "Output JSON array only."
    )
    print(f"  [LLM] extract_claims call ({len(text):,} chars in)...", file=sys.stderr)
    raw = _llm_call(EXTRACT_SYSTEM, user, max_tokens=4096)
    data = _extract_json(raw)
    claims = []
    for c in data:
        claims.append(Claim(
            claim_id=c.get("claim_id", f"C-{len(claims)+1:03d}"),
            claim_text=c.get("claim_text", ""),
            subject=c.get("subject", ticker),
            predicate=c.get("predicate", ""),
            object_value=c.get("object_value"),
            source_quote=c.get("source_quote", ""),
            category=c.get("category", "other"),
        ))
    return claims


# ============================================================================
# Stage 2: pick M-queries per claim
# ============================================================================

PICK_SYSTEM_TEMPLATE = BLINDING + """You match an extracted CLAIM to one or more pre-built M-source RECIPES (analyst-curated query templates) and fill in the variables.

{recipes}

Your job:
1. Read the claim.
2. Identify 1-2 recipes from the library above whose `applies_when` description fits.
3. For each, fill in the placeholder variables (e.g. <BRAND>, <STATE>, <COUNTERPARTY_CIK>, <CUTOFF>, <FUEL_TYPE>) using the claim text and the cutoff date.
4. If NO recipe fits, return an empty array. Do NOT invent queries off-recipe.

Variable conventions:
- <BRAND>: short company brand (e.g. "Rivian" not "Rivian Automotive Inc")
- <COMPANY_LEGAL_NAME>: legal name (e.g. "Rivian Automotive" or "Rivian IP Holdings") — try multiple if uncertain
- <STATE>: 2-letter US state code; null/skip recipe if state not US
- <CITY_OR_OMIT>: city name uppercase, or omit the kwarg entirely if no city
- <CUTOFF>: the cutoff_date string the user provides
- <COUNTERPARTY_CIK>: 10-digit zero-padded CIK from the hints list; OMIT this recipe if counterparty has no CIK (skip foreign / private counterparties)
- <COUNTERPARTY_START_OR_2018>: a date 1-2 years before the claim's first known disclosure, default "2018-01-01"
- <FUEL_TYPE>: "HY" for hydrogen, "ELEC" for EV charging
- <PATENT_AREAS> / <DICT_OF_BUCKETS_TO_KEYWORDS>: a dict like {{"battery": ["battery", "cell"], "motor": ["motor", "drive unit"]}} based on the claim's claimed tech areas
- <DISTINCTIVE_BRAND_OR_PRODUCT>: pick a name unlikely to collide (e.g. product code "EH216", drug brand "Trikafta", not common words)

Output JSON array. Each entry:
- recipe_id: id from the library
- source: source name from the recipe (you can copy from the recipe template)
- kwargs: filled-in dict (no placeholders left)
- rationale: 1 sentence why this recipe fits the claim

Hard rules:
- Only use recipes from the library above.
- All placeholders must be replaced with concrete values; never pass through a "<...>" string.
- If you can't fill a required placeholder (e.g. counterparty has no CIK, or claim is non-US), DROP that recipe rather than guess.
- Output JSON array only."""


def pick_m_queries(claim: Claim, cutoff_date: str, hint_ciks: dict | None = None) -> list[MQuery]:
    recipes_md = render_recipes_for_llm()
    hints = ""
    if hint_ciks:
        hints = "\n\nKnown CIKs you can reference:\n" + "\n".join(f"- {k}: {v}" for k, v in hint_ciks.items())
    user = (
        f"CLAIM:\n{json.dumps(asdict(claim), indent=2)}\n\n"
        f"Cutoff date: {cutoff_date}{hints}\n\n"
        "Output JSON array of recipe matches (1-2 typically; 0 if no recipe fits)."
    )
    raw = _llm_call(PICK_SYSTEM_TEMPLATE.format(recipes=recipes_md), user, max_tokens=2048)
    data = _extract_json(raw)
    queries = []
    for q in data:
        queries.append(MQuery(
            source=q.get("source", ""),
            kwargs=q.get("kwargs", {}),
            rationale=q.get("rationale", ""),
        ))
    return queries


# ============================================================================
# Stage 3: run queries (mechanical)
# ============================================================================

def run_queries(queries: list[MQuery]) -> list[dict]:
    out = []
    for q in queries:
        result = call(q.source, q.kwargs)
        out.append({
            "source": q.source,
            "kwargs": q.kwargs,
            "rationale": q.rationale,
            "result": result,
        })
        time.sleep(0.3)
    return out


# ============================================================================
# Stage 4: score claim vs evidence
# ============================================================================

SCORE_SYSTEM = BLINDING + """You are a forensic-disclosure analyst comparing a CLAIM to EVIDENCE from public records.

Your job: rate how well the evidence supports the claim, on this severity scale:

- PASS: Evidence corroborates the claim (registry shows the asserted fact).
- MODERATE_UNDERDELIVERY: Some support but quantitatively or qualitatively thinner than asserted.
- SEVERE_UNDERDELIVERY: Evidence shows ≤25% of what was claimed, or asserted fact largely missing.
- RED_FLAG_NEGATIVE: Direct contradiction — registry shows zero / the opposite of the claim.
- UNVERIFIABLE: Query failed (rate-limit / wrong source / no jurisdictional coverage). NOT to be used as a fraud signal — be honest when the framework can't verify.

Output a single JSON object with:
- severity: one of [PASS, MODERATE_UNDERDELIVERY, SEVERE_UNDERDELIVERY, RED_FLAG_NEGATIVE, UNVERIFIABLE]
- M_supports_claim: true | false | null  (null only if UNVERIFIABLE)
- M_check: one-line description of what was checked
- M_value: one-line summary of what the evidence shows
- interpretation: 2-3 sentences explaining the rating

CALIBRATION HEURISTICS (apply before deciding severity — these prevent false positives from M-source coverage gaps):

1. EPA FRS scope. EPA's Facility Registry Service only registers facilities with EPA-regulated activities (waste streams, air/water permits, pesticide/chemical reporting). Pure offices, R&D labs, software dev sites, light assembly, and aviation/aerospace test facilities are EXPECTED to be absent. Absence in EPA FRS is a red flag ONLY for facilities that plausibly require an environmental permit: chemical processing, paint/coating, large-scale metal powder handling, foundries, large emissions sources. Otherwise it's UNVERIFIABLE or PASS-by-default-on-other-evidence.

2. Foreign-issuer ADR disclosure. Foreign private issuers (20-F filers, ADR-only US presence) have structurally thinner US disclosure than 10-K filers. 0-2 EDGAR mentions of a foreign counterparty/parent is CONSISTENT WITH NORMAL practice and not a red flag by itself. Only red-flag a 0 if the counterparty is a US-listed 10-K filer AND the claimed commitment is materially large for them (e.g. multi-billion firm orders should appear in Material Commitments).

3. Planned vs operational. If a claim describes a facility as "planned", "identified", "to be built", "site selection", or similar future-tense language, registries are EXPECTED to be empty. Do not RED_FLAG_NEGATIVE on these — at most MODERATE_UNDERDELIVERY if the framing in the filing is misleadingly definite.

4. Investment vs operating partner. A counterparty named only as an investor/equity partner is unlikely to disclose the investee as a material customer. Apply red-flag standard only to operating/customer partnerships, not investment ones.

5. Source-jurisdiction mismatches. NHTSA covers ground motor vehicles only — aviation, charging networks, satellites, biotech, etc. are EXPECTED to be absent. Do not flag. EPA FRS covers US facilities only — non-US operations naturally absent. FMCSA covers interstate motor carriers only.

6. Name-variant fragility. "Joby" vs "Joby Aviation" vs "Joby Aero" can return very different registry hits. If a single-variant query returns 0 hits, lean UNVERIFIABLE rather than RED_FLAG_NEGATIVE unless you have evidence the query covered the legal-entity space adequately.

7. Counterparty-side disclosure threshold. A US-listed counterparty's filings disclosing the issuer 1-3 times is MODEST BUT REAL corroboration (PASS or MODERATE), not a SEVERE absence. SEVERE only applies when 0 mentions exist AND the counterparty would normally be expected to disclose materially (large firm order, named strategic partner, multi-year supply agreement).

Be calibrated, not paranoid. A clinical-stage biotech HAVING zero FDA-approved drugs is expected, not a red flag. A charging-network company NOT being NHTSA-registered is expected. An EV-OEM without an EPA FRS facility in the claimed state IS a red flag (because EV manufacturing emits and is EPA-regulated)."""


def score_claim(claim: Claim, evidence: list[dict]) -> Finding:
    user = (
        f"CLAIM:\n{json.dumps(asdict(claim), indent=2)}\n\n"
        f"EVIDENCE:\n{json.dumps(evidence, indent=2, default=str)[:8000]}\n\n"
        "Output a single JSON object scoring the claim."
    )
    raw = _llm_call(SCORE_SYSTEM, user, max_tokens=1024)
    data = _extract_json(raw)
    return Finding(
        claim_id=claim.claim_id,
        claim_text=claim.claim_text,
        severity=data.get("severity", "UNVERIFIABLE"),
        M_supports_claim=data.get("M_supports_claim"),
        M_check=data.get("M_check", ""),
        M_value=data.get("M_value", ""),
        interpretation=data.get("interpretation", ""),
    )


# ============================================================================
# Top-level: end-to-end LLM-driven analysis of one company
# ============================================================================

def _process_one_claim(claim: Claim, cutoff_date: str, hint_ciks: dict | None) -> tuple[Claim, list[dict], Finding]:
    """Pipeline for a single claim: pick → run → score. Used in parallel."""
    queries = pick_m_queries(claim, cutoff_date, hint_ciks=hint_ciks)
    evidence = run_queries(queries)
    finding = score_claim(claim, evidence)
    return claim, evidence, finding


def analyze_company(ticker: str, cutoff_date: str, filing_text: str,
                    hint_ciks: dict | None = None, out_dir: Path | None = None,
                    max_workers: int = 6) -> dict:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print(f"\n=== LLM analysis: {ticker} (cutoff {cutoff_date}) ===", file=sys.stderr)
    claims = extract_claims(ticker, filing_text)
    print(f"  {len(claims)} claims extracted", file=sys.stderr)

    findings = [None] * len(claims)
    all_evidence: dict = {}

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_process_one_claim, c, cutoff_date, hint_ciks): i
                   for i, c in enumerate(claims)}
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                claim, evidence, finding = fut.result()
            except Exception as e:
                print(f"  ! claim {claims[i].claim_id} failed: {e}", file=sys.stderr)
                finding = Finding(
                    claim_id=claims[i].claim_id,
                    claim_text=claims[i].claim_text,
                    severity="UNVERIFIABLE",
                    M_supports_claim=None,
                    M_check="pipeline error",
                    M_value=str(e)[:200],
                    interpretation=f"Per-claim pipeline failed: {e}"
                )
                evidence = []
            all_evidence[claims[i].claim_id] = evidence
            findings[i] = finding
            print(f"  [{claims[i].claim_id}] -> {finding.severity}  supports={finding.M_supports_claim}", file=sys.stderr)

    summary = {
        "ticker": ticker,
        "cutoff": cutoff_date,
        "n_claims": len(claims),
        "n_contradicted": sum(1 for f in findings if f.M_supports_claim is False),
        "claims": [asdict(c) for c in claims],
        "evidence": all_evidence,
        "findings": [asdict(f) for f in findings],
    }

    if out_dir:
        out_dir.mkdir(exist_ok=True, parents=True)
        (out_dir / "llm_analysis.json").write_text(json.dumps(summary, indent=2, default=str))

    return summary
