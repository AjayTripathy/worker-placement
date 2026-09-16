"""
Deterministic Phase-2 scorer.

For the proof-of-concept fintech run, the LLM scorer subagents repeatedly
stalled at the framework's 600s watchdog even though the data they needed
was tiny and pre-computed. This module replicates the *easy* part of the
scoring logic in pure Python so the architecture can be exercised
end-to-end without depending on an LLM session. The decisions it makes are
deliberately conservative; genuinely judgmental cases still need an LLM
revisit, but most fintech claims fall into one of a handful of mechanical
buckets:

  1. PROPOSED, connector-not-promoted          -> UNVERIFIABLE
  2. NONE / structural_none                    -> UNVERIFIABLE
  3. MAPPED + bad_kwargs / runtime error       -> UNVERIFIABLE
  4. MAPPED edgar_fts with 0 hits + counterparty CIK -> MODERATE_UNDERDELIVERY
  5. MAPPED edgar_fts with 0 hits otherwise    -> UNVERIFIABLE (coverage)
  6. MAPPED edgar_fts with >0 hits             -> PASS
  7. MAPPED uspto with 0 patents               -> UNVERIFIABLE (asymmetric)
  8. MAPPED fdic with summary                  -> PASS (existence + direction)
                                                  with credit-quality note

Heuristic 7 (counterparty-disclosure threshold) is the only non-trivial
emit pathway used here. The thresholds below are conservative — only
the strongest signals fire as MODERATE or stronger.

Usage:
    python3 -m verticals.public_co.deterministic_scorer TICKER [TICKER ...]

Writes data/_local/<TK>.scores.json for each ticker.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"


def _score_fdic(claim: dict, fdic_res: dict) -> tuple[str, str, str, bool]:
    """Score a claim adjudicated by FDIC Call Reports.

    Returns (severity, M_value_summary, interpretation, escalation_needed).
    Escalation is requested when the bank's credit-quality metrics are
    elevated relative to the filing's narrative tone (so an LLM pass can
    judge whether to upgrade PASS -> MODERATE/SEVERE)."""
    bank = (fdic_res.get("bank") or {}).get("bank_name") or "(unresolved)"
    cert = fdic_res.get("cert")
    s = fdic_res.get("summary") or {}
    co = s.get("charge_off_rate_pct")
    na = s.get("nonaccrual_rate_pct")
    yoy = s.get("consumer_loans_yoy_pct")
    m_value = f"{bank} (CERT {cert}): co={co}% na={na}% yoy={yoy}%"

    if not cert:
        return ("UNVERIFIABLE",
                m_value,
                f"FDIC institution lookup did not resolve a CERT for the named bank partner; not adjudicatable.",
                False)

    notes = []
    escalate = False
    if isinstance(co, (int, float)) and co > 3.0:
        notes.append(f"elevated bank-level charge-off rate {co}%")
        escalate = True
    if isinstance(na, (int, float)) and na > 3.0:
        notes.append(f"elevated nonaccrual rate {na}%")
        escalate = True
    if isinstance(yoy, (int, float)) and yoy > 30.0:
        notes.append(f"rapid book growth +{yoy}% YoY")
        # rapid growth alone doesn't escalate — paired with elevated rates it does
    note_str = "; ".join(notes) if notes else "Call Report consistent with claim"
    return ("PASS", m_value,
            f"Bank-partner identity + direction-of-book corroborated by Call Report. {note_str}.",
            escalate)


# Counterparty CIKs where Heuristic 7 (counterparty-disclosure threshold) is
# unsafe by default. These are mega-caps with huge revenue bases and broad
# customer-/vendor-ecosystems; they almost never name individual small-cap
# partners in their 10-K filings unless the relationship triggers a
# 10%-of-revenue customer-concentration disclosure or a formal material
# contract exhibit. Absence of mentions here is the expected baseline, not
# a disclosure gap. For these CIKs we soft-fail H7 to UNVERIFIABLE.
_MEGA_CAP_COUNTERPARTIES = {
    "1018724",   # Amazon (AWS as vendor; named partners only at concentration scale)
    "789019",    # Microsoft (Azure / Office / GitHub vendor relationships)
    "320193",    # Apple (App Store / hardware ecosystem)
    "1652044",   # Alphabet / Google (GCP / search / ads)
    "1326801",   # Meta Platforms (apps / WhatsApp / Reality Labs)
    "1045810",   # NVIDIA (GPU customer / partner network)
    "1341439",   # Oracle (Cloud / database customers)
    "1108524",   # Salesforce (CRM customer network)
    "51143",     # IBM (broad enterprise tech)
    "200406",    # JPMorgan Chase (banking customer set)
    "70858",     # Bank of America
    "1403161",   # Visa
    "1141391",   # Mastercard
    "1067983",   # Berkshire Hathaway
    "104169",    # Walmart (vendor of, customer of myriad small companies)
    "320187",    # Nike (vendor/customer network)
    "1018840",   # Cisco
    "1730168",   # T-Mobile US
    "732717",    # AT&T
    "732712",    # Verizon (legacy CIK form)
    "1594805",   # Shopify (millions of merchants — small ones unnamed)
    "1467373",   # Accenture
    # Major automakers — JDAs / supplier relationships rarely surface in 10-K
    # unless the partner is a Tier-1 OEM at scale. SES, MVST, etc. partnership
    # claims against these need a separate check.
    "1467858",   # General Motors
    "37996",     # Ford Motor
    "1318605",   # Tesla
    "1672688",   # Stellantis (was 0001672688; varies)
    # Big retail / consumer
    "70318",     # General Electric
    "354950",    # Home Depot
    "885639",    # Kroger
    # Big telecom / energy / etc.
    "34088",     # Exxon Mobil
    "1652044",   # Alphabet (already above; dup-safe via set)
}


def _score_edgar_fts(claim: dict, ed_res: dict, *, focal_cik: str | None = None) -> tuple[str, str, str, bool]:
    """Score a claim adjudicated by edgar_fts.query_fulltext.

    Heuristic 7 (counterparty-disclosure threshold) only fires as MODERATE when:
      (a) the search is against a counterparty's CIK (cik != focal_cik), AND
      (b) the counterparty is NOT a mega-cap whose customer/vendor base is too
          broad for selective small-cap disclosure (see _MEGA_CAP_COUNTERPARTIES).
    Zero hits against mega-cap counterparties is the expected baseline given
    materiality asymmetry — score UNVERIFIABLE instead.

    Zero hits against the focal company's own CIK is also UNVERIFIABLE
    (search-term mismatch is the likeliest explanation, not true absence).
    """
    hits = ed_res.get("total_hits", 0)
    search_term = ed_res.get("search_term", "")
    cik_raw = ed_res.get("cik") or ""
    cik = cik_raw.lstrip("0") or None
    fcik = (focal_cik or "").lstrip("0") or None
    m_value = f"edgar_fts: {hits} hits for {search_term!r} on cik={cik_raw}"

    if hits > 0:
        ctxt = (claim.get("claim_text") or "")
        wants_fact_check = any(tok in ctxt for tok in ["$", "million", "billion", "%", " on "]) and \
                           claim.get("category") in {"financial_distress", "production_volume", "regulatory_milestone"}
        return ("PASS", m_value,
                f"EDGAR fulltext returned {hits} filings matching the claim's terms within the cutoff window.",
                wants_fact_check)

    is_counterparty_search = bool(cik) and cik != fcik

    # Materiality gate: mega-cap counterparty + zero hits = expected baseline,
    # not a disclosure gap. Small-cap partnerships rarely make it into the
    # 10-Ks of $500B+ companies.
    if is_counterparty_search and cik in _MEGA_CAP_COUNTERPARTIES:
        return ("UNVERIFIABLE", m_value,
                f"EDGAR 0 hits but counterparty CIK {cik_raw} is a mega-cap whose customer/vendor "
                f"ecosystem is too broad for selective small-cap disclosure. Absence here is the "
                f"expected baseline, not a Heuristic-7 gap.",
                False)

    if is_counterparty_search and claim.get("category") in {"partnership", "vendor_relationship", "customer_pipeline"}:
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"Heuristic 7: counterparty CIK {cik_raw} returns 0 filings naming the claim's "
                f"subject; counterparty-disclosure gap.",
                False)
    return ("UNVERIFIABLE", m_value,
            "EDGAR fulltext returned 0 hits; against the focal company's own filings or with a narrow "
            "search term this is more likely a coverage/term-mismatch issue than a true absence.",
            False)


def _score_finra(claim: dict, f_res: dict) -> tuple[str, str, str, bool]:
    """Score a claim adjudicated by FINRA BrokerCheck."""
    matches = f_res.get("matches") or []
    n = len(matches)
    q = f_res.get("query", "")
    m_value = f"finra: {n} matches for {q!r}"
    if n == 0:
        return ("MODERATE_UNDERDELIVERY" if claim.get("category") == "regulatory_milestone" else "UNVERIFIABLE",
                m_value,
                f"FINRA BrokerCheck returned 0 matches for {q!r} — if the claim asserts a "
                f"registered broker-dealer status, this is a registry contradiction.",
                False)
    top = matches[0]
    detail = f"top: {top.get('firm_name')} (CRD {top.get('crd')}, SEC# {top.get('sec_number')})"
    return ("PASS",
            f"{m_value}; {detail}",
            "FINRA BrokerCheck returned at least one matching firm registration.",
            False)


def _score_fdic_bankfind(claim: dict, b_res: dict) -> tuple[str, str, str, bool]:
    """Score a claim adjudicated by FDIC BankFind (institution registry)."""
    matches = b_res.get("matches") or []
    q = b_res.get("query", "")
    if not matches:
        return ("MODERATE_UNDERDELIVERY",
                f"fdic_bankfind: 0 matches for {q!r}",
                "FDIC BankFind returned 0 matches; a claim of FDIC-chartered status is contradicted.",
                False)
    top = matches[0]
    return ("PASS",
            f"fdic_bankfind: matched {top.get('NAME')} (CERT {top.get('CERT')})",
            "FDIC BankFind resolved the named institution to an active FDIC CERT.",
            False)


def _score_fdic_multi(claim: dict, m_res: dict) -> tuple[str, str, str, bool]:
    """Score a concentration / cohort-credit claim adjudicated by the multi-bank
    consumer-loan aggregation."""
    agg = m_res.get("aggregate") or {}
    n_res = m_res.get("n_banks_resolved", 0)
    n_req = m_res.get("n_banks_requested", 0)
    total = agg.get("total_consumer_loans") or 0
    co = agg.get("weighted_charge_off_pct")
    na = agg.get("weighted_nonaccrual_pct")
    # FDIC reports balances in thousands of dollars; divide by 1e6 to get billions.
    m_value = f"fdic_multi: {n_res}/{n_req} banks resolved; total=${total/1e6:.2f}B co={co}% na={na}%"
    if n_res == 0:
        return ("MODERATE_UNDERDELIVERY", m_value,
                "Multi-bank lookup resolved 0 of the named partners — partner identification weak.",
                False)
    escalate = (isinstance(co, (int, float)) and co > 3.0) or (isinstance(na, (int, float)) and na > 5.0)
    notes = []
    if isinstance(co, (int, float)) and co > 3.0: notes.append(f"weighted co-rate {co}%")
    if isinstance(na, (int, float)) and na > 5.0: notes.append(f"weighted nonaccrual {na}%")
    note_str = "; ".join(notes) if notes else "weighted metrics within typical range"
    return ("PASS", m_value,
            f"Multi-bank Call Report aggregate corroborates partner-set existence. {note_str}.",
            escalate)


def _score_sec_filings(claim: dict, s_res: dict) -> tuple[str, str, str, bool]:
    """Score a claim adjudicated by SEC submissions list_filings_by_form."""
    n = s_res.get("n_total", 0)
    forms = s_res.get("forms", [])
    company = s_res.get("company", "")
    m_value = f"sec_filings: {n} filings for {company} forms={forms}"
    if n == 0:
        # 0 hits under the sponsor's CIK is NOT a contradiction for
        # securitization claims — the trust filings live under their own
        # CIKs. The synth heuristic uses the focal CIK by default, so
        # 0 hits here usually means "wrong CIK scope," not "no filings."
        # Score UNVERIFIABLE; a richer follow-up could resolve trust CIKs.
        return ("UNVERIFIABLE", m_value,
                "SEC submissions API returned 0 filings under the focal CIK for the named form types — "
                "for securitization claims, the relevant filings live under each trust's separate CIK, "
                "so this is more likely a CIK-scope issue than a true absence.",
                False)
    return ("PASS", m_value,
            f"SEC submissions API returned {n} filings of the named form types within the date window.",
            False)


def _score_claim_evolution(claim: dict, ce_res: dict) -> tuple[str, str, str, bool]:
    """Score a claim_evolution finding.

    Status mapping:
      REAFFIRMED_IN_STRUCTURED_DISCLOSURE → PASS (claim persists in 10-K/10-Q)
      REAFFIRMED_IN_8K_ONLY               → UNVERIFIABLE + escalate (could be
                                            material amendment or transient news)
      SILENT_POST_CLAIM                   → MODERATE (concerning for material
                                            claims; the focal company should
                                            continue disclosing if real)
      UNKNOWN / error                     → UNVERIFIABLE
    """
    status = ce_res.get("evolution_status", "UNKNOWN")
    n = ce_res.get("n_subsequent_mentions", 0)
    forms = ce_res.get("forms_mentioning", [])
    search = ce_res.get("search_term", "")
    m_value = f"claim_evolution: {n} subsequent mentions in {forms} (status: {status})"

    adverse = ce_res.get("adverse_findings") or []

    if status == "ADVERSE_EVENT_DETECTED":
        # Surface the specific adverse keyword(s) for the interpretation.
        kws = sorted({k for af in adverse for k in af.get("adverse_hits", [])})
        forms_dates = ", ".join(f"{af['form']} {af['filing_date']}" for af in adverse[:3])
        return ("SEVERE_UNDERDELIVERY", m_value,
                f"Adverse event detected in {forms_dates}: '{search}' appears near "
                f"{kws[:6]} — claim's relationship has been materially amended/terminated.",
                True)  # escalate so LLM can confirm
    if status == "AMENDMENT_DETECTED":
        kws = sorted({k for af in adverse for k in af.get("amendment_hits", [])})
        forms_dates = ", ".join(f"{af['form']} {af['filing_date']}" for af in adverse[:3])
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"Amendment/modification detected in {forms_dates}: '{search}' appears near "
                f"{kws[:6]} — relationship has been modified; could be routine extension or "
                f"adverse restructuring. LLM review needed.",
                True)
    if status == "REAFFIRMED_IN_STRUCTURED_DISCLOSURE":
        ctxt = (claim.get("claim_text") or "")
        wants_fact_check = any(tok in ctxt for tok in ["$", "million", "billion", "%"]) and \
                           claim.get("category") in {"financial_distress", "customer_pipeline",
                                                     "production_volume", "regulatory_milestone"}
        return ("PASS", m_value,
                f"Focal company has reaffirmed the claim's subject {n} times in structured filings "
                f"with no adverse-event signatures detected; directional continuity supports the claim.",
                wants_fact_check)
    if status == "SILENT_POST_CLAIM":
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"Focal company has not mentioned '{search}' in any subsequent filing between "
                f"{ce_res.get('window_start')} and {ce_res.get('window_end')}. Material claims "
                f"typically reappear in 10-Q cadence; silence is a disclosure-quality concern.",
                True)
    if status == "REAFFIRMED_IN_8K_ONLY":
        return ("UNVERIFIABLE", m_value,
                f"Mentioned only in 8-K filings ({n} mentions) with no adverse signatures. "
                f"Could be routine press-release tag-out. LLM review needed.",
                True)
    return ("UNVERIFIABLE", m_value,
            f"claim_evolution status {status!r}; insufficient for scoring.",
            False)


def _score_epa_emissions(claim: dict, e_res: dict) -> tuple[str, str, str, bool]:
    """Score an EPA FRS/TRI/GHGRP operational-capacity finding (v2).

    v2 added FRS-presence as the primary "company is permitted at all" probe
    and the claimed_location_audit. Signals:

      INDUSTRIAL_SCALE_CONFIRMED              → PASS (in TRI or GHGRP)
      CLAIMED_LOCATION_GAP                    → MODERATE + escalate
                                                 (company has FRS presence
                                                  elsewhere but NOT at any
                                                  caller-supplied claimed plant
                                                  location — strongest divergence)
      FRS_PERMITTED_NO_INDUSTRIAL_REPORTING   → context-dependent:
                                                  for chemistry/heavy-mfg
                                                  industrial claims → MODERATE
                                                  + escalate; for clean-tech /
                                                  electrolytic / assembly claims
                                                  the absence isn't diagnostic
                                                  by chemistry → UNVERIFIABLE
      NO_EPA_FOOTPRINT                        → MODERATE + escalate for any
                                                  industrial-text claim;
                                                  UNVERIFIABLE otherwise
    """
    sig = e_res.get("operational_scale_signal", "UNKNOWN")
    name = e_res.get("company_name", "")
    n_frs = (e_res.get("frs") or {}).get("facilities_found", 0)
    n_tri = (e_res.get("tri") or {}).get("facilities_found", 0)
    n_ghg = (e_res.get("ghgrp") or {}).get("facilities_found", 0)
    audit = e_res.get("claimed_location_audit") or []
    n_loc = len(audit)
    n_missing = sum(1 for a in audit if not a.get("company_present_at_loc"))
    m_value = (
        f"epa: {name} → FRS={n_frs} TRI={n_tri} GHGRP={n_ghg} "
        f"audit={n_missing}/{n_loc} missing (signal: {sig})"
    )

    # Diagnostic-by-claim-text: the EPA registry test is meaningful only when
    # the claim itself implies physical industrial operations.
    ctxt = (claim.get("claim_text") or "").lower()
    industrial_words = any(w in ctxt for w in [
        "manufactur", "production", "facility", "facilities", "plant",
        "gigafactory", "fleet", "shipped", "delivered", "tons ", "tonnes",
        "megawatt", "gigawatt", " gw", " mw", "kilotons",
    ])
    chemistry_words = any(w in ctxt for w in [
        "chemical", "solvent", "polymer", "battery", "cathode", "anode",
        "lithium", "cobalt", "nickel", "refining", "smelt", "ammonia",
        "methanol", "petrochem", "specialty chem", "active ingredient",
        "api ", "pesticide", "coatings",
    ])
    narrow_industrial_categories = {
        "production_volume", "manufacturing_capacity", "facility_capacity",
    }
    industrial_claim = industrial_words or (claim.get("category") in narrow_industrial_categories)

    if sig == "INDUSTRIAL_SCALE_CONFIRMED":
        return ("PASS", m_value,
                f"Focal company is present in EPA industrial-reporting registries "
                f"(TRI={n_tri}, GHGRP={n_ghg}); operational footprint corroborates the claim's "
                f"scale assertions.",
                False)

    if sig == "CLAIMED_LOCATION_GAP":
        missing = [a for a in audit if not a.get("company_present_at_loc")]
        loc_str = ", ".join(f"{a['city']} {a['state']}" for a in missing[:5])
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"Focal company has {n_frs} FRS-registered facilities elsewhere but is NOT "
                f"present at {len(missing)}/{n_loc} claimed plant locations ({loc_str}). "
                f"EPA recognizes the company generally; the gap is specifically at the "
                f"locations marketed as production facilities. Strong divergence between "
                f"R (claim of operating at named plant) and M (no permit at that address).",
                True)

    if sig == "FRS_PERMITTED_NO_INDUSTRIAL_REPORTING":
        if industrial_claim and chemistry_words:
            # Chemistry/heavy-mfg claim: TRI/GHGRP absence IS diagnostic (these
            # processes almost always cross thresholds).
            return ("MODERATE_UNDERDELIVERY", m_value,
                    f"Focal company has {n_frs} FRS-permitted facilities but none cross TRI "
                    f"(10k-25k lb/yr chemicals) or GHGRP (25kt CO2e/yr) thresholds. The "
                    f"claim describes chemistry-/heavy-manufacturing operations that would "
                    f"normally trigger those thresholds — sub-threshold operation contradicts "
                    f"the claimed scale.",
                    True)
        # Non-chemistry industrial (assembly, electrolytic, electronics): the
        # company could legitimately operate at scale without TRI/GHGRP hits.
        return ("UNVERIFIABLE", m_value,
                f"Focal company has {n_frs} FRS-permitted facilities but is below TRI/GHGRP "
                f"thresholds. For non-chemistry / assembly / electrolytic operations this "
                f"isn't necessarily diagnostic — the underlying process may not generate "
                f"reportable chemical or GHG events even at industrial scale.",
                False)

    if sig == "NO_EPA_FOOTPRINT":
        if industrial_claim:
            return ("MODERATE_UNDERDELIVERY", m_value,
                    f"Focal company has zero EPA-registered facilities under the searched "
                    f"name. The claim implies industrial-scale physical operations; absence "
                    f"of any FRS/TRI/GHGRP record is a strong divergence signal. Possible "
                    f"causes: filed under subsidiary name (LLM should check), pre-permit "
                    f"phase, or operations don't exist at claimed scale.",
                    True)
        return ("UNVERIFIABLE", m_value,
                f"No EPA footprint found, but the claim does not clearly assert industrial-"
                f"scale physical operations — signal not diagnostic.",
                False)

    return ("UNVERIFIABLE", m_value,
            f"EPA operational-scale signal {sig!r}; insufficient for scoring.",
            False)


def _score_uspto(claim: dict, u_res: dict) -> tuple[str, str, str, bool]:
    matches = u_res.get("matches") or u_res.get("results") or []
    n = len(matches) if isinstance(matches, list) else 0
    m_value = f"uspto_odp: {n} assignment records"
    if n == 0:
        return ("UNVERIFIABLE", m_value,
                "USPTO assignee name returned 0 records — patent activity may be filed under a subsidiary "
                "or a different legal entity name; asymmetric.",
                False)
    return ("PASS", m_value,
            f"USPTO returned {n} assignment records under the claimed assignee.",
            False)


_FEDERAL_KEYWORDS = (
    "dod", "defense", "military", "army", "navy", "air force", "marine",
    "nasa", "doe", "department of energy", "department of defense",
    "federal", "government", "agency", "contract", "darpa", "afrl",
    "veterans", "va ", "fbi", "homeland security", "dhs",
    "sbir", "sttr", "cooperative agreement",
)


def _score_usaspending_presence(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score a claim adjudicated by usaspending.query_federal_presence.

      - signal=INFLATION_SUSPECT      → SEVERE_UNDERDELIVERY (if the claim
                                         text references federal/agency
                                         terms; else UNVERIFIABLE so a
                                         planner mis-map can't emit a
                                         false bear signal)
      - signal=SUB_MATERIAL_FEDERAL   → UNVERIFIABLE with escalate=True
                                         (ambiguous band — sub-material
                                         can be honest-small or inflated;
                                         needs LLM scope-vs-language
                                         comparison)
      - signal=RECURRING_FEDERAL      → PASS
      - missing signal                → UNVERIFIABLE

    Defensive against planner mis-mapping: if the claim text has no
    federal-flavored keyword, an INFLATION_SUSPECT result is treated as
    UNVERIFIABLE (likely wrong source choice, not a real contradiction).

    The SUB_MATERIAL band is intentionally NOT a MODERATE flag: it
    mirrors the symmetric behavior of megacap_namecheck (where 1-2
    hits is also UNVERIFIABLE-ambiguous). A real inflation pattern
    (claim language overstates registry scope) requires LLM judgment
    on the claim text vs the dollar/agency breakdown — not a count
    threshold alone.
    """
    sig = r.get("signal")
    n_ueis = r.get("n_ueis_resolved", 0)
    contracts_M = r.get("contracts_amount_M", 0.0)
    grants_M    = r.get("grants_amount_M", 0.0)
    top_agency  = None
    ags = r.get("agencies") or {}
    if ags:
        top_agency = max(ags.items(), key=lambda x: x[1])[0]
    m_value = (f"usaspending: ueis={n_ueis} contracts=${contracts_M:.1f}M "
               f"grants=${grants_M:.1f}M top_agency={top_agency or '—'}")

    claim_text_lc = (claim.get("claim_text") or "").lower()
    federal_flavored = any(kw in claim_text_lc for kw in _FEDERAL_KEYWORDS)

    if sig == "INFLATION_SUSPECT":
        if not federal_flavored:
            return ("UNVERIFIABLE", m_value,
                    "$0 lifetime awards, but the claim text contains no federal/agency "
                    "keyword — likely a planner mis-map of a non-federal claim to a "
                    "federal-registry source. Not adjudicatable.",
                    False)
        if n_ueis == 0:
            interp = ("UEI-anchored search resolved 0 federal recipient profiles and "
                      "0 awards across all queried name variants. usaspending is a "
                      "comprehensive registry (every federal award recorded); absence "
                      "of any UEI for any variant is a hard contradiction of a "
                      "federal-relationship claim, not a coverage gap.")
        else:
            interp = (f"UEI-anchored search resolved {n_ueis} registered UEI(s) but "
                      f"$0 in contracts and $0 in grants. usaspending records every "
                      f"federal award; a UEI that has never won any award despite a "
                      f"claim of federal selection/contract/partnership is an "
                      f"inflation pattern — the company registered to bid but the "
                      f"award the claim implies does not exist in the registry.")
        return ("SEVERE_UNDERDELIVERY", m_value, interp, False)

    if sig == "SUB_MATERIAL_FEDERAL":
        return ("UNVERIFIABLE", m_value,
                f"Federal awards present (top agency {top_agency}) but lifetime scale "
                f"<$5M across {n_ueis} UEIs. This is the AMBIGUOUS BAND — could be an "
                f"honest disclosure of a real-but-small federal vendor relationship, "
                f"or could be a sub-material relationship being described in inflated "
                f"'program / partnership' language. Count alone can't disambiguate; "
                f"escalate for LLM scope-vs-claim-language comparison.",
                True)

    if sig == "RECURRING_FEDERAL":
        return ("PASS", m_value,
                f"Recurring federal presence (>$5M lifetime, ${contracts_M:.1f}M contracts + "
                f"${grants_M:.1f}M grants) across {n_ueis} UEIs corroborates the claim. "
                f"Top agency: {top_agency}.",
                False)

    return ("UNVERIFIABLE", m_value,
            "usaspending result lacks the signal field; not deterministically adjudicatable.",
            False)


