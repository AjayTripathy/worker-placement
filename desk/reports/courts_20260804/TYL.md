# TYL — Tyler Technologies, Inc. (NYSE: TYL)
**Court: COURT_QUEUE_20260804, tier 1. Sat 2026-08-03 (US evening), grading for the 08-04 session.**
Queue entry: score 76.3, cap $12,513M, "-52% from own 3y high, gm 47%, rev3y 8.0%", ai_complex: false.
Prior art: none. TYL appears in neither `research_ledger.json` nor `resolution_packs.json`. No frozen call to respect.

**VERDICT: STARTER 4/10.** De-rate with a genuine, one-quarter-old growth-and-margin reset underneath it.
The franchise is intact; the growth rate is not what the old multiple was paid for; and the most recent
quarter's headline is carried by items that are not operations.

---

## 1. PRICE PREMISE — TAPE-VERIFIED

Every price below is from bars, not from the screen.

| Fact | Value | Source / basis |
|---|---|---|
| Live price | **$305.54** | IBKR contract 13116, 2026-08-03 close, `is_close: true` |
| Prior close | $309.60 | IBKR + yfinance daily, 2026-07-31 |
| 52-week high | $619.99 | IBKR misc-statistics |
| 3-year high | **$646.74 on 2025-02-13** | yfinance daily, adjusted = raw (TYL pays no dividend) |
| 3-year low | **$275.27 on 2026-06-22** | yfinance daily close |
| Drawdown from 3y high | **−52.8%** at $305.54 | computed |
| Off the 3y low | **+11.0%** | computed |
| Days since the 3y low | **42** | computed |
| YTD | −32.7% | IBKR year-to-date-change |

**Path test: PASSES, and passes for the right reason.** +11.0% off a 42-day low is inside the generator's
own exhaustion guards (>35% off a <90-day low, or >50% off any low). This is not a GWRE/PINS-style late
entry. TYL pays no dividend, so its price drawdown and its total-return drawdown are the same number —
the screen's −52% is measured on the same basis I measure it on. **No basis dispute on this name.**

One caveat the screen cannot see: TYL ran **+16.4%** from $288.16 (07-23) to $333.50 (07-29, the print day)
and has since given back $28 of it. The market bought the print for two days and then sold it. That fade is
information, and section 4 says what it is about.

---

## 2. CAUSE-CHECK — WHY THE −52%

The drawdown is not one event. It is four, and they are separable. All price moves below are close-to-close
from yfinance/IBKR daily bars.

| Date | Move | Cause | Evidence status |
|---|---|---|---|
| 2025-02-13 → 2026-01-26 | $646.74 → $439.82, **−32%** | Slow multiple normalisation off an extreme (57x trailing non-GAAP EPS) through a year in which EPS still grew 19% | CONFIRMED (bars + FY25 results) |
| **2026-01-29** | **−9.3%** to $380.00, volume 842k vs ~270k normal | Sector. No TYL 8-K on or near this date (EDGAR filing index checked: nothing between 2025-12 and 2026-02-03) | CONFIRMED no-company-event; sector attribution PLAUSIBLE |
| **2026-02-03** | **−8.5%** to $332.05, volume 1.54M | The global software de-rate on AI-tooling fear. Forbes, 2026-02-04: *"Global Software Stock Selloff — Oracle, Adobe, More — Fueled By Anthropic's New AI Tools."* TYL's own 8-K that day was the For The Record acquisition PR (a $212.5M deal — far too small to move a $16bn cap 8.5%) | CONFIRMED (the 8-K is not the cause); sector cause PLAUSIBLE-strong |
| **2026-02-11 → 02-12** | −5.9% then **−15.4%** to $287.04 on 2.53M shares | Q4-2025 print + **initial 2026 guidance**. This is the single largest one-day loss in the series | CONFIRMED (8-K 2026-02-11, Ex-99.1) |
| 2026-02 → 2026-06-22 | grind to $275.27 | continuation | — |
| 2026-07-29 → 08-03 | $333.50 → $305.54, **−8.4%** | Q2-2026 print. Price targets cut the same week: Goldman $435→$395, Piper $543→$491, Baird $455→$435, BTIG $420→$400 | CONFIRMED (8-K 2026-07-29; broker actions via news feed) |

