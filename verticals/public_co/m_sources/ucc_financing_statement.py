"""State UCC-1/UCC-3 financing-statement M-source — DEBTOR-NAME keyed.

WHY THIS EXISTS (and why ucc_proxy does NOT cover it)
-----------------------------------------------------
`ucc_proxy` is CIK-keyed and rides SEC disclosure: it counts 8-K Item 2.03
("Creation of a Direct Financial Obligation") and secured-debt language in the
*issuer's own* filings. That structurally cannot see the case this source is
built for: an INSIDER's PERSONAL loan secured by a pledge of company stock.

Canonical case (Caris / CAI, 2026-05): founder David Halbert pledged 25,000,000
shares via "Halbert Family Capital, LLC" against personal debt (DEF 14A beneficial-
ownership footnote). That pledge is NOT a Caris obligation — no 8-K fires, no
issuer Note discloses it, so ucc_proxy returns LOW_LIEN_EXPOSURE while a real
forced-sale channel (~8.8% of shares out) sits off the issuer's balance sheet.
The lender perfects that security interest by filing a UCC-1 at the STATE level
against the DEBTOR (the LLC / the individual) — not against the issuer's CIK.

THE R/f(M) THIS ANSWERS
-----------------------
R: "Halbert's 25M-share pledge is/ isn't underwater / has/ hasn't been topped up."
The pledge MAGNITUDE is verified (DEF 14A); the LOAN PRINCIPAL and COVENANT are
not in any SEC registry, so the "underwater" claim is UNVERIFIABLE from filings.
The UCC record is the highest-leverage external M:
  - UCC-1  → existence + DATE the security interest was perfected (anchors the
             pledge to a share price → bounds the original LTV).
  - UCC-3  → amendments (added collateral = the top-up signal; the 1.66M→25M jump).
  - secured-party name → identifies the lender (a margin desk vs a related party).
It does NOT state the loan principal — so even a clean pull leaves "underwater"
conditional. This source returns the pull + the conditional, never a fabricated
severity.

ACCESS REALITY (this is the dominant constraint, not the code)
--------------------------------------------------------------
UCC filings are public record, so there is NO legal-authorization barrier — the
gate is commercial/technical and STATE-BY-STATE:
  - DE  : Division of Corporations has NO public online UCC index. Paid order
          only (UCC-11 search request, ~$20-75) via DOS or a commercial agent.
  - TX  : SOSDirect — free account, but each search ~$1 + per-image page fees.
  - CA  : bizfileOnline UCC search is free online (Cloudflare-walled to bots).
  - FL  : Sunbiz UCC search is free online.
  - NY  : free online via DOS.
  - NV  : SilverFlume, free online.
There is no free national UCC API. A production multi-state capability means a
PAID B2B aggregator (CSC, Wolters Kluwer Lien Solutions, First Corporate
Solutions / iLien) under a subscriber agreement + permissible-use attestation.

So this V1 is GRACEFUL-DEGRADATION by design:
  Tier 0 (always, no creds): resolve the correct filing jurisdiction per UCC
          Article 9 §9-307, emit a structured `manual_pull` instruction (which
          office, what it costs, what to search), and return UNVERIFIABLE with
          the conditional LTV note. Useful with zero access.
  Tier 1 (where a free state portal exists and isn't bot-walled): attempt fetch.
  Tier 2 (commercial aggregator): used only if ~/.ucc_api_key is present.
"""
from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["insider_share_pledge", "founder_controlled_single_class"],
    "asset_classes": ["corporate_ipo_dd", "public_co_defense", "public_co_space",
                      "public_co_quantum", "diagnostics_biotech_dd"],
    "applies_universally": False,
    "must_have_feature": "insider_share_pledge",
    "kind": "m_source",
    "summary": ("State UCC-1/UCC-3 financing-statement lookup keyed on the DEBTOR "
                "(pledging insider/affiliate), not the issuer CIK — covers the "
                "off-balance-sheet founder-pledge forced-sale channel ucc_proxy "
                "cannot see."),
    "verification_question": ("If an insider pledged company stock against personal "
                              "debt (R, from DEF 14A), does a UCC-1 perfect that "
                              "interest (M, state SOS), when was it dated, and do "
                              "UCC-3 amendments show collateral top-ups?"),
}

import json
import os
from pathlib import Path
from typing import Any, Optional

