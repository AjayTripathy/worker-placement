"""Strip HTML and extract the discriminative sections of an SEC filing.

10-K / S-4 / S-1 filings are huge (1-3 MB). The first 100 KB is mostly cover
page, table of contents, share counts, and definitions — none of the
discriminative business claims live there. The contestable claims are in:

  - Item 1.  Business
  - Item 1A. Risk Factors
  - Item 7.  Management's Discussion and Analysis (MD&A)
  - For S-4: "Information About <Company>" / "The Business" / "Background of the Merger"

This module finds those sections and concatenates them up to a budget. If
section boundaries can't be found, falls back to a sliding window approach.
"""
from __future__ import annotations

import re


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


# Strict section header patterns. Each must be specific enough to avoid
# inline-reference false positives. We use case-sensitive matching for ALL-CAPS
# patterns (real headers), and require structural markers (period after item
# number, "of the Merger" qualifier, etc.) for the rest.
SECTION_PATTERNS = [
    # 10-K / 10-Q items (case-insensitive but require period after number)
    ("ITEM 1. BUSINESS",        r"\bItem\s+1\.\s+Business\b",                                 re.IGNORECASE),
    ("ITEM 1A. RISK FACTORS",   r"\bItem\s+1A\.\s+Risk\s+Factors\b",                          re.IGNORECASE),
    ("ITEM 2. PROPERTIES",      r"\bItem\s+2\.\s+Properties\b",                               re.IGNORECASE),
    ("ITEM 7. MD&A",            r"\bItem\s+7\.\s+Management['’]s\s+Discussion\b",        re.IGNORECASE),
    # S-4 / S-1 / DEFM14A — qualified phrases that won't appear inline
    ("BACKGROUND OF MERGER",    r"\bBackground\s+of\s+the\s+(?:Merger|Business\s+Combination|Transactions?)\b", re.IGNORECASE),
    ("REASONS FOR MERGER",      r"\b(?:Reasons|Rationale)\s+for\s+the\s+(?:Merger|Business\s+Combination)\b", re.IGNORECASE),
    ("INFORMATION ABOUT",       r"\bInformation\s+About\s+(?:Nikola|Lordstown|the\s+Company|[A-Z][A-Za-z]+)\b", re.IGNORECASE),
    # Target-company business description (e.g. "Business of Lordstown" /
    # "BUSINESS OF NIKOLA"). This is where the operating-co's discriminative
    # forward-looking claims live in deSPAC merger docs. Use known company
    # names only — the generic fallback created false positives ("business of
    # the Parent...").
    ("BUSINESS OF COMPANY",     r"\bBusiness\s+of\s+(?:Nikola|Lordstown|Rivian|Lucid|Hyzon|Mullen|Fisker|Canoo|Arrival|Proterra|Faraday|Faraday\s+Future|ChargePoint|EVgo|QuantumScape|Lion\s+Electric|Lion|EHang|AeroVironment|Cassava|Vertex|Pharmaceuticals|Diamond\s+Foods|Hershey|Starbucks|Luckin)\b", re.IGNORECASE),
    ("COMPANYS BUSINESS",       r"\b(?:Nikola|Lordstown|Rivian|Lucid|Hyzon|Mullen|Fisker|Canoo|Arrival|Proterra|Faraday\s+Future|ChargePoint|EVgo|QuantumScape|Lion\s+Electric|EHang|AeroVironment|Cassava|Vertex|Diamond\s+Foods|Hershey|Starbucks|Luckin)['’]s\s+Business\b", re.IGNORECASE),
    # ALL-CAPS section headers — qualified to avoid cover-page legalese.
    # "THE BUSINESS" and "RISK FACTORS" alone fire all over cover pages, so we
    # require them to appear with non-inline qualifiers.
    ("CAPS BUSINESS OVERVIEW",  r"\b(?:OUR\s+BUSINESS\s+OVERVIEW|BUSINESS\s+OVERVIEW)\b", 0),
    ("CAPS DESCRIPTION OF BUS", r"\bDESCRIPTION\s+OF\s+(?:OUR\s+)?BUSINESS\b", 0),
    ("CAPS COMPANY OVERVIEW",   r"\bCOMPANY\s+OVERVIEW\b", 0),
    ("CAPS PRODUCTS SERVICES",  r"\b(?:PRODUCTS\s+AND\s+SERVICES|OUR\s+PRODUCTS)\b", 0),
    ("CAPS MANUFACTURING",      r"\bMANUFACTURING\s+(?:AND|OPERATIONS|FACILITIES|STRATEGY)\b", 0),
    ("CAPS CUSTOMERS",          r"\b(?:OUR\s+CUSTOMERS|MAJOR\s+CUSTOMERS|CUSTOMER\s+CONCENTRATION)\b", 0),
    ("CAPS INTELLECTUAL PROP",  r"\b(?:INTELLECTUAL\s+PROPERTY|PATENTS\s+AND\s+PROPRIETARY)\b", 0),
    ("CAPS GOVT REGULATION",    r"\bGOVERNMENT\s+REGULATION\b", 0),
    ("CAPS COMPETITION",        r"\bCOMPETITION\s+(?:AND|FROM|IN\s+OUR)\b", 0),
    # S-1 / F-1 prospectus summary — typically "Prospectus Summary" or
    # "Summary of the Offering" near the front of the doc, followed by
    # company description ("Our Company"). For the SECTION header version we
    # require it followed by typical body content (Hyzon, Lordstown, etc).
    ("PROSPECTUS SUMMARY",      r"\bProspectus\s+Summary\b", re.IGNORECASE),
    ("OUR COMPANY",             r"\bOur\s+Company\b\s*\.?\s*[A-Z]", re.IGNORECASE),
    ("OUR MISSION",             r"\bOur\s+Mission\b", re.IGNORECASE),
    ("THE COMPANY",             r"\bThe\s+Company\b\s*\n?\s*[A-Z][a-z]+\s+(?:is|was|provides|develops|manufactures|operates)\b", re.IGNORECASE),
    # Financial-statement-notes subsections. These contain disclosures that
    # don't surface in the Business section — issuer concessions to vendors,
    # related-party transactions, going-concern flags, contingent liabilities.
    # The Surf Air / Palantir stock-for-services arrangement was buried in
    # Commitments and Contingencies (Note 15) and therefore invisible to the
    # earlier slicer that only weighted Business-section narratives.
    ("COMMITMENTS CONTINGENCIES", r"\b(?:Commitments\s+and\s+Contingencies|COMMITMENTS\s+AND\s+CONTINGENCIES)\b", 0),
    ("RELATED PARTY TRANS",     r"\b(?:Related[\s\-]Party\s+Transactions?|RELATED[\s\-]PARTY\s+TRANSACTIONS?)\b", 0),
    ("GOING CONCERN",           r"\b(?:Going\s+Concern|GOING\s+CONCERN|substantial\s+doubt\s+about\s+(?:our|the\s+Company['’]s)\s+ability\s+to\s+continue)\b", 0),
    ("LIQUIDITY CAPITAL",       r"\b(?:Liquidity\s+and\s+Capital\s+Resources|LIQUIDITY\s+AND\s+CAPITAL\s+RESOURCES)\b", 0),
    ("SUBSEQUENT EVENTS",       r"\b(?:Subsequent\s+Events|SUBSEQUENT\s+EVENTS)\b", 0),
    ("NOTES TO FINANCIALS",     r"\b(?:Notes\s+to\s+(?:the\s+)?(?:Consolidated\s+)?Financial\s+Statements|NOTES\s+TO\s+(?:THE\s+)?(?:CONSOLIDATED\s+)?FINANCIAL\s+STATEMENTS)\b", 0),
]


