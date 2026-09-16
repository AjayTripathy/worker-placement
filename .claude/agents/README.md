# SignalOS Finance‑Agent Suite

Anthropic's finance‑agent release ships **10 ready‑to‑run templates** (skills + connectors +
subagents) for high‑value financial work. This suite adds them here **with SignalOS as the flagship
"supercharged quantitative analyst"** — the verification‑and‑alpha layer the standard templates lack.

**The pattern:** the suite agents draft, model, and summarize; **`signalos-quant-analyst` decides
what's actually true and where the edge is.** Any time a number has to be *trusted* (not just
reported), the suite agent hands off to SignalOS, which verifies it against primary sources
(EDGAR XBRL, USASpending, EMMA, satellite, live IBKR) and runs the two‑mode honesty pass.

| Agent | Anthropic template | What SignalOS adds |
|---|---|---|
| **signalos-quant-analyst** ⭐ | *(the flagship — net‑new)* | Two‑mode DD, honesty‑alpha, primary‑source verification, the dispatch pipeline + connectors |
| `pitch-builder` | Pitch Builder | A Mode‑B disconfirming pass so the comps/pitchbook aren't promotional; every comp number verified |
| `meeting-preparer` | Meeting Preparer | Entity resolution + connector‑sourced counterparty briefs (litigation, sanctions, filings) |
| `earnings-reviewer` | Earnings Reviewer | EDGAR XBRL deltas + multi‑venue claim‑consistency; flags takeaway‑vs‑data divergence |
| `model-builder` | Model Builder | Models built from audited XBRL + live IBKR, with cap structure pulled before EV claims |
| `market-researcher` | Market Researcher | Satellite + federal‑procurement alt‑data; physical ground‑truth vs the narrative |
| `valuation-reviewer` | Valuation Reviewer | Live‑price comps + the "verify, don't assert" check; UNVERIFIABLE ≠ approved |
| `statement-auditor` | Statement Auditor | Forensic claim‑consistency across filings/venues; the honesty‑divergence lens |
| `kyc-screener` | KYC Screener | OFAC + corporate‑registry + USASpending + entity resolution (real connectors SignalOS already has) |
| `gl-reconciler` | General Ledger Reconciler | Standard ops template; SignalOS overlays an independent recompute/tie‑out check |
| `month-end-closer` | Month‑End Closer | Standard ops template; SignalOS overlays anomaly/divergence flags on the close |

**Honest note:** the last two (GL recon, month‑end close) are back‑office fund‑accounting workflows
*outside* SignalOS's investment‑analyst remit — they're included for suite completeness, with
SignalOS contributing only an independent verification overlay, not the core ops.

**Deploy:** these are Claude Code subagents (`subagent_type: <name>`). They inherit the session's
tools and reach data‑provider MCP connectors via ToolSearch. Optimized for Opus. Keep a human in
the loop — review and approve before anything goes to a client.
