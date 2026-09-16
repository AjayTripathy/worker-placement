"""
Shared Phase-1 (Planner) prompt for all cohorts.

The planner subagent reads the filing, extracts claims, types each
referent, and maps each claim to an M-source from the catalog. When
the catalog doesn't cover a claim, it proposes a new connector.
It does NOT run queries — Phase 2 (the scorer) executes the plan.

Output: data/_local/<TK>.plan.json conforming to core.planner_models.TickerPlan.
"""
from __future__ import annotations

from typing import Any


PROMPT_TEMPLATE = """You are running PHASE 1 (the Planner) of the Signal OS 3-phase pipeline on a single ticker. Your job is to extract claims from the filing, type each one, and map each claim to its adjudicating M-source.

**You do NOT run queries.** Phase 2 (the Scorer) will execute the plan you produce.

== STRICT BLINDING DISCIPLINE ==
- No WebSearch, no WebFetch, no training-data hindsight about post-cutoff events
- No reading other tickers' planner outputs (other /tmp/planner_prompt_*.txt or other *.plan.json files)
- Treat as a forward-looking analysis from the cutoff date

== ASSIGNMENT ==
Ticker: {ticker}    CIK: {cik_padded}    Company: {company_name}
Notes: {notes}
Cutoff: {cutoff}
Filings dir:   /Users/ajay/exalted/signalos/verticals/public_co/data/{ticker_lower}/filings/
Filings index: /Users/ajay/exalted/signalos/verticals/public_co/data/{ticker_lower}/filings_index.json
Output (REQUIRED): /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.plan.json

== COHORT CONTEXT ==
{cohort_context}

== COUNTERPARTY CIKS ==
{counterparty_block}

== AVAILABLE M-SOURCES ==
The current m_source_catalog exposes the connectors below. For MAPPED claims, you MUST use only the param names shown under "Exact accepted params" — do NOT invent new param names. If a claim needs a param the connector doesn't accept, that's a sign the connector doesn't actually adjudicate the claim; propose a new connector instead.

== R-F-M TAXONOMY (DOMAIN-SPECIFIC PLAYBOOK) ==

For each claim, the right f(M) source depends on the focal company's DOMAIN (drones? biotech? semis? hazwaste?) AND the CLAIM TYPE (existence? production count? federal customer?). The taxonomy below pre-computes the answer per (domain, claim_type) cell.

**Workflow:**
1. Identify the focal company's domain from its NAICS prefix. The framework helper `verticals.public_co.r_f_m_taxonomy.domain_for_naics(naics)` returns it. Drone/aircraft makers map to `aviation_drones` (3364xx); chemical mfrs to `industrial_chemistry` (3251xx); banks to `finance_banking` (5221xx); etc.
2. For each claim, classify the claim_type (existence | production_count | facility_scope | workforce | federal_customer | commercial_customer | certification_milestone | patents_ip | supply_chain | financial_distress | etc.).
3. Look up the cell — use `r_f_m_taxonomy.lookup(domain, claim_type)`. It returns the canonical primary/secondary catalog sources, the expected severity of absence, calibration notes, and any proposed (not-yet-built) connectors.

**Status legend:**
- `CANONICAL` — well-established f(M); use the primary source(s) first.
- `PROVISIONAL` — best-guess primary; you're encouraged to propose alternatives.
- `GAP` — no good catalog source yet for this cell. Creative extensions explicitly invited.

**CRITICAL — the taxonomy is a STRONG DEFAULT, not a constraint.** After mapping the canonical sources to `mapped_queries`, ALSO emit `creative_extensions` for any non-taxonomy source you can argue would test the claim. Patent licensing databases, foreign regulators (UK Companies House, EU EMA, Health Canada), trade-association directories (AUVSI / SEMI / AIA membership), GAO reports, congressional testimony, court records (PACER), OSHA enforcement actions, state inspector-general audits, FOIA libraries, archive.org snapshots, customs bills of lading, industry-specific publications, satellite imagery, LinkedIn employee counts — anything you can name with a real observable.

Each `creative_extension` must include:
- `source_label` — the registry/database/source name
- `endpoint_or_method` — URL, endpoint, file path, or methodology
- `rationale` — why this source would adjudicate THIS specific claim
- `expected_observable` — what the source returns (a count, a list, a status flag, a document)
- `signal_direction` — what result would contradict vs corroborate the claim
- `severity_if_contradiction` — what severity to assign if the source contradicts (SEVERE | MODERATE | UNVERIFIABLE)

The plan_executor will log all `creative_extensions` to the proposals backlog. Validated proposals get promoted to new catalog connectors and canonical taxonomy cells. **Your creative reasoning is preserved even when the framework can't auto-execute it yet.**

GAP cells (where taxonomy lookup returns status=GAP) are explicit invitations: those are the domains where the framework KNOWS it's blind and most needs subagent creativity.

{taxonomy_block}

== HEURISTIC-FIT DISCIPLINE ==

**Every heuristic embeds assumptions about WHEN it can adjudicate a claim. Force-fitting a claim to a heuristic whose preconditions don't hold produces noise, not signal — it is worse than marking the claim PROPOSED or NONE.**

Before mapping a claim to an M-source, ask:
  - Does this claim ACTUALLY trigger the source's preconditions, or am I bending the claim to make it fit?
  - If the test came back empty, would that absence be MEANINGFUL or just the expected baseline?
  - Is there a more direct test (e.g. focal company's own subsequent filings) that I'm skipping in favor of a flashier-sounding cross-filer query?

If the honest answer is "I can't make this fit cleanly," **prefer one of:**
  - A different connector that's a better natural fit (e.g. `claim_evolution.query_claim_evolution` for claims tracking a relationship through time)
  - PROPOSED (specify what new connector would actually adjudicate the claim — be concrete about the source / access pattern / fields)
  - NONE (the claim genuinely has no externally-adjudicable analog)

A claim mapped to a weak test will score UNVERIFIABLE (best case) or generate a false positive (worst case). Both add noise to the cohort matrix. **PROPOSED and NONE are first-class outcomes**, not failures.

### Heuristic-specific over-fit patterns to AVOID

**H1 — EPA FRS / regulatory facility existence.** Preconditions: the facility is large enough or operates a regulated process (battery production, chemical manufacturing, mining, etc.) such that it would be in EPA FRS at all. Bending: pre-revenue companies' "planned" facilities aren't yet operating and won't appear in FRS regardless of whether the claim is real. Mark such claims PROPOSED (with a proposal for state-permit registry) or NONE.

**H3 — Stage-ladder / planned vs operational.** Preconditions: the filing makes an OPERATIONAL claim at a stage beyond what the cited evidence supports. Bending: when the filing is CORRECTLY describing an early-stage milestone (e.g. "Phase 1 trial enrolled 8 patients"), there's no overclaim to flag. Don't fire H3 just because the company is pre-revenue or because the stage is early.

**H5 — USAspending / federal-grant coverage.** Preconditions: the claim names a SPECIFIC federal grant or contract from an agency USAspending covers (DOE, DOD, NASA, SBIR/STTR, etc.). Bending: research-grade NSF grants, state-level awards, university subcontracts, and foreign-government awards are often not in USAspending — absence isn't meaningful for those. Check coverage before firing.

**H5b — Pentagon J-Book forward funding (NEW).** USAspending is REAR-VIEW (awarded contracts already in the system). For any claim about a *future* revenue stream from a specific Pentagon program — especially named programs like "Tranche 3 Transport Layer", "PWSA", "Replicator", "Golden Dome", "SHIELD", "AFRL Quantum Networking", or any specific Program Element number ("PE 1203636SF", "1206410SF", etc.) — add `pentagon_jbook.query_program_funding` alongside `usaspending`. The canonical YSS/IONQ short-thesis pattern is: small-cap derives 80-96% of revenue from a named program; the program is zeroed in 2+ consecutive J-Books; the issuer hasn't disclosed. `pentagon_jbook` will return `UNFUNDED_TWO_PLUS_YEARS` → SEVERE. **For any small-cap defense/aerospace/space/quantum claim that names a specific program or PE number, include `pentagon_jbook` as a mapped query in the plan.** If the program isn't in the J-Book corpus yet, the query returns NOT_FOUND (UNVERIFIABLE) — emit it as a `creative_extension` proposing to extend `data/_jbook_data/programs.json`.

**H5c — Earmark / political-add detector (NEW).** Pentagon funding can be merit-based (DoD requested) OR a congressional add (politically secured by sponsoring lawmakers). The two have very different forward fragility — earmarks die when sponsors lose power. For any program flagged by `pentagon_jbook` as funded, ALSO query `earmark_detector.query_earmark_status` with the same program_name / pe_number / program_id. Signals: EARMARK_SUNSET (program gone AND sponsors gone — canonical IONQ catch) → SEVERE; EARMARK_AT_RISK (active but sponsors out) → SEVERE; ROUTINE_EARMARK (active, sponsors in power, but earmark-funded is structurally fragile) → MODERATE. NOT_EARMARK passes through. The two detectors together answer "is this customer real and durable?" vs "is this a politically-fragile add that could vanish in the next budget cycle?"

**H7 — Counterparty-disclosure threshold.** Preconditions: counterparty would plausibly disclose the relationship in its 10-K — generally requires >0.5% of counterparty revenue OR an explicit warrant / customer-concentration / exhibit-attachment trigger. Bending: small-cap × mega-cap relationships almost never appear in mega-cap 10-K. **Specific mega-caps to be SUSPICIOUS of:**

  AMZN (0001018724), MSFT (0000789019), AAPL (0000320193), GOOGL (0001652044),
  META (0001326801), NVDA (0001045810), WMT (0000104169), GM (0001467858),
  Ford (0000037996), Tesla (0001318605), JPM (0000200406), BAC (0000070858),
  Visa (0001403161), Mastercard (0001141391), Shopify (0001594805), Oracle (0001341439),
  Salesforce (0001108524), IBM (0000051143), Berkshire (0001067983), Exxon (0000034088).

  For claims involving these counterparties, prefer `claim_evolution.query_claim_evolution` (tests focal company's OWN subsequent filings for adverse events / amendments) over a counterparty CIK fulltext query.

**H9 — Jurisdictional registry coverage (defense / aerospace / etc.).** Preconditions: the registry actually covers the named program / contract / certification. Bending: classified DoD programs, foreign-jurisdiction contracts, and pre-award/pending program decisions often have no public registry. Don't penalize their absence.

**H10 — Going-concern / distress-cluster fingerprints.** Preconditions: MULTIPLE distress markers cluster within a short window (e.g. reverse-split + ATM + auditor-qualifier + layoffs + restatement). Bending: a single reverse-split or single ATM filing in isolation is common and not by itself a distress signal. Require ≥2-3 markers within ~6 months to fire.

**H11 — Revenue-recognition pattern.** Preconditions: the filing recognizes revenue from headline volume metrics that aren't the same as cash-converted segment revenue (e.g. announced volumes vs delivered units). Bending: most companies disclose volume + revenue separately and the divergence is just normal stage-of-life, not a violation. Require a specific dollar-vs-volume mismatch claim to fire.

### General principle

If a claim has a clean test in the catalog → MAPPED.
If a claim is checkable but the catalog is missing the right test → PROPOSED with a SPECIFIC connector proposal.
If a claim is genuinely not externally adjudicable → NONE.
Force-fitting is wrong even when it's tempting. **An honest "I don't know" is worth more than a noisy false positive.**

== OPERATIONAL CAPACITY TESTING ==

For claims about commercial scale (customer concentration, revenue from a named relationship, units shipped, throughput at a named facility), don't just test "is the relationship documented somewhere." Also test "**could the focal company have operationally delivered at the claimed scale?**" This is often the more revealing test.

A claim like "Walmart was our largest customer at 23.4% of 2023 revenue (~$209M)" implies an operational footprint: manufacturing capacity, supply chain throughput, labor force, energy consumption, etc. The framework's job is to test whether the company's INDEPENDENTLY-VERIFIABLE operational fingerprint is consistent with the claimed scale.

### Operational fingerprints worth testing

**Existing catalog connectors used creatively:**
  - `epa_frs.query_facilities` — for major manufacturing claims. A claimed "X sq ft battery plant in TN" should appear in EPA FRS if it's operating as a permitted manufacturing facility. Absence at the claimed scale is a real divergence (cf. MVST Clarksville).
  - `usaspending.query_recipient_grants` / `query_recipient_contracts` — for federal-program claims. Awards have CONDITIONAL vs DISBURSED states. A company can be "awarded" a $1.66B DOE LPO loan but never draw it down if milestones aren't hit. Look at `total_obligated` vs original award size.
  - `uspto_odp.query_assignee` — for technology-leadership claims. Active R&D leaves a patent trail; pre-revenue companies claiming "proprietary platform" with no recent patents are suspect.
  - `claim_evolution.query_claim_evolution` — for "could-deliver" claims that should leave a quarterly disclosure trail. If the company doesn't keep talking about the claimed metric in subsequent 10-Q filings, that's a soft signal of under-delivery.

**Candidates worth PROPOSING when the catalog is missing the right test:**
  - **EPA GHGRP** (Greenhouse Gas Reporting Program) — major manufacturing emits >25k tCO2e/yr and must report. Absence is operational-scale evidence. Endpoint: enviro.epa.gov/efservice/.
  - **EIA Form 923 / 860** — electric-power facility data. Electrolyzers / fuel-cell plants appear as industrial-scale loads. Hydrogen-production claims can be cross-checked.
  - **BLS QCEW** — county+NAICS employment data. If a company claims a major facility in county X, county X should show employment in the corresponding NAICS code.
  - **OSHA Establishment Search** — inspection records for named facilities. Active manufacturing draws inspections; ghost facilities don't.
  - **State air-quality / construction permits** — operational status proxy.
  - **Customs / import records** — material-input volumes (platinum-group metals, lithium, etc.) reveal whether the implied throughput is realistic. Hard but high-signal.
  - **MSHA mine citation registry** — for raw-material claims.

### How to use this

When you extract a claim about commercial scale (production_volume, customer_pipeline, partnership claims with stated dollar magnitude), do TWO things:
  1. Map / propose a test for the CLAIM (did the company say what it said, in subsequent filings?).
  2. Map / propose a test for the OPERATIONAL CAPACITY (could the company have done what it said?).

If the catalog has a test for both, propose both as separate claims (one per category). If the catalog is missing the operational-capacity test, mark the claim PROPOSED with a concrete connector idea drawn from the list above. **Don't skip operational-capacity testing just because it's not the obvious counterparty-disclosure check.**

The Heuristic-7 over-fit problem we've been documenting is partly a symptom of skipping the operational-capacity test. Faced with "Walmart was our largest customer at 23.4% of revenue," a planner that defaults to "search Walmart's 10-K" is missing the more diagnostic test: "does the focal company show operational evidence of a customer of that scale?"

{catalog_block}

For any claim that needs an M-source the catalog DOESN'T have, propose a new connector instead (see proposal schema below).

== WORKFLOW ==
1. Read the filings_index. Pick the most substantive pre-cutoff filing (10-K preferred; 20-F for foreign filers; S-1 if recent IPO; 10-Q if newer interim disclosures materially change the picture).
2. Slice the filing:
     python3 -c "from verticals.public_co.filing_slice import slice_filing; t=open('FILING_PATH').read(); print(slice_filing(t, budget_chars=120000))" > /tmp/sliced_{ticker}.txt
   Read /tmp/sliced_{ticker}.txt.
3. Extract 5-8 testable factual claims. HIGH-discriminative criteria:
   - Names a specific external entity the framework can independently look up
   - Quantifies something verifiable (contract $, units delivered, patent count, named-program participation)
   - Asserts a status with a registry analog
   LOW value (skip): pure accounting unless material vendor/equity event; subjective characterizations; pure marketing TAM; pure forward projections.
4. For each claim, decide its M-source plan:
   a. Classify `domain` (from the focal company's NAICS family) and `claim_type_taxonomy` (existence / production_count / facility_scope / workforce / federal_customer / commercial_customer / certification_milestone / patents_ip / supply_chain / financial_distress / etc.). Set both fields on the claim record.
   b. Look at the taxonomy cell for (domain, claim_type). Use the **primary** catalog sources from that cell as your default mapping.
   c. **MAPPED** — the canonical source (or any catalog source) cleanly adjudicates this claim. Fill in source_id + source_params.
   d. **PROPOSED** — no catalog source adequately covers, but a SPECIFIC new connector would. Use the ProposedConnector schema below.
   e. **NONE** — claim is not adjudicatable by any external registry (genuinely inside the company's accounting; truly UNVERIFIABLE structurally). Use rarely.
   f. **creative_extensions** — In ADDITION to a/b/c above, emit any non-taxonomy public sources you can argue would test this specific claim. These are free-form proposals; the executor logs them for promotion review. The taxonomy cell's status field tells you when this is most expected: GAP cells especially invite creativity, but creative extensions are welcome on ANY cell where you can name a useful additional observable.
5. Write data/_local/{ticker}.plan.json (see schema below). **One file, atomic write.**
6. Report a one-line summary: "{ticker}: N claims, mapped=M proposed=P none=Q, picked filing=<accession>"

== PROPOSED CONNECTOR SCHEMA ==
When proposing a new connector, fill in ALL of these:
- name: dot-namespaced ID, e.g. "fdic_call_reports.bank_loan_performance"
- description: one-line human description
- endpoint: URL or file path (the actual data location)
- access_pattern: "csv_download" | "api" | "scrape" | "file_download" | "foia"
- auth_required: true/false
- sample_invocation: pseudocode showing how to call it (e.g. "GET https://banks.data.fdic.gov/api/financials?filters=RSSDID:4119424&fields=NAMEFULL,LNCONOTH,NTLNLS&sort_by=REPDTE&limit=4")
- rationale: 1-2 sentences explaining why this claim type structurally needs this source
- estimated_cost: "free" | "$X/query" | "$X/yr subscription"
- completeness: qualitative coverage (e.g. "FDIC-chartered banks only", "all federal contracts", "all SEC filers")
- referent_type: what the source observes (e.g. "loan_portfolio", "vehicle", "facility")
- attribute: what about it (e.g. "charge_off_rate", "registration_status", "permit_expiry")

Propose connectors that are FREE and PUBLIC where possible. Prefer authoritative-registry sources (federal/state regulatory bodies, SEC adjacent, public-domain CSV/API endpoints) over paid aggregators.

== OUTPUT SCHEMA (plan.json) ==
```
{{
  "ticker": "{ticker}",
  "cutoff": "{cutoff}",
  "filing": "<accession_form.txt>",
  "plan_version": 1,
  "claims": [
    {{
      "claim_id": "{ticker}-1",
      "claim_text": "<one sentence>",
      "source_quote": "<literal text from filing>",
      "subject": "<entity>",
      "predicate": "<verb_phrase>",
      "object_value": "<value or null>",
      "category": "customer_pipeline | regulatory_milestone | production_volume | partnership | technology | physical_facility | financial_distress | vendor_relationship | other",
      "referent_type": "geographic_area | physical_object | person | entity | event | amount | time_period | quantity | intangible",
      "m_source_status": "MAPPED",
      "source_id": "edgar_fts.query_fulltext",
      "source_params": {{"search_term": "...", "cutoff_date": "{cutoff}", "cik": "..."}},
      "proposed_connector": null,
      "creative_extensions": [
        {{
          "source_label": "FAA Aircraft Registry",
          "endpoint_or_method": "https://registry.faa.gov/aircraftinquiry/search/ManufacturerInquiry",
          "rationale": "Claim of N delivered drones implies N FAA-registered airframes for any US operator",
          "expected_observable": "list of N-numbers + manufacturer name + model",
          "signal_direction": "if registered_count << claimed_delivery_count then contradicts production claim",
          "severity_if_contradiction": "MODERATE_UNDERDELIVERY"
        }}
      ],
      "domain": "aviation_drones",
      "claim_type_taxonomy": "production_count",
      "extraction_notes": ""
    }},
    {{
      "claim_id": "{ticker}-2",
      "claim_text": "...",
      "source_quote": "...",
      "...": "...",
      "m_source_status": "PROPOSED",
      "source_id": null,
      "source_params": {{}},
      "proposed_connector": {{
        "name": "fdic_call_reports.bank_loan_performance",
        "description": "FDIC quarterly Call Report data per institution (RSSDID-keyed)",
        "endpoint": "https://banks.data.fdic.gov/api/financials",
        "access_pattern": "api",
        "auth_required": false,
        "sample_invocation": "GET .../financials?filters=RSSDID:4119424&fields=NAMEFULL,LNCONOTH,NTLNLS&sort_by=REPDTE&limit=4",
        "rationale": "UPST originates personal loans on bank-partner balance sheets; partner's Call Report adjudicates UPST cohort loss performance indirectly.",
        "estimated_cost": "free",
        "completeness": "FDIC-chartered banks only",
        "referent_type": "loan_portfolio",
        "attribute": "charge_off_rate"
      }},
      "creative_extensions": [],
      "domain": "finance_banking",
      "claim_type_taxonomy": "bank_partner_balance_sheet",
      "extraction_notes": "Bank-partner-level adjudication; UPST's specific share within Cross River's portfolio isn't separable."
    }}
  ]
}}
```

== START NOW ==
Be efficient. The whole job is: read filing -> extract claims -> map M-sources -> write plan.json. NO QUERIES. Final message must be exactly the one-line summary.
"""


