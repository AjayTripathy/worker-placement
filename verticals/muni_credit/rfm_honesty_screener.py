"""R/f/M honesty signal screener for hospital muni MD&As.

WHY THIS EXISTS

The Ascension R/f/M divergence analysis (outputs/ascension_2024A_rfm/
DIVERGENCE_REPORT.md) surfaced four Mode B "implied verification" findings —
not lies, but framing choices an investor should notice:

  Ω1  Rating-action omission — MD&A doesn't mention recent agency actions
  Ω2  Operating-margin omission — MD&A discusses revenue/expense without the
      headline operating margin number
  R9  Same-facility framing — pervasive use of "same facility" to obscure
      consolidated GAAP decline
  Ω5  Debt-remediation attribution — improving ratios celebrated without
      crediting the debt retirement that drove them

This module checks each of those patterns programmatically across any
obligor's MD&A. Output is a 0-100 "honesty score" per dimension + an
aggregate score, plus citations to the specific text that triggered.

METHODOLOGY

Each check is implemented as a deterministic text-pattern search (case-
insensitive regex with surrounding context). Scores are normalized so HIGHER
= MORE HONEST. Designed to be run on the cleaned text output of a pdftotext
extraction (the .txt files in data/mdas/).

This is intentionally NOT an LLM-based extraction — we want signals that are
reproducible across runs and that any analyst can re-derive by grepping the
source PDF themselves.
"""
from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Optional

HERE = Path(__file__).parent
MDAS_DIR = HERE / "data" / "mdas"
OUTCOMES_DIR = HERE / "data" / "verified_outcomes_2023_2025" / "per_obligor"


# -- Text normalization ------------------------------------------------------

def normalize(text: str) -> str:
    """Strip the U+202D / U+202C bidi marks that pdftotext leaves around words
    in some MD&A PDFs (Ascension's exports are full of them) and collapse
    whitespace. Without this, regex matches fail silently because the literal
    word 'rating' isn't a word boundary in the raw extract.
    """
    # Strip Unicode formatting marks
    text = re.sub(r"[‪-‮⁦-⁩]", "", text)
    # Strip soft hyphens
    text = text.replace("­", "")
    return text


def context_around(text: str, match: re.Match, chars: int = 120) -> str:
    """Return ±chars context around a regex match, single-line."""
    start = max(0, match.start() - chars)
    end = min(len(text), match.end() + chars)
    return re.sub(r"\s+", " ", text[start:end]).strip()


# -- Check 1: Rating-action acknowledgment -----------------------------------

RATING_AGENCY_TERMS = [
    r"\bmoody\'?s?\b", r"\bstandard\s*&?\s*poor\'?s?\b", r"\bs&p\b",
    r"\bfitch\b", r"\bkroll\b", r"\bkbra\b",
]
RATING_ACTION_TERMS = [
    r"\bdowngrade", r"\bupgrade", r"\bnegative\s+outlook",
    r"\bpositive\s+outlook", r"\bnegative\s+watch", r"\bcredit\s+watch",
    r"\baffirm(?:ed|ation)", r"\brating\s+action", r"\bAaa?[0-9]?\b",
    r"\bAa[0-9]?\b", r"\bBaa[0-9]?\b", r"\bAA[+-]?\b", r"\bA[+-]?\b",
    r"\bBBB[+-]?\b",
]


def check_rating_acknowledgment(text: str) -> dict:
    """Score 0-100: did the MD&A discuss its rating-agency actions?

    Higher score = more transparent. Considers:
      - Mentions of any agency name
      - Mentions of rating actions
      - Co-occurrence within ~200 chars (real discussion not boilerplate)
    """
    text = normalize(text)
    agency_hits = []
    for pat in RATING_AGENCY_TERMS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            agency_hits.append((m, pat))
    action_hits = []
    for pat in RATING_ACTION_TERMS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            action_hits.append((m, pat))

    # Co-occurrence — agency name within 200 chars of action term
    cooccurrences = []
    for am, _ in agency_hits:
        for cm, cpat in action_hits:
            if abs(am.start() - cm.start()) < 200:
                cooccurrences.append({
                    "agency_match": text[am.start():am.end()],
                    "action_match": text[cm.start():cm.end()],
                    "context": context_around(text, am, 100),
                })
                break

    score = min(100, len(cooccurrences) * 25)  # 4+ co-occurrences = 100
    return {
        "check": "rating_action_acknowledgment",
        "score": score,
        "agency_mentions": len(agency_hits),
        "action_mentions": len(action_hits),
        "cooccurrences": len(cooccurrences),
        "samples": cooccurrences[:3],
        "interpretation": (
            "GREEN" if score >= 75 else
            "YELLOW" if score >= 25 else "RED — MD&A does not acknowledge agency actions"
        ),
    }


# -- Check 2: Operating margin disclosure -----------------------------------

# Look for explicit "operating margin" / "operating loss" / "operating income" with %
OP_MARGIN_PATTERNS = [
    r"operating\s+margin[^.]{0,80}(-?\d{1,2}\.\d+)\s*%",
    r"(-?\d{1,2}\.\d+)\s*%[^.]{0,40}operating\s+margin",
    r"operating\s+(loss|income)[^.]{0,80}\$?\s*\(?-?\s*[\d,.]+",
    r"income\s+from\s+operations",
    r"loss\s+from\s+operations",
]


