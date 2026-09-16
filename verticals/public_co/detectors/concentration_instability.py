"""Customer-concentration instability detector — the "embedded ≠ irreplaceable" tell.

WHAT IT DOES
------------
Fires ELEVATE when an issuer's latest 10-K/10-Q discloses BOTH:

  (1) CONCENTRATION — a single customer (or named top-N) representing more than
      ~10% of total revenue, AND
  (2) INSTABILITY — that concentrated relationship is on shaky contractual ground:
      a short-term / month-to-month extension, an expired-and-unrenewed contract,
      or active renewal negotiations.

The CONCENTRATION half alone is honestly disclosed and fully priced — re-detecting
it is the SRPT non-alpha. The signal is the *pairing*: a load-bearing customer that
the same filing reveals is NOT contractually locked in, against a management
narrative of a "sticky / embedded / recurring / high-switching-cost" moat. That gap
— qualitative stickiness claim vs. quantitative terminable-and-being-renegotiated
reality — is the masking tell. Embedded ≠ irreplaceable.

TRAINING EXAMPLE (the blind that calibrated this)
-------------------------------------------------
Verra Mobility (VRRM), 10-Q filed 2026-05-06 — 20 days BEFORE Avis terminated its
~13%-of-revenue toll-management contract (stock -70%):

  "Commercial Services Customer Contracts — We are currently operating under a
   short-term contract extension and are engaged in contract negotiations with one
   of our significant Commercial Services customers which represented over 10% of
   our total revenue ..."

A blinded screen reading that single sentence fires CONCENTRATION (>10% customer) ×
INSTABILITY (short-term extension + renewal negotiations) → ELEVATE. The market saw
the same 10-Q and left the stock at ~$13; the detector's edge is WEIGHTING the
disclosed instability the consensus shrugged off — not predicting the trigger.

HONESTY-NEUTRAL / PRECISION NOTE
--------------------------------
This is an ELEVATE (risk-weighting), NOT an EXCLUDE. The concentration is disclosed,
so it carries no manufactured severity. Most customers on an extension DO renew, so
the fire's PRECISION on "predict a loss" is low (high recall, moderate precision):
its value is sizing/hedging the concentration and watching the renewal, not calling
the termination. Treat a fire as "size for a customer loss," never "this will crash."

FUTURE / SIBLING DETECTORS
--------------------------
- contractual_lockin_audit: parse the customer-contract section for minimum-volume,
  exclusivity, non-compete, or termination-penalty provisions. Their ABSENCE on a
  >10% customer is the contractual confirmation that the stickiness is narrative; it
  would upgrade ELEVATE → STRONG_ELEVATE and is the proper Mode-B verifier.
- guidance_reaffirmation_proximity: cross-check a guidance reaffirmation date against
  any subsequently-disclosed material customer loss (the VRRM May-6-reaffirm /
  May-26-terminate gap that drew the securities probes) — a disclosure-integrity
  EXCLUDE, distinct from this risk-weighting ELEVATE.
- renewal_cliff_calendar: extract named contract-expiry/renewal dates for each >10%
  customer to build a forward concentration-cliff timeline (the VRRM Hertz-Q2'27 /
  Enterprise-Q4'27 overhang).
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Optional

from ..edgar import (fetch_filing_text, list_filings, HEADERS,
                     html_to_clean_text, fetch_filing_clean, latest_filing)

# A customer representing more than ~10% of revenue (capture the % when present).
# Handles a RUN of percents so multi-year lists ("71%, 69% and 70% of net revenue")
# and verb variants ("generated 72% ... of net revenue from", "derived 24% of revenue")
# are all caught, not just the single-percent "represented 28% of revenue" form.
_CONC_RUN_RE = re.compile(
    r"(?:represent\w*|account\w*|compris\w*|generat\w*|deriv\w*|exceed\w*|"
    r"more than|over|in excess of|greater than)\s+(?:for\s+|to\s+)?(?:approximately\s+|about\s+)?"
    r"((?:\d{1,2}(?:\.\d+)?\s*%(?:\s*(?:,\s*)?(?:and|or|to)?\s*)?)+)"  # run: "69%, 66%, and 58%"
    r"\s*(?:or more\s+)?of\s+(?:our\s+|its\s+|the\s+company'?s\s+)?"
    r"(?:total\s+|net\s+|consolidated\s+|combined\s+)?(?:revenue|revenues|net\s+revenue|sales)",
    re.I,
)
# Back-compat single-percent alias (some callers/tests reference _CONC_RE).
_CONC_RE = _CONC_RUN_RE
_PCT_TOKEN_RE = re.compile(r"(\d{1,2}(?:\.\d+)?)\s*%")
# Bare "more than/over 10%" phrasing without a captured number (e.g. VRRM's "over 10%").
_CONC_BARE_RE = re.compile(
    r"(?:more than|over|in excess of|exceed\w*|greater than|at least)\s+10\s*%\s+"
    r"(?:or more\s+)?of\s+(?:our|the\s+company'?s|its|total)?\s*(?:total\s+)?(?:revenue|revenues|sales)",
    re.I,
)
# Negation guard — "NO customer accounted for more than 10% of revenue" is the
# STANDARD *no-concentration* disclosure; it must NOT register as concentration.
_NEG_BEFORE_RE = re.compile(
    r"(?:no\s+(?:single\s+)?(?:one\s+)?(?:customer|client|individual)|"
    r"not\s+|none\s+of|did\s+not|fewer\s+than|less\s+than|nor\s+did)\b", re.I)


def _is_negated(text: str, start: int) -> bool:
    """True when the concentration phrase is a negated/no-concentration statement."""
    return bool(_NEG_BEFORE_RE.search(text[max(0, start - 48):start]))


# A revenue % only counts as CUSTOMER concentration if a customer/client token sits
# near it — otherwise a segment / geographic / product-line / gross-margin percentage
# ("Government Solutions ... 95.4% of segment revenue") would inflate the reading.
_CUST_CTX_RE = re.compile(r"\b(?:customer|client)s?\b|\b[A-Z][a-zA-Z]+\s+Inc\.?")
# Segment / geographic / product-line / margin percentages are NOT customer concentration.
_SEG_ANTI_RE = re.compile(
    r"segment|geograph|\bregion|product\s+line|product\s+categor|each\s+product|"
    r"by\s+product|gross\s+margin|gross\s+profit|operating\s+margin", re.I)
# A company-level denominator (total/net/consolidated revenue) — as opposed to "of
# segment revenue" — is itself a concentration signal even when the customer name sits
# far from the % behind a long appositive (e.g. SWKS Note 14 "Apple … accounted for 69 %
# … of the Company's net revenue").
_TOTAL_DENOM_RE = re.compile(r"(?:total|net|consolidated)\s+(?:revenue|sales)", re.I)


def _has_customer_ctx(text: str, start: int, end: int) -> bool:
    window = text[max(0, start - 110):end + 50]
    if _CUST_CTX_RE.search(window):
        return True
    # company-level denominator with NO segment/product/margin anti-context = customer conc
    return bool(_TOTAL_DENOM_RE.search(text[start:end + 30]) and not _SEG_ANTI_RE.search(window))
# The instability markers — a concentrated relationship NOT locked in.
_INSTABILITY_PATTERNS = {
    "short_term_extension": re.compile(
        r"(?:short[\-\s]?term|month[\-\s]?to[\-\s]?month|interim|temporary)\s+"
        r"(?:contract\s+)?extension", re.I),
    "operating_under_extension": re.compile(
        r"operating\s+under\s+(?:a|an|the)?\s*(?:short[\-\s]?term\s+)?(?:contract\s+)?extension", re.I),
    "renewal_negotiations": re.compile(
        r"(?:engaged\s+in|currently|are\s+in|ongoing)\s+(?:contract\s+|renewal\s+)?negotiation", re.I),
    "negotiating_renewal": re.compile(
        r"negotiat\w*\s+(?:a|an|the|its)?\s*(?:contract\s+)?renewal", re.I),
    "expired_unrenewed": re.compile(
        r"contract\s+(?:that\s+|which\s+|has\s+)?expired", re.I),
    "renewal_negotiations2": re.compile(r"renewal\s+negotiation", re.I),
}
# The qualitative moat narrative the instability contradicts (Mode-B strengthener).
_STICKINESS_RE = re.compile(
    r"\b(?:embedded|deeply\s+integrated|sticky|high\s+switching\s+cost|"
    r"long[\-\s]term\s+relationship|recurring\s+(?:revenue|service))\b", re.I)

SETS_FEATURE = "customer_concentration_instability"

APPLIES_TO = {
    "asset_classes": [
        "corporate_ipo_dd", "public_co_defense", "public_co_space",
        "public_co_quantum", "public_co_nuclear", "diagnostics_biotech_dd",
        "public_equity",
    ],
    # Cheap + self-gating: classify() returns NO_CONCENTRATION when no >10% customer
    # is disclosed, so the brain always considers it and the matcher is the filter
    # (same pattern as insider_share_pledge).
    "applies_universally": True,
    "issuer_features": [SETS_FEATURE],
    "sets_feature": SETS_FEATURE,
    "kind": "detector",
    "summary": (
        "Detect a >10%-of-revenue customer whose relationship the same 10-K/10-Q "
        "reveals as unstable (short-term extension / expired contract / active "
        "renewal negotiations) against a 'sticky/embedded moat' narrative — the "
        "'embedded != irreplaceable' concentration-instability tell. ELEVATE."),
    "verification_question": (
        "Does the issuer disclose a customer representing >10% of revenue (R, "
        "10-K/10-Q concentration note) whose contract is on a short-term extension "
        "or in active renewal — i.e. NOT contractually locked in despite a "
        "stickiness narrative (M, customer-contracts subsection)?"),
}


def classify(text: str, records: Optional[list[dict]] = None) -> dict[str, Any]:
    """Pure text classifier — no I/O. Returns the concentration %, the instability
    markers found, the stickiness-narrative flag, and the fire decision. `records` are
    structured concentration facts from sec_tables (table + qualitative); when None they
    are derived from `text` so table-disclosed and sole-customer concentration the prose
    regex can't see still register."""
    if not text:
        return {"category": "NO_TEXT", "fires": False}
    # Normalize inline-XBRL typography: curly apostrophes (Company’s) and unicode
    # spaces break literal-apostrophe / \s patterns — fold them to ASCII first.
    text = text.replace("’", "'").replace("‘", "'").replace(" ", " ")
    # Concentration: highest disclosed customer % >= 10, or the bare "over 10%" form.
    # Skip NEGATED phrasings ("no customer accounted for more than 10% of revenue").
    pcts: list[float] = []
    for m in _CONC_RUN_RE.finditer(text):
        if _is_negated(text, m.start()) or not _has_customer_ctx(text, m.start(), m.end()):
            continue
        pcts.extend(float(p) for p in _PCT_TOKEN_RE.findall(m.group(1)))
    big = [p for p in pcts if p >= 10.0]
    bare = any(not _is_negated(text, m.start()) and _has_customer_ctx(text, m.start(), m.end())
               for m in _CONC_BARE_RE.finditer(text))
    # structured records from the generic table + qualitative ingestor (sec_tables).
    # Revenue records with >=10% join `big`; a qualitative sole-customer record sets
    # concentration on its own; accounts-receivable records do NOT count (wrong denom).
    if records is None:
        try:
            from ..sec_tables import extract_concentration_records
            records = extract_concentration_records(text)
        except Exception:
            records = []
    rev_recs = [r for r in records if r.get("pct") and r["pct"] >= 10.0
                and "receivable" not in (r.get("denominator") or "")]
    qual = any(r.get("source") == "qualitative" for r in records)
    big += [r["pct"] for r in rev_recs]
    has_conc = bool(big) or bare or qual
    top_pct = max(big) if big else (10.0 if (bare or qual) else None)
    # crude count of distinct >10% customer mentions (e.g. "three customers ... 10%")
    n_word = re.search(r"\b(two|three|four|five)\s+(?:of\s+(?:our|its)\s+)?(?:significant\s+|largest\s+)?"
                       r"customers?\b[^.]{0,80}?10\s*%", text, re.I)
    n_concentrated = {"two": 2, "three": 3, "four": 4, "five": 5}.get(
        (n_word.group(1).lower() if n_word else ""), 1 if has_conc else 0)

    markers = sorted(k for k, rx in _INSTABILITY_PATTERNS.items() if rx.search(text))
    has_instab = bool(markers)
    has_stickiness = bool(_STICKINESS_RE.search(text))

    fires = has_conc and has_instab
    cat = ("CONCENTRATION_INSTABILITY" if fires
           else "CONCENTRATION_STABLE" if (has_conc and not has_instab)
           else "NO_CONCENTRATION")
    return {
        "category": cat, "fires": fires,
        # top_customer_pct is the largest CUSTOMER-context revenue % detected; it can be
        # segment-relative, so when the at-risk customer is only disclosed via the bare
        # ">10%" form we report the conservative floor and keep this as evidence.
        "top_customer_pct": top_pct, "bare_present": bare,
        "qualitative_sole_customer": qual,
        "concentration_records": rev_recs + [r for r in records if r.get("source") == "qualitative"],
        "n_concentrated_customers": n_concentrated,
        "instability_markers": markers, "stickiness_narrative": has_stickiness,
    }


