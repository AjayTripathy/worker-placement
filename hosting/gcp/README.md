# Google Cloud deployment

Project: `worker-placement-508717` · region: `us-west1` · public service: `worker-placement-web`.

Live origin: https://worker-placement-web-653732113303.us-west1.run.app

Read [the hosted service guide](../README.md) first. The deployed scope includes Google accounts, CLI migration to private office snapshots, and shared seeded research. `project.json` describes the larger planned tier; Cloud SQL and hosted AI execution are not deployed. Manual editing uses the shared office workspace and encrypted object revisions.

## Current resources

- Cloud Run public service, 1 vCPU / 2 GiB, 0 minimum / 2 maximum instances, concurrency 1, request timeout 300 seconds.
- Identity Platform with the Google provider enabled; one account per email, the Cloud Run host authorized, and a Google OAuth web client with the exact `PUBLIC_ORIGIN/auth/google/finish` redirect. Set `GOOGLE_SIGNIN_ENABLED=true` after configuring the provider.
- API key `worker-placement-web`, restricted to Identity Toolkit and Secure Token. This is an API identifier, not a service account credential.
- Runtime identity `wp-web-runtime@worker-placement-508717.iam.gserviceaccount.com`, custom role `workerPlacementWebSessions`: `firebaseauth.users.createSession` and `firebaseauth.users.get`, plus bucket-scoped objectUser for office storage, objectViewer for research, and encrypter/decrypter on the specific office KMS key.
- Build identity `wp-web-build@worker-placement-508717.iam.gserviceaccount.com`, `roles/run.builder`.
- Cloud Build source bucket and Artifact Registry repository managed by the source deployment. They contain the staged public/auth application, never a household office.
- Logging exclusion `worker-placement-auth-links` excludes Cloud Run request URLs containing `/auth/finish` for this service. Application access logging is disabled.

The administrator uses their existing Google Cloud login; the runtime has no service-account JSON key. Private buckets `worker-placement-508717-offices` and `worker-placement-508717-research` use uniform access and public-access prevention. KMS key `projects/worker-placement-508717/locations/us-west1/keyRings/worker-placement/cryptoKeys/office-documents` wraps random document keys. Office bucket lifecycle deletes `devices/` and `transfers/` after seven days. Active office revisions are retained. No Cloud SQL instance is provisioned.

## Redeploy

Authenticate the Google Cloud CLI and verify the intended project. Stage into a **new** directory outside the repository; the script refuses to overwrite one.

```sh
python3 hosting/gcp/preflight.py
python3 hosting/gcp/stage_web.py /tmp/wp-web-release
```

Prepare an environment JSON file outside Git, readable only by you (`chmod 600`). It must contain `GOOGLE_CLOUD_PROJECT`, `PUBLIC_ORIGIN` the configured `FIREBASE_API_KEY`, `OFFICE_BUCKET`, `OFFICE_KMS_KEY`, `RESEARCH_BUCKET` and `RESEARCH_VERSION`. Retrieve the identifier through Google Cloud's API Keys service; never print full authentication config objects, which contain sensitive signing material.

```sh
gcloud run deploy worker-placement-web \
  --project=worker-placement-508717 --region=us-west1 \
  --source=/tmp/wp-web-release \
  --service-account=wp-web-runtime@worker-placement-508717.iam.gserviceaccount.com \
  --build-service-account=projects/worker-placement-508717/serviceAccounts/wp-web-build@worker-placement-508717.iam.gserviceaccount.com \
  --env-vars-file=/path/outside/git/wp-web-env.json \
  --min=0 --max=2 --memory=2Gi --cpu=1 --concurrency=1 --timeout=300
```

The service is public because its landing and signup endpoints must be reachable; `/app` and `/api/me` enforce verified sessions in application code. **Never start the `officekit.serve` HTTP listener in this service or use `--source .` at the monorepo root.**

Check `/api/health`, public pages, anonymous `/api/me` (401), and private office access, CLI migration, and a seeded research document. `/healthz` is intercepted by Google's frontend, so use `/api/health` for external checks. Run the synthetic authentication workflow in the parent README after auth changes.

For rollback, list revisions with `gcloud run revisions list --service=worker-placement-web --region=us-west1 --project=worker-placement-508717`, then use `gcloud run services update-traffic` with the selected known-good revision. A code rollback does not reverse Identity Platform, IAM or logging settings.

## Identity provisioning notes

The project was initialized through the public Identity Platform `initializeAuth` API after Firebase Management's `addFirebase` returned a permission error. Email sign-in uses the managed default action handler, which redirects to the exact approved continuation. Do not override `notification.sendEmail.callbackUri`: this project rejects that operation with `EMAIL_TEMPLATE_UPDATE_NOT_ALLOWED`.

Current migration implements UID ownership, encrypted documents, resumable chunks and atomic activation. The first release uses a verified session as the CLI credential; narrower upload grants, team membership, hosted AI jobs and reconnects remain planned in `officekit/HOSTED_ONBOARDING.md`. Cloud Run temporary storage is not a durable office. Do not infer tenant authorization from an entered email address.

