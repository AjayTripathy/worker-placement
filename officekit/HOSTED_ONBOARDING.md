# Host this office: local-to-hosted onboarding

Product direction: 2026-09-15. The principal requested one-click graduation from
a local office to a hosted office with email login. This document specifies the
full product direction. The first command-line release now implements email login,
explicit device approval, resumable migration, encrypted durable office snapshots,
the shared office workspace with manual editing/export, and shared seeded research. Start with the public installer,
then choose **Host office** in the local app, or use `./wp login` and `./wp migrate`.
The browser flow now supports device sign-in, an explicit file review, resumable
upload, and confirmed replacement. Hosted AI keys/jobs, statement uploads, Alpaca/IBKR Flex connections and opt-in
offline sync now ship; see [HOSTED_PARITY.md](HOSTED_PARITY.md). Scoped upload-only
grants and broader broker OAuth remain planned.
The sections below describe that fuller target, not an inventory of shipped work.
See [hosted operations](../hosting/README.md) for implemented boundaries and limits.

## Current release — 2026-09-17

The public installer clones the full product branch and executes `start.sh`.
`start.sh` bootstraps dependencies and runs the local office in one execution.
The explicit login command approves a 15-minute device intent using verified email
and a matching code. The local CLI retains a five-day session outside the office.
It is a session credential, not yet an office-scoped upload grant.

`migrate` snapshots the built office under the shared process/file lock, checks
stable bytes and file membership, and transfers allowlisted documents in resumable
1 MiB chunks. Limits are 64 MiB and 1,024 documents. The server derives ownership
from the verified UID, validates identities/dates/schema/hashes, retains immutable
encrypted revisions and uses a GCS generation precondition to activate one revision.
A replacement requires the current hosted digest; exact retries are idempotent.
The saved model is preserved, never refreshed from external paths in the cloud.

The hosted office reuses the local shell, page renderers and manual editing handlers
behind authenticated, owner-scoped routes. It does not expose the local HTTP listener,
machine integrations or process-wide AI credentials. Hosted edits save as encrypted
immutable revisions with stale-form and concurrent-write protection. Retained customer
research stays private. A separate immutable SignalOS seed library is available
to every verified account; shared seed updates never rewrite customer documents.

## Customer experience

The primary entry point is **Host this office** in the local app. Command-line
linking is an optional interface to the same process, never a prerequisite.

1. The local app shows the office name, the actual hosted service destination,
   and a concise explanation: upload this office's financial records, documents,
   private context and research history; keep the local copy. The customer enters
   an email and selects **Continue with email**. An authenticated customer can
   use **Host this office** as the single transfer action after this information
   is visible. Any plan/price must be explicit before accepting a paid plan.
2. A managed authentication provider verifies the email by a sign-in link. An
   email code is the fallback for cross-device or intercepted-link cases. Existing
   customers sign in; new customers create an account through the same flow.
3. The app shows **Preparing → Transferring → Checking → Ready**. The customer
   does not download, select or manually re-upload an archive. Transfer continues
   from the local server, even if the email opens on a different device. The local
   server must remain running until the transfer is acknowledged.
4. The hosted office opens at the matching workspace with its original office
   identity, holdings, goals, commitments, decisions and completed research.
   Repeated clicks resume the existing transfer; they never create another office.

Only the explicit hosting action authorizes the transfer. Typing an email,
opening the local app, ordinary page loads and email-link previews never upload
financial records. Signing in later only opens the existing hosted office.

## Email identity and transfer authorization

Use a managed email authentication service behind the hosted API. Its verified
subject ID owns the tenant membership; the submitted email string and a client-
supplied tenant ID confer no access. Email changes must not change office identity.
Keep auth-provider choices separate from the office document contracts.

The local server prepares a transfer manifest and registers a short-lived
transfer intent. The cloud pairs that intent with the verified account and the
customer's hosting action. A high-entropy proof retained by the initiating local
server is required to claim the resulting upload grant. Possession of a transfer
ID or an email URL alone is insufficient to fetch or overwrite an office.
Grants are short-lived and restricted to the intended tenant, office, manifest
and operation. Transfer registration and polling are bounded and rate-limited.

Email links land on the hosted origin; they do not redirect credentials to an
arbitrary localhost callback. Use exact approved redirect destinations, HTTPS,
server-held provider secrets, secure hosted sessions, and replay protection.
Keep login tokens and transfer proofs out of application logs. A link-scanner GET
must not consume a transfer or cause an upload; use a provider-supported
confirmation/code flow when an additional user interaction is necessary.

