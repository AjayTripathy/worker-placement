# CGS — CASTINGS P.L.C. | 3/10 NOT-A-DRAWDOWN (frame-reject) | LSE shelf court, 2026-08-04

**Identity.** Castings P.L.C., LSE Main Market (SSMM), ISIN GB0001795680, UK-incorporated (0.5% SDRT).
Iron-castings foundry group founded 1835: Brownhills (30,000t) + William Lee, Dronfield (52,000t) +
Castings Ductile, Scunthorpe (7,000t, asset purchase June 2024) + CNC Speedwell machining (120+
machines). ~1,147 employees, all UK.
**Unit basis.** Quotes in **GBp (pence)**; IBKR conid 37102425 @LSE returns bars in **GBP units**
(3.00 = 300p) — both checked. Live 2026-08-04: last **300.0p**, prior close 300.0p, `is_close:false`
→ **executable line, verified**; IBKR div yield 6.13% ties to 18.40p/300p. Shares 43,632,068 issued
incl. 138,259 treasury → **43,493,809 voting**. **Cap £130.5M ≈ $175M.** Screen's `px:293` is the
*bid*, not the last — cap understated 2.4%.

## Cause-check — what actually happened
| date | event | close (GBp) | move |
|---|---|---|---|
| 2026-03-11/12 | trough of the de-rate; intraday 52w low **205p** | 221–230 | — |
| **2026-06-04** | **no RNS. 37,050 sh (25x normal). Opened 260, closed 329** | 329 | **+22.3%** |
| 2026-06-17 | FY26 Final Results: PBT £10.3M vs £5.6M; *"PBT in line with market expectations"* | 328 | +0.9% |
| 2026-06-19 / 06-22 | volume 20,828 / 26,967 — second spike | 328/330 | — |
| 2026-07-03 / 07-20 | 52w high **339p** | 339 | — |
| 2026-07-23 | **ex-div 14.19p final** (announced 17-Jun, pays 25-Aug) | 320 | −5.3% |
| 2026-08-04 | today | **300** | −11.5% off high |

The re-rate did **not** happen on the results. It happened on **4 June, on no announcement**, and the
results 13 days later were explicitly *in line*. Leading hypothesis: a **FTSE UK index review** — FTSE
announces the June review after the close on the first Wednesday (3 June 2026); reaction day is
Thursday 4 June; effective date is the third Friday (19 June), and volume spikes again on 19/22 June.
That is the textbook two-spike index-flow fingerprint on a stock whose normal day is 1,500 shares.
**PLAUSIBLE, not confirmed** (no FTSE release reachable; WebSearch exhausted). If true, the June
re-rate is a *flow* event, not an information event, and 300p carries an index-inclusion premium.

