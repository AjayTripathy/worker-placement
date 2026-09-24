# September 2026 engineering review repairs

The nine concrete findings are covered by changes to the local request boundary,
score identity binding, packaged intake prompt, harvest HTTP handler, UTF-8 file
I/O, staging concurrency, root CLI entry point, legacy option-order warning and
versioned research validation. These are engineering corrections, not evidence
of investment performance or model independence.

Local clients first GET `/local-session`, retain the `X-Office-Local-CSRF`
response header, and send it with mutations. Browser forms/fetches receive the
session token automatically. Every local request requires an exact loopback Host;
supplied Origin must match the app. Hosted requests retain their authenticated
tenant/Origin/CSRF boundary.

New local public-company scores require the exact `score_binding` emitted in the
extraction evidence: ticker, cutoff, input digest and source digest. Historical
unbound scores are not silently upgraded. `python -m
verticals.public_co.score_audit ROOT --out REPORT.json` inventories them for
review. Historic golden outputs remain characterization, not correctness proof.

`desk.research_contracts` version 1 projects ambiguous historical calibration
records into `EXCLUDED_REVIEW` with content digests and reasons, without rewriting
the original ledger. Unknown taxonomies, unsupported statuses/outcomes, invalid
dates and duplicate OPEN identities need explicit adjudication. New freeze and
ingestion paths validate before writing. Performance reports expose exclusion
counts. Ready deployment requires consistent structured verdicts and numeric
`sizing.pct_lo`/`pct_hi`; prose percentages cannot authorize sizing. Incomplete
entries remain in the review list and drift report.

Raw historical corpus tests intentionally remain separate from implementation
tests: quarantining an ambiguity does not reconcile it. The dated private audit
report records the backlog. Do not delete duplicates, invent authors or infer
outcomes merely to make an old fixture pass.

Apache-2.0 applies to project code. `DATA_LICENSE.md` keeps third-party research,
market data and private office material outside that grant. The installer uses a
shallow sparse product checkout. Hash-pinned dependency locks cover portable,
hosted and root framework environments. Hosted staging emits a content-addressed
source manifest, base commit and an honest clean/dirty flag. Do not label a dirty
snapshot as an immutable source commit.

CI runs an installed-wheel prompt/office smoke test, real HTTP forms, security,
concurrency and scoring tests on Linux and Windows. `--offline` blocks external
sockets before fixtures while allowing loopback tests. Live integration tests are
separate. Windows CI must actually run before claiming Windows verification.

Remaining broader recommendations: independently reviewed frozen model efficacy
evaluation; near-limit hosted capacity/recovery benchmarks; attachment storage
separation; retention and self-service deletion. These are not established by
the regression tests in this repair.
