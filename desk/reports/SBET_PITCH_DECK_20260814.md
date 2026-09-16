No prior deck files here, so the deliverable is the deck itself. Both benches converged on REJECT (blue on corrected grounds), so the bands section carries reopen conditions rather than entry levels.

# PITCH — SBET — PROPOSED VERDICT (PROPOSED — PENDING ADJUDICATION)

**REJECT — no position, no substitute instrument; reopen only on a disclosed repurchase ≥$50M/quarter, a falling share count while the stock trades below 0.85× asset value, or a price near management's own revealed buy zone (~0.6× asset value, ≈$4.73 today).** PROPOSED — PENDING ADJUDICATION.

## What we believe

Sharplink (SBET) is a company whose business is holding Ethereum. It owns 889,355 ETH plus about $56M of other assets against $5.6M of liabilities, which at ETH ≈ $1,871 works out to **$7.89 per share of asset value against a $6.08 stock price** — the stock trades at roughly 77–80 cents per dollar of what it holds. Both our attacking and defending review teams verified that arithmetic independently and agree the discount is real.

We also believe the discount is **not a buyable opportunity**, for four reasons the review process converged on:

1. **The discount isn't closing fast enough to matter.** Management did buy back stock at the lows — 2.13 million shares at an average of $4.69 last quarter — but at a $10M/quarter pace, which is about 0.67% of their authorization and roughly 1% of shares per year. That pace cannot close a 20%+ gap. And in the three days after reporting the quarter, they committed $200M to *more* staked ETH rather than to buybacks.
2. **The riskier slice of the treasury is growing.** About 28.6% of the ETH is held through liquid staking tokens (instruments that track ETH but can trade below it and already carry a $76.1M writedown here). The new $200M staking deployment with Lido pushes that slice toward ~40%. The market may be pricing this haircut correctly, not irrationally.
3. **There is a structural lid on recovery.** The company has 16.3 million warrants outstanding at an average strike of $7.77 — including 10 million struck at $8.15, just above the $7.89 asset value. Any rally toward fair value runs into a wall of new share supply.
4. **The dominant exposure is ETH itself** — unhedged, high-volatility crypto beta that this book has no mandate for. A 20% discount is roughly one bad ETH week of cushion.

## What the market believes

The market prices SBET at ~0.77–0.80× its asset value and has kept it there. The implied view: the staking-token slice deserves a haircut, the buyback pace is token, the warrant overhang caps upside, and holders bear governance and mandate risk on top of raw ETH exposure. The 52-week high of $22.72 was reached when the stock traded at *more than twice* asset value — that premium has unwound, and the current price is +36–42% off the 52-week low of $4.46, so this is not a stock the market is dumping in a panic today.

## Why we might have edge

- The discount is verified arithmetic, not a narrative — two adversarial teams computed $7.89/share independently from the earnings release and the 10-Q.
- Management is genuinely **two-sided around asset value**: in the same quarter they bought back 2.1M shares at $4.69 (below asset value — accretive) and issued $75M of stock at $7.49 (near asset value — also accretive). A management that behaves this way *could* one day close the gap deliberately, and a large committed buyback would be a clean catalyst.
- A peer vehicle (BMNR) trades ~15 points richer on the same basic idea, so there is precedent for these discounts compressing.

## Why it might be priced in

- The 15-point gap to the peer is plausibly **correct pricing** of SBET-specific problems: a bigger liquid-staking-token slice (heading to ~40%), a warrant wall at $8.15, and slower buybacks.
- Revealed preference: within 72 hours of printing a quarter at ~0.80× asset value, management deployed $200M into more staked ETH. The mandate is ETH accumulation, not discount closure.
- The buyback pattern (zero in Q1, heavy at ~$4.69 in Q2) implies management's own trigger sits near **0.6× asset value** — well below today's 0.77. At this price, expect staking, not buybacks.
- Even if the discount closed fully, ~26% upside doesn't compensate for unhedged ETH downside on our sizing rules; anyone wanting the ETH exposure gets it cleaner via a spot ETF.

## What we checked ourselves