def _score_sam_entity(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score a SAM.gov entity lookup result.

    Signals checked, in priority:
      - error / no_entity_found → UNVERIFIABLE (might not be federal-eligible)
      - exclusion_flag == 'Y'   → SEVERE_UNDERDELIVERY (debarred)
      - registration_status != 'Active' → MODERATE if federal claim,
                                           else PASS
      - expected_naics_prefix on the claim and primary_naics doesn't
        match → MODERATE_UNDERDELIVERY (escalate, scope mismatch)
      - otherwise → PASS (declared identity matches claim shape)
    """
    if r.get("error"):
        return ("UNVERIFIABLE", f"sam: error={r.get('error')}",
                "SAM entity lookup failed or returned no record — entity may "
                "not be federally registered (most non-federal small-caps "
                "are not). Not adjudicatable from this source alone.",
                False)

    legal = r.get("legal_business_name") or "?"
    primary = r.get("primary_naics") or "?"
    addr = r.get("physical_address") or {}
    loc = f"{addr.get('city','?')}, {addr.get('state','?')}"
    status = r.get("registration_status") or "?"
    excl = r.get("exclusion_flag") or "N"

    naics_desc = ""
    for nc, nd in (r.get("all_naics") or []):
        if nc == primary:
            naics_desc = (nd or "").strip()
            break
    m_value = (f"sam: {legal[:30]} NAICS={primary} ({naics_desc[:30]}) "
               f"loc={loc} status={status} excl={excl}")

    if excl == "Y":
        return ("SEVERE_UNDERDELIVERY", m_value,
                "SAM exclusion_flag is 'Y' — entity is debarred from federal "
                "contracts. Any federal-customer-pipeline claim is materially "
                "compromised.",
                False)

    claim_text_lc = (claim.get("claim_text") or "").lower()
    federal_flavored = any(kw in claim_text_lc for kw in _FEDERAL_KEYWORDS)

    if status and status != "Active" and federal_flavored:
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"SAM registration status is '{status}', not 'Active'. The "
                "claim references a federal/agency relationship that requires "
                "an active SAM registration; inactive registration weakens "
                "the federal-customer pipeline narrative.",
                True)

    expected_naics = claim.get("expected_naics_prefix")
    if expected_naics and primary and primary != "?":
        if not primary.startswith(expected_naics):
            return ("MODERATE_UNDERDELIVERY", m_value,
                    f"SAM primary NAICS is {primary} ({naics_desc!r}) but the "
                    f"claim implies expected NAICS prefix {expected_naics!r}. "
                    f"The company self-declared a different business activity "
                    f"to the federal government than its filings describe — "
                    f"scope contradiction. Escalate for LLM scope-vs-language "
                    f"review.",
                    True)
        return ("PASS", m_value,
                f"SAM primary NAICS {primary} matches expected prefix "
                f"{expected_naics}; entity declared business activity is "
                f"consistent with the filing's claim.",
                False)

    return ("PASS", m_value,
            f"SAM entity active. Primary NAICS {primary} ({naics_desc!r}), "
            f"located in {loc}, CAGE {r.get('cage_code') or '—'}. No "
            "expected_naics_prefix supplied on the claim to mechanically "
            "test scope match.",
            False)


_DEFENSE_KEYWORDS = (
    "classified", "secret", "top-secret", "cleared",
    "u.s. citizen", "us citizen", "security clearance",
)

_LARGE_WORKFORCE_KWS = (
    "thousand", "1,000", "5,000", "10,000", "largest", "major u.s.",
    "fortune 500", "fortune-500", "national manufacturer",
    "industrial-scale", "mass production",
)


def _score_ucc_proxy(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score a UCC-proxy lien-exposure result.

      HIGH_LIEN_EXPOSURE (distress-credit cluster) → MODERATE_UNDERDELIVERY
        with escalate=True. Plus SEVERE if the claim text asserts
        clean / unencumbered balance sheet.
      ELEVATED_LIEN_EXPOSURE → UNVERIFIABLE escalate (mature company
        with senior facility looks similar to elevated-distress;
        needs LLM review of claim language vs term mix)
      MODERATE_LIEN_EXPOSURE → UNVERIFIABLE
      LOW_LIEN_EXPOSURE → PASS (clean balance sheet corroborated)
    """
    sig = r.get("signal")
    distress = r.get("distress_term_hits", 0)
    total = r.get("total_term_hits", 0)
    top_terms = r.get("top_terms_found", [])[:3]
    m_value = (f"ucc_proxy: distress_terms={distress} total_terms={total} "
               f"top={top_terms} signal={sig}")

    claim_text_lc = (claim.get("claim_text") or "").lower()
    clean_balance_sheet_kws = (
        "no secured", "no liens", "unencumbered", "no material",
        "no outstanding", "no senior debt", "debt-free",
        "no long-term debt",
    )
    claims_clean = any(kw in claim_text_lc for kw in clean_balance_sheet_kws)

    if sig == "HIGH_LIEN_EXPOSURE":
        if claims_clean:
            return ("SEVERE_UNDERDELIVERY", m_value,
                    f"Filing claims unencumbered balance sheet but SEC FTS "
                    f"returns {distress} distress-credit term mentions "
                    f"({top_terms}) in subsequent filings. Hard contradiction.",
                    False)
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"High distress-credit-term density ({distress} hits, "
                f"top={top_terms}). Consistent with active secured-debt "
                f"financing / factoring / distress-credit structures. "
                f"Escalate for LLM review of magnitude + counterparty mix.",
                True)

    if sig == "ELEVATED_LIEN_EXPOSURE":
        return ("UNVERIFIABLE", m_value,
                f"{total} secured-debt terms detected; mature companies "
                f"with senior facilities present similarly. Needs LLM "
                f"review of claim language vs term mix to distinguish "
                f"distress from normal secured-credit activity.",
                True)

    if sig == "LOW_LIEN_EXPOSURE":
        if claims_clean:
            return ("PASS", m_value,
                    "Filing claims unencumbered balance sheet; UCC-proxy "
                    "confirms 0 secured-debt term hits.",
                    False)
        return ("PASS", m_value,
                "No secured-debt terms detected — no material UCC-equivalent "
                "exposure visible in SEC filings.",
                False)

    return ("UNVERIFIABLE", m_value,
            f"Moderate lien exposure; could be ordinary corporate credit "
            f"or low-grade financing. {total} term hits.",
            False)