**What the February guide actually said** (8-K 2026-02-11, Ex-99.1, verbatim): FY2026 revenue **$2.50–2.55bn**,
non-GAAP diluted EPS **$12.40–12.65**, GAAP diluted EPS $8.36–8.61, FCF margin 26–28%. Against FY2025 actual
non-GAAP EPS of **$11.31 (+19.3%)**, the 2026 guide implied **+9.6% to +11.8%**. The de-rate on 02-12 was the
market repricing a 19%-grower as a 10%-grower. That is a legitimate reset, not a panic.

Also disclosed in that guide and worth naming: transaction revenue was guided **+5–7%, "between 10% and 12%
excluding the impact of the termination of the Texas payments contract."** A named, material customer loss.

**Cause-check verdict: READ. No unknown.** Roughly half the fall is multiple normalisation off an extreme,
a quarter is an exogenous AI-narrative sector de-rate, and a quarter is a company-specific growth-rate reset.

---

## 3. MODE B FIRST — THE DECISIVE QUESTIONS, PROMOTER FRAMING STRIPPED

I derived these before reading the company's framing, and hunted for the disconfirming answer to each.

### B-1. Is the "SaaS transition rev-rec noise" (the GWRE hypothesis) real here? **NO — REFUTED.**
The parent lane asked whether TYL's reported growth is depressed by a mid-flight cloud transition, the way
GWRE's was, and whether the same FX/mix artifacts are present.

- **FX artifact: impossible.** TYL is a domestic public-sector vendor. There is no meaningful foreign
  revenue and no functional-currency mismatch. The P1-2 basis defect that destroyed the TCOM ratio cannot
  fire here.
- **Transition artifact: largely spent.** Recurring revenue is **86.7% of total** (Q2-26) and maintenance —
  the line that a cloud transition cannibalises — is only **$105.8M of $645.1M**, 16.4% of revenue, guided
  to decline 5–7%. That is a ~1 percentage-point drag on total growth, not a 5-point one. TYL is not
  mid-transition; it is ~87% through it.

**So the 8.2% is real.** There is no rev-rec cushion under it. Whatever growth rate TYL is printing is
approximately its true growth rate. This is the single most important thing the GWRE analogy gets wrong,
and it cuts against the bull case, not for it.

### B-2. Is the state/local budget fear (the "DOGE" channel) the operative risk? **NO — and this is where the house has an edge.**
Muni credit is a house competence and it applies directly.

- TYL's customers are cities, counties, courts, school districts and utilities. Their dominant own-source
  revenue is **ad-valorem property tax**, which is (a) assessed on a **lagged** roll — typically 1–3 years
  behind market value — and (b) protected on the downside by assessment caps and by the fact that levies are
  set to a budget, not to a rate. Property-tax collections have not fallen year-over-year in aggregate in any
  post-war US recession, including 2008–2011, when values fell 30%+.
- The **federal** channel (the DOGE-era cuts) barely touches Tyler. Tyler is a local/state vendor; federal is
  a de-minimis slice of the client base.
- Management's read is consistent with the house read: "Public sector demand remains healthy, reflecting
  sustained modernization priorities" (Q2-26); "generally healthy budgets that continue to drive an active
  pipeline" (Q4-25). **These claims are CONSISTENT with the underlying fiscal data**, and the record bookings
  corroborate them.

**But there IS a fiscal channel, and it is the one nobody names: ARPA.** The American Rescue Plan gave state
and local governments $350bn with an obligation deadline of Dec-2024 and a spend deadline of Dec-2026. A
large share funded exactly the kind of one-time IT modernisation Tyler sells. That money is now obligated and
running off. It is a clean, dated, mechanical explanation for why ARR growth stepped down from ~11% to ~8%
between Q4-25 and Q2-26 while "budgets remain healthy" — because budgets ARE healthy; it is the *one-time
stimulus overlay* that is gone, not the base. **This is my Mode-B answer to the "why the deceleration"
question and I have not seen it in any sell-side note in the feed. It is a hypothesis, not a verified fact —
Tyler does not disclose ARPA-funded revenue — but it is the mechanism that fits the timing.**

