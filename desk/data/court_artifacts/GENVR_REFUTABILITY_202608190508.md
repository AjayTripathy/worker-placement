Cause-check resolved before triage: GENVR is not an operating company — it is the MoneyLion-deal contingent value right, a share-settled binary on GEN's own share price. Its −21% is its anchor's −3.8% times option elasticity, so the refutability framework has no operating metric to bind to.

```
CONTEXT: GENVR = Gen Digital CVR (NASDAQ, ~12.8M units), 1 per MoneyLion share. Pays 0.7546 GEN
shares ($23.00 ÷ assumed $30.48) IF GEN's average VWAP >= $37.50 over 30 consecutive trading days
at any point before 2027-04-17, or on a change of control. GEN closed $27.64 on 2026-08-18 — the
trigger is +35.7% away. On 2026-08-17 GEN fell 3.8% to $27.41; GENVR fell 20.8%. Elasticity 5.5x
is exactly what a ~36%-OTM, ~8-month, path-dependent binary does. There is no residual to explain.
```

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| GENVR | **UNTRIAGEABLE** — instrument-class mismatch (derivative, not an operating business); derivative-correct read below is **STRUCTURAL / discount is correct** | GEN 30-consecutive-trading-day average VWAP vs the $37.50 CVR trigger (the only metric that can pay or zero this instrument) | GEN $27.64 close 2026-08-18, **−35.7% below trigger**; trend is *up* fundamentally — Q1 FY27 printed +11% revenue/bookings, +19% EPS, FY27 non-GAAP EPS guide raised to $2.87–2.97, and MS/Barclays/RBC all *raised* targets to $30–32 after the print ([Gen Q1 FY27, 10-Q 0000849399-26-000031, filed 2026-08-07](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000849399&type=10-Q); CVR terms per [Gen's completion release, 2025-04-17](https://www.prnewswire.com/news-releases/gen-completes-acquisition-of-moneylion-accelerating-the-companys-leadership-in-financial-wellness-302431174.html)) | **No issuer print of its own.** Measured continuously off the daily VWAP tape; terminal date **2027-04-17**. GEN's next print ≈ early Nov 2026 (Q2 FY27) | The −21% is mechanical delta, not a de-rate. `excess_5d` is **+11.8%** — GENVR is *up* on the 5-day window; it was not sold indiscriminately, it ran up post-print and gave part back. Cohort membership is itself wrong. |

**Implied vs fair (the only real question here):**

- Payout if triggered: 0.7546 × GEN. At exactly $37.50 → **$28.30**.
- Implied risk-neutral probability: **10.3%** at the pack's $2.91 · **12.7%** at $3.60 · **14.0%** at $3.95.
- Fair sketch: σ≈33% (GEN 52w range $17.78–31.88, two ~3.7% daily moves last week), T_eff≈0.58y (166 trading days to expiry, less the 30-day averaging window → the run must *begin* by ~2027-03-05). Terminal N(d2) ≈ **9.9%**; path/averaging uplift 1.3–1.7× → **13–17%**, i.e. FV ≈ **$3.75–4.90**.
- Verdict: implied (10–14%) and fair (13–17%) **overlap**. Per anchor-and-adjust, no deviation with a mechanism behind it. No confirmed edge.

**COURT-WORTHY (damage-absent, ranked):** *none.* No member qualifies. GENVR has no damage to be absent — its decline is fully accounted for by its external anchor (GEN), which is the taxonomy's test for whether a mispricing is real. The one datum that could still make it court-worthy — GEN's listed Jan-2027/Dec-2027 $35–40 call surface, the clean external anchor for the same event — I could not retrieve: IBKR `search_contracts`/`get_price_snapshot` were permission-denied this session, and Barchart/MarketBeat returned no strike-level values. That gap is stated, not papered over; it is retrievable in one call if IBKR access is granted.

**COURT-WORTHINESS GENVR: 2/10** — a court cannot change sizing on a ~$105K/day-notional stub whose move is fully explained by its anchor and whose exposure is available more cheaply and liquidly in GEN listed calls.

**PRINT PROXIMITY: NONE — verified from the pack's own filing index.** Gen printed Q1 FY2027 on 2026-08-06 (8-K `0000849399-26-000028`) with the 10-Q on 2026-08-07 (`0000849399-26-000031`); the next print is Q2 FY27 in early Nov 2026, well beyond 5 trading days. The CVR itself has no print — it is marked continuously off GEN's VWAP tape to 2027-04-17. No pre-print reconstruction is owed. **Position: FLAT** — the instrument is inside its own fair band, and at 28,762 shares average daily volume the ≤1%-ADV rule caps participation near $1K/day, which cannot move a sizing decision at any scale we operate.

---

**Data-integrity flags — these should go back to the pipeline, not into a court:**

1. **`px` is contradicted.** Pack says $2.91 (internally consistent: `dd52` −75.7% and `pct_off_low` 7.244 both reconcile to $2.906). Yahoo — the pack's *own* named source — returns last $3.60, prior close $3.95, day range $3.25–3.88. I could not break the tie: every independent GENVR quote source 403'd, 404'd, or timed out. The verdict above holds under either price, but a court that sized off an unverified tape would be invalid.
2. **`mcap` is off by ~34×.** ~12.8M CVRs × ~$3.95 ≈ **$50M**, not the $1,705,973,041 in the event JSON. Looks like GEN/MoneyLion entity data joined onto the CVR ticker.
3. **XBRL `rev` rows are decade-stale.** $1.43–1.72B/qtr dated 2010-01-01 through 2012-06-29 — Symantec-era tags, higher than GEN's current ~$1.27B/qtr run-rate. Anyone flooring off those gets the sign of growth backwards. `sbc`/`dil_sh`/`ocf` are current-ish but are GEN-level and irrelevant to a CVR.
4. **Template mismatch.** `sector: "Technology"` and the operating-company refutability template were applied to a derivative. The screen should exclude CVR/warrant/right/unit tickers from velocity-dislocation cohorts, or route them to an option-elasticity check instead — a 5.5× move in a 36%-OTM binary off a 3.8% underlying move will trip a `1d -21%` trigger indefinitely.

Sources: [Gen completion release / CVR terms (PRNewswire, 2025-04-17)](https://www.prnewswire.com/news-releases/gen-completes-acquisition-of-moneylion-accelerating-the-companys-leadership-in-financial-wellness-302431174.html) · [Gen Digital S-4 (SEC)](https://www.sec.gov/Archives/edgar/data/849399/000114036125002752/ny20039778x6_s4.htm) · [MoneyLion DEFM14A (SEC)](https://www.sec.gov/Archives/edgar/data/1807846/000114036125007220/ny20041772x1_defm14a.htm) · [GEN quote & guidance (stockanalysis.com)](https://stockanalysis.com/stocks/gen/) · [GEN −3.8% on 2026-08-17 (GuruFocus)](https://www.gurufocus.com/news/9039519/gen-digital-inc-gen-stock-down-38-now-undervalued-gf-score-86100) · [GENVR quote (Yahoo Finance)](https://finance.yahoo.com/quote/GENVR/)