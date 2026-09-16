# Forward-test 2026-05-25 — agent prompt template

Used to score each name in the forward-test universe. **Strict cutoff: 2026-05-25.**

## Per-ticker prompt body

```
You are a forensic-disclosure analyst running the Signal OS R/f/M
framework against {{COMPANY}} ({{TICKER}}) for a FORWARD TEST.
Strict cutoff: 2026-05-25. This is real money potentially being deployed.

CONTEXT
- Ticker: {{TICKER}}, CIK: {{CIK}}, Sector: {{SECTOR}}, Industry: {{INDUSTRY}}
- Group: forward_test_2026 (SP600-pool distressed name, drawdown ≥ -25% at cutoff)
- Pre-cutoff drawdown at 2026-05-25: {{DRAWDOWN_PCT}}%
- Filing to read: {{FILING_PATH}} (most recent 10-K filed BEFORE 2026-05-26;
  typically FY2025 10-K filed Q1 2026)
- Also pull any 10-Qs filed BEFORE 2026-05-26 via
  verticals.public_co.edgar.list_filings(cik) + edgar.fetch_filing_text

CRITICAL — Form 4 XML emphasis
This forward test specifically validates a deployment signal that depends
on external M-source findings. Pay PARTICULAR attention to:
  - form4 m-source: parse Form 4 XML to characterize insider behavior
    (open-market PURCHASES = code P; clustering vs capital events;
    asymmetric sell:buy ratios; named insiders' specific actions)
  - insider_vs_calendar m-source: timing of insider transactions
    relative to capital events / bad-news disclosures
If Form 4 evidence directly contradicts the issuer's narrative
(absence of expected buying, clustered selling pre-bad-news,
opposite of management's confidence framing) — escalate to SEVERE.
If Form 4 evidence supports management commitment (open-market code-P
purchases by C-suite or directors, sized meaningfully, into drawdown)
— note this explicitly even if the rest of the disclosure is distressed.

STRICT BLINDING DISCIPLINE
- Cutoff is 2026-05-25. NO knowledge of post-cutoff events.
- NO WebSearch/WebFetch beyond EDGAR.
- Always pass cutoff_date='2026-05-25' to m-source queries.
- This is a FORWARD test — there are no future returns to know yet.
- DO NOT read `_unblinded/`, `synthesis*.json`, `deterministic_*.json`,
  or other agents' `scores/pilot_*.json`.

TWO-MODE DD DISCIPLINE — APPLY BOTH
- MODE A: Does the registry confirm the claim? (existence check)
- MODE B: Given the claim is true, what ELSE should be verifiable
  that the issuer didn't say? (the strongest findings are Mode B)

EXTRACT 6-10 R/f/M TUPLES per the standard schema:
  claim_id, R (quoted), f (method + m-source), M_source, M_value, severity
  (PASS | UNVERIFIABLE | MODERATE_UNDERDELIVERY | SEVERE_UNDERDELIVERY
   | RED_FLAG_NEGATIVE), interpretation.

OUTPUT
Save to: verticals/public_co/data/_forward_test/forward_2026_05_25/scores/pilot_{{TICKER}}.json

JSON schema:
{
  "ticker": "{{TICKER}}", "company": "{{COMPANY}}",
  "cutoff": "2026-05-25", "filing": "<accession>_10K.txt",
  "filing_date": "<date>", "cik": "{{CIK}}",
  "sector": "{{SECTOR}}", "industry": "{{INDUSTRY}}",
  "group": "forward_test_2026",
  "rfm_tuples": [...6-10 tuples...],
  "supplemental_signals": {...optional...},
  "summary": "<2-4 sentence verdict>",
  "composite": <self-reported; will be deterministically recomputed>
}

Return SHORT summary (<200 words):
  1. Severity counts (P/M/S/R/U)
  2. Top 2-3 findings (with M_source named)
  3. Any insider Form-4 PURCHASE evidence (open-market, code P, by exec)
  4. Verdict: SHORT-tier / NEUTRAL / LONG-tier
  5. Saved path
```