### B-3. Is TYL long or short the AI cycle? **SHORT the AI narrative — it is a negative-beta hedge to the house AI-BREAK call.**
The queue flags `ai_complex: false`, which is right about the revenue but wrong about the de-rate. Two of the
four legs of the drawdown (2026-01-29, 2026-02-03) are the market pricing *AI as a threat to vertical
software*. TYL does not need the AI-capex cycle to hold; a meaningful part of its multiple compression is
the market's fear that the cycle *succeeds*.

Against the frozen house call **AI-BREAK | 2027-12-31 @ p=0.45**: **the entry does NOT require the cycle to
hold, and the de-rate has already priced a piece of the break's inverse.** If the AI-capex cycle breaks, the
"AI eats vertical software" multiple compression is the first thing to reverse. Against a household already
carrying ~$5.2M / 26% AI-complex exposure, TYL is one of the few tier-1 candidates in this queue that leans
the *other* way. That is a real portfolio argument and I am not averaging it away — I am stating that it is
the strongest single reason to own this name at all.

### B-4. What is the growth rate we are actually buying? **UNVERIFIABLE, and it is the decisive unknown.**
See section 5. Reported ARR growth is 8.2%. It includes an acquisition. Organic is not disclosed.

---

## 4. MODE A — CLAIM VERIFICATION, Q2-2026 (8-K 2026-07-29, Ex-99.1)

Everything below is checked against the audited statements inside the same exhibit, not against the summary.

### The verified facts

| Metric | Q2-2026 | y/y | Q1-2026 y/y | Q4-2025 y/y |
|---|---|---|---|---|
| Total revenue | $645.1M | **+8.2%** | +8.6% | +6.3% |
| Recurring revenue | $559.5M (86.7% of total) | **+8.2%** | +10.4% | +10.9% |
| Subscriptions | $453.7M | +12.0% | +14.6% | +16.1% |
| — SaaS | $230.6M | +21.7% | +23.5% | +20.2% |
| — Transaction | $223.1M | **+3.5%** | +6.4% | +12.1% |
| **ARR** | **$2.24bn** | **+8.2%** | **+10.4%** | **+10.9%** |
| **GAAP operating income** | **$95.095M** | **−0.5%** | **+11.9%** | +4.6% |
| GAAP operating margin | 14.74% | **−130bps** | — | — |
| Non-GAAP operating income | $165.7M | +4.8% | +10.0% | +5.1% |
| Non-GAAP EPS | $3.08 | **+0.9%** | +9.3% | +7.8% |
| Adjusted EBITDA | $176.4M | +4.3% | +9.3% | +4.4% |
| Free cash flow | $118.5M | +34.7% | +112.9% | +9.7% |

Sources: 8-K 2026-07-29 Ex-99.1; 8-K 2026-04-29 Ex-99.1; 8-K 2026-02-11 Ex-99.1 (all primary).

### FINDING 1 — the GAAP headline is carried by a one-time gain, and the operating line is down. **REVIEW_FLAG.**

- **Claim:** "GAAP net income was $93.5 million, or $2.23 per diluted share, **up 10.5%**."
- **Method:** read the Condensed Consolidated Statements of Income printed in the same exhibit, line by line.
- **Authority:** TYL 8-K 2026-07-29, Ex-99.1, income statement.
- **Finding: TRUE BUT INCOMPLETE.** The same statement carries a **"Gain on remeasurement of equity
  investment" of $25,048k** in Q2-2026 and $0 in Q2-2025 — a one-time, non-operating item (Tyler held a prior
  stake in For The Record). Strip it at the 23.5% guided GAAP rate and GAAP net income is ~$74.4M, EPS ~$1.78,
  **down ~12% year over year, not up 10.5%.** Meanwhile **GAAP operating income was $95.095M vs $95.596M —
  down 0.5%.** The release states GAAP operating income **without a growth rate**, while stating a growth
  rate for every other metric in the section — including, one quarter earlier, for GAAP operating income
  itself ("up 11.9%"). The number is disclosed; the framing is selective.

