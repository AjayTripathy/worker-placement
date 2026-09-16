# Portfolio Doctrine — conditional rulings for books and wrappers

**Scope note:** these are CONDITIONAL rulings — each binds only when the tenant's profile and personal context match its stated condition (net buyer, cash-rich, taxable at top bracket, running an external harvester, etc.); none is universal. Tenants adopt them as plane-2 doctrine entries by id, pairing each ruling with their own profile facts. Ruling dates are preserved; a later amendment supersedes an earlier state of the same ruling.

## premium-selling-taxable-gate

**CONDITION: taxable book at a top combined bracket (~50%+ ordinary), tax-loss-harvest mandate. RULE: net-credit option premium (CSP/CC) is banned by default — it is non-deferrable short-term ordinary income and anti-TLH — except through three narrow, gated templates; net-debit defined-risk structures are outside the rule entirely.**

Doctrine arc: blanket ban (2026-07-02, caught on a LULU plan — same-day corrections to LULU/PODD/FUTU); amended to a gated live CSP program (2026-07-30); narrowed to two taxable templates (2026-08-03, "do we actually want to sell options?" → "BARELY"); net-debit carve-out (2026-08-11, first applied to a WYNN Macau bull-spread barbell); paid-trim CC template added (2026-08-21).
- Why the bar is high: premium "yield" is worth ~half its face after tax; the same entry discipline is free via resting GTC limit ladders, and fills create deferrable stock basis instead of income events. A book with underwriting edge OWNS optionality, mostly doesn't sell it. But the corrected after-tax comparison shows a gated CSP beats the free GTC ladder by ~P/2 in 3 of 4 states (~6-9%/yr on waiting capital) — hence templates, not a ban.
- Template 1 (event-IV CSP): pre-committed court band, the pack pre-commits through the event, after-tax math explicitly clears (QCOM precedent).
- Template 2 (dead-chain paid GTC): resting offers in dead chains at court bands, 1-2 contracts, research value counts (FAF precedent).
- Template 3 (paid-trim CC): a CC is a paid trim order — completed position only (no pending adds; WAL is the named non-example), strike at a court trim ladder, VRP positive + liquid chain, meme/catalyst exclusion, contracts ≤ rung size, qualified-CC OTM strike preserving holding period. The ladder fill realizes the gain anyway; the only delta vs the free ladder is the premium.
- Eight standing gates: liquid-US-chain executability at entry (the KALMAR catch) · RP_FAIR names only · strike ≤ court band · meme/squeeze exclusion · kill-linked mandatory buy-to-close · cross-account wash-sale check per name · 100sh replaces the full rung · CSP notional ≤5% of base until a 6-month graded record.
- Everything else runs SHADOW-ONLY as fund-wrapper evidence. The ledger file outranks memory — reference implementation: desk/data/csp_shadow_ledger.json (`_doctrine`, `_program_ruling_20260803`, `_cc_template_ruling_20260821`); desk/cc_paid_trim_scan.py flags when a trim ladder comes within 15%; shadow adds via `python3 -m desk.csp_shadow add` (IV as decimal fraction, not percent).

## put-selling-floor-and-vrp

**CONDITION: any premium-selling proposal, any book. RULE: high IV is never the trade signal — pass four ordered tests (break-floor ≥ strike; IV > RV; sleeve arithmetic first; no supply calendar in tenor) or reject.**

Ruling 2026-07-30: a directed "flip to selling puts" on the AI complex produced four full courts, four REJECTS, each a distinct failure mode now forming the checklist:
1. ORCL — NO FLOOR: break value $0-25 vs lowest strike 70 (debt + uncommenced leases consumed the annuity); "fair probability × catastrophic severity" is not premium.
2. VRT — NEGATIVE VARIANCE PREMIUM: IV 70.7 vs RV30 85.6 post-crash — selling below actuarial cost; the strikes that pay sit above the ownership band.
3. Mega-cap AI name — FAIR-NOT-PAID + house-specific: sleeve headroom under one contract, assignment would stack the book's largest existing exposure, premium under T-bills at floor strikes. Order of operations: sleeve/concentration/wash-sale arithmetic BEFORE valuation judgment.
4. SPCX — SUPPLY CALENDAR AHEAD: a verified unlock waterfall contaminates every tenor; spot 5x business floor.

Why: post-crash IV follows realized vol up, so vol looks rich exactly when it is fair or cheap; and the strikes that pay always sit in the no-support zone between spot and the floor. The surviving alternative is usually the free GTC ladder at the band (see: premium-selling-taxable-gate). Names passing all four can still clear court (EQT/QCOM precedent).

