# ACSO — accesso Technology Group plc (AIM: ACSO, GB0001771426)
**Court: lse_shelf_20260804 · 2026-08-04 · verdict 3/10 REJECT (value entry) — screen artifact, not a discount**

---

## 0. THE TENDER CHECK (mandated first, and it is decisive — but not the way the shelf feared)

| Question | Method / authority | Result |
|---|---|---|
| Is accesso in a Takeover Code offer period? | `LSE_OFFER_PERIODS.json` (39 issuers, sourced from thetakeoverpanel.org.uk disclosure table, generated 2026-08-04T17:20Z) — searched ISIN GB0001771426 | **NOT PRESENT — no offer period.** CONFIRMED |
| Cross-check via announcements | Full RNS index, investegate.co.uk/company/ACSO, Jan–Aug 2026 | **No Rule 2.4, 2.7, or any offer-related announcement.** CONFIRMED |
| What is the IBKR `ACSO.TEN` line? | RNS "Completion of Tender Offer & Total Voting Rights", 18-Mar-2026 | **A COMPLETED ISSUER SELF-TENDER (buyback), not a takeover.** Deutsche Numis purchased **4,833,333 shares at a fixed £3.00**, ≈**£14.5m** returned, shares cancelled. CONFIRMED |
| Resulting share count | Same RNS, Rule 5.6.1 Total Voting Rights statement | **33,282,874 ordinary shares**, no treasury shares. CONFIRMED |

**Ruling on the mandated question: there is NO live tender and NO offer period. This is a value court, not a special-sit court.**

But the `.TEN` line was still the right thread to pull, because the completed tender **invalidates the share count the whole shelf row is built on** (see §2). And a *different* special-situation element turned out to be present that the shelf never saw — §1.

---

## 1. MODE B FIRST — what the framing hid: the 5-Jun-2026 gap is a Constellation Software toehold

The shelf hands over a static row. The tape does not agree with a static story.

**Tape (yfinance ACSO.L daily, GBp, cross-checked against IBKR bars):**

| Date | Close | Volume | Note |
|---|---|---|---|
| 2026-06-04 | 261.5p | 36,096 | |
| **2026-06-05** | **319.0p** | **632,325** | **+22.0% in one session on ~10x median volume; high 333.7p** |
| 2026-06-08 | 321.0p | 126,932 | holds the gap |
| … two months … | 315–330p | | never fills the gap |
| 2026-08-03 | 315.0p | 187,600 | H1 update + IT incident |
| 2026-08-04 | 307.0p | 42,262 | live 306.5p, −2.7% |

*Unit discipline (priceMagnifier rule): IBKR `get_price_history` returns this line in **GBP** (3.094), `get_price_snapshot` in **GBp** (306.5). Both were pulled and reconciled; all figures below are GBp unless stated.*

**Cause of the gap — CONFIRMED from the primary document.** The only accesso RNS on 5-Jun-2026 (07:00) was "Holding(s) in Company". Its content:

> **Constellation Software Inc.** (Toronto), TR-1 notification, threshold crossed **03/06/2026**, issuer notified 04/06/2026 — **3.1628% of voting rights, 1,052,662 shares**, direct, no financial instruments, not controlled by any other entity.

That is the single most disciplined vertical-market-software acquirer in the world appearing on the register of a $137m-cap vertical-market-software company. The market re-rated it 22% in one session and has held that level for two months.

**What this means for the entry — and it is the whole point:**

- **~22% of today's price is unconfirmed-bid speculation.** The pre-CSU clearing price was ~262p. You are being asked to pay 306.5p.
- **Constellation itself bought at ~260p**, not at 306p. The best capital allocator in the sector validated a price **15% below the market**. Following them here means paying 18% more than they did.
- **No escalation in two months.** DTR5 thresholds on AIM require notification at 3% then each 1%. There has been **no 4% notification** — CSU has sat between 3% and 4% since 3-Jun. CSU is famously patient and essentially never launches hostile public bids; a 3% toehold is an option, not a process.
- The shelf's `sector_takeout_heat: 4` / `pe_bid_sector: true` flags were pointing at something real — they just could not see *what*.

**This is the finding the value framing hid: the name is not cheap *and* holding a bid option — the "cheapness" is a stale-input artifact (§2) and the 22% premium is the bid option, already paid for.**

---

## 2. MODE A — the three headline claims, verified against primaries. All three fail.

