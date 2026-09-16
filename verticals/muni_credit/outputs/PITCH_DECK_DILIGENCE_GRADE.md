# Pitch-Deck Diligence Grade — California Insulated Muni Sleeve (Sleeve C)

**Subject:** `outputs/CA_MUNI_SLEEVE_PITCH_DECK.html` — $1,000,000, 24-bond CA muni ladder
**Graded:** 2026-06-10 · graded as if from an outside promoter, no home-team courtesy
**Method:** Mode B (first-principles disconfirmation) led; Mode A (claim-by-claim) followed
**Question graded:** not "is the strategy good" but "does the marketed takeaway diverge from what the data supports?"

---

## HEADLINE

- **Letter grade: B+**
- **Honesty score: 84 / 100**
- One-line: An unusually honest deck — the arithmetic reconstructs to the penny, the named stress-district screen-out verifies against the primary CDE source, and a full caveats slide pre-empts most of the attacks. It loses points on three *framing* overreaches (a "none of it" absolute the data softly contradicts, a "traced to its primary source" claim broader than the per-issue work actually done, and a headline "99" that averages over names the deck itself scores lower), not on any fabricated number.

---

## MODE B — FIRST-PRINCIPLES DISCONFIRMATION (led)

I rebuilt the decisive numbers from raw coupon / price / maturity *before* accepting the deck's framing, and hunted for the ways an "8.18% after-tax, AI-insulated, every-name-verified" muni ladder is most commonly oversold.

### B-1. The after-tax TEY arithmetic — does it flatter? **NO — it reconstructs exactly, and the de-minimis drag is correctly applied (honest direction).**

I recomputed the headline metric for five holdings from scratch. The shop's formula is:

> after-tax TEY = (coupon / price) × 2.01  +  (YTW − coupon/price) × 1.00

i.e. the **tax-exempt current-yield component is grossed up ×2.01**, while the **discount-accretion component (taxed as ordinary income on de-minimis breaches) is added at face with NO gross-up.** That is the *correct* treatment: ordinary-taxed accretion needs no gross-up to be tax-equivalent to a taxable bond, because both sides are taxed at the same ordinary rate.

| Holding | Cpn | Px | YTW | My recomputed a-t TEY | Deck a-t TEY | Match |
|---|---|---|---|---|---|---|
| Lowell Joint 547541LJ9 | 3% | 78.12 | 4.82% | 8.70% | 8.70% | exact |
| Albany 012104QQ1 | 3% | 77.20 | 4.84% | 8.76% | 8.76% | exact |
| Modesto 607735CA3 | 3% | 81.40 | 4.57% | 8.29% | 8.30% | ±0.01 |
| Victor Elem 926055KH6 (no breach) | 4% | 99.99 | 4.00% | 8.04% (=4.00×2.01) | 8.04% | exact |
| San Benito 796472AS7 (no breach) | 4% | 98.75 | 4.09% | 8.22% | 8.23% | ±0.01 |

Crucially, the **sleeve headline 8.18% is BELOW the naïve 4.28 × 2.01 = 8.60%** — the de-minimis drag pulls it down ~42 bps, exactly as the deck claims ("materially below the naïve gross figure"). This is the single most common place a muni pitch flatters, and here it does not. **No flattering arithmetic found.**

### B-2. The ×2.01 gross-up premise — what does it assume, and is it stated? **Stated, but it is the load-bearing assumption and a buyer who is not a top-bracket CA resident does not earn it.**

1/(1 − 1/2.01) implies a **50.25% combined marginal rate** = federal 37% + CA 13.3%. That is internally correct for a CA top-bracket resident (munis are NIIT-exempt, so 3.8% is correctly excluded). The deck **does disclose** this premise — "(CA top bracket)" sits on the cover stat, and the caveats slide repeats "grossed up at the California top combined bracket (×2.01)."

The honest read: the ×2.01 roughly **doubles** the headline. A buyer in, say, a 35%/9.3% bracket earns a factor closer to ~1.79, dropping the headline from 8.18% to ~7.3%; a non-CA resident loses the state-exempt leg entirely. The deck states the premise but does not show the sensitivity — the entire "8.18%" pitch lives or dies on the buyer actually being a top-bracket Californian. **Disclosed, not hidden; but it is the assumption the whole headline rests on.**

### B-3. Yields-are-marks — what does the last-trade print overstate for a buyer crossing the spread? **The deck pre-empts this honestly, but the headline still quotes mid/last-trade yields, not acquirable yields.**

