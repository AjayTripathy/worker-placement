# Google Cloud deployment

Project: `worker-placement-508717` · region: `us-west1` · public service: `worker-placement-web`.

Live origin: https://worker-placement-web-653732113303.us-west1.run.app

Read [the hosted service guide](../README.md) first. The deployed scope includes email accounts, CLI migration to private office snapshots, and shared seeded research. `project.json` describes the larger planned tier; Cloud SQL and hosted editing are not deployed.

## Current resources

- Cloud Run public service, 1 vCPU / 2 GiB, 0 minimum / 2 maximum instances, concurrency 1, request timeout 300 seconds.
- Identity Platform, email-link sign-in enabled; the Cloud Run host is an authorized domain. Google sends the authentication emails.
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

The service is public because its landing and signup endpoints must be reachable; `/app` and `/api/me` enforce verified sessions in application code. **Never deploy `officekit.serve` to this service or use `--source .` at the monorepo root.**

Check `/api/health`, public pages, anonymous `/api/me` (401), and private office access, CLI migration, and a seeded research document. `/healthz` is intercepted by Google's frontend, so use `/api/health` for external checks. Run the synthetic authentication workflow in the parent README after auth changes.

For rollback, list revisions with `gcloud run revisions list --service=worker-placement-web --region=us-west1 --project=worker-placement-508717`, then use `gcloud run services update-traffic` with the selected known-good revision. A code rollback does not reverse Identity Platform, IAM or logging settings.

## Identity provisioning notes

The project was initialized through the public Identity Platform `initializeAuth` API after Firebase Management's `addFirebase` returned a permission error. Email sign-in uses the managed default action handler, which redirects to the exact approved continuation. Do not override `notification.sendEmail.callbackUri`: this project rejects that operation with `EMAIL_TEMPLATE_UPDATE_NOT_ALLOWED`.

Current migration implements UID ownership, encrypted documents, resumable chunks and atomic activation. The first release uses a verified session as the CLI credential; narrower upload grants, team membership, hosted editing and reconnects remain planned in `officekit/HOSTED_ONBOARDING.md`. Cloud Run temporary storage is not a durable office. Do not infer tenant authorization from an entered email address.

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