def _score_bls_qcew(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score a BLS QCEW county-NAICS plausibility query.

    The scorer can't on its own decide what "implausible share" is —
    the planner must encode the company's claimed headcount in
    `expected_employees` on the claim. If supplied, we compute the
    company's implied % share of county-NAICS employment and emit:

      implied share > 50% on a small-cap claim     → MODERATE (escalate)
      implied share 20-50% on small-cap claim      → UNVERIFIABLE escalate
      implied share < 20% OR no expected_employees → PASS (real footprint)
      0 establishments in county-NAICS              → UNVERIFIABLE (suppressed
                                                       cell, common at small
                                                       counties)
    """
    total_emp = r.get("total_employees", 0)
    total_estabs = r.get("total_estabs", 0)
    fips = r.get("fips5", "?")
    naics = r.get("naics_prefix", "?")
    m_value = (f"bls_qcew: county_emp={total_emp} county_estabs={total_estabs} "
               f"fips={fips} naics={naics}")

    if total_estabs == 0:
        return ("UNVERIFIABLE", m_value,
                "0 establishments reported for this county+NAICS cell — "
                "may be a suppressed (D-flagged) cell or a county where "
                "the industry is genuinely absent. Not informative.",
                False)

    expected = claim.get("expected_employees")
    if not expected or total_emp == 0:
        return ("PASS", m_value,
                f"County-NAICS shows {total_estabs} establishments / "
                f"{total_emp} employees — facility-scope claim plausible "
                f"at this aggregation level. (Claim didn't supply "
                f"expected_employees for share-implausibility check.)",
                False)

    try:
        share = float(expected) / total_emp
    except (TypeError, ValueError, ZeroDivisionError):
        return ("UNVERIFIABLE", m_value,
                "Could not compute implied share — bad expected_employees.",
                False)

    if share > 0.5:
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"Claim implies {expected} employees = {share*100:.0f}% of "
                f"county-NAICS total ({total_emp}). Implausibly large share "
                f"for a small-cap; either claim is inflated or county-NAICS "
                f"data is suppressed/old.",
                True)
    if share > 0.2:
        return ("UNVERIFIABLE", m_value,
                f"Claim implies {expected} employees = {share*100:.0f}% of "
                f"county-NAICS total — large but not impossible; needs "
                f"manual review of claim language vs facility footprint.",
                True)
    return ("PASS", m_value,
            f"Claim implies {expected} employees = {share*100:.0f}% of "
            f"county-NAICS total ({total_emp} across {total_estabs} estabs) "
            f"— plausible share.",
            False)


def _score_pentagon_jbook(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score Pentagon J-Book program-funding result.

    Canonical YSS/IONQ catch: a small-cap claims revenue from a Pentagon
    program; the J-Book shows the program is unfunded for 2+ consecutive
    FYs. The issuer's customer is disappearing on a public-record
    timeline they haven't disclosed.

    Signal → severity:
      UNFUNDED_TWO_PLUS_YEARS → SEVERE_UNDERDELIVERY
        (canonical pattern — program zeroed in 2+ consecutive J-Books)
      TERMINATED → RED_FLAG_NEGATIVE
        (program explicitly killed)
      UNFUNDED_THIS_YEAR → MODERATE_UNDERDELIVERY
        (one-year gap; could be CR timing, but flag for follow-up)
      FUNDED_SHRINKING → MODERATE_UNDERDELIVERY
        (funding declining year-over-year)
      FUNDED_STEADY / FUNDED_GROWING → PASS
      NOT_FOUND → UNVERIFIABLE
        (program not in our hand-extracted corpus; extend
         data/_jbook_data/programs.json to cover)
    """
    sig = r.get("signal", "NOT_FOUND")
    pm = r.get("primary_match") or {}
    n = r.get("n_matches", 0)
    prog_name = pm.get("program_name") or "(no match)"
    pe = pm.get("pe_number") or "—"
    consec = pm.get("n_consecutive_unfunded", 0)
    latest_y = pm.get("latest_funded_year")
    latest_m = pm.get("latest_funded_M")
    contractors = (pm.get("primary_contractors") or [])[:3]
    replacement = pm.get("replacement_program")
    repl_sole = pm.get("replacement_sole_source")

    m_value = (f"pentagon_jbook: matches={n} program={prog_name!r} "
               f"PE={pe} status={sig} consec_unfunded={consec}")

    if sig == "NOT_FOUND":
        return ("UNVERIFIABLE", m_value,
                f"No Pentagon program matched the query in the J-Book corpus. "
                f"Either the program isn't in our hand-extracted set yet "
                f"(extend data/_jbook_data/programs.json) or the query terms "
                f"don't match any known name/synonym/PE. Cannot assess forward "
                f"funding status.",
                False)

    if sig == "TERMINATED":
        return ("RED_FLAG_NEGATIVE", m_value,
                f"Program {prog_name!r} (PE {pe}) is officially terminated per "
                f"J-Book narrative. Any issuer relying on this program for "
                f"future revenue should have disclosed the termination.",
                False)

    if sig == "UNFUNDED_TWO_PLUS_YEARS":
        bridge = ""
        if replacement:
            bridge = (f" Replacement program: {replacement!r}"
                      f"{f' — sole-sourced to {repl_sole!r}' if repl_sole else ''}.")
        last_funded = (f"last funded year was FY{latest_y} at ${latest_m}M; "
                       if latest_y else "")
        return ("SEVERE_UNDERDELIVERY", m_value,
                f"Pentagon J-Book shows program {prog_name!r} (PE {pe}) is "
                f"unfunded for {consec} consecutive FYs.{bridge} Primary "
                f"contractors per our corpus: {contractors}. "
                f"{last_funded}A federal-customer claim that depends on this "
                f"program for forward revenue is contradicted by the public "
                f"budget record.",
                False)

    if sig == "UNFUNDED_THIS_YEAR":
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"Pentagon J-Book shows program {prog_name!r} (PE {pe}) is "
                f"unfunded for the current FY. Single-year gaps can reflect "
                f"continuing-resolution timing rather than program death, but "
                f"the issuer should be tracking this. Flag for follow-up at "
                f"next J-Book release.",
                True)  # escalate

    if sig == "FUNDED_SHRINKING":
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"Pentagon J-Book shows program {prog_name!r} (PE {pe}) is "
                f"FUNDED_SHRINKING — funding declining year-over-year. Not a "
                f"termination but a customer-concentration risk if this "
                f"program is the issuer's primary revenue source.",
                False)

    if sig in ("FUNDED_GROWING", "FUNDED_STEADY"):
        return ("PASS", m_value,
                f"Pentagon J-Book shows program {prog_name!r} (PE {pe}) is "
                f"{sig}. Forward funding trajectory supports the issuer's "
                f"federal-customer revenue claim.",
                False)

    if sig == "MULTIPLE_PROGRAMS":
        return ("UNVERIFIABLE", m_value,
                f"Query matched multiple programs ({n}); needs more specific "
                f"program_name or pe_number to disambiguate.",
                True)

    return ("UNVERIFIABLE", m_value,
            f"Pentagon J-Book returned unexpected signal {sig!r}; treat as "
            f"unverifiable.",
            False)


