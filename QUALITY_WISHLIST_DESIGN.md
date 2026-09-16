# QUALITY_WISHLIST — design proposal (fix 4 of the slow-slide review)

**Status: APPROVED 2026-08-13 — principal ruled same day: A=hybrid, B=two-band, C=manual Parametric list, D=8% sleeve cap. Financials-excluded v1 scope stands. Build dispatched; wishlist ACTIVATES only after the principal culls the mechanical candidate list to ~75.**
**Origin: the SPGI miss postmortem. Fixes 1–2 (broad-US universe, 63d/widening windows) and fix 3 (cohort layer) make the dislocation instrument complete — but all of them require something to FALL. This is the fourth failure class: the quality name that gets cheap without falling, by standing still while earnings grow. No drawdown-triggered screen can express the TINA doctrine ("for quality, fair value IS the entry"). This is a different instrument: a shopping list with prices, not a dislocation detector.**

## 1. What it is

A standing list of ~75 never-researched quality compounders, each carrying **valuation-percentile bands computed against its own history** — alerting when a name enters its cheap decile *regardless of how it got there* (drawdown, sideways drift, or earnings growth under a flat price). Band-fires feed the court conveyor exactly like dislocation fires; the wishlist proposes, courts dispose.

## 2. Universe seeding — DECISION A

Three options:
- **(a) Mechanical:** XBRL screen over the S&P 500 + broad universe → every name passing the quality gate (§3). Pro: no taste bias, reproducible. Con: ~150–250 names, includes quality-shaped value traps.
- **(b) Curated:** principal names the compounders they'd own at a price. Pro: high prior. Con: taste bias, small n, staleness.
- **(c) Hybrid (recommended):** mechanical screen produces ~200 candidates → principal culls to ~75 in one sitting → each name gets **lazy court verification**: no court until its first band-fire, at which point trap-verify runs the quality claims before any red/blue. Saves court capacity for names that actually get cheap.

## 3. The quality gate (mechanical, from audited XBRL — plumbing exists in court_evidence)

A name qualifies if, over the trailing 10 years:
- ROIC > 15% in ≥ 8 years (or ROE with leverage guard for financials — but see §6, financials carry their own trap catalog)
- Revenue grew in ≥ 8 years (durability, not velocity — no growth-rate minimum, per the GARP lesson that trailing growth screens are fragile)
- Gross margin stable-or-rising (10yr slope ≥ 0, or level within 300bps of the 10yr median in the latest year)
- Net debt / EBITDA < 2.0 (unlevered tails — the carry precondition)
- Diluted share count flat or shrinking over 10 years (owner-alignment; screens out serial diluters and roll-ups whose EPS is acquisition-stepped)

Deliberately absent: any valuation input (that's the band's job, not the gate's) and any growth-rate minimum (peak-growth screens select for base effects).

## 4. The bands — DECISION B

All percentiles are **own-history** (10yr, weekly samples) on two multiples: EV/EBIT and P/E. Never cross-sectional — the ADR-P/B and conservative-FV lessons both say peer-relative anchors mislead; a compounder's own history is the honest reference.

- **FAIR band** — multiple ≤ own 10yr **median**: fires a *tranche-1* proposal. This is the TINA doctrine mechanized: for a still-compounding business, median-of-own-history is the entry, and waiting for cheap is a bet the market misprices it twice.
- **CHEAP band** — multiple ≤ own 10yr **20th percentile**: fires a *starter* proposal (full court, standard sizing).
- **STANDING-STILL trigger** (the SPGI-class catch): multiple percentile fell ≥ 25 points over 12 months **while trailing EPS rose** — the name got cheap without a drawdown. Fires at any percentile level, labeled STANDSTILL.

Two-band vs cheap-only is the real decision: two-band produces more fires and directly tests TINA; cheap-only is quieter but re-imports the wait-for-blood bias the doctrine rejects. Recommended: **two-band, with FAIR-band fires capped at tranche-1 sizing.**

## 5. Trap guards (encoded from the desk's own loss catalog)

1. **Peak-earnings guard** (GARP trap #2): if the latest-year operating margin is > 90th percentile of own history, the cheap multiple is denominator-flattered — fire downgrades to REVIEW, court must normalize.
2. **Crash-cheapness guard** (GARP trap #3): if the name is currently flagged SLOW_BLEED or is a dislocation-sweep hit, the band-fire routes through the cause-check first — a falling knife entering its cheap decile is the dislocation pipeline's case, not the wishlist's.
3. **Acquisition step-up guard** (GARP trap #4): share-count or goodwill jump > 10% in the trailing year → EPS-based percentile suppressed, EV/EBIT-only.
4. **Value-trap decay:** a name that has sat in its CHEAP band > 12 months without a court ACCEPT gets a mandatory re-gate (is the multiple history still the right reference, or has the business changed regime?). The band percentile itself decays as cheap years enter the lookback — this is a feature (self-correcting reference) but must be surfaced, not silent.

## 6. Exclusions and interactions — DECISION C

- **Financials excluded from v1** (own trap catalog: ROE is peak-cycle-masked, release-flattered; the financials-screen vertical already covers them with the right tools).
- **Wash-sale surface:** the household's Parametric DI holds large-cap singles and GOOGL is a no-touch. Any wishlist name held in the Parametric account must carry a WASH-SALE flag at fire time — a wishlist buy at IBKR while Parametric harvests the same name creates exactly the interaction the household map warns about. Needs the Parametric holdings list wired in (currently not machine-readable to the desk — manual list acceptable at n≈75).
- Names already in the research ledger are excluded (they have bands/verdicts already); a wishlist name that gets courted graduates OUT of the wishlist into the ledger.

## 7. Governance and measurement (pre-registered before first fire)

- **Generator-never-grades-itself:** the wishlist proposes; every fire runs the standard conveyor (trap-verify → red → blue → adjudicate). No band-fire ever places an order directly.
- **Grading:** every band-fire logged with SPY-same-window counterfactual. Separately, the FAIR-band tranches vs CHEAP-band-only comparison is the *empirical TINA test* — n ≥ 20 fires before any claim that fair-entry beats waiting (the within-band market-timing memory says exactly this: N≥20 or it's anecdote).
- **Cohort tag:** fires inherit the cohort layer's tags, so a wishlist fire during a cohort de-rate is visibly "quality dragged with theme" vs idiosyncratic.

## 8. Cadence and cost

Weekly fundamentals/percentile refresh (XBRL companyfacts, cached); daily price-vs-band check off the existing price plumbing (~75 names is negligible against the sweeps' budgets); registry-integrated with the standard degraded-loud summary. Build size: roughly the intl-sweep effort — one module, one state file, tests.

## Decisions needed

| # | Question | Recommendation |
|---|---|---|
| A | Seed mechanically, curated, or hybrid? | Hybrid: screen → principal culls one sitting → lazy court at first fire |
| B | Two-band (FAIR tranche + CHEAP starter) or cheap-only? | Two-band — it's the TINA doctrine mechanized, and it's the only design that tests TINA empirically |
| C | Wash-sale integration: manual Parametric list, or skip names held there entirely? | Manual list + flag at fire time (skip = surrendering the best names) |
| D | Sleeve cap for wishlist-originated positions? | Propose 8% of book aggregate, standard per-name sizing via court |
