# KOO — KOOTH PLC · LSE shelf band 16-30 court · 2026-08-04 · **NOT A DRAWDOWN — 3/10**

**Identity.** Kooth plc, AIM (ISIN GB00BMCZLK30), incorporated England & Wales, reports GBP, **quotes pence (GBp)**. Shelf px 148p ties to yfinance `KOO.L` close 2026-08-04; IBKR conid 443363790 @LSE returns **live last 149.0p, `is_close: false`** — executable, not close-only. 36,032,154 shares ex-treasury → **£53.3M cap ≈ $71.7M** (FX 1.3444). Digital mental health: legacy UK NHS/local-authority service (Kooth/Qwell) plus a US state business dominated by the California DHCS "Soluna" contract. Audited data is 31-Dec-2025 — **7 months stale**, superseded by a 29-Jul-2026 H1 update.

## 1. The decisive fact — the California contract

**Runs to mid-2027; no successor exists.** AR2025 Strategic Report, "Economic environment", signed by the CEO 7-Apr-2026, verbatim: *"The California Department of Health Care Services has affirmed Soluna's status as part of California's behavioural health infrastructure, **with the current contract running to mid-2027. Kooth is engaged in ongoing dialogue with DHCS regarding the future funding pathway.**"* The 29-Jul-2026 update says Kooth "has now entered the fourth year of the contract" — a four-year term from ~mid-2023, consistent with mid-2027. **~11 months of contracted life remain on 71% of group revenue, and the successor is a "dialogue" about a "funding pathway".**

Structure, AR2025 Note 2.3, verbatim: *"The contracts include **an enforceable right by either party to terminate the contract without penalty with a fixed notice period. The contract term is therefore limited up to the end of the notice period.** The contract term is modified each month if the termination clause is not enacted…"* — the accounting term is one notice period, rolled monthly. Pricing is mixed fixed (population × expected hours) and variable (utilisation) across five IFRS-15 obligations, one of which is a contractual duty to run promotional campaigns — which is why direct marketing more than doubled to £8.1m in FY25 (FY24 £3.9m). **No grant or milestone clawback disclosed; capital commitments £nil (Note 30).** This is a binary, not a value name; everything below is secondary.

## 2. Concentration and the honesty test

| £m | FY2025 | FY2024 |
|---|---|---|
| California contract | **44.99** | 48.60 |
| … % of group | **71%** | 73% |
| Other US (NJ + counselling) | 1.10 | 0.10 |
| UK (NHS / local authority) | 17.20 | 18.05 |
| **Group** | **63.29** | 66.74 |

AR2025 Note 4 plus the auditor's Key Audit Matter, which names "Revenue recognition from significant contract (2025: £44.9m)" as one of the most significant assessed risks of material misstatement **due to fraud and error**.

**Honesty grade: ELEVATE on takeaway-divergence.** The 71% datum *is* disclosed. But **Principal Risks and Uncertainties lists seven risks — safeguarding, system stability, laws/regulation, cyber, people, public discourse, economic environment — and contains no customer-concentration or contract-renewal risk at all.** The mid-2027 expiry appears only inside a paragraph opening *"the macroeconomic environment remains favourable and funding stability is expected"*. Meanwhile the strategy narrative asserts the "State Alliance Model … **reduces customer concentration risk** and deepens the institutional relationships that underpin the long-term durability of our contracts", supported by "3 US states contracted". The actual diversification is **£1.1m of non-California US revenue plus a $2.6m first-year Michigan contract — together ~4-5% of the California line.** ~17 Michigan-sized wins would be needed to replace it. Marketed takeaway ≠ data. Graded on divergence, not on whether the datum is somewhere in the notes.

## 3. Segment decomposition — and why it cannot be read straight

AR2025 Note 4, adjusted EBITDA by segment: **US £2.79m on £46.09m revenue (6.1%)**, FY24 £2.47m on £48.70m (5.1%); **UK £8.53m on £17.20m (49.6%)**, FY24 £13.29m on £18.05m (73.6%). Read literally: the 73%-of-revenue US "growth story" earns a 6% margin, the "low-growth legacy UK" carries all the profit, and the entire £4.4m group EBITDA fall came from the UK leg. **Do not read it literally.** A 50-74% EBITDA margin on labour-intensive counselling is not economic. Non-current assets are £9.04m UK vs £0.12m US — the Soluna platform IP sits in the UK entity (Kooth Group Ltd, "platform development") and is recharged to the US, so the UK segment contains intra-group build margin and its £4.8m fall is most plausibly the California build taper (FY25: "£2m reduction in California revenue from lower contractual product development activity"; H1-26: "planned tapering of California product development revenue"). **Conclusion: the segment split is a legal-entity / transfer-pricing view, not an economic one, and the standalone profitability of the UK NHS business is UNVERIFIABLE from published disclosure.** What is verifiable: UK revenue declining ~4%/yr (£18.05m → £17.20m), £1.4m of churn from unfunded pilot contracts, offset by 14 new contracts and DWP work, renewal uplift improving to 54% (from 45%).

