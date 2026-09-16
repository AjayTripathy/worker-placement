# FDXF — FedEx Freight Holding Company, Inc.
**Court:** court_queue_20260804, TIER_4 spinoffs · **Date:** 2026-08-03 (grades for the 08-04 session)
**Live:** $139.02 (2026-08-03 close, IBKR ctr 884688186 NYSE, `is_close: true`)
**Queue label:** FORCED_BUY_INVERTED, LATE_WINDOW, dist 2026-05-27
**Prior house note:** *"still dumping −25.6% at 67d, knife, revisit on base"*

## VERDICT: 3/10 — AVOID at spot. Re-open band $100–112.
Not a flow trade in either direction. The mechanical index flow was ~NULL, the real supply is a
19.9% parent retained stake, and the drawdown is a fundamental re-rate whose bridge is being
contradicted in real time by the peer tape.

---

## 1. TAPE VERIFICATION — the house premise was built on when-issued prints

| Claim | Method / source | Result | Finding |
|---|---|---|---|
| Distribution date 2026-05-27 | FDXF 8-K acc. 0001104659-26-068521 Item 5.01; FDX 8-K 0001104659-26-068519 Item 2.01 | "Effective as of 12:01 a.m., Central Time, on **June 1, 2026**… FedEx completed the Spin-Off" | **REFUTED.** Real date = 2026-06-01 |
| First bars 05-27/28/29 are regular way | FedEx PR 05-13-2026 (EX-99.4 to 8-K 0001104659-26-060223) | "Beginning May 27, 2026 and ending at the close of business on May 29, 2026… a **'when-issued'** market… under the symbol **'FDXF WI'**" | **REFUTED.** Three when-issued bars |
| Early high $185 / drawdown −25.6% | IBKR daily bars | 05-28 bar: **3,268 shares**, high $200.00, close $185.00 | **REFUTED as a price premise.** This is the ADIG 379-share trap repeated |
| Regular-way series | IBKR bars from 06-01 | 06-01 vol **3,621,851**, O 164.00 / C 149.53 | CONFIRMED as the clean start |

**Corrected path (regular way only):** start $149.53 (06-01) → real high close **$188.46** (06-09) →
low close **$137.55** (07-30), intraday low $135.64 → **$139.02** (08-03).
- True drawdown from the regular-way high: **−26.2%** (not −25.6% from a 3,268-share print — the
  house number was right by coincidence, wrong by construction).
- **Days since distribution = 63** (not 67). LATE_WINDOW confirmed; window closes ~2026-08-30.
- Off the low: **+1.1%**, low is **2 sessions old**. This is not a base. It is a name still at its low.

---

## 2. FLOW SIGN — the queue label is wrong, and the real supply is elsewhere

**Index placement (verified as far as reachable):** FDXF joined the **S&P 500** and replaced American
Airlines in the **Dow Jones Transportation Average**, effective 06-01-2026. Primary issuer statement:
FDXF completion press release, EX-99.1 to 8-K 0001104659-26-068521 — *"It has been announced that
FedEx Freight will join leading global equity indices, including the S&P 500 and the Dow Jones
Transportation Average."* S&P DJI's own announcement page returns **HTTP 403** even with a full
Chrome fingerprint → the S&P primary is **UNVERIFIED**; the constituent FDXF replaced in the S&P 500
is unknown.

**Mechanism correction (doctrine).** "FORCED_BUY_INVERTED" names the wrong mechanism. FDX was already
in the S&P 500; S&P 500 index funds **received FDXF in kind at exactly index weight** and were
required to buy nothing. The mechanical S&P flow is **NULL, not a forced buy**. The only genuine
forced buying was DJTA trackers replacing AAL — a rounding error against a $20.8B cap.

**The real flow fact the generator missed entirely — a 19.9% parent overhang:**
- FedEx distributed only **80.1%** and **retained up to 19.9% (~30M shares)**.
  Source: Form 10 information statement (EX-99.1 to 8-K 0001104659-26-060223), "When and How You Will
  Receive Our Shares"; reconfirmed in the 06-01 completion press release.
