## Cause-check first

The screen fired on a contaminated anchor. SLI's 52-week high of $6.40 was printed **October 16, 2025**, a day the stock rose ~25% on speculation of a U.S. government equity stake, capping a +300% 2025 run ([Motley Fool, 2025-10-16](https://www.fool.com/investing/2025/10/16/why-standard-lithium-stock-soared-25-today-to-a-52/)). The company announced a $130M follow-on **that same day**. So dd52 −63% measures the deflation of a one-day speculative policy premium that the issuer itself monetized — not fundamental damage. The cohort tag is also wrong: SLI is a pre-revenue development-stage brine developer, and "excess_dd −0.435 vs Industrials/Major Chemicals median" compares it to operating chemical companies whose damage metrics (volume, margin, utilization) do not exist for SLI.

Separately, the cohort's implied commodity narrative is refuted by the tape: lithium carbonate (99.5%, CIF Asia, spot) was assessed at **$18,160/t on 2026-08-10**, down from $19,250/t end-July but far above the 2025 trough; China futures 147,500 CNY/t on 2026-08-13. Lithium recovered while SLI made new lows.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| SLI | **DAMAGE-ARRIVING** | Signed senior-secured project debt commitment (~$1.1B target) + offtake coverage to ~80% of 22,500 tpa nameplate — the two gates that convert FID from intent to fact | Debt is **indications of interest only**, not committed; offtake = 8,000 tpa Trafigura take-or-pay (10yr, signed 2026-03-09), ~36% of nameplate vs ~80% target. FID **slipped from end-Q2-2026 to "later this year"** — CEO David Park: *"earlier in the year, we were hopeful that we would be in a spot to FID by the end of the second quarter. We're clearly not there."* New **US$50M ATM filed 2026-08-11** on top of US$13.99M unused from the prior ATM ([SEC SUPPL 0001104659-26-093563](https://www.sec.gov/Archives/edgar/data/1537137/000110465926093563/tm2622588d1_suppl.htm)); [MD&A 6-K](https://www.sec.gov/Archives/edgar/data/1537137/000119312526341303/ck0001537137-ex99_2.htm) | **~2026-11-05 (yfinance-derived, UNCONFIRMED)** — but the binding dated checkpoints are earlier: remaining offtakes guided to **Q3-2026**, FID to **YE-2026** | Damage is real (FID slip, live ATM) but magnitude unresolved: the stated capital stack leaves SLI's own check far smaller than the drawdown implies — see reconstruction below |

### The decisive reconstruction — SLI's actual equity check

Company-stated stack for SWA Phase 1: base capex **~$1.5B**, senior secured limited-recourse project debt **up to $1.1B**, DOE grant **$225M** (finalized Jan-2025; NEPA FONSI issued May-2026), remainder as **pro-rata equity from Standard Lithium (55%) and Equinor (45%)**.

- Residual equity: $1.5B − $1.1B − $225M ≈ **$175M**
- SLI's 55% share: **≈ $96M**
- SLI liquidity: $137.3M cash at 6/30/26, **no term or revolving debt**, plus ~$64M ATM capacity ≈ **$201M**

On management's own numbers the construction equity is covered with headroom — this is not the death-spiral a −63% drawdown implies. Pre-FID burn is ~$36M/half ($9.0M operating + $27.2M JV contributions, six months to 6/30/26), and the company states it has funding "through June 30, 2027." **The entire equity story therefore hinges on one variable: whether the $1.1B debt closes at size.** A $300M shortfall adds ~$165M to SLI's check — roughly 71M shares at $2.33, ~29% dilution. That is the binary, and it is not yet resolved.

**COURT-WORTHY (damage-absent, ranked):** none. SLI does not classify damage-absent — the FID slip and the live ATM are confirmed deterioration. The one genuinely damage-absent *sub-claim* is the commodity leg: the lithium-price-collapse premise embedded in the cohort narrative is refuted by $18,160/t CIF Asia, and SLI's demonstration plant has processed >1M barrels of brine across 15,000+ DLE cycles with battery-quality carbonate validated downstream in Nano One LFP cells at ~155 mAh/g first discharge ([6-K 2026-08-13](https://www.sec.gov/Archives/edgar/data/1537137/000117184326005480/exh_991.htm)). Technical and commodity risk are retiring; financing and dilution risk are not.

**COURT-WORTHINESS SLI: 7/10** — a court would adjudicate one clean, sizing-flipping question: does the $1.1B/$225M/55-45 stack really cap SLI's check near $96M against ~$201M of resources, or do contingency and a debt shortfall blow it out into forced dilution at a 63% drawdown?

**PRINT PROXIMITY: ~2026-11-05 — yfinance-derived, UNCONFIRMED (no company PR names it).** Not within 5 trading days; Q2 already printed 2026-08-10, four days ago. No pre-print reconstruction is triggered. For completeness, the stance the reconstruction supports is **FLAT into any ATM window, revisit on a signed debt commitment** — with a live $50M ATM authorized three days ago and $14M unused before it, there is a disclosed continuous seller into every rally, and the catalyst that repairs the story (debt close → FID) is management-guided to year-end, not to the November print.

Two caveats on my own numbers: the $1.5B is **base** capex and excludes contingency/escalation, which the MD&A does not quantify; and Equinor's "up to $160M for 45%" is earn-in consideration for the interest, which I have treated as *separate* from pro-rata construction equity — the MD&A does not disclose the remaining earn-in balance, so if part of that $160M is still payable it would improve SLI's position, not worsen it.

Two pipeline defects this triage surfaced, flagged not fixed — I had no repo write or read access this session (the Grep on `signalos` was permission-denied), so I could not wire them:
1. **Sector mistag** — SLI is tagged Industrials/Major Chemicals and diffed against that sector's median dd52; pre-revenue developers need a separate cohort or the excess_dd is noise.
2. **dd52 anchor contamination** — the $6.40 anchor is a single-day speculative spike. Both are already on the TECH_DEBT list from batch 8/14; this is a concrete instance for each.

Also note: **IBKR tape verification was not available** — `get_price_snapshot` and `get_price_history` were both permission-denied, so all price facts above come from the evidence pack and public sources rather than a live broker pull. Per standing doctrine that is a gap, not a verified tape.