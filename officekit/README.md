# Worker Placement

Your family office workspace for accounts, commitments, scenarios and reviewed investment proposals. OfficeKit is the engine; SignalOS supplies research and evidence.

[Hosted signup](https://worker-placement-web-653732113303.us-west1.run.app/signup) · [Local guide](https://worker-placement-web-653732113303.us-west1.run.app/guides/local)

## One execution to run locally

Paste this into your terminal:

```sh
curl -fsSL https://worker-placement-web-653732113303.us-west1.run.app/install.sh | sh
```

The script clones the full `main` branch of [Worker Placement](https://github.com/AjayTripathy/worker-placement) into `worker-placement`, including research datasets. It creates an isolated Python environment, installs the product and connector dependencies, prepares `./office`, starts the localhost server and opens the browser. No separate clone, activation or pip commands are needed. You can inspect `/install.sh` before running it.

Prerequisites: Git and Python 3.9+ (3.11+ recommended). No GitHub login is required. The installer does not reset an existing checkout or change its branch. AI features need a provider key; manual entry, CSV import and core planning do not.

On subsequent runs, from the downloaded repository:

```sh
./start.sh
```

Your office is preserved and unchanged dependencies are reused. Stop with Ctrl+C. On Windows, clone branch `main` and run `python wp start` from the checkout.

Use `./start.sh --dir /path/to/office` to open an existing office, `--port 8790` for another port, or `--no-browser` to suppress browser opening. The local server binds only to localhost. Keep it private; hosted access uses the separate authenticated service.

## Build your office

Review imported positions and their sources, enter assets and debts, add goals and commitments, then build. Start with Home and Capital & Commitments. Scenario Planner stress-tests the plan; strategy creation produces a proposal for research, courts and Risk Officer review. It never places trades.

Back up the entire office folder. `answers.json` and `balance_sheet.json` preserve your plan; the folder also retains research, decisions and source history. `models.json` stores provider/model choices and environment-variable names, never API keys. Set the corresponding provider keys in your environment for chat and courts.

## Bring your office from the website

Sign in and choose **Bring an office** from your workspace (also available at
[/app/import](https://worker-placement-web-653732113303.us-west1.run.app/app/import)).
Choose the saved office folder containing `answers.json` and `balance_sheet.json`,
review the selected documents, then choose **Upload and open office**. You do not
need to run the local server or use terminal commands. Use a desktop browser with
folder selection support. Save local edits before selecting the folder.

Selection prepares the review on your computer; the upload starts only when you
choose it. Existing hosted records require explicit replacement confirmation tied
to the revision you reviewed. Uploads can resume with the same saved files, and
hosted connection keys remain in their separate encrypted store. Your local files
remain available. Connect an AI key in hosted **Office settings** for AI features.

## Host your office from the local app

Choose **Office settings → Hosting & sync** in the local app's top bar. The hosting page opens separately so your workspace stays available.

1. **Connect:** choose **Sign in with Google**, open the sign-in page, and approve the matching device code. Return to the local hosting page; it updates automatically. Signing in uploads nothing.
2. **Review:** choose **Review saved files** to see the signed-in destination, saved balance date, document count, size, and exact file list. Save any form edits first.
3. **Upload:** choose **Upload my office**. Follow the progress, then choose **Open hosted office**. If a different snapshot already exists, explicitly confirm its replacement first.

Your local copy remains available. An interrupted upload can be retried. If the local files, signed-in account, or hosted snapshot changed, review again before proceeding. The hosted office uses the same workspace, with private connection settings, statement imports and background research. Enable **automatic sync** below the migration controls to keep both saved copies in step; conflicting edits pause for a reviewed choice. See [the local/hosted guide](HOSTED_PARITY.md).

The terminal commands below remain available as an alternative.

## One command to log in

```sh
./wp login
```

Your browser opens hosted Google sign-in. Choose your Google account, then compare the terminal's device code and select **Connect this device**. On another browser/device, reopen the terminal's connection URL after signing in. Login does not upload an office. The local credential is stored outside the office with owner-only permissions and expires with the verified session (up to five days). Run login again when it expires.

## One command to migrate

```sh
./wp migrate
# Existing office elsewhere:
./wp migrate --dir /path/to/office
```

Migration copies the built office and its retained research, preserving its identity and original document bytes. It resumes missing chunks, checks hashes, validates the saved data and atomically activates the hosted revision. The local copy stays available. An exact repeat returns the same receipt; later local edits sync only after you explicitly enable automatic sync in the local UI.

Included: the saved answers/balance sheet, context, staging, model variable names, decisions/learning/signal records and supported documents under `research/`, `attachments/`, `documents/`, `transcripts/` and `strategy_proposals/`. Supported retained formats: JSON, JSONL, Markdown, text, CSV, PDF, PNG, JPEG and WebP. Limits: 64 MiB and 1,024 files per snapshot. Credentials, symlinks, generated HTML, executable files, other directories and Git history are excluded or refused. Research outside the office folder stays in the repository; move a supported document into `research/` to retain it with your office.

The hosted office reuses the local workspace and supports planning edits, private documents, AI connections, background research, statement imports and complete export. Edit online or locally; automatic sync is opt-in from the local app. To replace an existing hosted snapshot from the CLI, copy its digest from **Migration receipt** and pass `--replace-revision DIGEST`; a stale digest is refused. The website provides a reviewed replacement checkbox.

Every account also receives access to a shared, read-only SignalOS seed library. Version `seed-20260916-accounts` includes 32,412 files from the tracked research at commit `6207310c8`; 64 administrative or credential-shaped files were withheld. This library is separate from private customer uploads and retains original research dates.

## Troubleshooting

- **Repository not found:** use `https://github.com/AjayTripathy/worker-placement.git` and branch `main`.
- **Port in use:** open the existing server or choose `./start.sh --port 8790`.
- **Wrong office:** pass the same `--dir` to start and migrate. Default is `./office`.
- **Migration interrupted:** rerun the same migration command; verified chunks are reused.
- **Snapshot changed:** wait for local work to finish and retry. App writers coordinate with the snapshot lock; external editors should be idle.
- **Credentials detected:** remove secrets from retained documents and keep provider keys in environment variables.
- **Google sign-in:** use the same Google email as your existing hosted account. If an embedded browser is rejected by Google, open the sign-in page in your regular browser, then reopen the device connection URL there.

## Development

[Architecture](ARCHITECTURE.md) · [Operating contracts](OPERATING_CONTRACTS.md) · [Hosted onboarding](HOSTED_ONBOARDING.md) · [Hosting operations](../hosting/README.md) · [Packaging](../officekit_dist/README.md)

```sh
python3 -m pytest -q tests/test_officekit*.py -k 'not record_onboarding_walkthrough'
# Hosted tests also require hosting/app/requirements.txt, pytest and httpx.
python3 -m pytest -q tests/test_hosted_web.py tests/test_hosted_migration.py
```
