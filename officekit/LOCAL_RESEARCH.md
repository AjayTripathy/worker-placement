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
