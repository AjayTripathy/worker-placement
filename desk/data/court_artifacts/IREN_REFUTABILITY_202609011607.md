## IREN — GRADE-AND-RULE (v2 refutability triage)

**Access note, stated up front:** the frozen 8/16 branch record is not reachable from this session — Bash is disabled, the repo tree outside the (empty) `court_tmp` cwd is permission-denied, and IBKR MCP is denied. SEC EDGAR returned **HTTP 403** to every direct fetch (consistent with the known full-fingerprint scraping limit). So the 10-K itself was **not** read. Everything below is company-sourced (Q4 FY26 deck + management call) via aggregators, plus exchange tape. One independent reconciliation gives me confidence in the company figures: management's "$7.6B cash, $1.7B restricted for Microsoft GPUs" nets to $5.9B unrestricted, which matches the independently-reported total cash of $5.90B exactly.

---

### 1. The frozen branch scheme, graded

Entry reconstructed as **116 @ 44.4086, filled Mon 8/17** (8/16 was a Sunday; 44.4086 sits inside the 8/17 range 43.87–46.59).

| branch | frozen p | trigger level | what the tape did | grade |
|---|---|---|---|---|
| gates pass at 8/27 print | 0.60 | *(gate text MISSING)* | split — see below | **SPLIT / partly ungradeable** |
| +10% by T+3 | 0.50 | 48.85 | max high 8/18–8/20 = **45.28** (+1.96%); never within 7% of trigger | **FALSE** |
| −10% | 0.25 | 39.97 | low 39.60 / close 39.81 on **8/24** | **TRUE** |

The +10% branch is robust to the ambiguity in the frozen text: if T+3 ran from the *catalyst* instead of entry, the window high was 38.05 (−14.3%). False either way.

**The load-bearing finding is the date on the −10% branch: it triggered 8/24 — three trading days *before* the catalyst.** The event sleeve hit its downside branch pre-event and was then carried *through* the event unhedged. That is a discipline breach independent of the P&L, and it is worth more than the mark.

**Calibration:** p=0.50 on the branch that never came within 7% of triggering, p=0.25 on the one that did. Directionally inverted. The gap in `calibration_ledger` is confirmed as a real gap — I could not locate the frozen rows, and they should be written from this grading rather than left absent.

**Why the squeeze test failed, mechanically —** and this is the reusable lesson: short interest was ~26% of shares out / ~30% of float, but **days-to-cover was 2.44** on 33–90M ADV. High SI% with low days-to-cover is *not* a squeeze setup — shorts were never trapped and could exit into the print's own volume. The premise was miscast at election.

**The 8/27 gates, on what I can verify:**
- *Business gates — PASSED.* Operating ARR $500M→$1B on Microsoft's Horizon 1 acceptance; $4B contracted ARR for 2026 capacity; 3-yr contract pricing **+125% since Nov 2025 to >$25M per IT MW** (5-yr +70% to ~$20M); mining decommissioning on schedule for end-Dec 2026.
- *Squeeze/tape gates — FAILED.* Revenue $137.2M vs $157.1M consensus (and *down* $7.6M sequentially); headline net loss $684.0M; −12.6% the next day on 89.9M shares.

The elected thesis was the squeeze test. **Its operative gate failed.**

---

### 2. Refutability triage

The narrative that fired on 8/28: *AI-datacenter capex is impairing; the neocloud trade unravels.* IREN **led** that tape (−13.2%) versus APLD −7.4%, CORZ −7.6%, WULF −7% — peers explicitly described as selling in sympathy with "no bad news of their own." So IREN's move was ~2x cohort and idiosyncratic to its own headline.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| IREN | **DAMAGE-ABSENT** (on the priced narrative) | Contract revenue per IT megawatt, and composition of the impairment | Pricing **+125% (3-yr, to >$25M/MW) and +70% (5-yr, to ~$20M/MW) since Nov 2025**; the entire $450.4M Q4 / $638.8M FY impairment is **decommissioned Bitcoin-mining hardware plus mining assets held for sale**, not AI assets ([deck](https://www.investing.com/news/company-news/iren-q4-fy26-slides-4bn-arr-contracted-amid-mining-exit-93CH-4880319), [call](https://www.fool.com/earnings/call-transcripts/2026/08/31/iren-iren-q4-2026-earnings-call-transcript/), [attribution](https://247wallst.com/investing/2026/08/28/applied-digital-sinks-7-iren-tumbles-13-as-data-center-selloff-broadens-past-one-name/)) | **~2026-11-05, UNCONFIRMED** | The market priced a mining-exit write-off as an AI-capex impairment. Rising *price* per MW is the direct refutation of the oversupply claim. **But a different damage is structural — see below.** |