- **"FedEx must generally dispose of the retained shares within 24 months of the completion of the
  Spin-Off"** — i.e. by ~2026-06-01 + 24m = **June 2028** — *"through one or more subsequent exchanges
  of shares of our common stock in repayment of certain FedEx debt held by FedEx creditors and/or
  through distributions… as dividends or in exchange for outstanding shares of FedEx common stock."*
- Size: 30M shares ≈ **$4.17B at $139.02**. Recent FDXF ADV ≈ 500k shares ≈ $70M/day →
  **~59 trading days of ADV** of committed future supply.
- FDXF's own guidance share count (149.5M) is explicitly stated to **include** the 30M retained shares.
- Mechanically this arrives as a **discrete debt-for-equity block or split-off exchange offer**, not a
  daily drip. It is a dateable, single-name supply event with a hard 24-month clock — and a split-off
  exchange offer would be priced at a **discount to market** to attract FDX holders.

**Net flow sign: negative, and it has not happened yet.** The right posture is to be a buyer *of* the
overhang event, not a buyer *before* it.

---

## 3. CAPITAL STRUCTURE LOADED AT SEPARATION (all CONFIRMED)

| Item | Value | Source |
|---|---|---|
| Shares outstanding | 148,906,159 pro forma; **149.5M** per guidance (incl. 30M FedEx-retained) | Form 10 Capitalization; Q4 FY26 release |
| Senior unsecured notes | **$3.70B**: $1.0B 4.300% '29 · $1.0B 4.650% '31 · $0.7B 4.950% '33 · $1.0B 5.250% '36 (issued 02-05-2026, 144A) | FDX 8-K 0001104659-26-011069 Item 8.01; Description of Certain Indebtedness |
| Term loan | **$600M** 3-yr delayed-draw, **fully drawn 2026-05-27** | FDXF 8-K 06-01, Item 2.03 |
| **Total debt** | **$4.264B**, weighted-average **4.79%** | Form 10 pro forma |
| Revolver | $1.2B five-year, **undrawn**; $50M LC sub-facility | ibid. |
| Cash | **$250M** pro forma | Form 10 Capitalization |
| **Cash dividend paid TO FedEx** | **~$4.1 billion**, pre-Effective-Time, funded by the notes + term loan | FDXF 8-K 06-01 Item 8.01; FedEx PR 05-13 |
| **Total equity** | **$(562)M — negative** | Form 10 pro forma |
| Deferred tax liabilities | $318M (+$111M at separation) | ibid. |
| Operating leases | $178M current + $1,289M long-term ≈ **$1.47B** | ibid. |
| Pension | Multiemployer historically; only **active-employee** obligations transfer, inactive retained by FedEx; management estimated a net benefit-plan **asset** transfers | Form 10; actual transferred amounts **UNVERIFIED** |
| Self-insurance | FedEx **retains** substantially all WC / vehicle / property reserves; FDXF's higher standalone deductibles = **+$63M FY25 / +$32M 9M-FY26** expense; +$393M retained-earnings adjustment | Form 10 |

**Standalone cost load — a disclosure gap, not a clean number.** There is **no dollar estimate of
incremental annual standalone public-company costs anywhere in the Form 10.** The pro formas carry an
"Autonomous Entity Adjustments" column that is **$0 on every line**, on the assertion that *"the costs
to be incurred under the Transition Services Agreement are not expected to exceed the amounts
historically recorded… Therefore, no adjustment is made to pro forma net income."* The only quantified
drags are self-insurance (+$63M), transferred employee obligations (+$29M FY25), and the deck's
**−120bps TSA** line in the TY26 bridge. **A zero autonomous-entity adjustment on a $8.8B carve-out is
an assumption, not a measurement.** UNVERIFIABLE ≠ clean.

**Parent entanglement:** TSA effective 05-31-2026, term *"generally no longer than two years"* (→ ~June
2028); trademark licence for the "FedEx Freight" name, **5-year initial term** auto-renewing in 1-year
increments up to 5 more, terminable by Federal Express on **change of control of FedEx Freight** — i.e.
an acquirer loses the brand. Commercial agreements (LTL↔parcel network) were **never filed as exhibits
and no term/volume/pricing is disclosed — UNVERIFIED**. Sizing relief: FedEx-related revenue was only
**$171M in FY25 = 1.9% of revenue**, and it flows *to* FDXF.

