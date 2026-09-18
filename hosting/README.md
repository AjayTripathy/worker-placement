# Hosted Worker Placement

Live: https://worker-placement-web-653732113303.us-west1.run.app

The hosted service provides the same office workspace as the local app: Home, Capital & Commitments, Scenario Planner, Strategies, Growth, Harvest, Risk Officer, Signals and Imports. Manual planning edits save privately online. Office settings accepts office-scoped AI keys, Alpaca keys and IBKR Flex credentials. Durable background jobs run the shared research/court pipeline; Imports accepts statements. Optional local sync preserves an offline copy and stops on conflicts. See [the shared-runtime contract](../officekit/HOSTED_PARITY.md). Retained documents, full export and the shared SignalOS research library remain available.

## Use it

From a checkout, run `./start.sh` to start locally, `./wp login` to connect your terminal through Google sign-in and a matching device code, then `./wp migrate` to transfer the built `./office`. Pass `--dir` for another saved office. Migration, imports and explicitly enabled automatic sync transfer saved records; login alone does not. See [the usage guide](../officekit/README.md) for limits and replacing a snapshot.

Every signed-in account can browse `/app/research`. The immutable seed is shared, while migrated documents are private to their verified identity. Uploads never become seed research. The initial seed contains 32,412 research files; credential-shaped and administrative files were withheld.

## Boundaries and persistence

- `app/main.py`, `auth.py`: FastAPI authentication boundary with Google OAuth through Identity Platform. `workspace.py` adapts the shared `officekit.serve` renderers and request handlers in-process; it never starts or forwards to the unauthenticated local HTTP listener.
- Browser sessions: five-day Secure/HttpOnly/SameSite `__Host-` cookie; private requests check verification and revocation. Exact Origin and CSRF checks protect browser mutations. OAuth callback GETs do not exchange codes. The callback page clears its query string and completes through a CSRF-protected POST. Existing email links may still finish, but new email links are no longer sent.
- CLI device login: 15-minute intent with a high-entropy proof retained locally, explicit verified browser approval and matching device code. The proof retrieves the approved session; tokens never enter URLs. The CLI stores it with owner-only permissions outside the office.
- `offices.py`: derives an owner namespace from the verified provider UID, never an entered email or submitted tenant. CLI mutations require an explicit Bearer credential. This first release has one owner per office, not collaborative membership.
- `store.py`: durable private GCS objects, per-object random AES-GCM keys wrapped with Cloud KMS, object identity bound as authenticated data, and generation preconditions for compare-and-swap. The runtime service can decrypt authorized objects; encryption is not protection against a compromised runtime.
- Migration: manifest v1, 1 MiB digest-addressed chunks, up to 64 MiB/1,024 documents. Retries resume. Activation validates allowlisted paths, document hashes, JSON, balance schema, office IDs and dates, then atomically changes the active pointer. Replacements require the current digest. Unchanged activation is idempotent. Uploaded scripts/HTML are never executed.
- Local snapshots use a reentrant cross-process lock shared by application writers and recheck file bytes and membership. This does not coordinate an arbitrary external editor; keep outside edits idle while migrating. Original facts and dates are preserved, not refreshed or reconstructed in the cloud.
- Transfer/device staging expires logically after 24 hours/15 minutes; bucket lifecycle removes it after seven days. Immutable office revisions are retained for export/recovery. Self-service deletion and retention controls remain work to do.
- `research.py`: indexed, immutable per-area ZIPs in a separate private bucket. Authenticated users browse or download individual seed files. Text is escaped and other files forced to download. The service does not run seed code or assume old findings are current.

## Shared workspace and durable editing

`officekit.serve.render_saved_office` renders the uploaded balance sheet without
rebuilding financial facts on GET. The local builder and hosted renderer share
the same core and supplementary page functions and app shell. The adapter mounts
links, forms, fetch calls, deep links and refresh checks under the explicit office
UUID, so multiple office tabs do not share an active-office cookie.

Each authorized request materializes verified documents into a private temporary
folder that is deleted afterward. The runtime ContextVar disables machine discovery,
process-wide AI keys and local desk fallbacks. Retained relative CSV imports are
confined to the office; absolute local paths cannot be read. Shared handlers perform
manual goal, asset, commitment, receipt, allocation and strategy edits. Successful
writes validate the documents and publish an encrypted immutable revision, then
compare-and-swap its active pointer. Failures and concurrent writes leave the prior
revision active. Forms carry CSRF and office-revision fields; fetch mutations carry
the equivalent headers. Exact Origin is required. Error dismissal is event-scoped
and may use the current revision; financial edits always require the reviewed one.

Preview documents and commitment history are allowlisted in migration/export; older
hosted revisions retain them in the compatible `workspace` section. Runtime error
notices stay in that section and are not synchronized. Generated
HTML is disposable and never uploaded or executed from customer documents. GETs
never publish rebuilt balances. Hosted and local copies synchronize only after explicit opt-in in the local app.