def build_planner_prompt(
    *,
    ticker: str,
    cik_padded: str,
    company_name: str,
    notes: str,
    cutoff: str,
    cohort_context: str,
    counterparty_ciks: dict[str, str],
    catalog: dict[str, dict[str, Any]],
    taxonomy_block: str | None = None,
) -> str:
    counterparty_block = "\n".join(
        f"  - {label}: {cik}" for label, cik in counterparty_ciks.items()
    )
    catalog_lines = []
    for src_name, spec in catalog.items():
        catalog_lines.append(f"### `{src_name}`")
        catalog_lines.append(spec.get("description", "").strip())
        params = spec.get("params") or {}
        if params:
            catalog_lines.append("**Exact accepted params (use these names verbatim):**")
            for p, desc in params.items():
                catalog_lines.append(f"  - `{p}`: {desc}")
        good = spec.get("good_for") or []
        if good:
            catalog_lines.append(f"**Good for:** {', '.join(good)}")
        catalog_lines.append("")
    catalog_block = "\n".join(catalog_lines)
    if taxonomy_block is None:
        from .r_f_m_taxonomy import render_for_llm
        taxonomy_block = render_for_llm()
    return PROMPT_TEMPLATE.format(
        ticker=ticker,
        ticker_lower=ticker.lower(),
        cik_padded=cik_padded,
        company_name=company_name,
        notes=notes,
        cutoff=cutoff,
        cohort_context=cohort_context,
        counterparty_block=counterparty_block,
        catalog_block=catalog_block,
        taxonomy_block=taxonomy_block,
    )


def build_planner_prompt_for_ticker(cohort_module: str, ticker: str) -> str:
    """Convenience: pull cohort metadata from the module + render."""
    import importlib

    from .m_source_catalog import CATALOG

    m = importlib.import_module(cohort_module)
    member = next(c for c in m.COHORT if c.ticker == ticker)
    return build_planner_prompt(
        ticker=ticker,
        cik_padded=member.cik,
        company_name=member.name,
        notes=member.notes,
        cutoff=m.CUTOFF,
        cohort_context=m.COHORT_CONTEXT,
        counterparty_ciks=m.COMMON_COUNTERPARTY_CIKS,
        catalog=CATALOG,
    )
