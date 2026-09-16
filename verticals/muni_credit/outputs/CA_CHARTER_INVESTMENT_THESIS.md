# CA Charter School Muni Bond — Investment Thesis

**Prepared**: 2026-05-28
**Author**: Signal OS framework run, post-foundation-rebuild
**Position type**: CA-tax-advantaged muni for HNW self-managed SMA replacing institutional active CA muni manager
**Honest framing**: framework correctly classifies operator quality; bond pricing does not reflect it (verified mask via rating-compression); product value is diligence-replication + fee savings, NOT spread alpha

---

## Headline finding

The CSFA LCFF intercept (Ed Code 17199.4) creates a structural masking mechanism: the State Controller diverts per-pupil LCFF funding pre-distribution to bondholders, producing a 2-3 notch credit uplift that compresses bond spreads to a **rating-band** rather than to operator-credit fundamentals.

**Verified empirically (2026-05-28)**: within the **BB+ rating band**, the framework's two strongest empirical anchor pairs trade at **identical spreads** (143 bps over MMD AAA) despite a **33-point operator-strength differential**:

| Obligor | Rating | Operator score (0-100) | Spread to MMD AAA |
|---|---|---|---|
| **ICEF Public Schools** | BB+ | **54** (weakest in universe) | **143 bps** |
| **New Designs Charter School** | BB+ | **87** (top quartile) | **143 bps** |

Same rating → same spread → operator-credit signal invisible to bond pricing. Same structural pattern as Cal-Mortgage in CA NH muni, but mediated through ratings rather than direct insurance wrap.

**Implication for self-managed SMA**: the framework's exclusion logic is correct on operator quality (ICEF will deteriorate before New Designs), but the bond price doesn't reward you for the call. The realizable alpha is **fee-savings vs the institutional active CA muni manager who would also exclude ICEF** — ~75-150 bps/yr — not spread capture.

---

## Universe

Audited universe (post-foundation-rebuild, v2 as of 2026-05-28):

| Structure class | N | Description | Pricing behavior |
|---|---|---|---|
| **csfa_intercept** | 17 | CSFA-issued with State Controller LCFF intercept (Ed Code 17199.4). 2-3 notch rating uplift. | Trades to rating band; operator credit invisible within rating |
| **cscda_no_intercept** | 3 | CSCDA-issued, no intercept structure | Trades to operator credit; spreads ~75 bps wider than CSFA-intercept (estimated, not empirically verified at meaningful N) |
| **pcsd_lease** | 2 | Pacific Charter School Development facility-lease structure | Single-obligor signal obscured behind facility pool |
| **ccsa_jpa_pool** | 1 | CCSA Financing Authority pooled structure | Pool-level pricing; single-charter signal masked at CUSIP level |
| **private_placement** | 1 | Bank-purchased, not in capital markets | Opaque; not analyzable for spread alpha |
| **unknown_or_no_bonds** | 5 | Operator does not have public muni debt at obligor level | Not investable through this thesis |