---

## 4. THE BUSINESS — and the honesty finding

**FedEx segment basis (FDX's own reported segment; $M):**

| | FY2024 | FY2025 | FY2026 |
|---|---|---|---|
| Revenue | 9,429 | 8,892 | **8,795 (−1.1%)** |
| Operating income | 1,821 | 1,489 | **616 (−58.6%)** |
| Operating ratio | **80.7%** | **83.3%** | **93.0%** |
| Adjusted operating income | — | — | **1,108 (−25.6%)** |
| **Adjusted operating ratio** | | | **87.4%** |
| Avg daily shipments (000) | 94.0 | 90.1 | **86.1 (−4.4%)** |

Volumes have fallen four consecutive years: **99.7k/day FY23 → 86.1k FY26, −13.6%.** Q3 FY26 (quarter
ended 02-28-2026) was an outright **operating loss of $(6)M** on the carve-out basis.

### The takeaway diverges from the issuer's own data — twice, in one release
Source: FDXF Q4 FY26 press release, EX-99.1 to 8-K 0001628280-26-045515, 06-25-2026.

1. **"Revenue was $2.4 billion, a 4.8% increase"** — while **average daily shipments fell 5.9%.** The
   release itself attributes the increase to *"the favorable impact of fuel surcharges and higher
   weight per shipment"* with *"lower volumes and a slight decline in base revenue per hundredweight."*
   The marketed top line is fuel and mix; the volume line is negative. Reuters propagated the headline
   ("FedEx Freight forecasts up to 6% revenue growth").
2. **"Operating margin of 9.0% to 9.5% compared to 7.8%"** is guided alongside
   **"adjusted operating margin of 11.5% to 12.0% compared to 11.8%."** The GAAP "expansion" is
   entirely the non-recurrence of $130M of spin costs. On the **comparable** measure the company is
   guiding **flat to 30bps DOWN.** The company's own bridge (investor deck slide 8) confirms it:
   11.8% → ~11.8%, built from Net Yield **+200bps**, Efficiency **+80bps**, Variable Comp **−130bps**,
   **TSA −120bps**, Net Volume **−30bps**.

This is takeaway-vs-data divergence on disclosed data — the numbers are all in the release. It is not
fraud; it is framing. But it means **year one of the standalone plan delivers zero adjusted margin
improvement**, which is not what the sell-side story says.

### The bridge's biggest plank is being contradicted on the tape right now
The +200bps **Net Yield** line is over half the positive bridge. Peer Q2 CY26 primary filings:

| Carrier | Volume | Yield | Margin |
|---|---|---|---|
| ODFL (8-K 07-29, acc. 0000878927-26-000021) | shipments/day **−5.7%**, tons/day −4.1% | rev/cwt +15.2%, **ex-fuel +5.5%** | OR **70.1%** vs 74.6% |
| SAIA (8-K 07-30, acc. 0001193125-26-324937) | shipments/day **+4.4%**, tonnage/day +8.4% | **rev/cwt ex-fuel −2.2%** | OR **86.9%** vs 87.8% |
| XPO (8-K 07-30, acc. 0001104659-26-088438) | — | — | NA LTL OI **+43.2%** |
| ArcBest (8-K 07-29, acc. 0001104659-26-087722) | shipments/day **−2.8%**, tons +4.9% | billed rev/shipment +12.5% | impairment + restructuring plan announced 07-16 |

Read: the LTL market is in a **price-for-volume share war**. SAIA bought +8.4% tonnage with the first
**negative ex-fuel yield print** of the cycle; ODFL held price and gave up 5.7% of shipments. ArcBest
announced a restructuring. Layer on **Amazon's nationwide LTL expansion** (the whole group fell on it
06-10-2026). A carrier guiding **+200bps of net yield** into a market where the #2 growth carrier just
printed **−2.2% ex-fuel yield** is the fragile pillar of this thesis.

**I must correct my own first read:** I initially attributed the FDXF July slide to an LTL demand
break. The primary prints refute that — ODFL, SAIA and XPO all **expanded** margins in Q2 CY26. The
group de-rated on **price**, not demand. FDXF is the only one of the five whose margin collapsed, and
the collapse is mostly spin costs. The correct bear is pricing, not volume.

