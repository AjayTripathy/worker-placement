Both benches landed REJECT, so this deck is a no-entry pitch with reopen conditions. I don't have read access to the court_artifacts directory in this session, so I'm delivering the deck as the message body for the pipeline to capture.

# PITCH — GOGO — PROPOSED VERDICT (PROPOSED — PENDING ADJUDICATION): REJECT — no position, no orders; both benches (8/10 red kill, sustained by blue 8/10) found the guidance cut is a real operating decline plus a permanent legal cost, not the mislabeled one-time item the original idea claimed.

## What we believe
Gogo (in-flight internet for business jets, ~$3.64/share, down 72% from its 52-week high) cut its full-year 2026 guidance on August 6 alongside Q2 results. The idea that brought it to court was a bull case: the cut looked mostly cosmetic — supposedly $27M of the free-cash-flow reduction was a newly disclosed $30M "strategic investment" plan, meaning the underlying business was roughly fine and the stock was trading at a 15–21% free-cash-flow yield.

After reading both the Q1 and Q2 guidance press releases word-for-word, we believe the opposite. The $30M strategic-investment figure was **already inside the prior guidance, in identical language** — so it explains none of the cut. The ~$25M free-cash-flow reduction is roughly $14M of litigation costs and ~$11M of genuine operational weakness, and the earnings (EBITDA) guide fell about $12M (−5.5%) on a like-for-like basis three months after being reaffirmed. On top of that: the headline free cash flow leans on a finite ~$45M/year FCC reimbursement program; a jury found Gogo **willfully** infringed SmartSky's patents (opening the door to up to ~$68M tripled damages plus an ongoing royalty on the very 5G product meant to drive growth); its largest visible customer group (the NetJets fleet, 600+ aircraft) is migrating to Starlink through 2027; cash is $63M and falling against ~$22M/year of legal spend; and essentially all the debt comes due on a single date, April 30, 2028, at roughly 3.8x leverage.

## What the market believes
The market has already punished the stock severely — it sits 20% above its 52-week low after the post-guidance drop. The prevailing story is "cheap on free cash flow, but melting": a legacy air-to-ground network being shut off, customers defecting to Starlink, a patent loss, and a debt wall. At this price the market is treating the guidance cut as real deterioration, not noise. One genuine positive the market may be underweighting (our blue bench found it): the **service** (recurring subscription) revenue guide is essentially unchanged (~$740M before vs ~$741M now) — the entire ~$42.5M revenue cut is low-margin equipment sales. The recurring franchise is guided to hold through the network-shutoff year. But flat service revenue combined with lower earnings means service margins are compressing, so this tempers the bear case rather than overturning it.

## Why we might have edge
Honestly: the court concluded we don't, on the long side. The only claimed edge — "the cut is non-operating" — was refuted by primary documents in one read. What we do have is process knowledge: we caught a specific analytical trap (a company re-naming an item already inside old guidance, which careless readers book as a new incremental hit). That trap is now encoded in our detector library. The residual asymmetric knowledge is the blue bench's flat-service-revenue finding, which most quick reads of the release likely missed — it's the seed of a possible future long if the recurring business proves durable, but it is not enough today.