Total active obligors with public CA charter muni debt: **23**. Plus 4 historical/distress reference obligors (Today's Fresh Start, etc.) used as positive controls.

**v1→v2 audit findings (foundation-rebuild value)**:
- 86% EIN error rate in v1 (24 of 28 verifiable EINs were wrong, including 2 placeholder-collision EINs reused across multiple obligors)
- 3 hallucinated school closures debunked (ICEF View Park, both Aveson schools)
- Rocketship reclassified from CSCDA to CSFA (structure-class correction)
- 5 par amounts corrected (Aspire $75M→$33M, Granada Hills $38M→$13.6M, Magnolia $28M→$6M, etc.)

---

## Buy list — clean basket (csfa_intercept, top operator quality)

These are the obligors with the highest framework-verified operator-strength scores. The intercept structure means bond pricing doesn't reward you for picking them over weaker operators at the same rating — but for **long-term hold-to-maturity** positions where you're avoiding credit events (rather than capturing spread differentials), these are the right names.

| Obligor | Op Score | Estimated Spread | Estimated YTM | TEY (top bracket 50.3%) | Conduit | Most recent issue |
|---|---|---|---|---|---|---|
| **Ednovate** | 94 | ~135 bps | ~5.75% | ~11.6% | CSFA | 2024 EFF, 2025 — obligated group of 4-5 campuses |
| **Da Vinci Schools** | 89 | ~105 bps | ~5.45% | ~11.0% | (intercept presumed) | Wiseburn USD partnership; uniquely-supportive structural arrangement |
| **Granada Hills Charter** | 89 | **110 bps (empirical)** | **4.20% (BBB- 2021 refunding)** | **~8.4%** | CSFA | 2021 ($13.6M) + 2024 ($8/2024) |
| **Bright Star Schools** | 87 | ~165 bps | ~6.05% | ~12.2% | CSFA | 2023 issuance |
| **New Designs Charter School** | 87 | **143 bps (empirical)** | ~5.83% | ~11.7% | CSFA | 2024 issuance (BB+) |
| **Partnerships to Uplift Communities (PUC)** | 87 | ~140 bps | ~5.80% | ~11.7% | CSFA | (3-entity split obligated group) |
| **Caliber Schools** | 87 | ~160 bps | ~6.00% | ~12.1% | CSFA | — |
| **Camino Nuevo Charter Academy** | 83 | ~130 bps | ~5.70% | ~11.5% | CSFA | — |
| **Larchmont Charter School** | 83 | ~145 bps | ~5.85% | ~11.8% | CSFA | — |

**Top recommendation**: **Granada Hills Charter** is the only name in the basket with an empirical primary-market anchor (110 bps BBB- per CSFA 2024 Conduit Financing Program Report) at the strongest end of operator quality. Best risk-adjusted hold in the basket.

**Secondary recommendation**: **Da Vinci Schools** — the Wiseburn USD partnership is a structurally unique credit enhancement (school district co-locates and partially backstops). Likely BBB-area on operator merits.

---

## Empirical-anchor view (most defensible)

The four obligors with primary-market spread anchors from the CSFA 2024 Conduit Financing Program Report:

| Obligor | Rating | Issue date | Spread (bps over MMD AAA) | Operator score | Verdict |
|---|---|---|---|---|---|
| Alliance College-Ready | BBB | 10/24/2024 | 91 | 75 | Tightest pricing in basket; weakest operator in BBB band (LAUSD multi-school 2023-2025 renewal cycle ongoing — watch) |
| Granada Hills Charter | BBB- | 8/2024 | 110 | 89 | **BEST RISK/RETURN** — empirical anchor + strongest operator |
| New Designs Charter | BB+ | 5/2024 | 143 | 87 | Wider spread reflects BB+ rating, not operator quality |
| ICEF Public Schools | BB+ | (2019 refunding context) | 143 | 54 | **AVOID** despite same spread as New Designs — operator distress not in price |

The Alliance vs Granada comparison is informative: Alliance has the WEAKER operator (75 vs 89) but trades 19 bps TIGHTER because of its BBB vs BBB- rating. Operator quality is invisible within and across rating bands.

---

## Exclude basket

These obligors have low operator-quality scores or known distress. The bond prices don't reflect their condition (rating-band compression), so an unscreened CA charter muni portfolio will hold them at the same yield as healthier names. **The framework's value is identifying them as exclusion candidates.**

| Obligor | Op Score | Why exclude | Structure class | Action |
|---|---|---|---|---|
| **ICEF Public Schools** | **54** | Bottom-quintile CAASPP + declining LCFF + declining enrollment. Form 990 recovering (+90% FY20→FY24) but academic + funding trajectory weak. Trades at 143 bps despite this — same as New Designs (op 87). | csfa_intercept | **HARD AVOID** — clearest mispricing in basket |
| **Stockton Collegiate International School** | **59** | Verified bottom-quintile math (17% vs CA charter avg 31%). Small $5.7M par 2024 issuance. | csfa_intercept | AVOID |
| **Today's Fresh Start** | (defaulted) | Historical positive control. SBE-auth closure 6/30/2015; Inglewood closure 6/30/2020; LA County BOE revocation 1/8/2020; SBE renewal denial 7/9/2020. Likely bank private placement, not in capital markets. | private_placement | NOT INVESTABLE — flag for any retail muni ETF/SMA holding (likely none, but verify) |
| **Aveson Charter Schools** | — | PCSD lease structure obscures single-operator signal. Both Aveson schools active per CDE Feb 2026 (not closed as v1 claimed), but FY24 990 shows real financial deterioration (-$1.85M net income, net assets down 45%). The bond is PCSD facility lease pool, not Aveson-specific — single-name action is moot. | pcsd_lease | AVOID PCSD facility pool exposure if framework can identify it; otherwise note as latent risk in any PCSD-exposed muni position |
| **Summit Public Schools** | — | 4 schools closed in last 5 years (Rainier, Denali, Everest, Olympus). Not currently in muni-debt universe but flagged for any future re-entry. | unknown_or_no_bonds | MONITOR |

---

## Honest TEY math

CA top-bracket TEY multiplier = 1 / (1 − 0.37 − 0.133) = 2.01×

For a $1M position in a BBB- CSFA-intercept charter at 110 bps over MMD AAA 20yr (~4.10%) = ~5.20% YTM:
- Annual tax-exempt yield: 5.20% × $1M = **$52,000**
- Taxable-equivalent yield: 5.20% × 2.01 = **10.45% TEY**
- Equivalent taxable-bond annual income: $52,000 × 2.01 = **$104,520**

For comparison: a passive CA muni ETF (e.g., NCAA, MUB) yields ~3.20-3.50% (broad investment-grade) with management fee ~25-35 bps. A self-managed CA charter SMA at ~5.20% YTM nets ~170-200 bps more yield, after which the fee differential vs an active charter SMA manager (~100 bps/yr) adds further to net edge.

**Net realizable edge vs alternative**:
- vs passive CA muni ETF: ~170-200 bps yield pickup (junkier credit) + 25-50 bps fee savings
- vs active CA charter muni SMA at 100 bps fee: ~100 bps fee savings (assuming framework matches institutional research quality)
- vs DIY-passive holding distress names unscreened: framework's exclusion of ICEF + Stockton Collegiate + similar = avoided credit loss when those names default

---

## Risk stack — read this before any allocation

**1. Charter defaults are real (not theoretical)**
- Today's Fresh Start defaulted multiple times 2015-2020 (4 separate authorizer events). This was caught only in retrospect; the bond was private placement so capital-markets impact was contained, but the operator-level distress was clear in CDE Charter Schools Division records years before resolution.
- KIPP Capital Region defaulted 2024 (cross-state; not in CA universe but indicates sector default rate)
- Charter default rate: ~3-5%/yr sector-wide. CSFA intercept REDUCES bondholder loss-given-default but doesn't eliminate it.

**2. CSFA LCFF intercept is the load-bearing structural assumption**
- The State Controller payment mechanism (Ed Code 17199.4) has not been tested in a major charter default. It's untested under stress.
- Per-pupil LCFF funding has been growing in CA but enrollment-decline at the operator level (ICEF case) means intercept revenue declines too.
- Catastrophic scenarios (CA fiscal crisis, Prop 13 restructure, major LCFF cut) would erode intercept value system-wide.

**3. Rating-band compression isn't credit-quality compression**
- ICEF and New Designs trade at the same 143 bps because they're both BB+. The bond MARKET treats them as equivalent. The framework correctly identifies they're NOT equivalent.
- If you hold the BB+ basket undifferentiated, you'll get ICEF-style operator distress at the same yield as New Designs-style operator strength.
- The framework's job is to differentiate within rating bands — but you have to ACT on the framework's signal (avoid ICEF) rather than chasing yield.

**4. Most ratings are sub-IG**
- BBB at best (Alliance, Aspire) — and only via intercept uplift
- BB+ for many obligors (ICEF, New Designs, Stockton Collegiate)
- These are NOT blue-chip muni holdings. Default risk + spread volatility under stress are real.
- Position sizing: <5% of total muni allocation per obligor; <30% of muni allocation across all charter exposure.

**5. Data quality caveats from this framework run**
- 4 empirical primary-market spread anchors; 16 modeled. The within-rating-band finding is the load-bearing measurement (ICEF=143 = New Designs=143 at same BB+). The full-universe correlation is partially tautological because modeled spreads encode the assumed compression.
- CSCDA control sample N=3 is thin. National non-CA CSCDA charters could augment but introduce cross-state LCFF-analog confounders.
- EMMA was blocked for direct CUSIP search; per-bond CUSIPs require AVIA Communications PLOM docs or Form 990 Schedule K direct pulls. Without CUSIPs, execution requires manual dealer search.
- Operator-strength scores have inflation risk for low-coverage obligors (Ednovate, Bright Star, PUC, Caliber, Larchmont, Camino Nuevo all have 3-4 verified subscores out of 6; treat as MEDIUM confidence).

**6. Liquidity is thin**
- 0 observable EMMA secondary-market trades on the universe at scrape time. Most CSFA-intercept charter bonds are buy-and-hold institutional + retail SMA. Bid-ask 50-200 bps. Strategy is hold-to-maturity, not active trading.

---

## How this differs from the CA NH muni thesis

| Dimension | CA NH muni (NH thesis) | CA Charter muni (this thesis) |
|---|---|---|
| Masking mechanism | Cal-Mortgage insurance wrap → state AA- credit | CSFA LCFF intercept → 2-3 notch rating uplift |
| Empirical anchor coverage | Bond-level CUSIPs + yields for clean + exclude basket | 4 primary-market spread anchors only; per-bond CUSIPs not pulled |
| Realizable alpha | ~30-60 bps TEY after wrap compresses signal | Diligence-replication only (fee savings ~100 bps/yr vs institutional) |
| Default risk | Lower (institutional CCRC/NH operators with multi-decade balance sheets) | Higher (charter default rate 3-5%/yr sector-wide) |
| Investment grade | Mostly insured AA- or A-rated | Mostly BBB to BB+ (sub-IG common) |
| Position cap recommendation | Up to 30-40% of muni allocation | <30% of muni allocation, with explicit operator-strength screen |
| Primary catch (this session) | Realized alpha is narrower than backtest because wrap masks signal in pricing | ICEF and New Designs trade at same 143 bps despite 33-point operator gap — exclusion of ICEF is the value-add |

---

## Action items for execution

1. **Pull per-bond CUSIPs** via AVIA Communications PLOM docs OR Form 990 Schedule K for the buy-list obligors (Granada Hills, Da Vinci, Ednovate, Bright Star, PUC). Schedule K lists exact CUSIPs by maturity for tax-exempt bond reporting.
2. **Verify current secondary-market levels** via dealer sheet or Bloomberg muni desk for actual execution prices. Modeled spreads in this thesis are MMD-anchored estimates; actual prices may vary ±20 bps.
3. **Confirm CSFA conduit-issuer covenant terms** for the chosen series. Ed Code 17199.4 intercept structure should be verified on official statement, not assumed from CSFA prefix.
4. **Set up monitoring** for: ICEF operator deterioration (CDE Dataquest annual), Alliance LAUSD multi-school renewal cycle (2023-2025), Today's Fresh Start residual exposure (if any retail muni vehicle holds the private placement).
5. **Re-run the operator-strength scoring annually** — operator quality moves faster than rating refresh cycle. Use the rubric in `data/charter_operator_signals.json` for repeatability.

---

## Bottom line

CA charter muni offers ~10-12% TEY at the BBB- to BB+ rating tier with a structural CA tax advantage. The framework's empirical contribution: identifying which obligors are mispriced (within-rating-band masking) so you can hold the BB+/BBB- tier WITHOUT also holding the operator-deteriorating names that trade at the same yield.

**The framework is the exclusion engine, not the alpha generator. ~10% TEY on a screened basket is the realistic product.**
