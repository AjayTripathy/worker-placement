# FNF — 10-Q CURE VERIFICATION

**Pack:** FNF-10QCURE | due 2026-08-14
**Prior record:** FNF_TRAP_VERIFY_202608110452 / FNF_COURT_RED_202608110913 / FNF_COURT_BLUE_202608111631
**Status entering this pack:** RP_FAIR badge REVOKED (red 7/10, blue SUSTAINED 8/10). Position: 210 sh, avg $48.005, HOLD / no adds / no band, pending a primary read of the Q2-26 10-Q that three benches were blocked from by sec.gov 403s.

**The 403 wall is down.** Every number below was pulled from the filings themselves via the full-fingerprint fetcher (`desk/sec_fetch.py`), not from vendor summaries or the earnings release. Both court benches, and every prior session on this name, worked without these documents.

**Live price at write-up:** $49.40 (bid 49.37 / ask 49.41, live two-sided, not a close), +0.88% on the day, prior close $48.97, indicated yield 4.17%. Position is +2.9% over break-even.

---

## PRIMARY SOURCES READ

| Document | Accession | Why it mattered |
|---|---|---|
| FNF Q2-2026 10-Q (`fnf-20260630.htm`) | 0001331875-26-000073 | Title dividend capacity, reserve roll-forward, F&G dividends received, segment splits |
| FNF FY-2025 10-K (`fnf-20251231.htm`) | 0001331875-26-000026 | **Schedule II parent-company-only statements** — the decisive document nobody had read |
| FNF Q1-2026 10-Q (`fnf-20260331.htm`) | 0001331875-26-000042 | Capacity draw-down rate |
| FNF DEF 14A 2026-04-29 | 0001104659-26-051485 | Actual F&G ownership percentage |
| F&G Q2-2026 10-Q (`fg-20260630.htm`) | 0001934850-26-000085 | F&G-only debt, preferred terms, F&G insurer dividend capacity |
| F&G FY-2025 10-K (`fg-20251231.htm`) | 0001934850-26-000026 | Multi-year F&G insurer dividend history |
| **F&G 8-K dated 2024-01-12** (Item 3.02) | 0001934850-24-000005 | **Who actually holds the mandatory convertible** |

---

## CURE ITEM 1 — Statutory title-subsidiary upstream dividend capacity

**Claim under test:** title underwriters can upstream ≥ ~$600M/yr to the holdco.

| | |
|---|---|
| **Source** | FNF 10-K FY2025, Item 1 (Regulation) and Item 7 (Liquidity and Capital Resources); FNF 10-Q Q1-26 and Q2-26, Liquidity |
| **Found** | 10-K: *"During 2026, our title insurers can pay or make distributions to us of approximately **$437 million**, without prior approval"* — and, separately, *"We anticipate that our title insurance subsidiaries will pay or make dividends to us in 2026 of approximately $437 million."* Combined statutory capital and surplus of the title insurers $1,273M (12/31/25) vs $1,223M (12/31/24). Combined statutory net earnings $488M (2025), $587M (2024), $503M (2023). Restricted net assets $1,141M. Draw-down through the year: Q1-26 10-Q says $349M remaining, Q2-26 10-Q says **$260M** remaining — i.e. ~$88M taken in Q1 and ~$89M in Q2, a ~$355M/yr pace running *below* the $437M ceiling. |
| **Verdict** | **The literal bar FAILS — $437M, not $600M. But the bar was pointed at the wrong perimeter, and the underlying question clears.** |

**Why the metric was mis-specified.** The regulated title underwriters are only one of the holdco's funding channels. FNF's own language, in both the 10-K and the 10-Q, is explicit: *"Our underwritten title companies and non-insurance subsidiaries are not regulated to the same extent as our insurance subsidiaries."* ServiceLink, the underwritten title companies, and the escrow operations sit outside the insurance perimeter and upstream without a statutory cap. For scale: the title segment booked $694M of escrow, title-related and other fees in Q2-2026 alone.

**The audited answer, from Schedule II (parent-company-only) — the statement no bench had read:**

| FNF holdco (parent only) | 2025 | 2024 | 2023 |
|---|---|---|---|
| Net cash transfers from subsidiaries | **$888M** | $703M | $689M |
| Cash dividends received from title underwriters and F&G (Note D) | $0.6B | $0.6B | $0.4B |
| Dividends paid to FNF shareholders | $(546)M | $(532)M | $(500)M |
| Cash interest paid (Note C) | $(73)M | $(73)M | $(73)M |
| **Coverage of dividend + interest by subsidiary transfers** | **1.43×** | 1.16× | 1.20× |