AI proposals use office-scoped credentials and durable Cloud Tasks jobs. Keyless
briefs remain `awaiting_key` until explicitly retried. See [HOSTED_PARITY.md](../officekit/HOSTED_PARITY.md)
for credential isolation, job leases/checkpoints, supported brokers and sync conflict rules.

## HTTP controls and operations

Public/auth pages keep the strict self-only CSP and no-referrer policy. Office pages use nonce-bearing scripts, translate inline event handlers to listeners, and allow only same-origin framing for the shared workspace shell. The workspace uses same-origin referrers so native form POSTs retain their Origin; no referrer is sent to external sites. Every response is no-store. No third-party analytics. JSON limits are route-specific: 4 KiB auth, 1 MiB manifests, 1.5 MB base64 chunk requests. Auth/device request limits are process-local and can multiply across instances or reset; provider quotas also apply. This is early access, not a distributed abuse-control system.

Application access logs are disabled. The Cloud Logging exclusion `worker-placement-auth-links` drops Cloud Run `/auth/finish` and `/auth/google/finish` request URLs. Unexpected failures retain server tracebacks with generic browser messages. Never log tokens, request bodies, complete auth configuration, or provider responses. Keep the deployed host authorized in Identity Platform and register the exact `/auth/google/finish` redirect URI on the Google OAuth web client. Its secret belongs only in the managed Google provider configuration, never the browser, app environment, source tree or office export.

## Configure and deploy

See [GCP operations](gcp/README.md). Stage only the explicit `stage_web.py` allowlist; never deploy the repository root or a customer's office.

| Variable | Purpose |
| --- | --- |
| `OFFICE_TASK_QUEUE` | Full Cloud Tasks queue resource for office jobs |
| `OFFICE_TASK_ACCOUNT` | Dedicated OIDC delivery service-account email |
| `GOOGLE_CLOUD_PROJECT` | `worker-placement-508717` |
| `PUBLIC_ORIGIN` | Exact deployed HTTPS origin |
| `GOOGLE_SIGNIN_ENABLED` | `true` after the Google provider and OAuth client are configured |
| `FIREBASE_API_KEY` | Restricted Identity Toolkit/Secure Token API identifier |
| `OFFICE_BUCKET` | Private encrypted office/device/transfer objects |
| `OFFICE_KMS_KEY` | Fully qualified KMS key name |
| `RESEARCH_BUCKET` | Separate private research seed bucket |
| `RESEARCH_VERSION` | Published immutable seed prefix |

Use the attached runtime identity; do not ship service-account keys. Keep deployment config outside Git. `WORKER_PLACEMENT_HOSTED_URL` overrides the local destination, and `WORKER_PLACEMENT_CONFIG_DIR` isolates CLI login state for testing.

## Verify

```sh
python3 -m pip install -r hosting/app/requirements.txt pytest httpx
python3 -m pytest -q tests/test_hosted_web.py tests/test_hosted_migration.py tests/test_hosted_workspace.py
python3 -m uvicorn hosting.app.main:create_app --factory --host 127.0.0.1 --port 8790 --no-access-log
```

Without runtime config, public preview works and unavailable services say so. TestClient uses injected stores and identities. Live tests use a synthetic `example.invalid` identity and authenticated `returnOobLink: true`, so no email is sent. Test login, transfer, resume, export, cross-user denial and one seeded file; remove synthetic accounts and their data afterward. Google account selection and successful OAuth completion require a real Google account; an email-link smoke test does not verify Google OAuth.

## Google sign-in

The public button calls `POST /api/auth/google/start` with exact Origin and CSRF.
`accounts.createAuthUri` generates a Google authorization-code flow with only the
provider's default identity scopes and explicit account selection. A random session
proof lives in a ten-minute Secure/HttpOnly/SameSite-Lax `__Host-wp_google` cookie.
Identity Platform binds its OAuth state to that proof and checks both when exchanging
the callback through `accounts.signInWithIdp`. Google codes are single-use. No OAuth
refresh token is requested or retained. The app accepts only the fixed callback and
never trusts a submitted redirect, email, UID, or provider ID.

The resulting Firebase ID token must have a verified email, a UID, Google as the
sign-in provider, and an authentication time within five minutes. It is exchanged
for the existing five-day session cookie. Office ownership continues to use that
provider UID. Keep Identity Platform's one-account-per-email setting enabled; its
verified-provider linking rules handle existing accounts. Never implement a second
account store or remap office ownership based on a submitted email. If the provider
requires account linking or extra authentication, fail closed with a friendly error.

The device-approval cookie survives the redirect, returning a local login to `/cli`
for its explicit matching-code approval. Signup alone never uploads an office.
An embedded browser may be refused by Google; use the normal browser and reopen
the device connection URL there. This is not a reason to bypass browser warnings.