Google Cloud project `worker-placement-508717` is the selected destination.
Use Firebase Authentication email-link sign-in for the first hosted deployment;
see [the GCP setup](../hosting/gcp/README.md) for the selected services and verified
setup status. Enable Email/Password and email-link sign-in, authorize only the
actual hosted origin, and verify mail delivery before exposing the local button.
The code-entry fallback remains an acceptance requirement requiring a supported
provider flow; do not assume Firebase email links provide an email OTP API.
Provider reference: [Firebase email-link authentication](https://firebase.google.com/docs/auth/web/email-link-auth).

## Transfer and activation

The export is an explicit, versioned collection of office documents and retained
artifacts. Do not zip an arbitrary filesystem tree. Preserve source and record
identities, original as-of dates, custody provenance, partial/complete coverage,
receipt history, personal context, proposal checkpoints and adjudication lineage.
Transfer only artifacts actually retained; do not claim recovery of missing files.

Include validated model-slot configuration without credentials. Never collect
environment files, credentials, login/transfer tokens, local gateway sessions,
unrelated paths, or executable plugins. User-authored packs remain untrusted data.
Regenerate application pages with the hosted renderer; do not execute uploaded
HTML or scripts on the authenticated app origin. Retained document previews must
be isolated from that origin.

Snapshot a coherent office revision. Today's process-local locks and separately
atomic file writes do not provide this across all producers: a migration snapshot
barrier must cover imports, financial edits, drafts and background proposal writes,
or use an equivalent immutable revision mechanism. Every transferred item has a
content digest, type, version and size in the manifest. Uploads are bounded,
resumable and idempotent. Reject path traversal, symlinks, unsupported executable
content, checksum errors and incompatible schemas.

The cloud stores uploads in tenant-contained staging. It validates the manifest,
document schemas, references and financial invariants before activating an office
revision atomically. Comparing the imported financial facts and provenance is
required; merely checking that a dashboard rendered is insufficient. Activation
preserves the imported as-of dates; hosting never makes a stale balance fresh.

The transfer key includes verified tenant, office ID and snapshot digest. An
office ID is identity, not authorization. An already hosted office must not be
overwritten by a newer upload without an explicit revision/conflict decision.
Only a committed cloud receipt with the verified digest marks the local transfer
complete. Failed transfers leave the local office usable and expose a retryable
status through the shared error banner. Partial remote uploads expire.

## Active office and connections

The initial release is a one-time handoff. After successful activation, the hosted
office is the active workspace; the local folder remains an intact snapshot and
can be opened independently. Show the handoff time and **Open hosted office** in
the local app. Local edits after that point do not silently merge into the cloud.
Bidirectional synchronization requires a later explicit conflict/revision design.

Imported account balances and history are available immediately. A connection's
status is evaluated separately:

- Cloud-capable providers require their hosted authorization flow unless an
  existing grant is explicitly portable to the hosted service.
- A desktop broker gateway remains local. Show **Local connection — reconnect
  for hosted updates**. A future local relay would be a separate, explicitly
  authorized component that only works while the user's machine is online.
- CSV and statement sources keep their last successful data and original dates;
  they remain manual refresh sources.
- Managed model access can replace local BYOM credentials according to the chosen
  plan. Unavailable models and private evidence plugins are visible dependencies,
  never silently treated as equivalent coverage.

Activation does not launch paid courts, replay in-flight external calls, place
trades, infer receipts, or enroll the household in shared learning. Interrupted
research is visible for review/resume. Scheduled hosted work follows the configured
plan and connection permissions after activation.

## Implementation and acceptance boundary

Required before a working production button: hosted origin and deployment,
managed email auth and mail delivery, tenant-authorized document/attachment store,
encryption/key management, the transfer protocol and snapshot barrier, hosted
rendering, and status/recovery UI. A button with a success animation or a local
test receiver does not meet this requirement.

Acceptance must cover verified and unverified emails; existing and new accounts;
expired/replayed links and email scanners; phone login while the desktop uploads;
cross-tenant read/write denial; repeated clicks; interrupted uploads and restarts;
concurrent local writes; digest mismatch; unsupported schema/attachments; existing
office conflicts; unchanged holdings, obligations and provenance; missing broker
connections; zero secret transfer; and no paid job replay. Use synthetic offices
until an explicit customer hosting action targets the actual deployed service.
