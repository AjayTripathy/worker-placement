# One office UI, local or hosted

Updated 2026-09-18. The same renderers, planning handlers, proposal pipeline,
Risk Officer and imports drive both runtimes. Google sign-in identifies the hosted
owner. There is no trading/execution API in either runtime.

## Use the new controls

- **Bring your office** (`/app/import`) opens the shared open-source onboarding
  directly: statements, holdings, income, natural-language intake and goals, then
  **Build my office**. Reopening resumes the same private draft. No existing office
  is replaced. **Upload a saved office** is a separate account-management option
  at `/app/import/saved` for a saved folder; only that flow needs replacement review.
- **Goals** has a visible navigation link in both shells. Describe one or several
  goals in plain language with a connected AI agent, or use the manual fields.
  Goal projections and strategy coverage use the existing shared planning model.
  Navigation wraps on small screens; it does not become a dropdown.
- **Office settings** appears in both shells. Locally, **Hosting & sync** opens
  the Google/device login, reviewed migration and automatic-sync controls.
- In hosted **Office settings**, connect your Anthropic key to enable chat,
  PDF/image extraction, strategy research, courts and pitch decks. Calls use your
  provider account and may incur charges. Existing `models.json` selects models;
  the hosted key supplies its conventional `ANTHROPIC_API_KEY` slot. Connecting a
  key does not automatically run pending proposals: open one and choose Retry.
- Connect **Alpaca** live/paper keys or **IBKR Flex** token/query ID in hosted
  settings. Flex must return XML with Open Positions / Lots. **Imports → Pull now**
  reads positions; later refreshes are explicit Re-pull actions. No order endpoints
  are called. A saved credential is checked by its provider when first used.
- **Imports** accepts CSV, PDF and images (20 MiB per hosted request). CSV is
  deterministic; PDF/images require an AI key. Original files are retained
  privately, staging keeps provenance, and existing reconciliation rules apply.
- Desktop gateways (TWS / IB Gateway), Downloads and desk imports run locally.
  Onboarding, Settings and Imports offer **Install the local app** with a guide
  for new offices and existing hosted exports. See [connector architecture](CONNECTOR_ARCHITECTURE.md).
  With automatic sync enabled, their saved balance updates reach the hosted copy
  while the local app is running. Cloud workers never scan the server's desktop.
- Home greetings use the browser's clock in both runtimes.

## Credentials and isolation

`runtime.hosted_office` supplies a ContextVar credential map, queue callback and
checkpoint callback. Model and supported broker lookups never fall back to process
environment or home-directory keys in this context. Extraction/discovery thread
pools copy the context for each submitted task. Do not replace this with temporary
`os.environ` mutation.

`hosting.app.credentials` stores secrets as a separate, KMS-envelope-encrypted
object under the verified UID/office namespace. Settings exposes connection presence
and a CAS generation, never saved values. Export, migration and sync exclude keys.
Disconnect clears the active credential object; provider revocation is needed to
invalidate any in-flight or retained historical copy. Existing cloud storage
retention applies. Custom provider plugins still need their own hosted integration.

## Durable background work

`hosting.app.jobs` uses Cloud Tasks with a dedicated OIDC delivery identity.
`POST /internal/office-job` verifies Google issuer/audience, verified service-account
email, and a small validated payload. A browser session cannot invoke a worker.
Job request bodies/results are encrypted, owner-scoped objects under `office-jobs/`;
Cloud Tasks carries identifiers, not office contents or provider keys.

An active office holds one job lease. Starting a job CAS-claims that pointer before
queue delivery. Reads continue; writes and migrations reject while work is active.
This avoids losing research to a simultaneous edit. Proposal stages checkpoint
through the same validated immutable-revision publisher. Status/results survive
process replacement and are accessible from Office settings. Browser fetch adapts
queued JSON operations to the same response contract used locally.

Workers CAS-claim a queued attempt once. Duplicate deliveries do not repeat a running
or finished call. A 30-minute expired attempt retains checkpoints and needs an
explicit resubmission; it is never silently retried at the provider. This is an
at-most-once attempt policy, not a claim of exactly-once provider billing. Calls
already in flight can still incur charges after an interruption. A stale worker
cannot publish after its lease expires or another job replaces it. Completed raw
requests are removed from the active job record; GCS deletes job records after
30 days. Queue dispatch is limited to two concurrent jobs across the service.

Hosted broker refreshes are explicit. Local auto-pull continues on its existing
schedule and can relay snapshots through office sync. There is no new automatic
AI research schedule.

## Opt-in offline sync

`officekit.cloud_sync` (distinct from financial-source `officekit.sync`) records
file digests for a common base in `.office-sync.json`. It binds origin, account
email and office UUID, and uses the existing bearer login and 1 MiB migration
chunks. It polls the lightweight revision pointer every 30 seconds while the local server runs; unchanged offices do not redownload retained documents. The five-day login
must be renewed when it expires; expiry pauses transfers with a visible error.

Identical copies establish a base. If only one copy changed, its saved files and
explicit deletions travel to the other copy. If both changed—or initial copies
have no known common base—nothing is overwritten. The UI lists differing files
and offers Keep local / Keep hosted. A choice is tied to both file maps and the
exact hosted revision; changed reviews are rejected. There is no automatic
financial-field merge. Unsaved browser edits are never synchronized.

Local downloads hold the existing reentrant process/file lock. A private recovery
journal records the prior bytes before replacement; failure restores them, and
server startup recovers an interrupted download. Successful downloads retain the
last five backups in `.sync-backups/`, then render saved facts without importing or
calling an AI model. These hidden files and credentials are never transferred.
Server activation checks the hosted digest and GCS generation, including any
running job lease. Runtime API-error notices stay local to their runtime; retained
research, commitments/history and previews travel with office facts.

## Validation and limits

Tests use synthetic households and mock provider responses: tenant/key separation,
thread context, stale settings/office revisions, worker authentication, duplicate
and interrupted delivery, proposal checkpoints, upload persistence, wrong-owner
access, two-way sync, deletion, conflicting edits, stale choices, account changes,
rollback and symlink refusal. Live deployment checks must include a synthetic
Cloud Tasks delivery; mocks alone do not verify IAM. Real paid AI calls and broker
accounts require user-provided credentials and are separate acceptance checks.

The existing 64 MiB / 1,024-document office limit remains. Office-scoped device
grants, team membership, self-service deletion and per-account storage/rate quotas
are still separate work. Do not describe these as shipped.

## UI ownership contract

All office screens and workflows, including onboarding, live in `officekit`.
The hosted service supplies authentication, encrypted persistence, credentials and
job execution, and mounts the same HTML under the owned office URL. Landing and
account-management screens may differ. Do not create a second hosted onboarding
form or replace onboarding with a migration UI. Desktop-only connections remain
local capabilities; explain their setup without changing the planning workflow.
