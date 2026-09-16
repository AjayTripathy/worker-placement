# PITCH — BTBT — VERDICT
**ADJUDICATED 2026-08-08 — EXCLUDE WHILE THE CONDUCT CONTINUES. No position, no price gate; the discount is real (~0.47x) and unharvestable, so this becomes a dated watch, not a buy at a lower price.**

## What we believe

Bit Digital is a holding company whose parts are worth roughly twice its stock price, and that gap will not close for us.

The parts, using the marks both our teams could verify:

| Piece | Amount | Value |
|---|---|---|
| Stake in WhiteFiber (WYFI), ~70% owned | 27.0M shares × $24.63 (2026-08-07 close) | $665M |
| Ethereum treasury | 158,461 ETH × $1,901 (June count) | $301M |
| Cash | — | ~$80M |
| **Total assets** | | **~$1.05B** |
| Market value of the whole company | 353,399,420 shares × $1.38 | $488M |
| **Ratio** | | **~0.47x** |

That is about $2.96 of assets per share against a $1.38–$1.45 stock. Even if you mark WhiteFiber at its all-time low print of $10.51 (March 2026), the assets are ~$1.88/share and the stock still trades at ~0.73x — a discount under nearly any assumption.

We also believe the reason it stays cheap is management behavior, not investor blindness. Two facts do the work:

1. On 2026-01-28 the company publicly stated it will not sell any WhiteFiber shares in a secondary offering or any other discretionary sale during 2026. The one action that would turn the stake into cash for shareholders has been talked away until the end of this year.
2. Meanwhile the share count went from roughly 331M to **353,399,420 by 2026-05-31** — about 22M new shares in two months — with the proceeds going into more Ethereum. The company is selling its own stock at roughly 47 cents on the dollar of asset value and buying an asset at 100 cents on the dollar. Every such dollar shrinks the asset value behind each existing share. That is roughly 9% of per-share value per half-year, running against us.

So: the cheapness is genuine, and the person holding the only key has both announced they won't use it and is actively making the lock heavier. We do not buy that, at any price, while it is true.

## What the market believes

The market believes exactly what we believe about the assets, and prices the behavior on top of it.

This is not a hidden story. The company itself publishes the sum-of-the-parts case every month — the May treasury release states "~27.0 million WYFI shares (~70%), ~$755.6 million" in plain text, and it put out a January press release titled "Bit Digital Reaffirms Long-Term Investment in WhiteFiber Shares." Investors can read the stake, the ETH count, and the share count without a subscription. The 53% discount is therefore a *considered* price, not an oversight: it is what buyers will pay for assets they cannot reach, held by a manager who keeps issuing stock below their value.

The market is also likely marking down the WhiteFiber stake for a reason our own bull case understated: WhiteFiber's tradable float is only about 9.3M shares, and our stake is roughly 27M shares — about three times the entire float. Nobody can sell that block into that market at $24.63.

## Why we might have edge

Three things we know that a casual reader of the stock screen does not:

- **The discount survives a hostile re-mark.** The first, most obvious rebuttal is "the $24.63 is a fake price on a thin float — it was $10.51 in March and $46.87 in June." We tested that by redoing the whole calculation at the post-crash August mark and with corrected ETH and share counts. It still came out at 0.47x. The discount is not an artifact of a June price spike.
- **The float problem cuts only one way.** A 27M-share block cannot be *sold* into a 9.3M-share float. But it can be *distributed* — handed to Bit Digital shareholders directly, no market sale required. That route is untouched by the float objection, and it is the route most likely to be used if the company ever acts.
- **The lock has a date on it.** The no-sale statement is not a contract; it is a stated intention, it carries a carve-out for derivatives and treasury activity, and it expires 2026-12-31. So there is a specific day when the single largest reason to avoid this stock stops being true — and the market currently has no reason to pay for that in advance.

## Why it might be priced in

Honestly: mostly it is.

