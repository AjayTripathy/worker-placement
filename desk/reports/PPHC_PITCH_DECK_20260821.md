# PITCH — PPHC — VERDICT

**PROPOSED — PENDING ADJUDICATION** — no position today; a 0.4%-of-book maximum starter is proposed, but it is *hard-blocked* until we verify how much stock actually trades each day, and two pieces of arithmetic neither bench ran are finished.

---

## What we believe

Public Policy Holding Company (Nasdaq/AIM: PPHC, CIK 1903508) is a Washington DC lobbying and corporate-communications roll-up: it buys small advocacy firms and bolts them together. About 1,500 clients, none more than 2% of revenue, top ten only 7.5% — genuinely no customer-concentration risk, which is rare and which we verified rather than assumed.

Three things we think are true and that the market has no organized opinion about:

1. **The core business is good and the damage is in the smaller half.** Government Relations did $58.7M of revenue at a 46.7% profit margin in the first half. Corporate Communications did $36.5M at 24.9%. Every deceleration and margin complaint in both of our own benches was stated at the company level, which averages the two together and hides that the good segment is intact.
2. **Nobody covers this stock.** We searched and found no published analyst estimate for 2026 or 2027, no short report, and no independent forecast of any kind. The only number in the market is management's own guidance. A dual-listed micro-cap with zero coverage cannot be efficiently priced — which cuts both ways, but it means "it's already in the price" is an assertion nobody has actually made.
3. **The stock is cheap on the headline metric and much less cheap on an honest one — and the honest one is still not expensive.** At $10.56 with 30,216,533 shares outstanding (per the company's own 8/7/26 cover-page count), the equity is worth $319.1M. Add $5.2M net debt and $16.7M of earn-outs owed to sellers of acquired firms and you get roughly $341M of enterprise value, about 6.9x profits before interest, tax and depreciation — versus the ~6.5x the headline gets you by ignoring the earn-outs. That is a 6% difference, not a disqualification.

What we do **not** believe: that this is an edge trade. If we own it, we own it as a dividend-paying, low-debt, boring holding at a fair-to-cheap price. It should be labeled that way in the book.

## What the market believes

There is almost no market opinion to describe, and that is the finding.

- The stock IPO'd in the US on 1/28/26 at $12.25 and trades at $10.56, down 13.8% from issue. It is 30.3% below its 52-week high of $15.15 and 50.7% *above* its 52-week low of $7.005 — mid-range, not distressed. The tape is not screaming anything.
- The 180-day lock-up on IPO shares expired around 7/27/26. Legacy AIM holders and the partner-shareholders of the acquired firms became free to sell, and the stock has drifted. That is the most likely explanation for the discount, and it is a supply story, not a business story.
- The last visible news was management raising full-year revenue guidance to $213–216M. Press coverage recirculated the raise. It did not report what the company itself said in the same document: the raise "is attributable to completed and announced acquisitions, **with the company's outlook for the underlying business unchanged**." So the market's one data point is weaker than it reads.

## Why we might have edge

- **We read the filing, not the transcript.** On the 8/17 earnings call, management said the big share-based-compensation grant "fully amortizes 12/31/2026" — the standard version of "our reported earnings inflect upward next year." The quarterly filing says $14.0M of that expense is still unrecognized, including $9.9M of restricted stock units spreading over up to **4.9 years**. And the company granted 669,879 *new* units in the first half at $9.10, about 2.2% of the company per year. The expense steps down; it does not end. Anyone trading the "2027 earnings cliff" story off the call is trading a fact the filing contradicts.
- **We priced the earn-outs.** $16.7M of contingent payments to sellers plus $15.6M of prepaid post-combination obligations = $32.3M of acquisition liabilities that the "net debt $5.2M" headline leaves out.
- **We know what the cash-flow add-back is.** The company reports positive "adjusted free cash flow" of $4.1M off operating cash flow of *negative* $9.1M. The largest bridging item is $9.6M of "prepaid post-combination expense" — plain English: cash retention payments to the partners of the firms it bought. In a business whose only assets are people, that is a real, recurring cost of the thing you purchased, running roughly $19M a year, and it is excluded from both the free-cash-flow and the profit metrics the stock is valued on.
- **Segment-level, not company-level.** See above: the two halves of this business are diverging and nobody is reporting it that way.

## Why it might be priced in

Stated plainly, because we should not talk ourselves into this:

- **Cash collection genuinely got worse, in both quarters, not just seasonally.** Second-half-weighted businesses normally show negative first-half cash flow, and this one did in 2025 too (−$0.3M). But 2026 was −$9.05M, and the standalone second quarter went from +$8.35M to +$2.61M, down 69%. Receivables grew from $21.9M to $30.9M; the average time to get paid went from about 40 days to about 54. A drifting, uncovered micro-cap may simply be pricing that correctly.
- **Shareholders captured none of last year's growth.** Revenue up 16.3%; adjusted profit up 15.5%; adjusted earnings *per share* down 1.7% for the half and down 24% in the second quarter alone, because the diluted share count went from 25.8M to 30.3M.
- **The second-half guide requires an acceleration.** Guidance of $213–216M against $102.266M booked in the first half implies second-half revenue of $110.7–113.7M, or +12.3% to +15.3% over last year's second half — while the most recent reported quarter grew 7.3%.
- **They paid a $7.0M dividend out of negative operating cash flow**, funded in effect by IPO money. That is a governance flag regardless of what you think of the business.
- **More stock may be coming.** The lock-up expiry detector's second stage is a follow-on offering in the 90–180 days after expiry. Nothing has been filed. That window runs to late January but the dangerous part of it is October–November.

## What we checked ourselves

| Claim | How checked | Found | Confirmed? |
|---|---|---|---|
| Market cap $252.6M (evidence pack) | Company's own cover-page share count 30,216,533 @ 8/7/26 × $10.56 | **$319.1M.** The pack was 26% low. | **Pack wrong — corrected** |
| Pack's per-quarter revenue / share / cash-flow fields | Pack shipped them blank; pulled from SEC's XBRL API directly | Full series recovered | Pack incomplete — closed |
| "sec.gov blocks us" | Both benches retrieved every primary document through a proxy | The blocking caveat in the brief was avoidable; no citation was actually unavailable | **Our own process error** |
| Original brief: "the cash-flow gap is a receivables timing problem" | Company's own cash-flow reconciliation in the 8-K | The bridge is dominated by a $9.6M payment to acquired-firm partners, not working capital | Confirmed as an *addition* |
| Red bench: "the gap contains **zero** working capital" | Blue bench re-ran red's own arithmetic | **Overstated.** Receivables are the reason operating cash flow is negative in the first place — they sit *inside* the −$9.05M, before the add-backs. Both problems are live. | **Our bench erred** |
| Red bench's self-nominated strongest kill: "growth was bought with paper" (25.8M → 30.3M shares) | Decomposed the 4.5M share increase | 3,742,500 shares are the **IPO primary issuance** — 83% of it — which is the same issuance that paid net debt down from $42.2M to $5.2M. Compensation vesting and deal paper together are ~1.0M shares. You cannot call the shares pure dilution and the cash "not theirs." | **Our bench erred — kill substantially overturned** |
| Red bench: cash-flow deterioration is a "consensus" concern | Searched for sell-side notes, short reports, press coverage | No sell-side estimate exists at all. Nobody is carrying this. | **Our bench's own tag wrong — retagged novel** |
| Red bench findings 3 and 4 | Read together | Internally inconsistent: finding 3 proves the guide is acquisition-driven; finding 4 then judges the acquisition-driven guide as if it were an organic-growth stretch, against a quarter that itself contained partial acquisition revenue. | **Our bench erred — reduced to plausible** |
| Transcript "SBC fully amortizes 12/31/2026" | 10-Q equity note | $14.0M unrecognized, RSUs over up to 4.9 years, plus 669,879 new units granted at $9.10 | **Confirmed — this is the case's decisive fact, and our red bench ranked it seventh** |
| Segment split | 8-K segment table | GR $58.7M / 46.7% margin; Corp Comms $36.5M / 24.9% | **Confirmed — and both benches argued only at company level** |
| Quarterly cash-flow splits used by both benches | Derivation check | Both derived Q1/Q2 by subtracting year-to-date figures — unaudited, carries derivation error. Neither bench established the 2024/2025 third-quarter baseline that red's own "what would change my mind" test requires. | **Both benches erred — gap open** |
| "CEO sold $13.2M of stock" (QuiverQuant) | Form 4s | 1000× unit error in the data vendor. False. | Refuted |
| June 16 Form 4 cluster | Transaction codes | All code A — grants, not sales | Refuted as a red flag |
| 10-K/A amendment | Read | Denominator-only revision (two-class share counting). Not a restatement. | Refuted as a red flag |
| Customer concentration | Filings | Top ten = 7.5%, none over 2%. Genuinely clean — a positive finding, not just an absent negative. | Confirmed |
| Average daily trading volume | Attempted via broker | **Blocked — broker data permission denied this session. Not verified.** | **Open — blocking** |
| Physical-world checks (construction permits in three cities, satellite emissions, import records, app reviews, consumer demand) | Dispatched and each individually cleared | All correctly inert: one leased DC office, no goods, no app, no consumer product. No hidden signal available from these. | Confirmed not applicable |

## PROPOSED ENTRY BANDS

**Today: no order. Size is zero until the liquidity check clears** — we do not know this stock's average daily volume, and our own publishing rule caps any order at 1% of it. That is a hard gate, not a preference. Everything below is conditional.

**Three checks must all pass before the first share:**

1. **Liquidity.** Verify average daily dollar volume through the broker. If a 0.2%-of-book order cannot be worked at ≤1% of daily volume over five sessions, the position is unbuildable and the answer is no.
2. **The acquisition-revenue bridge.** Decompose the $213–216M guide into revenue from deals already closed versus underlying growth. Neither bench ran it. If underlying growth is ≥5%, the second-half guide is arithmetic and the deceleration complaint dies. If it is below 3%, the guide is a stretch and we do not buy at any price above the low band.
3. **Third-quarter cash-flow baseline.** Establish what third-quarter standalone operating cash flow actually was in 2024 and 2025, so that the 11/10 number can be judged. Without it we cannot tell a bad quarter from a normal one.

**If all three pass:**

- **First tranche — 0.2% of book at $10.56 or lower.** Basis: 6.9x enterprise value to profits including the earn-outs, on a business whose better half earns a 46.7% margin with no customer over 2%. This is the fair-value entry, not a bargain.
- **Second tranche — a further 0.2% at $9.10 or lower.** Basis: $9.10 is the price at which the company itself granted 669,879 restricted units to its own people in the first half of 2026 — the only internal mark we have. That level is roughly 6.0x including earn-outs.
- **Total cap: 0.4% of book.** Not negotiable upward on this evidence. This is a carry position — low debt, a dividend, bounded downside — not an alpha position.

**Adds below the cap, only if the business is intact:**

- **$8.00 or lower is an add only if the third-quarter filing shows operating cash flow at or above the 2025 third quarter *and* the prepaid post-combination obligation flat or down from $15.6M.** At $8.00 the enterprise is ~5.4x, and ~15–17x our realistic estimate of this year's true free cash flow ($14–16M). Without those two conditions, a lower price is information, not an opportunity.

**Exits and trims:**

- **Exit on a follow-on stock offering** (an S-1, S-3 or 424B filing). A primary raise this soon after the IPO re-dilutes into the same story and triggers the second leg of the lock-up pattern.
- **Exit if second-half revenue lands below $110.7M** — the bottom of what management's own guide implies.
- **Exit if the prepaid post-combination obligation grows again from $15.6M while operating cash flow is still negative.** That combination means the roll-up is paying for its acquisitions out of a shrinking cash base while reporting positive "adjusted" cash flow.
- **Exit on partner-shareholder sales** — Form 4s with transaction code S from the principals of acquired firms after the lock-up.
- **Trim into $12.25.** Above the IPO price, the post-lock-up discount that is the entire entry rationale no longer exists.
- **Break of $7.005 (the 52-week low): do not average down.** Reopen the case from scratch.

**Catalyst dates:**

- **~2026-10-25** — 90 days past lock-up expiry; the highest-risk point in the follow-on window. Watch the filing feed, not the tape.
- **2026-11-10** — third-quarter results. **This date is derived from a data vendor and is NOT confirmed by any company announcement.** Treat it as approximate until a company release names it. This is the print that settles cash collection, share count, and the earn-out balances.
- **2026-12-31** — the date management said on the call that the big compensation grant fully amortizes. The filing already contradicts this. If the fourth-quarter filing shows the expense continuing, that is a documented gap between what was said out loud and what was filed.

## ARMED SENSORS

(armed provisionally with this deck; session adjudication ratifies)

- price alert: fires below 7.005 (deck-provisional: 52-week low — do not average down; reopen the reject case from scratch)
- filing watch: S-1,S-3,424B4,424B5 until 2027-02-17 (deck-provisional: follow-on offering is the untriggered second leg of the lockup-expiry pattern (lockup expired ~2026-07)
- dated pack PPHC|2026-10-25: PPHC: 90 days past lockup expiry — peak of the follow-on offering risk window; watch filings, not tape (date confirmed=False)
- dated pack PPHC|2026-11-10: PPHC: Q3 2026 results — vendor-derived date, no company announcement names it; settles cash collection, share count and earn-out balances (d
- dated pack PPHC|2026-12-31: PPHC: date management said on the 8/17 call that the equity grant 'fully amortizes' — already contradicted by the 10-Q's $14.0M unrecognized


## What remains unverified

- **Average daily trading volume.** Blocked this session. Everything is gated on it.
- **The split of guided second-half revenue between acquisitions and underlying growth.** Neither bench produced it. This is the single number that decides whether the guide is arithmetic or a stretch.
- **Third-quarter operating cash flow in 2024 and 2025.** Without the baseline we cannot grade 11/10.
- **The quarterly cash-flow figures both benches used** were derived by subtracting year-to-date numbers rather than read from a filed quarterly statement. Directionally reliable; not audited.
- **The 11/10 earnings date.** Vendor-derived, unconfirmed by the company.
- **The dividend rate does not reconcile.** $7.0M paid in the first half across ~30M shares is about $0.23 per share; the blue bench quotes a ~3.4% yield, which at $10.56 implies about $0.36 a year, or roughly $0.09 a quarter — about $5.4M for two quarters, not $7.0M. Either the $7.0M spans a different number of periods, includes a one-off, or the yield figure is wrong. **We have not read the declared per-share rate from a primary source, and the carry case leans on it.** This should be resolved before any purchase.
- **Fair value is not gradeable.** With no external forecast in existence, neither bench's valuation can be scored against anything. We can say what multiple we are paying; we cannot say we are paying less than the market thinks it is worth, because the market has not said.
- **Whether the second-quarter comparison period actually contained full quarters of the 2026 acquisitions.** Red asserted yes; blue disputed it. Unresolved, and it changes whether the deceleration is real.

Primary sources: [Q2 2026 10-Q](https://www.sec.gov/Archives/edgar/data/1903508/000162828026055678/pphc-20260630.htm) · [Q2 2026 earnings 8-K](https://www.sec.gov/Archives/edgar/data/0001903508/000162828026055194/pphc-earningsreleasex2026q.htm) · [SEC XBRL operating cash flow series](https://data.sec.gov/api/xbrl/companyconcept/CIK0001903508/us-gaap/NetCashProvidedByUsedInOperatingActivities.json) · [SEC XBRL shares outstanding](https://data.sec.gov/api/xbrl/companyconcept/CIK0001903508/dei/EntityCommonStockSharesOutstanding.json)

```json
{"price_gates": [{"level": 10.56, "direction": "below", "basis": "first tranche 0.2% of book — 6.9x enterprise value incl. $16.7M earn-outs; only after liquidity, bridge and baseline gates clear"}, {"level": 9.10, "direction": "below", "basis": "second tranche 0.2% — price at which the company granted 669,879 RSUs to its own people in H1'26; the only internal mark; ~6.0x incl. earn-outs"}, {"level": 8.00, "direction": "below", "basis": "conditional add only if Q3 operating cash flow >= FY25 Q3 and prepaid post-combination obligation flat-to-down from $15.6M; ~5.4x EV, ~15-17x realistic FY26 free cash flow of $14-16M"}, {"level": 7.005, "direction": "below", "basis": "52-week low — do not average down; reopen the reject case from scratch"}, {"level": 12.25, "direction": "above", "basis": "IPO price — above issue the post-lockup discount that is the entire entry rationale no longer exists; trim"}], "event_gates": [{"forms": ["S-1", "S-3", "424B4", "424B5"], "why": "follow-on offering is the untriggered second leg of the lockup-expiry pattern (lockup expired ~2026-07-27); a primary raise re-dilutes and is an exit"}, {"forms": ["10-Q"], "why": "Q3 filing settles standalone Q3 operating cash flow, days-to-collect (40 -> 54 in H1), prepaid post-combination obligation ($15.6M), contingent consideration ($16.7M) and diluted share count"}, {"forms": ["8-K"], "why": "new acquisitions create fresh partner-retention cash obligations excluded from adjusted free cash flow; also carries dividend declarations and any guidance change"}, {"forms": ["4"], "why": "post-lockup partner-shareholder sales — the 2026-06-16 cluster was all code A grants; code S sales would be new and are an exit trigger"}], "catalyst_dates": [{"date": "2026-10-25", "what": "90 days past lockup expiry — peak of the follow-on offering risk window; watch filings, not tape", "confirmed": false}, {"date": "2026-11-10", "what": "Q3 2026 results — vendor-derived date, no company announcement names it; settles cash collection, share count and earn-out balances", "confirmed": false}, {"date": "2026-12-31", "what": "date management said on the 8/17 call that the equity grant 'fully amortizes' — already contradicted by the 10-Q's $14.0M unrecognized over up to 4.9 years", "confirmed": false}], "immediate_entry": null}
```
---

# Adjudication & verification update (2026-08-22)

**Ruling (2026-08-22):** MINIMUM STARTER 0.25% (~245 sh at ≤$10.40), RP_FAIR-CARRY. Red's REJECT was
overturned on audit — 83% of the claimed "dilution" was the January IPO primary, which is the very
transaction that created the net-cash position; red's H2-guide finding contradicted its own M&A
finding. Four surviving kills, all NOVEL and all sizing-class (SBC cliff overstated vs the transcript
claim; DSO 40→54; AFCF flattered ~$19M/yr by post-combination cash comp; earnout-inclusive EV 6.9×).
No named fatal kill exists, so the clean-court minimum starter is the ruling — at the 0.25% floor
because the name is an orphan (zero sell-side coverage, no external anchor). **Instruction #101
staged** (BUY 245 @ $10.40 DAY, marketable cap vs $10.17 tape — entry at fair, not a resting bid).

## Verification results (all primary-source; run 2026-08-22)

**1. Add-gate 1 — inorganic bridge: DECOMPOSED, GATE NOT PASSED.**
*Claim:* growth is mostly acquired. *Method:* company's own organic disclosure, H1-26 earnings
release (8-K Ex. 99.1, 8/10) + 10-Q (8/11). *Finding:* H1-26 revenue +16.3% to $102.3M, of which
**organic +4.4%** (Q2 alone: +3.9%). FY26 guide raised ($205–209M → $213–216M revenue; adj. EBITDA
$46–48M → $48.5–50.5M) with the raise **100% attributed to acquisitions** — "the Company's outlook
for the underlying business is unchanged," organic guide ~5%. Segment split: Government Relations
organic +6.3% (PR) / +7.4% (10-Q MD&A — minor PR-vs-filing divergence, footnoted); Public
Affairs/Comms organic **−0.9%**. *Gate math:* 4.4% < 5.0% bar → **adds stay closed**; re-test at Q3.

**2. Add-gate 2 — Q3 OCF seasonality baseline: BUILT.** (desk/seasonality.py is a revenue-shape
tool on XBRL and PPHC has only two US-filer quarters, so the baseline was built by hand from
filings.) *Method:* S-1/A (1/23/26) interim statements + 10-Q comparatives. *Finding:* PPHC's cash
year is violently seasonal — H1 is bonus-payment season and runs ~breakeven-to-negative; **Q3 is
the strong cash quarter: Q3-24 +$7.7M, Q3-25 +$9.6M standalone** (cross-derivation from 9M-25
+$10.0M minus restated H1-25 −$0.3M gives +$10.3M; ~$0.7M restatement/rounding delta noted).
Normal Q3 ≈ **+$8–10M**. Context the print must resolve: H1-26 OCF was **−$9.05M** vs −$0.3M in
H1-25 (AFCF $4.1M vs $11.7M), partly the post-combination prepay ramp. The kill trigger "Q3 OCF
negative" is therefore a ~$17–19M miss against seasonal normal — a real signal, now gradeable.

**3. Kill-trigger watch — follow-on filing: CLEAN.** No S-1/S-3/424 since the ~7/28 lockup expiry
(180 days from the 1/29 424B4). Post-window filings are: 8-K 8/03 (Advocacy Partners completion),
8-K 8/10 (H1 results), 10-Q 8/11. The 7/15 Form D is an exempt placement consistent with
acquisition share consideration (the quarterly Form-D cadence tracks deal closings), not a public
follow-on. Watch stays live through late October.

**4. Next print date: STILL UNCONFIRMED.** Checked the H1 release (no Q3 date), the corporate site
(no calendar), and the IR subdomain (timed out). Reporting cadence implies ~11/9–11/10 (Q1 reported
5/12, Q2 on 8/10, both ~41 days after quarter-end) — consistent with the yfinance-derived 11/10 but
not primary-confirmed. The calendar guard should re-check when the Q3 notice 8-K posts.

## New facts since the benches
Two post-period acquisitions completed, both cash-and-shares: **Tancredi Intelligent Communication
Ltd** (London strategic comms, 7/01) and **The Advocacy Partners** (Florida government relations,
8/01) — these are what the guide raise carries, and they feed the existing dilution kill-trigger
("diluted WAS growing QoQ into Q4 on new deal paper"), which now has two more share issuances to
track through the Q3/Q4 filings.

**Adds posture: UNCHANGED.** Starter stands as ruled; both add-gates remain closed (organic 4.4%
vs the 5% bar; Q3 baseline now exists but grades only at the print). Nothing here re-rules.