# State SOS UCC-search access map. `access` drives whether Tier 1 can even try.
#   FREE_ONLINE     — searchable free on a public web portal (often bot-walled)
#   ACCOUNT_REQUIRED— free/cheap but needs a registered account + per-search fee
#   PAID_ORDER_ONLY — no public online index; must order a paid UCC-11 search
STATE_UCC_ACCESS = {
    "DE": {"office": "Delaware Division of Corporations (UCC Section)",
           "access": "PAID_ORDER_ONLY",
           "search_url": "https://corp.delaware.gov/ucc/",
           "cost": "UCC-11 search request ~$20-75; no public online index",
           "note": "Most LLCs/Corps are DE-formed → this is usually the controlling jurisdiction for a registered-org debtor."},
    "TX": {"office": "Texas Secretary of State (SOSDirect)",
           "access": "ACCOUNT_REQUIRED",
           "search_url": "https://www.sos.state.tx.us/ucc/index.shtml",
           "cost": "free SOSDirect account; ~$1/search + per-page image fees"},
    "CA": {"office": "California Secretary of State (bizfileOnline)",
           "access": "FREE_ONLINE",
           "search_url": "https://bizfileonline.sos.ca.gov/search/ucc",
           "cost": "free online (Cloudflare bot-walled — manual/browser pull)"},
    "FL": {"office": "Florida Secured Transaction Registry (Sunbiz)",
           "access": "FREE_ONLINE",
           "search_url": "https://www.floridaucc.com/uccweb/",
           "cost": "free online debtor search"},
    "NY": {"office": "New York Department of State (UCC)",
           "access": "FREE_ONLINE",
           "search_url": "https://appext20.dos.ny.gov/pls/ucc_public/web_search.main_frame",
           "cost": "free online"},
    "NV": {"office": "Nevada Secretary of State (SilverFlume)",
           "access": "FREE_ONLINE",
           "search_url": "https://www.nvsilverflume.gov/ucc",
           "cost": "free online"},
}
_DEFAULT_ACCESS = {"office": "<state> Secretary of State UCC office",
                   "access": "UNKNOWN",
                   "search_url": "",
                   "cost": "verify the state's UCC search availability + fee schedule"}

_AGG_KEY_PATH = Path.home() / ".ucc_api_key"


def _jurisdiction(debtor_type: str,
                  state_of_formation: Optional[str],
                  state_of_residence: Optional[str]) -> tuple[Optional[str], str]:
    """UCC Article 9 §9-307 governing-jurisdiction rule.

    Registered organization (LLC / corp / LP): file in the STATE OF FORMATION.
    Individual: file in the state of the debtor's PRINCIPAL RESIDENCE.
    Returns (state_code, rationale).
    """
    t = (debtor_type or "").lower()
    if t in ("registered_org", "llc", "corp", "corporation", "lp", "organization"):
        st = (state_of_formation or "").upper()[:2] or None
        return st, ("§9-307(e): a registered organization is located in its state "
                    "of formation; the UCC-1 must be filed there.")
    if t in ("individual", "person", "natural_person"):
        st = (state_of_residence or "").upper()[:2] or None
        return st, ("§9-307(b): an individual debtor is located at their principal "
                    "residence; the UCC-1 must be filed there.")
    return None, ("debtor_type unspecified — cannot resolve §9-307 jurisdiction. "
                  "Pass debtor_type='registered_org' (with state_of_formation) for "
                  "an LLC/corp, or 'individual' (with state_of_residence).")


def _manual_pull(state: Optional[str], debtor_name: str, rationale: str) -> dict:
    acc = STATE_UCC_ACCESS.get((state or "").upper(), {**_DEFAULT_ACCESS})
    return {
        "jurisdiction_state": state,
        "jurisdiction_rationale": rationale,
        "office": acc["office"].replace("<state>", state or "<state>"),
        "access_tier": acc["access"],
        "search_url": acc["search_url"],
        "cost": acc["cost"],
        "search_instructions": (
            f"Run a DEBTOR-name search for '{debtor_name}' (and close variants — "
            f"trailing 'LLC'/'L.L.C.', the bare surname for an individual). "
            f"Pull the UCC-1 (initial, dates + bounds the original LTV via the "
            f"share price on the filing date), the SECURED-PARTY name (identifies "
            f"the lender), the COLLATERAL description, and ALL UCC-3 amendments "
            f"(added collateral = the top-up signal)."
        ),
        "note": acc.get("note", ""),
    }


def _aggregator_query(debtor_name: str, state: Optional[str],
                      secured_party: Optional[str], as_of_date: Optional[str]) -> Optional[dict]:
    """Tier 2: commercial multi-state UCC aggregator. Active only if a key file
    exists at ~/.ucc_api_key. Vendor-specific request wiring is intentionally a
    stub — drop in the CSC / Lien Solutions / iLien client when a contract exists."""
    if not _AGG_KEY_PATH.exists():
        return None
    # Placeholder for the paid-aggregator client. Returning a structured
    # not-implemented keeps the contract honest rather than faking a hit.
    return {
        "_tier": 2,
        "signal": "AGGREGATOR_KEY_PRESENT_CLIENT_NOT_WIRED",
        "_note": (f"Found {_AGG_KEY_PATH}; a commercial UCC-aggregator subscription "
                  "appears configured but the vendor client is not wired in this "
                  "build. Implement the request against your subscriber endpoint."),
    }