def _score_earmark_detector(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score an earmark_detector result.

    Signal → severity:
      EARMARK_SUNSET    → SEVERE_UNDERDELIVERY
        (program is gone AND political backers gone — canonical IONQ pattern)
      EARMARK_AT_RISK   → SEVERE_UNDERDELIVERY
        (program live now but sponsors out → forward de-funding likely)
      ROUTINE_EARMARK   → MODERATE_UNDERDELIVERY
        (still active, but earmark-funded is forward-fragile)
      AMBIGUOUS         → UNVERIFIABLE
      NOT_EARMARK       → PASS
        (program funded via regular Pentagon request, not a political add)
    """
    sig = r.get("signal", "NOT_EARMARK")
    pm = r.get("primary_match") or {}
    sp = pm.get("sponsors") or {}
    n_sponsors = sp.get("n_sponsors", 0)
    n_in_power = sp.get("n_in_power", 0)
    n_lost = sp.get("n_lost_power", 0)
    all_lost = sp.get("all_lost_power", False)
    most_recent_loss = sp.get("most_recent_loss")
    earmark_id = pm.get("earmark_id") or "—"
    program_name = pm.get("program_name") or "—"
    m_value = (f"earmark_detector: earmark={earmark_id} signal={sig} "
               f"sponsors={n_in_power}/{n_sponsors} in_power, "
               f"all_lost={all_lost}")

    if sig == "NOT_EARMARK":
        return ("PASS", m_value,
                f"No matching earmark in the corpus. The claim's underlying "
                f"program funding does not appear to be a known congressional "
                f"add (or the earmark isn't in our corpus yet; extend "
                f"data/_earmark_data/earmarks.json).",
                False)

    if sig == "EARMARK_SUNSET":
        return ("SEVERE_UNDERDELIVERY", m_value,
                f"Earmark {earmark_id!r} for {program_name!r} has SUNSET: "
                f"funding has been zero in the latest FY(s) AND "
                f"{n_lost}/{n_sponsors} sponsoring lawmakers have lost power "
                f"({sp.get('sponsors_resolved', [])[:3]}). Most recent "
                f"sponsor loss: {most_recent_loss}. Forward revenue from this "
                f"line is structurally finished, not just paused. This is "
                f"the canonical IONQ-style 'earmark + politics + zero "
                f"current funding' SEVERE catch.",
                False)

    if sig == "EARMARK_AT_RISK":
        return ("SEVERE_UNDERDELIVERY", m_value,
                f"Earmark {earmark_id!r} for {program_name!r} is AT RISK: "
                f"the line item was previously a congressional add, and "
                f"sponsoring lawmakers are in transitioning state "
                f"({n_in_power}/{n_sponsors} still in power; "
                f"{n_lost} have lost power). Earmark-funded programs do not "
                f"survive once their political backers exit committee or "
                f"chamber majority. High forward de-funding risk.",
                False)

    if sig == "ROUTINE_EARMARK":
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"Earmark {earmark_id!r} for {program_name!r} is ROUTINE: "
                f"line item is a congressional add but sponsoring lawmakers "
                f"are still in power ({n_in_power}/{n_sponsors}). Funding "
                f"is current but earmark-funded programs are structurally "
                f"more fragile than Pentagon-requested ones — flag for "
                f"follow-up if a sponsor loses re-election or committee "
                f"position. Lower-conviction signal than EARMARK_AT_RISK.",
                True)

    if sig == "AMBIGUOUS":
        return ("UNVERIFIABLE", m_value,
                f"Earmark history is partial; cannot determine current "
                f"signal. Likely missing sponsor information or incomplete "
                f"annual funding history.",
                True)

    return ("UNVERIFIABLE", m_value,
            f"earmark_detector returned unexpected signal {sig!r}.",
            False)


def _score_cybercom_budget(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score a cybercom_budget envelope result.

    Aggregates service cyber SAGs (+ USCYBERCOM unified appropriation when
    available) and adjudicates a CMF/CYBERCOM-customer claim against the
    envelope trajectory.

    Signal → severity:
      FUNDED_GROWING            → PASS
      FUNDED_STEADY             → PASS
      FUNDED_SHRINKING          → MODERATE_UNDERDELIVERY
      COVERAGE_PARTIAL          → UNVERIFIABLE (< 3 services in envelope)
      NOT_FOUND                 → UNVERIFIABLE

    IMPORTANT: a PASS at the envelope level does NOT verify the issuer's
    own share of that envelope. OP-5 SAGs carry no contractor attribution,
    so envelope health is necessary but not sufficient for the claim. The
    interpretation flags this and recommends paired usaspending lookup.
    """
    sig = r.get("signal", "NOT_FOUND")
    envelope = r.get("envelope_by_fy") or {}
    services = r.get("services_covered") or []
    trajectory = r.get("trajectory")
    n_sags = r.get("n_sags", 0)
    gaps = r.get("_gaps") or []
    contractor_note = r.get("_contractor_note") or ""

    fy_keys = sorted(envelope.keys())
    latest_fy = fy_keys[-1] if fy_keys else "?"
    latest_amt = envelope.get(latest_fy, 0)
    traj_pct = f"{trajectory*100:+.1f}%" if trajectory is not None else "n/a"

    m_value = (
        f"cybercom_budget: signal={sig} envelope_{latest_fy}=${latest_amt:,.0f}M "
        f"trajectory={traj_pct} services={services} n_sags={n_sags}"
    )

    if sig == "NOT_FOUND":
        return ("UNVERIFIABLE", m_value,
                "No cyber SAGs in J-Book corpus. Either Army/Navy/USMC/SOCOM "
                "O&M books haven't been ingested, or the cyber SAG naming "
                "doesn't match the patterns this aggregator looks for. "
                "Extend data/_jbook_data/programs.json with service cyber "
                "SAGs.",
                False)

    if sig == "COVERAGE_PARTIAL":
        gaps_str = "; ".join(gaps) if gaps else "missing services"
        return ("UNVERIFIABLE", m_value,
                f"Cyber envelope has fewer than 3 services covered "
                f"({services}). Trajectory not actionable until corpus "
                f"covers ≥ 3 services. Known gaps: {gaps_str}.",
                False)

    contractor_caveat = (
        " IMPORTANT: OP-5 SAGs do not carry contractor attribution — a "
        "healthy envelope is necessary but not sufficient for the issuer's "
        "own CYBERCOM-customer claim. Pair with usaspending awards under "
        "CYBERCOM agency codes / named cyber IDIQs to verify the issuer's "
        "share."
    )

    if sig == "FUNDED_SHRINKING":
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"Aggregate CMF/CYBERCOM cyber envelope is FUNDED_SHRINKING "
                f"(trajectory {traj_pct}, latest {latest_fy}=${latest_amt:,.0f}M "
                f"across {n_sags} SAGs in {services}). An issuer claiming "
                f"forward growth from CMF/CYBERCOM customer mix is not "
                f"corroborated by the budget side.{contractor_caveat}",
                False)

    if sig in ("FUNDED_STEADY", "FUNDED_GROWING"):
        return ("PASS", m_value,
                f"Aggregate CMF/CYBERCOM cyber envelope is {sig} "
                f"(trajectory {traj_pct}, latest {latest_fy}=${latest_amt:,.0f}M "
                f"across {n_sags} SAGs in {services}). Forward funding "
                f"trajectory supports an issuer's CYBERCOM-customer "
                f"revenue claim at the envelope level.{contractor_caveat}",
                False)

    return ("UNVERIFIABLE", m_value,
            f"cybercom_budget returned unexpected signal {sig!r}.",
            False)


