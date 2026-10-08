# 0DTE module handoff

Last updated 2026-10-08. Start with [EXPERIMENT.md](EXPERIMENT.md) for the hypotheses
and [README.md](README.md) for execution/accounting invariants. Local manifests,
not this dated note, determine the active protocol and operating state.

## Module and repository boundary

This is the importable source-tree module `desk.odte`. It is **not yet a standalone
distribution**: the root `pyproject.toml` package allowlist does not include
`desk` or `officekit_ai`. Commands work from a checkout with its dependencies.
The forecast and report workers run as separate processes from the collector;
the matched side trial does not require a web server or a broker connection.

| Layer | Files | Dependencies |
|---|---|---|
| Rules and book simulation | `doctrine`, `templates`, `risk`, `shadow`, `storage` | Mostly stdlib; default paths point into this checkout |
| Data capture / orchestration | `capture`, `runner`, `calendar` | IBKR / `ib_insync`, local calendar and data; runner has desk account-registry and notification integration |
| Execution | `rail`, live branch of `runner` | Broker connection, desk account selection and risk/envelope context; separate authorization from paper research |
| Original research | `text_overlay`, `forecast_worker`, `volatility`, `arms` | Stdlib for analysis; `officekit_ai.models`/`intelligence` for inference |
| New matched evaluation | `edge_trial`, `edge_stats`, `render_edge_trial` | Reads original sealed artifacts; same intelligence adapter; no broker or office UI required |
| Displays / diagnostics | `render_arms`, `research_health`, `grader` | Local generated HTML/JSON; grader also reads live ledger |

The intelligence interface is `complete(Request) -> Response`. Local execution
uses the signed-in coding agent via the existing adapter; hosted execution uses
the configured API adapter. No inline provider API is added by this experiment.
The model resolver/local adapter currently depend on `officekit.runtime` for
hosted-mode checks. Some providers return no resolved model identifier; preserve
`unknown`, never promote the requested name into verified provenance.

Recommendation: keep one source of truth in Worker Placement until the boundary
is packaged. For a separate 0DTE repository, first extract a research-only package with
explicit data/config paths and an injected intelligence factory; move broker,
account, office-page and scheduling connections into optional adapters. Include
synthetic fixtures and offline CI. Test installation in a clean environment
without this checkout on `sys.path`. Then import the versioned package here,
rather than maintaining two copies. Extraction changes code fingerprints: start
a new future trial; keep existing registrations with their original checkout.
Do not import private development history or local `desk/data` as a shortcut.

## Runtime topology and files

```text
Gateway quotes -> runner (shadow) -> first T3 candidate -> arm decisions/outcomes
                       |                                 |
                       +-> hash-linked feature ledger    +-> report
public RSS + frozen premarket job -> original forecast ---+
                   |
                   +-> matched edge trial: text / no_text / prior-only numeric
                                      |                    |
                                      +---- sealed forecasts
                                                   + source arm outcomes -> evaluation
```

Default private roots under `desk/data/odte/`:

- `text_overlay/`: initial source pilot.
- `arm_experiment/`: factorial trial; `news/` may be its ongoing source.
- `edge_trial/`: independent matched evaluation.
- `research_archives/`: prior registrations retained intact.
- `chains/`, shadow/live ledgers: source market/execution observations. The
  entire `desk/data/odte/` tree is ignored; never force-stage runtime data.

Operational paths may be symlinks into a new, dated `research_trials/` directory
after a reviewed code change. Resolve those paths and read the active manifests.
The previous registrations and their source snapshot belong in `research_archives/`;
do not mix observations across them or infer routing from a historical date in prose.

Read `arm_experiment/manifest.json` to discover the actual source directories and
date routing. Read `edge_trial/manifest.json` for its source identity and start.
The matched trial stores immutable `runs`, `inputs`, per-condition `attempts`,
`forecasts`, and `completions`; reports are regenerable. Source run directories
contain corpora, model provenance and attribution. They are private even when
individual evidence excerpts originally came from public feeds.

## Commands