| # | Claim (shelf row / intake) | Method + authority | Finding |
|---|---|---|---|
| 1 | **"8.5x EV/EBIT"** (`am` 8.517) | Recomputed. Shelf uses `share_counts.filing` = 36,880,399 and 31-Dec-25 cash. Authoritative count = **33,282,874** (TVR RNS 18-Mar-26). Live 306.5p, GBPUSD 1.3444 (yfinance 2026-08-04) | **REFUTED as stated.** Mktcap = 33.283m × £3.065 = £102.0m = **$137.1m**, not $152.2m (shelf **+11% too high**). But cash is also overstated (row 3), and the two errors partly offset → **EV/EBIT ≈ 9.0x on FY25 EBIT, ≈11.0x on FY26E EBIT.** Not 8.5x. |
| 2 | **"below book", P/B 0.78** | FY25 Final Results (RNS 30-Mar-2026), consolidated statement of financial position + Note 12 | **REFUTED — textbook CAPD-class artifact.** Net assets $196,125k. **Intangible assets $163,442k, of which GOODWILL $139,433k.** Tangible book = **$32.7m** pre-tender; after the £14.5m tender (~$18.7m) and Dexibit (goodwill-additive) it is **~$7m, i.e. ≈zero**. "Below book" for an asset-light software rollup is a statement about goodwill, not about value. **P/TBV is not <1; it is effectively unmeasurable/enormous.** |
| 3 | **"net cash, 19.3% of cap"** ($29.3m) | Balance sheet is **31-Dec-2025**. Two large cash events happened AFTER it | **REFUTED as of today.** Walk: $30.5m (company-defined net cash, FY25) − **£14.5m tender ≈ $18.7m** (18-Mar-26) − **$7.1m Dexibit initial cash** (28-Mar-26, "funded through existing cash reserves"; + up to $5.0m earnout over 3 yrs) + H1-26 generation (est. +$2–8m) ⇒ **≈$6–13m, call it ~$8m ≈ 6% of cap, not 19%.** |

**Supporting verified facts (FY25 Final Results, 30-Mar-2026):**
- Revenue **$155,105k** (+1.8%; **+0.9% constant currency**) · Cash EBITDA **$23,019k** (+0.8%) · Statutory PBT **$14,321k** (+37.7%) · Net cash **$30,498k** · Adjusted basic EPS 44.26c, basic EPS 27.96c.
- Borrowings: bank loans $11,322k gross, against a **$40.0m HSBC RCF to May-2027** (secured, fixed and floating charges). Lease liabilities $1,159k excluded from the company's net-cash definition — a definitional choice, disclosed.
- FY25 buybacks $15,911k + $4,053k into the EBT; $4.0m 1RISK IP purchase.

**Cap-structure check (mandated before any net-cash/EV claim):** ordinary shares only — 33,282,874, no treasury, no preference shares, no convertibles, no warrants found in the FY25 equity note. "Own shares held in trust" $8,447k is an EBT reserve (share-based-payment settlement), not a separate claim. Contingent claim: **up to $5.0m Dexibit earnout** over three years. Clean.

---

## 3. CAUSE-CHECK — why is it here? Two major customers, one software solution.

This is the part the shelf could not see at all, and it is not a multiple story.

| Date | Event (primary: RNS) | Consequence |
|---|---|---|
| Jul-2025 | Group announces a product used by **a major customer** not expected to continue beyond end-2025 | De-rate begins from the 52w high **451p** |
| **5-Jan-2026** | "Trading Update": that customer **will** continue, one year only, **on revised commercial terms**. Separately, **another major customer will NOT renew its agreement for the SAME software solution** beyond expiry **31-Jan-2026** | The core-product franchise question opens |
| **29-Jan-2026** | Confirms the non-renewal. Sets FY26 guidance. Announces the £14.5m tender at £3.00 | Guidance: **revenue ~$146m, Cash EBITDA ~$20.0m** |
| 30-Mar-2026 | FY25 results; Dexibit acquired ($7.1m + $5.0m earnout) | Goodwill grows into a shrinking P&L |
| 1-May-2026 | CEO succession: Steve Brown → **Lee Cowie** | New management, "accelerating AI strategy" |
| 3-Jun-2026 | **Constellation Software crosses 3%** | +22% gap (§1) |
| **3-Aug-2026** | H1 trading update **in line**, FY26 guidance **reaffirmed**; separate **Notice of IT Security Incident** | −2.7% on 4-Aug |

**The arithmetic of the guide:** FY25 $155.1m → **FY26 ~$146m = −5.9% revenue**. FY25 Cash EBITDA $23.0m → **FY26 ~$20.0m = −13.1%.**

**RULING: DERAILMENT, not de-rate.** The contract's winner pattern is a multiple compressing against *stable or rising* estimates. Here the multiple compressed *because* the estimates fell, and they fell for a franchise reason — the loss of one major customer and the repricing-downward of another **on the same core software solution**. The shelf's `ebit_vs_peak: 1.00` ("EBIT at its own peak") is true only because it is reading the FY25 print; the *forward* number is guided down double digits. This is precisely the trailing-anchor failure mode.

