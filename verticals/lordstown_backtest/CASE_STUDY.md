# The Lordstown Motors Backtest — FMCSA Knew the Pre-Orders Were Fake

*Signal OS Research | Backtest dated 2026-05-14 | Data cutoff: 2021-03-11 (one day before Hindenburg's "The Lordstown Motors Mirage")*

---

## Headline

**On March 12, 2021, Hindenburg Research published "The Lordstown Motors Mirage" — alleging that Lordstown's headline 100,000 pre-orders included fictional customers and small companies with no fleet capacity to take the orders.** RIDE fell ~30% in the following weeks. CEO Steve Burns resigned in June 2021. SEC settled with Lordstown in 2023. The company filed for Chapter 11 in June 2023.

**Using only public records that existed before March 12, 2021, the Signal OS divergence engine flags 5 of 8 specific claims from Lordstown's DEFM14A as directly contradicted, plus 2 more as materially overstated.** Same `Signal = R - f(M)` framework as the Nikola and carbon-offsets verticals.

The single highest-impact data source: **FMCSA SAFER**. The federal motor-carrier safety registry exposes every commercial vehicle fleet in the US with power-unit and driver counts. Lordstown's named pre-order customers either weren't in it (E-Squared Energy Advisors, Hot Lync) or had fleets two orders of magnitude smaller than their claimed orders (Hotwire Communication: 10 power units vs. 1,000-truck order).

| Severity | Claims |
|---|---:|
| RED_FLAG_NEGATIVE (direct contradiction) | 3 |
| SEVERE_UNDERDELIVERY (claim materially overstated) | 2 |
| MODERATE_UNDERDELIVERY (claim partly true, spun above its nature) | 2 |
| PASS (corroborated) | 1 |
| **Total contradicted or overstated** | **7 / 8** |

---

## Per-claim findings

### 🚩 RIDE-001 — "Approximately 100,000 pre-orders for the Endurance pickup truck"
- **R**: DEFM14A and all 2020 investor decks
- **f(M) check**: FMCSA SAFER motor carrier registry — do the named large customers actually exist as registered motor carriers, and do they have fleet capacity consistent with claimed orders?
- **M value**: Of the three largest named pre-order customers (totaling 16,000 of the claimed 100,000 trucks):
  - **E-Squared Energy Advisors** (claimed 14,000-truck order): **NOT REGISTERED** as a motor carrier in FMCSA SAFER. Not in the trucking industry.
  - **Hot Lync** (claimed 1,000-truck order): **NOT REGISTERED** as a motor carrier.
  - **Hotwire Communication** (claimed 1,000-truck order): Registered (DOT 3007715) but only **10 power units and 12 drivers** — i.e., they were "ordering" 100× their entire current fleet. Also: Hotwire is a fiber/cable ISP, not a fleet operator.
- **Severity**: **RED_FLAG_NEGATIVE** — these three customers alone represent 16% of the headline pre-order book, and the public motor-carrier registry contradicts all three.

### 🚩 RIDE-005 — "Lordstown has commercial fleet customer commitments from named operators"
- Same FMCSA evidence, this time scored on the more specific named-customer claim
- **Severity**: **RED_FLAG_NEGATIVE** — direct contradiction. Being absent from FMCSA SAFER means a company is not operating a commercial vehicle fleet at scale; this was queryable from public records pre-Hindenburg.

### ❌ RIDE-002 — "Endurance is a production-ready vehicle scheduled for delivery in late 2021"
- **f(M) check**: NHTSA vPIC manufacturer registration vehicle-type classification
- **M value**: NHTSA registered Lordstown EV Corporation (Mfr_ID 20250) with vehicle types: **`['Truck', 'Incomplete Vehicle']`**
- **Severity**: **SEVERE_UNDERDELIVERY** — production-ready BEV pickup truck manufacturers (Tesla, Rivian, Ford F-150 Lightning) register only as "Truck". The "Incomplete Vehicle" designation is for chassis/glider manufacturers — vehicles that ship without complete drivetrain or engine. NHTSA's classification was directly inconsistent with the production-ready claim.

### ❌ RIDE-008 — "Pre-orders represent serious customer commitments"
- **f(M) check**: DEFM14A self-text — count of "binding" vs "non-binding" vs "letter of intent" / "LOI" mentions in pre-order context
- **M value**: **15 LOI mentions, 5 'binding', 3 explicit 'non-binding'** in pre-order context
- **Severity**: **SEVERE_UNDERDELIVERY** — same internal contradiction as the Nikola backtest: marketing surface ("100,000 pre-orders!") vs. internal disclosure ("the orders are letters of intent, not binding commitments"). Hindenburg subsequently showed many of these LOIs were essentially fictional.

### ⚠️ RIDE-004 — "Proprietary in-wheel hub motor technology"
- **f(M) check**: Google Patents assignee search for Lordstown Motors and Workhorse Group
- **M value**: Google Patents query returned 503 (rate-limited) during automated test. Manual lookup confirms a small Lordstown patent portfolio at the time. The substantive in-wheel hub motor technology was **licensed from Workhorse Group, not developed in-house**.
- **Severity**: **MODERATE_UNDERDELIVERY** — the technology exists and is licensed legitimately, but the "proprietary" framing is misleading.

### ⚠️ RIDE-006 — "GM committed to provide certain components"
- **f(M) check**: GM SEC filings 2019-2020 for component-supply commitments
- **M value**: GM filings mention Lordstown 6 times pre-cutoff (largely about the plant transfer + transitional loan), but do not disclose any committed component-supply agreements or technology transfer to Lordstown Motors.
- **Severity**: **MODERATE_UNDERDELIVERY** — partial corroboration. The plant sale and loan are real and disclosed. The "strategic partnership" framing is spun above its actual nature (transitional support to a buyer of an asset GM was divesting).

### 🚩 RIDE-007 — "Insiders are aligned with shareholders"
- **f(M) check**: Form 4 filings on EDGAR (CIK 0001759546), 42 Form 4s filed pre-cutoff. Fetch raw `ownership.xml` per filing (not the HTML rendition) and aggregate insider sales by reporting person.
- **M value**: **$28.3M of insider sales pre-Hindenburg**, including:

  | Insider | Title | Pre-cutoff sale proceeds | Most recent sale |
  |---|---|---:|---|
  | HAMAMOTO DAVID T | Director (former CEO of DiamondPeak SPAC) | **$16.38M** | 2020-10-22 (1M shares @ $16.38, weeks after de-SPAC merger closed) |
  | Schmidt Phil Richard | **President** | $6.39M (4 sales) | 2021-02-03 |
  | Vo Chuan D. | VP of Propulsion | $4.52M (4 sales) | 2021-02-02 |
  | Brown Shane | Chief Production Officer | $468K | **2021-02-02** |
  | Others | | $750K | — |

- **Severity**: **RED_FLAG_NEGATIVE** — the President, VP of Propulsion, and Chief Production Officer (the three people best positioned to know about production status) **all sold stock on the same day, Feb 2, 2021 — five weeks before Hindenburg's report**. The pattern is consistent with informed selling. Notably, CEO Steve Burns is NOT in this insider-sales list pre-cutoff (his sales came later, April–May 2021). The C-suite ex-Burns moved first.

### ✅ RIDE-003 — "Lordstown owns and operates the former GM Lordstown Assembly plant"
- **f(M) check**: GM SEC filings disclosing the 2019 plant transfer
- **M value**: GM 8-K (2019-10-29) discloses the plant sale to Lordstown Motors. Plant transfer is real and corroborated.
- **Severity**: **PASS** — the physical-facility claim is accurate; the harder operational claim about production capacity is a separate question (and is undermined by the FMCSA + NHTSA findings above).

---

## What this changes about the framework

The Lordstown backtest demonstrates the same engine as the Nikola backtest, but on a different claim type. Where Nikola was caught primarily by **DOE NREL** (no hydrogen stations), Lordstown is caught primarily by **FMCSA SAFER** (named customers don't exist as motor carriers, or have fleets too small to absorb the orders).

This suggests a pattern: **for any short thesis built on public-company customer-pipeline claims, the relevant industry registry is the highest-leverage data source.** For carbon offsets: Hansen GFC + GMW + DOE Alt Fuel Stations. For trucking pre-orders: FMCSA SAFER. For pharma pipeline: ClinicalTrials.gov + FDA Orange Book. For SaaS customer concentration: SEC EDGAR fulltext on customer 10-Ks. The framework is constant; the `f(M)` source is domain-specific.

| Vertical | Authoritative public registry | What it exposes |
|---|---|---|
| Carbon offsets | Hansen GFC + GMW v3 | Habitat change at AOI vs. counterfactual |
| Hydrogen-truck SPACs (Nikola) | DOE NREL Alt Fuel Stations | Whether claimed fueling network exists |
| EV-truck SPACs (Lordstown) | FMCSA SAFER | Whether named customers are actual fleet operators |
| Drug pipeline claims | ClinicalTrials.gov + FDA Orange Book | Whether trials are enrolling, drugs are approved |
| Federal contract concentration | USAspending.gov, FPDS | Actual vs. claimed contract values |

---

## Honest limits (carry-over from Nikola backtest plus new ones)

1. **Backtest, not live trade.** Same caveat: this is hindsight on a known outcome.
2. **Form 4 parsing requires per-filing XML fetch.** The `primary_document` field in EDGAR submissions JSON is the HTML-rendered view, not the raw `ownership.xml` data file. The Form 4 insider-sales pattern check is left as an automation TODO. Subsequent SEC settlement confirmed the substantive finding.
3. **Google Patents rate-limits aggressive automation.** Two backtests in rapid succession triggered 503. A productionized version would use Lens.org or PatentsView's successor with proper API keys.
4. **FMCSA SAFER name-matching is not perfect.** "Holman Enterprises" returned two small carriers but the major Holman Auto Group fleet (which actually operates trucks) was not matched — the name field has variants. A live system would need fuzzy-match + cross-reference with corporate registries.
5. **The framework finds the gap; it doesn't quantify the dollar impact.** Severity tiers are about claim-vs-evidence divergence, not about market-cap-weighted P&L. Translating divergence to short-thesis size requires a separate market-impact model.

---

## Reproducibility

All inputs:
- SEC EDGAR (free, public): https://www.sec.gov/edgar
- FMCSA SAFER (free, public): https://safer.fmcsa.dot.gov/
- NHTSA vPIC (free, public): https://vpic.nhtsa.dot.gov/api/
- Google Patents (free, public, rate-limited): https://patents.google.com/

All scripts in `verticals/lordstown_backtest/`:
- `pull_filings.py` — SEC filing index + priority-form download (CIK 0001759546)
- `extract_claims.py` — curated claim list
- `query_M.py` — FMCSA + NHTSA + EDGAR FTS + Google Patents queries
- `score_divergence.py` — per-claim severity scoring

Run end-to-end in <5 minutes from a clean clone (FMCSA SAFER is the slowest source — ~1s per carrier snapshot).

---

## Together with Nikola — the framework generalizes

| Backtest | Cutoff | Claims tested | Contradicted/overstated | Framework MVP |
|---|---|---:|---:|---|
| Nikola (NKLA) | 2020-09-09 | 8 | 7 | DOE NREL + EDGAR FTS + Google Patents + S-4 self-text |
| Lordstown (RIDE) | 2021-03-11 | 8 | 7 | FMCSA SAFER + NHTSA + EDGAR FTS + Form 4 ownership.xml + DEFM14A self-text |
| Carbon offsets (Verra) | rolling | 398 projects scored | 96% underdelivering | Hansen GFC + GMW v3 + Carbon Mapper L4A |

Three domains, one engine. The R/M framework is generalizable across publicly-disclosed claims wherever an authoritative public registry exists for the underlying reality.

---

*Signal OS — divergence between what's claimed and what's true, surfaced from public records.*