Use Python >=3.11 and the same interpreter for tests and scheduled runs. The
original pilot also has Python 3.9 timestamp compatibility coverage, but that
does not lower the project's supported Python version. Run from the repo root.

```sh
python -m desk.odte.research_health
python -m desk.odte.edge_trial --check
```

A new matched trial is registered once, **before its future first date**, using
an unused directory. Substitute the intended future date, do not replay the
historical date in this note:

```sh
python -m desk.odte.edge_trial --init --start-date YYYY-MM-DD \
  --root desk/data/odte/edge_trial --arms-root desk/data/odte/arm_experiment
```

Morning order (08:45–09:00 Eastern preparation, all completion before 09:15):

1. Run the original and matched preflights. An edge-only failure must not stop
   the original trial; an invalid original source prevents the dependent trial.
2. Select today's source from the arm manifest. Prepare its original job once,
   then run `forecast_worker --once --root <source>` once. Existing attempts are
   never retried to get a different forecast.
3. Run `python -m desk.odte.edge_trial --once` while still before the deadline.
   It reuses the saved corpus and makes two additional bounded model calls.
   No new source fetch or broker call occurs. A crash-reserved run cannot retry.
4. Ensure the already-authorized collector captures the opening observations,
   first candidate and path through exit. Do not start live mode as a remedy
   for missing research data. Power, network, Gateway and model authentication
   remain operational prerequisites.

After close, first run the original reports to finalize missing paths, then:

```sh
python -m desk.odte.forecast_worker --report --root <today-source>
python -m desk.odte.arms --report
python -m desk.odte.edge_trial --report --page ~/office/pages/odte_edge_trial.html
```

The generated page is served by the local office if that office folder is in use.
The edge worker has no internal scheduler or resident daemon. This office's
existing weekday morning/afternoon automation must explicitly invoke it; source
checkout alone does not schedule anything on another machine. Check the actual
automation and process state instead of trusting a handoff's old PID or status.

## Failure handling

- Code drift: fail visibly, retain old manifests/records, test changes and use a
  new future registration. No hash rewriting, retrospective prediction or
  pooled history across protocols. The sidecar can fail without breaking the
  original observer because original frozen files do not import it.
- Missing/late/failed prediction: report unavailable plus costs; never cash alpha.
- Incomplete quote path: unresolved label/P&L; retain stress scenarios separately.
- Provider exception: safe stage and exception class only; do not persist keys
  or full provider diagnostics. Failed responses and attempts are not deleted.
- Collector missing: restore only the previously authorized operating mode.
  Research test success does not authorize execution, a broker reconnect with
  orders, higher size, or automatic graduation.

## Validation and sharing

The public source of truth is `main` in `AjayTripathy/worker-placement`.
Follow [PUBLIC_RELEASE.md](../../PUBLIC_RELEASE.md): transfer reviewed source,
synthetic tests and documentation as patches; never merge private development
history. Keep actual experiment registrations and observations on their original
machine. Installing or updating this module does not migrate or restart an
existing experiment. Source changes alter fingerprints and require a new future
registration when adopting them for research.

```sh
python -m pytest --offline -q tests/test_odte.py tests/test_odte_execution.py \
  tests/test_odte_data_quality.py tests/test_odte_fixes.py \
  tests/test_odte_text_overlay.py tests/test_odte_arms.py \
  tests/test_odte_research_health.py tests/test_odte_edge_trial.py
```

New tests exercise matched information sets, absence of original-forecast
leakage, all-attempt costs, code freeze, one-shot reservation, late responses,
economic rejection despite low risk, calibration on skips, missing paths,
source digests, prior-only labels, fixed validation boundaries and HTML escaping.
Fixtures contain no actual brokerage or household data. Network and model calls
are fake in unit tests. A unit-test pass is not a successful real forecast.

Share reviewed source/tests/docs under the repository's Apache-2.0 code license.
That license does not license redistribution of RSS, broker or other third-party
data. Do not stage an entire working tree: unrelated work and previously tracked
private data may coexist. Review explicit staged paths and secret patterns.
No automatic upload/publication is part of the research worker.