## 4. Latest trading — the trajectory has inflected

29-Jul-2026 H1 update (to 30-Jun-2026): revenue **£30.8m** (H1-25 £32.1m), down on California product-development taper plus £0.7m FX, part-offset by Michigan; adjusted EBITDA **£5.0-5.4m** vs **£1.6m**; unaudited net cash **£23.1m** (H1-25 £15.3m); 187,000 California registrations, ahead of target. H1 results due September 2026. Revenue still eroding, profit recovering hard — the FY25 audited snapshot the screen uses is the trough, not the run-rate.

## 5. Screen-corruption battery — every check

1. **Securities-as-cash / net-cash sign — N/A and reconciled.** `st_investments` null. Filer: cash £21.580m, **zero borrowings**, net cash £21.580m. Screen `ncash_r` +0.405 **CONFIRMED**; now £23.1m.
2. **Pension by hand — NONE.** AR2025 discloses a **defined contribution** plan only; no DB scheme, no surplus in equity, no deficit for EV. No P/B adjustment needed.
3. **Share count — RESOLVED.** Share capital £1,835k → 36.70m issued; 662,529 treasury acquired FY25 (+9,250 FY24) → 36.03m ex-treasury. The 2% four-way divergence is treasury plus option exercises, not dual class or vintage drift.
4. **Trough anchor / `ebit_vs_peak` 0.44 → melting — CONFIRMED as history, misleading forward.** Operating profit £3.392m FY25 vs £9.156m FY24: real. But FY24 was inflated by one-off Soluna platform-**build** revenue (capitalised dev £6.9m FY24 → £4.4m FY25, "substantially completed in the prior year") and H1-26 EBITDA is +3x. The flag is measuring a completed build cycle. Dock the screen, not the company.
5. **Commodity frame — N/A.** Not a producer or energy-services name.
6. **Committed capex — CONFIRMED CLEAN.** Note 30: **capital commitments £nil (2024 £nil).** (FCF yield 2.1% is not load-bearing anyway.)
7. **Trust-safe / customer cash — TESTED, PASSES.** Contract liabilities (deferred income) **£1.553m** (2024 £3.781m) — 7% of cash. Net cash net of customer money ≈ **£20.0m, ~38% of cap**. Exposure runs the other way: **contract assets £3.040m (2024 £0.292m), which the auditor states relate entirely to California** — £3.0m of revenue recognised but unbilled to the concentration customer, up nine-fold in a year.
8. **Path — docked.** +48% off a 100p low of 23-Mar-2026 (133 days), −15.7% off the 175.5p high of 26-May-2026, +10.4% 3m, −6.9% 1y. Not fresh-low, not at the high; the <90-day rule does not trigger, but half the round trip off the low is already banked — a mid-recovery entry. (IBKR intraday 52w range 97-187.5p vs close-basis 100-175.5p; consistent.)
9. **Staleness — 7 months, and materially superseded.** The 29-Jul-2026 update changes both EBITDA (+3x) and net cash. Court on the update, not the row.
10. **Friction — 0% stamp (AIM, SDRT-exempt since Apr-2014) + half of a 462bp touch (148/155) = 231bp in, ~462bp round trip** before impact. Near the worst in the band. **Kooth pays no dividend**, so the 0% UK withholding holding-edge is worth exactly zero here — only the friction is real.
11. **PFIC — SCREEN ERROR, and the correction is the most useful item in this court.** The row flags "asset-test FAIL (passive 55%)" — that 55% is **book** assets (£21.58m cash / £39.26m total). §1297(e) requires a listed foreign corporation to run the asset test on **fair market value**, and the row's own `pfic_fmv_share` is **0.354**. The income test is not close either: interest £0.718m on £63.3m gross (~1%). **Not a PFIC at 148p.** **Now solve for the trip price:** £23.1m ÷ (0.3603 × price + £7.7m liabilities) ≥ 0.5 → **price ≤ ~107p**. Below ~107p Kooth flips into likely-PFIC territory on the FMV test — **it was almost certainly a PFIC at its 100p March low.** The de-rate manufactures the status, exactly the intake's mechanism. For a US taxable account: **the price at which the balance sheet makes this "cheap" is the price at which it becomes tax-toxic.** QEF needs issuer cooperation an AIM microcap will not give; the mark-to-market fallback rests on AIM qualifying as a "qualified exchange", itself not free of doubt. Hard kill on averaging down.
12. **Offer period / tender — none.** `in_offer_period` false, no `.TEN` line at IBKR. `pe_bid_sector` is the 38%-of-shelf noise flag; ignored.