Three consecutive years of subsidiary cash transfers above the ~$600M level the bar was reaching for, verified from audited parent-only statements rather than inferred. Holdco liquidity at 12/31/25: cash $396M + short-term investments $262M = **$658M** (the $457M figure carried in the court record does not tie to any parent-only line in the filing).

**One honest caveat.** Holdco cash *fell* $138M in 2025 ($534M → $396M) because FNF layered $251M of buybacks and a $151M open-market purchase of F&G common on top of the dividend. The base dividend and interest are covered 1.43×; the discretionary layer on top ran modestly ahead of upstream cash. That is a capital-allocation choice against a $658M liquidity stack, not a funding stress.

---

## CURE ITEM 2 — Holdco-only versus F&G debt

**Claim under test:** the $4.4B consolidated debt figure overstates what FNF the holdco actually owes.

| | |
|---|---|
| **Source** | FNF 10-K Schedule II, Note B (parent-company-only notes payable); F&G Q2-2026 10-Q, Note L (Notes Payable); FNF Q2-2026 10-Q balance sheet |
| **Found** | **FNF holdco only, 12/31/25: $2,132M** — 4.50% Notes due 2028 $448M; 3.40% Notes due 2030 $646M; 2.45% Notes $596M; 3.20% Notes due 2051 $445M; revolver $(3)M. **F&G only, 6/30/26: $2,239M carrying / $2,270M principal** — 7.40% Senior '28 $500M; 6.50% Senior '29 $550M; 6.250% Senior '34 $500M; 7.95% Senior '53 $345M; 7.300% Junior Subordinated '65 $375M. FNF consolidated at 6/30/26: $4,378M. Segment interest expense confirms the split independently: F&G $41M/qtr, Corporate and Other $20M/qtr. F&G's notes are guaranteed by *F&G's own subsidiaries*, not by FNF. |
| **Verdict** | **CLEARS FAVORABLY.** |

Holdco debt is **$2.13B, not $4.38B** — the consolidated figure overstates the parent's obligation by ~105%. Against $658M of holdco cash and short-term investments, net holdco debt is ~$1.47B, carrying $73M/yr of cash interest, with nothing maturing before the 4.50% notes in 2028. Any leverage or EV framing struck off the consolidated $4.4B is wrong for an equity holder at the FNF level.

---

## CURE ITEM 3 — Claims-reserve development direction

**Claim under test:** is title reserve development favorable or adverse?

| | |
|---|---|
| **Source** | FNF Q2-2026 10-Q, Note B (Summary of Reserve for Title Claim Losses); FNF 10-K FY2025, Critical Accounting Estimates (three-year loss development table) |
| **Found** | **1H-2026:** provision $140M, **100% current-year, prior-years nil**; rate 4.5% of title premiums, unchanged; reserve $1,700M → $1,715M; prior-year claims paid $115M vs $125M in 1H-2025 (declining). **FY 2025 / 2024 / 2023 development table:** prior-year provision **$0 in all three years**; rate 4.5% current-year and **0.0% prior-years in all three years**. Recorded reserve $1,700M at 12/31/25 sits **$34M above the midpoint** of the actuarial range ($1.5B–$1.9B) — versus $61M above at 12/31/24. Open claim inventory 8,300 → 8,500. Sensitivity: 1pp on the provision rate ≈ $58M/yr; a 10% reserve move ≈ $170M. |
| **Verdict** | **CLEARS — no adverse development. Direction favorable-to-neutral, with one watch item.** |

Zero prior-year reserve strengthening across 3.5 consecutive years, at a flat 4.5% rate, is about as clean as a title book reads. Two things belong in the file rather than buried: (a) the conservatism cushion above the actuarial midpoint **eroded from $61M to $34M** year over year — not a charge, but less room to absorb a surprise before one is required; (b) FNF discloses that policy years 2023–2024 show *"increased levels of early reported and paid claims,"* mostly wire and real-estate fraud, which it correctly characterises as short-tail and offset by positive development on 2022-and-prior. Both facts are stated plainly by the company; neither is hidden.

---

## CURE ITEM 4 — F&G 6.875% Series A Mandatory Convertible Preferred

**Claim under test (blue bench):** *"mandatory conversion into FG common will mechanically dilute FNF below 72% — hits both the SOTP stub math and future upstream cash."*