Every YTW/TEY in the deck is computed off the **EMMA last-trade price**, which is a print from a past trade — for the thin (L4) names, days or weeks old (e.g. Bellevue Union last printed 36 days before as-of; Modesto 19 days). A buyer lifting an offer pays the dealer markup the caveats slide pegs at **0.1–0.5 pt**. On an 18-year bond, 0.3 pt of markup is ~3 bps/yr of yield — i.e. the realized after-tax TEY on the L4 core is plausibly **15–30 bps below the quoted figure**. The deck flags this twice (cover footnote-style caveat + dedicated caveat slide + the "spread is paid once on the buy" framing). **The overstatement exists but is disclosed; the headline number is a pre-cost, last-trade-mark number, which the deck says.** Fix: show a "realized after-fill" TEY band, not only the mark-based headline.

### B-4. The "insulation 99" and "credit 87" scores — whose scores? Honestly labeled as the shop's own? **YES — labeled as proprietary throughout, not passed off as agency ratings. This is handled well.**

Both scores are repeatedly and explicitly the shop's own: "Independent credit score," "our pledge-level read," "AI-insulation (AI-1…AI-5)" with the shop's own five-tier scale defined on slide 5. The agency column is **labeled "a security-class benchmark, not an issue-specific rating,"** with the honest disclosure that "EMMA publishes no third-party rating for most of these issuers." **No rating-laundering.** This is the textbook-correct way to present a proprietary score. (See B-7 for the one place the credit score's *granularity* is oversold.)

### B-5. Claimed-verified vs absence-of-evidence — **one real tell: `cert_status: "POSITIVE(absent)"`. "Clear of the stress list" ≠ "affirmatively certified Positive."**

The basket records every K-12 district as `"POSITIVE(absent)"` — meaning the district is **absent from the CDE Negative/Qualified lists**, from which the shop *infers* Positive. The deck phrases this as "every K-12 district in the basket is interim-certification clear (**Positive**, no stress flag on record)." Absence from the negative/qualified roster is strong evidence (CDE only publishes the non-Positive LEAs), but it is technically *absence-of-evidence-of-stress*, not a positive certification document pulled per district. The deck's parenthetical "(no stress flag on record)" is the honest version; the bolded "Positive" leans slightly past what was checked. **Minor — the underlying inference is sound and the methodology note discloses the mechanism.** The deck *does* get the community-college treatment exactly right ("unverified-not-clean," AB-1200 doesn't apply).

### B-6. Selection vs survivorship — 147 → 24 with survivors' yields quoted — silent biases? **One: the funnel is presented as pure verification, but the final cut is a yield-rank, so the quoted yields are the top-of-distribution survivors.**

The 39 → 24 step is explicitly "**selected on after-tax yield, then verified**" (slide 4) — i.e. the last cut maximizes the very metric the deck headlines. That is legitimate portfolio construction, but it means the **8.18% is the yield of the highest-after-tax-TEY survivors**, not a representative yield of the insulated universe. The deck does not hide this (it states "ranked on de-minimis-aware after-tax TEY"), but a reader could mistake "verified-safe" for "and this is what insulated CA munis yield generically." The 27-taxable / 23-illiquid / 17-pledge-fail drops are the honest part — those are real exclusions, not yield-shopping. **Disclosed; no survivorship in a backtest sense (no performance is claimed).**

### B-7. **STRONGEST MODE-B CATCH: the credit score is a security-CLASS constant, but the cover claims per-issue primary-source verification.**

All 18 school/college GO holdings carry credit = **exactly 90** — because the score is a formulaic map from `security_credit_key = school_go_sb222`, not a per-district financial read. Only **3 of 24** names carry `issuer_verified: true`. Yet the cover states: "every pledge, price, **credit** and liquidity figure traced to its primary source," and the methodology says credit is "read from the official statement or the governing statute … not the issuer's name or marketed label."

The defensible reading: SB-222 (Gov. Code §53515) applies to *every* CA school GO *by statute*, so a class-level statutory read genuinely does apply to all 18 — the "or the governing statute" clause covers it. The **overreach** is that two districts with very different finances (a wealthy Bay Area unified vs. a small rural district) both score 90, and the cover's "every credit figure traced to its primary source" implies *per-issuer* credit diligence that was not performed. **This is the deck's biggest takeaway-vs-data gap:** the credit number is a pledge-structure score, not an issuer-credit score, and the framing blurs the two.

