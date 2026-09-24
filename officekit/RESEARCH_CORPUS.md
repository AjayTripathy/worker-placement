# Contextual research corpus

Status (2026-09-20): attribution and admission hardening implemented locally;
two-office hosted contract passes with synthetic providers. The live donor's
first Anthropic request was rejected for insufficient credit before any research
was generated. No live contribution or public release occurred. The milestone
remains open; deployment and independent output audit are still required.

The principal selected `AjayTripathy/worker-placement`, under `research_exchange/`,
as the public release destination. Do not make the private SignalOS repository
public. Retained evidence and results are in
[the evaluation folder](evals/research_exchange_20260920/README.md).

## Milestone and acceptance

An office contributes an anonymized case preserving the purpose, investor
context, alternatives and court arguments of its investigation. A second office
retrieves it, identifies differences in its own circumstances, reuses eligible
public evidence, and produces a separately adjudicated proposal. Evaluation must
show useful reuse, fewer duplicate source acquisitions, and preservation of the
second office's constraints. An unsuitable or stale case must not silently become
a recommendation. Original recommendations, human decisions and execution are
different observations.

Required evidence before calling this milestone complete:

1. Shared local/hosted proposal capture and retrieval, with inspectable lineage
   in the pitch and retained office records.
2. A reviewed public projection that retains contextual reasoning while excluding
   office identity, account identifiers, exact household amounts and raw private
   context. No automatic publication of legacy court exports.
3. A portable corpus artifact, validated import and deterministic contextual
   retrieval. Import does not certify the truth of a contribution.
4. Fresh, explicitly reusable public evidence can avoid duplicate source work;
   local holdings and current market data are always acquired for the recipient.
   Each recipient runs its own courts and Risk Officer.
5. Rejected, stale, contradictory, unknown-context and tampered cases are covered
   in tests. Cross-office isolation and proposal recovery remain intact.
6. A reproducible paired evaluation, including actual model runs when available,
   with source-acquisition counts, usage/latency, supported-claim checks and
   constraint checks. Synthetic fixtures prove mechanics only. No investment
   performance or court-superiority claim follows from this milestone.

## Boundaries

Private investigation records live in the office's retained `research/` directory.
An immutable public case has a content identity independent of user identity.
Structured context includes the relevant strategy, goal kind and horizon,
accumulation/decumulation, jurisdiction and declared constraints. Unknown values
remain unknown. Free-text arguments are preserved in a proposed projection;
anonymization transformations are recorded and the projection requires review.
One projection cannot prove the anonymity of a contributor's entire history.

Evidence dates and source lineage survive reuse. A prior verdict is historical
context, never an eligibility gate for the recipient. Model configuration is
provenance, not a measured intelligence score. Source overlap is not independent
corroboration. Adoption records intent; execution stays unknown without custody
evidence.

Contextual exchange remains an explicit reviewed JSON bundle, consumed by the
same modules locally and hosted. General court records can separately pass through
the authenticated hosted exchange and an operator Git export. Sharing starts off;
when enabled it defaults to anonymous. Household suitability stays private.
Independent publisher signatures, population-wide disclosure analysis, task
allocation and long-horizon effectiveness evidence remain future work.

The eventual central index is a query projection of admitted versioned artifacts;
private contributor mappings remain separate. The worker-placement public library
will record accepted releases, corrections and retractions. Published
copies cannot be recalled from other people's clones. Source-specific reuse
permission must accompany evidence; a repository's code license is insufficient
metadata for deciding what source material to republish.

## Implementation and evaluation notes

### Order and admission contract

1. Imported general research retains its original ID and contributor envelopes
   in a private custody sidecar. Index rebuilds distinguish own, imported and
   unknown records. Reusing a record never makes the recipient its author.
2. Connectors default to private. A public declaration and an exact supported
   field schema are both required. Unknown sections and extra fields are withheld;
   raw connector exceptions cannot enter public evidence. Private instruments
   require an explicit release regardless of evidence eligibility.
3. Each narrative field, including bench briefs and unverified queues, requires
   independent claim review against publisher-controlled evidence. Every claim
   names its source digest, exact quote, kind and support reasoning. Missing
   coverage, changed digests, absent quotes, unsupported findings, self-review and
   reviewer failure withhold publication. The model checks semantic support and
   calculations; deterministic checks verify coverage, hashes and quote presence.
   This is not a proof of entailment or truth. Synthetic reviewer fixtures test
   enforcement mechanics, not reviewer accuracy.
4. Hosted admission accepts no caller-supplied approval. Retained review reports
   are private; record-bound public receipts are publisher assertions, not signed
   attestations. Identical retries reuse an intact current-policy review. Old
   unreviewed records stay on disk but disappear from admission-required listings
   and exports. Publication failure is visible in the proposal.
