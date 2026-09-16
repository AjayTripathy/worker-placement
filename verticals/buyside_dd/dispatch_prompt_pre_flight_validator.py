"""Dispatch-prompt pre-flight validator for Signal OS orchestrator.

The session-meta-finding (from the IPO DD round 2026-05-28): 5 of 5 sub-agent
dispatches contained at least one factual error in the orchestrator's prompt
(IBM control of Quantinuum, H&F/KKR on Entrata cap table, State of CA POBs,
Vallejo POBs, AB 1054 per-event cap). Every one was caught by the hostile-
validator discipline applied AT the sub-agent. By then the agent had spent
~30s correcting context.

This validator runs the same check at the ORCHESTRATOR level — extracts named-
entity claims from a draft prompt and suggests verification queries before the
prompt is dispatched. Targets ~10-30 second pre-flight overhead vs ~30 min
of agent-time spent correcting downstream.

## Pattern catalog (extracted from the 5 known-bad prompts)

Each known-bad claim shares structure: a specific factual assertion about a
named entity that's verifiable via a known public source. The validator
identifies these patterns and suggests verification queries.

| Pattern | Example | Verification source |
|---|---|---|
| "X is an investor in Y" / "X owns Z% of Y" | "IBM-controlled Quantinuum" | SEC EDGAR principal stockholders + 13F + Form D |
| "X had $N in Y" | "$10B+ in CA State POBs" | SEC EDGAR / CDIAC / agency disclosure |
| "X went bankrupt because Y" / "X had problem with Y" | "Vallejo BK due to POBs" | Court filings / news search |
| "Regulatory program X has Y cap/limit/rule" | "$5B per-event cap under AB 1054" | Statute text / regulatory agency |
| "X filed for Y on date Z" | "SpaceX S-1 filed 2026-05-20" | SEC EDGAR submissions endpoint |
| "X is in sector Y" | "Sensei Harbor is a SPAC" | EDGAR + company description |

## Usage

```python
from verticals.buyside_dd.dispatch_prompt_pre_flight_validator import validate
report = validate(prompt_text)
if report["flagged_claims"]:
    # Review before dispatching
    for c in report["flagged_claims"]:
        print(f"  {c['pattern']}: '{c['claim_text']}' → verify via {c['verification_url']}")
```

## v2 changes (from v1 → 5/5 catch-rate on known-bad fixtures)

- Added `hyphenated_control_claim` pattern (catches "IBM-controlled Quantinuum")
- Added `regulatory_program_with_dollar_limit` pattern (catches "AB 1054 has $5B cap")
- Loosened `regulatory_program_detail` regex to also match more verbs
- Whitespace normalization (`_normalize`) to fix cross-newline regex misses
- `auto_verify=True` mode: dispatches EDGAR full-text verification per claim,
  returns `n_likely_false` count for orchestrator triage

## Auto-verify semantics

EDGAR full-text returns "plausible / likely false" — a ZERO-hit result is a
strong signal the claim is wrong (entities never co-appear in any filing); a
non-zero result is weak (they co-appear but the relationship might still be
mis-stated). For high-precision falsification, escalate to structured XBRL
principal-stockholders parsing or LLM-based ownership extraction (v3).

## Limitations

- Heuristic regex extraction; misses prose-only claims (e.g., "is a market leader")
- Entity extraction is greedy in some patterns — flagged-claim text may include
  leading words. Sufficient for the orchestrator-review use case; not clean enough
  for fully autonomous dispatch decisions.
- No NER beyond capitalized-token heuristic

v3 would: (a) use LLM-based NER for cleaner entity extraction,
(b) parse XBRL principal-stockholders table for hard ownership verification.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Optional


def _normalize(text: str) -> str:
    """Pre-process prompt for cleaner regex matching:
    - collapse whitespace (multi-line -> single line per sentence)
    - normalize quotes/dashes
    - ensure sentence boundaries
    """
    # Normalize unicode quotes/dashes
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    text = text.replace("—", "-").replace("–", "-")
    # Collapse internal whitespace to single space, preserving sentence boundaries
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    text = " ".join(lines)
    # Normalize multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text


# Patterns from the 5 known-bad prompts (v2 — broader matching)
PATTERNS = [
    {
        "name": "investor_ownership_claim",
        "regex": re.compile(
            r"(?P<entity>(?:[A-Z][A-Za-z0-9&\.]+(?:\s+[A-Z][A-Za-z0-9&\.]+){0,3}))"
            r"\s+(?:is\s+(?:an?\s+)?investor\s+in|owns|owned\s+by|controls?|controlled\s+by|"
            r"acquired|merged\s+with|partnered\s+with)"
            r"\s+(?P<target>(?:[A-Z][A-Za-z0-9&\.]+(?:\s+[A-Z][A-Za-z0-9&\.]+){0,3}))",
            re.IGNORECASE,
        ),
        "verification_hint": "SEC EDGAR principal-stockholders table + 13F + Form D + S-1 cap-table; cross-check Sidley/Wilson Sonsini press release",
        "verification_url_template": "https://efts.sec.gov/LATEST/search-index?q=%22{entity}%22+%22{target}%22&forms=S-1,13F-HR,D",
        "auto_verify": "edgar_fulltext",
    },
    {
        "name": "hyphenated_control_claim",
        "regex": re.compile(
            # require word boundary then a single capitalized token before the hyphen
            r"\b(?P<entity>[A-Z][A-Za-z0-9&\.]+)"
            r"-(?:controlled|owned|backed|funded|managed|sponsored|operated|run|led|affiliated)\b"
            r"(?:\s+[a-z]+)?"  # optional connector word
            r"\s+(?P<target>(?:[A-Z][A-Za-z0-9&\.]+(?:\s+[A-Z][A-Za-z0-9&\.]+){0,2}))?",
        ),
        "verification_hint": "SEC EDGAR principal-stockholders table — the hyphenated 'X-controlled Y' form often inflates 'partnership' to 'control'",
        "verification_url_template": "https://efts.sec.gov/LATEST/search-index?q=%22{entity}%22+%22{target}%22&forms=S-1,13F-HR,D",
        "auto_verify": "edgar_fulltext",
    },
    {
        "name": "specific_dollar_amount_claim",
        "regex": re.compile(
            r"(?P<amount>\$\d+(?:\.\d+)?(?:[KMBT]|\s*(?:million|billion|trillion)))"
            r"(?:\s+(?:in\s+|of\s+|raise\s+|outstanding\s+|debt\s+|equity\s+|cap\s+|fund\s+))"
            r"(?P<subject>(?:[A-Za-z][A-Za-z0-9&\.\s]{0,40}))",
            re.IGNORECASE,
        ),
        "verification_hint": "SEC EDGAR / agency disclosure / press release",
        "verification_url_template": "https://efts.sec.gov/LATEST/search-index?q=%22{subject}%22+%22{amount}%22",
    },
    {
        "name": "historical_bankruptcy_event",
        "regex": re.compile(
            r"(?P<entity>(?:[A-Z][A-Za-z0-9&\.]+(?:\s+[A-Z][A-Za-z0-9&\.]+){0,3}))"
            r"(?:\s+(?:filed|filing)\s+(?:for\s+)?(?:Ch(?:\.|apter)?\s*(?:7|9|11|13)|bankruptcy|BK))",
            re.IGNORECASE,
        ),
        "verification_hint": "PACER docket search + news search",
        "verification_url_template": "https://www.google.com/search?q=%22{entity}%22+bankruptcy+OR+%22chapter+11%22+OR+%22chapter+9%22",
    },
    {
        "name": "regulatory_program_detail",
        "regex": re.compile(
            r"(?P<program>(?:AB|SB|HR|S|Ed\s+Code|Gov(?:'t|ernment)?\s+Code|H(?:SC|&\s+SC)|Title|Section|Sec\.)\s*\d+(?:\.\d+)?[a-z]?)"
            r"(?:\s+(?:has|provides|caps|limits|requires|exempts|prohibits|sets|establishes|creates|authorizes|wraps|allows|forbids))"
            r"\s+(?P<detail>[^.;]{1,80})",
            re.IGNORECASE,
        ),
        "verification_hint": "California Legislative Information / OneCASE / statute text directly",
        "verification_url_template": "https://leginfo.legislature.ca.gov/faces/billSearchClient.xhtml?search_keywords={program}",
    },
    {
        "name": "regulatory_program_with_dollar_limit",
        "regex": re.compile(
            r"(?P<program>(?:AB|SB|HR|S|Ed\s+Code|Gov(?:'t|ernment)?\s+Code)\s*\d+(?:\.\d+)?)"
            # allow optional noun phrase (e.g. "Wildfire Fund") + flexible verb
            r"(?:\s+[A-Za-z]+){0,5}\s+"
            r"(?:has|provides|caps|limits|imposes|sets|establishes|allows|creates)"
            # optional intermediate words/preposition ("a", "an annual cap of", "liability at")
            r"(?:\s+[A-Za-z]+){0,6}\s+"
            r"(?:at\s+|of\s+|to\s+|at\s+a\s+)?"
            r"(?P<amount>\$\d+(?:\.\d+)?(?:\s*[KMBT]|\s*(?:million|billion|trillion))?)",
            re.IGNORECASE,
        ),
        "verification_hint": "Read the statute text directly — claims of specific dollar limits in regulatory programs are often wrong",
        "verification_url_template": "https://leginfo.legislature.ca.gov/faces/billSearchClient.xhtml?search_keywords={program}",
    },
    {
        "name": "filing_date_assertion",
        "regex": re.compile(
            r"(?P<entity>(?:[A-Z][A-Za-z0-9&\.]+(?:\s+[A-Z][A-Za-z0-9&\.]+){0,3}))"
            r"\s+(?:filed|submitted)\s+(?:its\s+)?(?P<filing_type>S-1|S-1/A|F-1|10-K|10-Q|8-K|Form\s+D|DRS|DRS/A)"
            r"(?:\s+(?:on|in)\s+(?P<date>\d{4}-\d{2}-\d{2}|\w+\s+\d{4}))?",
            re.IGNORECASE,
        ),
        "verification_hint": "SEC EDGAR submissions endpoint for the CIK",
        "verification_url_template": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={entity}&type={filing_type}",
    },
    {
        "name": "sector_or_classification_assertion",
        "regex": re.compile(
            r"(?P<entity>(?:[A-Z][A-Za-z0-9&\.]+(?:\s+[A-Z][A-Za-z0-9&\.]+){0,3}))"
            r"\s+is\s+(?:an?\s+)?(?P<classification>SPAC|blank\s+check|ETF|biotech|pharma|REIT|SaaS|aerospace|"
            r"defense|conduit|charter\s+school|CCRC|housing\s+authority|hospital)",
            re.IGNORECASE,
        ),
        "verification_hint": "EDGAR business-description + SIC code (https://data.sec.gov/submissions/CIK{cik}.json)",
        "verification_url_template": "https://efts.sec.gov/LATEST/search-index?q=%22{entity}%22",
    },
]

# Patterns that are SAFE (don't need pre-flight verification)
SAFE_PHRASES = {"the company", "the issuer", "the obligor", "the target", "the subject"}


@dataclass
class FlaggedClaim:
    pattern: str
    claim_text: str
    extracted_entity: Optional[str]
    extracted_subject: Optional[str]
    verification_hint: str
    verification_url: str
    line_context: str

    def __repr__(self):
        return f"<FlaggedClaim {self.pattern}: '{self.claim_text[:50]}...'>"


def _edgar_fulltext_verify(entity: str, target: str) -> dict:
    """Auto-verify an investor_ownership_claim against SEC EDGAR full-text search.

    Returns: {"verified": bool, "hit_count": int, "verification_url": str}
    Verified = some filing mentions both entity and target. (Weak signal — many false
    positives possible — but a ZERO-hit result is a strong signal the claim is wrong.)
    """
    try:
        q = f'"{entity}" "{target}"'
        url = f"https://efts.sec.gov/LATEST/search-index?q={urllib.parse.quote(q)}&forms=S-1,13F-HR,D,SC+13D,SC+13G"
        req = urllib.request.Request(url, headers={"User-Agent": "SignalOS/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read())
        total = d.get("hits", {}).get("total", {}).get("value", 0)
        return {
            "verified": total > 0,
            "hit_count": total,
            "verification_url": url,
            "interpretation": (
                "STRONG signal claim is FALSE — EDGAR has zero filings mentioning both entities."
                if total == 0 else
                f"Plausible — {total} EDGAR filings mention both entities (still review for ownership specifics)."
            ),
        }
    except Exception as e:
        return {"verified": None, "hit_count": None, "verification_url": url if 'url' in dir() else '',
                "interpretation": f"Auto-verify failed: {e}"}


def _hyphenated_control_verify(entity: str, target: str) -> dict:
    """Same as investor_ownership_claim — control claims should appear in S-1 / 13D / Form D."""
    return _edgar_fulltext_verify(entity, target)


AUTO_VERIFIERS = {
    "edgar_fulltext": _edgar_fulltext_verify,
}


def validate(prompt_text: str, max_flagged: int = 30, auto_verify: bool = False) -> dict:
    """Run pre-flight validation on a dispatch prompt.

    auto_verify: if True, for each flagged claim with a registered verifier, query
    the verification source and attach the result. ~1-3 seconds per claim. Recommended
    for production dispatch.

    Returns:
    {
      "prompt_length": int,
      "n_flagged": int,
      "n_likely_false": int,  # only set when auto_verify=True
      "flagged_claims": [...],
      "verification_query_urls": [str, ...],
    }
    """
    # Pre-process: normalize whitespace + remove newline-spanning issues
    normalized = _normalize(prompt_text)
    flagged: list[FlaggedClaim] = []

    for pat in PATTERNS:
        for m in pat["regex"].finditer(normalized):
            claim_text = m.group(0).strip()
            groups = m.groupdict()
            entity = (groups.get("entity") or "").strip()
            subject = (groups.get("subject") or groups.get("target") or "").strip()
            if any(p in claim_text.lower() for p in SAFE_PHRASES):
                continue
            url = pat["verification_url_template"]
            for k, v in groups.items():
                if v:
                    url = url.replace("{" + k + "}", v.replace(" ", "+"))
            line_start = max(0, m.start() - 80)
            line_end = min(len(normalized), m.end() + 80)
            context = normalized[line_start:line_end]
            flagged.append(FlaggedClaim(
                pattern=pat["name"],
                claim_text=claim_text,
                extracted_entity=entity or None,
                extracted_subject=subject or None,
                verification_hint=pat["verification_hint"],
                verification_url=url,
                line_context=context,
            ))
            if len(flagged) >= max_flagged:
                break
        if len(flagged) >= max_flagged:
            break

    # Auto-verify (optional)
    verification_results = {}
    n_likely_false = 0
    if auto_verify:
        for i, f in enumerate(flagged):
            # Find the pattern's auto_verify kind
            pat_def = next((p for p in PATTERNS if p["name"] == f.pattern), None)
            verifier_key = (pat_def or {}).get("auto_verify")
            if verifier_key and verifier_key in AUTO_VERIFIERS and f.extracted_entity and f.extracted_subject:
                result = AUTO_VERIFIERS[verifier_key](f.extracted_entity, f.extracted_subject)
                verification_results[i] = result
                if result.get("verified") is False:
                    n_likely_false += 1

    verification_urls = list(dict.fromkeys(f.verification_url for f in flagged))

    return {
        "prompt_length": len(prompt_text),
        "normalized_prompt_length": len(normalized),
        "auto_verify": auto_verify,
        "n_flagged": len(flagged),
        "n_likely_false": n_likely_false if auto_verify else None,
        "flagged_claims": [
            {
                "pattern": f.pattern,
                "claim_text": f.claim_text,
                "entity": f.extracted_entity,
                "subject": f.extracted_subject,
                "verification_hint": f.verification_hint,
                "verification_url": f.verification_url,
                "context": f.line_context,
                "auto_verify_result": verification_results.get(i),
            }
            for i, f in enumerate(flagged)
        ],
        "verification_query_urls": verification_urls,
    }


def validate_coverage(prompt_text: str, issuer: dict) -> dict:
    """Check whether the prompt invokes all graph-known applicable detectors / M-sources.

    Distinct from validate() (which catches false factual claims): this catches
    completeness failures — applicable graph nodes the orchestrator forgot to
    inline. Returns the missing nodes with their R/M framing so the orchestrator
    can patch the prompt before dispatch.
    """
    # Late import to avoid mandatory cross-vertical dep when only validate() is used
    import sys
    from pathlib import Path
    repo_root = Path(__file__).parent.parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from knowledge_graph.dispatch import coverage_report
    return coverage_report(prompt_text, issuer)


def format_coverage_report(coverage: dict) -> str:
    """Human-readable coverage report."""
    lines = [
        f"Coverage: {coverage['n_present']}/{coverage['n_applicable']} graph-applicable nodes mentioned in prompt",
        "",
    ]
    if coverage["n_missing"] == 0:
        lines.append("✓ Full coverage. No graph-applicable detectors/M-sources missing.")
        return "\n".join(lines)
    lines.append(f"⚠ {coverage['n_missing']} graph-applicable node(s) missing from prompt:")
    lines.append("")
    for m in coverage["missing"]:
        lines.append(f"  - [{m['kind']:8}] {m['vertical']}/{m['name']}")
        lines.append(f"      Summary: {m['summary']}")
        if m.get("verification_question"):
            lines.append(f"      R/M gap: {m['verification_question']}")
        lines.append(f"      Match reasons: {', '.join(m['match_reasons'])}")
        lines.append("")
    return "\n".join(lines)


def format_report(report: dict, indent: int = 2) -> str:
    """Format validator output as human-readable report."""
    lines = [
        f"Pre-flight validation: {report['n_flagged']} claims flagged in {report['prompt_length']}-char prompt",
        "",
    ]
    if report["n_flagged"] == 0:
        lines.append("✓ No factual-claim patterns detected. Prompt clean for dispatch.")
        return "\n".join(lines)
    for i, c in enumerate(report["flagged_claims"], 1):
        lines.append(f"{i}. [{c['pattern']}] '{c['claim_text'][:80]}'")
        if c["entity"]:
            lines.append(f"   Entity: {c['entity']}")
        if c["subject"]:
            lines.append(f"   Subject: {c['subject']}")
        lines.append(f"   Verify via: {c['verification_url']}")
        lines.append(f"   Hint: {c['verification_hint']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        prompt = open(sys.argv[1]).read()
    else:
        prompt = sys.stdin.read()
    report = validate(prompt)
    print(format_report(report))
