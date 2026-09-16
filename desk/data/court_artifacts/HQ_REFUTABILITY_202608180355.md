## Context

`blob_sweep` selected HQ on `dd52 -0.706 / excess_dd -0.377`, but the cause-check disposes of the selection before refutability applies: HQ's 52-week high is a **parabolic low-float print on 2026-06-22**, not a pre-selloff fundamental anchor. The stock is **+98.7% above its 52-week low** ($8.29, 2026-04-02) and **+26% above its 2026-04-20 close** ($13.05). There is no drawdown to triage — there is a squeeze unwinding.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| HQ | **STRUCTURAL — selection void** | Recognized revenue (the only metric that can move a $0-revenue name off a hype multiple) | **$0.00 in Q2 2026**, flat at zero since inception; opex $7.18M vs $2.8M Q2'25 (+156% YoY); net loss $115.23M of which **$108.29M is non-cash warrant FV** (Adj. EBITDA −$5.46M) — [6-K ex-99.1, 2026-08-04](https://www.sec.gov/Archives/edgar/data/0002088256/000121390026084895/ea030025901ex99-1.htm) | **~2026-11-03 (derived, UNCONFIRMED)** — cadence Q1→05-05 (announced 04-21), Q2→08-04 (announced 07-21) | Drawdown cause = **float mechanics, not damage**. 52,966,280 Class A registered for resale = **91.92% of shares out**, against 53.97M total shares and **273,356 sh/day ADV** (~$4.6M). Effective free float ≈ non-redeemed SPAC shares + 2.4M warrant-exercise shares — [424B3, effective 2026-04-24](https://www.sec.gov/Archives/edgar/data/0002088256/000121390026047285/ea0287238-424b3_horizon.htm) |

**The mechanism, dated.** Merger closed 2026-03-19 at 51,578,134 shares (31.83M A + 19.74M B). PIPE was 9,196,021 sh @ $11.82 = ~$110.4M gross, yet total merger+PIPE proceeds were **$98.2M** — the trust contributed ~nil net, i.e. near-total redemption, which is what left the float this thin. Shares then went 51.58M → 53.97M, and that **+2.39M is exactly the warrant exercises** (~2.5M public warrants @ $11.50, $28.7M gross through 08-03). Warrant exercise roughly **doubled the tradeable float into the June 22 top** — that is the supply that broke the squeeze. It is now ~79% exhausted on the public side (~0.66M of 3,159,500 public warrants remain; 2,884,660 private warrants are separate).

**Cuts both ways, stated plainly:** with the general lock-up running to **2028-03-19** (sponsor up to 2027-03-19) there is *no near-term supply cliff*. A 3–5M share float, 273K ADV, and no release for 19 months means **HQ can squeeze again**. That is why this is not a short — it fails the MEME EXCLUSION gate outright — and equally why it needs no bid.

**Diligence flag (not a verdict):** IonQ holds **13.3%** (4,230,118 sh, SCH 13D) *and* is the vendor for the Dublin 256-qubit testbed HQ is purchasing. Strategic-holder-as-equipment-vendor is a circular-flow pattern worth resolving before any capital, alongside Peak XV 20.3% and Tencent 11.1%; CEO Fitzsimons holds ~38.3% economic / **65% voting**.

**COURT-WORTHY (damage-absent, ranked):**
*(none)* — HQ does not qualify. DAMAGE-ABSENT requires the narrative's predicted damage to be testably missing; HQ has **$0.00 revenue and an EV of ~$793M** ($906M cap less $113.25M cash). The generic quantum-hype narrative is not refuted here, it is *satisfied*. And the discount the sweep priced does not exist: the reference high is a 2-month-old +443% parabola in a stock with five months of trading history, so `excess_dd` vs a seasoned Technology sector median is not a comparable quantity.

**COURT-WORTHINESS HQ: 2/10** — the sizing decision is FLAT under every branch a red/blue bench could reach, so a court buys no information.

**PRINT PROXIMITY: NONE — verified two ways:** (1) no company PR names a Q3 date (last release 2026-08-06, conference participation only); (2) reporting cadence puts Q3 at ~2026-11-03, ~54 trading days out. No print-decisive reconstruction is owed.

---

**Two defects to report upward, not silently absorb:**

1. **R2.3 template-fill failure.** This dispatch arrived with `COHORT: ?` and `NARRATIVE: see cohort definition in knowledge_graph/cohorts.json` — both unresolved. Strictly, a narrative-relative classification is *not constructible* from what was passed; I classified against the generic quantum-hype narrative and the cause-check, and I'm flagging that substitution rather than hiding it. `cohorts.json` was unreadable in this session (permission not granted), so the slot could not be filled from source.

2. **`blob_sweep` sibling defect to commit `c2dd2cc5`.** That commit stopped the sweep from selecting LEVERAGE and reporting it as DISLOCATION. This is the same failure on a different axis: selecting **post-de-SPAC squeeze decay** and reporting it as DISLOCATION. The guard is a two-predicate preflight, both computable from data the sweep already has:
   - **reject if `pct_off_low > 0.50`** — a name that has nearly doubled off its 52-week low is not dislocated regardless of `dd52`;
   - **reject if trading history < 52 weeks** (first-print date, or de-SPAC/IPO effective date) — `excess_dd` vs a seasoned sector median is undefined when the lookback window isn't full.

   HQ trips both (`pct_off_low` 0.987; ~5 months of history). I have not touched `blob_sweep` — say the word and I'll wire the guard plus a backfill pass over the current queue to see how many other members it voids.

**Sourcing honesty:** sec.gov returned HTTP 403 to my fetcher on every direct attempt, so the two primary documents above were read through mirrors ([stocktitan](https://www.stocktitan.net/sec-filings/HQ/424b3-horizon-quantum-holdings-ltd-prospectus-filed-pursuant-to-rule--bb1c4f856e8d.html), [Quantum Computing Report](https://quantumcomputingreport.com/horizon-quantum-reports-q2-2026-financial-results-warrant-cash-infusion-beryllium-early-access-and-european-testbed-expansion/)) rather than fetched from EDGAR — the URLs cited are canonical but unverified by me at the source. The tape is the pack's `ibkr_gw` $16.47; I could not independently poll IBKR (permission not granted), though the 2026-08-17 close prints $16.80, consistent. Float and lock-up figures are the load-bearing claims and should be confirmed against the 424B3 itself before anyone acts on them.