def _score_auditor_change(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score auditor_change_tracker result.

    Signal → severity:
      CLEAN_AUDITOR_TENURE       → PASS
      UPGRADE_OR_LATERAL         → PASS (routine change)
      DOWNGRADE_TO_SMALLER_FIRM  → MODERATE_UNDERDELIVERY
      RESIGNATION_OR_DECLINE     → SEVERE_UNDERDELIVERY
      DISAGREEMENT_DISCLOSED     → RED_FLAG_NEGATIVE (affirmative-only)
      FREQUENT_TURNOVER          → SEVERE_UNDERDELIVERY
      NOT_FOUND                  → UNVERIFIABLE
    """
    sig = r.get("signal", "NOT_FOUND")
    n_changes = r.get("n_8k_item_401", 0)
    changes = r.get("changes") or []
    n_resign = r.get("n_big4_resignations", 0)
    n_dis = r.get("n_disagreements", 0)
    latest = changes[0] if changes else {}

    m_value = (
        f"auditor_change: signal={sig} n_changes={n_changes} "
        f"big4_resign={n_resign} disagreements={n_dis}"
    )

    if sig == "NOT_FOUND":
        return ("UNVERIFIABLE", m_value,
                f"Could not retrieve filings for auditor-change check.",
                False)

    if sig == "CLEAN_AUDITOR_TENURE":
        return ("PASS", m_value,
                f"No Item 4.01 auditor-change disclosures in lookback "
                f"({r.get('lookback_start','?')} to {r.get('cutoff_date','?')}). "
                f"Stable audit relationship.",
                False)

    if sig == "UPGRADE_OR_LATERAL":
        return ("PASS", m_value,
                f"Single auditor change ({latest.get('date')}) but no "
                f"resignation language and no disclosed disagreement. "
                f"Routine change; not a quality signal.",
                False)

    if sig == "DOWNGRADE_TO_SMALLER_FIRM":
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"Auditor change ({latest.get('date')}) from Big 4 to "
                f"smaller firm. Often signals fee pressure or audit-"
                f"relationship friction. Not definitively bad but "
                f"deserves analyst review of the 8-K text.",
                True)

    if sig == "RESIGNATION_OR_DECLINE":
        return ("SEVERE_UNDERDELIVERY", m_value,
                f"Former auditor ({latest.get('former_auditor','?')}) "
                f"resigned or declined re-appointment on {latest.get('date')}. "
                f"This is uncommon for Big 4 firms unless something is "
                f"materially wrong. High-priority red flag for any long "
                f"position.",
                False)

    if sig == "DISAGREEMENT_DISCLOSED":
        return ("RED_FLAG_NEGATIVE", m_value,
                f"8-K Item 4.01 ({latest.get('date')}) AFFIRMATIVELY "
                f"discloses material disagreement / reportable event / "
                f"material weakness between issuer and former auditor "
                f"({latest.get('former_auditor','?')}). The detector "
                f"uses affirmative-only matching ('there were' / 'there "
                f"was'); 'no disagreement' template language does not "
                f"trigger. This is the canonical disclosure-quality red "
                f"flag — investigate before any long position.",
                False)

    if sig == "FREQUENT_TURNOVER":
        return ("SEVERE_UNDERDELIVERY", m_value,
                f"{n_changes} auditor changes in lookback window. "
                f"Pattern correlated with restatement risk and management "
                f"opacity. Investigate each change individually.",
                True)

    return ("UNVERIFIABLE", m_value,
            f"auditor_change_tracker returned unexpected signal {sig!r}.",
            False)


def _score_going_concern(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score going_concern_detector result.

    Signal → severity:
      EXPLICIT_GOING_CONCERN   → SEVERE_UNDERDELIVERY
        (current-period auditor/management language; 12-month survival
         in question)
      MITIGATED_GOING_CONCERN  → MODERATE_UNDERDELIVERY
        (cure language present but recent history)
      CURE_LANGUAGE            → MODERATE_UNDERDELIVERY (escalate for analyst review)
      NO_GOING_CONCERN         → PASS
      NOT_FOUND_FILING         → UNVERIFIABLE
    """
    sig = r.get("signal", "NOT_FOUND_FILING")
    n_total = r.get("n_matches", 0)
    n_current = r.get("n_current_period_matches", 0)
    n_cure = r.get("n_cure_matches", 0)
    filing = r.get("filing") or {}
    form = filing.get("form", "?")
    filed = filing.get("filed_at") or filing.get("filing_date", "?")

    m_value = (
        f"going_concern: signal={sig} form={form} filed={filed} "
        f"matches={n_total} current={n_current} cure={n_cure}"
    )

    if sig == "NOT_FOUND_FILING":
        return ("UNVERIFIABLE", m_value,
                f"No 10-K/10-Q available for going-concern check. "
                f"{r.get('_note', '')}",
                False)

    if sig == "EXPLICIT_GOING_CONCERN":
        sample = (r.get("sample_contexts") or [""])[0][:300]
        return ("SEVERE_UNDERDELIVERY", m_value,
                f"Auditor or management uses 'substantial doubt about the "
                f"ability to continue as a going concern' language in the "
                f"current-period {form} (filed {filed}); {n_current} "
                f"current-period matches found. Sample: '...{sample}...' "
                f"All other claim verification is moot until this is "
                f"resolved. Strong AVOID signal for any long position.",
                False)

    if sig == "MITIGATED_GOING_CONCERN":
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"Going-concern language appears in the most recent {form} "
                f"({filed}) with cure language nearby ({n_cure} cure "
                f"matches). Suggests recent history of substantial doubt "
                f"that management has addressed. Verify the cure (capital "
                f"raise, refinancing) actually closed; if so, the language "
                f"may clear in the next filing.",
                True)

    if sig == "CURE_LANGUAGE":
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"Going-concern phrase appears in {form} ({filed}) but "
                f"classification is ambiguous — {n_total} total matches, "
                f"{n_current} look current-period. Escalate for analyst "
                f"review of the specific text.",
                True)

    if sig == "NO_GOING_CONCERN":
        return ("PASS", m_value,
                f"No going-concern language in most recent {form} "
                f"(filed {filed}). 12-month survival not in question per "
                f"management/auditor disclosure.",
                False)

    return ("UNVERIFIABLE", m_value,
            f"going_concern_detector returned unexpected signal {sig!r}.",
            False)