## Path check — this is not a drawdown
IBKR raw bars (my own pull, not the screen's): 52w low **205p**, 52w high **339p**, last **300p**.
→ **+46.3% off the 52-week low**; **−11.5% off the high**; and adding back the 14.19p that went ex on
23 July, **−7.3% off the high on a total-return basis.** The screen's yfinance-derived
`pct_off_52w_low 0.305 / pct_off_hi −0.133` understates the bounce (dividend-adjusted series).
Under the brief's rule 8, a name ~7% below its 52-week high after a +46% run is **frame-rejected as a
drawdown candidate**, not valued. Late entry, and the catalyst is already published.

## The UK battery
**1. Pension by hand — the headline test. CLEAN, and in the *opposite* direction to CHH/COST.**
AR2026 **Note 5** (prelims Note 8): two DB schemes, closed to accrual 6-Apr-2009, no active members.
Obligation £29,088k; plan assets £41,087k; **surplus £11,999k** (2025: £12,233k). Then:
*"Unrecognised pension surplus (asset ceiling) **(11,999)** → Net amount recognised in the balance
sheet **—**."* Basis stated verbatim: **IFRIC 14 — "the group does not have an unconditional right to
receive returns of contributions or refunds under the scheme rules."**
→ **Book equity £127.272M contains ZERO pension surplus. No strip required. P/B 1.03 at 300p is
honest.** No deficit either, so nothing goes into EV. The dead-guard trap does not bite this name.
**Buy-in already done**: Trustees completed a **bulk annuity buy-in with Aviva on 24 March 2020**,
fully matching liabilities *except GMP equalisation*; scheme assets are £30,040k "asset held by
insurance company" + £11,743k cash. So the surplus is already locked inside an insured structure.
*Optionality, disclosed by management*: the FY26 results deck lists **"Pension buy-in to buy-out"** as
a stated opportunity. A buy-out + wind-up is the only realistic route by which £12.0M (9.2% of cap)
returns to shareholders; after the 25% UK authorised-surplus-payment charge ≈ £9.0M ≈ **20.7p/share**.
Probability and timing UNVERIFIABLE (scheme rules not public). Do not capitalise it.
**2. Capital-commitments note (the THX lesson). CLEAN.** Note 7: contracted but not provided for =
**£1,309k** (2025: £7,376k), "primarily on-going investment in the machining business" — 1.0% of cap.
The cash is **not** earmarked; the new Savelli foundry line is finished and paid for.
**3. Net cash (screen check 1). CONFIRMED against the filer.** 31-Mar-2026: cash **£17,390k** (deposits
£566k + demand £16,824k), **zero borrowings**, IFRS-16 leases £2,148k (Ductile site). Screen
`netcash 15,242` = 17,390 − 2,148, exact. Company's own line: "Net cash position 17.4 / No debt".
No securities-as-cash, no client float — the CAPD inversion is absent.
**4. Friction.** 50bp SDRT + half the 169bp median touch (84.5bp) = **~135bp all-in entry**, ~219bp
round trip. The 0% UK dividend WHT is worth ~**92bp/yr** here (6.13% yield × a 15% treaty baseline) —
unusually large on this shelf, but a *holding* edge that repays entry only after ~1.5 years.
**5. Executability and max order.** Conid 37102425, LSE, STK, live two-sided line confirmed. Median
ADV **$87k** (63-session median; ignore IBKR's 90-day *mean* of $185k — `adv_block_inflated:true`).
**Max single-day order $17.3k.** A 0.75% position ($24,750) = ~1.4 sessions to build, 3-8 to exit.
**6. Register / float.** `float_pct 0.896` — not the 100% the brief queried. Disclosed >3%:
**Threadneedle 17.05, Aberforth 15.32, Ruffer 8.91, Janus Henderson 6.60, B.J. Cooke 4.70,
NR Holdings 4.13** = 56.7%. **No family or board control block** despite the 1835 heritage. The exit
risk is the inverse of the one anticipated: **four UK value funds own ~48% of a stock trading $87k/day**
— a single redemption is the tape. Both "analysts" (Canaccord Genuity, Zeus) are the company's **joint
house brokers**; independent coverage is zero.

## Demand frame — EBIT *is* the European truck cycle
**Commercial vehicle = 71% of revenue** (FY25 76%), automotive 5%, other 24%. Destination: Sweden
£49.6M (28.7%), UK £33.2M (19.1%), Germany £26.2M (15.1%), Netherlands £24.6M (14.2%), rest of Europe
£25.9M, Americas £13.0M (7.5%); 81% exported. **Customer concentration is fully disclosed** (deck
slide 16 + AR Note 2): top-4 CV customers **A 27% / B 18% / C 11% / D 7% = 63%**; Note 2 gives three
ultimate customer groups at £53,496k / £30,957k / £19,383k of foundry revenue, unnamed — the
Sweden/Netherlands/Germany split makes Volvo, PACCAR-DAF and Daimler/Traton the obvious candidates
(PLAUSIBLE only). **One customer is ~27-31% of the company.**

| FY (to 31-Mar) | 23 | 24 | 25 | 26 |
|---|---|---|---|---|
| Revenue £M | — | **224.4** | 177.0 | 173.2 |
| Profit from operations £M | 16.4 | **19.8** | **4.8** | 10.0 |
| Foundry sales weight ex-Ductile (t) | 53,100 | 50,450 | 40,100 | **40,017** |
| ROCE (EBIT / net assets less cash) | — | ~19.5% | 4.3% | **9.1%** |

Decomposition: FY24→FY25 revenue −£47.4M drove EBIT −£15.0M — a **31.6% incremental drop-through**.
The FY25 trading statement (18-Feb-2025) states it plainly: *"underlying demand for heavy trucks
(approximately 75% of group revenue) was down 20% on the previous year."* European heavy-truck
registrations peaked at **344k in 2023**; Volvo's estimate for **2026 is 310k** (deck slide 5) — ~10%
below peak, exactly the "10% below normalised trend" the OEMs told the company. **~100% of the EBIT
swing is volume × operating leverage.** The FY26 recovery is likewise not operational: like-for-like
volume was **flat** (40,017t vs 40,100t; the +1.2% headline is entirely the acquired Ductile business,
disclosed), and the £5.2M EBIT increase decomposes into a £1.5M electricity-penalty non-repeat, a
£1.3M Ductile loss reversal, and a **£1.179M RDEC credit sitting inside operating profit of which only
£0.4M relates to the current year** (a 2-year catch-up = 7.8% of reported EBIT, non-recurring).
**Ruling on the frame: the multiple is a cycle-position statement, not a value statement.** 11.6x
EV/EBIT on the *second* year off a trough at 9% ROCE is not cheap — it is what a mid-cycle industrial
should cost. **Utilisation is 41,500t sold against ~80,000t of sales capacity = 52%**; the latent
operating leverage is enormous both ways and the capex to serve it is already spent.
**EV-transition test.** The company discloses the impaired slice itself: *"c. 30% of group revenue
arises from the supply of cast iron powertrain components."* The rest of the CV revenue is
chassis/axle/driveline hardware that survives electrification, and near-term the direction is a
**tailwind** — the AR states US and EU emissions-target deferrals *extended* diesel HDV lifecycles,
and the deck ranks heavy trucks "last on the list". Verdict: **a real ~30% terminal-value haircut on
a 2030s fuse, not a near-term impairment** — but a legitimate reason to hold the terminal multiple
below a generic industrial's.

## Findings table
| claim | source | result | verdict |
|---|---|---|---|
| DB scheme surplus inflates book equity (CHH/COST pattern) | AR2026 Note 5, prelims Note 8 | £11,999k surplus **fully unrecognised** under IFRIC 14; net BS amount NIL | **REFUTED — P/B is honest** |
| Scheme bought in / bought out | AR2026 Note 5 | Aviva bulk annuity **buy-in 24-Mar-2020**; buy-out named as a management opportunity | **CONFIRMED** |
| Net cash +12% of cap | Consolidated Balance Sheet 31-Mar-26 | cash £17,390k, zero borrowings, leases £2,148k → net £15,242k, exact match | **CONFIRMED** |
| Cash earmarked against committed capex (THX) | Note 7 Commitments | £1,309k only (prior yr £7,376k) | **REFUTED — cash is free** |
| Screen FCF yield 7.99% | Cash flow statement + deck slide 13 | FY26 FCF £10.0M includes a **£9.3M inventory release** and excludes £6.7M of capex paid in FY25. Company's own FCF: FY25 **−£7.7M**, FY26 +£10.0M. Ex-working-capital FY26 FCF = **£3.3M = 2.5% yield** | **REFUTED — screen error** |
| `wc_fcf: false` | same | FY26 free cash flow is 66% working-capital release | **REFUTED — flag should have fired** |
| Ordinary dividend covered | prelims Note 4 + EPS | DPS **18.40p** vs EPS **17.36p** — **0.94x cover**, second consecutive uncovered year (FY25 0.52x). Supplementary dividend **nil in FY25 and FY26** after 7p/15p/15p/15p in FY24/23/22/19 | **REFUTED — the special is already gone** |
| EBIT is the European truck cycle | FY25 trading statement; deck slides 5-7; segment note | 31.6% drop-through; registrations 344k(2023)→310k(2026E); LFL volume flat | **CONFIRMED** |
| Customer concentration disclosed | deck slide 16; AR Note 2 | top-4 = 63%; largest = 27% (£53.5M) | **CONFIRMED** |
| Family/board control of register | company substantial-shareholders page | none — 4 institutions hold ~48%; no director >3% except B.J. Cooke 4.70% | **REFUTED** |
| Share count reconciles | DTR statement / prelims Note 5 | 43,493,809 voting vs screen filing 43,476,771 vs weighted-avg basic 43,468,111; `lse_implied` 44,532,910 is +2.4% vendor drift | **CONFIRMED (no dual class)** |
| PFIC | passive assets 10.5%, active manufacturer | clean | **CONFIRMED** |
| Live/Code offer period | LSE_OFFER_PERIODS, IBKR line check | none; no `.TEN` line | **CONFIRMED** |
| Cause of the 4-Jun-2026 +22% day | Investegate RNS list (no announcement), Google News RSS, LSE page | no information event found; FTSE June-review date arithmetic + twin volume spikes fit index flow | **UNVERIFIABLE / PLAUSIBLE** |

## Valuation and scenarios (pence; price 300p; EV £115.2M; EV/EBIT 11.6x; P/E 17.3x; P/B 1.03x)
- **Bear 215p, p=0.35.** European schedules slip again (the deck's own words: "increases pushed out"),
  US tariff drag persists, Savelli-line depreciation adds fixed cost into flat volume → FY27 EBIT
  £6-7M, EPS ~11p. Uncovered 18.4p dividend gets cut; the yield support goes; ~0.75x book.
- **Base 310p, p=0.45.** The +5-10% forward schedules half-arrive; the ~50% Northern Powergrid supply
  restriction at William Lee (Apr-May FY27, transformer repaired 24-May-2026) costs Q1; FY27 EBIT
  £11-12M, EPS ~20p; ~10x EV/EBIT. Dividend held, no special.
- **Bull 420p, p=0.20.** Registrations climb back toward 344k by FY28, volumes to ~50,000t; at a 31.6%
  drop-through, +£30M of revenue = +£9.5M EBIT → ~£20M, EPS ~35p at 12x. Wind/agriculture and the
  larger-casting range add mix. Supplementary dividend restored. Capex already spent, so it drops through.

**E[FV] = 299p vs 300p → edge −0.4%.** Before 135bp of entry friction. **There is no edge.**

## Kills / re-court triggers
1. **Re-court only below 240p** (≈0.82x book, ≈8.5x EV/EBIT on normalised EBIT) *while* European HCV
   registrations remain ≥300k — i.e. a de-rate without a demand break. That is the ownable shape.
2. Kill the recovery frame if the **AGM trading statement (~21 Aug 2026** on the FY25 precedent; the
   company's calendar posts no future events) walks back the +5-10% schedule guidance.
3. Kill if the **ordinary dividend is cut** — it is already uncovered at 0.94x with cash at £17.4M
   against £14-20M/yr of capex.
4. Kill if a **top-3 customer** (27% / 18% / 11%) resources a platform or is lost.
5. Kill if the 2027 European heavy-truck estimate (Volvo/ACEA) drops below **290k**.
6. **Do not enter blind inside ~2 weeks of the late-August AGM statement.**

## Ruling
**NOT A DRAWDOWN — frame-reject**, with one named **SCREEN ERROR**. The name is 7% below its 52-week
high on a total-return basis after a +46% run off the low, and its June re-rate was most likely index
flow rather than news. The screen's two attractive fields do not survive: the **7.99% FCF yield is a
working-capital release** (two-year FCF is +£2.3M, ex-WC yield 2.5%), and **P/B 1.00 is real but not a
discount** on a business earning 9.1% ROCE. Everything the UK battery was built to catch comes back
**clean** — the pension is unrecognised (opposite of CHH/COST), the commitments note is empty
(opposite of THX), the net cash ties to the filer exactly (opposite of CAPD). This is an honest,
well-run, genuinely debt-free 190-year-old foundry — priced correctly for the middle of its own cycle.
Not a value opportunity today. **3/10.**

**Freezable call:** `CGS | 2027-06-30 | Castings' FY27 (year to 31-Mar-2027) reported profit from
operations lands BELOW £14.0M | our_p 0.72` — graded off the June-2027 preliminary results.
