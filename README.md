# Worker Placement

**Give every dollar a job.** Worker Placement brings your accounts, goals, commitments and investment decisions into a family office workspace. OfficeKit powers the product; SignalOS provides research and evidence.

- **[Get started with email](https://worker-placement-web-653732113303.us-west1.run.app/signup)** — private office snapshots and an included SignalOS research library.
- **[Run locally](officekit/README.md)** — one script installs dependencies, initializes your office and opens the app.
- **[Deployment and operations](hosting/README.md)** — authentication, migration, storage and verification.

The public [Worker Placement repository](https://github.com/AjayTripathy/worker-placement) includes the app and SignalOS research on `main`. No GitHub account is required to download it. Start with one command, which clones the full repository including research, installs the app and opens it:

```sh
curl -fsSL https://worker-placement-web-653732113303.us-west1.run.app/install.sh | sh
```

After cloning, **`./start.sh` is the only startup command**. It manages its own `.venv-worker-placement` environment; no activation or separate install is needed. Requires Git and Python 3.9+ (3.11+ recommended). Windows: `python wp start`. Use `--dir /path/to/office` for an existing office or `--port 8790` for another port. Default: `./office` at `http://127.0.0.1:8787`.

```sh
./wp login      # Email sign-in and device approval; uploads nothing
./wp migrate    # Saved office + retained research; keeps the local copy
```

Hosted offices currently support viewing and export. Editing, broker reconnects and cloud jobs remain local. Every hosted account can browse the same seeded research library; private office documents are never added to it. Manual entry and core planning need no API key. AI features use the providers you configure.

For product contributors: [architecture](officekit/ARCHITECTURE.md), [operating contracts](officekit/OPERATING_CONTRACTS.md), and [agent handoff](officekit/AGENT_HANDOFF.md).

## SignalOS research framework

A cross-record divergence framework. Detects gaps between what entities self-report (R) and what observable public records show (M), under known statutory or contractual relationships f. The signal is `R - f(M)`.

```
Signal value ≈ I × L × accessibility(M)
```

- **I** — financial benefit of non-compliance is large in absolute terms
- **L** — structural decoupling of obligation from enforcement (self-reported, weak penalty, agency silos)
- **accessibility(M)** — observable reality is in queryable public records at affordable cost

When all three are non-zero, the divergence is findable at scale.

## Repo layout

| Path | Purpose |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Full architecture: R/f/M abstraction, layer model, productization, operational discipline (Layer 3). Read this first. |
| [`TECH_DEBT.md`](TECH_DEBT.md) | Honest accounting of gaps between what `ARCHITECTURE.md` claims and what the code does — cross-vertical reuse, empty placeholders, calibration caveats, identified-but-not-built features. |
| [`vertical_ilr_scoring.md`](vertical_ilr_scoring.md) | I × L × accessibility(M) prescreening for candidate verticals. |
| [`core/`](core/) | Framework primitives — engine, models, protocols, registry, LLM adapter. |
| [`cli/`](cli/) | `signalos` CLI entry points (`run`, `report`). |
| [`store/`](store/) | SQLite signal store. |
| [`compiler/`](compiler/) | Reserved (placeholder for f-rule statute compiler). |
| [`sources/`](sources/) | Reserved (placeholder for cross-vertical source registry). |
| [`verticals/`](verticals/) | Vertical applications. See `verticals/README.md`. |

## Verticals built

| Vertical | What it detects | Status |
|---|---|---|
| `property_tax/` | Detroit/Michigan tax-uncap evasion (TV not reset post-transfer) | Built, citywide scan complete; held-out blinded re-run in `lasalle_v2/` |
| `rent_stabilization/` | NYC J-51 / RGB rent-stabilization overcharges | Built, NYC jurisdiction wired |
| `carbon_offsets/` | Voluntary carbon market satellite-vs-claim divergence (REDD+, methane, mangrove) | Built; 398 satellite-direct projects scanned, 96% underdelivering |
| `buyside_dd/` | Private deal data-room divergence (Section 8 RE, venture pre-orders, etc.) | Built; FCRE2 + AHC validated |
| `public_co/` | Public-co SEC-filing forensic divergence screen (Nikola, Lordstown, eVTOL, 3D printing); runs forward and as backtest | Built with subagent firewall + USPTO ODP + slicer fix |

## API keys

**Strictly speaking, zero API keys are required.** Every M-source is independently optional. When a connector has no key (or fails for any other reason), the claims it would have verified become `UNVERIFIABLE` — the rest of the pipeline continues. Per the operational discipline (Layer 3 §2 in `ARCHITECTURE.md`), `UNVERIFIABLE` is correctly read as "no data" rather than "clean", so the framework degrades honestly.

What each key unlocks (all free):

| Key | Unlocks | Without it | How to obtain | Where to put it |
|---|---|---|---|---|
| **Anthropic** | LLM-driven claim extraction + recipe picking + severity scoring across `property_tax` (LLM exemption-rule fallback behind `--llm`), `buyside_dd` (claim extraction in `pipeline.py`), `public_co` (`ApiProvider` mode) | Use the local-LLM shim path below — `LocalProvider` for `public_co`, hand-written `Claim` schema for `buyside_dd`, omit `--llm` for `property_tax` (SQL-only screen). | [console.anthropic.com](https://console.anthropic.com/) | `export ANTHROPIC_API_KEY=sk-ant-...` (env path) **and/or** `~/.anthropic_api_key` mode `0600` (file path used by `public_co/llm_pipeline.py`). |
| **USPTO ODP** | `uspto_odp.query_assignee` patent verification in `public_co` (preferred over deprecated Google Patents) | Patent claims become `UNVERIFIABLE`. The Nikola-pattern (claimed IP areas not present in granted portfolio) won't fire. | [data.uspto.gov](https://data.uspto.gov/) → request key | `~/.uspto_api_key` mode `0600`. Header: `X-API-KEY`. |
| **HUD FMR** | Section 8 Fair Market Rent comparison in `buyside_dd` (FCRE2-style "rent above HUD FMR cap" detection) | Rent-vs-FMR claims become `UNVERIFIABLE`. The other 13 buyside_dd connectors (SEC EDGAR, OSHA, building permits, state corp registries, etc.) still run. | [huduser.gov/portal/dataset/fmr-api.html](https://www.huduser.gov/portal/dataset/fmr-api.html) → register | `export HUD_API_TOKEN=...` |
| **Census ACS** | Demographic context (B25031 rent-by-bedroom comps, 5-year estimates) in `buyside_dd` | Demographic comps become `UNVERIFIABLE`. The deal-level analysis still runs without comp context. | [api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html) | `export CENSUS_API_KEY=...` |
| **NREL** | Higher rate limits on `nrel_fuel.query_alt_fuel_stations` in `public_co` (hydrogen / EV charging station counts) | Falls back to `DEMO_KEY` — works but rate-limited; can return errors on heavy cohort runs. | [developer.nrel.gov/signup](https://developer.nrel.gov/signup/) | Code currently hard-codes `DEMO_KEY`; to use a real key, set `NREL_API_KEY` env var and edit `verticals/public_co/m_sources/nrel_fuel.py`. |
| **PatentsView** *(legacy)* | `buyside_dd/connectors/uspto_patents.py` legacy patent path | Patent claims via that connector become `UNVERIFIABLE`. Use USPTO ODP in `public_co` instead — it supersedes this. | [patentsview.org/apis/keyrequest.html](https://patentsview.org/apis/keyrequest.html) | `export PATENTSVIEW_API_KEY=...` |

### Running without an Anthropic API key (local-LLM shim)

The framework's LLM-driven steps (claim extraction, recipe picking, severity scoring) can be performed by a local LLM session — including a Claude Code subagent — instead of by an API call. This works because the pipeline factors into mechanical steps (filing pulls, query execution, cohort aggregation — pure Python, no LLM) and LLM-driven steps that consume / produce structured JSON files.

Per vertical:

| Vertical | Without Anthropic API key |
|---|---|
| `property_tax/` | Omit `--llm` flag — SQL-only screen runs end-to-end. The LLM is only consulted for rare PA210 / OPRA exemption-rule fallback; the divergence detection itself is pure Python. |
| `rent_stabilization/` | No LLM dependency at all. Runs regardless. |
| `carbon_offsets/` | No LLM dependency. All scoring is satellite-vs-claim arithmetic. |
| `buyside_dd/` | `pipeline.py` already gates on `os.getenv("ANTHROPIC_API_KEY")` and runs claim extraction only if present. Without the key, you can hand-write claims to the same schema (`schemas.py:Claim`) and the rest of the pipeline (typing, f-rules, source-atlas, comparison, scoring) runs unchanged. |
| `public_co/` | Use `LocalProvider` instead of `ApiProvider`. Spawn a Claude Code subagent (or any local LLM session) per ticker using the template at [`verticals/public_co/SUBAGENT_PROMPT_TEMPLATE.md`](verticals/public_co/SUBAGENT_PROMPT_TEMPLATE.md) — the subagent writes `data/_local/<ticker>.{input,scores}.json`, then `python3 -m verticals.public_co.<cohort>_cohort --provider local` runs the matrix without any API call. This is exactly how the eVTOL and 3D-printing cohorts in this repo were scored — there was no Anthropic API key in the loop for either run after the initial smoke tests. |

The shim approach has one advantage beyond cost: it provides a structural blinding firewall. A subagent doesn't share the main session's context, so it can't be contaminated by hindsight knowledge of cohort outcomes. See `signalos/ARCHITECTURE.md` Layer 3 §4 for the full discipline rationale.

### Per-vertical signal coverage by key

Every vertical runs without any keys — claims that would have used a missing connector return `UNVERIFIABLE` and the rest of the pipeline continues. This table shows which keys add which signal coverage.

| Vertical | Runs without any key? | Keys that add signal coverage |
|---|---|---|
| `property_tax/` | **Yes** — full SQL-only uncap screen runs (the eVTOL-cohort-equivalent finding for Detroit doesn't need any keys) | **Anthropic** unlocks LLM exemption-rule fallback for PA210/OPRA edge cases |
| `rent_stabilization/` | **Yes** — RSL overcharge detection runs fully | None — no LLM dependency, no paid sources |
| `carbon_offsets/` | **Yes** — satellite-based scans run fully on bundled GMW + public Hansen GFC tiles | None |
| `buyside_dd/` | **Yes** — degraded mode: SEC EDGAR + OSHA + permits + state corp registries + Wayne County all run keyless. Hand-write `Claim` objects to substitute for LLM extraction. | **Anthropic** unlocks LLM claim extraction from raw PDFs/decks. **HUD FMR** unlocks Section 8 rent comparison. **Census** unlocks demographic comps. |
| `public_co/` | **Yes** — use the local-LLM shim (subagent writes input.json + scores.json); cohort runner reads via `LocalProvider`. This is how the eVTOL and 3D-printing cohorts in this repo were actually scored. | **Anthropic** unlocks `ApiProvider` mode (no subagent firewall needed). **USPTO ODP** unlocks patent verification. |

**SEC EDGAR User-Agent:** EDGAR doesn't require an API key but requires a descriptive User-Agent including a contact email per their fair-access policy. The connectors set this; if you fork them, edit the `user_agent` field to your own contact info.

## Quickstart

```bash
# Install
pip install -e .

# Set up keys (minimum for property_tax + public_co)
echo 'sk-ant-YOUR_KEY' > ~/.anthropic_api_key && chmod 600 ~/.anthropic_api_key
echo 'YOUR_USPTO_KEY' > ~/.uspto_api_key && chmod 600 ~/.uspto_api_key
export ANTHROPIC_API_KEY=sk-ant-YOUR_KEY  # also set env-var path for buyside_dd / core/llm.py

# Property tax — Detroit, one zip code
signalos run --zip 48238 --deeds --llm

# Generate a report from the SQLite store
signalos report --tier high --csv out.csv

# Public-co (eVTOL cohort, backtest mode)
python3 -m verticals.public_co.evtol_cohort --provider local --reveal-outcomes
```

See each vertical's README for vertical-specific commands.

## Documentation

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — framework architecture, R/f/M decomposition, three input pipelines, productization layer, operational discipline rules
- [`verticals/public_co/ARCHITECTURE.md`](verticals/public_co/ARCHITECTURE.md) — public-co-vertical-specific machinery (subagent firewall, slicer, USPTO ODP, calibration heuristics)
- [`verticals/public_co/EVTOL_FORWARD_TEST.md`](verticals/public_co/EVTOL_FORWARD_TEST.md) — eVTOL cohort case study (with hindsight-bias caveats)
- [`verticals/property_tax/lasalle_v2/`](verticals/property_tax/lasalle_v2/) — held-out blinded re-run of the Detroit LA Salle analysis