This is an emphasis divergence, not a fabrication, and I grade it accordingly: **REVIEW_FLAG, not ELEVATE.**
But it is the reason the two-day post-print pop round-tripped.

### FINDING 2 — the guidance raise is financed below the operating line. **CONFIRMED.**

| Guide vintage | Revenue | Non-GAAP EPS | Net interest income |
|---|---|---|---|
| **2026-02-11** (initial) | $2.50–2.55bn | **$12.40–12.65** | $25–27M |
| **2026-04-29** | $2.535–2.575bn (raised on the FTR deal) | $12.50–12.75 | $8–10M |
| **2026-07-29** | **$2.535–2.575bn (UNCHANGED)** | **$12.95–13.20 (+$0.45 mid)** | **$19–21M (+$11M)** |

- **Method:** compare the three guidance tables verbatim; then attribute the EPS delta.
- **Authority:** the three 8-K Ex-99.1s above.
- **Finding: CONFIRMED.** The revenue guide has not moved since April. The +$0.45 EPS raise decomposes into
  (a) **+$11M of net interest income** from the May convertible proceeds ≈ **+$0.20/share after tax**, and
  (b) **share count**: February's guide assumed **44.0M diluted shares** (stated in the GAAP-to-non-GAAP
  reconciliation table); shares outstanding are now **40,952,274** (10-Q cover, 2026-07-27), down **4.7%
  since 2026-02-16** and 5.6% year-to-date per management. On a ~$12.6 base a 4% lower share count is worth
  roughly **+$0.50**. **The entire EPS raise since February is interest income plus buyback. Operating
  earnings guidance has not improved.**

That is not fraud — the buyback is real, accretive, and disclosed. But a reader who takes "we raised EPS
guidance" as evidence the operating business improved has been misled by emphasis, and the marketed takeaway
("strong execution and performance across our key financial and operational measures") diverges from the
operating data underneath it.

### FINDING 3 — where the operating leverage went. **CONFIRMED.**
From the same income statement, Q2-26 vs Q2-25: **R&D $62.8M vs $50.8M (+23.6%)**, **G&A $93.7M vs $76.6M
(+22.4%)** against revenue +8.2%. One quarter earlier the CFO attributed Q1's margin expansion to "cloud
efficiency gains and disciplined expense management." A partial mitigant is real: For The Record closed
2026-04-14, so Q2 absorbs a full quarter of an acquired cost base against a partial-quarter revenue
contribution plus deal costs. **PLAUSIBLE mitigant, not verified** — Tyler does not break out FTR.

### FINDING 4 — "SaaS revenues accelerated 21.7%". **CONSISTENT, but the weaker read.**
21.7% is above FY2025's 20.6% and above Q4-25's 20.2%, so "accelerated" is defensible on a year-over-year-rate
basis. It is nonetheless **down from Q1-26's 23.5%** sequentially. Not a misstatement. Noted, no flag.

### FINDING 5 — capital structure, pulled BEFORE any valuation claim (per standing doctrine)

| Item | Value | Source |
|---|---|---|
| Shares outstanding | **40,952,274** | 10-Q cover, 2026-07-27 |
| Cash & equivalents | $895.4M | XBRL `CashAndCashEquivalentsAtCarryingValue`, 2026-06-30 |
| Short-term investments | $74.7M | XBRL `ShortTermInvestments`, 2026-06-30 |
| Convertible notes (non-current) | **$1,408.7M** | XBRL `ConvertibleDebtNoncurrent`, 2026-06-30 |
| **Net debt** | **+$438.6M** | computed |
| Market cap @ $305.54 | **$12.51bn** | computed — matches the queue's $12,513M exactly |
| **Enterprise value** | **$12.95bn** | computed |

The May-2026 issue is **$1.4bn of 0.50% convertible senior notes due 2031**, with capped calls that raise the
effective conversion price to **$655.77**. At $305.54 the converts are deep out of the money; the capped call
neutralises dilution up to $655.77. **No hidden dilution. There is no "net cash" here — TYL is modestly net
levered, and any valuation asserting otherwise is wrong.**