def query_ucc_filings(
    debtor_name: str,
    debtor_type: Optional[str] = None,
    state_of_formation: Optional[str] = None,
    state_of_residence: Optional[str] = None,
    secured_party: Optional[str] = None,
    as_of_date: Optional[str] = None,
) -> dict[str, Any]:
    """Look up state UCC-1/UCC-3 financing statements against a DEBTOR.

    Args:
      debtor_name: the pledging entity/person, EXACTLY as it would be on the
                   financing statement (e.g. 'Halbert Family Capital, LLC').
      debtor_type: 'registered_org' (LLC/corp/LP) or 'individual'.
      state_of_formation: 2-letter state — required for a registered org (§9-307).
      state_of_residence: 2-letter state — required for an individual (§9-307).
      secured_party: optional lender name to filter/confirm.
      as_of_date: ISO YYYY-MM-DD — backtest upper bound (informational in V1).

    Returns (V1 — Tier 0 always; Tier 2 if key present):
      {
        "debtor_name", "jurisdiction_state", "jurisdiction_rationale",
        "manual_pull": {...office/url/cost/instructions...},
        "signal": one of
            UNVERIFIABLE_NO_ADAPTER       — no auto-pull; manual_pull emitted (Tier 0)
            UNVERIFIABLE_JURISDICTION      — could not resolve §9-307 state
            AGGREGATOR_KEY_PRESENT_*       — Tier 2 path (see _note)
            FILINGS_FOUND / NO_FILINGS     — reserved for Tier 1/2 once live,
        "conditional_note": the standing R/f(M) caveat for the 'underwater' claim,
      }

    Severity mapping for the deterministic scorer:
      UNVERIFIABLE_*                 → UNVERIFIABLE (never a manufactured severity)
      FILINGS_FOUND + UCC-3 top-up   → MODERATE  (collateral added → larger/again-
                                                   levered loan; forced-sale channel grew)
      NO_FILINGS (only if a real registry was searched) → PASS-leaning, but a
                                                   pledge can be perfected privately
                                                   in some structures → treat as weak.
    """
    state, rationale = _jurisdiction(debtor_type, state_of_formation, state_of_residence)

    conditional = (
        "The UCC record dates and bounds the pledge but does NOT state the loan "
        "principal or maintenance covenant. 'Underwater' therefore stays "
        "CONDITIONAL: it requires (a) shares pledged [DEF 14A: verified], "
        "(b) market value [tape: verified], (c) loan principal [NO public M], "
        "(d) maintenance LTV [NO public M]. Report c/d as unverifiable; do not "
        "convert into a severity score."
    )

    # Tier 2 first (a paid subscription, if present, is authoritative & multi-state).
    if state:
        agg = _aggregator_query(debtor_name, state, secured_party, as_of_date)
        if agg is not None:
            agg.update({"debtor_name": debtor_name, "jurisdiction_state": state,
                        "jurisdiction_rationale": rationale,
                        "conditional_note": conditional})
            return agg

    if not state:
        return {
            "debtor_name": debtor_name,
            "jurisdiction_state": None,
            "jurisdiction_rationale": rationale,
            "manual_pull": None,
            "signal": "UNVERIFIABLE_JURISDICTION",
            "conditional_note": conditional,
            "_note": rationale,
        }

    return {
        "debtor_name": debtor_name,
        "jurisdiction_state": state,
        "jurisdiction_rationale": rationale,
        "manual_pull": _manual_pull(state, debtor_name, rationale),
        "secured_party_filter": secured_party,
        "as_of_date": as_of_date,
        "signal": "UNVERIFIABLE_NO_ADAPTER",
        "conditional_note": conditional,
        "_note": ("Tier 0 (no UCC adapter/credentials wired). The correct filing "
                  "jurisdiction is resolved and a manual-pull instruction is "
                  "emitted. Add a free-state adapter (CA/FL/NY/NV) or a commercial "
                  "aggregator key (~/.ucc_api_key) to upgrade to an automated pull."),
    }


if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "Halbert Family Capital, LLC"
    # Default demo: a DE-formed family-capital LLC (the CAI pledge debtor).
    print(json.dumps(
        query_ucc_filings(name, debtor_type="registered_org",
                          state_of_formation="DE",
                          secured_party=None, as_of_date="2026-05-29"),
        indent=2, default=str))