**Undisclosed-customer note (whale channel).** accesso will not name either customer. The customs-BOL shipper-alias route that resolves undisclosed whales does not reach a pure-software vendor — no physical shipments — so the connector's normal method is inapplicable here (a known blind spot, stated rather than papered over). The circumstantial fit is the Six Flags / Cedar Fair merger (completed Jul-2024) consolidating two legacy virtual-queuing contracts onto one vendor, which would explain "two major customers … for the same software solution" with one exiting on a fixed contractual expiry. **This is PLAUSIBLE, not CONFIRMED, and nothing in this verdict rests on it.**

---

## 4. What is genuinely GOOD here (anti-masking — absence of masking is itself a finding)

The corrected numbers are much worse than the shelf's. **The company is not the reason.** accesso's own disclosure is, on the evidence, honest:

- **Conservative capitalisation.** "Capitalised development expenditure of **$3.1m** … represents **6.7%** of total development expenditure." accesso expenses ~93% of R&D. Most listed software peers capitalise 30–50%. This is the opposite of the usual software flattery, and it means the shelf's FCF figure is *not* inflated by capitalisation games.
- **Cash EBITDA is defined against the company's own interest** — explicitly *less* capitalised development costs. A vanity metric would add it back.
- **Bad news was pre-announced early and repeatedly** (Jul-25, 5-Jan-26, 29-Jan-26), each time flagged as inside information under MAR, before the numbers forced it.
- **The IT incident was disclosed the day it was characterised**, with the board's risk assessment stated ("low") and the investigation openly described as ongoing.
- Capital returns are real and priced sensibly: 7% of share capital bought back, then a £3.00 tender — struck within 2% of today's price.

**Honesty grade: CLEAN.** The marketed takeaway does not diverge from the data. **The divergence is entirely between the SCREEN's takeaway and the data.** That distinction matters: this is a data-quality catch, not a management-integrity catch, and it should not be logged as the latter.

---

## 5. The live overhang: IT security incident (3-Aug-2026)

Verified from the RNS text: temporary unauthorised access to a limited part of the Group's systems; contained; no downtime or major disruption; incident response plan enacted; external specialists engaged; **the accessed systems "contained internal information relating to the Group's own business operations"**; no suspicious activity since; **board assesses risk of financial exposure as low**; customers and relevant authorities notified; **investigation remains ongoing.**

Read straight: this is the good version of a breach notice — internal data, not a customer-payment-card compromise. **But it cannot be graded clean yet.** Three reasons: (i) the investigation is open and initial scoping of breaches routinely widens; (ii) accesso is a ticketing/POS/payments processor for 1,100 venues and is **launching accessoPay this month**, so a security event lands on the exact asset the new strategy depends on; (iii) the phrase "internal information relating to the Group's own business operations" is a scope statement made 0–few days in.

**UNVERIFIABLE ≠ clean.** Carry it as an open tail into the 15-Sep interims.

---

## 6. Valuation — corrected, three scenarios

Basis: 33,282,874 shares · live **306.5p** (IBKR snapshot, GBp, 2026-08-04) · GBPUSD **1.3444** · mktcap **$137.1m** · est. net cash **~$8m** · **EV ≈ $129m**.

Cash EBITDA → EBIT bridge (FY25 actual): Cash EBITDA $23.0m − D&A/SBC/acquisition costs net of the capdev add-back ≈ $8.3m → EBIT ≈ $14.7m (ties to statutory PBT $14.3m + net interest). Applying the same bridge to FY26 guidance: **FY26E EBIT ≈ $11.7m**.

| Multiple | Shelf said | **Corrected** |
|---|---|---|
| EV/EBIT (FY25) | 8.5x | **9.0x** |
| EV/EBIT (FY26E) | — | **11.0x** |
| EV/Cash EBITDA (FY26E) | — | 6.5x |
| FCF yield | 16.7% | **~11.7%** (FY25 FCF $25.4m included a **$9.5m** trade-receivables release, $38.3m→$28.8m — a one-off, not run-rate) |
| P/B | 0.78 | 0.77 — **but P/TBV ≈ ∞ (tangible book ≈ $7m)** |
| Net cash / cap | 19.3% | **~6%** |

| Scenario | p | Thesis | FV |
|---|---|---|---|
| **Bear** | 0.35 | No bid. FY26 lands at/below guide; the $1.9m Saudi milestone slips; CSU sells or sits; the 5-Jun premium unwinds. Also the tail where the IT investigation widens. 8x FY26E EBIT + net cash | **235p** |
| **Base** | 0.45 | No bid in the window. Guidance holds, accessoPay contributes modestly in FY27, revenue stabilises ~$146–150m. 10x FY26E EBIT + net cash — i.e. roughly where CSU bought | **270p** |
| **Bull** | 0.20 | A firm offer emerges (CSU or another VMS/PE acquirer — precedent VMS take-privates 12–16x EBITDA on ~$20m Cash EBITDA ⇒ EV $240–320m) | **620p** |

