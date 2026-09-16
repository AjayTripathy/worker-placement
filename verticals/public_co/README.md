# public_co

Public-company SEC-filing forensic divergence screen for the Signal OS framework. Same pipeline runs forward (current ticker, current cutoff) and as a backtest (historical ticker, pre-event cutoff with known outcome). The historical-cohort runs are how the methodology was developed and validated; the forward runs are the alpha-generating mode.

## Production state

| Cohort | Cutoff | Sample | Result (post-improvement methodology) |
|---|---|---|---|
| **eVTOL** (JOBY, ACHR, EVEX, LILM, EVTL, SRFM) | 2024-06-30 | N=6, 1 confirmed bankruptcy (LILM Oct 2024) | **Perfect monotonic ranking** — P=100% R=100% Sp=100% at threshold 0.5/claim Loose. LILM at 1.75 (caught), JOBY at 0.00 (clean). |
| **3D printing** (VLD, VJET, DM, MKFG, SSYS, MTLS, NNDM, XMTR) | 2024-03-31 | N=8, 1 confirmed bankruptcy (VLD Sep 2024) + 3 acquired-distressed | **Held-out test pre-improvements** — P=50% R=50%. Surfaced the Velo3D coverage-gap pattern (private dominant customer = invisible to EDGAR). |
| **15-company SPAC EV** (NKLA, RIVN, LCID, …) | per-name | N=15, multiple bad outcomes | Earlier hindsight-fitted run; superseded by blinded methodology |
| **Frauds + clean pairs** (LKNCY/SBUX, SAVA/VRTX, EH/AVAV, DMND/HSY) | per-pair | 4 pairs | Earlier hindsight-fitted run |

## Read first

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — full vertical architecture: pipeline stages, Provider pattern, cohort module structure, M-source library, slicer details, subagent firewall, calibration heuristics, cohort iteration history
- [`EVTOL_FORWARD_TEST.md`](EVTOL_FORWARD_TEST.md) — eVTOL cohort case study (with hindsight-bias caveats and the post-blinding correction)

## Quick orientation

| Concept | File |
|---|---|
| End-to-end runner | [`unified_runner.py`](unified_runner.py) |
| Provider pattern (LocalProvider / ApiProvider) | [`providers.py`](providers.py) |
| LLM pipeline (extract / pick / score) | [`llm_pipeline.py`](llm_pipeline.py) |
| Filing slicer (with notes-section weighting) | [`filing_slice.py`](filing_slice.py) |
| M-source library | [`m_source_catalog.py`](m_source_catalog.py), [`m_recipes.py`](m_recipes.py), [`m_sources/`](m_sources/) |
| Shared dataclass contract | [`analysis_types.py`](analysis_types.py) |
| eVTOL cohort | [`evtol_cohort.py`](evtol_cohort.py) + [`_evtol_outcomes.py`](_evtol_outcomes.py) |
| 3D printing cohort | [`threedp_cohort.py`](threedp_cohort.py) + [`_threedp_outcomes.py`](_threedp_outcomes.py) |

## Run

```bash
# Pull SEC filings for a cohort
python3 -m verticals.public_co.evtol_cohort --stage pull

# Score with LocalProvider (reads pre-written JSONs in data/_local/)
python3 -m verticals.public_co.evtol_cohort --provider local --reveal-outcomes

# Score with API (calls Claude via ~/.anthropic_api_key)
python3 -m verticals.public_co.evtol_cohort --provider api --reveal-outcomes
```

For blinded analysis (subagent firewall pattern), spawn one subagent per ticker with the standard blinded prompt template — the subagent writes `data/_local/<ticker>.{input,scores}.json` and the main session runs the cohort matrix. See `ARCHITECTURE.md` §"Subagent firewall pattern" for the prompt template.

## Key lessons codified during this vertical's build

1. **Slicer fix** — financial-statement notes (Commitments, Going Concern, Related Party) carry the highest-density divergence signal; previously dropped from slice
2. **USPTO ODP** — Google Patents is rate-limited dead end; ODP at `api.uspto.gov` works with free key (`~/.uspto_api_key`). Multi-word names need quoted-phrase syntax.
3. **Subagent firewall** — for cohort screens, blinding via subagents catches hindsight bias the analyst can't self-monitor
4. **Calibration heuristics** — written into SCORE_SYSTEM and subagent prompts; transferred from eVTOL but should be re-validated per-cohort
5. **Divergence ≠ solvency** — DM (3D printing) was confidently scored clean while being acquired in distress; framework catches misrepresentation, not cash burn

These are also written to user memory as cross-vertical operational discipline (`~/.claude/projects/-Users-ajay-exalted/memory/feedback_*`) and to the top-level `signalos/ARCHITECTURE.md` Layer 3.

## File layout

```
backtest/
├── ARCHITECTURE.md                     full vertical architecture
├── EVTOL_FORWARD_TEST.md               eVTOL case study
├── README.md                           this file
├── analysis_types.py                   shared dataclasses
├── providers.py                        Provider protocol + LocalProvider + ApiProvider
├── unified_runner.py                   provider-agnostic runner
├── llm_pipeline.py                     LLM extract/pick/score with BLINDING preamble
├── filing_slice.py                     section-aware slicer (notes sections weighted)
├── m_source_catalog.py                 LLM-facing source catalog
├── m_recipes.py                        analyst-curated recipe library
├── m_sources/                          per-source connectors (uspto_odp.py preferred for patents)
├── edgar.py                            SEC EDGAR puller
├── scoring.py                          Severity enum + weights
├── evtol_cohort.py                     eVTOL cohort runner
├── _evtol_outcomes.py                  outcomes (revealed at matrix time)
├── threedp_cohort.py                   3D printing cohort runner
├── _threedp_outcomes.py
├── configs/                            per-ticker configs (legacy; see ARCHITECTURE history)
└── data/
    ├── <ticker>/                       per-company filings + filings_index.json
    ├── _local/                         LocalProvider scratch (input/scores/evidence + .hindsight/.preslicer preserved iterations)
    ├── _evtol_cohort/                  per-company analysis output
    └── _threedp_cohort/
```

## Files of historical interest

- `blinded_5co.py`, `blinded_manual.py` — earlier blinded harnesses (pre-Provider-refactor)
- `_evtol_inputs.py`, `_evtol_scores.py`, `_local_inputs.py`, `_local_scores.py`, `_threedp_outcomes.py` — generator scripts for the LocalProvider JSON files
- `cohort_screen.py`, `cohort_v2.py`, `llm_cohort.py` — earlier cohort runners superseded by `unified_runner.py` + per-cohort modules