def _find_section_starts(text: str) -> list[tuple[str, int]]:
    """Return [(name, char_offset), ...] sorted by offset.

    Heuristic: a real section header typically has ≥5KB of substantive text
    immediately after it (not TOC-shaped, not an inline 'see also' reference).
    For each pattern, prefer the LATEST occurrence whose next 200 chars look
    substantive (not just '<title> 132' style page-number references).
    """
    hits: list[tuple[str, int]] = []
    for name, pat, flags in SECTION_PATTERNS:
        matches = list(re.finditer(pat, text, flags=flags))
        if not matches:
            continue
        # Walk matches from latest to earliest; pick the first that "looks like
        # a section header" (next chars don't start with a 1-3 digit page num).
        chosen = None
        for m in reversed(matches):
            after = text[m.end() : m.end() + 80].lstrip()
            # TOC entries look like "Section Name 132" — page number within
            # first 80 chars after the header. Skip those.
            if re.match(r"^\d{1,4}\b", after):
                continue
            # Inline back-references look like '" Section Name " above' — skip
            if re.search(r"^\s*['\"”]", text[m.end() : m.end() + 5]):
                continue
            chosen = m
            break
        if chosen is None:
            chosen = matches[-1]
        hits.append((name, chosen.start()))
    hits.sort(key=lambda x: x[1])
    return hits


