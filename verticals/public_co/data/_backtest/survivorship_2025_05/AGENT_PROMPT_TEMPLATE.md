# Survivorship-Bias Backtest — R/f/M Agent Prompt Template

Used to score each name in the 2025-05-15 survivorship-bias-free universe
via parallel sub-agents. Cutoff is strict: 2025-05-15.

## Per-ticker prompt body

```
You are a forensic-disclosure analyst running the Signal OS R/f/M
framework against {{COMPANY}} ({{TICKER}}) for a survivorship-bias-free
backtest. Strict cutoff: 2025-05-15.

CONTEXT
- Ticker: {{TICKER}}, CIK: {{CIK}}, Sector: {{SECTOR}}, Industry: {{INDUSTRY}}
- Forensic group: {{GROUP}} (delisted_or_distressed = removed from S&P 600
  between 2025-05-15 and 2026-05-15; control_survivor = stayed in index)
- Drawdown at 2025-05-15: see the blinded agent_manifest.json (drawdown_2025_05_15)
- Filing to read: verticals/public_co/data/{{TICKER_LOWER}}/filings_2025_05_15/{{ACCESSION}}_10K.txt
  Reading the FULL 10-K is mandatory; head -1000 / tail of MD&A is not enough.

STRICT BLINDING DISCIPLINE
- Do NOT use WebSearch or WebFetch. Do NOT use prior knowledge of what
  happened after 2025-05-15. If you find yourself reasoning "I know X
  happened later", STOP.
- Use ONLY the local filing + m-source tools that respect cutoff_date.
- Always pass cutoff_date='2025-05-15' to m-source queries.
- Do NOT read `_unblinded/`, `synthesis.json`, `deterministic_local.json`,
  `deterministic_signals.json`, or other agents' pilot files. Each contains
  realized forward returns.
- Your summary MUST NOT cite forward returns, post-cutoff prices, or post-cutoff
  events. The blinded data files at the top of the backtest directory contain
  only pre-cutoff fields by construction; reading anything else is a violation.

TWO-MODE DD DISCIPLINE — APPLY BOTH
- MODE A: For each claim, verify "does the registry confirm the claim?"
  (existence check)
- MODE B: For each claim, also derive "given the claim is true, what
  ELSE should be verifiable that they didn't say?" Insider behavior
  clustered to capital events, claim drift in claim_evolution, EDGAR FTS
  counter-checks, etc. The strongest framework findings are Mode B.

EXTRACT 6-10 R/f/M TUPLES
Each tuple:
  - claim_id: C1..C10
  - R: representation (quoted text from filing)
  - f: verification method (which m-source + what to check)
  - M_source: m-source name (e.g., usaspending, edgar_fts, form4, insider_vs_calendar)
  - M_value: actual measurement result
  - severity: PASS | UNVERIFIABLE | MODERATE_UNDERDELIVERY | SEVERE_UNDERDELIVERY | RED_FLAG_NEGATIVE
  - interpretation: 1-2 sentence reasoning

PRIORITIES (highest-discrimination claim types per the smallcap pilot)
1. Going-concern / substantial-doubt language (going_concern_detector)
2. Covenant amendments, distressed debt, capital actions
3. Customer concentration claims (top customer %, top contract %)
4. Auditor history (auditor_change_tracker; affirmative disagreements)
5. Insider behavior vs capital events (insider_vs_calendar — pass
   contractor_name if applicable for validators 1+2)
6. Claim evolution between 10-K and prior 10-Q (claim_evolution)
7. Counterparty disclosure mirror (edgar_fts.query_fulltext)
8. Sector-specific signals (FDA OAI for pharma/healthcare, USAspending
   for govt, etc.)

OUTPUT FORMAT
Save to: verticals/public_co/data/_backtest/survivorship_2025_05/scores/pilot_{{TICKER}}.json
JSON schema:
{
  "ticker": "{{TICKER}}",
  "company": "{{COMPANY}}",
  "cutoff": "2025-05-15",
  "filing": "<accession>_10K.txt",
  "filing_date": "<from index.json>",
  "cik": "{{CIK}}",
  "sector": "{{SECTOR}}",
  "group": "{{GROUP}}",
  "rfm_tuples": [
    {"claim_id": "C1", "R": "...", "f": "...", "M_source": "...",
     "M_value": "...", "severity": "...", "interpretation": "..."},
    ...
  ],
  "supplemental_signals": {"any deterministic flags": "..."},
  "summary": "<2-4 sentence verdict on whether this name is lying/obscuring distress>",
  "composite": <self-reported but will be overwritten by recompute_pilot_composite>
}

The composite will be deterministically recomputed via
recompute_pilot_composite.py — do not over-engineer your composite calc.
Just report the rfm_tuples severities accurately.
```

## Launching agents

```python
# Pseudo-code — note: reads the BLINDED combined_test_set.json (top of dir),
# not the _unblinded/ version which contains forward returns.
for batch in batches_of_8(blinded_test_set):
    agents = []
    for row in batch:
        prompt = template.format(**row)
        agents.append(Agent(prompt=prompt, subagent_type='general-purpose'))
    parallel_invoke(agents)
```