5. Prove the existing two-office milestone before decomposing research. General
   research uses today's immutable court record. The factor/mechanism layer is
   the existing knowledge graph and promotion pipeline: detector, `APPLIES_TO`
   contract, dispatch and lineage. Candidate acceptance alone does not demonstrate
   executable dispatch on another issuer. Do not introduce parallel prose mechanisms.
6. Schema decomposition, central analytical tables and task allocation follow
   empirical reuse evidence. Preserve existing `as_of`, `fetched_at`, `resolved_at`,
   lookahead exclusion and CIK lineage. Reliability estimates should pool sparse
   groups and stay advisory; do not add early task/domain/horizon gates. The
   existing 20-resolution reporting threshold is not evidence of skill.

Public source times are coarsened to dates; anonymity is the default for all
names, including thinly covered ones. Pseudonyms require explicit opt-in. Rotation
changes an identifier but cannot remove content/timing fingerprints. Full batching
and disclosure analysis are deferred with decomposition, not claimed as solved.
Account-bound attribution establishes who submitted under a key, not true
authorship. `acq_coherence` now returns a nonzero CLI status for total or partial
model failure, while a genuinely empty acquisition set remains a successful result.

### Existing contextual artifacts

`officekit_research/cases.py` owns versioned cases, private capture, projection,
validation, content identities, import and retrieval. `corpus.py` is the explicit
file-exchange CLI. `officekit_ai/strategy_proposal.py` retrieves before candidate
selection and again for newly discovered candidates, freezes those retrievals,
and passes context differences to fresh courts. `render_research.py` and
`research_routes.py` are used by both transports. Strategies links to `/research`;
pitch decks disclose source reuse, original source dates and contextual differences.

`strategy_proposals.save()` captures private investigation state under
`research/private_cases/<proposal UUID>.json`. The saved proposal remains the
exact original source, referenced by its content digest. User decision reasons
are `not_recorded` and execution is `unconfirmed`; no narrative reconstruction
turns an agent's reasoning into a user's stated motive.

The first public schema supports security and option cases. Factor tags describe
topics investigated under a known strategy template, not measured factor betas.
Known household facts cannot be relabeled through declared context overrides.
Unknown horizon, goals or jurisdiction are visible in comparisons. An explicit
review binds the exact projection; source reuse grants separately name their
permission basis and expiry. This is a contributor assertion, not a signature or
independent source audit. Public source snapshots currently support fund profiles
and filing text. Legacy filings/XBRL data lacking a source locator remain private.

The old `export_shareable_adjudications()` no longer returns raw native court
records. It returns validated reviewed security bundles from the office's shared
library. Consumers must inspect the versioned bundle schema. Office identifiers
and free-text rationale are not safe merely because their field names were
allowlisted.

Library limits are 1,000 cases, 32 MiB total, and 512 KiB per bundle. Case context
has a 90-day pilot window; reusable evidence requires an explicit expiry within
30 days of its original collection. The current window uses UTC dates. Original
collection dates survive another office's re-export. Conflicting source snapshots
force reacquisition rather than majority voting. Unknown or mismatched context is
disclosed; excluded instruments, incompatible near-term horizons and known
jurisdiction conflicts are rejected. The local book and tape always refresh.
Ticker-plus-source-date is a pilot identity: issuer/listing identifiers and
corporate-action-aware joins remain future work.

Agent provenance freezes requested/resolved model, client/provider, reasoning
configuration, protocol hash, measured usage and latency. Missing usage stays
unknown. Costs are not inferred without a versioned price schedule. Agent roles
and shared parent case IDs preserve dependencies; they do not prove independent
corroboration. Prompt input is bounded and excerpts are labeled.

### Use the pilot

In either office UI: **Strategies → Shared research**. Prepare a completed
investigation, review the projected context, original arguments and source
material, then download the reviewed case. Another office can import that file.
The next proposal automatically considers compatible cases and displays lineage.
No UI action publishes to GitHub or sends data to a central contribution service.

Equivalent CLI, with explicit output paths:

```sh
python -m officekit_research.corpus prepare --office ./office --proposal PROPOSAL_UUID --symbol SGOV --out case-draft.json
# Inspect/edit all draft content. The command prints the current projection hash.
python -m officekit_research.corpus approve case-draft.json --reviewed-sha256 REVIEWED_HASH --out research-case.json
python -m officekit_research.corpus import research-case.json --office ./second-office
python -m officekit_research.corpus list --office ./second-office
```

Context-only exchange needs no reuse grant. To avoid refetching a source, supply
`--reuse-grants grants.json` while approving, for example a list with `section`,
`basis` (`original_summary`, `public_domain`, or `licensed`), and `valid_until`.
An original summary must actually replace the source text and preserve the
source URL and collection date. Review all retained source material for permission
to redistribute, even when it has no reuse grant.

### Reproduce evaluation

Contract tests exercise actual orchestration with deterministic provider fixtures:

```sh
python -m pytest -q tests/test_contextual_research.py tests/test_officekit_strategy_proposals.py tests/test_officekit_ai.py
python -m pytest -q tests/test_research_evaluation.py
python -m pytest -q tests/test_hosted_research.py tests/test_hosted_workspace.py
```

The original file-exchange fixture keeps recipient facts and instructions equal across arms:
no reuse, evidence-only reuse, and evidence plus contextual reasoning. It records
three source acquisition attempts without reuse versus two in each reuse arm;
all arms still run six model stages. Tests inspect every model request to verify
that evidence-only reuse withholds historical arguments while preserving the
same source. A controlled issuer outage leaves the baseline source gap visible.
This isolates source availability from the incremental contribution of context.
These are mechanism results, not evidence of better model judgment, lower model
cost or investment performance. Fixture usage is absent or explicitly synthetic;
neither can establish real cost savings.

The hosted fixture additionally reuses the general court: recipient model-call
counts are seven/seven/four for baseline/evidence-only/contextual, with source
acquisition counts three/two/two. It verifies preserved attribution, a distinct
recipient suitability ruling and one idempotent Git commit in an isolated test
repository. These counts exclude publisher review; no synthetic output is pushed.

The live harness uses fictional accumulation/decumulation households, a frozen
manually checked SGOV issuer summary, actual configured model calls, and a paired
issuer-outage condition. The recipient has 150,000 cash with an explicit 90,000
reservation due in ten days; the donor reserves a 10,000 cash floor. The controlled
scenario excludes unspecified lifestyle spending instead of mixing an inferred
estimate into the comparison. The obligation is a cash reservation as well as a
goal: describing a goal alone would not constrain the funding calculation.
The harness does not read household data. Create the donor in a fresh v4 directory:

```sh
python -m officekit_research.evaluate donor --out ./pilot-v4 --evidence ./sgov-evidence.json
```

Review its case using the CLI above; label `provenance.kind` as
`evaluation_scenario`, review the anonymized narrative, and explicitly grant reuse
of the frozen original source summary. Evaluation cases are excluded from normal
proposals. Then:

```sh
python -m officekit_research.evaluate pair --out ./pilot-v4 --evidence ./sgov-evidence.json --bundle ./reviewed-pilot-case.json
```

The v4 plan freezes the model, code protocol, source, contribution, scenario date,
recipient facts and a randomized arm order before dispatch. Missing, expired or
mismatched contributions fail before model construction. Changed inputs require
a new output directory; earlier checkpoints remain intact and cannot be relabeled
as v4 results. Reuse mode cannot change during proposal recovery.

For hosted contribution/retrieval, add `--hosted-origin https://EXCHANGE_HOST`
and `--bearer-env DONOR_EXCHANGE_BEARER` for the donor, then the same origin with
`--bearer-env RECIPIENT_EXCHANGE_BEARER` for the pair. Use distinct verified test
accounts. Tokens stay in the named environment variables, never in artifacts.
Hosted admission needs an operator-controlled resolver for the identical frozen
source summary and a funded reviewer distinct from the producing models. The
normal live issuer-page loader will correctly reject a different summary digest;
do not bypass that check or trust a client-supplied snapshot to make the pilot pass.
The donor phase fails if hosted admission fails; the contextual arm fails unless
it actually reuses the frozen donor general record from the hosted exchange.

The harness serializes runs on its output directory, records each call before
dispatch, preserves checkpoints and stops after an error. The default ceiling is
30 calls / 80,000 output tokens across donor and recipient runs; the hosted fixture
uses seven donor calls and recipient counts of seven/seven/four. Publisher review
is a separate service call and is outside this caller budget and these counts;
retain its usage separately for a live cost comparison. Missing measured usage
reserves that call's requested output ceiling rather than counting it as free.
`--resume` explicitly retries a saved failure; uncertain completions require
inspection and are never automatically replayed.

After the comparison, `review-packet.json` contains the original outputs, supplied
evidence, exact fictional recipient inputs and an ungraded rubric. It masks arm
labels; narrative and source gaps can still reveal treatment. Review it before
opening `review-key.json` or the arm metrics. Record quoted output and evidence
locators for constraint preservation, source support, alternatives, uncertainty
and independent judgment. Existing human notes survive idempotent reruns. A model
does not grade its own response. A small pilot cannot establish statistical
superiority. Market-direction grading is not goal-success grading.

### Remaining acceptance evidence

- The browser review and local/hosted route tests exercise preparation, revision
  gates, file import/download, retained storage and cross-tenant denial.
- Contract tests cover changed investor type, horizon/jurisdiction mismatch,
  exclusions, stale/future/contradictory evidence, tampering, explicit source
  permissions, private-field removal, symlinks, prompt budgets and restart reuse.
- Actual model generation and independent output audit remain outstanding due to
  the API credit rejection. Do not mark the milestone complete or claim that
  contextual reuse improves recommendation quality until those results exist.