# Sections weighted higher get more of the budget. BUSINESS OF COMPANY and
# COMPANYS BUSINESS are typically where forward-looking discriminative claims
# live; they get 2-3x the share. Financial-statement-footnote sections (CAPS
# DESCRIPTION OF BUS, INFORMATION ABOUT when followed by accounting boilerplate)
# get less.
SECTION_WEIGHTS = {
    "BUSINESS OF COMPANY": 4.0,
    "COMPANYS BUSINESS": 4.0,
    "ITEM 1. BUSINESS": 4.0,
    "ITEM 1A. RISK FACTORS": 2.5,  # risk factors often contain quantified concerns
    "REASONS FOR MERGER": 2.0,
    "BACKGROUND OF MERGER": 1.5,
    "INFORMATION ABOUT": 1.0,
    "CAPS DESCRIPTION OF BUS": 0.5,  # often financial-statements footnote
    "ITEM 7. MD&A": 1.5,
    "ITEM 2. PROPERTIES": 1.5,
    # Financial-statement-notes subsections — high signal for issuer
    # concessions, related-party deals, distress disclosures.
    "GOING CONCERN":           3.0,
    "COMMITMENTS CONTINGENCIES": 2.5,
    "RELATED PARTY TRANS":     2.5,
    "LIQUIDITY CAPITAL":       2.0,
    "SUBSEQUENT EVENTS":       1.5,
    "NOTES TO FINANCIALS":     1.5,
}
DEFAULT_SECTION_WEIGHT = 1.0


def slice_filing(text: str, budget_chars: int = 120_000) -> str:
    """Return a concatenated slice of section content up to budget_chars.

    Strategy:
    1. Strip HTML.
    2. Find section starts. Allocate budget WEIGHTED by section type so the
       most discriminative sections (BUSINESS OF COMPANY, RISK FACTORS) get
       larger slices than financial-statement footnotes.
    3. If no sections found, take a centered slice (skip first 20% cover material).
    """
    text = strip_html(text)
    sections = _find_section_starts(text)

    if not sections:
        n = len(text)
        skip = int(n * 0.20)
        return text[skip : skip + budget_chars]

    weights = [SECTION_WEIGHTS.get(name, DEFAULT_SECTION_WEIGHT) for name, _ in sections]
    total_w = sum(weights)
    # Per-section char budgets (proportional to weight, min 5K each)
    budgets: list[int] = []
    for w in weights:
        b = int(budget_chars * (w / total_w))
        budgets.append(max(b, 5_000))

    # If total > budget after the min-5K floor, scale down proportionally
    if sum(budgets) > budget_chars:
        scale = budget_chars / sum(budgets)
        budgets = [int(b * scale) for b in budgets]

    # Concatenate sections with markers
    parts: list[str] = []
    used = 0
    for i, ((name, start), per) in enumerate(zip(sections, budgets)):
        end = sections[i + 1][1] if i + 1 < len(sections) else len(text)
        section_text = text[start : min(start + per, end)]
        marker = f"\n\n=== {name} ===\n"
        if used + len(marker) + len(section_text) > budget_chars:
            section_text = section_text[: budget_chars - used - len(marker)]
        parts.append(marker)
        parts.append(section_text)
        used += len(marker) + len(section_text)
        if used >= budget_chars:
            break

    return "".join(parts)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    if len(sys.argv) < 2:
        print("usage: filing_slice.py <filing.txt>", file=sys.stderr)
        sys.exit(1)
    text = Path(sys.argv[1]).read_text(errors="ignore")
    sliced = slice_filing(text)
    print(f"in: {len(text):,} chars  out: {len(sliced):,} chars", file=sys.stderr)
    sects = _find_section_starts(strip_html(text))
    print(f"sections found: {len(sects)}", file=sys.stderr)
    for name, off in sects[:20]:
        print(f"  @{off:>9,}  {name}", file=sys.stderr)
    print(sliced[:2000])