**E[FV] ≈ 0.35(235) + 0.45(270) + 0.20(620) = 82 + 121 + 124 = 327p.**
Live 306.5p ⇒ **edge ≈ +6.7pp.**

That +6.7pp is *entirely* the 20% bid leg. Strip the bid and E[FV] on the fundamental legs alone is **~255p, i.e. −17% from spot.** An edge that survives only on an unannounced takeover, at a price 18% above where the potential acquirer bought, is not an edge — it is a coin-flip already paid for. **Default-REJECT stands.**

---

## 7. Path check (mandated)

- 52w high **451p** → 52w low **231p** → live **306.5p**.
- **+32.7% off the 52w low, 117 days since the low** — and **22 of those 33 percentage points came in a single session** (5-Jun) on a stake disclosure.
- The shelf's `entry_exhausted: false` is technically within its threshold but substantively wrong: **this is a late entry into a one-day repricing that has not retraced in two months.**

## 8. Four-idea frame

1. **Long the value discount** — dead. The discount does not survive the corrected share count, corrected cash, and the goodwill composition of book.
2. **Long the CSU takeout option** — real, but you buy it 18% above the strategic's own cost and with no Rule 2.4 to define a window. Wrong price, undefined clock.
3. **Short the bid premium** — coherent in theory (22% of price is speculation) but uninvestable: AIM micro-cap, $158k/day, no borrow to speak of, and the tail is a bid that doubles it. **Never short an unannounced-bid premium in a name a serial acquirer is accumulating.**
4. **Wait for the fill CSU got** — the only disciplined expression. See §9.

## 9. Ruling, and the level that would re-open it

**3/10 — REJECT. No entry band; below the contract's 4/10 threshold.** Not red-team required.

Not a fraud, not a broken balance sheet, and not a dishonest management — simply not cheap, de-growing, and already carrying a takeover premium.

**Re-court trigger (a watch level, deliberately NOT a live band):** **255–270p**, the pre-CSU clearing zone and where Constellation itself bought. A fill there requires either the bid premium bleeding out or a guidance cut — so it must be re-courted on arrival, not bought on a resting order. If re-courted and clean, UK sizing caps at **0.75% of $3.3M ≈ $24.8k**, which is ~1 day of the 20%-of-prints order cap ($31.6k/day). Friction at entry: 81bp touch, **0% stamp (AIM)**, 0% dividend WHT.

## 10. Kill triggers / dated gates

| Trigger | Date | Action |
|---|---|---|
| Interim results | **15-Sep-2026** | FY26 guidance ($146m / $20.0m Cash EBITDA) cut ⇒ dead, re-court only below 230p |
| The $1.9m Saudi milestone revenue not delivered in H2 | by FY26 close | Guidance miss ⇒ kill |
| IT incident scope widens (customer/payment data, or a quantified financial exposure) | any | Kill regardless of price |
| Constellation Software files a **4%+** TR-1 | any | Escalate immediately — thesis flips to special-sit court |
| Constellation Software's stake **falls below 3%** | any | The 22% premium unwinds; expect 255–265p; re-court |
| A Rule 2.4/2.7 announcement | any | Stop the value court; open a special-sit court (spread/terms/break risk) |
| Goodwill impairment charge against the $139.4m balance | FY26 results | Confirms franchise erosion |

## 11. Freezable call

**`ACSO | 2026-12-31 | no firm offer under Rule 2.7 for accesso Technology Group is announced on or before 31-Dec-2026 | our_p = 0.82`**

(Encodes the base rate that a 3% Constellation toehold, held flat for two months with no threshold escalation, is an option rather than a process.)

## 12. Verification gaps — UNVERIFIABLE, listed honestly

1. **Net cash today is ESTIMATED, not reported.** The £14.5m→USD conversion uses an assumed ~1.29 mid-March GBPUSD (not pulled), and H1-26 cash generation is modelled (+$2–8m), not disclosed. UK semi-annual reporting means the last audited balance sheet is **31-Dec-2025 — seven months stale.** Resolved 15-Sep-2026.
2. **The identity of both major customers is UNVERIFIED** (see §3). The Six Flags/Cedar Fair read is an inference; the whale-resolution method does not reach software vendors.
3. **Constellation's intent is unknowable.** A 3.16% stake is consistent with a takeout, a long-term hold, and an index-agnostic value purchase alike.
4. **The IT incident's final scope is open** by the company's own statement.
5. Share count 33,282,874 is as at 18-Mar-2026; any subsequent option exercises are not captured (immaterial to the ruling).
6. IBKR line **is** verified executable (conid 129385962, LSE, verified 2026-08-04) — this is one of the few conids on the shelf that is not data-gated.