| | |
|---|---|
| **Source** | **F&G 8-K filed 2026-01-16, event date 2024-01-12, Item 3.02 (Unregistered Sales of Equity Securities)** and its EX-99.1 pricing announcement; F&G Q2-2026 10-Q, EPS note and Dividends note; FNF 10-K Schedule II parent-only cash-flow statement |
| **Found** | The 8-K, verbatim: *"F&G Annuities & Life, Inc. issued and sold in a private placement **to Fidelity National Financial**, the owner of approximately 85% of the Company's shares of common stock, 5,000,000 shares of 6.875% Series A Mandatory Convertible Preferred Stock... for an aggregate purchase price of $250 million in cash."* Independently corroborated on FNF's side: Schedule II parent-only cash flows show *"Purchase of F&G preferred stock (250)"* in the 2024 column. Terms: liquidation preference $50.00/sh; mandatory conversion **January 15, 2027**, into **0.9456 to 1.1111** F&G common shares per preferred share; 5,000,000 shares outstanding. |
| **Verdict** | **REFUTED — the mechanism runs the opposite direction. Blue's finding is wrong on both the sign and the starting point.** |

**FNF is the holder.** This is an intercompany instrument, privately placed from subsidiary to parent, approved by a special committee of F&G's independent directors with Barclays and Sullivan & Cromwell advising. On 1/15/2027 F&G will **issue 4.73M–5.56M new common shares to FNF**. Running it against the actual share count (F&G had 130,935,209 shares outstanding at 7/31/26; FNF holds ~91.7M):

- Pre-conversion: 91.7 / 130.9 = **70.0%**
- Post-conversion: 96.4 / 135.7 to 97.3 / 136.5 = **71.0% – 71.3%**

Conversion is **accretive to FNF's stake by roughly 1.0–1.3 points.** It cannot dilute FNF below 72% because FNF is not at 72% — it is at 70%, and the instrument moves it *up*.

**The 72% premise was itself stale.** DEF 14A filed 2026-04-29: *"on December 31, 2025, we distributed an additional 16,280,204 shares of F&G common stock, representing approximately 12% of the outstanding shares of F&G, to our shareholders... **We continue to control F&G through our 70% ownership interest.**"* Both benches carried 72% forward; the Second F&G Distribution had already taken it to 70%.

**The one genuine negative, and it is small.** After conversion FNF stops receiving the preferred coupon — $0.8594/qtr × 5M shares = **$17.2M/yr** — and instead picks up common dividends on the new shares, ~$4.7M–$5.6M/yr at the current $1.00 annual rate. Net cash to the holdco falls ~**$11.6M–$12.4M/yr from 2027**, roughly 2% of holdco upstream. Worth a line in the model; not a thesis input.

---

## VERIFICATION OF BLUE'S ~$94M/yr F&G-DIVIDEND LEG

| | |
|---|---|
| **Source** | FNF Q2-2026 10-Q, MD&A, Corporate and Other segment discussion; cross-checked to F&G Q2-2026 10-Q financing cash flows |
| **Found** | FNF's own words: *"Interest and investment income includes **dividends received from F&G of $28 million and $56 million in the three and six months ended June 30, 2026**, respectively, and $28 million and $56 million in the three and six months ended June 30, 2025... The dividends received from F&G are eliminated upon consolidation."* Build-up: 70% × 130.9M sh × $1.00/yr = $91.7M common **+ $17.2M preferred = $108.9M**, against the $112M/yr the MD&A run-rate implies. Ties to F&G's side: F&G reports *"dividend payments of approximately $75 million"* in 1H-26 to all holders = $65.5M common + $8.6M preferred = $74.1M. |
| **Verdict** | **CORRECTED UPWARD — the leg is ~$112M/yr, not $94M.** Blue understated it ~19% by using a stale 72% ownership and by omitting the preferred coupon entirely. |

**But a structural finding blue did not reach, which cuts the other way.** F&G's operating insurer cannot fund this dividend. From F&G's 10-K and repeated in its Q2-26 10-Q: *"FGL Insurance did not pay dividends to its parent, Fidelity & Guaranty Life Holdings, Inc., for the years ended December 31, 2025, 2024, and 2023... it is estimated that **FGL Insurance's maximum ordinary dividend capacity for 2026 is $0**."* The $112M reaching FNF is paid out of F&G's *holding-company* balance sheet — $2,103M cash, $545M short-term investments, $750M undrawn revolver, $200M FNF credit facility — not out of regulated insurance earnings. It has been stable at $28M/qtr for two-plus years and F&G raised its common rate from $0.22 to $0.25, so the track record is good; but this leg is discretionary and balance-sheet-funded, with no statutory capacity behind it.

