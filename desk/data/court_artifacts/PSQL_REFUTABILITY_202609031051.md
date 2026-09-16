Cause-check complete. Writing the triage.

---

PSQL is not a cohort-narrative casualty — it is a 5-session-old de-SPAC (closed 2026-08-27, first trade 2026-08-28) whose ~2.7M-share unredeemed float squeezed to $19.11 on debut and is now unwinding into a $12.00 triple-pivot; the quantum-cohort selloff (IONQ/RGTI/QBTS on yields) is secondary beta, not the driver.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| PSQL | **STRUCTURAL** | Commercial revenue vs. operating burn, and **net** (not gross) cash after the $312.5M convertible | FY2025 revenue **€16,468k**, grants €7,211k, other €1,907k (total €25,586k); operating loss **€79,243k**; pro forma cash **€343,758k** against non-current borrowings **€286,169k** (incl. €278,529k March-2026 Financing) → **net cash ≈ €55M**, <1yr at burn ([Ex 15.1 pro forma](https://www.sec.gov/Archives/edgar/data/2119292/000121390026096761/ea030376501ex15-1.htm)) | **2027-04-30 (est.)** — FPI 4-month rule off Dec-31 FY end, per the 20-F's own statement of its obligation; **no quarterly duty** (FPI + EGC), no confirmed interim 6-K ([20-F](https://www.sec.gov/Archives/edgar/data/2119292/000121390026096761/ea0303765-20f_pasqal.htm)) | 90.6% redemption: 26,039,602 shares out for ~$266.0M, ~$27.7M left in trust → **~2.7M public float on 212,293,691 shares (~1.3%)**. The $2.9B "market cap" is a float artifact, not a valuation. |

**Why STRUCTURAL, not damage-absent.** The narrative being sold across the cohort — cash burn, de minimis revenue, valuation detached, funding risk — is *true of this business*, and PSQL's apparent refutation is borrowed:

- **The $360M war chest is 87% debt.** The company's own closing release touts "approximately $360 million of cash available at closing" ([Ex 99.1](https://www.sec.gov/Archives/edgar/data/2119292/000121390026094393/ea030366701ex99-1.htm)). Against it sits **$312.5M principal** of senior unsecured convertible bonds, subscribed for $250.0M — a **20% original issue discount** ([20-F](https://www.sec.gov/Archives/edgar/data/2119292/000121390026096761/ea0303765-20f_pasqal.htm)). Net cash is ~$30–50M, not $360M.
- **$12.00 is a triple pivot.** It is simultaneously the convert conversion price (26,041,667 shares), the Investment Warrant strike (32,552,083 warrants), *and* the lock-up early-release trigger. Spot is $13.48 — **11% above the line**, one more red day away.
- **Dilution is entirely in the money.** 26.04M (converts) + 32.55M (Investment Warrants @ $12.00) + 17.33M (public warrants @ $11.50) = **75.93M shares, +35.8%** on the 212.29M base. Fully diluted ≈ 288.2M → **~$3.9B** at spot, ~$3.5B EV on **€16.5M** commercial revenue (**~180x**).
- **Heads-you-lose structure.** Above $12: converts convert, warrants exercise, and the lock-up releases. Below $12: $312.5M of senior debt against a €79M/yr operating loss and no sell-side coverage (**0 analysts**).

**The dated supply cliff — this is the kill.** The lock-up on the Sponsor, Legacy Pasqal holders, directors/officers and Investors terminates at the earlier of 180 days post-close (~2027-02-23) **or "the day after the date on which the closing price… equals or exceeds $12.00 per share" for "any 20 trading days within any 30-trading day period commencing after the date on which the Closing occurs"** ([8-K](https://www.sec.gov/Archives/edgar/data/2088295/000121390026023839/ea0279218-8k425_bleich2.htm)). There is **no 150-day delay** in that clause. Sessions 1–5 (Aug 28–Sep 3) all closed ≥$12. If PSQL simply holds the line, the 20th qualifying day lands **~2026-09-25**, and ~209.6M shares — **98.7% of the register** — become free. Per the value-ladder flow gate: do not bid into flow you are yourself forecasting.

**COURT-WORTHY (damage-absent, ranked):**

*None.* The one genuinely damage-absent leg is real but **undated**: commercial revenue grew **€3.5M → €16.5M** (~4.7x) in 2025 with **>€66M booked-and-awarded** as of March 2026, and 7 QPUs deployed with 3 in production — traction that does outrun several cohort members ([Ex 15.1](https://www.sec.gov/Archives/edgar/data/2119292/000121390026096761/ea030376501ex15-1.htm)). But R2.3 requires a carrying date, and the next one is **~8 months out**, behind a 36% dilution event and a full lock-up release. A metric the market cannot be forced to re-rate on before the supply arrives is not tradeable dispersion.

**COURT-WORTHINESS PSQL: 2/10** — no print until ~April 2027, price is mechanical de-SPAC discovery off a 1.3% float rather than dislocation from any external anchor, and a dated ~209M-share unlock sits ~3 weeks out; a court would change no sizing decision.

**PRINT PROXIMITY: NONE** — verified two ways: EDGAR shows no filing after the 2026-09-02 shell 20-F, and the 20-F states the company's only periodic obligation is a 20-F "within four months of the close of each fiscal year ended December 31" (→ ~2027-04-30). As an FPI and EGC, PSQL has **no quarterly reporting duty**; the pack's `NEXT PRINT: null` is correct, and the yfinance-derived date is properly UNCONFIRMED. No print within 5 trading days, so the print-decisive reconstruction is not triggered.

**PRE-PRINT POSITION: FLAT** — named kill, not a silence: the $12.00 triple pivot means both outcomes are adverse near-term (dilution + unlock above, leveraged burn below), with no earnings event to resolve it for ~8 months.

---

Two things I could not do and one I'd flag:

- **Repo reads were denied.** `knowledge_graph/cohorts.json` sits outside `court_tmp`, so the COHORT field and its narrative string stayed `?`. I reconstructed the priced narrative from the cohort tape instead (IONQ/RGTI/QBTS extending losses on yields, with focus on "cash burn, valuations, and the path to real profit"). If the stored cohort definition differs materially, the classification should be re-checked against it.
- **IBKR tools were denied** (session is non-interactive), so tape facts rest on the pack's `ibkr_gw` snapshot plus the debut prints ($16.98 open / $19.11 close / $20.10 high, ~3.7M shares) rather than my own bar pull.
- **Screen defect, OWED:** `excess_5d` and `excess_21d` are `null` because PSQL has **five trading days of history**, and its `dd52 -0.454` is measured off a 4-session-old debut spike. The velocity-dislocation screen fired on a name that structurally cannot have a dislocation — de-SPACs in price discovery will trip it every time. A minimum-trading-history guard (or a de-SPAC/`8-A12B`-within-90-days exclusion) belongs in the detector, not in the triage write-up. I did not implement it since the detector lives outside the permitted path.