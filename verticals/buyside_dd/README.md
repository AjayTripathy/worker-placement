# buyside_dd

General-purpose forensic DD on private deal data rooms. Takes a folder of PDFs / decks / spreadsheets, extracts claims (LLM), types referents, looks up f-rules and M-sources, runs cross-checks, writes a divergence report.

## Production state

Two real-deal validations:

- **FCRE2 LLC** — $30M Section 8 housing private credit. Caught: systematic cost-basis inflation in 9 of 16 verified properties (~17% aggregate, ~$110K on the verified subset), Section 8 FMR violations (4 properties priced 30–41% above HUD FMR), one property with no recorded sale, sponsor anonymity escalated to deal-level material. Output: [`outputs/20260512_212228/DIVERGENCE_REPORT.md`](outputs/20260512_212228/DIVERGENCE_REPORT.md).
- **AHC Series A** — $50M raise at $235M pre. Caught: Form D dollar mismatches on prior rounds (deck $2M / $7M vs SEC $485K / $2M); zero parent-entity Form D filings under any "American Housing" search variant; zero Austin building permits or OSHA records under any AHC name; AHC TX entity registered in Dallas (75201) not Austin where the factory is claimed; internal capacity divergence (1,000 pitch vs 1,750 model = 75% overstatement). Output: [`outputs/ahc_20260513_093817/DD_REPORT.md`](outputs/ahc_20260513_093817/DD_REPORT.md).

## Pipeline (8 stages)

```
inputs/<deal_folder>/
        │  PDFs, decks, spreadsheets
        ▼
1. Load documents
2. Extract claims (LLM)
3. Type referents (LLM + ontology)
4. Look up f-rules (f_library)
5. Look up M sources (source_atlas)
6. Acquire observations (connectors)
7. Compare and score
8. Write outputs/<run_id>/DIVERGENCE_REPORT.md
```

Orchestrator: [`pipeline.py`](pipeline.py). AHC-specific runners: [`run_ahc.py`](run_ahc.py), [`run_ahc_v2.py`](run_ahc_v2.py).

## Layout

```
buyside_dd/
├── pipeline.py                  Main orchestrator
├── run_ahc.py / run_ahc_v2.py   AHC-specific runners
├── ahc_factory_hardened_check.py  Address-resolved factory check (AHC false-negative lesson)
├── schemas.py                   Claim, TypedClaim, FRule, MSource, Finding, Observation, Severity
├── f_library.py                 Codified expected-relationship rules per (predicate, referent_type, jurisdiction)
├── source_atlas.py              M-source directory: which observable supplies which attribute for which referent type
├── dispatcher.py                Routes typed claims to source connectors
├── comparator.py                f(M) computation + severity scoring
├── cross_claim_check.py         Cross-claim consistency (deck pre-orders × counterparty disclosure)
├── materiality.py               Per-claim materiality tier; deal-level materiality re-derivation
├── budget.py                    BudgetState + StopReason + Convergence (when to stop spending on verification)
├── policy.py                    RunPolicy (paid-source budget, FOIA gating)
├── connectors/                  M-source connectors (sec_edgar, hud_fmr, austin_permits, osha_establishment, ...)
├── fixtures/                    Test input fixtures
├── inputs/                      Live deal data rooms (per-deal subfolders; AHC artifacts at top level, FCRE2 archived)
└── outputs/                     Per-run output folders, named <run_id>_<YYYYMMDD_HHMMSS>
```

## Connectors

Currently in [`connectors/`](connectors/):

- `sec_edgar.py` — Form D, 10-K, 8-K full-text search
- `hud_fmr.py` — HUD Fair Market Rents (Section 8 cap)
- `osha_establishment.py` — OSHA establishment registry
- `austin_permits.py`, `albuquerque_permits.py`, `bozeman_permits.py` — city building permits
- `wprdc_allegheny.py` — Pittsburgh / Allegheny County records
- `state_corp_pa.py` — Pennsylvania SoS (CF-blocked, see ARCHITECTURE limits)
- `tx_comptroller_corp.py` — Texas SoS / comptroller business registrations
- `census_acs.py` — Census ACS demographic context
- `uspto_patents.py` — Patent assignee lookup (legacy; prefer `verticals/public_co/m_sources/uspto_odp.py` for new work)
- `company_signal.py` — entity-resolution helper
- `web_discovery.py` — Tier 1 broad web discovery (DDG / Brave / Wayback fallback)

Adding a connector: subclass `connectors/base.py`, register in `source_atlas.py`, add a fixture under `fixtures/`.

## Run

```bash
python3 -m verticals.buyside_dd.pipeline inputs/<deal_folder>/
```

For AHC-specific runs use `run_ahc.py` / `run_ahc_v2.py` — they pre-wire the AHC-specific Form D / Austin permit / Texas SoS checks.

## Output naming

Outputs land in `outputs/<run_id>_<timestamp>/` with `DIVERGENCE_REPORT.md` (final report), `01_doc_texts.json` (extracted text), and `prompts/` (LLM prompt artifacts for audit trail). Earlier AHC iterations show the methodology evolution; the canonical AHC output is `outputs/ahc_20260513_093817/`.

## Methodology lessons (apply to future runs)

- **DD must query M** (FCRE2 lesson) — internal deck-vs-spreadsheet consistency is not enough; pipeline must hit external public records
- **Address-resolved checks** (AHC lesson) — when a deal claims a specific property, query permits / records by ADDRESS, not entity name; tenants don't file permits, GCs and landlords do
- **M has tiers — broad before narrow** (AHC factory lesson) — open-web discovery is M too; query Tier 1 (broad, fact-surfacing) before Tier 2/3 (narrow, fact-verifying)

These are codified in `~/.claude/projects/-Users-ajay-exalted/memory/feedback_*` files and applied automatically in future buyside_dd work.