### B-8. "No CA school GO payment default through Loma Prieta / Northridge / Camp Fire" — verifiable and appropriately careful? **Substantially true and carefully scoped to *debt-service payment*, but stated as an absolute on an absence-of-evidence basis.**

The claim is narrow and correct in spirit: CA school GOs are backed by an unlimited ad-valorem levy that the county *must* levy to cover debt service, and there is no widely-recorded instance of a post-1986 CA school GO missing a scheduled debt-service payment through those three events. The deck scopes it correctly to "**missed a debt-service payment**" (not "no distress," not "no downgrade"). The care is appropriate. The residual: it is an absence-of-recorded-default claim (you cannot fully prove a negative across all issuers), and Teeter-plan advance-collection (cited as a backstop) is **county-optional and can be terminated** — the deck mentions Teeter as a positive but not that it is revocable. **Minor scoping caveat; the headline claim itself is well-formed.**

### B-9. "None of it" — the thesis absolute vs. the deck's own AI-2 names. **A genuine internal tension.**

Slide 2 states the state-General-Fund channel is excluded: "This sleeve holds **none of it.**" But the basket holds two UC names (8% of par): **UC GRB (insulation 87)**, whose pledge — per the shop's own tearsheet — includes "**certain state educational appropriations**," and **UC LPRB (insulation 93)**. The shop's own scores say these are *AI-2, not AI-1* — i.e. they carry 7–13% modeled exposure to the very channel the thesis says is held at zero. The holdings table is honest (shows AI-2, shows 87/93), but the bolded thesis absolute "none of it" is contradicted by 8% of the par. **Fix: change "none of it" to "the sleeve excludes income-tax-backed *state* GO and appropriation debt; two UC revenue names carry modest (AI-2) residual exposure."**

---

## MODE A — CLAIM-BY-CLAIM VERIFICATION
*(table follows in next section)*

### Mode A — claim → how verified → source authority → finding