- The stake, the ETH, the cash, and the share count are all published by the company, monthly. There is no information asymmetry.
- The discount is the market's *answer*, not its mistake. Holding-company discounts of 20–30% are normal when the parent won't distribute; ours is wider because the parent is also diluting. That is a rational premium for bad behavior, not a mispricing.
- A "dated 2027 catalyst" is a soft catalyst. December 31 is the day a promise not to sell lapses — nobody has promised to sell after it. There is no announced spin, distribution, or timetable. We would be paying today for an option the company has not written.
- The ETH treasury declined for the first time in June (162,081 → 158,461), consistent with cash and coins being drawn into funding WhiteFiber's build-out through a ~$100M facility (expandable to $150M). The parent's liquidity is committed downstream, not available to shareholders.
- Time works against us at ~9% of per-share asset value per half-year while we wait.

## What we checked ourselves

| Claim | How checked | Found | Confirmed? |
|---|---|---|---|
| The company has barred itself from selling WhiteFiber | Pulled the company's own 2026-01-28 press release and read it | Wording confirmed verbatim, ~27M shares, "during 2026" | **Partly — our own prosecution overstated it.** Our red team called it "contractually forsworn." It is a stated intention with a derivatives/treasury carve-out and an expiry of 2026-12-31. Real, but weaker and dated |
| The 0.47x discount is manufactured by a spiked, thin-float WYFI mark | Re-ran the whole sum-of-the-parts at WYFI's post-crash 2026-08-07 close of $24.63, with corrected ETH and share counts | 27.0M × $24.63 + 158,461 ETH × $1,901 + ~$80M cash ≈ $1.02–1.05B vs $488M market cap = **still ~0.47x** | **No — our red team was wrong on this one.** The June spike is not what creates the discount. The $10.51 trough case (0.73x) is a legitimate error bar, not the base case |
| Share count and dilution pace | Company monthly treasury releases | 353,399,420 shares at 2026-05-31; ~22M shares issued in two months; ETH rose 140,196 (3/31) → 162,081 (5/31) | **Yes, and worse than the bull brief said.** The brief stopped at 349.2M shares on May 11 and called dilution "+7.7% — the live counter-risk." It is larger and ongoing |
| "Proceeds are earmarked to buy Ethereum" | Traced the cited prospectus supplement | The quoted document is the **July-2025** B. Riley registered direct, not the current at-the-market program. **Our own source citation was stale.** The conclusion survives on other evidence — ~21.6k ETH bought in the same window as ~22M shares issued | **Conclusion yes, citation no** |
| ETH holdings of 140,195.9 | Company monthly releases + third-party treasury tracker | The bull brief's number was ~13–15% stale, in our favor: 162,081 at 5/31, then 158,461 in June (first decline) | **No — the brief's number was wrong, in the direction that helped us.** We corrected it against us where it mattered |
| Cash of ~$79.5M is "free" on top | Company release on the WhiteFiber financing facility | The cash is the funding source for a ~$100M (expandable $150M) facility into WhiteFiber's capital spending | **No — it is committed, not distributable** |
| The market is missing the story (a masking/misread edge) | Read the company's own investor-relations output | The company markets the sum-of-the-parts case itself, monthly, with dollar figures | **No. Nothing is hidden.** There is no misread to exploit |
| Next earnings date | Evidence pack said 2026-11-12; checked against the company's own filings | The pack date was a data-vendor estimate. The real Q2 print was **2026-08-13**, confirmed by the company's Form 8-K (accession 0001213900-26-088768, Item 2.02, 10:30 AM ET call) | **Pack was wrong; corrected.** Worth noting because our red team caught this four days before the print and our machine pack did not |
| WhiteFiber's own reporting date | Blue team check | **WYFI reported 2026-08-12 — one day before BTBT.** The mark on our largest asset re-rates before our own print | **Yes — and our red team missed it entirely.** This was the nearest tripwire and it went unflagged in the prosecution |
| Live price | Vendor tape (broker feed was unavailable — coverage gap) | $1.38 close 2026-08-06; $1.45 in the machine pack 2026-08-18; 52-week range $1.18–$4.55 | Yes |
| Financial statement detail (revenue, cash flow, stock comp) | Evidence pack XBRL block | The pack's figures are **2025 first/second-quarter vintage** — a year stale. Not used for anything load-bearing | **Flagged, not used** |