| Claim | How checked | Found | Confirmed? |
|---|---|---|---|
| Asset value ≈ $7.89/sh; stock at 0.77–0.80× | Both teams: 889,355 ETH × $1,871 + $56.2M − $5.6M ÷ 217.22M shares, from the [Q2 earnings release (Ex-99.1)](https://www.sec.gov/Archives/edgar/data/1981535/000149315226036741/ex99-1.htm) and 10-Q | $1,714.5M ÷ 217.22M = $7.89 | **Yes** |
| "Every buyback was above today's price — $10.24 average" (our attacking team's kill claim) | Defending team re-read the 10-Q *period-by-period* repurchase tables | **Our own bench erred**: $10.24 was a blend of 2025 buys at ~$16.35 with Q2-2026 buys at ~$4.69. Management **did** buy at the lows. Claim overturned. | **No — bench error, corrected** |
| "Zero net buyback into the discount window" (same team) | Share count and repurchase tables, Ex-99.1 + 10-Q | Overturned as stated: Q2 saw 2.13M shares bought at $4.69. What survives: pace is ~$10M/qtr (0.67% of authorization), and shares out *rose* +240k after 6/30 with no disclosed repurchases | **Partially — reduced to a scale finding** |
| $200M Lido deployment grows the staking-token slice | Read the press release body (the original thesis admittedly had not) | "Will stake $200M of ETH through Lido… receive wstETH." No rotation-from-existing-LST language; slice → ~40.6% pro forma | **Yes** (funding source unspecified — see unverified) |
| Warrant/dilution overhang | 10-Q equity note (closing a coverage gap the attacking team flagged) | 16,312,635 warrants, avg strike $7.77; 10.01M @ $8.15; 3.46M @ $6.15–8.00; 80k pre-funded. Dilution ≈ nil at $6.08, but the $8.15 wall sits just above asset value | **Yes** |
| Original thesis's tax argument ("selling shelters gains") | Cost basis math: ~$3.3bn ÷ 889k ≈ $3,710/ETH vs $1,871 spot | The treasury carries an embedded **loss**; there are no gains to shelter. Thesis error, caught by the attacking team | **Refuted** |
| Next earnings date 2026-11-12 | yfinance-derived only; no company PR names it | Unconfirmed | **No** |
| Live broker quote | IBKR quote tool permission-denied on **three consecutive runs** (flagged for the pipeline runner) | Working from Yahoo $6.08 (Aug-13 close $6.32 per secondary source) | **No — data-access gap** |

## PROPOSED ENTRY BANDS

**The courts say no entry at any price today** — the objection is the exposure itself (unhedged ETH beta with an unbounded staking-token tail), not just the price. So these are **reopen bands** — conditions to bring SBET back to court, not standing buy orders:

- **Reopen on action:** a disclosed buyback of **≥$50M in a single quarter**, or shares outstanding **falling** while the stock trades below **0.85× asset value** (≈ below $6.71 at today's $7.89 asset value). Either would show closure has become policy, not token gesture.
- **Reopen on price:** stock at or below **~0.6× asset value ≈ $4.73 today** — the zone where management's own Q2 buying fired ($4.69 average). Recompute against *live* asset value at trigger time, since it moves daily with ETH; the dollar level is only valid at ETH ≈ $1,871.
- **Ceiling to respect in any future long case:** the **$8.15 warrant wall** (10M shares of supply just above the $7.89 asset value) caps realistic recovery; any reopened thesis must model exits below it.
- **Sizing if ever reopened:** the defending team's framework treats this as risk that fails the bounded-tail bar regardless of price, so any future position would need the staking-token slice bounded (e.g., disclosed rotation out of LSTs) before sizing above a starter.
- **Catalyst dates:** next earnings ~**2026-11-12 (UNCONFIRMED** — derived from a data vendor, not a company announcement); weekly treasury/share-count press releases are the higher-frequency tell.

## ARMED SENSORS

(armed provisionally with this deck; session adjudication ratifies)

- price alert: fires below 4.73 (deck-provisional: ~0.6x asset value ($7.89/sh at ETH $1,871) — management's revealed Q2-2026 buyback zone ($4.69 avg); r)
- filing watch: 8-K,10-Q until 2027-02-10 (deck-provisional: reopen trigger: disclosed repurchase >=$50M/qtr or shares outstanding falling while stock <0.85x asset)
- dated pack SBET|2026-11-12: SBET: Q3-2026 earnings (vendor-derived, no company PR confirms) (date confirmed=False)


## What remains unverified

- **Next earnings date** (2026-11-12 is vendor-derived, no company confirmation).
- **Funding source of the $200M Lido deployment** — native ETH (slice grows to ~40.6%) vs rotation from existing staking tokens (slice stable, and materially bullish for the risk picture). The press release doesn't say.
- **Unvested options/RSUs** — not disclosed in the 10-Q extract pulled; warrant count is verified but the full dilution picture isn't.
- **The ~0.6× buyback-trigger hypothesis** — inferred from one quarter's pattern (Q1 zero, Q2 heavy at $4.69). It's a single observation, not a policy statement.
- **Live executable quote** — IBKR access was permission-denied on three consecutive court runs; all price work rests on Yahoo/secondary tape.

```json
{"price_gates": [{"level": 4.73, "direction": "below", "basis": "~0.6x asset value ($7.89/sh at ETH $1,871) — management's revealed Q2-2026 buyback zone ($4.69 avg); recompute vs live NAV at trigger"}, {"level": 7.89, "direction": "above", "basis": "asset value per share — approach signals discount closure and tests the 10M-warrant wall at $8.15"}], "event_gates": [{"forms": ["8-K", "10-Q"], "why": "reopen trigger: disclosed repurchase >=$50M/qtr or shares outstanding falling while stock <0.85x asset value"}, {"forms": ["8-K"], "why": "treasury deployment PRs: LST sleeve crossing ~40% of holdings, or rotation OUT of LSTs (bullish, would rebound the risk case)"}], "catalyst_dates": [{"date": "2026-11-12", "what": "Q3-2026 earnings (vendor-derived, no company PR confirms)", "confirmed": false}], "immediate_entry": null}
```