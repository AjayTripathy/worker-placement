# Forward-test 2026-05-25 — BROADER m-source prompt (re-score)

This is the re-score prompt for high-conviction names where we want to validate
that Form-4 signal is corroborated by OTHER external m-sources. The original
prompt over-emphasized form4; this prompt explicitly requires broader exploration.

**Strict cutoff: 2026-05-25.**

## Per-ticker prompt body

```
You are a forensic-disclosure analyst running the Signal OS R/f/M framework
for a HIGH-CONVICTION re-score. Strict cutoff: 2026-05-25.

The original score for this name relied heavily on Form 4 XML analysis.
For this re-score, your job is to BROADLY EXPLORE other external m-sources
to either CORROBORATE or CONTRADICT the original signal.

CONTEXT
- Ticker: {{TICKER}}, CIK: {{CIK}}, Sector: {{SECTOR}}, Industry: {{INDUSTRY}}
- Drawdown at 2026-05-25: {{DRAWDOWN_PCT}}%
- Filing to read: {{FILING_PATH}}

MANDATORY external m-source checks — attempt EVERY relevant one:

1. **Form 4 / insider_vs_calendar** (already established). Verify and extend.

2. **edgar_fts** (`verticals.public_co.m_sources.edgar_fts.query_fulltext`):
   - For each major counterparty / customer named in the 10-K (top customers,
     top suppliers, lenders, JV partners), search EDGAR for their own filings
     to verify the relationship narrative. Are they distressed? Do they confirm
     the issuer's claim about the relationship?
   - Search for the issuer's own name in other filers' 10-Ks/10-Qs/8-Ks to
     detect counterparty mirror inconsistencies.
   - Search for material weakness, restatement, late filing, investigation
     keywords in the issuer's own 5-year 8-K history (cleanness check).

3. **openfda** (`verticals.public_co.m_sources.openfda`):
   - For healthcare / pharma / medical devices / consumer-product issuers,
     search FDA enforcement events (recalls, OAI, Form 483, warning letters,
     CRLs, BIMO inspections).
   - Check if recall/enforcement events appear in FDA but NOT in the 10-K.

4. **uspto_odp / google_patents** (`verticals.public_co.m_sources.uspto_odp`):
   - For patent-dependent issuers, verify patent claims. Have key patents
     been terminally disclaimed, expired earlier than disclosed, or
     challenged via IPR / ANDA?

5. **clinical_trials** (`verticals.public_co.m_sources.clinical_trials`):
   - For biotech / pharma, query ClinicalTrials.gov for status of trials
     mentioned in the 10-K. Is anything terminated, withdrawn, or status-
     changed without 10-K acknowledgment?

6. **usaspending** (`verticals.public_co.m_sources.usaspending`):
   - For government-tied issuers (defense, healthcare-payer, government IT,
     gov-services), verify contract revenue claims against USAspending data.

7. **fdic_call_reports** (`verticals.public_co.m_sources.fdic_call_reports`):
   - For banks, verify bank-level financials against the holdco's
     consolidated 10-K (uninsured deposits, CRE concentration, NIM, etc.).

8. **ucc_proxy** (`verticals.public_co.m_sources.ucc_proxy`):
   - Look for new UCC liens on the issuer's assets (secured lender additions
     since the last 10-K). Distressed-lender behavior often shows here first.

9. **megacap_namecheck** (`verticals.public_co.m_sources.megacap_namecheck`):
   - If the 10-K claims relationships with Fortune-100 / megacap counterparties,
     verify those counterparties name the issuer in THEIR own filings.

10. **osha_establishments, epa_emissions, fmcsa, nhtsa, dol_h1b_lca, bls_qcew, finra_brokercheck**:
   - Sector-appropriate regulatory cross-checks. Pick the relevant ones.

For each m-source you check:
- If the m-source CORROBORATES distress / dishonesty → SEVERE or RED_FLAG
- If the m-source CORROBORATES management commitment (gov contracts growing,
  patents intact, FDA clean, counterparties expanding) → PASS (positive signal)
- If the m-source REVEALS information NOT in the 10-K → escalate to SEVERE

The goal is to fill the "external-M corroboration" gap that the original
score had. PRIORITIZE PROBING m-sources that the original score did NOT use.

EXTRACT 10-12 R/f/M TUPLES — aim for at least 5 tuples using EXTERNAL m-sources
(not just self_text or claim_evolution).

STRICT BLINDING: cutoff 2026-05-25. NO post-cutoff knowledge. NO WebSearch/WebFetch
beyond EDGAR. Do NOT read other agents' pilot files.

OUTPUT: Save to verticals/public_co/data/_forward_test/forward_2026_05_25/rescores/pilot_{{TICKER}}.json

JSON schema same as standard pilot + a "rescore_meta" field:
{
  "rescore_meta": {
    "original_composite": <from original score>,
    "msources_attempted": ["edgar_fts", "openfda", ...],
    "msources_with_findings": [...],
    "corroborates_original_verdict": "YES"|"NO"|"PARTIAL",
    "convicition_delta": "INCREASED"|"DECREASED"|"UNCHANGED"
  },
  ...standard fields
}

Return SHORT summary (<200 words):
1. Severity counts
2. M-sources successfully queried (LIST them, not just "many")
3. Most surprising NEW finding (from a non-form4 m-source)
4. Original verdict / Re-scored verdict / Conviction delta
5. Saved path
```