**The split I will not paper over.** The narrative that moved the stock is refuted; a *second*, unpriced-that-day risk is real and correct: FY2027 capex guided **$25–30B** against ~$14B identified funding ($7.6B cash incl. $1.7B restricted, plus committed GPU financing and prepayments), $8B merely "targeted," remainder unnamed. That is ~2x enterprise value ($16.49B) to be financed in one fiscal year, against net debt $1.94B and an Altman Z of 0.98. Per response taxonomy this is a **SIZE** input, not a price gate — and it is the correct reason to be small here, which is different from the reason the stock fell.

**CROWDED gate:** ~30% of float short, 33–90M ADV, retail-heavy AI/BTC crossover — `discovery_state = CROWDED`. A one-day misreading of an impairment's composition is unlikely to persist 45 trading days to the next print in a name this watched. The dispersion is real but its half-life is short, which argues against sizing the *correction* of it as a trade.

**COURT-WORTHY (damage-absent, ranked):**
1. **IREN** — the impairment that led the cohort down is 100% legacy-mining decommissioning while AI contract pricing is up 125%, yet the funding gap ($25–30B vs ~$14B secured) is severe enough that the two readings point to opposite sizes; reconciling them is genuine court work.

**COURT-WORTHINESS IREN: 6/10** — the damage-absent read and the funding-gap read imply opposite sizing, and only a court settles which governs.

---

### PRINT PROXIMITY: ~2026-11-05 — UNCONFIRMED (yfinance-derived; no company PR names it, and sources disagree: Nov 5 vs Dec 1). Not within 5 trading days (~45 out), so no print-decisive reconstruction is owed.

One forward flag that matters more than the date: management stated December-quarter capacity "is expected to come on late in the quarter, so we will see the reported revenue effect come through predominantly in the **March** quarter." **The next print will likely look weak on reported revenue again by construction.** Anyone re-entering on the ARR story should not be re-entering on a November revenue beat.

---

### 3. RULING

**(2) Event-sleeve disposition — PROPOSE EXIT of all 116 shares.** The event resolved, the operative squeeze gate failed, and the −10% branch triggered on 8/24. I could not read the frozen action text mapped to that branch, so I am not claiming a mechanical mandate I can't cite — but the doctrine holds regardless: an event-sleeve position whose event resolved against it does not convert to a hold by inertia. Continued holding also adds to the AI-capex complex the frozen 0.45 hedge caps.

- Mark: 116 × 36.85 (9/1 close) = **$4,274.60** vs $5,151.40 cost → **−$876.80, −17.0%**.
- Tax: held 15 days → **short-term capital loss**, the most useful kind. Wash-sale bites until ~**2026-10-01**; if the AI-transition thesis is to be re-entered, either take the loss and wait out the window or accept deferral. Flagging because re-entry is plausible here.

**(3) Tranche-2 at 38.70 — VOID, explicitly.** Price (36.85–37.07) is *below* 38.70, so this zone is live and would fire by inertia if not killed. The rule voids it unless the 8/27 gates are shown PASSED at primaries: I could not reach the primaries (SEC 403), and the squeeze gate demonstrably failed. **Void it.**

**If the AI-transition case is to be owned, it is a new thesis, a new sleeve, and a new size — not an add on a broken event trade.** Its entry facts are attractive (EV/contracted-ARR ≈ 4.1x, EV/operating-ARR ≈ 16.5x) and its kill variable is named: the FY27 funding gap. That belongs in a fresh court with the funding gap as the load-bearing question, not stapled onto this one.

**Owed to the ledger (not done — I lack write access to the repo from here):** write the four graded calibration rows (gates SPLIT, +10%/T+3 FALSE, −10% TRUE-on-8/24, plus the entry record) into `calibration_ledger`, and file the reusable finding — *high short-interest-% with low days-to-cover is not a squeeze setup; require days-to-cover as a gate on any future SQUEEZE TEST election.*

**Sources:** [Q4 FY26 deck summary](https://www.investing.com/news/company-news/iren-q4-fy26-slides-4bn-arr-contracted-amid-mining-exit-93CH-4880319) · [Q4 FY26 call transcript](https://www.fool.com/earnings/call-transcripts/2026/08/31/iren-iren-q4-2026-earnings-call-transcript/) · [daily tape 8/12–9/1](https://stockanalysis.com/stocks/iren/history/) · [balance-sheet stats](https://stockanalysis.com/stocks/iren/statistics/) · [8/28 cohort attribution](https://247wallst.com/investing/2026/08/28/applied-digital-sinks-7-iren-tumbles-13-as-data-center-selloff-broadens-past-one-name/) · [pre-print short interest](https://www.benzinga.com/markets/equities/26/08/61237255/iren-stock-earnings-could-spark-a-big-move-as-short-interest-reaches-26) · [May 2026 $3.0B convert, $73.07 conv price](https://www.sec.gov/Archives/edgar/data/1878848/000114036126021285/ef20073507_ex99-1.htm) *(URL from search index; direct fetch 403)*