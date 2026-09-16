"""LLM-based pairwise disclosure classifier (Haiku) — shared helper.

Extracted from claim_evolution.py 2026-05-29 so that both that module AND the
new multi_venue_disclosure_consistency.py can reuse the same classification
engine. Pure helper — no ingestion logic, no EDGAR-specific behavior.

Given a search-term + a snippet of disclosure text, classifies one of:
  AFFIRMED   — claim reaffirmed, expanded, or newly entered
  AMENDED    — substantive economic terms changed
  TERMINATED — claim ended, canceled, defaulted
  UNRELATED  — term appears incidentally / boilerplate

Same prompt + same retry/backoff behavior as claim_evolution v3.

Honored design constraint from claim_evolution.py: if the anthropic SDK or API
key is unavailable, classify() returns {'error': ...} rather than falling back
to noisy keyword matching (LLM-only design choice 2026-05-18).
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "helper",
    "summary": "Shared LLM pairwise disclosure classifier (AFFIRMED/AMENDED/TERMINATED/UNRELATED) used by claim_evolution and multi_venue; infra, never dispatched.",
}

import json
import os
import re
import time
from pathlib import Path

# ── LLM setup ───────────────────────────────────────────────────────
_MODEL = os.environ.get("DISCLOSURE_CLASSIFIER_MODEL",
                         os.environ.get("CLAIM_EVOLUTION_MODEL",
                                         "claude-haiku-4-5-20251001"))
_KEY_FILE = Path("~/.anthropic_api_key").expanduser()
_SDK_CLIENT = None
_SDK_ERROR: str | None = None

if _KEY_FILE.exists():
    try:
        from anthropic import Anthropic
        _key = _KEY_FILE.read_text().strip()
        if _key.startswith("sk-ant-"):
            _SDK_CLIENT = Anthropic(api_key=_key)
    except Exception as e:
        _SDK_ERROR = f"SDK init failed: {e}"
else:
    _SDK_ERROR = f"no API key file at {_KEY_FILE}"


_SYSTEM_PROMPT = """You are classifying disclosure snippets (SEC filings, conference posters, press releases, earnings transcripts, pitch decks, regulatory letters) to determine whether they affirm, amend, or terminate a previously-disclosed relationship/transaction/claim.

You will receive a SEARCH TERM (e.g., a counterparty name like "Viking", a metric like "going concern", or a transaction descriptor like "Phase 2 enrollment of 38 patients") and a SNIPPET from a disclosure where that term appears.

Your job: classify the snippet into EXACTLY ONE of:

- AFFIRMED — the snippet confirms, reaffirms, expands, or NEWLY ENTERS a relationship/transaction. Examples: a 10-K disclosing the relationship continues; a new 8-K announcing the deal closed; an Amended-and-Restated Agreement that updates terms but keeps the deal alive; a press release describing the relationship in present-tense without any termination language; a conference poster reporting the same trial at a later cutoff with consistent design.

- AMENDED — the substantive terms of the relationship CHANGED in a way that has economic significance (consideration, scope, milestones, governance, cohort definition, endpoint, response criteria). NOT just executing a standard amendment-and-restatement that updates boilerplate. AMENDED requires a real substantive change visible in the snippet. For clinical/scientific claims: a cohort size change, endpoint redefinition, or evaluation-criteria shift counts as AMENDED.

- TERMINATED — the snippet ANNOUNCES that the relationship has ended, been canceled, rescinded, defaulted, withdrawn, or otherwise no longer holds. Examples: an 8-K Item 1.02 "Termination of Material Definitive Agreement"; a press release announcing the deal was called off; an explicit statement that "the Company terminated the Agreement on [date]"; counterparty exited; a trial cohort discontinued.

- UNRELATED — the term appears incidentally, in a boilerplate definitions section, in legal jargon that doesn't pertain to the original relationship, or the snippet is about something else and merely uses the same word.

