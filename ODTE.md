# Run the 0DTE research module by itself

`desk.odte` is a source-tree Python module. You can run its tests, collector,
forecast workers and reports without starting Worker Placement's web app.
It is not yet a separately published pip package. Use a checkout of
[`AjayTripathy/worker-placement` on `main`](https://github.com/AjayTripathy/worker-placement/tree/main),
and run every command below from its repository root.

For a future LLM: read [the module README](desk/odte/README.md), then
[AGENT_HANDOFF.md](desk/odte/AGENT_HANDOFF.md) and
[EXPERIMENT.md](desk/odte/EXPERIMENT.md). The module's [AGENTS.md](desk/odte/AGENTS.md)
records the prospective-research and sharing rules.

## 1. Install only the research/test dependencies

Use Python 3.11 or 3.12 on macOS/Linux; the file locks require POSIX. Python 3.12
is the tested collector runtime. No web-server installation is required.

```sh
python3.12 -m venv .venv/odte
.venv/odte/bin/python -m pip install -r desk/odte/requirements.txt
.venv/odte/bin/python -m desk.odte.runner --help
.venv/odte/bin/python -m desk.odte.forecast_worker --help
.venv/odte/bin/python -m desk.odte.edge_trial --help
```

The minimal requirements support the signed-in local agent and broker-free
tests. Local model calls require the existing Codex CLI/desktop installation and
an active sign-in. Model/provider choices come from `models.json` and optional
`models.local.json` in the folder passed with `--office`; an empty configuration
folder uses local defaults. The folder need not contain a household or web app.
Check the resolved choice before registration; existing manifests freeze it.

An explicitly configured API provider additionally needs its SDK (`openai>=2,<3`
or `anthropic>=0.80,<1`) and credentials via the configured environment variable.
Keep credentials out of the repository and experiment manifests.

## 2. Verify without a broker or model call

```sh
.venv/odte/bin/python -m pytest --offline -q \
  tests/test_odte.py tests/test_odte_execution.py \
  tests/test_odte_data_quality.py tests/test_odte_fixes.py \
  tests/test_odte_text_overlay.py tests/test_odte_arms.py \
  tests/test_odte_research_health.py tests/test_odte_edge_trial.py
.venv/odte/bin/python -m desk.odte.research_health
```

A fresh checkout reports `not_registered`; that is expected. Local manifests,
source excerpts, forecasts and outcomes are not part of the shared code.
The tests use synthetic data and fake model/broker transports.

## 3. Register a new paper experiment

Do this only on a new installation or in unused experiment directories.
On an existing installation, inspect the manifests and run preflight instead of
reinitializing them. Choose a future **Eastern session date** before running:

```sh
# Replace this placeholder with your intended future session date.
ODTE_START_DATE=YYYY-MM-DD

# An ongoing premarket source; --office only supplies model configuration.
.venv/odte/bin/python -m desk.odte.forecast_worker --init --premarket \
  --office ~/office --submitter local-research
.venv/odte/bin/python -m desk.odte.arms --init \
  --start-date "$ODTE_START_DATE" --forecast-root desk/data/odte/text_overlay
.venv/odte/bin/python -m desk.odte.edge_trial --init \
  --start-date "$ODTE_START_DATE"

.venv/odte/bin/python -m desk.odte.research_health
.venv/odte/bin/python -m desk.odte.edge_trial --check
```

This example uses one ongoing source. The existing office may instead use a
one-day pilot followed by a continuation: follow its arm manifest's source paths
and date routing, not the example's path. Registration hashes code and settings.
An edited frozen dependency requires a new future trial; never rewrite the old
hash or recreate a missed forecast.

## 4. Capture and run the morning forecasts

Market capture needs IB Gateway/TWS configured for the code's current endpoint,
`127.0.0.1:4001`, and live XSP/SPX/VIX1D market-data access. The collector is a
separate foreground process. Run a single instance, without `--live`:

```sh
.venv/odte/bin/python -u -m desk.odte.runner --daemon
```

It connects around 09:28 Eastern and captures the opening and intraday quote
path. Keep it running through the exit. It does not start a web server. The
existing desk can emit configured end-of-day notifications; this is not an
isolated new notification service. Do not start a second collector if one is
already running. Real-money execution is outside this quickstart.

In a second terminal at **08:45–09:00 Eastern** (05:45–06:00 Pacific for the
current schedule), prepare and run the applicable source, then the matched trial:

```sh
.venv/odte/bin/python -m desk.odte.forecast_worker --prepare \
  --root desk/data/odte/text_overlay
.venv/odte/bin/python -m desk.odte.forecast_worker --once \
  --root desk/data/odte/text_overlay
.venv/odte/bin/python -m desk.odte.edge_trial --once
```

All forecasts must finish strictly before **09:15 Eastern / 06:15 Pacific**.
The matched worker reuses the original saved corpus for two additional isolated
model calls and a numerical control. It does not fetch newer evidence.
Run it only on or after its own start date. Missing prior-day capture is an
explicit input gap on a fresh installation; never substitute future data.
Existing attempts and crash reservations must not be retried for another answer.

## 5. Review after the close

At 16:20 Eastern / 13:20 Pacific, with the source path selected from the manifest:

```sh
.venv/odte/bin/python -m desk.odte.forecast_worker --report \
  --root desk/data/odte/text_overlay
.venv/odte/bin/python -m desk.odte.arms --report
.venv/odte/bin/python -m desk.odte.edge_trial --report
```

Open `desk/data/odte/arm_experiment/report.html` and
`desk/data/odte/edge_trial/report.html` directly in a browser. Their companion
JSON files contain the underlying metrics. To copy the matched report into an
existing local office, append `--page ~/office/pages/odte_edge_trial.html` to
the last command. The office server is optional.

This checkout does **not** install a scheduler. Schedule the morning preparation,
forecast and afternoon review explicitly on the machine running the collector.
The user's existing automation is machine-local and is not installed by Git.

Results are hypothetical, with assumed fees and minute-sampled paths. Missing
outcomes remain unknown. Read [the experiment's coverage gaps](desk/odte/EXPERIMENT.md)
before interpreting a winning arm or forecast score as evidence of an edge.
