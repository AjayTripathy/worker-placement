# From research to a strategy

The product has one derived catalog (`officekit_research.discovery.catalog`),
used by incoming-money deployment, new strategy creation and research browsing.
It reads the existing durable contracts. It is not a parallel research store.
Human-facing names live in `officekit_research.taxonomy` and appear in the
Strategies creation flow and the catalog.

| Type | Existing record | Meaning and use |
| --- | --- | --- |
| Security research | General court | Stock/fund findings independent of an office. Eligible evidence and per-claim admission govern exchange contributions. Reuse additionally checks freshness, protocol, intelligence tier and corroboration. |
| Strategy ideas | Strategy pack manifest + deck | Discoverable thesis, factors and tickers. Manifest validation is not investment approval. |
| Prior investigations | Reviewed contextual case | Retains original question, circumstances, argument, verdict and decision. Context differences must be considered; suitability does not transfer. |
| Office decisions | Private suitability ruling | Decision for this office and strategy, with dissent, conditions and unresolved questions. |
| Imported office theses | Owned desk-thesis snapshot | Legacy research retained with its previous verdict and date. A discovery lead, not refreshed evidence. |
| Source material | Published archive document | Reports, filings and datasets linked to original files. Path search locates documents; it does not extract or validate claims. |

Factor profiles remain attached to security research. Reusable mechanisms remain
detectors in the existing knowledge graph and promotion/dispatch pipeline; this
catalog does not create a competing mechanism layer.

## Lifecycle and attachment

1. Original work is saved in its existing contract. Another agent's general
   research enters through the admitted exchange; reviewed cases are explicitly
   imported. Strategy packs are installed or included in a reviewed published
   library version. Uploading a file to Git alone does not approve or deploy it.
2. Browsing derives ticker entries, original dates, authors, verdicts, source
   digests and stable links. Future-dated records and synthetic evaluation cases
   are excluded. Invalid cases/packs produce visible coverage warnings.
3. Every normal strategy proposal takes a bounded catalog snapshot before its
   first analyst call. Ranking uses seed symbols, strategy identity and terms in
   the brief. The snapshot reports omissions and retains negative verdicts.
   Incoming-money proposals use the Capital Planner profile, adding a private
   snapshot of goals, existing strategies, cash commitments and disaster
   scenarios before selecting tickers. See STRATEGY_PROPOSALS.md for that contract.
4. After selection, `research_attachments` records the matching snapshot URLs
   for each selected symbol. These are lineage matches, not assertions that the
   agent relied on every source or that a prior verdict applies.
5. Current evidence, the general court, office suitability and Risk Officer
   determine the proposed basket. The user records a decision separately.

No-reuse and evidence-only evaluation arms do not receive catalog arguments.
Viewing a catalog or deployment page never creates a proposal, calls a model,
changes balances or publishes research. Library path searches span published
areas and retain their authenticated document routes. Search does not bypass
publication gates or reach into a tenant's files.

Matching manifests deduplicate across installed and published sources; differing
versions retain distinct references even when their public IDs are the same.
Archived library content is immutable by version. Refreshing its search metadata
does not automatically promote legacy source documents into structured courts.

Private deals require explicit publication release. Office holdings, suitability
and decisions remain private. Attribution and original dates survive ingestion;
early calibration estimates do not determine admission or ranking.

Charitable goals, recipient choices, owned gift lots and tax-review assumptions
belong to the private office/strategy layer. They inform gifting programs and
capital deployment through the same catalog workflow, but never enter general
security court inputs or become public factor research. See CHARITABLE_GOALS.md.
