# Hosted Worker Placement

Live: https://worker-placement-web-653732113303.us-west1.run.app

The hosted service provides the same office workspace as the local app: Home, Capital & Commitments, Scenario Planner, Strategies, Growth, Harvest, Risk Officer, Signals and Imports. Manual planning edits save privately online. Strategy briefs wait for an AI agent key; hosted AI keys/jobs, statement uploads and live broker reconnects are not enabled yet. Retained documents, full export and the shared SignalOS research library remain available.

## Use it

From a checkout, run `./start.sh` to start locally, `./wp login` to connect your terminal through verified email and a matching device code, then `./wp migrate` to transfer the built `./office`. Pass `--dir` for another saved office. Only the migration command uploads financial records; login does not. See [the usage guide](../officekit/README.md) for limits and replacing a snapshot.

Every signed-in account can browse `/app/research`. The immutable seed is shared, while migrated documents are private to their verified identity. Uploads never become seed research. The initial seed contains 32,412 research files; credential-shaped and administrative files were withheld.

## Boundaries and persistence

- `app/main.py`, `auth.py`: FastAPI authentication boundary with Google Identity Platform email verification. `workspace.py` adapts the shared `officekit.serve` renderers and request handlers in-process; it never starts or forwards to the unauthenticated local HTTP listener.
- Browser sessions: five-day Secure/HttpOnly/SameSite `__Host-` cookie; private requests check verification and revocation. Exact Origin and CSRF checks protect browser mutations. Email-link GETs do not exchange codes.
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

Preview documents and commitment history are retained in a separately allowlisted
`workspace` portion of the same encrypted revision and included in export. Generated
HTML is disposable and never uploaded or executed from customer documents. GETs
never publish rebuilt balances. Hosted and local copies do not automatically sync.

AI proposal creation saves the shared brief and snapshot with `awaiting_key` status.
No provider call, environment-key fallback or background job runs. Future agent keys
must be owner-scoped secrets resolved through the runtime capability boundary; do
not wire the local `/key` route or global environment into the hosted process.

## HTTP controls and operations

Public/auth pages keep the strict self-only CSP and no-referrer policy. Office pages use nonce-bearing scripts, translate inline event handlers to listeners, and allow only same-origin framing for the shared workspace shell. The workspace uses same-origin referrers so native form POSTs retain their Origin; no referrer is sent to external sites. Every response is no-store. No third-party analytics. JSON limits are route-specific: 4 KiB auth, 1 MiB manifests, 1.5 MB base64 chunk requests. Auth/device request limits are process-local and can multiply across instances or reset; provider quotas also apply. This is early access, not a distributed abuse-control system.

Application access logs are disabled. The Cloud Logging exclusion `worker-placement-auth-links` drops Cloud Run `/auth/finish` request URLs. Unexpected failures retain server tracebacks with generic browser messages. Never log tokens, request bodies, complete auth configuration, or provider responses. Google sends email through its default action handler; keep the deployed host authorized. The project rejects a custom `notification.sendEmail.callbackUri`.

## Configure and deploy

See [GCP operations](gcp/README.md). Stage only the explicit `stage_web.py` allowlist; never deploy the repository root or a customer's office.

| Variable | Purpose |
| --- | --- |
| `GOOGLE_CLOUD_PROJECT` | `worker-placement-508717` |
| `PUBLIC_ORIGIN` | Exact deployed HTTPS origin |
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

Without runtime config, public preview works and unavailable services say so. TestClient uses injected stores and identities. Live tests use a synthetic `example.invalid` identity and authenticated `returnOobLink: true`, so no email is sent. Test login, transfer, resume, export, cross-user denial and one seeded file; remove synthetic accounts and their data afterward. Inbox delivery remains a separate test.