Where the two benches disagreed, the adjudication sided with blue on severity (the no-sale pledge and the float objection are sizing/timing issues, not fatal) and with red on the verdict. The kill is not the discount and not the float — it is the dilution.

## PROPOSED ENTRY BANDS

**No entry. No price. No size. Zero position, zero orders.**

This is deliberate and it is not a "wait for a better price" call. When the problem is what management does with our money, a lower price does not fix it — it makes the dilution cheaper for them and more expensive for us. So we do not set a buy level. We set conditions under which the case is reopened:

**Reopen gates (verbatim, as adjudicated):**
- **ATM suspension or ANY buyback authorization = immediate reopen.** Either one reverses the exact behavior that disqualifies the name. A buyback below asset value is the single most valuable thing this management could do and is the strongest possible signal.
- **WYFI Q2 8/12 + BTBT 10-Q 8/13: shares ≤358M AND stake ≥70% = thesis intact on watch.** This is a *maintenance* test, not an entry trigger. Passing it keeps the name on the watch list; failing it (more shares than that, or a stake that has slipped) removes it.
- **1/2027 pledge expiry = scheduled re-court.** The no-sale statement lapses 2026-12-31. We re-run the full adversarial process in January 2027 against whatever the company has actually announced by then.

**Sizing if reopened:** to be set at the re-court, not now. For reference, the benches' own arithmetic brackets fair value at ~$2.96/share of assets at live marks and ~$1.88/share if WhiteFiber is marked at its all-time low — and neither number is claimable by a shareholder until there is a distribution mechanism. Any future entry gets sized off the stressed number, not the live one, and off a *dated* monetization plan, not a lapsed promise.

**Dates that matter:** WYFI Q2 — 2026-08-12 (passed). BTBT Q2 — 2026-08-13 (passed; 10-Q accession 0001213900-26-088709). Monthly treasury releases — ongoing, the highest-frequency read on share count. Pledge expiry — 2026-12-31. Scheduled re-court — January 2027.

## ARMED SENSORS

(armed provisionally with this deck; session adjudication ratifies)

