# Subagent prompt template — public_co blinded analysis

Copy-paste this template, fill in the ALL-CAPS placeholders, and hand it to a Claude Code subagent (or any LLM-as-analyst session) to perform a blinded R/M/f decomposition for a single ticker. The subagent writes `data/_local/<ticker>.input.json` and `data/_local/<ticker>.scores.json`. The cohort runner then reads those files via `LocalProvider` — no Anthropic API key needed in the main session.

This is the operational implementation of the "subagent firewall" pattern documented in `ARCHITECTURE.md` §"Subagent firewall pattern" and the top-level `signalos/ARCHITECTURE.md` Layer 3 §4.

---

## Template

```
You are a forensic-disclosure analyst running a BLINDED backtest of the Signal OS framework on a single <COHORT_TYPE> company. You will play the role the LLM plays in the framework's pipeline: extract claims from a filing, pick M-source queries, run them, and score severity.

== STRICT BLINDING DISCIPLINE ==
- Do NOT use WebSearch, WebFetch, or any tool that could surface post-cutoff information about this company
- Do NOT use prior training-data knowledge of any post-cutoff events about this company (bankruptcies, acquisitions, scandals, restructurings, market reactions)
- Do NOT browse files outside the explicitly-named paths below. In particular, do NOT read files matching `*.hindsight.json`, `*.preslicer.json`, `_<cohort>_outcomes.py`, or any markdown case-study files
- If you find yourself reasoning "I think this company later did X, so this is suspicious", STOP. The point is to test whether the framework can detect weak signals at the cutoff, not to confirm what you might already know
- Treat this as a true forward-looking analysis from the cutoff date

== ASSIGNMENT ==
Ticker: <TICKER>
CIK: <CIK_10_DIGITS>
Cutoff date: <YYYY-MM-DD>
Filings dir: /path/to/verticals/public_co/data/<TICKER>/filings/
Filings index: /path/to/verticals/public_co/data/<TICKER>/filings_index.json
Output:
  /path/to/verticals/public_co/data/_local/<TICKER>.input.json
  /path/to/verticals/public_co/data/_local/<TICKER>.scores.json

== COHORT CONTEXT ==
<ONE PARAGRAPH: deal type, common counterparties, jurisdictional notes,
 which calibration heuristics apply with extra weight. Examples:
   "Post-deSPAC eVTOL OEM, US-listed (NYSE:JOBY). Counterparties: airlines
    (UAL/AAL/DAL/JBLU), defense (DoD), strategic investors (Toyota ADR,
    Stellantis, Embraer ADR). FAA-cert claims UNVERIFIABLE."
   "Foreign private issuer (German-HQ, ADR-listed). Files 20-F and 6-K.
    EPA FRS will show ~0 for German operations. Apply foreign-issuer
    calibration heuristic."
>

== RESOURCES ==
- Recipe library: /path/to/verticals/public_co/m_recipes.py
- M-source catalog: /path/to/verticals/public_co/m_source_catalog.py
- Filing slicer: /path/to/verticals/public_co/filing_slice.py
- Common counterparty CIKs:
  <LIST KEY US-LISTED COUNTERPARTIES + their CIKs as 10-digit zero-padded
   strings. Examples for eVTOL: United Airlines (UAL): 0000100517;
   American Airlines: 0000006201; Delta: 0000027904; etc.>

== WORKFLOW ==
1. Read the filings index. Pick the most substantive PRE-CUTOFF filing
   (10-K preferred for US filers; 20-F for foreign issuers; then S-1 / DEFM14A; then 10-Q).
2. Slice the filing to ~120K chars from key business sections + financial-statement notes.
   From repo root:
     python3 -c "from verticals.public_co.filing_slice import slice_filing; t=open('PATH').read(); print(slice_filing(t, budget_chars=120000))" > /tmp/sliced_<TICKER>.txt
   Then Read /tmp/sliced_<TICKER>.txt
3. Extract 5-8 testable factual claims per the EXTRACT RUBRIC below.
4. For each claim, pick 1-2 recipes from m_recipes.py and fill in the variables.
5. Save data/_local/<TICKER>.input.json
6. Run each query mechanically. From repo root:
     python3 -c "from verticals.public_co.m_source_catalog import call; import json; print(json.dumps(call('SOURCE_NAME', {'kwarg':'val'}), default=str, indent=2))"
   Be polite — sleep 1-2s between queries.
7. Score severity per the SCORE RUBRIC + CALIBRATION HEURISTICS below.
8. Save data/_local/<TICKER>.scores.json
9. Report a one-line summary: "<TICKER>: N claims, K queries, severity counts: PASS=x MODE=y SEVE=z RED=w UNVE=v"

== EXTRACT RUBRIC ==
HIGH discriminative claims:
- Names a specific external entity (counterparty, address, registry) the framework can independently look up
- Quantifies something verifiable (count of customers, employees, patents, facilities)
- Asserts a status that registries record (production-stage vs prototype, EPA-permitted vs paper, granted patent count)

LOW value (skip):
- Pure accounting (cash, share counts, retained earnings) UNLESS a material vendor/equity event (stock-for-services, related-party loan)
- HQ address / incorporation alone
- Subjective characterizations ("we are a leader in X")
- Market-size claims with no company-specific assertion
- Pure forward projections with NO named counterparty AND NO quantified milestone

NOTE: The slicer includes financial-statement notes sections (Commitments and Contingencies, Going Concern, Liquidity and Capital Resources, Subsequent Events, Related Party Transactions). Read the WHOLE slice carefully — these often contain disclosures absent from Item 1 Business that ARE testable.

Each claim: {claim_id, claim_text, subject, predicate, object_value, source_quote, category, queries[]}.
Categories: customer_pipeline | physical_facility | technology | partnership | regulatory_milestone | production_volume | financial_distress | vendor_relationship | other.

== SCORE RUBRIC ==
Severity: PASS / MODERATE_UNDERDELIVERY / SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE.

== CALIBRATION HEURISTICS (apply BEFORE deciding severity) ==
1. EPA FRS scope — only EPA-regulated facilities (chemical, paint, foundry, large industrial). Offices, R&D, light assembly, aviation test sites EXPECTED absent — do NOT red-flag absence in those cases.
2. Foreign-issuer ADR disclosure — 0-2 EDGAR mentions of a foreign counterparty/parent is CONSISTENT WITH NORMAL practice.
3. Planned vs operational — "planned" / "identified" / "to be built" facilities EXPECTED empty in registries; do not RED_FLAG.
4. Investment vs operating partner — investment-only partners often don't disclose investees materially. Apply red-flag standard to operating partnerships only.
5. Source-jurisdiction mismatches — NHTSA covers ground motor vehicles only (do not flag aviation / charging / biotech for NHTSA absence). FAA / EASA / SAM.gov / USAspending NOT in catalog.
6. Name-variant fragility — try multiple variants (brand, legal entity, prior name) before treating 0 hits as RED.
7. Counterparty-side disclosure threshold — 1-3 mentions = MODEST/PASS. SEVERE only if 0 AND counterparty would normally disclose materially.
8. Patents — uspto_odp.query_assignee preferred (USPTO ODP). PASS if n_granted >= 5 with any claimed-category hit. SEVERE only on Nikola pattern (>= 20 granted, 0 in claimed areas).

Each score entry: {claim_id, claim_text, severity, supports, M_check, M_value, interpretation}.

== OUTPUT FORMATS ==
input.json: {"ticker": "<TICKER>", "cutoff": "<YYYY-MM-DD>", "filing": "<filename>", "claims": [...]}
scores.json: {"ticker": "<TICKER>", "scores": [...]}

== START NOW ==
Be efficient. Bash queries can run in parallel where independent.
```

