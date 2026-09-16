# Phase 5/6 J-Book Re-Score Delta — 2026-05-23

_Cutoff 2026-05-20 · Corpus: 663 programs (R-2 410 + P-40 159 + OP-5 94)_
_Prior OP-5 coverage: 5 (SOCOM only). New: 89 Army SAGs (Active 53 + NG 19 + Reserve 17)._

## Method

The Phase 5/6 cohort (PLTR, BAH, KBR, PSN, VVX, HON, ESLT, DRS, DCO, VSEC, CDRE)
was previously scored against a J-Book corpus of 574 programs that contained
no Army O&M SAGs. The current 663-program corpus adds 89 Army Active/NG/Reserve
OP-5 entries.

This re-score does **not** re-run the LLM subagent. Instead it:
1. Scans each ticker's existing scored claims
2. Identifies claims that resolved to `NOT_FOUND` previously and whose text
   contains trigger phrases mapping to specific OP-5 SAGs (e.g. "LOGCAP" →
   "Base Operations Support")
3. Looks up the SAG status in the new corpus at cutoff
4. Proposes a severity update with explicit hand-rules per claim to avoid
   false-positive trigger matches (e.g. T-45 "depot maintenance" is Navy,
   not Army Land Forces Depot Maintenance)

## Claim-level delta

| Ticker | Claim | Prior | Proposed | Trigger SAG | SAG status (FY26) | Δ weight |
|---|---|---|---|---|---|---:|
| BAH | C5 | UNVERIFIABLE | UNVERIFIABLE | Cyberspace Operations | SHRINKING $331M | 0 |
| VVX | C1 | UNVERIFIABLE | **PASS** | Base Operations Support | STEADY $10,264M | 0 |
| VVX | C2 | UNVERIFIABLE | **PASS** | Base Operations Support | STEADY $10,264M | 0 |
| VVX | C3 | UNVERIFIABLE | **MODERATE_UNDERDELIVERY** | Training Support | SHRINKING $550M | +1 |
| VVX | C4 | UNVERIFIABLE | REVIEW_NEEDED | (Navy depot, false-positive) | n/a | 0 |
| DCO | C6 | MODERATE | MODERATE (corroborated) | Aviation Assets | SHRINKING $1,709M | 0 |
| VSEC | C4 | UNVERIFIABLE | REVIEW_NEEDED | (segment mix unknown) | n/a | 0 |

## Composite impact

| Ticker | n_claims | Prior composite | Re-scored | Δ | Tier |
|---|---:|---:|---:|---:|---|
| BAH | 12 | 0.286 | 0.286 | 0 | NEUTRAL (unchanged) |
| VVX | 10 | 0.400 | 0.375 | −0.025 | NEUTRAL (unchanged) |
| DCO | 10 | 1.000 | 1.000 | 0 | SHORT (unchanged) |
| VSEC | 8 | 0.000 | 0.000 | 0 | LONG (unchanged) |

No tier changes. The expanded corpus moved **VVX** the most — verified two
LOGCAP claims as PASS (Base Ops Support steady $10.3B) and converted one
UNVERIFIABLE (WTRS) to MODERATE (Training Support shrinking). Net composite
actually drops slightly because the denominator grew (2 UNVERIFIABLE → PASS
counted as zeros) faster than the numerator (1 new MODERATE).

The other 7 Phase 5/6 tickers (PLTR, KBR, PSN, HON, ESLT, DRS, CDRE) are
**unchanged** — their claims reference program-specific PE names
(Gotham, Maven, TITAN, hypersonics, Sentinel, Columbia subs, NNSA pits, etc.)
that the new Army OP-5 SAGs don't cover.

## Findings

1. **VVX C3 (WTRS) gets a real signal upgrade.** WTRS is sustainment work
   funded under the Army's Training Support SAG (`324`). That SAG is
   FUNDED_SHRINKING at FY26 cutoff ($550M FY26 vs higher FY25). The 10-K's
   "explicit pipeline-growth narrative" on WTRS is not corroborated by the
   Army budget. MODERATE_UNDERDELIVERY.

2. **VVX C1/C2 (LOGCAP V) are now verified PASS.** Army Base Operations
   Support is the canonical funding home for LOGCAP-style installation
   services contracts. FUNDED_STEADY at $10.3B FY26 — a $441M annual TO is
   a small slice of a big, stable pie. Underlying budget supports the
   stated PoP through 2030.

3. **DCO C6 (Aviation Assets) corroborates the existing MODERATE.** Already
   flagged MODERATE on the revenue-vs-backlog axis; now the budget-side
   evidence agrees — Army Aviation Assets SAG is FUNDED_SHRINKING into
   FY26. Severity unchanged but evidence is stronger.

4. **VSEC C4 and VVX C4 flagged REVIEW_NEEDED** — segment-mix or
   service-attribution issues prevent auto-promotion.

## Corpus gaps still open

The Phase 5/6 names with the most cohort-claim NOT_FOUND results
that the new corpus could **not** resolve:
- KBR: hypersonics test/eval, Sentinel ICBM ground systems, Vandenberg
  launch infra — all Air Force / MDA, blocked at the DNS layer at this
  network
- DRS: Columbia Class submarine, EW, quantum cascade laser — Navy/AF
- HON: aerospace spinoff, Bombardier commercial — out of scope
- ESLT: FMS to Asia-Pacific, IMOD Merkava — foreign customer

Filling these requires the Navy SECNAV FMB and Air Force SAFFM books;
neither is reachable from this network without further infrastructure.

## Files

- `verticals/public_co/data/_jbook_exposure_cohort/phase5_6_rescore_delta_2026-05-23.json` — machine-readable delta
- `verticals/public_co/data/_jbook_data/programs.json` — expanded corpus (663 entries)
- `verticals/public_co/data/_jbook_pdfs_p40/asafm_url_manifest.json` — full 1,087-URL inventory