---

## 5. VALUATION (cap structure loaded first, per house rule)

- Market cap = 149.5M × $139.02 = **$20.78B**
- Net debt = $4.264B − $0.250B = **$4.014B** → **EV = $24.80B** (incl. $1.47B operating leases: $26.3B)
- FY26 adjusted operating income $1,108M → **EV/adj-EBIT = 22.4x**
- TY26 guide annualized: adj OI $605–645M × 12/7 = **$1.04–1.11B** → *zero growth in year one*
- EPS: TY26 $2.40–2.60 ex-spin-cost (7 months) → annualized **$4.11–4.46** → **P/E 31–34x**
- Form 10 **pro forma FY25 EPS was $6.06** — current run-rate EPS is **~28% below** the pro forma base
- Gross leverage $4.264B / ~$1.66B adj EBITDA ≈ **2.57x**; target ~2.5x within 12m — already there

**Peer check (live 08-03 closes):** ODFL $211.52 → ~26x EV/EBIT (OR 70.1). SAIA $360.10 → ~21x
(OR 86.9). **FDXF at 22.4x with an 87.4 adjusted OR is priced in line with SAIA, its true OR peer.**
It is *not* cheap; it is *fair-to-full* in a group that may itself be too expensive.

### Scenarios
| | p | Path | FV |
|---|---|---|---|
| **Bear** | 0.30 | Yield bridge fails in the price war; adj margin to ~10% (adj OI ~$880M); sector multiple compresses to 17x; overhang block prices at a discount | **$73** |
| **Base** | 0.45 | TY26 delivered as guided (adj margin ~11.8%, adj OI ~$1.10B); 21x peer-in-line | **$128** |
| **Bull** | 0.25 | Deck slide 28 executed — adj margin to ~15% on 5% revenue CAGR by CY28 ($1.53B adj OI), 21x, discounted 2y @10% | **$155** |

**E[FV] = $118.25 vs $139.02 → edge = −15.0%.** Negative edge. This is not a "wait," it is an avoid.

---

## 6. FOUR-IDEA FRAME
1. **Consensus:** *the most compelling story in LTL* (Jefferies Buy PT $200, 06-23; BofA/RJ/Wolfe/
   Evercore/GS Buy). Largest NA LTL carrier, worst OR in the group = biggest self-help runway;
   87.4 → 85 → "15% margin" is $400M+ of found operating income.
2. **Our variant:** the self-help is real and the runway is real, but **year one delivers none of it**
   by the company's own bridge, and the bridge's dominant plank (+200bps yield) is the exact line the
   sector just repriced. You are paid nothing to wait and you carry a 59-days-of-ADV parent overhang.
3. **The bear:** LTL price war + Amazon capacity + a levered ($4.26B debt, negative equity, $4.1B
   dividended out) carrier with **no independent operating history**, no quantified dis-synergy
   estimate, unfiled commercial agreements, and a brand licence that dies on change of control.
4. **What would change our mind:** (a) the FedEx retained-stake block prints and clears — buy the
   discount, not the anticipation; (b) an ex-fuel yield print ≥ +3% at FDXF or ODFL confirming pricing
   held; (c) the mid-August 10-K recast showing the carve-out CY-basis margin above the segment basis.

---

## 7. CATALYST MAP (probability × timing × magnitude)

| Catalyst | Date | p | Magnitude | Notes |
|---|---|---|---|---|
| **FY26 Form 10-K + recast CY24/CY25 carve-out financials** | **by mid-Aug 2026** (deck slide 10) | 0.85 filed on time | ±3–6% | Re-bases every model; carve-out OR (84.2% FY25) ≠ segment OR (83.3%) — expect a reconciliation discontinuity |
| CFO Marshall Witt fireside, Deutsche Bank Chicago Industrials Summit | **2026-08-11, 1:00pm CDT** | 0.95 occurs | ±2–4% | First unscripted standalone commentary; yield-trend question is the whole thesis |
| **First TY26 earnings** (3- and 4-month periods ending 09-30) | **late Oct 2026** | 0.90 | ±8–15% | ⚠️ NOT "fiscal Q1 FY27 ending 08-31" — the fiscal year changed to Dec-31 |
| FedEx retained-stake disposal (debt-for-equity block or split-off exchange offer) | anytime → hard stop **June 2028** | 0.90 by mid-2027 | −5 to −12% on announce, then clears | The single largest identifiable supply event |
| Peer prints (ODFL monthly metrics, SAIA/XPO Q3) | Sept–Oct | 0.99 | ±3–8% sympathy | ODFL publishes **monthly** operating metrics in an 8-K — the cheapest leading yield read |