- filing watch: 8-K until 2027-02-14 (deck-provisional: ATM suspension or ANY buyback authorization = immediate reopen)
- dated pack BTBT|2026-08-13: BTBT 10-Q (8/13 est): HIT = shares out <=358M AND WYFI stake >=70% (thesis intact); separate standing trigger: ATM suspension/buyback = reop
- dated pack BTBT|2026-08-12: BTBT: WhiteFiber (WYFI) Q2 results - re-marks BTBT's largest asset one day before BTBT's own print; occurred, result unread (date confirmed=
- dated pack BTBT|2026-11-12: BTBT: estimated Q3 2026 print - data-vendor derived, no company announcement; the pack's date for Q2 was wrong by three months (date confirm
- dated pack BTBT|2026-12-31: BTBT: expiry of the company's stated intention not to sell WhiteFiber shares during 2026 (date confirmed=False)
- dated pack BTBT|2027-01-04: BTBT: scheduled full re-court on the first trading day after the pledge lapses; entry only against a dated monetization plan, never against 


## What remains unverified

Stated plainly, because several of these are load-bearing:

- **Neither bench read the 10-Q or the Q2 press release.** The court adjudicated on 2026-08-08, five days before the print. The 8/13 10-Q (0001213900-26-088709) and the earnings 8-K (0001213900-26-088768) are now on file, and the dated sensor above has fired without anyone confirming the result. The two numbers that decide whether this name stays on the watch list — shares outstanding and the WhiteFiber ownership percentage as of 6/30/2026 — are sitting in a filing nobody in this process has opened. **This is the single most important open item and it is overdue.**
- **What WhiteFiber reported on 8/12, and where WYFI trades now.** Our asset value is mostly this one mark, and our newest verified mark is 2026-08-07.
- **Direct SEC access failed during the court** (EDGAR fetch returned a 403). The 8/3 8-K contents were inferred from context, never read. Broker price data was also unavailable on permissions; all prices are vendor tape.
- **August share count and ownership percentage** were unverifiable at adjudication time and remain so until the 10-Q is read.
- **The current ETH balance.** Our last verified figure is 158,461 for June, and it was *declining*.
- **Whether the no-sale statement is actually binding on anyone.** We read the press release; we did not locate a lock-up agreement, underwriting agreement, or contractual restriction behind it. Our red team asserted one and could not support it.
- **Whether anything happens after 2026-12-31.** There is no announced plan to monetize or distribute the stake. The expiry of a promise is not a catalyst.
- **The financial statements themselves.** The machine-built evidence pack supplied 2025-vintage revenue, cash-flow and stock-compensation figures. We used none of them and have not replaced them with current ones.

Primary sources: company statement of intent not to sell WhiteFiber shares during 2026 — https://www.prnewswire.com/news-releases/bit-digital-reaffirms-long-term-investment-in-whitefiber-shares-302673075.html · company monthly treasury and staking metrics, May 2026 (share count 353,399,420; ETH 162,080.6; "~27.0 million WYFI shares (~70%)") — https://bit-digital.com/press-releases/ethereum-treasury-and-staking-metrics-for-may-2026/ · company financing facility supporting WhiteFiber — https://bit-digital.com/press-releases/bit-digital-originates-strategic-financing-facility-supporting-whitefiber-growth-initiatives/ · Form 8-K dated 2026-08-13, accession 0001213900-26-088768 (Item 2.02, Q2 2026 results), and Form 10-Q accession 0001213900-26-088709, both filed by Bit Digital, Inc., CIK 0001710350.

```json
{"price_gates": [], "event_gates": [{"forms": ["8-K"], "why": "ATM suspension or ANY buyback authorization = immediate reopen"}, {"forms": ["424B5", "S-3", "S-3/A", "424B3"], "why": "new or upsized at-the-market/shelf = dilution continues, exclusion confirmed, drop from watch"}, {"forms": ["10-Q", "10-K"], "why": "shares outstanding <=358M AND WhiteFiber stake >=70% keeps thesis intact on watch; failure removes it"}, {"forms": ["8-K", "SC 13D/A", "SC 13D"], "why": "any WhiteFiber distribution, spin, or in-kind transfer = the one closure route the thin float does not block"}, {"forms": ["8-K"], "why": "monthly Ethereum treasury and staking metrics release: fastest read on share count between quarters"}], "catalyst_dates": [{"date": "2026-08-12", "what": "WhiteFiber (WYFI) Q2 results - re-marks BTBT's largest asset one day before BTBT's own print; occurred, result unread", "confirmed": true}, {"date": "2026-08-13", "what": "BTBT Q2 2026 10-Q and earnings 8-K filed (accessions 0001213900-26-088709 / -088768); dated sensor fired, shares-out and stake % still unread", "confirmed": true}, {"date": "2026-11-12", "what": "estimated Q3 2026 print - data-vendor derived, no company announcement; the pack's date for Q2 was wrong by three months", "confirmed": false}, {"date": "2026-12-31", "what": "expiry of the company's stated intention not to sell WhiteFiber shares during 2026", "confirmed": false}, {"date": "2027-01-04", "what": "scheduled full re-court on the first trading day after the pledge lapses; entry only against a dated monetization plan, never against a lapsed promise", "confirmed": false}], "immediate_entry": null}
```