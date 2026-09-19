# Browser office migration — 2026-09-18

- Account pages always link **Bring an office** at `/app/import`. The browser
  prepares an allowlisted, hashed snapshot from a selected saved-office folder;
  nothing uploads until the user reviews and submits. Folder selection does not
  need a running local app. The original local files are retained.
- `/api/browser-migrations` and its chunk/activation routes enforce verified
  identity, exact Origin and CSRF. Do not loosen the bearer-only CLI migration
  routes. Both routes call the same `Offices` validation, encrypted staging,
  missing-chunk resume and revision compare-and-swap activation.
- The browser reads selection rules from the shared migration constants. Keep
  `office-import.js` in the public asset allowlist and Cloud Run staged sources.
  An existing different office revision requires an explicit checkbox; a newer
  revision rejects the activation. Provider keys stay outside snapshots/exports.

# Goals and visible navigation — 2026-09-18

- `render_goals.py` restores `/pages/goals.html` as a shared core page. The shell
  uses visible, wrapping links at every width; goal projections keep Goals active
  and link back there. Existing Home goals remain available.
- The prominent natural-language composer reuses `/goals/add` and the scoped
  intake agent. An office AI key is required; manual fields work without it.
  Missing keys, empty extraction and invalid goals return errors without changing
  saved facts. New goals always receive server-generated UUIDs.
- Hosted natural-language submissions use the existing durable job queue and
  tenant key. Manual add/remove stays synchronous. `back=goals` is an allowlisted
  return destination. Include `officekit/INTAKE_AGENT.md` in deployed sources;
  Python modules alone are not sufficient for intake.
- Verified 80 local goal/editor/regression tests and 29 hosted workspace/job
  tests, plus browser checks of desktop/mobile navigation and goal drill-down.

# Local / hosted parity — 2026-09-17

Read [HOSTED_PARITY.md](HOSTED_PARITY.md) for the current contract. The changes in
this section supersede older notes saying keys/jobs/imports/sync are unavailable.

- Both shells link Office settings. Same renderers and edit handlers; browser-local
  greeting. Hosted credentials use KMS storage and a ContextVar, never os.environ.
- Cloud Tasks handles long requests and proposal checkpoints. One job lease per
  office; duplicate deliveries do not replay paid calls. Owner-only status/results.
  Cloud Run staging now includes officekit_agents doctrine/templates and adapters.
- CSV and AI statement imports use the existing staging/reconciliation engine;
  original documents are retained. Alpaca/Flex are hosted read-only connections.
  Desktop gateways stay local. Hosted Re-pull is explicit, not a daily schedule.
- Opt-in `cloud_sync.py` shares saved files/deletions every 30 seconds. Distinct
  from the pre-existing financial `sync.py`. Never overwrite both-sided edits:
  hash-bound user choice, account binding, GCS CAS, file lock and recovery journal.
- Keys, device sessions and local recovery files never migrate/export. API-error
  notices remain runtime-local. Five-day device login expiry stops sync visibly.
- Do not run real broker/model calls or migrate the principal's household as QA.
  Use synthetic records and mocked models for financial mutations.
- Verification: 549 local tests (Python 3.9), 98 hosted/sync/packaging checks
  (Python 3.12), plus live synthetic Cloud Tasks/import/credential/export/sync
  acceptance. No real household was changed. Revision `worker-placement-web-00015-b52`.
- Open follow-ups: scoped upload/device grants, per-account quotas, self-service
  deletion, team membership and wider broker OAuth support.

---

## Google sign-in — 2026-09-17

Live on Cloud Run revision `worker-placement-web-00013-m4t` with 100% traffic. Google Auth Platform is in production and the `google.com` Identity Platform provider is enabled. A real Google login completed, preserved the existing account UID and returned the existing hosted office. All 82 relevant auth, migration, workspace and landing tests pass. Callback request logging is excluded; no Google client secret is shipped in the app.