def _score_revenue_concentration(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score a revenue_concentration result.

    Adjudicates 10-K concentration disclosures against industry norms +
    peer percentile.

    Signal → severity:
      DIVERSIFIED            → PASS (cleaner than TYPICAL)
      TYPICAL                → PASS (industry-standard distribution)
      CONCENTRATED           → MODERATE_UNDERDELIVERY
      SEVERELY_CONCENTRATED  → SEVERE_UNDERDELIVERY
      UNVERIFIABLE           → UNVERIFIABLE
    """
    sig = r.get("signal", "UNVERIFIABLE")
    by_axis = r.get("by_axis") or {}
    op_note = r.get("operational_diversification_note") or ""

    # Build M_value summary from axes
    axis_parts = []
    for axis_name, a in by_axis.items():
        pct = a.get("peer_percentile")
        pct_str = f"p{pct:.0f}" if pct is not None else "no-peers"
        axis_parts.append(f"{axis_name}={a['value']:.1f}%({a['tier']},{pct_str})")
    m_value = f"revenue_concentration: signal={sig} " + " ".join(axis_parts)

    if sig == "UNVERIFIABLE":
        return ("UNVERIFIABLE", m_value,
                "Need at least top_vehicle_pct or top_task_order_pct to "
                "adjudicate revenue concentration. The 10-K MD&A section "
                "typically discloses both in the Customer Concentration "
                "or Contract Vehicles discussion.",
                False)

    if sig == "DIVERSIFIED":
        return ("PASS", m_value,
                f"All concentration axes are below industry-median thresholds. "
                f"{r.get('_note','')}",
                False)

    if sig == "TYPICAL":
        # PASS — issuer is at the industry norm for federal services primes
        op_str = f" {op_note}" if op_note else ""
        return ("PASS", m_value,
                f"Concentration is within industry-standard distribution for "
                f"federal services primes — vehicle 12-30% and TO 4-10% is "
                f"the norm (peer median ~16% / ~4%). Not a concentration "
                f"risk.{op_str}",
                False)

    if sig == "CONCENTRATED":
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"One or more concentration axes exceeds the CONCENTRATED "
                f"threshold (vehicle ≥30% or TO ≥10%). "
                f"{r.get('_note','')} Loss-of-recompete on the concentrated "
                f"vehicle/TO would be material to forward revenue.",
                False)

    if sig == "SEVERELY_CONCENTRATED":
        return ("SEVERE_UNDERDELIVERY", m_value,
                f"One or more concentration axes exceeds the SEVERE "
                f"threshold (vehicle ≥50% or TO ≥20%). "
                f"{r.get('_note','')} Issuer's forward revenue is highly "
                f"exposed to a single contract/vehicle outcome.",
                False)

    return ("UNVERIFIABLE", m_value,
            f"revenue_concentration returned unexpected signal {sig!r}.",
            False)


def _score_ic_contracting_proxy(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score an ic_contracting_proxy result.

    Adjudicates an IC-revenue disclosure ($X, Y% of revenue) against the
    cleared-FTE benchmark + USAspending IC-agency floor.

    Signal → severity:
      CONSISTENT             → PASS (claim survives both the benchmark
                                envelope and the visible-floor sanity check)
      SUSPICIOUSLY_LOW       → PASS (under-claiming is not a fraud signal —
                                if anything, the issuer is being conservative)
      SUSPICIOUSLY_HIGH      → MODERATE_UNDERDELIVERY (claim materially
                                exceeds cleared-FTE economics — possible
                                segment-revenue inflation or unusual product mix)
      COVERAGE_INSUFFICIENT  → UNVERIFIABLE (visible USAspending floor too
                                small to ground-truth)
      UNVERIFIABLE           → UNVERIFIABLE (missing cleared_FTE input)
    """
    sig = r.get("signal", "UNVERIFIABLE")
    disclosed = r.get("disclosed_M")
    expected = r.get("expected_M")
    floor = r.get("visible_floor_M")
    by_agency = r.get("visible_by_agency") or {}
    rd_e = r.get("ratio_disclosed_to_expected")
    rv_d = r.get("ratio_visible_to_disclosed")

    m_value = (
        f"ic_contracting_proxy: signal={sig} disclosed=${disclosed}M "
        f"expected=${expected}M floor=${floor}M "
        f"d/e={rd_e:.2f}x" + (f" v/d={rv_d:.2f}x" if rv_d is not None else "")
        if expected else f"ic_contracting_proxy: signal={sig}"
    )

    if sig == "UNVERIFIABLE":
        return ("UNVERIFIABLE", m_value,
                "IC-revenue consistency check needs both disclosed IC revenue "
                "and cleared-headcount disclosure. The 10-K typically discloses "
                "cleared headcount in the Human Capital section. Without it, "
                "the benchmark envelope can't be computed.",
                False)

    if sig == "CONSISTENT":
        agencies_with_floor = [a for a, amt in by_agency.items() if amt > 0]
        return ("PASS", m_value,
                f"Disclosed IC revenue ${disclosed:,.0f}M is consistent with the "
                f"cleared-FTE benchmark envelope (${expected:,.0f}M, "
                f"{rd_e:.2f}× benchmark). USAspending visible floor "
                f"${floor:,.0f}M ({rv_d:.2f}× disclosed) from IC agencies "
                f"{agencies_with_floor}. The bulk of IC revenue is from "
                f"classified TOs that don't appear in unclassified spend "
                f"data, so a 30-50% visible-floor ratio is normal and "
                f"supports the disclosure.",
                False)

    if sig == "SUSPICIOUSLY_HIGH":
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"Disclosed IC revenue ${disclosed:,.0f}M is {rd_e:.2f}× the "
                f"cleared-FTE benchmark envelope of ${expected:,.0f}M (assumes "
                f"industry-standard 0.75 utilization × $145k revenue per "
                f"cleared FTE). Plausible explanations: unusually high "
                f"revenue-per-cleared-FTE mix (heavy delivery + product), "
                f"non-labor IC revenue (resale, hardware), or revenue "
                f"inflation. The benchmark is industry-standard not "
                f"company-specific so this is a flag for review, not a "
                f"falsification.",
                True)  # escalate

    if sig == "SUSPICIOUSLY_LOW":
        return ("PASS", m_value,
                f"Disclosed IC revenue ${disclosed:,.0f}M is {rd_e:.2f}× the "
                f"cleared-FTE benchmark envelope of ${expected:,.0f}M — under "
                f"the expected envelope. This is the conservative direction; "
                f"the issuer may be either under-disclosing IC mix (likely "
                f"intentional) or operating in lower-revenue-per-cleared-FTE "
                f"segments. Not a falsification signal.",
                False)

    if sig == "COVERAGE_INSUFFICIENT":
        return ("UNVERIFIABLE", m_value,
                f"USAspending visible IC-agency floor (${floor:,.0f}M) is "
                f"only {rv_d:.2f}× the disclosed revenue — too low to "
                f"ground-truth the claim. Either the issuer's IC mix is "
                f"weighted toward classified-task-order agencies (NSA/NRO/"
                f"CIA) that don't appear in unclassified spend data, or the "
                f"disclosure is inflated. The benchmark check passed, so "
                f"the claim is not falsified, but lower-confidence than "
                f"CONSISTENT.",
                False)

    return ("UNVERIFIABLE", m_value,
            f"ic_contracting_proxy returned unexpected signal {sig!r}.",
            False)


def _score_acq_coherence(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score an acq_coherence LLM result.

    Signal → severity:
      INCOHERENT_ROLLUP   → SEVERE_UNDERDELIVERY (canonical IONQ rollup tell)
      MIXED_COHERENCE     → MODERATE_UNDERDELIVERY (some related, some not)
      COHERENT_ROLLUP     → PASS (vertical integration / related M&A)
      NO_ACQUISITIONS     → PASS (no rollup to evaluate)
      LLM_UNAVAILABLE     → UNVERIFIABLE
    """
    sig = r.get("signal", "LLM_UNAVAILABLE")
    n_scored = r.get("n_acquisitions_scored", 0)
    mean_coh = r.get("mean_coherence")
    n_low = r.get("n_low_coherence", 0)
    n_synth = r.get("n_revenue_synthetic", 0)
    low_value = r.get("total_low_coherence_value", 0.0)
    m_value = (f"acq_coherence: n_scored={n_scored} mean={mean_coh!s} "
               f"n_low={n_low} n_synth={n_synth} signal={sig}")

    if sig == "LLM_UNAVAILABLE":
        return ("UNVERIFIABLE", m_value,
                f"LLM unavailable for acquisition coherence scoring "
                f"({r.get('error','no key configured')}). Cannot evaluate "
                f"rollup distraction risk.",
                False)

    if sig == "NO_ACQUISITIONS":
        return ("PASS", m_value,
                f"No acquisitions in window — no rollup-distraction pattern "
                f"to evaluate.",
                False)

    if sig == "INCOHERENT_ROLLUP":
        return ("SEVERE_UNDERDELIVERY", m_value,
                f"Acquisition pattern is INCOHERENT_ROLLUP: {n_low} of "
                f"{n_scored} recent acquisitions scored low-coherence "
                f"(<0.5) vs the parent's stated thesis; mean coherence "
                f"{mean_coh:.2f}. {n_synth} flagged as revenue-synthetic "
                f"(adding headline revenue from unrelated business). "
                f"Total low-coherence deal value: ${low_value/1e6:.0f}M. "
                f"This is the canonical IONQ-style rollup-distraction "
                f"signal — parent backfilling lost revenue with "
                f"acquisitions of incoherent businesses.",
                False)

    if sig == "MIXED_COHERENCE":
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"Mixed acquisition coherence: {n_low} of {n_scored} score "
                f"low-coherence vs the parent thesis; mean {mean_coh:.2f}. "
                f"Not yet a clear rollup pattern but worth tracking; "
                f"reviewer should examine which acquisitions diverge from "
                f"the core thesis.",
                True)

    if sig == "COHERENT_ROLLUP":
        return ("PASS", m_value,
                f"Acquisition pattern is COHERENT_ROLLUP: all {n_scored} "
                f"recent acquisitions score >=0.5 coherence vs the parent "
                f"thesis; mean {mean_coh:.2f}. Vertical integration / "
                f"related M&A, not rollup distraction.",
                False)

    return ("UNVERIFIABLE", m_value,
            f"acq_coherence returned unexpected signal {sig!r}.",
            False)


def _score_insider_vs_calendar(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score insider-sale × budget-calendar overlay.

    Signal → severity:
      CLUSTERED_DISCRETIONARY             → SEVERE_UNDERDELIVERY
        (validators 1+2 passed: issuer has program exposure AND at
         least one matched event's content references their programs)
      CLUSTERED_DISCRETIONARY_UNCONFIRMED → MODERATE_UNDERDELIVERY
        (insider distribution clustered around budget events but no
         program-level link to the events — likely temporal
         coincidence, not MNPI)
      PROXIMATE_DISCRETIONARY             → MODERATE_UNDERDELIVERY
      PROXIMATE_DISCRETIONARY_UNCONFIRMED → MODERATE_UNDERDELIVERY (escalate)
        (single-insider discretionary near budget event but no
         program link)
      ROUTINE_10B5_1                      → PASS
      NO_PROXIMATE_SALES                  → PASS
    """
    sig = r.get("signal", "NO_PROXIMATE_SALES")
    n_form4 = r.get("n_form4_filings", 0)
    n_prox = r.get("n_proximate_sales", 0)
    n_disc = r.get("n_discretionary_proximate", 0)
    n_owners = r.get("n_unique_owners_proximate", 0)
    prox_val = r.get("proximate_value_usd", 0)
    m_value = (f"insider_vs_calendar: n_form4={n_form4} n_prox={n_prox} "
               f"n_disc={n_disc} n_owners={n_owners} signal={sig}")

    if "error" in r:
        return ("UNVERIFIABLE", m_value,
                f"insider_vs_calendar error: {r['error']}",
                False)

    if sig == "NO_PROXIMATE_SALES":
        return ("PASS", m_value,
                f"No insider sales within ±{r.get('window_days', 14)} days of "
                f"any federal budget event in the lookback window. "
                f"({n_form4} Form 4 filings scanned.)",
                False)

    if sig == "ROUTINE_10B5_1":
        return ("PASS", m_value,
                f"{n_prox} insider sales found within budget-event windows "
                f"but all appear to be 10b5-1 pre-planned. Pre-planned "
                f"sales are not informative about MNPI-style timing.",
                False)

    if sig == "PROXIMATE_DISCRETIONARY":
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"{n_disc} discretionary (non-10b5-1) insider sale(s) within "
                f"±{r.get('window_days', 14)} days of a federal budget event "
                f"by {n_owners} insider(s); proximate sale value "
                f"~${prox_val/1e6:.1f}M. Single-insider proximate sales can "
                f"be coincidence; flag for follow-up to check what budget "
                f"action the sale fell near.",
                True)

    if sig == "CLUSTERED_DISCRETIONARY":
        events = r.get("matched_events") or []
        ev_str = "; ".join(f"{e['event_date']} ({e['event_type']}) {e['n_discretionary']} sales"
                            for e in events[:3])
        vm = r.get("validator_meta") or {}
        links = vm.get("event_program_links") or []
        link_str = "; ".join(f"{l['event_date']}→{l['matched_token']}" for l in links[:3])
        return ("SEVERE_UNDERDELIVERY", m_value,
                f"{n_disc} discretionary insider sales within ±"
                f"{r.get('window_days', 14)} days of federal budget events "
                f"by {n_owners} different insiders; proximate value "
                f"~${prox_val/1e6:.1f}M. Top matched events: {ev_str}. "
                f"Validators passed: issuer has named-program exposure AND "
                f"event content references their programs ({link_str}). "
                f"This is the canonical IONQ-pattern signal.",
                False)

    if sig == "CLUSTERED_DISCRETIONARY_UNCONFIRMED":
        vm = r.get("validator_meta") or {}
        reason = vm.get("downgrade_reason", "validator failed")
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"{n_disc} discretionary insider sales by {n_owners} "
                f"different insiders within ±{r.get('window_days', 14)} "
                f"days of federal budget events; proximate value "
                f"~${prox_val/1e6:.1f}M. BUT: {reason}. The temporal "
                f"clustering is real but the issuer-specific MNPI link "
                f"isn't substantiated — common when sales coincide with "
                f"earnings, vesting cycles, or special dividends rather "
                f"than budget-driven MNPI. Treat as yellow flag, not "
                f"red. Investigate sale-vs-earnings-date proximity.",
                True)  # escalate for analyst review

    if sig == "PROXIMATE_DISCRETIONARY_UNCONFIRMED":
        vm = r.get("validator_meta") or {}
        reason = vm.get("downgrade_reason", "validator failed")
        return ("MODERATE_UNDERDELIVERY", m_value,
                f"{n_disc} discretionary insider sale(s) within budget-event "
                f"window but {reason}. Likely temporal coincidence; treat "
                f"as yellow flag pending earnings-date overlap check.",
                True)

    return ("UNVERIFIABLE", m_value,
            f"insider_vs_calendar returned unexpected signal {sig!r}.",
            False)