### Verified valuation

| Multiple | Value |
|---|---|
| Forward P/E on FY26 non-GAAP EPS mid ($13.075) | **23.4x** |
| Forward P/E on FY26 GAAP EPS (~$8.7 est.) | ~35x |
| EV / FY26 FCF (27% of $2.555bn = $690M) | **18.8x** |
| EV / ARR ($2.24bn) | **5.78x** |
| EV / FY26 revenue | 5.07x |
| Rule of 40 (8.2% ARR growth + 27% FCF margin) | **35** |
| **Peak multiple, 2025-02-13** | **$646.74 / $11.31 = 57.2x trailing non-GAAP** |

**Stock-based comp honesty (standing rule for software):** Q2 SBC **$43.7M = 6.8% of revenue**; H1 $80.8M;
FY26 run-rate ~$170M ≈ **25% of guided FCF**. That is a real cost, and the FCF multiple above flatters TYL by
that amount. The mitigant is unusually strong: buybacks are running >$1bn annualised, **more than 5x** the SBC
cost, and the share count is genuinely shrinking 4.7% in five months. Net-net dilution is negative.

---

## 5. THE DECISIVE UNVERIFIABLE — ORGANIC ARR

**ARR growth of 8.2% INCLUDES For The Record, acquired 2026-04-14 for $212.7M in cash. Tyler does not
disclose organic ARR, and I could not derive it from any filing.**

Sizing the hole: at a 4–6x ARR purchase multiple (the normal range for a sub-scale vertical SaaS asset), FTR
carries roughly **$35–53M of ARR**. Against $2.24bn that is **1.6–2.4 percentage points**. Backing it out puts
**organic ARR growth at roughly 5.8–6.6%** — versus 10.9% two quarters earlier.

If organic ARR is ~6%, 23.4x forward earnings is not cheap; it is approximately right, and the bear case is
live. If organic ARR is ~7.5%+ and Q2 was distorted by the Texas payments termination lapping through the
transaction line, then 23.4x on a monopoly franchise is genuinely too low.

**I cannot resolve this from primary sources. UNVERIFIABLE ≠ clean.** It is the single most important number
in the name, it is the number management chose not to give, and it is the reason this is a 4 and not a 6.

### Other gaps, stated honestly
- **The June Investor Day "raised 2030 financial targets" are not in any SEC filing.** EDGAR carries no 8-K
  for the Investor Day; the only June filing (8-K 2026-06-12) is a $150M Rule 10b5-1 buyback plan. The CEO's
  Q2 reference to "our raised 2030 financial targets" is therefore **UNVERIFIED against a primary source**.
- **Next print date is ESTIMATED, not company-confirmed.** Prior-year cadence (Q3-2025 released around
  2025-10-29) implies **late October 2026**, ~12 weeks out. That is comfortably outside the two-week
  no-blind-entry window, so the rule is satisfied either way — but I have not confirmed the date with Tyler.
- FTR's standalone revenue, ARR and margin: not disclosed.

---

## 6. DE-RATE vs DERAILMENT — THE RULING

**Neither cleanly. This is a DE-RATE ON A GENUINELY RESET GROWTH RATE — the multiple fell far more than the
estimates, but the estimates did deteriorate, and the deterioration is one quarter old and unconfirmed.**

Against the HUBS/CTSH/SAP winner pattern (multiple compressed, business intact):
- **Matches:** 86.7% recurring revenue; record SaaS and total bookings; SaaS +21.7% for a 22nd straight quarter
  above 20%; FCF +34.7%; near-zero churn in a switching-cost monopoly; management buying back 5.6% of the
  company year-to-date at an average around $310 while publicly calling the stock undervalued; revenue
  guidance never cut.
- **Does not match:** ARR growth 10.9% → 10.4% → **8.2%** in two quarters, with the organic rate undisclosed
  and plausibly ~6%; GAAP operating income **down 0.5%**; GAAP operating margin **−130bps**; non-GAAP EPS
  **+0.9%** *despite* a 5.6% share-count reduction, which means non-GAAP net income **fell**; a named customer
  loss (the Texas payments contract) costing ~5 points of transaction growth.