Signup now uses Google OAuth through the existing Identity Platform account store.
`hosting/app/auth.py` starts `createAuthUri` CODE_FLOW and exchanges its callback
with `signInWithIdp`, bound to an HttpOnly browser session proof. `main.py` protects
start/completion with Origin and CSRF; callback HTML never reflects codes, and JS
clears the URL. The final Firebase token must prove Google, verified email, UID and
recent authentication. Existing office and CLI ownership remain UID-based.

Keep one-account-per-email enabled. Do not manually merge offices by email or trust
unverified provider claims. Account-linking/MFA requirements fail closed. New email
link requests return 410; old link completion remains for compatibility. Provider
secrets belong in Identity Platform only. The Cloud Run flag is
`GOOGLE_SIGNIN_ENABLED=true`; callback request URLs must be excluded from request
logs. Test Google account selection and actual sign-in separately from synthetic
email-link migration tests. Local and CLI device approval is unchanged.

# Shared hosted workspace shipped — 2026-09-17

- The hosted office now uses the local app shell, page renderers and manual mutation handlers through `hosting.app.workspace`. Do not build a separate hosted dashboard or start the local unauthenticated HTTP listener in production.
- `render_saved_office` preserves saved financial facts on GET. Shared core and extra rendering functions are also called by the local builder. Keep behavior changes in these shared modules.
- Hosted edits use verified owner identity, explicit office UUID, CSRF/Origin checks, a submitted revision, then an encrypted immutable revision and GCS compare-and-swap. Temporary folders are disposable; never keep a customer's office in module globals or a shared working directory.
- `officekit.runtime` isolates hosted capabilities. No local machine discovery, process-key fallback, arbitrary CSV paths, or detached background threads. Future AI keys must use tenant-scoped secrets. Proposals are saved as `awaiting_key`, with no paid research or court run.
- The HTML mounting adapter rewrites office links/forms and wraps fetch; converts inline event attributes to nonce-bearing listeners. Workspace-only same-origin framing and referrers support the shared iframe and native POSTs. Keep strict auth-page policies.
- Tests: `tests/test_hosted_workspace.py` covers all nine pages, preserved GET facts, durable edits after a new app instance, stale forms, concurrent save, owner isolation, CSRF, machine-path refusal, injected HTML and keyless strategy briefs. The related hosted/local regression suite and a synthetic browser save were verified. No real household was changed or migrated as a test.
- Still separate follow-ups: hosted AI credentials/jobs, statement uploads, live connectors, scoped transfer credentials, tenant deletion and stronger distributed request quotas. Local and hosted copies do not auto-sync.

# Hosting UI shipped — 2026-09-17

- The local shell now has **Host office**, opening `/hosting` separately. The flow is connect by email/device code, review saved files, then explicitly upload. Progress and retry stay in the page. Hosted replacement requires a checkbox tied to the reviewed revision.
- `hosting_ui.py` owns the local workflow; `render_hosting.py` renders it. `cloud.py` shares login and snapshot-upload helpers with the CLI. Never return device proofs/session tokens to the browser or collect them in the office snapshot.
- Review pins the account, origin, exact saved bytes, and hosted revision. Account/local-data changes require another review; hosted changes are rejected by activation. Do not remove these gates for a smoother-looking flow.
- The local route is protected by Host, Origin, and a per-server page token. Never add CORS access or deploy the local server on the public origin.
- Hosted views and device confirmation now direct users back to the local app. Scoped upload grants, quotas, and deletion remain future work. The shared workspace supersedes the original viewing-only release.
- Acceptance uses synthetic offices and mocked hosted storage. No real household migration is performed as a test; the user initiates that in the UI.

# Current handoff — installer, login, migration and seeded research

Updated 2026-09-16. Public origin: `https://worker-placement-web-653732113303.us-west1.run.app`.
Public product repository: `https://github.com/AjayTripathy/worker-placement`, branch `main`.
SignalOS is its research component. This repository starts from a reviewed snapshot
with one initial commit; it has no ancestry from the private development repository.
Do not merge private development history into this repository. See `../PUBLIC_RELEASE.md`.

