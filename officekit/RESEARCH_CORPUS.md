# Contextual research corpus

Status (2026-09-18): pilot implemented; contract and transport evaluation passing.
Live-model comparison pending: the first Anthropic request was rejected for
insufficient API credit before any research was generated. The milestone remains
open. This document distinguishes implementation from demonstrated effectiveness.

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

First-milestone exchange is an explicit reviewed JSON bundle, retained and consumed
by the same Python modules locally and hosted. The shared library can be rebuilt
from those artifacts. Central contribution admission, independent publisher
signatures, multi-contributor disclosure analysis, automated Git releases,
research task allocation and long-horizon outcome grading are subsequent phases.
Do not silently turn on those features or publish household-derived material.

The eventual central index is a query projection of admitted versioned artifacts;
private contributor mappings remain separate. A dedicated public research
repository records accepted releases, corrections and retractions. Published
copies cannot be recalled from other people's clones. Source-specific reuse
permission must accompany evidence; a repository's code license is insufficient
metadata for deciding what source material to republish.

## Implementation and evaluation notes

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
python -m pytest -q tests/test_hosted_research.py tests/test_hosted_workspace.py
```

The paired fixture keeps recipient context equal across arms. It records three
source acquisition attempts without reuse versus two with reuse; both still run
all six model stages. A controlled issuer outage leaves the baseline source gap
visible while a fresh, permitted shared snapshot remains available to the reuse
arm. These are mechanism results, not evidence of better model judgment, lower
model cost or investment performance. The test provider has no measured token
usage, so usage/cost are unknown.

The live harness uses fictional accumulation/decumulation households, a frozen
manually checked SGOV issuer summary, actual configured model calls, and a paired
issuer-outage condition. It does not read household data. First create the donor:

```sh
python -m officekit_research.evaluate donor --out ./pilot --evidence ./sgov-evidence.json
```

Review its case using the CLI above; label `provenance.kind` as
`evaluation_scenario`, review the anonymized narrative, and explicitly grant reuse
of the frozen original source summary. Evaluation cases are excluded from normal
proposals. Then:

```sh
python -m officekit_research.evaluate pair --out ./pilot --evidence ./sgov-evidence.json --bundle ./reviewed-pilot-case.json
```

The harness records each call before dispatch, enforces call/output-token budgets,
preserves checkpoints, and stops after an error. `--resume` is an explicit retry
after resolving a definite rejection; uncertain completions require inspection.
Inspect original model outputs and independently audit source support, recipient
constraints, recognition of context differences, and unsupported claims. A model
does not grade its own response. A small paired pilot cannot establish statistical
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