**No print inside two weeks** — FDXF is the only name in this batch clear of the pre-print gate. But the
10-K recast and the 08-11 fireside both land inside 8 days, so "clear of a gate" ≠ "clear to act."

---

## 8. KILL / RE-OPEN TRIGGERS
- **Re-open band: $100–112.** Below $112 the base case ($128) carries a >12% margin of safety; below
  $100 the bear is more than priced. Expires 2026-11-30 (after the late-Oct TY26 print).
- **Kill the re-open entirely** if: FDXF prints ex-fuel revenue/cwt **negative** in any period (the
  +200bps yield bridge is then dead), **or** TY26 adjusted operating margin guidance is cut below 11.0%,
  **or** the retained-stake block is placed at a >8% discount and the stock does not recover the
  discount within 10 sessions (signals no natural bid).
- **Kill the bull leg** if adjusted OR is not below 86.5% by the CY26 full-year print.
- **Do not buy the overhang in anticipation.** Buy it only after the block prices.

## 9. FREEZABLE CALL
`FDXF | 2026-10-31 | TY26 (Jun 1–Dec 31, 2026) adjusted operating margin guidance is REAFFIRMED at
≥11.5% at the late-October print (not cut) | our_p = 0.45`
Rationale for a sub-coin-flip: the +200bps net-yield plank is the largest single item in a bridge that
already nets to flat, and the peer tape just printed negative ex-fuel yield at SAIA.

## 10. VERIFICATION NOTES — what is NOT verified
1. **S&P DJI primary announcement — UNVERIFIED.** spglobal.com/spdji returns HTTP 403 on every path,
   including with the full Chrome fingerprint (UA + Sec-Ch-Ua + Sec-Fetch-* + Referer). Index placement
   rests on the issuer's own press release plus news secondaries. The S&P 500 constituent FDXF replaced
   is unknown.
2. **Standalone dis-synergy — NOT DISCLOSED.** $0 autonomous-entity adjustment across the pro formas.
   This is the largest single unquantified item in the model.
3. **Commercial agreements with FedEx — never filed, no term/volume/pricing disclosed.**
4. **Pension amounts actually transferred — UNVERIFIED** (measured at legal-transfer date).
5. Sell-side ratings/PTs above are **headline-derived from Google News RSS**, not read from research
   notes. They are not a consensus and no consensus EPS was used in this court.
6. Deck slide 30 mislabels the senior **unsecured** notes as "Secured Notes." Filings control; noted as
   a disclosure-quality datum, not a finding.

## 11. DOCTRINE OUTPUT (for the generator)
- `spin_index_inkind_flow_null` — when parent and spinco are both in the same index family, index funds
  receive the spinco **in kind at index weight** and are forced to buy nothing. "FORCED_BUY_INVERTED"
  should be renamed **FLOW_NULL_SAME_INDEX**. The label's *conclusion* (no orphan washout) is right;
  its *mechanism* (forced buyers) is wrong, and the wrong mechanism invites the wrong trade.
- `retained_stake_overhang` — a spin distributing **<100%** creates a dated, sizeable forced seller that
  dominates any index effect. Parse "at least 80.1% / retaining up to 19.9%" and the 24-month tax
  disposal clock out of the Form 10; express it in **days of ADV**. The generator missed this on FDXF.
- `when_issued_window_from_pr` — the when-issued window is stated verbatim in the parent's spin-approval
  press release ("beginning May 27… ending at the close of business May 29… symbol FDXF WI"). Parse it
  rather than inferring the distribution date from the first traded bar.