## References

- [Cloud Run source deployment](https://docs.cloud.google.com/run/docs/deploying-source-code)
- [Identity Platform initialization](https://docs.cloud.google.com/identity-platform/docs/reference/rest/v2/projects.identityPlatform/initializeAuth)
- [Email-link authentication](https://firebase.google.com/docs/auth/web/email-link-auth)
- [Verified session cookies](https://firebase.google.com/docs/auth/admin/manage-cookies)

## Publishing a research seed

Run `python3 hosting/gcp/seed_research.py --help`. Build from a pinned Git revision into a new directory outside Git, review the exclusion report, upload the complete catalog/index/ZIP set under a new version prefix in the private research bucket, then update `RESEARCH_VERSION`. Never replace an already published version. Runtime access is read-only. Initial seed `seed-20260915` came from `6207310c8`, with 32,412 files (about 9.3 GiB uncompressed, 3.0 GiB compressed); 64 files were withheld by the administrative/credential filters. Customer office data is never a seed source.

### Account identifiers in shared research

The seed builder loads confirmed account IDs from `desk/data/accounts.json` at
its pinned Git revision. It replaces them with consistent anonymous labels in
text and filenames; the private mapping is never written into published output.
This preserves position and research data, including unrelated public property
identifiers. Files with a confirmed ID in binary content require separate review.
This targeted correction is not a substitute for a full publication audit of
unknown identifiers, secrets, images or Git history. The original seed contained
three text files with brokerage IDs and has been superseded by
`seed-20260916-accounts`; do not reactivate `seed-20260915`.

### Google OAuth setup

Use Google Auth Platform in this project to configure the Worker Placement app for
external Google accounts and create a Web application OAuth client. Register only
`https://worker-placement-web-653732113303.us-west1.run.app/auth/google/finish` as the
hosted redirect. Configure its client ID/secret in Identity Platform's `google.com`
provider, then enable `GOOGLE_SIGNIN_ENABLED=true` in the Cloud Run revision.
The server-side authorization flow does not need JavaScript origins or a browser SDK.
Request only the standard identity scopes; no Gmail, Drive or financial scopes.

Before traffic promotion, extend `worker-placement-auth-links` to exclude both the
legacy and Google callback request URLs. Preserve no-access-log in uvicorn. Check
that `/api/auth/google/start` returns an `accounts.google.com` URL with the exact
redirect and that the Google account chooser opens without a configuration error.
A successful real account sign-in must still be checked separately; synthetic
Firebase/email-link identities cannot demonstrate that OAuth works end to end.


Google sign-in is live on revision `worker-placement-web-00013-m4t` (2026-09-17).
The OAuth app is External / In production, with the hosted homepage and privacy
policy configured. The active web client is named **Worker Placement hosted
sign-in**. Its secret is stored only in Identity Platform. A real login preserved
the existing Firebase UID and returned the previously migrated office.

Setup also produced an unused duplicate client. It is named **Unused setup
duplicate - no authorized redirects**, has no authorized origins or redirect URIs,
and is not referenced by Identity Platform. Do not select it when configuring the
provider. Only the named active client should be used.

## Shared AI/import workers and sync

See [HOSTED_PARITY.md](../../officekit/HOSTED_PARITY.md). Cloud Tasks queue
`projects/worker-placement-508717/locations/us-west1/queues/office-jobs` dispatches
at most two jobs concurrently and one per second. Delivery uses
`wp-office-jobs@worker-placement-508717.iam.gserviceaccount.com`, with Cloud Run
Invoker on this service. The web runtime has queue-scoped Cloud Tasks Enqueuer and
Service Account User on that delivery identity. Preserve the managed Cloud Tasks
service agent's token-minting role; never create a service-account key.

Set `OFFICE_TASK_QUEUE` and `OFFICE_TASK_ACCOUNT` to those resources alongside the
existing environment. Cloud Run request timeout is 1,800 seconds, concurrency 4,
max instances 3. This keeps browser reads available during jobs. A duplicate task
delivery never replays a claimed provider call. Expired attempts require explicit
resubmission. The service itself checks OIDC issuer/audience/verified identity;
public ingress for the landing page does not make the worker endpoint public.

Keep a bucket lifecycle Delete rule for `office-jobs/` after 30 days, preserving
existing transfer/device rules. This does not delete office revisions. Agent
packages/directives/templates and supported broker code are in the explicit
source stage; research seed files are never executable deployment code.

Parity rollout: `worker-placement-web-00015-b52` (2026-09-17 local date).
Synthetic live acceptance verified authenticated Cloud Tasks delivery, retained
CSV/staging, credential exclusion from exports, bidirectional sync and wrong-owner
denial. Test users and their exact storage namespaces were removed afterward.
Real provider credentials and paid model/broker calls were not used for acceptance.
The prior `worker-placement-web-00013-m4t` is the pre-parity rollback revision;
leave the new queue/IAM in place when rolling back unless intentionally retiring it.