- Public onboarding is `curl -fsSL <origin>/install.sh | sh`. The installer clones
  the complete repo and calls `start.sh`; subsequent visits use `./start.sh`.
  `wp` manages `.venv-worker-placement` and installs the assembled product.
- `./wp login` uses an explicit browser-approved device code and a local secret
  proof. Login uploads nothing. `./wp migrate --dir <office>` is the transfer action.
- Historical first release: hosted offices were saved snapshots with downloads
  and export. The shared workspace above supersedes that UI; court/research
  jobs, broker reconnects and the in-app hosting button are not implemented.
- Use [hosting/README.md](../hosting/README.md) for the actual storage/auth/locking
  contract. The longer onboarding plan still contains future requirements.
- Current research seed `seed-20260916-accounts` is pinned to `6207310c8`: 32,412 files from
  `verticals/` and `strategies/`, with 64 administrative/credential-shaped files
  withheld. Do not seed from a live worktree or customer office. Runtime only reads
  the seed bucket. Research is data, never executed on the hosted origin.
- Local app writers coordinate through `office_lock.py`. Keep lock ordering as
  file lock then legacy thread lock. Snapshot also detects outside changes, but
  cannot coordinate arbitrary external editors. Do not remove the barrier to
  speed up long-running courts without preserving atomic snapshot behavior.
- Next: scope upload credentials per office/manifest, add hosted editing against
  explicit revisions, per-account storage quotas, deletion/retention controls,
  team membership and distributed abuse limits. Preserve local export and identity.
- No real household was uploaded during implementation. Live acceptance uses
  synthetic accounts with generated no-email links, then removes their data.

Verification: `start.sh` bootstrapped on Python 3.9 and served a new scratch office
on port 8794. Hosted/local-page tests: 41 passed on Python 3.12. The combined
576-test run had two environment-specific failures: golden float text differs on
3.12, and that hosted test environment lacked the offline wheel build backend.
Both affected tests passed on the existing Python 3.9 test environment; do not
regenerate financial goldens for this startup change. The preceding full local
run passed 538 tests. Live Cloud Run revision `worker-placement-web-00006-frv`
passed synthetic device login, chunk resume, byte-identical export, replacement
revision gating, cross-account denial, and reads from small and large seed ZIPs.
Synthetic accounts, uploaded documents and CLI credentials were removed.

Publication preference (2026-09-16): the principal explicitly welcomes publishing
position history. Preserve positions and research; real financial account IDs and
credentials must be removed. The existing private product branch contains known
broker account IDs in 25 files, including historical order records, logs and code.
A visibility toggle is not ready until reachable Git history is also sanitized.
Do not equate position history with sensitive account identifiers or strip all
position records as a shortcut. The shared seed had three documents containing
known account IDs; the corrected seed uses stable anonymous account labels while
preserving holdings and research. The account alias mapping is never published.

The older checkpoint notes below are historical and are not current deployment
status. Background research/desk changes in the checkout are unrelated to this
release and must not be bulk-staged.

---

# Agent handoff — operating loop hardening

Updated 2026-09-13. Start with [OPERATING_CONTRACTS.md](OPERATING_CONTRACTS.md).

## Checkpoint and scope

The principal asked to commit the existing repository, implement a first pass at the
review suggestions, and leave architecture/handoff notes. Baseline checkpoint:
**`ddbe72fc1`**, `checkpoint: preserve current SignalOS and Worker Placement work`,
on `muni-current-state-and-utility-sleeve` (3,498 files after rename detection).
The follow-on change is a separate implementation commit; find it in the branch log.
No push, release, live broker action or reference-office mutation was performed.

Background: Worker Placement is the product; OfficeKit is the engine. The desk is
being deprecated by migrating its machinery through the office registries. At the
review, the reference office contained 32 imported desk theses and six pilot packs;
those imports were not evidence of an exercised native office court loop. Root
research architecture and the September 3 office tier document had fallen behind
the implementation.

