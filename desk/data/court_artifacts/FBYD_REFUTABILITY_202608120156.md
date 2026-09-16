## FBYD — Refutability Triage

The class-dislocation screen misfired here: FBYD's −65.7% dd52 is measured from a **squeeze peak**, not from cohort-narrative damage — the stock is **+168% off its 52w low ($3.71)** and was up >200% YoY at its July peak, and the operative discount is a going-concern capital-structure discount that has nothing to do with discretionary-leisure demand.

**PRINT PROXIMITY: 2026-08-13 — 2 trading days out. Verified via stockanalysis.com listing (Aug 13); marketchameleon/Nasdaq show an Aug 19 variant. NO company PR names either date — treated as WITHIN the 5-day window on the earlier candidate.**

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| FBYD | **STRUCTURAL** | **Unrestricted cash + contract liabilities vs the ~$4.6M/qtr adj-EBITDA burn** (solvency, not demand) | Cash **$1.18M** at 3/31/26, down from $1.87M at 12/31/25; adj EBITDA **−$4.6M** Q1'26; working capital **−$12.9M**; total debt **$19.0M** (up from $17.98M q/q). 10-Q states the company "does not currently have sufficient cash or liquidity to pay liabilities that are owed or are maturing at this time" ([8-K ex-99.1](https://www.sec.gov/Archives/edgar/data/0001937987/000119312526224204/fbyd-ex99_1.htm); [balance sheet](https://stockanalysis.com/stocks/fbyd/financials/balance-sheet/?p=quarterly)) | 2026-08-13 | Discount is CORRECT and arguably incomplete — ~$959M–$1.22B mcap on $18.6M TTM revenue (~52–65x sales) with negative operating income and a going-concern qualification |
| FBYD | *(cohort-narrative leg — damage genuinely absent, but this is the wrong lens)* | Consolidated revenue + FCG contracted pipeline | Q1'26 revenue **$5.4M vs $1.7M** YoY (+218%); TTM **$18.6M (+167.6%)**; FCG pipeline **$29.2M** contracted, plus ~$18M VAI dark-ride agreements and a **$10.6M** VAI master consulting agreement signed 6/5/26 ([8-K](https://www.sec.gov/Archives/edgar/data/0001937987/000119312526224204/fbyd-ex99_1.htm)) | 2026-08-13 | Demand damage is absent — which is precisely why fading a "cohort sold indiscriminately" story here is a category error; nobody sold this on consumer discretionary |

### PRINT-DECISIVE RECONSTRUCTION (pre-print public data)

**1. The $11.1M credit cannot repeat — a negative GAAP headline on 8/13 is near-mechanical.** Q1's +$6.1M net income was driven by a non-recurring credit reversing accrued transaction expenses from the 2023 business combination; ex-credit, Q1 was roughly **−$5.0M**. No comparable accrual remains to reverse. The float ran on the "swings to profit" headline; 8/13 reads as a reversal even if operations improve.

**2. The cash bridge cannot close from operations, and no market financing appears in the record.** $1.18M cash against a $4.6M quarterly burn means Apr 1 → Aug 13 was funded by (a) VAI customer prepayments, (b) related-party/new debt, or (c) stretched payables. The filing record between the Q1 print and today shows **only** RSU grants (6/16), the annual-meeting 8-K (6/12), and the 6/5 VAI agreement — **no S-1/S-3, ATM, or offering 8-K.**

→ **The single decisive line item on 8/13 is contract liabilities / deferred revenue and cash at 6/30/26.** Material jump in contract liabilities + cash rebuilt above ~$5M ⇒ the VAI awards are cash-funding the business, going concern eases, and that is *not* priced. Cash still ~$1–2M with debt up again ⇒ an imminent dilutive raise is the base case, and the **5/21 Nasdaq listing of the 11% Series B convertible preferred (FBYDP)** reads as pre-positioning for exactly that — you list a preferred to create an exit/currency, not for fun, at 11% on an issuer that can't pay current obligations.

**3. Seasonality is a known tailwind, therefore already priced.** PDP (Katmandu Park, Mallorca) carried a $1.2M Q1 operating loss on winter closure; Q2 opens the season, so the equity-method line improves sequentially *by construction*. Don't credit it as a surprise.

**PRE-PRINT POSITION: FLAT.** The one pre-print-knowable asymmetry points to a negative GAAP headline into a float that ran 200%+ on the prior positive one, while solvency stays unresolvable until the 6/30 balance sheet prints — and no long is underwritable at $1.18M cash against −$12.9M working capital. No short either: micro-float, +168% off the low, retail-driven tape — the conditioning-layer squeeze-fuel rule that overturned RCAT applies directly here.

### COURT-WORTHY (damage-absent, ranked)
**None.** FBYD's demand metrics are inflecting, but the drawdown that triggered this event was never a cohort mispricing — it is a pump unwind on a going-concern shell. There is no dispersion for a court to arbitrage.

**COURT-WORTHINESS FBYD: 2/10 — the discount is correct (and likely incomplete); a court would spend a full red/blue bench to conclude "stay flat" on a name that is unfinanceable long and unshortable short.**

---

Three things you should know about how this was produced:

- **sec.gov is 403-blocking WebFetch in this session and no Bash tool is available**, so I could not read the 10-Q or 8-K exhibits directly. Filing *content* above came from mirrors (stocktitan's 8-K parse, search extraction of the going-concern sentence) cross-checked against stockanalysis.com's balance sheet. The URLs cited are the real EDGAR documents, but I read them secondhand — flagging that against the "≥1 primary citation" rule rather than papering over it.
- **One unreconciled figure:** the mirror reports FCG segment revenue of $13.0M against consolidated revenue of $5.4M for the same quarter. That doesn't reconcile on its face (likely a 100%-basis or period mismatch in the mirror). I did not use it in any conclusion. Also, the evidence pack's $1.22B mcap disagrees with stockanalysis' $958.57M on 96.24M shares — the valuation conclusion holds either way.
- **The dashboard closing ritual did not run.** I have no shell and no read permission on `/Users/ajay/exalted/signalos`, so the ledger upsert / edge_classification / entry_plan / scanner re-run could not be executed from here. Given the verdict is NO POSITION and the score routes below the ≥6 escalation threshold, nothing changes in the book — but the screen-misfire finding is worth writing back: **class-dislocation should suppress members whose dd52 is measured from a squeeze peak** (test: `pct_off_low` > ~1.0 with positive YoY price), or it will keep manufacturing cohort events out of pump unwinds.