## deployment-conditioned-index-insurance

**CONDITION: net buyer with unconditional inflows. RULE: cash-rich state buys NO index insurance (drawdowns are discounts); the protection phases in only as the book approaches full deployment, and unwinds when it returns to cash-rich.**

Original rule: insurance is for forced sellers, levered, or decumulating books. Amended 2026-08-03 (principal-ratified): the premise — powder to buy discounts — EXPIRES with deployment, so a fully-deployed book carries phased tail protection.
- Phasing: insurance scales with the thing it protects, never ahead of it — each increment of net equity deployed adds ~0.85-1.1%/yr (of covered notional) in long-dated deep-OTM index tail premium; target ~50-60% notional coverage at the −20% strike zone once fully deployed (priced at 2026's ~12.7 ATM vol — dated — re-verify before relying).
- Vehicle: XSP/SPX-class ONLY (Section 1256, 60/40 treatment) — expiring-worthless legs harvest as capital losses in a max-TLH book; never SPY options (equity-option tax), never a standing physical index short.
- Tenor matched to the model window the hedge grades against; cohort-tag the legs so the edge claim grades with its thesis.
- Funding symmetry: sold legs (periphery spreads, dead-chain court-band premium) part-fund the bought tail — sell overpriced insurance to pay for underpriced insurance.
- Exit/kill: the thesis board going green OR the book returning to cash-rich unwinds the protection — insurance follows the deployment state, not the fear state.

## beta-placeholder-and-index-landing

**CONDITION: alpha book inside a household that already carries substantial core cap-weight index exposure elsewhere. RULE: no physical US cap-weight placeholder in the alpha book (it duplicates the core) — but idle cash is still GRADED against SPY-same-window, and a large cash landing deploys index-first before rotating to single names.**

Doctrine arc: adopted 2026-07-05 (idle capital defaults into a broad ETF; cash must defend itself like any position — the gate cohort had foregone ~8.6% avg in 5 weeks of up-tape while a failed single-name at starter sizing costs 15-30bp); amended 2026-07-06 (no physical placeholder — the household core already carries the beta; duplication rejected); amended 2026-08-21 (large-windfall landing re-authorizes physical broad index for exactly two roles).
- What survives from the original: idle cash, gates, and missed entries all benchmark against SPY-same-window; a gate's true cost is (name minus beta); the missed-entry scorer never compares to nothing.
- The two authorized index roles: (1) day-one deployment vehicle for a large cash landing — index-first, migrate to the TLH slot map via harvest-driven rotations; (2) permanent completion sleeve (whatever remains unrotated at month 12). The ban stands for its original case: never park an individual thesis in an index while awaiting its court.
- Long leg is BROAD, never QQQ (doubles AI concentration vs a typical cap-weight core); hedge leg is NDX-class §1256 puts. Reference implementation: desk/data/DEPLOYMENT_RUNBOOK_5M_20260821.md.
- Instrument case law: SPLG was RENAMED SPYM on ARCA (conid 45540646, same fund, ~0.02% ER, qualified divs) — verify identity by conid, not ticker (dated — re-verify before relying).

## factor-sleeves-computed-not-capped

**CONDITION: capital-abundant book (dry powder + committed inflows exceed the supply of courted candidates). RULE: compute the factor sleeve (held + resting + staged = INTENDED allocation) before dispatching any court and print it in the DD brief — but sleeves are information, never gates; no court may refuse or shrink a name on axis-cap grounds alone.**

Two rulings merged:
- 2026-07-15 (the catch): eight names each passed court at a defensible 1-3%, but one factor ("AI-disruption discount on enterprise software/services is overdone") silently stacked to 29.2% held / 36.2% intended (HUBS/SAP/CTSH/MNDY/G/IBEX/NOW + III/IT pending). Courts grade names; nothing graded the factor. Per-name kill triggers don't protect against the common factor being right.
- 2026-07-29 (the cap removal, OMF staging): with abundant capital, forcing name-vs-name trims inside an axis solves a constraint that doesn't bind — the scarcity is courted candidates, not capital. The court had also conflated the financials umbrella with the credit axis (WRB is P&C; cancelling it reduced credit-tail risk by zero).

How to apply: (1) sleeve math from positions + live orders + staged instructions — plans count toward intended; (2) the court adjudicates the MARGINAL position, not the name in isolation; (3) "factor-capped shelve" is a distinct verdict state — court verdict VALID + entry WITHDRAWN, packs still paper-scored, re-entry is a fresh proposal (first instance: IT/Gartner, 2026-07-15); (4) when a cap does bind, resting/staged orders are the cheapest lever (free to cancel) and tax-consequential positions the last (~37% ST-gain displacement); (5) the principal owns any numeric cap — propose the number, never assume it; (6) per-name sizing discipline (0.5-1.5% starters, kill triggers, conviction gate at n≥20) is unchanged; revisit the no-caps regime at full deployment or leverage.

## equity-over-bonds-for-tlh

**CONDITION: taxable tax-loss-harvest book at top state+federal brackets. RULE: when a thesis has both a bond and an equity expression, lead with the equity — bond market discount is ordinary income (IRC §1276) and un-harvestable; high variance is a feature, so size for recoverable variance and cap only the permanent-impairment tail.**

Stated 2026-06-29. A bond bought below par accretes market discount taxed as ORDINARY income at disposition (~50%+ combined top bracket), coupons are ordinary too, and bonds held to recovery don't generate harvestable swings; equity gains are LTCG (~33% all-in) and equity losses harvest against the gain goal. Applied: a Ukraine sleeve flipped from the sovereign step-up bond to MHP/Astarta equity. Keep the bond expression only as a tax-deferred/IRA-sleeve alternative.
Variance corollary: don't reflexively shrink wide distributions. Distinguish recoverable variance (drawdown that snaps back on a catalyst — size FOR it; volatility manufactures harvestable losses while keeping exposure) from permanent impairment (squeeze-out, going-concern, fraud — CAP it). Pair correlated-but-not-substantially-identical names (e.g. MHP↔Astarta) as a wash-sale rotation pair to harvest through the 31-day window.

## dogfood-payup-allowance

**CONDITION: a "dogfood" sleeve of tools the desk itself depends on. RULE (2026-08-15): fair-to-modestly-rich verdicts get tranche-1 at tape instead of a pure price gate — bounded at ~0.3-0.5% tranche size and ~3% aggregate sleeve cap (provisional); courts keep full kill authority.**

Origin: a CBOE court killed entry-now on top-of-band fairness; principal ruled "okay to pay up for dogfooding." The sleeve's edge is usage telemetry plus the ownership preference itself — for infrastructure you can't route around (broker/exchange/toll-road class), fair value IS the entry; waiting for cheap forfeits the position for a discount that may never come. The allowance moves the ENTRY bar only, never the exit or integrity bars: the court's price zone becomes the ADD zone, its dated tests govern tranche-2, and it does NOT apply where the court finds actual overvaluation (vs mere fairness) or integrity issues. Related: see fairly-paid-risk and TINA doctrine.

## zero-basis-tax-reserve

**CONDITION: large realized gain landing in a taxable account (e.g. zero-basis windfall). RULE (2026-08-03): carve the tax reserve FIRST — ~37% of a zero-basis gain at blended top CA+federal LTCG rates — hold it in SGOV-class T-bill funds, and treat only the residual (~63%) as the deployment budget.**

The intuition "no reserve needed — if we lose it we won't owe tax" is backwards and dangerous: the gain is fixed in its tax year the moment the position is sold, and capital losses carry FORWARD only, never backward. Deploy the full amount, lose 30% the following Q1, and you hold impaired assets, an undiminished bill due in April, and losses that offset gains you don't have — the dot-com option-exercise failure mode (exercised 2000, wiped out 2001).
- The one escape: losses realized before Dec 31 of the SAME year net against the gain — which makes same-year harvesting a dated deadline, not an optimization: every unit harvested before Dec-31 releases ~37% of it from reserve into deployable capital.
- Reserve vehicle: SGOV-class (state-tax-exempt, zero duration, liquid on the estimated-payment dates — Q3 est. Sep 15, Q4 Jan 15, balance Apr 15 — a calendar that front-runs any forecast drawdown window).
- Reference implementation: desk/data/tax_shelter_ledger_2026.json.

## muni-taxable-gate

**CONDITION: any tax-exempt-yield strategy. RULE (2026-06-10): verify TAX STATUS per CUSIP on EMMA at entry before any TEY gross-up — an optimizer maximizing a tax benefit harvests exactly the names where the premise is false.**

An after-tax-TEY selector surfaced a fake "8.75% after-tax" basket by loving high odd coupons (5.105%, 5.32%, 4.032%) near par — the signature of federally TAXABLE munis (BABs-era/2019-21 taxable refundings, judgment-obligation, taxable limited-obligation), for which the ~×2 gross-up is invalid. 27 of 106 scanned candidates were taxable; prior baskets escaped only by accident (liquidity gate ×2, issuer dedup ×1 — luck, not design).
- Tells: three-decimal coupons, near-par pricing with ~100bp+ yield premium to the exempt curve.
- Verification: EMMA states `TAX STATUS : TAXABLE` (Final Scale section) and/or `(FEDERALLY TAXABLE)` in the issue title; also reject JUDGMENT OBLIGATION and LIMITED OBLIGATION sectypes; screen the AMT flag. No constraint built for another purpose counts as the check. A-audit same day found 2 more taxable CUSIPs (91412GXY6, 91412GN43) whose praised "mispriced" yield pickup was just the taxable premium — the market was right.
- OID corollary (2026-06-11): a discount muni's after-tax yield is not computable from current price alone — pull the original issue price (EMMA Security/Details 'Initial Offering Price') to split tax-exempt OID accretion from ordinary-income market discount (de-minimis measures from ADJUSTED issue price). Treating all discount as market discount is the safe default (errs low); never the reverse.
- Reference implementation: build_option_B.verify() taxable flag; gate also wired into build_option_A_backfill.py.

## attention-instruments-sector-conditional

**CONDITION: any attention/heat instrument (Wikipedia views, search trends) proposed as a signal on a new cohort. RULE (2026-07-02): backtest per cohort against printed fundamentals BEFORE reading any name — the instrument does not transfer across sectors — and enforce a views floor (<~200 views/mo is noise-floor).**

Case law: luxury cohort backtested ~0.4-0.5 correlation (ex-outliers), but US mid-cap specialty apparel backtested NULL on the same method (within-brand directional 0.382 — below coin-flip; same-quarter Pearson ~0; cross-sectional rank −0.055; n=68-69). Why: mid-cap apparel attention is news/campaign-driven (viral ads, controversies), not shopping intent; secular wiki-decay drift dominates YoY direction; low comp dispersion leaves nothing to rank. Tiny bases fabricate signals (a ~10 views/mo article produced a fake +133% "heat" on BKE).
How to apply: when the attention layer is dead for a name, find the PRIMARY-data tripwire instead (e.g. monthly comps press releases). A NULL backtest is a positive finding — catalog it so nobody retries the same instrument on the same cohort.

## count-goals-bend-selection

**CONDITION: any "find N investable tickers" goal. RULE (2026-07-04): count pressure leaves per-name rigor intact but bends SELECTION, TEMPO, and FRAMING — so count-goals carry a diversity constraint (max 2 per thesis family toward the count), staging cadence never changes under a goal, and marginal grades are never promoted in framing.**

Audit evidence: the underwriting bar held (rejections continued under pressure — BBWI and Hyundai; every survivor downsized and tranche-gated), but three leaks ran around it: selection drifted to the countable (mining an already-verified vein → three names, one thesis family; the harder mechanism theses run post-goal produced 0 entries and better knowledge); tempo compressed (staged in 24-48h vs the soak-as-READY norm); framing promoted 5/10 merely-RP_FAIR plans to "found ✓". Why: courts guard the name level; nothing guards portfolio-level outputs (concentration, tempo) — pressure flows to the unguarded level.
Empirical check pattern: tag goal-cohort calls in the calibration ledger (e.g. `cohort: goal_pressure_YYYY_MM`) and at resolution compare their Brier/outcomes vs the non-goal book — if the goal cohort grades worse, the leak was bigger than the audit found.

## pnl-attribution-picks-the-pond

**CONDITION: before building or trusting any idea-generator/screen. RULE (2026-08-03): attribute realized P&L first and calibrate the screen on the entry-time signature of what actually made money — a generator encodes a hypothesis about where edge lives, and unchecked it runs at full throughput in the wrong pond.**

Case law: fourteen consecutive courts produced zero passes and it read as a dry market; the P&L said otherwise — 94% of the book's unrealized gain came from ten names (HUBS, GCT, DFIN, CTSH, SAP, BRBY.L, MNDY, KNSL, G, HRTG: software, services, insurance, brands), while all fourteen courted names were 0.5-0.9× book industrials, distributors, banks, retailers — because every generator owned was a cheap-on-assets screen aimed at a category that had produced none of the returns. The winners at entry sat at a median −46% (range −38 to −77%) to their own 3-year highs: good businesses at deep discounts to their OWN valuation history — a pattern book value structurally cannot express.
Validation standard for a recalibrated screen: it should surface names already held or admired, unprompted. Reference implementation: verticals/generators/quality_drawdown.py (weekly gen_quality_drawdown).

## ratchet-check-your-own-bar

**CONDITION: any adversarial review process whose pass rate collapses. RULE (2026-08-03): every correction adds a gate and none removes one — the ratchet is monotonic — so before believing "the market is expensive," blue-team the rejections and back-test every new gate against your known winners.**

Case law: ten disqualifying gates added in ~24 hours (mix regression, pension adjustment, earnings-durability, cohort takeout math, window-anchoring, touch-vs-terminal units, strict book denominator, PFIC-on-drawdown, no-quiet-period, snapshot dedup) — each individually correct, each from a real error. At ~15% rejection per gate, ten gates cut a 50% pass rate to 10%. Fourteen courts, zero passes — an outcome indistinguishable from "expensive market" unless deliberately tested, and the market explanation is the comfortable one.
Two standing checks: (1) blue-team the near-miss rejections with red-team rigor — if none flips, the bar is calibrated; if most flip, the ratchet is the problem; (2) back-test each new gate against realized winners — would it have rejected DFIN? killed BRBY.L? Any gate that blocks the best historical positions is overfitted to the single failure that created it. A filter that rejects everything is a wall; its rejections stop carrying information. Reference implementation: desk/data/setup_drought_diagnosis_20260803.json.

## long-dated-collar-mechanics

**CONDITION: designing any multi-year index collar, especially against an asset held at another custodian. RULE (2026-08-08): strike off the implied FORWARD not spot; size in SPX not XSP; and check the short-call notional against the EXECUTING ACCOUNT, not the hedged asset.**

Three reusable mechanics from a live-priced (not executed) Dec-2027 collar design on a large externally-custodied direct-index sleeve:
1. **Forward, not spot.** Put-call parity on two matched strikes gave DF 0.9498 and an implied forward +5.7% above spot at ~16 months (8,151 vs 7,710 — dated — re-verify before relying). A call "10% above spot" is only ~5% above the forward; a symmetric-around-spot collar quietly sells most of the expected return. Tell: the "symmetric" structure threw a large credit instead of pricing near zero. Derive the forward from `(F−K)·DF = C−P` on two strikes — never assume spot.
2. **XSP cannot carry institutional size; SPX can.** The same hedge was ~119 XSP contracts vs 13 SPX; XSP open interest at the needed long-dated strikes was 9-51 contracts — less than the order — with ~6% spreads and invalid broker IV; SPX OI at the same expiry was 2,000-104,000 with ~1.8% spreads. A quoted price is not an acquirable one — check OI against your own order size before designing anything.
3. **Cross-custodian collars have a funding mismatch.** The short-call notional was ~10× the executing account's NLV: at index +23% the short calls owed ~88% of that account's NLV; at +30%, ~151%. The hedge "works" at household level while the executing account is wiped out — margin calls land where the option is, paper gains sit where the asset is, monetizable only by realizing the gains the collar was built to avoid. For a custodied sleeve, the correct venue is an OTC collar with the custodian, where the assets themselves are collateral.

## incoming-gain-harvest-hedge

**CONDITION: a large realized capital gain awaiting its tax bill PLUS a live systematic tax-loss harvester (direct-index / long-short SMA). RULE (2026-07-10): treat the tax reserve as ANTI-CORRELATED with the market, not fixed — a selloff spikes harvest, offsets the gain, shrinks the reserve — an automatic, convex drawdown cushion that argues against pre-hedging the harvester-held book.**

Mechanism: a selloff pushes the harvester's lots underwater → realized losses spike → they offset the incoming gain → the reserve shrinks → net worth is cushioned. Linear factor models miss it because they hold the reserve fixed.
Heuristic model: incremental harvest ≈ `gross_long_MV × capture × max(0, −equity_move − embedded_gain_buffer)` with capture ≈ 0.6 (realizable-as-loss net of wash-sale friction) and embedded_gain_buffer ≈ 0.159 (smaller drops just shrink embedded gains — no new losses); then `reserve_scenario = max(gross×rate − min(base_harvest+boost, gross)×rate, 0)`; cushion = base_reserve − reserve_scenario. Properties: convex (bigger crash → more harvest), capped at the gain, one-tax-year only. Modeled result: worst-case tech-wipeout drawdown improved from −31.6% to −27.3% of net worth; ~zero cushion for shocks inside the embedded-gain buffer.
Meta-pattern (same ruling): insights live as registered PROGRAMS, not prose — each effect is a decorated function `fn(ctx)->{delta|shadow, fires, note}` with metadata (ENCODED moves the number / NOTED computes a shadow), a dispatch `run(ctx)`, and a selftest; surfaces dispatch the registry, and a new insight = a new registered effect + test, never an engine edit. Reference implementation: desk/effects.py (registry), desk/disaster.py `_tax_hedge`. Sibling NOTED effects worth porting: low-fixed-rate mortgage as an economic rates short; illiquid mark-lag (false near-term stability); harvester short-book flight-to-quality rotation; correlations→1 in liquidity crises.