## 6. Cause-check — the March low and the May high

The de-rate is a **2025 event**: 157.5p (29-Aug-25) → 100p (23-Mar-26), −36% over seven months. Dated cause: **23-Sep-2025 H1-2025 results** — adjusted EBITDA £1.6m vs £7.8m and a statutory **operating loss of £2.1m** on front-loaded California marketing. The 22-Jan-26 Michigan win and 28-Jan-26 update ("adjusted EBITDA ahead of market expectations", consensus £9.5m) bounced 107p → 138p, then it bled back to 100p by 23-Mar **with no RNS on or near that date**. **Verdict on the low: no single-RNS cause — the tail of the H1-25 profit collapse in a thin tape.** The May high does have a candidate: the **19-May-26 Annual Report** (137.5p) → 153.5p on 20-May → 175.5p on 26-May, +28% in five sessions, CCO appointment 21-May. The annual report is where the "contract running to mid-2027 / DHCS affirmation" sentence first appears — the market re-rated on contract *visibility*. **PLAUSIBLE, not confirmed**; no broker note or dated news item pins it.

## 7. Findings

| Claim | Source | Result | Status |
|---|---|---|---|
| California contract runs to mid-2027; successor only a "dialogue" | AR2025 Strategic Report | Verbatim | **CONFIRMED** |
| "Fourth year of the contract" as of mid-2026 | RNS 29-Jul-2026 | Consistent with mid-2027 expiry | **CONFIRMED** |
| Either party may terminate without penalty on notice | AR2025 Note 2.3 | Term = one notice period, rolled monthly | **CONFIRMED** |
| Largest customer 71% of FY25 revenue (FY24 73%) | AR2025 Note 4 + auditor KAM (£44.9m) | Exact | **CONFIRMED** |
| Principal Risks omits concentration / renewal | AR2025 Principal Risks (7 listed) | Omission verified | **CONFIRMED** |
| Screen net cash +40% of cap | Cash £21.580m, borrowings nil | Reconciles exactly; £23.1m at 30-Jun-26 | **CONFIRMED** |
| The cash is customer money | Note 20: contract liabilities £1.553m | 7% of cash — it is shareholder cash | **REFUTED** |
| Capital commitments earmark the cash | Note 30: £nil (2024 £nil) | Clean | **REFUTED** |
| Hidden DB pension in equity | AR2025: defined contribution only | No DB scheme | **REFUTED** |
| Capitalised development inflates EBIT | Additions £4.381m (**6.9% of revenue**); carrying £10.124m → £8.464m ⇒ **amortisation ≈ £6.0m (9.5% of revenue)** | Amortisation now **exceeds** capitalisation — EBIT is not flattered | **REFUTED at EBIT** |
| "Adjusted EBITDA" is a fair cash proxy | Adj EBITDA £11.33m vs CFO £5.55m vs **FCF £1.10m**; cash £21.84m → £21.58m | Overstated by ~£6.2m D&A + £1.1m SBC; cash went backwards | **CONFIRMED (gap is real)** |
| PFIC — asset test fails | `pfic_fmv_share` 0.354; passive income ~1% | Not a PFIC at 148p; likely one below ~107p | **SCREEN ERROR (corrected)** |
| EBIT 0.44x peak = melting | £3.392m vs £9.156m; H1-26 EBITDA +3x | True history, stale forward | **PLAUSIBLE / stale** |
| UK segment is the profit engine | Note 4: £8.53m EBITDA on £17.20m revenue | 50% margin ⇒ intra-group recharge, not economic | **UNVERIFIABLE** |
| 2024 California procurement-ethics controversy involved Kooth | California Healthline headlines Oct-2024 ("A California Official Helped Save a Mental Health Company's Contract. It Flew Him to London"; agency director resigned) surfaced under Kooth queries; article bodies unreachable | No retrievable text names the company | **UNVERIFIABLE — top gap** |