# Clean-extract + doc-selection now live in the shared edgar module so EVERY SEC
# consumer inherits them (edgar.html_to_clean_text / fetch_filing_clean / latest_filing).
_html_to_text = html_to_clean_text          # back-compat alias for callers / harnesses
_fetch_clean_text = fetch_filing_clean       # back-compat alias


def _latest_filing_text(cik: str, data_dir: Optional[str], cutoff: Optional[str]) -> Optional[str]:
    """The MOST RECENT 10-K or 10-Q AS OF the cutoff (point-in-time seam), bs4-cleaned.
    Uses the shared edgar.latest_filing (most-recent-of-either-form, NOT prefer-10-Q) +
    edgar.fetch_filing_clean. Honours an on-disk cutoff-filtered corpus when provided."""
    ddir = Path(data_dir) if data_dir else None
    if ddir and (ddir / "filings_index.json").exists():
        rows = json.loads((ddir / "filings_index.json").read_text())
        if cutoff:
            rows = [r for r in rows if r["filing_date"] <= cutoff]
        cand = sorted((r for r in rows if r["form"] in ("10-K", "10-Q")),
                      key=lambda r: r["filing_date"], reverse=True)
        for r in cand[:4]:
            fsafe = r["form"].replace("/", "_").replace(" ", "_")
            local = ddir / "filings" / f"{r['accession']}_{fsafe}.txt"
            if local.exists():
                return local.read_text()
        return None
    r = latest_filing(cik, cutoff)
    if not r:
        return None
    return fetch_filing_clean(cik, r["accession"], r["primary_document"])