**And the pressure on it is building, visibly.** From the same filings: F&G segment pre-tax **loss of $(94)M** in Q2-26; FGL Insurance statutory capital and surplus **$1,735M → $1,384M (−20%) in six months**, on statutory net losses of $(85)M for 1H-26; the benefit of prescribed and permitted accounting practices to surplus fell from $249M to $50M; and F&G discloses that without permitted practices, Corbeau Re's risk-based capital *"would have fallen below the minimum regulatory requirements."* If any leg of this structure is going to break, it is this one — not the mandatory convertible.

---

## BOTTOM LINE

**The cure moves toward RESTORE, not EXIT. Nothing found points to EXIT.**

| Cure item | Bar | Found | Result |
|---|---|---|---|
| 1. Title-sub upstream capacity | ≥ ~$600M/yr | $437M regulated; $888M actual holdco transfers (2025) | Literal metric short; **substance clears at 1.43× coverage** |
| 2. Holdco vs F&G debt | Split it | Holdco $2.13B / F&G $2.24B | **Clears favorably** — consolidated figure overstates parent debt ~105% |
| 3. Reserve development | Not adverse | Zero prior-year development, 3.5 yrs, rate flat 4.5% | **Clears favorably**; cushion erosion $61M→$34M is a watch item |
| 4. MCPS terms/timing | Quantify dilution | Held **by FNF**; converts 1/15/27; **accretive** 70.0%→~71.2% | **Clears — blue's finding refuted** |
| Bonus: F&G dividend leg | Verify $94M | **$112M/yr**, but zero statutory capacity behind it | Corrected upward; new structural caveat logged |

**On the badge.** Three of the four grounds on which RP_FAIR was revoked are now retired on primary evidence: the dividend is genuinely covered (1.43× from audited parent-only statements, not from consolidated adjusted EPS), the balance sheet is materially better than the consolidated optic, and the reserve is clean. The fourth ground — the **stub multiple**, self-declared UNVERIFIED and annualized off a seasonally strong quarter — is untouched by this pack, because it was not one of the four items.

That distinction is the whole call. RP_FAIR's bar is *fairness verified*. What this pack verified is **safety**, not **fairness**. I would restore the position from UNCLASSIFIED HOLD to a defensible carry hold and permanently retire the balance-sheet and dividend-durability objections; I would **not** restamp RP_FAIR until red's remaining cure item — a seasonality-weighted FY-26 title net that puts the stub at or under ~10× on a FAF-equivalent basis — is actually run. Restoring the badge on safety evidence would repeat the original error in the opposite direction.

**Honesty read on the issuer, which is separate from the verdict on the thesis.** Every fact that could have embarrassed FNF is disclosed in plain text in its own filings, unhedged: the exact $437M title capacity, FGL Insurance's $0 dividend capacity three years running, the 20% statutory surplus decline, the shrinking reserve cushion versus the actuarial midpoint, and Corbeau Re's RBC dependence on permitted practices. Nothing required inference to find; it required only that someone open the documents. The single divergence between marketing and data is the IR-deck framing of the payout ratio against consolidated adjusted earnings that include F&G income which does not upstream — a real framing defect, correctly caught by the red bench, but sitting on top of a coverage fact that turns out to be sound. **FNF grades CLEAN as a discloser.** The court's kill was a correct process kill of an *unverified thesis*; it was not, and should not be recorded as, a finding against the company.

**Position:** 210 sh, avg $48.005, live $49.40. HOLD stands. The "no adds" gate loses its balance-sheet rationale and keeps its valuation rationale.

---

### Corrections to the standing record

1. FNF owns **70%** of F&G, not 72% (DEF 14A 2026-04-29, post the 12/31/2025 Second Distribution of 16,280,204 shares).
2. The F&G→FNF cash leg is **$112M/yr**, not $94M (FNF 10-Q MD&A: $56M received in 1H-26).
3. The 6.875% MCPS is **held by FNF** and is **accretive**, not dilutive (F&G 8-K 2026-01-16, Item 3.02).
4. Holdco cash and short-term investments were **$658M** at 12/31/25 ($396M + $262M, Schedule II), not $457M.
5. Holdco debt is **$2,132M**, not the consolidated $4,378M (Schedule II, Note B).
6. FGL Insurance has **$0** ordinary dividend capacity for 2026 and paid nothing to its parent in 2023, 2024 or 2025 — the F&G dividend is holdco-funded (F&G 10-K; F&G 10-Q Liquidity).

*No ledger, queue, or classification file was modified by this pack.*