def _score_nasa_ntrs(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score NASA NTRS results.

    NASA collaboration is asymmetric:
      PRESENT (n_filtered > 0) → PASS (NASA published evidence)
      ABSENT  (n_filtered == 0) → UNVERIFIABLE if claim asserts NASA
        collaboration but doesn't claim specific NASA programs/awards
        (NASA work may be ITAR/EAR-restricted). MODERATE if claim
        names specific NASA centers/programs that should produce
        public technical output.
    """
    n = r.get("n_filtered", 0)
    total = r.get("total", 0)
    sig = r.get("signal")
    centers = list((r.get("by_center") or {}).keys())[:3]
    m_value = (f"nasa_ntrs: n={n} (raw={total}) top_centers={centers} "
               f"signal={sig}")

    claim_text_lc = (claim.get("claim_text") or "").lower()
    specific_programs = any(kw in claim_text_lc for kw in (
        "nasa program", "nasa contract", "nasa-funded", "nasa partner",
        "nasa-sponsored", "nasa task order", "nasa technology transition",
    ))

    if sig == "NASA_PUBLISHED":
        return ("PASS", m_value,
                f"NASA NTRS returned {n} citations after word-boundary "
                f"filter (raw {total}). Centers: {centers}. NASA "
                f"collaboration corroborated.",
                False)

    if specific_programs:
        return ("MODERATE_UNDERDELIVERY", m_value,
                "Claim names a specific NASA program / partnership but "
                "no NTRS technical-output citations match. Either the work "
                "is ITAR-restricted (real but not publicly published) or "
                "the claim overstates the depth of NASA engagement. "
                "Escalate for LLM review against usaspending NASA awards.",
                True)

    return ("UNVERIFIABLE", m_value,
            "0 NTRS citations — NASA work may exist via SBIR/task-order "
            "without publicly-published technical output. Cross-check with "
            "usaspending NASA awards for confirmed funding.",
            False)


def _score_dol_h1b_lca(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score a DOL H-1B LCA result.

    Calibrated from spike (FY2024 Q4 sample): FAANG = 1000s, Tesla
    = 483, Intel = 488, biotech (Moderna) = 6, semis (KLIC) = 4,
    most small-cap drone/refrigerant/hazwaste = 0.

      REGISTERED_H1B_SPONSOR (>=10 worker positions) → PASS
      SMALL_SPONSOR (<10 positions) + large-workforce claim → MODERATE
      SMALL_SPONSOR (<10 positions) + ordinary claim → UNVERIFIABLE
      NO_LCA_FOOTPRINT + claim is in H-1B-dense industry → MODERATE
      NO_LCA_FOOTPRINT + claim references US-citizen/cleared work
        OR refrigerant/hazwaste/heavy-industrial → UNVERIFIABLE
      NO_LCA_FOOTPRINT (default) → UNVERIFIABLE (could be honest)
    """
    sig = r.get("signal")
    n_lcas = r.get("n_filings", 0)
    n_workers = r.get("n_worker_positions", 0)
    top_soc = list((r.get("by_soc_title") or {}).keys())[:1]
    m_value = (f"dol_h1b_lca: n_lcas={n_lcas} workers={n_workers} "
               f"top_soc={top_soc} signal={sig}")

    if sig == "NO_DATA_AT_CUTOFF":
        return ("UNVERIFIABLE", m_value,
                f"DOL LCA file has no decisions on or before the cutoff "
                f"(data range {r.get('data_min_date')} → "
                f"{r.get('data_max_date')}). Cannot retroactively verify "
                f"H-1B sponsorship at this cutoff.",
                False)

    claim_text_lc = (claim.get("claim_text") or "").lower()
    cohort_context = (claim.get("cohort_context") or "").lower()
    is_cleared_work = any(kw in claim_text_lc + cohort_context
                          for kw in _DEFENSE_KEYWORDS)
    is_large_workforce_claim = any(kw in claim_text_lc
                                    for kw in _LARGE_WORKFORCE_KWS)

    if sig == "REGISTERED_H1B_SPONSOR":
        return ("PASS", m_value,
                f"DOL H-1B LCA registry returned {n_lcas} certified filings "
                f"covering {n_workers} worker positions. Top SOC: "
                f"{top_soc[0] if top_soc else '—'}. Workforce-at-worksite "
                f"claim corroborated.",
                False)

    if sig == "SMALL_SPONSOR":
        if is_large_workforce_claim:
            return ("MODERATE_UNDERDELIVERY", m_value,
                    f"Claim asserts large workforce but only {n_workers} "
                    f"H-1B LCA positions filed. Sub-scale relative to the "
                    f"language used. Escalate for LLM review.",
                    True)
        return ("UNVERIFIABLE", m_value,
                f"Real but small H-1B sponsorship ({n_workers} positions) — "
                f"ambiguous band; honest small operation or sub-scale "
                f"relative to claim language. Compare to claim wording.",
                True)

    if sig == "NO_LCA_FOOTPRINT":
        if is_cleared_work:
            return ("UNVERIFIABLE", m_value,
                    "0 H-1B LCA filings, but the claim references "
                    "cleared/US-citizen work where H-1B sponsorship is "
                    "structurally rare. Absence is the expected baseline.",
                    False)
        if is_large_workforce_claim:
            return ("MODERATE_UNDERDELIVERY", m_value,
                    "0 H-1B LCAs for a claim asserting large workforce in "
                    "an H-1B-eligible industry. Either the workforce is "
                    "100% US citizens (rare at claimed scale) or the "
                    "claim is inflated.",
                    True)
        return ("UNVERIFIABLE", m_value,
                "0 H-1B LCAs — could be a small operation, a US-citizen-"
                "only workforce, or a foreign-staffed entity. Coverage "
                "gap rather than contradiction.",
                False)

    return ("UNVERIFIABLE", m_value,
            "dol_h1b_lca result missing signal field; not adjudicatable.",
            False)


def _score_osha_establishments(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score an OSHA Form 300A establishment search.

    Calibrated as a CORROBORATION source — presence at scale = strong
    PASS; absence is mostly UNVERIFIABLE because of the 20-employee
    threshold + low-injury-rate exemption (real small-cap drone/biotech/
    electronics operations don't file 300A).

    Exceptions where absence becomes MODERATE:
      - Claim text asserts large-headcount manufacturing (e.g.
        '1,000-employee facility', 'major US manufacturer', 'Fortune
        500', 'largest', 'thousand-strong workforce') → absence then
        DOES contradict the language.
    """
    n = r.get("n_matches", 0)
    emps = r.get("total_employees", 0)
    sig = r.get("signal", "?")
    top_naics = list((r.get("naics_breakdown") or {}).items())[:2]
    data_years = r.get("data_years") or []
    cutoff_year = r.get("cutoff_year")
    m_value = (f"osha: n_est={n} total_emps={emps} top_naics={top_naics} "
               f"signal={sig}")

    if sig == "NO_DATA_AT_CUTOFF":
        return ("UNVERIFIABLE", m_value,
                f"OSHA 300A file has no rows with year_filing_for <= "
                f"{cutoff_year}; available years: {data_years}. Cannot "
                f"retroactively verify operations at this cutoff — the "
                f"only signal would require a contemporaneous data snapshot.",
                False)

    if sig == "REGISTERED_EMPLOYER":
        return ("PASS", m_value,
                f"OSHA 300A returned {n} establishment(s) with {emps} total "
                f"employees under the queried name — operational scope "
                f"corroborated.",
                False)

    claim_text_lc = (claim.get("claim_text") or "").lower()
    large_workforce_kws = (
        "thousand", "1,000", "5,000", "10,000", "largest", "major u.s.",
        "fortune 500", "fortune-500", "national manufacturer",
        "industrial-scale", "mass production",
    )
    asserts_large = any(kw in claim_text_lc for kw in large_workforce_kws)

    if sig == "NO_OSHA_FOOTPRINT":
        if asserts_large:
            return ("MODERATE_UNDERDELIVERY", m_value,
                    "Claim asserts large/thousand-person manufacturing but "
                    "OSHA 300A returns 0 establishments — a large-employer "
                    "claim should produce filings. Escalate for LLM review "
                    "on whether the absence is genuine or a subsidiary-name "
                    "search gap.",
                    True)
        return ("UNVERIFIABLE", m_value,
                "0 OSHA 300A establishments — but the 300A roster excludes "
                "sub-20-employee operations and low-injury-rate industries "
                "(common for small-cap drone/biotech/electronics). Absence "
                "is not informative unless the claim implies large workforce.",
                False)

    if sig == "SMALL_EMPLOYER":
        return ("UNVERIFIABLE", m_value,
                f"OSHA found {n} establishment(s) with only {emps} total "
                f"employees — sub-50 scale is the ambiguous band. Honest "
                f"small operation or sub-scale relative to a large claim; "
                f"LLM needed to compare claim language to headcount.",
                True)

    return ("UNVERIFIABLE", m_value,
            "OSHA 300A result lacks a recognized signal field.",
            False)


def _score_megacap_namecheck(claim: dict, r: dict) -> tuple[str, str, str, bool]:
    """Score a claim adjudicated by megacap_namecheck.query_megacap_mentions.

    Asymmetric counterparty-disclosure test from the megacap side:
      - signal=INFLATION_SUSPECT (0 hits across N megacaps) + claim is
        a commercial counterparty claim → MODERATE (megacap-side
        absence at scale is a real signal, but weaker than federal-
        registry absence; the megacap can have many real sub-material
        relationships that don't surface in filings)
      - signal=SUB_MATERIAL_RELATIONSHIP (1-2 hits) → UNVERIFIABLE
        (ambiguous band — can't tell real-sub-material from inflated)
      - signal=RECURRING_RELATIONSHIP (3+ hits) → PASS
    """
    sig = r.get("signal")
    total = r.get("total_hits_across_megacaps", 0)
    n_with = r.get("n_megacaps_with_hits", 0)
    by_mc = r.get("by_megacap") or {}
    n_queried = len(by_mc)
    m_value = (f"megacap_namecheck: {total} total hits across {n_queried} megacaps "
               f"({n_with} with any hits)")

    if sig == "INFLATION_SUSPECT":
        if n_queried >= 2:
            return ("MODERATE_UNDERDELIVERY", m_value,
                    f"0 mentions across {n_queried} megacap SEC filings (10-K/Q + 8-K) "
                    f"over 10 years. None of the named megacap counterparties have ever "
                    f"referenced this small-cap in their own filings. Likely inflation: "
                    f"either fabricated or a sub-material relationship being described as "
                    f"a 'partnership'/'deployment'/'program' that would normally surface "
                    f"in an earnings-call transcript at any material scale.",
                    False)
        return ("UNVERIFIABLE", m_value,
                "Only 1 megacap queried with 0 hits; single-counterparty absence is "
                "noisy. Re-query against additional plausible megacaps to disambiguate.",
                False)

    if sig == "SUB_MATERIAL_RELATIONSHIP":
        return ("UNVERIFIABLE", m_value,
                f"{total} megacap mention(s) — ambiguous band. Could be a real "
                "sub-material partnership (e.g. warrants / channel arrangement) or an "
                "alleged inflation. Megacap-side count alone cannot disambiguate; "
                "additional signals (joint patents, customer-concentration disclosure, "
                "earnings-call text) needed.",
                True)

    if sig == "RECURRING_RELATIONSHIP":
        return ("PASS", m_value,
                f"{total} hits across {n_with} megacap(s) — real ecosystem-partner "
                "cadence corroborates the claim.",
                False)

    return ("UNVERIFIABLE", m_value,
            "megacap_namecheck result lacks the signal field; not adjudicatable.",
            False)


# Worst-signal-wins priority. PASS beats UNVERIFIABLE because confirmation
# from any M-source is more informative than "we couldn't test."
_SEVERITY_PRIORITY = {
    "SEVERE_UNDERDELIVERY":   4,
    "RED_FLAG_NEGATIVE":      3,
    "MODERATE_UNDERDELIVERY": 2,
    "PASS":                   1,
    "UNVERIFIABLE":           0,
}


def _score_single_result(
    claim: dict, r: dict, *, focal_cik: str | None
) -> tuple[str, str, str, str, bool]:
    """Adjudicate one (claim, result) pair → (severity, label, M_value,
    interpretation, escalation_needed). Pure: no aggregation, no I/O."""
    status = claim.get("m_source_status", "NONE")
    label = r.get("label", "")
    res = r.get("result") or {}

    if status == "PROPOSED" and label == "proposed_not_promoted":
        prop = r.get("proposed") or ""
        return ("UNVERIFIABLE",
                f"{prop} (proposed, not promoted)",
                "—",
                f"Proposed connector '{prop}' not yet built; intentional coverage acknowledgement, not failure.",
                False)

    if status == "NONE" or label == "structural_none":
        return ("UNVERIFIABLE",
                "structural_none",
                "—",
                "Claim is not externally adjudicatable by any registry; structurally UNVERIFIABLE.",
                False)

    if isinstance(res, dict) and "error" in res and res["error"]:
        return ("UNVERIFIABLE", label, f"error: {res['error']}",
                "M-source returned an error; cannot adjudicate this run.",
                False)

    if "fdic_call_reports.consumer_loan_originations" in label:
        sev, mv, interp, esc = _score_fdic_multi(claim, res)
    elif "fdic_call_reports" in label:
        sev, mv, interp, esc = _score_fdic(claim, res)
    elif "fdic_bankfind" in label:
        sev, mv, interp, esc = _score_fdic_bankfind(claim, res)
    elif "finra_brokercheck" in label:
        sev, mv, interp, esc = _score_finra(claim, res)
    elif "sec_filings" in label:
        sev, mv, interp, esc = _score_sec_filings(claim, res)
    elif "claim_evolution" in label:
        sev, mv, interp, esc = _score_claim_evolution(claim, res)
    elif "edgar_fts" in label:
        sev, mv, interp, esc = _score_edgar_fts(claim, res, focal_cik=focal_cik)
    elif "epa_emissions" in label:
        sev, mv, interp, esc = _score_epa_emissions(claim, res)
    elif "uspto" in label:
        sev, mv, interp, esc = _score_uspto(claim, res)
    elif "usaspending.query_federal_presence" in label:
        sev, mv, interp, esc = _score_usaspending_presence(claim, res)
    elif "megacap_namecheck" in label:
        sev, mv, interp, esc = _score_megacap_namecheck(claim, res)
    elif "sam_entity" in label:
        sev, mv, interp, esc = _score_sam_entity(claim, res)
    elif "osha_establishments" in label:
        sev, mv, interp, esc = _score_osha_establishments(claim, res)
    elif "dol_h1b_lca" in label:
        sev, mv, interp, esc = _score_dol_h1b_lca(claim, res)
    elif "bls_qcew" in label:
        sev, mv, interp, esc = _score_bls_qcew(claim, res)
    elif "nasa_ntrs" in label:
        sev, mv, interp, esc = _score_nasa_ntrs(claim, res)
    elif "ucc_proxy" in label:
        sev, mv, interp, esc = _score_ucc_proxy(claim, res)
    elif "pentagon_jbook" in label:
        sev, mv, interp, esc = _score_pentagon_jbook(claim, res)
    elif "acq_coherence" in label:
        sev, mv, interp, esc = _score_acq_coherence(claim, res)
    elif "insider_vs_calendar" in label:
        sev, mv, interp, esc = _score_insider_vs_calendar(claim, res)
    elif "earmark_detector" in label:
        sev, mv, interp, esc = _score_earmark_detector(claim, res)
    elif "cybercom_budget" in label:
        sev, mv, interp, esc = _score_cybercom_budget(claim, res)
    elif "ic_contracting_proxy" in label:
        sev, mv, interp, esc = _score_ic_contracting_proxy(claim, res)
    elif "revenue_concentration" in label:
        sev, mv, interp, esc = _score_revenue_concentration(claim, res)
    elif "going_concern" in label:
        sev, mv, interp, esc = _score_going_concern(claim, res)
    elif "auditor_change" in label:
        sev, mv, interp, esc = _score_auditor_change(claim, res)
    else:
        sev, mv, interp, esc = ("UNVERIFIABLE", f"{label}",
                                "No deterministic scorer for this source — needs LLM revisit.",
                                False)
    return (sev, label, mv, interp, esc)


def score_claim(claim: dict, results: list[dict], *, focal_cik: str | None = None) -> dict:
    """Aggregate over ALL results attached to a claim — worst severity wins,
    escalation = any True, supports/M_value combined across results.

    Earlier versions read only `results[0]`, which silently dropped any
    additional M-source result the planner attached (e.g. a B2-style EPA
    audit appended alongside an existing edgar_fts adjudication, or any
    future multi-source plan). The fix preserves the existing single-result
    behavior while making multi-result claims honest."""
    cid = claim["claim_id"]
    if not results:
        results = [{}]

    scored = [_score_single_result(claim, r, focal_cik=focal_cik) for r in results]
    # Pick the highest-priority severity; tie-break by first occurrence.
    best = max(scored, key=lambda s: _SEVERITY_PRIORITY.get(s[0], 0))
    severity = best[0]

    supports = [s[1] for s in scored if s[1]]
    m_values = " | ".join(s[2] for s in scored if s[2] and s[2] != "—") or "—"
    interpretation = best[3]
    escalation_needed = any(s[4] for s in scored)

    return {
        "claim_id":          cid,
        "claim_text":        claim.get("claim_text", "")[:300],
        "severity":          severity,
        "supports":          supports,
        "M_check":           best[1],
        "M_value":           m_values,
        "interpretation":    interpretation,
        "escalation_needed": escalation_needed,
    }


def _focal_cik_from_filing(plan: dict) -> str | None:
    """Filing accession lives in plan['filing'], e.g. '0001801169-26-000010_10-K.txt'.
    The 10-digit prefix is the filer CIK."""
    f = plan.get("filing") or ""
    head = f.split("-")[0]
    if head.isdigit() and len(head) == 10:
        return head
    return None


def score_ticker(ticker: str, *, data_dir: Path | None = None) -> dict:
    base = Path(data_dir) if data_dir else LOCAL
    plan_path = base / f"{ticker}.plan.json"
    qry_path  = base / f"{ticker}.queries.json"
    if not plan_path.exists() or not qry_path.exists():
        return {"error": f"missing inputs for {ticker}"}
    plan = json.loads(plan_path.read_text())
    qry  = json.loads(qry_path.read_text())
    focal_cik = _focal_cik_from_filing(plan)
    scores: list[dict] = []
    for claim in plan.get("claims", []):
        cid = claim["claim_id"]
        results = qry.get("results", {}).get(cid, [])
        scores.append(score_claim(claim, results, focal_cik=focal_cik))
    out = {"ticker": ticker, "scores": scores}
    (base / f"{ticker}.scores.json").write_text(json.dumps(out, indent=2, default=str))
    counts: dict[str, int] = {}
    for s in scores:
        counts[s["severity"]] = counts.get(s["severity"], 0) + 1
    return {
        "ticker": ticker,
        "n_claims": len(scores),
        "counts": counts,
    }


def main():
    if len(sys.argv) < 2:
        print("usage: python3 -m verticals.public_co.deterministic_scorer TICKER [TICKER ...]", file=sys.stderr)
        sys.exit(2)
    for tk in sys.argv[1:]:
        r = score_ticker(tk.upper())
        if "error" in r:
            print(f"  {tk}: {r['error']}")
            continue
        ord = ["PASS", "MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY", "RED_FLAG_NEGATIVE", "UNVERIFIABLE"]
        parts = [f"{k[:4]}={r['counts'].get(k,0)}" for k in ord]
        print(f"  {r['ticker']}: {r['n_claims']} claims, " + " ".join(parts))


if __name__ == "__main__":
    main()