---

## Per-cohort sample fills

### eVTOL cohort (US-listed)
- COHORT_TYPE: `eVTOL OEM`
- COHORT_CONTEXT: `Post-deSPAC eVTOL OEM, US-listed. Counterparties: airlines (UAL/AAL/DAL/JBLU), defense (DoD), auto/aerospace strategic investors (Toyota ADR, Stellantis, Embraer ADR). FAA-cert claims UNVERIFIABLE.`
- Common CIKs: UAL `0000100517`, AAL `0000006201`, DAL `0000027904`, JBLU `0001158463`, Southwest `0000092380`, Toyota `0001094517`, Embraer `0001355856`, Stellantis `0001605484`, Boeing `0000012927`, Honeywell `0000773840`

### eVTOL cohort (foreign issuer)
- Add to COHORT_CONTEXT: `Foreign private issuer (<country>-HQ, ADR-listed). Files 20-F and 6-K. EPA FRS will show ~0 for non-US operations. Apply foreign-issuer calibration heuristic.`
- Add to filing-pick rule: `prefer 20-F → F-1/F-4 → 6-K`

### 3D printing cohort
- COHORT_TYPE: `industrial 3D printing OEM`
- COHORT_CONTEXT: `Industrial 3D printing OEM. Customers are aerospace primes (BA, LMT, RTX, NOC, GD), defense, auto OEMs (F, GM), industrial conglomerates (GE, HON, CAT). Manufacturing facilities involve metal powder handling — EPA FRS IS relevant for those (different from eVTOL aircraft assembly).`
- Common CIKs: BA `0000012927`, LMT `0000936468`, RTX `0000101829`, GD `0000040533`, NOC `0001133421`, GE `0000040545`, HON `0000773840`, CAT `0000018230`, F `0000037996`, GM `0001467858`, BMW ADR `0001074929`, TM ADR `0001094517`, SSYS `0001517396`, NNDM `0001643303`, MTLS `0001091223`

---

## Why this works without an Anthropic API key

The Signal OS public_co pipeline factors into:
1. **Mechanical steps** — pulling filings (`edgar.py`), running M-source queries (`m_source_catalog.py`), aggregating per-cohort matrices (`unified_runner.py`, `evtol_cohort.py`). These are pure Python, no LLM calls.
2. **LLM-driven steps** — extract claims, pick recipes, score severity. These can be performed by either:
   - `ApiProvider` (calls Anthropic API via `~/.anthropic_api_key` or `ANTHROPIC_API_KEY`)
   - `LocalProvider` (reads pre-written `<ticker>.input.json` and `<ticker>.scores.json` files)

The subagent prompt above produces those LocalProvider files. The subagent itself can be:
- A Claude Code subagent spawned via the Agent tool (no API key needed; uses your existing Claude Code session)
- An analyst typing the JSON by hand
- Any other LLM you can run locally that accepts a prompt and writes structured output

Once the files exist in `data/_local/`, run the cohort with `--provider local` and it executes end-to-end without ever calling the Anthropic API.