The honest summary: **the multiple went from 57x to 23x while EPS went from $11.31 to a guided $13.08.** The
fall is ~90% multiple. But 23x is no longer an obvious mispricing for an 8%-grower whose most recent quarter
produced zero operating-income growth. The gap between "cheap against its own history" and "cheap" is exactly
the trap this queue was built to avoid, and TYL sits right on the line.

---

## 7. FOUR-IDEA FRAME

1. **The franchise is not the question.** Nothing in the Q2 data threatens Tyler's position. Public-sector
   software has the highest switching costs in enterprise software; 87% of revenue is recurring; bookings
   set records. If you are worried Tyler loses its market, you have read the wrong risk.
2. **The growth rate is the question, and the company withheld the number that answers it.** Reported ARR
   growth of 8.2% includes an acquisition. Organic is ~6%. Management has the number and did not print it.
3. **The EPS line has been detached from the operating line.** Since February, guided EPS is up $0.45 and
   guided revenue is unchanged; the raise is interest income plus buyback. Below the surface, GAAP operating
   income is flat and margins are compressing 130bps. Underwrite the operating line, not the EPS line.
4. **The de-rate is partly an AI-narrative artifact, which makes TYL a rare negative-beta line in this book.**
   Two of the four drawdown legs were the market pricing AI as a threat to vertical software. That reverses
   if the house's AI-BREAK call (p=0.45) hits. In a household already 26% AI-complex, that is the strongest
   portfolio reason to own it — and the reason a small position beats none.

---

## 8. SCENARIOS (12–18 months)

| | p | FY27 non-GAAP EPS | Multiple | FV |
|---|---|---|---|---|
| **Bear** | 0.35 | $13.60 (buyback-only growth) | 18.7x | **$255** |
| **Base** | 0.45 | $14.20 | 25x | **$355** |
| **Bull** | 0.20 | $14.65 | 30x | **$440** |

- **Bear:** organic ARR confirms at ~6%; the ARPA modernisation overlay is gone and does not come back;
  R&D/G&A growth persists above revenue growth; operating income stays flat and the market re-rates TYL to a
  Jack-Henry-style 18–19x. Note this bear FV is still **−7% from spot** — the downside from here is bounded
  by the buyback and the cash generation, not open-ended.
- **Base:** ARR stabilises around 8%, FTR integrates, the Texas payments comparison laps in Q1-2027, the
  multiple holds where it is on a bigger number.
- **Bull:** transaction growth normalises to 10%+ once Texas laps, cloud flips accelerate (Q4-25: flip ACV
  +64.5%), ARR reaccelerates toward 10%, and the market pays a monopoly multiple again.

**E[FV] = $337.0. Edge vs $305.54 = +10.3%.**

Sanity check against the Street (per the memory note on conservative-FV reflexes): the Street's **lowest**
published target in the feed is **$395–400** (Stifel, BTIG). My base of $355 sits **11% below the Street's
floor** and my E[FV] of $337 sits 15% below it. I am comfortable being below the Street here — the Street is
still applying ~28x to a business that just printed flat GAAP operating income — but I am flagging the gap
rather than hiding it, because being systematically 13% low is a documented failure mode of this desk.

---

## 9. CATALYST MAP — probability × timing × magnitude

| Catalyst | Date | p | Magnitude | Leading indicator |
|---|---|---|---|---|
| **Q3-2026 print — the ARR confirmation** | ~late Oct 2026 (estimated, not confirmed) | 1.00 | ±12–18% | Whether ARR growth prints above or below 8.2%; whether GAAP operating income grows |
| Buyback execution | continuous | 0.85 | +3–5%/yr to EPS | $1.745bn remaining authorisation = **14% of the market cap**; Q2 pace was $505M |
| Texas payments comparison laps | Q1-2027 | 0.90 | +2–3pts of transaction growth | transaction revenue growth inflecting off +3.5% |
| Organic-ARR disclosure | unlikely | 0.15 | ±15% | any IR deck breaking out acquired vs organic |
| AI-narrative reversal (AI-BREAK) | by 2027-12-31 | 0.45 (frozen house call) | +15–25% multiple | software-sector multiples re-rating as a group |
| Further M&A | continuous | 0.70 | neutral-to-negative near term | Tyler has done 5 deals in 4 quarters; each one further obscures organic growth |

