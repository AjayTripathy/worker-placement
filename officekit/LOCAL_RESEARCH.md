# Build research locally and bring it into your office

Local agents can author the existing strategy-pack format: `pack.json` plus
`DECK.md`. The hosted app imports it into the same saved research catalog used
by new strategies, cash deployment and proposal candidate discovery. A pack is
an attributed strategy idea. It does not become a general court, verified claim,
forecast or approved allocation merely because it was imported.

## Author and export

Put original analysis, claim-level source links, assumptions, alternatives and
unresolved questions in `DECK.md`. Do not include API keys. Uploaded packs stay
private to the destination office; this workflow does not publish to the shared
exchange or open-source repository.

Example `pack.json` (replace the example date and source with actual research):

```json
{
  "id": "index_protection",
  "name": "Index downside protection",
  "bucket": "defensive",
  "thesis": "Compare outright puts with put spreads; verify current quotes and household fit.",
  "author": "your-submitter-handle",
  "agent": "your-research-agent",
  "model": "unknown",
  "intelligence_level": "unrated",
  "as_of": "2026-09-28",
  "positions": ["SPY", "SPX", "XSP"],
  "deck": "DECK.md",
  "gaps": ["Live quotes and suitability review"],
  "sources": [{
    "title": "Cboe XSP specifications",
    "url": "https://www.cboe.com/tradable-products/sp-500/xsp-options/specifications",
    "retrieved_at": "2026-09-28"
  }]
}
```

Author/model attribution is supplied by the contributor, not a verified identity
or model-quality rating. Use `unknown`/`unrated` when appropriate. A pack has no
Brier score unless a separate immutable prediction with a resolution contract
is recorded through the existing prediction ledger.

```sh
./wp research-export --pack ./index_protection --output ./research.json
```

In the office's Research library, choose **Local research pack**, optionally
select an unfinished proposal, and click **Import local research**. The same
control is available locally and in the web app. The proposal's **Refresh saved
research** button discovers later uploads without starting AI calls.

## Upload directly from a local agent

Use the normal `./wp login` device sign-in, then:

```sh
./wp research-upload --pack ./index_protection --office OFFICE_UUID --proposal PROPOSAL_UUID
```

Omit `--proposal` to import into the catalog only. The authenticated API is
`POST /api/offices/{office_id}/research/packs` with `bundle`, current office
`revision`, and optional `proposal_id`. It checks office ownership, the active
job lease and a compare-and-swap revision. No whole-office replacement is needed.
A conflict requires fetching the current revision and retrying deliberately.

Uploads validate the bounded manifest, sources and deck digest before writing.
The transport envelope is content-addressed; repeating identical bytes is
idempotent. Editing a deck creates a new immutable version, so old references
still open the original. Packs are saved under `research/strategy_packs/` and
travel with existing encrypted snapshots, downloads and office sync.

An unfinished proposal refreshes its discovery inventory before its first
successful synthesis, including bounded deck text, dates, sources and contributor
metadata. Completed synthesis, courts and decisions retain the original inventory;
create a new proposal revision to reconsider them. Discovery stays bounded to
32 entries/30,000 characters and each deck excerpt to 6,000 characters, with
truncation and omission recorded. An import is not guaranteed a place if more
relevant research fills that limit. Full decks remain available through catalog
links. No research-import action makes model calls, adopts a strategy or places
an order.

## Private research directories and lazy content

Large private libraries use `research/pack_directory.json`. Each entry retains the
manifest, symbols, summary, as-of date, attribution, historical ruling, reopen gates,
content hashes and court revision. Hosted office reads and catalog browsing load
this directory, not the decks. Opening a research page fetches that one immutable
bundle; strategy discovery ranks metadata first and fetches only selected notes
within its existing prompt budget. PDF companions download on demand through an
owner-authenticated route. The content is encrypted under the owning tenant and
office, separate from its active snapshot. This is not public-exchange admission.

An agent can create a validated `strategy_pack_transfer_v1` bundle, then call
`officekit_research.pack_directory.cache(office_folder, bundle, pdf_bytes)` to retain
it locally. The private cache is `.research-content/`. Upload the directory with:

```sh
./wp research-sync --dir ~/office --office HOSTED_OFFICE_UUID
```

Uploads contain at most 25 versions and approximately 8 MiB per batch. Each batch
merges against the current hosted revision, preserving holdings, goals, proposals
and other research. An interruption, expired login or revision conflict fails
visibly. Rerun after resolving it: the uploader checks hosted immutable IDs and
sends only missing versions. A historical court revision must name its predecessor;
metadata-only changes are versions too. The current catalog selects the latest
court version, while older content-addressed links remain readable. Historical
rulings remain research leads, never current suitability approvals.

The normal synced snapshot contains the directory only. An explicit hosted office
ZIP export hydrates all referenced bundles and PDFs into `.research-content/` so
the archive also works offline. When moving a directory to a different hosted
office, transfer its content with `research-sync` as well; copying the directory
alone cannot grant access to another office's private blobs.

Optional `forecasts` use the immutable private prediction schema, with original
capture timestamp, submitter, agent, model, protocol, probability, declared base
rate and explicit resolution criteria. Optional `outcomes` must refer to those
forecasts and contain a binary result, source URL and resolution time. The receiving
office records when it learned an outcome and labels attribution `claimed_import`.
Brier scores group by the original submitter and agent. Conviction ratings, legacy
rows missing their forecast contract, and inferred model identities are never
converted into attributed scores. Missing historical identity remains unknown.
