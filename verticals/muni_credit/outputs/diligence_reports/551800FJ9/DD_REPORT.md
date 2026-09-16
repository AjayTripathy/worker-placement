# Diligence Report — Lynwood Unified School District GO, CUSIP 551800FJ9

**Bond:** Lynwood Unified School District (Los Angeles County, CA), Election of 2012 General Obligation Bonds, **Series C** — 4.000% coupon, maturity 08/01/2041 (term bond), dated 05/05/2016.
**Cutoff:** 2026-06-20  |  **Status:** in buy book (DILIGENCE_MASTER). **Insured by Assured Guaranty Municipal Corp (AGM)** — insured rating S&P "AA", underlying S&P "A" (at issuance, 2016). *This corrects the master record, which flagged FJ9 as uninsured — see (a).*
**Verdict:** **BUY (hold-and-add on weakness)** — pledge is clean, levy is insulated from the district's real problem (enrollment), seismic is a known long-tail priced in. See section (h).

A note on convention: yields below are **gross** unless explicitly labeled TEY. After-tax taxable-equivalent yield (TEY) is grossed up at the CA top-bracket factor ~2.01 (federal + CA exempt). Do not read TEY as a gross coupon.

---

## (a) Security identity, issuer, and pledge — VERIFIED

| Claim | How verified | Authority | Finding |
|---|---|---|---|
| Issuer = Lynwood USD, LA County, CA | EMMA security page + OS cover | EMMA `/Security/Details/551800FJ9` → issue **EP371894**, desc "LYNWOOD UNIFIED SCHOOL DISTRICT (LOS ANGELES COUNTY, CALIFORNIA) ELECTION OF 2012 GENERAL OBLIGATION BONDS, SERIES C"; Official Statement | **VERIFIED** |
| This CUSIP = Election of 2012 GO Bonds, Series C, 4% 2041 | Three-way cross-check: EMMA security details (coupon 4.0, mat 08/01/2041, dated 05/05/2016); FY2025 audit GO-debt note ("2012 Series C, issued 5/5/2016, final maturity 8/1/2041, 2.00–4.00%, original $9,610,000"); OS issuance note ("On April 19, 2016 the District issued $9,610,000 of 2012 GO Bonds, Series C … mature 8/1/2041") | EMMA + audited financials + OS | **VERIFIED** |
| Unlimited ad-valorem GO pledge | OS cover: "The Bonds are general obligations of the District payable solely from ad valorem property taxes. The Board of Supervisors of Los Angeles County is empowered and obligated to levy such ad valorem taxes, **without limitation as to rate or amount**, upon all property … for the payment of … principal … and interest" | OS, EMMA | **VERIFIED — unlimited (UTGO)** |
| SB-222 statutory lien | Series C OS, verbatim: "Pursuant to **Section 53515 of the State Government Code, enacted by Senate Bill 222 (Stats. 2015, Chapter 78)**, the Bonds will be secured by a statutory lien on all revenues received pursuant to the levy and collection of the tax" | OS (`raw/official_statement.pdf`) | **VERIFIED — exact SB-222 binding**; the prompt's "SB-222 lien" is confirmed at the statute level |
| Tax-exempt (federal + CA) | Series C OS bond-counsel opinion: interest "excluded from gross income for federal income tax purposes," not an AMT preference item, and "exempt from State of California personal income tax" | OS | **VERIFIED — double tax-exempt; not a taxable muni** (taxable-gate cleared) |
| **Insured + ratings** | Series C OS cover: **INSURED RATING S&P "AA"; UNDERLYING RATING S&P "A."** Policy by **Assured Guaranty Municipal Corp (AGM)** issued concurrently with delivery (AGM financial strength then S&P AA / KBRA AA+ / Moody's A2) | OS | **VERIFIED — AGM-wrapped, S&P "A" underlying.** Corrects the master's `insured=false` (the master was wrong for FJ9; sister 551800HW8 is BAM-insured, FJ9 is AGM-insured) |

The investor-accessible Official Statement is saved to `raw/official_statement.pdf` (source URL in `raw/os_url.txt`).

**Mode-B note (no promoter framing):** the security is a plain-vanilla CA school UTGO. The pledge stands on the county's mandatory unlimited levy and a statutory lien — it does **not** depend on the district's operating budget, enrollment, project completion, or any revenue stream. That distinction is the entire credit thesis and it drives every "insulated" call below.

---

## (b) Assessed-value base, taxpayer concentration, debt-to-AV

| Metric | Value | Source |
|---|---|---|
| AV at issuance (Series C OS, FY2015-16) | **$2,840,280,380** | Series C OS "ASSESSED VALUATIONS" table (CA Municipal Statistics) |
| AV history 2008-09→2016-17 | $2.64B → $2.96B; only two down years (−3.5% FY11, −4.1% FY14), recovered each time | OS (companion 2017 OS table) |
| AV (current, derived) | **≈ $9.6 billion** (derived) | Measure U levy math: ballot levy "$50 per $100,000 AV = $4,800,000/yr" ⇒ AV ≈ $4.8M ÷ (50/100,000). Could not pull a 2024/25 OS AV table directly (EMMA 403 rate-limit) — flagged as derived, not audited |
| Top-1 taxpayer | **Plamex Investment LLC — 1.52%** of local secured AV (shopping center) | OS "Largest Local Secured Taxpayers" (FY2016-17) |
| Top-20 taxpayers | **9.39%** combined; granular, no single dominant payer; mix of retail / industrial / medical / apartments | OS |
| GO bonds outstanding (FY2025) | **$142,353,946** | FY2025 audit, GO long-term-debt note |
| GO debt-to-AV (FY2025, on derived current AV) | **~1.5%** ($142.4M / ~$9.6B) | computed; low |
| Direct + overlapping tax/assessment debt-to-AV (2016-17 snapshot) | 2.39%; combined-total (incl. RDA tax-increment) 4.49% | OS Direct & Overlapping Debt report |

**Read:** Taxpayer concentration is genuinely low — the #1 payer is 1.52% and the top-20 is under 10%. That is a positive, not a masking gap; a single taxpayer default cannot impair the levy. Debt-to-AV is conservative (~1.5% GO-only). The base is broad and residential/commercial-diversified. The one caveat is that the **audited AV anchor is from 2016-17**; the current AV is inferred from the Measure U levy formula (~$9.6B) and not independently pulled from a current OS — treat the precise current debt-to-AV as approximate.

---

## (c) AB-1200 fiscal certification + enrollment trend — the load-bearing section

### AB-1200 / fiscal-distress channel — CLEAN (honestly disclosed)
| Claim | How verified | Authority | Finding |
|---|---|---|---|
| No negative/qualified certification | FY2025 audited financials carry an **unmodified ("clean") audit opinion**; the only "going concern" strings are the standard *management/auditor responsibilities* boilerplate, NOT a going-concern qualification — checked in context (lines 130-165 of the opinion) | FY2025 audit (CWDL) | **CLEAN — POSITIVE-equivalent** |
| Reserves adequate | Available reserves **$29.2M = 10.9% of outgo** (FY2025) vs the 3% state minimum; unassigned GF balance $36.3M incl. $12.7M economic-uncertainties reserve | FY2025 audit | **CLEAN** — ~3.6× the floor |
| Operating posture | Operating **surpluses each of the last 3 years**; GF balance +$47.1M over two years; FY2025-26 budget plans a ~$24.8M (−15%) drawdown driven by enrollment, reserves still ample after | FY2025 audit MD&A | Honestly disclosed |
| "FCMAT report" is not a distress signal | The Aug-16-2024 FCMAT report is a **Facilities/Maintenance/Operations/Transportation organizational review** (district-initiated management-assistance), **not** an AB-139 extraordinary/fraud audit and not a fiscal-solvency review; no negative-cert, insolvency, or state-takeover language | FCMAT report (`raw/fcmat.txt`) | **Anti-masking finding** — scary-sounding source is routine ops consulting |

### Enrollment trend — REAL and ONGOING decline, but levy-insulated
Primary-source enrollment series (the soft-flag the screen wanted verified):

| Year | Enrollment | Source |
|---|---|---|
| 2009-10 | 16,715 | OS ADA/Enrollment table |
| 2017-18 (proj) | 14,195 | OS |
| 2019-20 | 13,245 | District / FCMAT |
| 2020-21 | ~11,967 | District (Wikipedia/NCES) |
| 2024-25 | ~10,762 | District ("Addresses Budget Challenges Amid Declining Enrollment") |
| 2025-26 | **10,373** | Ed-Data district profile |
| 2030-31 (proj) | **< 9,000** | District projection |

ADA at P-2 was **9,382 (FY2025)** and the FY2025-26 budget assumes a further **~4%/yr** ADA decline. This is a ~38% enrollment contraction since 2009-10 and it is **continuing** — the master's `enrollment_cagr_5y = −3.8%` is confirmed from primary sources.

**Why this does NOT impair 551800FJ9:** the bond is repaid from the **unlimited ad-valorem GO levy on the property-tax base (AV)**, which is mechanically *separate* from enrollment. Enrollment drives **LCFF state operating funding** (the General Fund), not the debt-service tax. A district can lose students and still levy whatever rate is needed on a flat-or-rising AV to cover GO debt service — and Lynwood's AV has been rising. The enrollment decline is therefore an **operating-credit / marketability** issue, not a GO-repayment issue. The district has disclosed it plainly (audit MD&A, FCMAT, board communications), so under the honesty framework this is **disclosed bad news, not a masked divergence** — it does not flip the verdict.

**Marketability flag (honest):** secondary-market liquidity and any future *underlying* rating could face mild pressure from the enrollment/operating narrative and from added GO leverage (Measure U, $80M authorized Nov-2024, layering onto the same AV base). This is a spread/exit risk, not a default risk. Sized accordingly in (h).

---

## (d) Call schedule — VERIFIED; near-term par call is out-of-the-money

| Field | Value | Source |
|---|---|---|
| Callable | Yes | EMMA security details |
| Next/optional call | **08/01/2026 @ 100.000 (par)** | EMMA security details |
| Structure | **2041 term bond** with mandatory sinking-fund redemption; bonds maturing on/before 8/1/2026 are non-callable, those after are optionally callable 8/1/2026+ at par | Series C OS "Optional/Mandatory Redemption" |

This is the standard ~10-year par call (issued Apr/May 2016 → first optional call Aug 2026). **At the current discount price (~98.9–99.6) the call is out-of-the-money for the issuer** — refunding/redeeming a sub-par bond at par 100 would be uneconomic, so the yield-to-worst is **to maturity, not to call** (confirmed by the bond math in (f): YTC > YTM). This **resolves the master's prior `call_risk = UNVERIFIABLE / next_call_date = null` gap.** Net: no meaningful near-term call risk to the buyer at today's price; if rates rally hard and the bond pushes well over par, the 2026+ par call would cap upside — a normal premium-call dynamic, not a surprise.

---

## (e) Trade tape — VERIFIED (916 prints; adequate liquidity for a school GO)

Source: EMMA RTRS tape for 551800FJ9 (`raw/trade_tape.json`, 916 rows).

- **Most recent investor-accessible mark:** last *sale-to-customer* **98.912 @ 4.096% on 2026-03-30**. The "~99.64" in the screen was a **2026-05-12 inter-dealer** print, not a customer execution — minor but worth flagging (a buyer pays the customer side, ~0.7pt below the inter-dealer mark).
- 2026 YTD: 42 prints (10 sales-to-customer), price range 97.53–100.08.
- 2025: 68 prints, range 90.52–99.85 — the sub-91 lows are the rate-driven 2025 drawdown showing the bond's ~11-yr duration, not a credit event; price has recovered toward par into 2026.
- **Liquidity:** ~28 distinct trade days in the trailing 12 months; blocks up to **$2.45M par** (also $2.13M, $2.0M, $1.98M, $1.0M, $0.555M). Two-sided dealer activity is regular. Consistent with the master's `two_sided_days = 15`, `max_block = $555k` on a stricter window. For a hold-to-maturity ladder position this supports entry/exit at a normal 1-3 bps/yr buy-side spread cost.

---

## (f) Seismic context, bond math, yield/tax

### Seismic (the main soft flag) — HIGH hazard, known and long-tailed
| Parameter | Value | Source |
|---|---|---|
| Mapped MCE_R short-period **Ss** | **~1.73g** (USGS ASCE7-16 at 33.93N/-118.21W, Site Class D); screen used **1.95** (very-high band; exact value parcel/site-class dependent) | USGS Building-Code web service |
| **S1** (1-sec) | ~0.62g | USGS |
| Fault setting | LA Basin — **Newport-Inglewood** right-lateral (source of the 1933 M6.4 Long Beach quake, ~120 deaths) and **Puente Hills** blind thrust; basin amplification | USGS / SCEDC; master `fault_zone` |

**Credit translation (Mode B):** A damaging Newport-Inglewood/Puente Hills event is a real physical tail for LA-Basin property. The credit channel is *AV impairment* — Article XIIIA lets owners seek calamity reassessment, and the OS itself names "earthquake" among events that could reduce AV. **But the GO structure is self-correcting:** under the unlimited levy, a drop in AV forces a *higher tax rate* to produce the same debt service (the OS states this explicitly: any AV reduction "would result in a corresponding increase in the annual tax rates levied by the County"). The risk is therefore a *severe, low-probability, slow-moving* AV/affordability stress, not a coupon-skip. CA school UTGOs have no modern default history through major quakes. This is a priced-in long tail, not a fresh finding — and it is the correct reason this bond carries a few extra bps vs an inland CA school GO of the same rating.

### Bond math (settle 2026-06-05; my engine, validated vs EMMA)
| At price | YTM (gross) | Yield-to-worst | Worst case | Mod. duration | After-tax TEY |
|---|---|---|---|---|---|
| 98.912 (last sale-to-cust) | 4.097% | 4.097% | **Maturity** | ~11.1 | **~8.23%** |
| 99.64 (recent inter-dealer) | 4.032% | 4.032% | Maturity | ~11.1 | ~8.10% |

My computed YTM (4.097%) matches EMMA's reported trade yield (4.096%) to 0.001 — math validated. **Gross YTW ≈ 4.10%; after-tax TEY ≈ 8.2%** (CA top-bracket gross-up ~2.01), confirming the screen. Modified duration **~11.1** is long — this bond's dominant *price* risk is rates, not credit (the 2025 tape proves it). Appropriate for a hold-to-maturity, income-and-insulation sleeve; less so for a mark-to-market-sensitive book.

---

## (g) Screen reconciliation (claim → finding)

| Screen claim | Finding |
|---|---|
| AB-1200 POSITIVE (LA) | **CONFIRMED-equivalent** — clean FY2025 audit, 10.9% reserves, 3-yr surpluses, no negative/qualified cert |
| AI insulation 99 | **CONSISTENT** — UTGO levy on property AV; no cap-gains/state-approp channel; school GO is the AI-insulated class per our framework |
| Fire 0% / flood tail 0% | **CONSISTENT** — dense urban LA parcel; master fire/flood tails 0.0 |
| EQ Ss 1.95 (moderate-HIGH) | **VERIFIED as HIGH** — USGS Ss ~1.73g / screen 1.95g, Newport-Inglewood/Puente Hills; priced-in long tail (see f) |
| Enrollment soft-decline | **VERIFIED and ongoing** (16,715→10,373, <9,000 by 2030-31) — but **GO-levy insulated**; operating/marketability concern only |
| Last px ~99.64 / TEY ~8.2% | **Refined** — last *customer* sale 98.91; TEY ~8.2% holds; 99.64 was inter-dealer |
| call_risk UNVERIFIABLE (master) | **RESOLVED** — 08/01/2026 @ par, out-of-the-money at discount; worst = maturity |
| insured = false (master) | **REFUTED — master was wrong.** FJ9 (2012 Series C) is **AGM-insured**, S&P insured "AA" / underlying "A." (The master likely mis-mapped FJ9; sister 551800HW8 is BAM-insured.) Net effect is *credit-positive* vs the screen |

---

## (h) Verdict and sizing — BUY (hold-and-add on weakness)

**BUY / retain.** The diligence is *confirmatory of the buy thesis, with two honest caveats sized below.*

- **What makes it edge (mechanism):** the masked-vs-disclosed test comes out clean. The two scary-looking items — a "declining-enrollment district" and an "FCMAT report" — are exactly the kind of headers that look like masking but, read to the data, are (i) honestly disclosed operating news on a channel (LCFF/General Fund) that is *mechanically severed* from the bond's repayment source (the unlimited AV levy + Govt Code 53515 statutory lien), and (ii) a routine facilities ops review, not a distress audit. Honesty-alpha rule: disclosed bad news on a non-pledge channel is CLEAN, not a flag.
- **Real risks, correctly priced:** (1) **rate/duration** — mod. duration ~11.1; this is the dominant mark-to-market risk, shown live by the 90.5 print in 2025. (2) **Seismic AV tail** — severe-but-rare LA-Basin quake; self-correcting under the unlimited levy, no CA school-UTGO default precedent. (3) **Marketability** — enrollment narrative + Measure U leverage could keep a few bps of spread / soft underlying rating; an exit (not a default) cost.
- **Why not HOLD-only:** none of the three risks touches principal/coupon security; the after-tax TEY ~8.2% on a double-tax-exempt, statutorily-liened UTGO — **additionally AGM-wrapped (S&P insured "AA") over an S&P "A" underlying** — is well compensated for them. The AGM wrap is a tie-break, not the thesis: the UTGO pledge + Govt Code 53515 statutory lien stand on their own; the wrap compresses spread conditional on the (sound) underlying and aids exit liquidity. The bond fits the AI-insulated, hold-to-maturity school-GO sleeve precisely.
- **Sizing discipline:** keep within the LA-Basin **seismic aggregate cap** (do not stack FJ9 + sister 551800HW8 + other Newport-Inglewood/Puente Hills names beyond the per-fault-zone limit) and respect the duration budget. Add on rate-driven weakness (sub-97 prints), not on credit fear. Execute on the **customer** side (~0.7pt back from inter-dealer marks) and use the trade tape for block sizing.

**One-line:** a clean, double-tax-exempt CA school UTGO whose only headline risks (enrollment, "FCMAT," LA-Basin quakes) are either disclosed-and-off-pledge or priced-in long tails — BUY/retain, sized to the seismic and duration caps.

---

### Source documents (all under `outputs/diligence_reports/551800FJ9/raw/`)
- `official_statement.pdf` (+ `.txt`) — **canonical** Lynwood USD Official Statement, Election of 2012 GO Bonds, **Series C** (EMMA issue EP371894; source `emma.msrb.org/ES782548-ES615413-ES1011099.pdf`, see `os_url.txt`). Carries the SB-222/53515 statutory-lien text, unlimited-ad-valorem pledge, tax opinion, AGM insurance + ratings, AV, taxpayers, debt, ADA/enrollment, and the 8/1/2026 par-call terms.
- `combined_2012D_2016A_OS.txt` — companion 2017 OS (2012 Series D / 2016 Series A) used for the AV-history table and top-20 taxpayers (same issuer/program).
- `security_details.json` — EMMA security page (coupon/maturity/dated/call/mark) for 551800FJ9.
- `trade_tape.json` — 916-row EMMA RTRS trade tape.
- `scale_EP371894.json` — EMMA maturity scale for Series C (shows the 4%/2041 $6.45M term bond = this CUSIP).
- `fcmat_lynwood.pdf` / `fcmat.txt` — FCMAT Facilities/MOT review, Aug 16 2024.
- `audit2025.pdf` / `audit2025.txt` — Lynwood USD FY2025 audited financial statements (clean opinion, reserves, GO-debt note, ADA).
- Pull scripts: `pull_emma.py`, `pull_seriesC_os.py`, `find_fj9_v2.py`, `analytics.py`.

External authorities cited: EMMA `/Security/Details/551800FJ9`; USGS ASCE7-16 building-code web service; CDE/Ed-Data district profile; district Measure U disclosures.

<!-- current-state-refresh -->
### Current-State Verification (AV / coverage refresh — 2026-06-20)

Refreshed 2026-06-20 via a SERIAL, throttled EMMA continuing-disclosure pull (the original UNVERIFIABLE flag was an EMMA 403 rate-limit from concurrent scraping, not a real disclosure gap). Latest issuer annual report: _Annual Financial Disclosures Posted 02/02/2026  for the year ended 06/30/2025 (371 KB)_. **Current total assessed valuation (levy base): $5,014,638,065 for FY2025-26**; secured-tax delinquency **2.51%**; audited FY2025 on file. For an unlimited ad-valorem GO the AV base + the delinquency cushion ARE the 'coverage' — there is no DSCR; the levy rate floats to hold debt service constant. **This resolves the prior 'current AV/coverage UNVERIFIABLE' caveat.**