def evaluate(issuer_name: str, data: dict) -> dict[str, Any]:
    """Args (in `data`): filing_text (skips fetch), or cik [+ data_dir, cutoff] to
    pull the latest 10-Q/10-K as of the cutoff (pass cutoff=as_of in a backtest so
    nothing post-event leaks). Returns a fire/no-fire R/f(M) dict; on fire the signal
    is ELEVATE and `sets_feature` activates the contractual_lockin_audit sibling."""
    text = data.get("filing_text")
    cik = data.get("cik")
    if not text and cik:
        text = _latest_filing_text(cik, data.get("data_dir"), data.get("cutoff"))
    if not text:
        return {"fires": False, "reason": "NO_10K_OR_10Q_TEXT", "sets_feature": None, "evidence": {}}

    c = classify(text)
    if not c["fires"]:
        return {"fires": False, "reason": c["category"], "sets_feature": None,
                "evidence": {k: c.get(k) for k in ("top_customer_pct", "instability_markers")}}

    pct = c["top_customer_pct"]
    n = c["n_concentrated_customers"]
    # When the at-risk customer is disclosed via the bare ">10%" form, headline the
    # conservative floor — a higher run-captured % may be a different (segment-level)
    # customer and would overstate the at-risk concentration.
    pct_s = (">10%" if c.get("bare_present") else f"~{pct:.0f}%" if pct and pct > 10 else ">10%")
    # Name the customer when the structured ingestor resolved one (skip generic codes).
    recs = c.get("concentration_records") or []
    ent = next((r["entity"] for r in recs
                if r.get("entity") and len(r["entity"]) > 3
                and r["entity"].lower() not in ("a customer", "a single customer")), None)
    ent_s = f" ({ent})" if ent else ""
    if c.get("qualitative_sole_customer") and not c.get("bare_present") and not (pct and pct > 10):
        conc = f"its sole disclosed customer{ent_s}"
        conc_short = "a sole-source customer"
    else:
        conc = (f"{('a' if n <= 1 else str(n))} customer{'s' if n > 1 else ''}{ent_s} "
                f"at {pct_s} of revenue")
        conc_short = f"a {pct_s} customer"
    finding = {
        "R": (f"{issuer_name} discloses {conc} whose relationship the same filing shows "
              f"as UNSTABLE ({', '.join(c['instability_markers'])})"
              + (" — against a 'sticky/embedded' moat narrative" if c["stickiness_narrative"] else "")
              + "."),
        "f": ("Pair the concentration disclosure (>10% / sole customer, from the revenue "
              "note, customer-table, or 'one end customer' statement) with the customer-"
              "contract subsection: a short-term extension / expired contract / active "
              "renewal on a load-bearing customer = NOT contractually locked in."),
        "M": ("SEC EDGAR 10-Q/10-K — revenue-concentration note / customer-concentration "
              "table + 'Customer Contracts' subsection; contractual_lockin_audit (sibling) "
              "confirms absence of minimum-volume / exclusivity / termination-penalty lock-in."),
        "Finding": (f"CONCENTRATION-INSTABILITY — {conc_short} is terminable / "
                    f"being renegotiated. ELEVATE (size for a customer loss; watch the "
                    f"renewal). NOT a prediction of loss."),
    }
    return {
        "fires": True,
        "reason": "CONCENTRATION_INSTABILITY_ELEVATE",
        "signal": "ELEVATE",
        "sets_feature": SETS_FEATURE,
        "activates": ["contractual_lockin_audit", "renewal_cliff_calendar"],
        "top_customer_pct": pct,
        "n_concentrated_customers": n,
        "instability_markers": c["instability_markers"],
        "stickiness_narrative": c["stickiness_narrative"],
        "evidence": c,
        "finding": finding,
    }