**Dead-money check: NO.** There is a dated, fireable catalyst with a binary read (Q3 ARR) roughly 12 weeks out,
and a mechanical one (14%-of-cap buyback) running continuously in between.

---

## 10. PLAN

**STARTER, price-gated, two tranches, capped at the LOWER half of the 1.2% ruled range.**
The lower half is deliberate: this is not a red-team survivor, and the decisive number (organic ARR) is
undisclosed. Deployable base $3.3M.

| Tranche | Size | Trigger |
|---|---|---|
| **T1** | **0.45% = ~$14.9k** | GTC limit **$296** (−3.1% from spot). Do not chase; the post-print fade is still running |
| **T2** | **0.45% = ~$14.9k** | **EITHER** GTC limit **$272** (below the 3y low of $275.27) **OR** at market after a Q3-2026 print that shows ARR growth **≥8.5%** *and* GAAP operating income growth **≥+5%** |
| **Cap** | **0.90%** | Do not exceed without a fresh court |

Rationale for the price gate rather than a market order: my finding is a **valuation** finding (23x is fair,
not cheap, for ~6% organic growth) combined with a **timing** finding (one unconfirmed quarter). Per the
response taxonomy, valuation → price gate, timing → tranche. Both apply, so both are used.

No premium selling. This is a taxable book; short puts here would convert the entry into non-deferrable
short-term ordinary income at ~50%+. Use the GTC limit ladder.

### Dated kill triggers
1. **2026-10-31** — Q3-2026 ARR growth prints **below 7.5%** → **exit in full.**
2. **2026-10-31** — GAAP operating income declines year-over-year for a **second consecutive quarter** →
   **exit in full.** (One quarter is For The Record; two is the business.)
3. **2026-10-31** — FY2026 revenue guidance is **cut** → exit in full.
4. **2027-02-28** — any disclosure or reliable derivation putting **organic ARR growth below 6.0%** →
   exit in full.
5. **Continuous** — buyback pace falls below **$250M/quarter** while the stock trades under $350 →
   management's own "shares are undervalued" claim is falsified by its own behaviour → **halve.**
6. **Continuous** — a fifth acquisition announced before Q3 reports → **freeze adds** (serial M&A is how an
   8% grower is dressed as a 10% grower).

### Freezable call
**TYL | 2026-10-31 | "Tyler's Q3-2026 reported ARR growth comes in at or below 8.2% — i.e. no
re-acceleration from Q2" | our_p = 0.70**

Reasoning: the deceleration is broad (recurring, transaction, ARR, operating income all decelerated
simultaneously), the ARPA rolloff is a structural rather than a timing headwind, and For The Record's ARR
contribution is already in the Q2 base so it stops helping the year-over-year comparison. The 30% weight on
re-acceleration is the Texas comparison beginning to ease plus record Q2 bookings converting to revenue.

---

## 11. WHAT WOULD CHANGE THIS TO A 6+

- Tyler disclosing organic ARR growth at 7.5% or better.
- One clean quarter of GAAP operating income growing faster than revenue.
- Price below $272 (below the 3y low) with the franchise unchanged — at ~20x forward with a 14%-of-cap
  buyback authorisation running, the fair-value argument becomes an edge argument.

## 12. CLASSIFICATION

**RISK_PREMIUM with a thin EDGE overlay.** There is no informational edge: TYL is covered by at least seven
sell-side firms that all published within four days of the print. What is on offer is a fairly-to-slightly-
cheaply priced monopoly franchise whose multiple has compressed 59% from an extreme, with bounded downside
(the bear FV is only 7% below spot), a shrinking share count, and a negative correlation to the largest
concentrated risk already in the household book. That is ownable at a small size without an edge — but it is
carry and diversification, not alpha, and it is labelled as such.