This pass covers scoped custody reconciliation, honest strategy risk/pack labels,
a deterministic native lifecycle acceptance test, an offline paired evaluation
contract, tenant-specific exclusions and a portable wheel acceptance test. It does
not complete desk migration or certify the product ready for another live household.

## Where to work next

1. **Opt in one real adapter to complete coverage.** Use `fetch_snapshot` and
   `staging.validate_snapshot`. Obtain independently sourced account totals, stable
   account identifiers, security coverage, market-value currency and trustworthy
   economic timestamps. Test sale, settled cash, transfer, expiry, account removal,
   stale data and failed refresh. Existing adapters intentionally remain partial.
   Never derive the control total by summing the same rows being validated.
2. **Make legacy ownership explicit.** Existing manual cash/bond/option sleeves can
   overlap imports. Build a reviewable mapping before replacing them; the current
   reconciler retains them and emits warnings. Resolve account aliases across
   feeds, dated market marks vs basis, transfers and corporate actions. A separate
   goal capital-reservation ledger is still needed; taxonomy is not that ledger.
3. **Run one live office-native lifecycle.** Start with a permitted watcher/candidate,
   freeze evidence, convene the native docket/court, review the verdict, import
   actual custody, rebuild after restart, and later grade at the fixed horizon.
   Keep execution in its existing separate boundary. Do not invent a holding from
   a court result or mistake the synthetic test for this live acceptance gate.
4. **Build an independently labeled evaluation corpus.** Give analyst and court
   identical frozen evidence and explicit event probabilities. Record actions,
   cost, latency and separate claim audits before running `evaluation.compare`.
   Add meaningful sample size, stratification and uncertainty estimates. Do not
   claim the court beats one analyst from prompt complexity or fixture arithmetic.
5. **Finish portable capability extraction.** Missing fleet implementations are
   visible as `UNAVAILABLE`; they are not yet shipped. Migrate a bounded generator
   into a generic package with no private `desk/` dependency, then prove it from
   the installed wheel. Test actual connector dependency installation and a fresh
   household setup on supported Python/OS combinations.

Additional follow-ups: atomic publication of a complete rendered office; process
coordination around staging and outcome ledgers; per-position freshness surfaced
alongside model as-of dates; measured liquidity/financing and nonlinear strategy
stress; actual independent review of contributed packs. Keep these separate from
the existing first-order estimates and schema checks.

## Tests and operational notes

```sh
PYTHONPYCACHEPREFIX=/private/tmp/signalos-pycache python3 -m pytest -q tests/test_officekit*.py -m 'not integration' -rs
```

The final OfficeKit run passed **317 tests with one skip**, including building and
installing the wheel without dependency downloads. The skipped onboarding-video
test could not launch Chromium because macOS denied its Mach port registration.
HTTP browser-flow tests passed after granting localhost network access. The
saved-API-key test now mocks the home directory so a developer's key cannot change
its outcome. The acceptance tests use the host's Python 3.9; supported-version and
fresh-dependency release matrices remain outstanding.

Adjacent verification: `tests/test_signals_desk.py` passed **3 tests**, covering
fleet registration, strategy mapping and referenced implementation code.

Important tests:

- `test_officekit_reconciliation.py`: account-scoped sales/closures, source failures,
  stale marks, partial coverage, option identity, ETF identity, manual ownership,
  cost-only data, partial basis/lot information and a second household rebuild.
- `test_officekit_operating_cycle.py`: real native persistence with synthetic inputs;
  restart/cursor recovery; independent metric validation; tenant exclusions; stress
  coverage; authored pack vs adjudicated/custody truth.
- `test_officekit_portable.py`: no repo imports in the installed acceptance process;
  generic tape remains generic; missing fleet implementation fails explicitly.

The reference machine has live desk/log writers. They can dirty `desk/data/` and
`logs/` while you work. Do not reset, stash, overwrite or repeatedly checkpoint
those files to manufacture a clean tree. The original checkpoint captured all
unignored work; subsequent runtime writes are new activity. Stage your code/docs
paths explicitly. Public packaging excludes private data, but this private repo's
checkpoint/history contains the household/desk state; the existing publication
plan uses a fresh-history split.