def check_operating_margin_disclosure(text: str) -> dict:
    """Score 0-100: does MD&A explicitly disclose operating margin/income?

    Higher = more transparent. Counts explicit margin numbers and operating
    income/loss line items (not just expense discussion).
    """
    text = normalize(text)
    margin_with_pct = []
    op_income_loss = []
    for pat in OP_MARGIN_PATTERNS[:2]:
        for m in re.finditer(pat, text, re.IGNORECASE):
            margin_with_pct.append({
                "match": text[m.start():m.end()],
                "context": context_around(text, m, 100),
            })
    for pat in OP_MARGIN_PATTERNS[2:]:
        for m in re.finditer(pat, text, re.IGNORECASE):
            op_income_loss.append({
                "match": text[m.start():m.end()],
                "context": context_around(text, m, 100),
            })

    # Explicit % disclosure is the strongest signal
    score = min(100, len(margin_with_pct) * 50 + len(op_income_loss) * 10)
    return {
        "check": "operating_margin_disclosure",
        "score": score,
        "explicit_margin_pct_disclosures": len(margin_with_pct),
        "operating_income_loss_mentions": len(op_income_loss),
        "samples": (margin_with_pct + op_income_loss)[:3],
        "interpretation": (
            "GREEN" if score >= 75 else
            "YELLOW" if score >= 25 else
            "RED — MD&A discusses revenue/expense without disclosing operating margin %"
        ),
    }


# -- Check 3: Same-facility framing density --------------------------------

def check_same_facility_framing(text: str) -> dict:
    """Score 0-100: how heavily does the MD&A lean on 'same facility' framing?

    HIGHER score = LESS reliance on same-facility framing (MORE transparent).
    Same-facility metrics are legitimate but excessive use can mask consolidated
    GAAP decline through divestitures.

    Threshold:
      - 0-2 mentions per 1000 words: GREEN (standard disclosure)
      - 3-7: YELLOW (notable framing)
      - 8+: RED (heavy framing, likely obscuring GAAP shrinkage)
    """
    text = normalize(text)
    word_count = len(text.split())
    matches = list(re.finditer(r"same[-\s]facility", text, re.IGNORECASE))
    density_per_1000 = (len(matches) / max(1, word_count)) * 1000

    # Score inversely
    if density_per_1000 < 2:
        score = 100
        interp = "GREEN — minimal same-facility framing"
    elif density_per_1000 < 7:
        score = 60
        interp = "YELLOW — moderate same-facility framing"
    else:
        score = 20
        interp = f"RED — heavy same-facility framing ({density_per_1000:.1f}/1k words) likely masks GAAP decline"

    return {
        "check": "same_facility_framing",
        "score": score,
        "total_mentions": len(matches),
        "word_count": word_count,
        "mentions_per_1000_words": round(density_per_1000, 2),
        "samples": [context_around(text, m, 100) for m in matches[:3]],
        "interpretation": interp,
    }


# -- Check 4: Investment-income masking -------------------------------------

INVESTMENT_MASKING_PATTERNS = [
    r"investment\s+(?:income|gains?|returns?)[^.]{0,120}(?:improvement|improved|strong|growth|favorable|positive)",
    r"(?:improvement|improved|strong|growth|favorable|positive)[^.]{0,120}investment\s+(?:income|gains?|returns?)",
    r"non-?operating\s+(?:income|gains?)[^.]{0,120}(?:improvement|improved|strong|growth|favorable|positive)",
]


def check_investment_income_masking(text: str) -> dict:
    """Score 0-100: is the MD&A using investment income to frame operational
    'improvement'?

    LOWER score = more masking, less honest. Looks for investment-income terms
    in proximity to positive-framing language. A single instance can be
    legitimate; 3+ is the pattern we flagged on Ascension.
    """
    text = normalize(text)
    matches = []
    for pat in INVESTMENT_MASKING_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            matches.append({
                "match": text[m.start():m.end()][:200],
                "context": context_around(text, m, 100),
            })

    n = len(matches)
    if n == 0:
        score = 100
        interp = "GREEN — no investment-income masking detected"
    elif n <= 2:
        score = 70
        interp = "YELLOW — some investment-income framing (could be legitimate)"
    else:
        score = 30
        interp = f"RED — {n} investment-income-as-improvement passages; pattern of operational masking"

    return {
        "check": "investment_income_masking",
        "score": score,
        "matches_count": n,
        "samples": matches[:3],
        "interpretation": interp,
    }


# -- Aggregate screener ------------------------------------------------------

def screen_obligor(obligor_slug: str, mda_text: str) -> dict:
    """Run all 4 checks on one obligor's MD&A text.

    Returns dict with per-check scores + aggregate.
    """
    checks = {
        "rating_action_acknowledgment": check_rating_acknowledgment(mda_text),
        "operating_margin_disclosure": check_operating_margin_disclosure(mda_text),
        "same_facility_framing": check_same_facility_framing(mda_text),
        "investment_income_masking": check_investment_income_masking(mda_text),
    }
    aggregate = sum(c["score"] for c in checks.values()) / len(checks)
    n_red = sum(1 for c in checks.values() if "RED" in c["interpretation"])
    return {
        "obligor": obligor_slug,
        "aggregate_honesty_score": aggregate,
        "n_red_flags": n_red,
        "checks": checks,
        "tier": (
            "HONEST" if aggregate >= 75 and n_red == 0 else
            "MIXED" if aggregate >= 50 else
            "SUSPECT — multiple Mode B framing concerns"
        ),
    }


def screen_all() -> dict:
    """Screen every MD&A in data/mdas/*.txt."""
    results = {}
    for txt_path in sorted(MDAS_DIR.glob("*.txt")):
        slug = txt_path.stem.replace("_mda", "")
        text = txt_path.read_text(encoding="utf-8", errors="ignore")
        results[slug] = screen_obligor(slug, text)
    return results


if __name__ == "__main__":
    out = screen_all()
    print(json.dumps(out, indent=2))