| # | Deck claim | How verified | Source authority | Finding |
|---|---|---|---|---|
| 1 | After-tax TEY **8.18%** (par-wtd) | Recomputed par-weighted a-t TEY from per-bond fields | basket JSON (tey_ytw_aftertax × par) = 8.179% | **VERIFIED-INTERNAL** (8.18 = 8.179 rounded) |
| 2 | Per-bond a-t TEY (Lowell 8.70, Albany 8.76, Modesto 8.30, Victor 8.04, San Benito 8.23) | Rebuilt from raw coupon/price/maturity with the de-minimis split | Independent recompute | **VERIFIED** (matched to ±0.01) |
| 3 | ×2.01 gross-up = "CA top combined bracket" | 1/(1−1/2.01) = 50.25% = fed 37% + CA 13.3%, NIIT correctly excluded | Independent tax-rate check | **VERIFIED** (and disclosed) |
| 4 | "8.18 is below the naïve gross figure" (de-minimis drag) | 4.28 × 2.01 = 8.60 > 8.18; drag ≈ 42 bps | Independent recompute | **VERIFIED** (honest direction) |
| 5 | YTW **4.28%** par-weighted | Σ(ytw × par)/par = 4.280% | basket JSON | **VERIFIED-INTERNAL** |
| 6 | AI-insulation **99/100** par-weighted | Σ(insul × par)/par = **98.6**, rounds to 99 | basket JSON | **VERIFIED-INTERNAL** (rounds up; two AI-2 names dilute it — see #18) |
| 7 | Credit **87/100** par-weighted | Σ(credit × par)/par = 87.4 | basket JSON | **VERIFIED-INTERNAL** |
| 8 | "Every K-12 district certification-clear; SFUSD & Plumas **Negative**, Oakland & Hayward **Qualified**, screened out" | Parsed the cached CDE Second-Interim 2024-25 roster; confirmed SFUSD+Plumas in Negative list, Oakland+Hayward in Qualified list; confirmed NO basket district appears on either list | **CDE First/Second Interim Status Report FY24-25** (cde.ca.gov, primary) | **VERIFIED** (independent primary source) |
| 9 | Basket "Mendocino Unified" is clean | CDE list hits for "Mendocino" are Leggett Valley / Potter Valley / Willits — NOT Mendocino Unified | CDE roster (primary) | **VERIFIED** (correct entity discrimination) |
| 10 | Total IBKR commission ≈ **$215 / 2.2 bps**, ~0.2 bp/yr amortized | Modeled 5bps/1.25bps tiered + per-order min on the 24 face amounts: $130 at $1-min, $240 at $10-min | IBKR muni schedule (per prompt) + independent recompute | **VERIFIED-as-reasonable** (deck figure sits between; errs slightly HIGH = honest) |
| 11 | Median same-day spread **0.329 pt** | median of px_spread across 24 = 0.329 | basket JSON (MSRB tape) | **VERIFIED-INTERNAL** |
| 12 | Liquidity mix L1×4 / L2×7 / L3×5 / L4×8 | Reapplied the deck's own L1–L4 thresholds to spread/freq/two-sided fields | basket JSON | **VERIFIED-INTERNAL** (reconstructs exactly) |
| 13 | "42% liquid-anchor share (min 40%)" | L1+L2 par = 45%; the explicit "A-liquid" sleeve tag is only **20%** | basket JSON | **CONSISTENT but loosely labeled** — "liquid-anchor" = L1+L2, not the A-sleeve; L1-only is just 16% |
| 14 | 11 of 24 de-minimis breaches | Counted demin_breach=true | basket JSON | **VERIFIED-INTERNAL** |
| 15 | Ladder 2035–2045, 24 positions, $1.0M par | min/max maturity, count, Σpar | basket JSON | **VERIFIED-INTERNAL** |
| 16 | Max single fault-zone 18% (cap 25%) | LA Basin = 18% is the max *charted* zone — BUT $280k / **28%** of par (UC+water revenue) is omitted from the seismic chart entirely | basket JSON | **MISLEADING-BY-OMISSION** — the geographic-concentration view excludes 28% of the book; "max 18% vs cap 25%" reads more diversified than the par actually is |
| 17 | "Credit read from the official statement or governing statute… not the marketed label" | All 18 school/college GO names score **exactly 90** (class constant from security_credit_key); only **3 of 24** have issuer_verified=true | basket JSON | **OVERSTATED** — credit is a pledge-CLASS score, not per-issuer OS analysis; cover's "every credit figure traced to its primary source" implies more than was done |
| 18 | Thesis: "holds **none** of the state-General-Fund channel" | UC GRB pledge (shop's own tearsheet) includes "certain state educational appropriations"; insul 87 ≠ AI-1; 8% of par is AI-2 | basket JSON + tearsheet | **OVERSTATED (absolute)** — 8% of par carries modeled state-approp/AI-2 exposure; holdings table is honest but the bolded thesis absolute is not |
| 19 | Agency column = "class benchmark, not issue rating; EMMA publishes none" | Confirmed the column is labeled as such on slide 7 + caveats; not laundered as agency ratings | Deck text | **VERIFIED** (handled correctly) |
| 20 | "No CA school GO missed debt service through Loma Prieta/Northridge/Camp Fire" | Claim is narrowly scoped to debt-service payment; structurally supported by unlimited-ad-valorem + statutory levy; an absence-of-recorded-default claim | Domain knowledge / structural | **VERIFIED-as-careful** (well-scoped; residual = proving-a-negative + Teeter is revocable, unstated) |
| 21 | Dot-com "cut CA capital-gains revenue ~71%" and "state GF credits −4–5 notches (AA→BBB)" | Drawn from the shop's own AI-crash β-framework; not independently re-derived here | shop capgains framework (internal) | **VERIFIED-INTERNAL / UNVERIFIABLE externally in this pass** — directionally well-established (dot-com CA capgains collapse + 2003 CA GO downgrade to ~BBB are real), but the exact 71% / 4–5-notch figures are the shop's own and not re-sourced |
| 22 | Funnel 147 → 106 → 39 → 24; "27 taxable, 23 illiquid, 17 pledge/mark fails" | Not independently re-derivable from the delivered JSON (only the 24 survivors are present) | Deck text | **UNVERIFIABLE from delivered data** (consistent narrative; intermediate drop-lists not in the basket file) |
| 23 | UC LPRB a-t TEY 6.32% (lowest name, shown) | 3.143% YTW × 2.01 = 6.32 | Independent recompute | **VERIFIED** (and honestly shown despite dragging the headline) |

---

## TOP FINDINGS RANKED BY SEVERITY

| # | Severity | Exact deck quote | What the data supports | Fix |
|---|---|---|---|---|
| 1 | **Moderate** | "every pledge, price, **credit** and liquidity figure traced to its primary source" | Credit is a security-CLASS constant — all 18 school GOs = exactly 90 from a statute map; only 3/24 issuer-verified. No per-district financial read. | Say "credit reflects the *pledge structure* read from statute/OS; it is not a per-issuer financial rating." Drop "every credit figure traced to its primary source" or qualify it. |
| 2 | **Moderate** | "the state-General-Fund channel… This sleeve holds **none of it.**" | Two UC names (8% of par) are scored AI-2, and UC GRB's own pledge includes "certain state educational appropriations." | Change to "excludes income-tax-backed *state* GO/appropriation debt; two UC revenue names carry modest AI-2 residual exposure." |
| 3 | **Moderate** | Fault-zone chart: "Max single fault-zone 18% (cap 25%)" | 28% of par (UC + water revenue) is omitted from the geographic chart, so the book is less single-name/region diversified than the chart implies. | Add an "off-zone (UC/water revenue) 28%" bar or footnote so the chart sums to 100% of par. |
| 4 | **Minor** | "every K-12 district… interim-certification clear (**Positive**, no stress flag on record)" | Status is *absence from the Negative/Qualified roster* (`POSITIVE(absent)`), inferred not document-pulled per district. | Phrase as "absent from the CDE Negative/Qualified lists" — keep the (correct) parenthetical, drop the bolded "Positive." |
| 5 | **Minor** | "8.18% After-tax tax-equivalent yield" (cover, dominant stat) | Correct, but ~doubles on a ×2.01 that only a top-bracket CA resident earns; no bracket-sensitivity shown. | Add one line: "at a lower bracket / non-CA resident, the headline falls toward ~7.3% / loses the state leg." |

*(Findings 1–3 are takeaway-vs-data divergences — the kind the house standard fails on. None involves a fabricated number; all are framing overreach on top of honest underlying data.)*

---

## GRADE & HONESTY SCORE

**Letter: B+  ·  Honesty score: 84 / 100**

**Why not higher:** three framing overreaches that a reader would act on — "none of it" (contradicted by 8% AI-2 par), "every credit figure traced to its primary source" (the credit score is a class constant, not per-issuer work), and a seismic chart that silently drops 28% of the book. Each makes the sleeve look incrementally safer / more diligently verified / more diversified than the shop's own data supports. That is exactly the takeaway-vs-datum divergence the house standard grades down.

**Why not lower:** this deck does the hard honest things most promoter decks skip. The after-tax TEY reconstructs to the penny with the de-minimis ordinary-income drag correctly applied (and the headline is *below* the naïve gross-up, not above it). The proprietary scores are labeled proprietary, never laundered as agency ratings. The single most checkable external claim — the named stressed-district screen-out — **verifies against the primary CDE source**, with correct entity discrimination (Mendocino Unified ≠ the three other Mendocino LEAs on the list). The commission figure errs *high*. And a full caveats slide pre-empts the marks-are-stale, fill-slippage, rate-shock, unverified-CC, and de-minimis-bracket attacks before a reader raises them. An honestly-disclosed thin/illiquid book is CLEAN under our standard; this one mostly is.

**Verdict (one paragraph):** This is a fundamentally honest deck that earns a B+ rather than an A because its *framing layer* runs slightly ahead of its *data layer* in three specific, fixable places. The arithmetic is real — I rebuilt the 8.18% after-tax TEY from raw coupon/price/maturity and it ties out exactly, including the correct (and yield-reducing) ordinary-income treatment of de-minimis accretion, which is the single most common spot a muni pitch inflates and here does not. The proprietary insulation/credit scales are labeled as the shop's own and the agency column is honestly disclosed as a class benchmark, so there is no rating-laundering. The one fully independent primary-source check — the AB-1200 stress-district screen-out — verifies cleanly against the cached CDE rosters. What keeps it from an A is that the marketed takeaway overshoots the evidence at the edges: "holds none of the state-GF channel" is contradicted by 8% of par the deck itself scores AI-2; "every credit figure traced to its primary source" oversells a credit score that is actually a statute-class constant identical across all 18 school GOs; and the earthquake-concentration chart reads as well-diversified only because 28% of the book is left off it. None of these is a lie or a fabricated number — they are confidence-inflating framing on top of honest data — but under the house standard (grade on takeaway-vs-data divergence, not on disclosed bad facts) they are precisely the deductions to take. Fix the five quotes above and this is a defensible A-/A deck.