## 8. Valuation, scenarios, and the market-implied check

EV = £53.3m cap − £23.1m net cash = **£30.2m**; FY25 EBIT £3.39m → 8.9x on the trough. FY26E revenue ~£61m, adjusted EBITDA ~£12-14m, less D&A ~£6.2m and SBC ~£1.1m → **EBIT ~£5-7m → EV/EBIT 4.3-6.0x.** Genuinely cheap — *if* the revenue base exists after mid-2027.

- **Bear (p 0.35) — 100p.** No successor, or a re-procurement Kooth loses. Revenue → ~£20m (UK + NJ/Michigan), adjusted EBITDA £3-4m, EBIT ~nil after stranded US cost and restructuring. ≈ net cash ~72p + a shrinking UK book at ~30p, discounted as a broken AIM story.
- **Base (p 0.45) — 172p.** Successor agreed but re-scoped and cheaper — the natural read of "future funding pathway" once the build is done and targets met. FY27 revenue ~£45-50m, adjusted EBITDA ~£11m, EBIT ~£5m; 7x EV/EBIT + ~£27m cash.
- **Bull (p 0.20) — 278p.** Renewal on comparable terms, Michigan/NJ scale, Soluna UK launch. FY27 revenue ~£65m, EBIT ~£8m; 9x + ~£28m cash.

**E[FV] ≈ 168p vs 148p = +13.5% gross, ~+11% after the 231bp entry.** Holding bull at 20%, the live 148p solves to **p(bear) ≈ 0.63** — the market already prices a ~63% chance of non-renewal or major re-scope. The "edge" is nothing more than *"I think renewal odds are 45% not 37%."* Nothing primary discriminates: no RFP, no DHCS budget line, no successor award, and the one governance item that would move the number is unverifiable. **No edge — a fairly-priced binary.**

## 9. Execution

Friction **231bp in / ~462bp round trip**, no dividend so the 0% WHT edge is worth zero. Median ADV **$92k**; 20%-of-prints cap = **$18.4k/day max order**; IBKR showed 4,500 shares (~$9k) traded at snapshot — thinner than the median. A 0.75% position ($24,750 ≈ 12,440 shares at 148p) takes **~1.4 sessions to build and ~1.4 to exit in a normal tape, 3-5 in a stressed one** — precisely when you would want out. **Executability verified; capacity is not.**

## 10. Kills

1. **No successor contract announced by 31-Mar-2027** (≈3 months of contracted revenue left) — exit regardless of price.
2. **Any RNS disclosing DHCS termination notice, scope reduction, or competitive re-procurement** — immediate exit.
3. **Price below ~107p** — a *tax* kill, not a dip: the FMV asset test likely makes this a PFIC for a US taxable holder. Never average down into it.
4. **Contract assets rising again from £3.040m** at the September interims — nine-fold growth in a year on a shrinking contract is a collection-timing tell.
5. **UK revenue declining faster than 4%/yr** at the September interims — that removes the floor the bear case rests on.

## 11. Ruling — NOT A DRAWDOWN (frame-reject), 3/10

Kooth is not a quality-at-own-history discount. It was a genuine **DERAILMENT** through 2025 (revenue −5%, EBIT −63%, adjusted EBITDA −29%) that has since inflected — H1-26 EBITDA tripled — and the tape has already paid for that, +48% off the March low. What remains is **a single-contract binary expiring in ~11 months**, priced at roughly a 63% chance of the bad outcome, which is about where an outsider with no procurement visibility should price it. The balance sheet is clean and genuinely verified (net cash £23.1m, nil commitments, no DB pension, £1.6m deferred income, capital-light, amortisation now exceeding capitalisation) — but a clean balance sheet is the *bear case's floor*, not a reason to own the equity. Against it: a 462bp round trip, $18k/day of capacity, a narrative claiming concentration is mitigated by contracts worth 4% of the concentration, a Principal Risks section that omits the only risk that matters, and a de-rate path that manufactures PFIC status for this account below ~107p. **Pass. Re-court the day a successor is announced — the information, not the price, is the gate.**

**Freezable:** KOO | 2027-06-30 — "Kooth announces a signed successor or extension of the California DHCS contract effective beyond mid-2027, on or before 30-Jun-2027." **our_p 0.45** (market-implied ~0.37).