CRITICAL RULES:
1. The mere presence of words like "terminate", "cancel", "material adverse", "default" does NOT mean TERMINATED. Every M&A contract has a "Termination" section listing conditions under which termination COULD occur — that is boilerplate, not actual termination. Classify based on whether the snippet ANNOUNCES an event, not on whether termination language is present.
2. If the snippet is the text of a contract that's being filed (Exhibit 2.1, Exhibit 10.x) AND that contract is being entered/amended/restated, this is AFFIRMED (the deal exists) or AMENDED (if you can see substantive changes), NOT TERMINATED.
3. "Going concern" mentioned in a snippet typically means the company still HAS a going-concern qualifier — that's AFFIRMED (the distress claim persists), not TERMINATED.
4. For scientific claims: if a later disclosure shows the same trial design but a LARGER cohort or LATER data cutoff, that's AFFIRMED (data maturing). If it shows the same N but a different ORR denominator definition or response threshold, that's AMENDED (definition shifted).
5. If you can't tell from the snippet, classify UNRELATED rather than guessing.

Output strict JSON only, no other text:
{
  "classification": "AFFIRMED" | "AMENDED" | "TERMINATED" | "UNRELATED",
  "reasoning": "one-sentence justification grounded in what the snippet actually says"
}"""


def is_available() -> bool:
    """Returns True if the classifier can make LLM calls right now."""
    return _SDK_CLIENT is not None


def unavailable_reason() -> str | None:
    """If not available, returns the reason string. None if available."""
    return None if _SDK_CLIENT is not None else (_SDK_ERROR or "LLM not configured")


def classify(search_term: str, snippet: str,
             venue: str = "(unspecified)",
             disclosure_date: str = "(unspecified)") -> dict:
    """Call Haiku to classify one snippet.

    Args:
      search_term: the entity / metric / claim being tracked
      snippet: text excerpt around the term (typically 1000-2500 chars)
      venue: source venue (e.g. "10-K", "ASCO 2025 poster", "press release")
      disclosure_date: ISO-ish date of the disclosure

    Returns:
      {"classification": "AFFIRMED" | "AMENDED" | "TERMINATED" | "UNRELATED",
       "reasoning": "..."}
      OR {"error": "..."} if the call fails.
    """
    if _SDK_CLIENT is None:
        return {"error": _SDK_ERROR or "LLM not configured"}
    user = (
        f"VENUE: {venue}\n"
        f"DISCLOSURE DATE: {disclosure_date}\n"
        f"SEARCH TERM: {search_term!r}\n\n"
        f"SNIPPET (text from this disclosure where the term appears):\n"
        f"---\n{snippet}\n---\n\n"
        f"Classify per the schema."
    )
    backoffs = [0, 2, 5, 12]
    last_err = None
    for delay in backoffs:
        if delay:
            time.sleep(delay)
        try:
            resp = _SDK_CLIENT.messages.create(
                model=_MODEL,
                max_tokens=400,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user}],
            )
            text = "".join(b.text for b in resp.content
                            if getattr(b, "type", None) == "text").strip()
            t = text
            if t.startswith("```"):
                t = re.sub(r"^```(?:json)?\s*", "", t)
                t = re.sub(r"\s*```$", "", t)
            try:
                j = json.loads(t)
            except json.JSONDecodeError:
                m = re.search(r"\{.*\}", t, re.DOTALL)
                if not m:
                    return {"error": f"non-JSON LLM output: {text[:200]}"}
                j = json.loads(m.group(0))
            cls = j.get("classification", "").upper().strip()
            if cls not in ("AFFIRMED", "AMENDED", "TERMINATED", "UNRELATED"):
                return {"error": f"bad classification {cls!r}",
                        "raw": text[:300]}
            return {"classification": cls,
                    "reasoning": j.get("reasoning", "")[:400]}
        except Exception as e:
            last_err = str(e)
            msg = last_err.lower()
            if not any(t in msg for t in ("529", "overload", "rate_limit", "timeout")):
                return {"error": last_err}
    return {"error": f"LLM failed after retries: {last_err}"}


def model_name() -> str:
    """Currently configured Haiku model id."""
    return _MODEL


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 -m verticals.public_co.m_sources.disclosure_classifier <search_term> <snippet>")
        sys.exit(1)
    term, snippet = sys.argv[1], sys.argv[2]
    print(json.dumps(classify(term, snippet), indent=2))