## Why it might be priced in
It largely is, in the bearish direction — a 72% drawdown already discounts a lot of pain. The reason we still reject rather than bottom-fish: the apparently high free-cash-flow yield is an illusion of subsidy and timing. Strip the $45M FCC reimbursement and guided free cash flow is roughly $30M — about a 6% yield on the ~$492M equity value (blue bench bounds the true run-rate anywhere from $30M to $75M because the reimbursed capital spending also ends when the program does; the press releases can't resolve it). Six-ish percent is thin compensation for 3.8x leverage, an uncapped willful-infringement tail attached to the growth product, a marquee customer exodus, and a single-date 2028 refinancing. Cheapness that depends on a government reimbursement and precedes a debt wall is not a mispricing; it's fairly priced distress.

## What we checked ourselves

| Claim | How checked | Found | Confirmed? |
|---|---|---|---|
| "$30M strategic investments = −$27M of the FCF cut" (the bull thesis's core) | Fetched Q1 and Q2 guidance press releases, compared inclusion language verbatim ([Q1 PR](https://www.globenewswire.com/news-release/2026/05/07/3289794/0/en/Gogo-Announces-First-Quarter-Results.html), [Q2 PR](https://www.globenewswire.com/news-release/2026/08/06/3340082/0/en/gogo-announces-second-quarter-results.html)) | The $30M was inside the **prior** FCF guide in identical words; the incremental effect is $0. The −$25M cut ≈ $14M litigation + $11M operations. **Our own triage bench manufactured the −$27M delta from a re-disclosed constant — this deck exists because of that error.** | REFUTED (thesis); both benches independently replicated |
| EBITDA guide cut is operational | Arithmetic on both releases' stated inclusions: prior $208M mid + $3M + $8M = $219M like-for-like vs new $180M + $5M + $22M = $207M | −$12M (−5.5%) operational cut. **Red bench's own bridge was garbled (it subtracted the add-backs instead of adding); blue corrected the arithmetic; the conclusion survived unchanged.** | CONFIRMED |
| "15–21% FCF yield" | Both releases: guidance assumes $45M FCC reimbursement, net capex $20M | Ex-reimbursement, guided FCF ≈ $30M ≈ 6% yield. **Red called this fatal; blue correctly demoted it to a sizing issue** — the reimbursed capex also ends with the program, so run-rate FCF is only boundable at $30–75M | PARTIALLY — subsidy real, exact floor unproven |
| "Revenue resilient (−1%) despite units −15%" | Evidence pack XBRL (quarterly revenue ~$102M in 2024 → ~$226M in 2025) + Q2 release | Resilience is an artifact of consolidating the Satcom Direct acquisition plus military/government +40%; core business-aviation service revenue fell 8% YoY; departing NetJets planes are high-revenue units | CONFIRMED (mix); forward acceleration plausible, not proven |
| SmartSky litigation is contained | News/PR review ([verdict PR](https://www.prnewswire.com/news-releases/smartsky-wins-patent-infringement-lawsuit-versus-gogo-on-all-claims-302625784.html)); court docket **not** read | Willful verdict; enhanced (up to ~3x, ~$68M) damages and a running royalty through 2033/35 on the 5G product are being sought; post-trial motions pending | CONFIRMED as filed posture only |
| Service-revenue guide held flat (bull-direction find) | Blue bench bridge: ~80%×$925M vs ~84%×$882.5M | ~$740M vs ~$741M — the whole revenue cut is equipment | CONFIRMED |
| Live price $3.635 / no position / no orders | IBKR was **permission-denied to both benches**; used the pack's Yahoo tape and book snapshot | Not broker-verified this session | UNVERIFIED (disclosed) |
| Next earnings date 2026-11-05 | yfinance-derived only; no company PR names it | Treat as approximate | UNCONFIRMED |

## PROPOSED ENTRY BANDS
The courts say **no entry at any current price** — so these are reopen conditions, not orders:

- **Price reopen: below ~$1.50** (≈ $200M market value on ~136M shares). That is where the benches' own worst-case math — $30M of free cash flow with the FCC subsidy stripped out and litigation burn continuing — would itself equal a 15% yield, the return the bull case falsely advertised at $3.64. A touch of that level reopens a fresh court, not an automatic buy: by then the 2028 refinancing question dominates everything.
- **Event reopeners (any one triggers a re-court at market price):**
  1. The 10-Q or a later filing shows the ~$11M operational cash-flow cut was FCC-receivable *timing*, not demand (red's own reversal trigger).
  2. SmartSky's enhanced-damages and ongoing-royalty motions are **denied** (removes the uncapped tail).
  3. The April 2028 debt is refinanced at no worse than the current spread (removes the wall).
  4. A quarterly report beats on service revenue **with** revenue-per-aircraft on the legacy network disclosed flat or up (blue's trigger), or NetJets is disclosed at under 5% of business-aviation service revenue with the new Galileo product's economics shown comparable.
- **Sizing if any reopen court flips to buy:** small — the litigation and refinancing tails are all-or-nothing and can't be hedged; both benches barred a short as well (borrow and crowding never checked, and short-premium structures are off-limits in this book).
- **Catalyst dates:** ~2026-11-05 next earnings (unconfirmed); SmartSky post-trial rulings (no date; watch the docket via 8-K); 2028-04-30 debt maturity.

## ARMED SENSORS

(armed provisionally with this deck; session adjudication ratifies)

- price alert: fires below 1.5 (deck-provisional: ex-FCC-subsidy $30M FCF = 15% yield at ~$200M cap - reopen court, not auto-buy)
- filing watch: 8-K until 2027-02-05 (deck-provisional: SmartSky post-trial motion ruling, 2028 debt refinancing, or confirmed Q3 date)
- dated pack GOGO|2026-11-05: GOGO: Q3 2026 earnings (yfinance-derived, no company PR) (date confirmed=False)
- dated pack GOGO|2028-04-30: GOGO: single-date debt maturity wall at ~3.8x leverage (date confirmed=False)


## What remains unverified
- The 10-Q itself ([sec.gov filing](https://www.sec.gov/Archives/edgar/data/0001537054/000119312526337921/gogo-20260630.htm)) was **not read** — litigation accrual, covenant headroom, and the FCC receivable detail are all open.
- The true post-subsidy free-cash-flow run rate (bounded $30–75M, unresolvable from press releases alone).
- Whether Galileo (the new satellite product) replaces legacy *margin*, not just legacy units.
- The actual court docket on SmartSky (only press coverage read).
- Live broker tape and book state (IBKR permission-denied both benches; Yahoo tape used).
- The November 5 earnings date (software-derived, no company confirmation).

```json
{"price_gates": [{"level": 1.50, "direction": "below", "basis": "ex-FCC-subsidy $30M FCF = 15% yield at ~$200M cap - reopen court, not auto-buy"}], "event_gates": [{"forms": ["8-K"], "why": "SmartSky post-trial motion ruling, 2028 debt refinancing, or confirmed Q3 date"}, {"forms": ["10-Q", "10-K"], "why": "FCC receivable timing vs demand, litigation accrual, covenant headroom - all unread"}], "catalyst_dates": [{"date": "2026-11-05", "what": "Q3 2026 earnings (yfinance-derived, no company PR)", "confirmed": false}, {"date": "2028-04-30", "what": "single-date debt maturity wall at ~3.8x leverage", "confirmed": false}], "immediate_entry": null}
```