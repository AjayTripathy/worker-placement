# R/f/M Survivorship-Bias Backtest — Agent Instructions

You will be given a TICKER. Score it using the Signal OS R/f/M framework with strict cutoff 2025-05-15.

## Steps

1. Load metadata from `verticals/public_co/data/_backtest/survivorship_2025_05/agent_manifest.json` for your ticker (CIK, sector, group, filing_path, filing_date, drawdown_2025_05_15).

   The agent_manifest.json at this path is the **blinded** view — it contains only pre-cutoff fields. Do NOT read anything inside `_unblinded/`; that directory contains post-cutoff outcomes used by `synthesize.py` for measurement and is off-limits to scoring agents.

2. Read the 10-K at `filing_path`. Also check for any 10-Qs filed BEFORE 2025-05-15 in the same directory — pull them via EDGAR if not present (use `verticals.public_co.edgar.list_filings(cik)` + filter to 10-Q forms with filing_date <= '2025-05-15', then `edgar.fetch_filing_text`).

## Strict Blinding
- NO WebSearch, NO WebFetch (beyond EDGAR for 10-Q)
- NO prior knowledge of post-2025-05-15 events
- Always pass `cutoff_date='2025-05-15'` to m-source queries
- If you find yourself reasoning "I know X happened later", STOP
- Do NOT read any of: `_unblinded/`, `synthesis.json`, `deterministic_local.json`,
  `deterministic_signals.json`, or other agents' `scores/pilot_*.json` files.
  Each of these contains realized forward returns.
- Your summary MUST NOT cite forward returns or post-cutoff events. Audits will reject pilots that do.

## Two-Mode DD
- MODE A: For each claim, "does the registry confirm the claim?" (existence check)
- MODE B: For each claim, "given the claim is true, what ELSE should be verifiable that they didn't say?" The strongest framework signals are Mode B.

## Extract 6-10 R/f/M Tuples

Each tuple: `claim_id` (C1-C10), `R` (quoted representation from filing), `f` (verification method + m-source), `M_source` (m-source name), `M_value` (measurement result), `severity` (PASS | UNVERIFIABLE | MODERATE_UNDERDELIVERY | SEVERE_UNDERDELIVERY | RED_FLAG_NEGATIVE), `interpretation` (1-2 sentences).

### Priority claim types
1. **Distress signals**: going-concern language, covenant amendments, subordinated debt, dividend cuts, buyback bans
2. **Customer concentration**: top customer %, top contract %
3. **Auditor history**: Big 4 vs tier 2, resignations, disagreements
4. **Insider behavior near capital events** (insider_vs_calendar)
5. **Claim evolution** between 10-K and pre-cutoff 10-Q (the strongest "lying" tell)
6. **Counterparty disclosure mirror** (edgar_fts.query_fulltext)
7. **Capital allocation tells** (buyback decel into trough, asymmetric buyback-vs-insider-sell pricing)
8. **CFO / auditor transitions** (timing relative to bad-news disclosures)
9. **Goodwill / impairment risk** vs market signals
10. **Sector-specific tells** (FDA OAI for healthcare, USAspending for govt-tied, etc.)

## Output

Save to `verticals/public_co/data/_backtest/survivorship_2025_05/scores/pilot_<TICKER>.json`:

```json
{
  "ticker": "<TICKER>",
  "company": "<NAME>",
  "cutoff": "2025-05-15",
  "filing": "<accession>_10K.txt",
  "filing_date": "<from manifest>",
  "cik": "<CIK>",
  "sector": "<SECTOR>",
  "group": "<GROUP>",
  "drawdown_context": "<2-3 sentences>",
  "rfm_tuples": [...6-10 tuples...],
  "supplemental_signals": {...optional...},
  "summary": "<2-4 sentence verdict>",
  "composite": <best estimate; will be recomputed deterministically>
}
```

## Return Format

Return a SHORT summary (<200 words) with:
1. Severity counts (P/M/S/R/U)
2. Top 2-3 findings
3. Verdict: SHORT-tier / NEUTRAL / LONG-tier (your best read)
4. Saved path

DON'T include the full JSON in your response — just save it to disk.
