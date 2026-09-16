## Cause-check first

The screen's loudest artifact is a false positive: the **25-NSE (2026-07-22) is not a common-stock delisting** — it removed the *public warrant* class (27.6M warrants, $11.50 strike) that **expired unexercised on 2026-07-23**. The 8-K of 2026-08-07 is likewise benign (Item 5.02: Derek Liu appointed CAO). Neither is the cause.

The actual cause is a two-step operating break, fully disclosed: **Q1 2026 revenue $60.6M, −48% y/y** (vs. $116.5M) against a ~$101M consensus, printed 2026-05-11 with the stock −38.6%; preceded by a $32.5M inventory charge in the FY2025 print. **Going-concern substantial doubt has now appeared in three consecutive filings** — FY2025 10-K (Mar-2026), Q1 10-Q (May-2026), Q2 10-Q (2026-08-10) — and is **unalleviated** in the most recent one. This is not an unexplained dislocation; the issuer confirms the narrative in primary text.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| MVST | **DAMAGE-ARRIVING** | Going-concern conclusion status + 12-mo debt maturities ($104.2M ST bank borrowings + $41.7M bond due 2027-01-31 = $145.9M) vs. unrestricted cash ($127.8M) | Substantial doubt **NOT alleviated** as of 2026-08-10 10-Q; mitigation plans "cannot be deemed probable." H1-26 OCF **−$33.3M** (vs. +$44.3M PY); H1 adj. EBITDA **−$1.9M** (vs. +$54.4M). BUT damage decelerating: Q2 rev **$87.3M, −4.5% y/y** vs. Q1's −48%; Q2 adj. EBITDA back **positive +$3.6M**; GM 29.5% (from 34.7%); working capital **positive ~$31.2M** ($374.9M CA / $343.7M CL); debt roughly flat H1 while cash rose $105.0M→$127.8M. [Q2 8-K/PR](https://www.sec.gov/Archives/edgar/data/0001760689/000162828026055471/mvst2026q2ex991earningspre.htm), [Q1 10-Q](https://www.sec.gov/Archives/edgar/data/0001760689/000162828026033590/mvst-20260331.htm) | **~2026-11-09** (yfinance-derived, **UNCONFIRMED** — no company PR names it; Q1/Q2 filed May-11/Aug-10, so the cadence supports it) | Not DAMAGE-ABSENT (issuer confirms) and not STRUCTURAL (30% GM, revenue stabilized, net debt only ~$17M). The binding constraint is **holdco refinancing access, not unit economics** |

**Sourcing note:** SEC.gov returns 403 to this session's fetcher (no custom UA available, and Bash/file reads are permission-blocked here). Every figure above was read from mirrors of the primary documents; the SEC URLs are cited so a bench can re-pull them directly. Flagging this rather than implying I read EDGAR raw.

## COURT-WORTHY (damage-absent, ranked)

**NONE.** No member qualifies. MVST cannot be classified damage-absent against an issuer's own thrice-repeated, unalleviated going-concern conclusion — that would be arguing with the primary source. With N=1 member, the cohort-dispersion ranking the mandate asks for is degenerate in any case.

Three findings the cause-check surfaced that belong in the record regardless:

1. **The "profit" is reflexive and non-cash.** YTD net income of +$36.2M exists only because of a **$58.0M favorable fair-value swing on warrant liability + convertible loan** — i.e. the company booked income *because its own stock collapsed*. Operating result was **−$9.7M**. Headlines reading "posts profit yet flags going-concern" are describing a mark-to-market artifact, not earnings.
2. **Disclosure withdrawal at the decisive moment.** The Q2 2026 call carried **no analyst Q&A**, and management addressed neither the going concern, the ST-borrowing rollover, the Jan-2027 bond, repatriation, nor dilution. When the single load-bearing question is liquidity and the Q&A is removed, the nondisclosure is itself the finding.
3. **The RMB800M MPS facility does not solve the problem.** It is ring-fenced to Huzhou capacity capex and cannot fund holdco liquidity; Clarksville full-scale build remains "contingent on securing additional financing or strategic partnerships." Cash rose H1 on *restricted-use borrowings*, not on operations.

**PRINT PROXIMITY: ~2026-11-09 (Q3 2026 10-Q) — yfinance-derived, UNCONFIRMED by any company PR; ~60 trading days out, NOT within 5.** No pre-print reconstruction is owed. Note the favorable posture: the Q2 print landed 2026-08-10, five days ago, so this triage sits on fresh audited-quarter data with no catalyst being raced.

**COURT-WORTHINESS MVST: 4/10** — the cause is found and issuer-confirmed, and the one variable that would flip the verdict (Chinese bank rollover intent + PRC repatriation to the Delaware holdco) is unreachable from any public primary source a bench can litigate, so a full court lands where the triage already does.

Why 4 and not higher, despite genuinely arresting dispersion (a $291M market cap on ~30% gross margin, positive Q2 EBITDA, and only ~$17M net debt): the resolution path most likely runs through **equity issuance at $0.84 and/or a reverse split** — MVST already burned both 180-day bid-price compliance windows in 2024–25 and is back below $1 — which destroys the entry math whichever way a court rules on the credit. Management has closed the disclosure surface. And the decisive datum (does the doubt get alleviated, does the Jan-2027 bond get refinanced) **arrives free on ~Nov 9**. Paying a full bench cycle to front-run an unobservable is the wrong trade.

**What would raise this to ≥6:** a disclosed refinancing or retirement of the $41.7M Jan-2027 bond, *or* a Q3 10-Q that alleviates substantial doubt, while the market cap is still sub-$400M — that flips it to a real damage-absent re-rate candidate. Worth a tripwire, not a court.

**Recommended posture: FLAT.** Consistent with the pack (`held=NO POSITION, orders=NONE`) — no action, no gate. Per the response taxonomy this is a **data-blocking kill**, not a valuation gate: the finding is that the decisive input is unobtainable, and price gates are valuation instruments that don't belong on an unresolvable-solvency binary.

---

**Owed / BLOCKED — flagging rather than skipping:** the standing closing step (ledger upsert + `edge_classification` + `entry_plan`, re-run scanner, verify via `/api/everything`) could not run — this session has no Bash and both `knowledge_graph/cohorts.json` and the IBKR tools returned permission denials. Two consequences: (a) **the cohort narrative was never resolved** — I triaged against the issuer-specific narrative reconstructed from the tape and filings, so if the cohort thesis differs materially, the classification should be re-checked against it; (b) the dashboard write is outstanding. Both need an interactive session.