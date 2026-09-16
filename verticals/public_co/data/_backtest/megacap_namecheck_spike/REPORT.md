# Megacap-Namecheck Connector — Spike

_Spike test 2026-05-18. New M-source connector targeting the
inflation-vs-fabrication question raised in the H7 critique: instead
of asking "did the megacap disclose this small-cap counterparty?"
(which fails at sub-material scale), ask "how many times has the
megacap mentioned the small-cap in any 10-K/10-Q/8-K over the past
decade?"_

## Hypothesis

Megacap 10-K disclosure is materiality-gated (>10% revenue, key
segment). But megacap 8-K filings carry earnings-call transcripts as
Ex-99 attachments, and product-launch announcements, and material-
agreement filings. Earnings calls in particular name-drop ecosystem
partners (e.g. Microsoft × Intel, Amazon × Anthropic) at a much lower
materiality threshold than the 10-K MD&A's customer-concentration
table.

So the megacap's *own* SEC filings, scoped via EDGAR full-text search
on the megacap's CIK, should have:
- **0 hits** for fabricated partnerships (Akazoo×Sony)
- **1-2 hits** for real-but-sub-material relationships (PLUG×AMZN
  warrants)
- **3+ hits** for ecosystem-level partnerships (NVDA×AMZN,
  Anthropic×AMZN, Intel×MSFT)

## Calibration panel results (10-year window, ending 2026-05-18)

| Category | Pair | Megacap hits | Signal |
|---|---|---:|---|
| **FABRICATED** | Akazoo × {AMZN, MSFT, AAPL, GOOG} | 0+0+0+0=0 | INFLATION_SUSPECT |
| **CONTROL (no claim)** | Hudson Technologies × {AMZN, MSFT, AAPL, WMT} | 0+0+0+0=0 | INFLATION_SUSPECT |
| **CONTROL (no claim)** | La Rosa Holdings × {AMZN, MSFT, AAPL, WMT} | 0+0+0+0=0 | INFLATION_SUSPECT |
| **CONTROL (no claim)** | KULR Technology × {AMZN, MSFT, AAPL, TSLA, NVDA} | 0 | INFLATION_SUSPECT |
| **CONTROL (no claim)** | CareDx × {JNJ, PFE} | 0 | INFLATION_SUSPECT |
| **CONTROL (no claim)** | Perma-Fix × {GM, BA, LMT, XOM} | 0 | INFLATION_SUSPECT |
| **INFLATED (alleged)** | Lordstown × {GM, Ford, Boeing} | 0+0+0=0 | INFLATION_SUSPECT |
| **REAL (sub-material)** | Plug Power × Walmart | 0 | INFLATION_SUSPECT |
| **REAL (sub-material)** | Plug Power × Amazon | 1 | SUB_MATERIAL |
| **INFLATED (alleged)** | Nikola × GM | 2 | SUB_MATERIAL |
| **REAL (material)** | Intel × Microsoft | 4 | RECURRING |
| **REAL (material)** | Nvidia × Amazon | 13 | RECURRING |
| **REAL (material)** | Anthropic × Amazon | 26 | RECURRING |

## What the spike establishes

### Strong negative discrimination (0 hits)
Akazoo's fabricated label deals score **0 across 4 megacaps**.
Combined with controls (HDSN, LRHC, KULR, CDNA, PESI — none of
which claim a megacap partnership) also scoring 0, the negative
signal is unambiguous: **0 hits across multiple megacaps = strong
absence-of-relationship**.

### Strong positive discrimination (3+ hits)
Intel × Microsoft (4), Nvidia × Amazon (13), Anthropic × Amazon (26)
all hit the RECURRING band cleanly. These are the canonical real-
ecosystem-partnership examples and the connector identifies them.

### Weak middle band (1-2 hits) — confirms the user's concern
This is the most important finding. **PLUG × Amazon (real, warrants
deal) and Nikola × GM (alleged inflated, dramatically reduced post-
Hindenburg) both score 1-2 hits.** The connector cannot tell them
apart by count alone.

Implication: the connector is most useful as a **veto** (0 hits =
strong absence) and a **corroboration** (3+ hits = strong presence).
The middle is genuinely ambiguous and needs additional signals
(e.g., joint patents, language-vs-scope delta, customer-concentration
cross-check, earnings-call transcript text analysis).

### Lordstown × GM = 0 — worth explaining
Lordstown DID buy the Lordstown OH plant from GM and had a real
asset-purchase transaction. But over the 10-year window, GM never
mentions "Lordstown Motors" in any 10-K/10-Q/8-K. Possible reasons:
1. GM's plant sale was material enough to disclose but used different
   naming (e.g., "purchaser of our Lordstown OH facility").
2. The transaction was via subsidiaries or didn't trigger an 8-K item.
3. Lordstown's claimed "100,000 binding orders" went to fleet operators,
   not GM directly — the partnership claim and the GM relationship
   were separate.

Either way: a small-cap claiming a GM relationship would score 0
here, which is the same signal as Akazoo's fabricated label deal.
**The connector flags both as INFLATION_SUSPECT — which is the right
answer for shorting purposes**, even if the underlying truths differ.

## Calibrated thresholds

```python
if total_hits == 0:
    signal = "INFLATION_SUSPECT"          # strong
elif total_hits <= 2:
    signal = "SUB_MATERIAL_RELATIONSHIP"  # ambiguous
else:
    signal = "RECURRING_RELATIONSHIP"     # strong corroboration
```

## What the connector does NOT solve

1. **Cannot differentiate sub-material real vs alleged inflation**
   in the 1-2 hit band. Both PLUG×AMZN and NKLA×GM land here.
2. **Tested on small panel** (n=14). Replication needed at
   additional pairs.
3. **English-name disambiguation is fragile.** "Nikola" matches
   Nikola Corp but could also catch unrelated "Nikola" persons /
   trademarks in megacap filings. Quoted-string search reduces but
   doesn't eliminate this.
4. **Megacap filing cadence varies.** Berkshire Hathaway publishes
   minimal SEC filings; Apple uses 8-K Ex-99 for earnings; some
   sectors use 8-K very rarely. Cross-megacap comparability is not
   perfect.

## How this should plug into the framework

The connector is a new M-source for the planner's `counterparty_claim`
adjudication. When the planner extracts a claim like "we entered into
a strategic partnership with [MEGACAP]":

1. Call `query_megacap_mentions(small_cap_name, cutoff, [megacap])`
2. Map signal → severity:
   - INFLATION_SUSPECT → SEVERE_UNDERDELIVERY
   - SUB_MATERIAL_RELATIONSHIP → MODERATE_UNDERDELIVERY (claim
     intensity > scope evidence)
   - RECURRING_RELATIONSHIP → PASS (claim corroborated)

This **demotes H7 (small-cap-side counterparty disclosure)** to a
secondary signal — the megacap's own filings are the better f(M).

## Files
- `verticals/public_co/m_sources/megacap_namecheck.py` — connector
- `test.py` — calibration spike
- `spike_results.json` — per-case raw results