## UI / UX implementation follow-up — 2026-09-13

The principal approved the UI review and requested the Home and Strategies design
work. The new daily brief and strategy workspace are implemented in the existing
Python renderers and static-page shell. Read the final section of
`OPERATING_CONTRACTS.md` before extending these views. Keep the shared goal
assessment, independent custody/review states, explicit action labels, allocation
validation and pending-cash exclusion intact.

The reference office pages were rebuilt from saved answers and the localhost
server restarted with source reload enabled. No target allocation, goal terms,
mandates or positions were changed through the browser. Its invalid legacy
100% stock / 2% bond target remains on disk; the warning asks for a reviewed save.
Unsaved preview tests were discarded with the explicit reload control. Existing
source refresh behavior remains part of the running server.

Browser acceptance used the actual Codex in-app browser at the ordinary panel
width, 390×844 and 1280×900. Verified: compact Home and Strategies layouts; all
navigation destinations available; held/review/draft filters; search and empty
results; direct goal-plan anchors; goal action labels; Risk Officer → Growth
navigation and selected state; browser Back returning to Risk Officer; sliders
reconciling to 100% with immediate projection changes; rebuild notifications
preserving unsaved slider input until explicit reload; import readiness; and
Signals' empty monitoring state. No broker, court or model action was submitted
for browser acceptance. A browser-tool timeout during Back testing recovered to
the correct page and active navigation; iframe DOM metric queries were not
reliable in this browser, so responsive acceptance used the rendered UI.

The final OfficeKit regression suite passed **334 tests, with one recorder test
deselected**. Focused renderer and contract checks also passed after final spacing
adjustments. Adjacent Signals Desk verification passed three tests. The new
`test_officekit_decision_ux.py` covers cross-page property affordability,
post-shock assessment without mutation, pending-cash exclusion, allocation
validation and invalid POST atomicity, legacy warnings, source ages/setup, and
held-versus-reviewed pack state. Golden Home/Strategies fixtures were updated for
the intentional redesign; endpoint and financial behavior assertions remain.
The final command explicitly deselects the onboarding-video test:

```sh
python3 -m pytest -q tests/test_officekit*.py -k 'not record_onboarding_walkthrough' --disable-warnings
```

An earlier explicit-file pytest command still ran that recorder despite `--ignore`
and regenerated the walkthrough GIF. That generated file is left unstaged alongside
its pre-existing changes. Interactive acceptance used the in-app browser.

Remaining product work is the live native lifecycle, complete custody coverage,
capital reservations, and calibrated risk/financing models described above. This
visual pass does not turn those research or data gaps into completed capabilities.
Do not reset unrelated runtime data or other agents' uncommitted changes.

## Source-boundary follow-up — 2026-09-14

Checkpoint `bea72ee79` preserves the then-current OfficeKit UI, inferred-commitment,
packaging, and generic-account merge changes (31 files). It is a checkpoint, not
resolution of every finding in the September 14 review. Runtime desk/log changes
were not swept into it. Later edits from other agents must remain separate.

The principal requested the complete-closure and partial-refresh fixes, while
deferring independent feeds that share a non-generic account label. `specific_account`
still selects the legacy matching policy for those labels; its name does not
establish economic ownership. Do not infer common ownership or independence from
a name, ticker, quantity, or value. An explicit source-to-owning-feed mapping is
future work, outside this patch.

The source observations already kept separate for generic/missing account labels
now stay separate in `staging.covers`, persisted equity contribution matching,
cost-only fallback and non-equity custody keys. Complete coverage can close only
its matching source contribution; partial omissions preserve the prior mark.
Cash/options/bonds append source ID to their key for generic accounts. Old keys
recover it from saved custody provenance, never from the newest unrelated feed.
Closure reports include the source. Already erased or ambiguously collapsed
historical contributions cannot be reconstructed without reviewing source data.

`tests/test_officekit_source_isolation.py` covers the reproduced $100/$200 cases,
partial/failed pulls, cost-only marks, cash/options/bonds, legacy key recovery,
missing identity, repeated reconciliation and a saved-office rebuild/restart.
The existing named-account deduplication tests remain unchanged to pin the
explicitly deferred behavior. Tests use synthetic sources and temporary offices;
no live account mappings or household financial inputs are changed by this patch.

Validation: the full OfficeKit suite passed **386 tests, 1 recorder deselected**
in 17.65 seconds using the explicit recorder-deselection command above. The
focused import/reconciliation/sync set passed 80 tests before the final two
integration/coverage cases were added; those passed in the full run. Diff
whitespace checks passed. No push or live broker/model action was performed.
# Latest handoff — commitments and capital, 2026-09-14

Receipt workflow is implemented: read COMMITMENTS.md's incoming-money section.
Capital previews receipt attribution to existing cash by stable sleeve ID, then
publishes receipt/reversal events inside answers.json. Never add a second cash
sleeve for a receipt or reduce the original expected gross in place. Partial
receipts allocate tax pro rata; withholding reduces the liability once. Imported
cash remains source-owned. Home and Scenarios use remaining pending net proceeds.
Validation: **468 passed, 1 deselected** (27.02s), including 34 receipt regressions.
Browser acceptance on a synthetic office recorded $2M against $2.25M reported
cash: pending fell to $3M, current tax became $600K, pending tax $900K, and cash
stayed $2.25M. Reference-office receipts were not recorded or inferred.

Next authorized work in this task: every strategy-creation door must generate a
substantive proposal using the SignalOS research/capability layer, native courts,
and Risk Officer review, yielding a pitch deck and specific proposed instruments.
This applies to ALL planner suggestions, goal-driven and ad-hoc strategies;
the non-tech rotation was an example, not the whole scope. Preserve origin and
evidence/verdict lineage. Strategy adoption is intent; custody and execution
remain distinct. The existing court/docket and pitch-builder directive should
be reused rather than claiming an unreviewed draft has passed court.

Review follow-up: the tax on the excluded pending inflow is now reserved against
that inflow by stable ID, not against today's cash. Independent/current taxes and
explicit payment schedules still reserve current cash. Do not revert to exempting
all taxes merely because a pending asset exists. Retirement household totals share
the lifestyle spending pool; a goal-page selector marks truly additional spend.
Unapplied previews expire in 24 hours, applied files in seven days (100-file cap);
before/after history remains durable. The legacy mortgage endpoint is tested for
cached forms. Public HTML previews now have explicit head/body wrappers.

Review validation: **434 passed, 1 deselected** (23.70s), including 15 new
regressions for linked tax funding and receipt, retirement reconciliation and
scenario overlays, preview expiry, and the legacy route. The rebuilt live Capital
page shows $249,288 current cash, $59,135.09 scheduled payments, $0 other current
reserves, and **$190,152.91 available**, with no shortfall. Its $1,671,491 modeled
tax remains visibly reserved against the pending inflow. The same-ID receipt
transition is covered synthetically; a durable receipt workflow is still future
work. No real financial inputs were replaced with test values.

The principal approved reliable mortgage/home/lifestyle editing followed by the
Capital & Commitments calendar. Read [COMMITMENTS.md](COMMITMENTS.md) before
extending this work. New modules: `commitments.py`, `commitment_routes.py`,
`render_capital.py`, and `officekit_ai/commitment_edit.py`. Shared affordability
uses resolved commitments. Do not revert confirmation to `/goals/add` or key
home/mortgage edits by name. The same-label independent-feed case remains deferred.

Verification includes real HTTP save/rebuild tests and browser editing against a
synthetic office. New cash planning tests stub provider calls. Run:

```sh
python3 -m pytest -q tests/test_officekit*.py -k 'not record_onboarding_walkthrough' --disable-warnings
```

Final validation: **415 passed, 1 deselected** (21.17s), including 28 new
commitment cases and the installed-wheel check. Browser acceptance covered the
mortgage/home/lifestyle/school-fee journey and desktop/390px layouts. The principal
office was rebuilt from saved answers, with a pre-build answers backup retained
outside the repo. Its server was restarted with source reload enabled. No real
mortgage terms, home values or spending assumptions were filled from test data.

The walkthrough recorder must be deselected (explicit test globs bypass an
`--ignore` intended to skip it). Do not run a headless browser as a substitute for
the authorized CUA browser review. Background desk/data/log changes are unrelated;
keep commits scoped. Existing principal financial inputs should only be rebuilt,
not replaced with acceptance values. The preceding implementation commits are
`bea72ee79` (checkpoint) and `d57f20e7a` (source-scoped refresh/closure fixes).

## Strategy proposal workflow — 2026-09-14

User direction: every suggested strategy should develop a proposal using SignalOS, native courts and the Risk Officer, ending in a pitch deck and actual investment implementations. All 31 planner responses, goal choices and ad-hoc creation now open a durable proposal page. Existing agent drafts have the same review door with frozen origin lineage. Read [STRATEGY_PROPOSALS.md](STRATEGY_PROPOSALS.md) before editing this workflow.

The code is split into `strategy_playbooks.py` (starting briefs), `strategy_proposals.py` (jobs/snapshots), `strategy_routes.py` (shared creation/review), `officekit_ai/strategy_proposal.py` (SignalOS → courts → risk → pitch), `render_proposal.py` (printable deck), and `officekit_research/funds.py` (primary issuer source registry). The Risk Officer's new shipped directive runs on the configured adjudicate slot.

Preserve: no purchase/reserve writes from proposals; current cash and contingent receipts stay separate; KILL/AVOID/WATCH/exclusions cannot receive positive allocations; program/option courts cannot become equity approvals; failed sources and unverified claims remain visible. Revisions freeze fresh evidence and retain predecessor records. Normal builds/GETs never start paid work.

Live acceptance hit Anthropic's insufficient-credit response before research could complete. The failure/retry view was checked in the browser; the completed deck was checked using explicitly labeled synthetic provider results. Do not describe that synthetic deck as a live recommendation. No real-office proposal was adopted or account balance changed for this test. See the proposal document for connector limitations and recovery behavior.

Validation at completion: **495 passed, 1 recorder deselected** across `tests/test_officekit*.py`. The distributable wheel built successfully and contains the proposal modules, fund source, Risk Officer directive and proposal contract; internal handoff remains excluded. The reference office pages were rebuilt from saved answers; sleeves, positions, incoming proceeds, receipt events, commitments and goals were unchanged. The live app is left at Create strategy.

## Shared API error banner — 2026-09-15

The principal requested a visible error bar when an API fails. `api_errors.py`
adds a persistent, dismissible shell banner, injected by `serve.py` so existing
saved pages gain it without a rebuild. It catches fetch/HTTP/JSON errors and
background proposal, native court, SignalOS and account refresh failures. Common
credit, credential, rate-limit and connection errors use readable messages;
credential-like strings are redacted and display uses text nodes.

Keep the notice store separate from balances and proposal facts. It retains at
most 20 active contexts; successful matching work clears a notice. Dismiss exact
UUIDs, not contexts: later failures must remain visible. The response header
`X-Office-API-Error-Id` closes the race between immediate display and polling.
The parent shell owns display/polling; child frames delegate, and rendered/exported
HTML files are not rewritten. Never add automatic POST retries or form reloads
to the error handler. Full details are in ARCHITECTURE.md.

Browser acceptance uses an isolated office with synthetic provider failures:
credit errors show immediately, typed drafts survive, dismissal persists, new
failures reappear, successful retries clear, and a background review notice links
to its page inside the shell. No real provider calls or financial edits are
needed to test error presentation. Keep the unrelated walkthrough GIF and desk
data/log changes out of this commit.

Validation: **504 passed, 1 recorder deselected** across `tests/test_officekit*.py`.
The live app was reloaded at Create strategy after verifying its form was empty;
no saved financial page or input needed rebuilding for this change.

## Email login and local-to-hosted direction — 2026-09-15

The principal asked for one-click local-to-hosted graduation with email login.
`HOSTED_ONBOARDING.md` makes **Host this office** the primary entry, followed by
verified email login and automatic transfer. Architecture now points to that
flow instead of requiring CLI device-code onboarding. This is a design contract,
not a shipped hosted service: no deployment/domain or authentication provider is
configured in the local product, no email was sent, and no office data was uploaded.

The proposed first release makes the cloud copy active after a verified transfer
and preserves the local snapshot. Local broker gateways need reconnect/relay;
their credentials must never ride with the office. Preserve office and record IDs,
reconciliation provenance and research history. A real snapshot barrier and atomic
hosted activation are prerequisites; current process-local locks are insufficient
for every concurrent producer. The auth/transfer protocol, connector behavior and
acceptance cases are in the new document. Do not ship a disconnected button that
claims an office is hosted. Provider/destination integration is the next dependency.

## Review fixes — 2026-09-15

Addressed the review of the proposal/error-banner patch. All three allocation
writers share the finite `(0, 100]` gate, with agent validation before ledger
recording. Strict financial serialization prevents NaN/Infinity publication.
Strategy POSTs now require an explicit page revision under the office write
lock, including decline and goal unadopt; only exact recorded-decision replay
bypasses the gate. Never substitute the latest revision when a POST omits it.
GET proposal forms use current answers while adoption retains its frozen
research/evidence checks. Rebuild saved strategy/scenario pages for their new
hidden revision fields.

`_failure` and the guarded HTTP entry points classify validation/provider/internal
errors as 400/502/500. Pass actual exception objects so unexpected failures log
full stderr tracebacks; public messages and staging/signal error summaries are
sanitized. Import/onboard no longer report errors as successful flash pages.
Partial uploads keep good sources, mark failed uploads manual, and reuse the
same banner context. Capability failures before recording no longer become
success, and full proposal queues create a linked, retryable notice.

Regression coverage lives in `test_officekit_review_regressions.py`; existing HTTP
proposal tests now send revisions. Browser acceptance used a synthetic office:
500 generic banner, 502 provider guidance, one notice, dismissal, HTTP 204 draft
save with no false error, and stale strategy rejection with typed draft retained
on Back. No provider calls or real investment decisions were made for acceptance.

Validation: **534 passed, 1 recorder deselected**. Live strategy/scenario pages
were rebuilt with their revision fields; all saved answers remained identical.
The live answers file parses as strict JSON and has no non-finite targets.

## 2026-09-15 — public entry and deployed email accounts

The landing page and email signup are live at
`https://worker-placement-web-653732113303.us-west1.run.app/`.
See `hosting/README.md` and `hosting/gcp/README.md` for the deployed boundary,
identities, verification and redeployment. Public presentation lives in
`officekit/public/` plus `render_landing.py`; a fresh local root shows it, `/start`
opens onboarding, and an existing office retains its normal app root. Public
pages never poll or inject private office error notices.

The separate FastAPI service issues verified five-day sessions through Identity
Platform. The default Google email handler redirects to `/auth/finish`; GET is
inert, the page clears URL credentials, and confirming the email exchanges the
single-use code. CSRF, exact Origin, session revocation and sanitized errors are
covered. Provider/session/replay/logout were checked with disposable synthetic
accounts without sending mail. Actual inbox delivery is still a separate check.

Do not mistake a hosted account for a hosted office. There is no office upload,
tenant document store, transfer grant, local relay or financial endpoint in this
service. Implement the existing hosted onboarding contract next. Current abuse
budgets are process-local and can reset or multiply across the two allowed
instances; replace with a shared limit before broader availability.

Historical deployment note: the product originally lived in a private SignalOS
branch. The current public repository is `AjayTripathy/worker-placement` on `main`,
created from a reviewed snapshot with new history. Keep the private development
repository private and transfer future changes only after review.
