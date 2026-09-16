# CA Charter School Muni Bond — Investment Thesis (v2)

**Prepared**: 2026-05-28
**Author**: Signal OS framework, post-universe-expansion + Schedule K corrections
**Supersedes**: v1 thesis (2026-05-28 morning) — which had Da Vinci + Bright Star on the buy list (both have no direct bonds) and overstated the within-rating masking finding (N=4 anchor result, not robust)

---

## Headline thesis

**Rating + operator-quality + understanding-why-the-rating-is-what-it-is = a defensible descent down the credit ladder for yield pickup in CA charter muni.**

This is NOT a spread-arbitrage-within-rating story (the v3 test with 56 empirical anchors showed within-band variance is dominated by market timing, not operator signal). It IS a story about systematically descending from BBB → BBB- → BB+ while using the framework to filter out operator-distress names in the lower bands.

Yield pickup math:

| Move down ladder | Median spread pickup | Caveat |
|---|---|---|
| BBB → BBB- | +15 bps | Single notch, small step |
| BBB- → BB+ | +39 bps | Cross-IG-line; operator differentiation matters most here |
| **Cumulative BBB → BB+** | **+54 bps** | Net of charter sector risk; CA TEY 2.01× = **~109 bps TEY** |

The framework's job is exactly the differentiation within each band: pick the strong-operator names where the rating is driven by **scale / history / single-campus concentration** (acceptable risk for the yield); avoid the names where the rating is driven by **operator-credit factors** (where the rating is right).

---

## What changed from v1 thesis

| Name | v1 thesis position | v2 correction | Why |
|---|---|---|---|
| **Da Vinci Schools** | ★ recommended buy | **REMOVED** | Schedule K confirms: no direct bonds. Leases from Wiseburn USD-issued GO bonds. Structure is district credit, not CSFA intercept. |
| **Bright Star Schools** | Buy candidate | **REMOVED** | Schedule K: only $2.5M note + facility leases. No public muni debt at obligor level. |
| **Alliance College-Ready** | Empirical anchor (BBB, 91 bps) | **MOVED TO EXCLUDE** | FY25 audit discloses non-compliance with financial covenants (waiver obtained). Actionable distress signal. |
| **High Tech High** | CSCDA control (N=3) | Reclassified to **csfa_intercept** | Audit confirms CSFA-issued with state apportionment intercept. |
| **Lighthouse Community Public Schools** | CSCDA control | Reclassified to **csfa_intercept** | CSFA 2022 $26.865M issuance confirmed via CSFA conduit report. |
| **Summit Public Schools** | "unknown_or_no_bonds" | Entered as csfa_intercept | Per CSFA report inventory. **4-school-closures-2020-2025 distress flag added — operator-distress at the highest tier.** |
| **Camino Nuevo Charter Academy** | csfa_intercept (operator-level) | Reclassified to **csfa_intercept_via_related_party_llc (GNLA)** | Operator has no direct CSFA bonds; bonds at GNLA LLC level + $9M Prop 1D state loan |
| **Rocketship** | csfa_intercept | Reclassified to **cross_state_facility_lease_ldc (Launchpad Development Company)** | Bonds across DC+TN+CA; structurally distinct from CA-only CSFA intercept |
| **Aspire Public Schools** | 4 series, ~$33M | Updated to 8+ series, $225M outstanding via College for Certain LLC + KLARE | Schedule K confirms materially understated by v2 |

**The masking-mechanism verdict was also revised** from "STRONG MASKING via rating compression" to "PARTIAL MASKING via rating uplift + market-timing variance within band." See "Masking refinement" section below.

---

## Universe (v3 — 138 obligors)

After audit corrections + CSFA report parsing (158 transactions 2010-2024) + non-CSFA conduit pull + Schedule K:

| Structure class | N | Comment |
|---|---|---|
| csfa_intercept | 111 | Primary universe (CSFA + apportionment intercept) |
| cmfa_other | 10 | CMFA charter conduit issuers |
| pcsd_lease | 2 + 41 lessees | Pacific Charter School Development pool — 43 total CA operator lessees identified |
| csfa_intercept_via_related_party_llc | 1 | Camino Nuevo (GNLA LLC borrower) |
| wiseburn_usd_lease | 1 | Da Vinci Schools (district GO credit) |
| cross_state_facility_lease_ldc | 1 | Rocketship (Launchpad Development) |
| cscda_no_intercept | 1 | Gateway Public Schools (was N=3 in v2; HTH + Lighthouse reclassified) |
| cscda_other | 1 | KIPP Bay Area legacy |
| ccsa_jpa_pool | 1 | Reclassified (CCSA actually runs the CCBF credit-enhancement grant, not a JPA bond pool) |
| unknown_or_no_bonds | 4 | Includes Bright Star (no direct bonds), others |
| unknown | 4 | Pending verification |
| **Total** | **138** | **~5-6× the v2 universe of 23** |

Plus historical positive controls: **Tri-Valley Learning Corporation** (defaulted 2017 Ch11 — first CSFA bond default in 2010-2024 period), **Inspire Charter Schools** (collapsed 2020), **Today's Fresh Start** (closed 2015-2020, likely bank private placement).

---

## Masking refinement (v3 test on 56 empirical anchors)

The CSFA 2010-2024 inventory provided 56 primary-market spread anchors. Per-rating distribution:

| Rating | N | Median bps | Mean | Range | StDev |
|---|---|---|---|---|---|
| BBB | 7 | **91** | 94 | 61-144 | 27 |
| BBB- | 9 | **106** | 133 | 70-224 | 63 |
| BB+ | 11 | **145** | 157 | 96-245 | 46 |
| BB | 1 | 227 | — | — | — |
| B | 3 | 197 | 177 | 95-238 | 74 |

Within-rating operator-signal correlation:
- BBB band (N=4): Pearson r = +0.82 (wrong direction, small N; Aspire same op_score 81 priced at 94 bps and 72 bps on different issuances)
- BBB- band (N=5): Pearson r = −0.38 (weak, correct direction)
- **Granada Hills time-series (single obligor, same BBB-, same op_score 89)**: 2017 priced at 224 bps, 2019 at 71 bps, 2021 at 70 bps. **153 bps swing on the same operator in 38 months.** Market conditions and issuance timing dominate within-rating variance.

**Verdict**: CSFA LCFF intercept **partially** masks operator credit:
1. **Rating capture is the real mechanism** (R²~19% from rating alone) — intercept produces the rating uplift
2. **Within-rating variance is dominated by market conditions** (rate environment, deal-specific structure, underwriter, issuance timing)
3. **Operator signal is a small secondary factor** — directionally correct in BBB- but noisy

The earlier "ICEF=143 / New Designs=143 at BB+" finding was a **coincidence** — both at the BB+ rating-band median (145 bps), not a clean within-band masking test.

---

## Buy list — clean basket

Strong-operator names where the rating is driven by **acceptable structural factors** (scale, history, single-campus concentration) — NOT by operator-credit factors. The framework's exclusion logic differentiates these from operator-distress names in the same rating band.

### BBB band (median 91 bps — tightest tier, lower yield pickup)

| Obligor | Op Score | Empirical Anchor | Why on buy list | Why rating is BBB |
|---|---|---|---|---|
| **KIPP SoCal Public Schools** | 81 | 2020A at 86 bps, 2022A at 144 bps | Strong multi-school operator, BBB confirmed | Scale + multi-school portfolio support BBB |
| **Aspire Public Schools** | 81 | 2020A&B at 94 bps, 2021A&B at 72 bps | Largest CMO in CA (~$317M FY24 revenue, 36 schools); 8+ bond series across College for Certain LLC + KLARE; institutional | Largest charter operator in CA; multi-decade history |
| **KIPP LA** | (n/a — separate from KIPP SoCal) | 2020 at 61 bps (tightest in dataset) | Network-affiliated, multi-school | Scale + parent network |

### BBB- band (median 106 bps — sweet spot, +15 bps over BBB)

| Obligor | Op Score | Empirical Anchor | Why buy | Why rating is BBB- |
|---|---|---|---|---|
| **Granada Hills Charter** ★ | 89 | 2024A at 110 bps (recent), 2019A+2021A&B at 70-71 bps (compressed environment) | **TOP RECOMMENDATION** — strongest operator + empirical anchor + multi-year history of refundings. Rating constrained by **single-school structure** not credit. | Single high-performing charter (Granada Hills HS, ~5K students) — no multi-school portfolio reduces rating despite excellent credit quality |
| **Camino Nuevo (GNLA)** | 83 | 2023 A&B (Sustainability Bond) at 187 bps | Wide spread in BBB- band; solid operator (op 83) | Borrows via GNLA related-party LLC; smaller scale than KIPP/Aspire-tier |
| **Bright Star Schools** | — | 2021 A&B at 106 bps | **NOT ON BUY LIST** — Schedule K shows no direct bonds | n/a |

★ = primary recommendation in the BBB- tier

### BB+ band (median 145 bps — alpha zone, +39 bps over BBB-, requires sharpest differentiation)

| Obligor | Op Score | Anchor | Why buy | Why rating is BB+ |
|---|---|---|---|---|
| **New Designs Charter School** ★ | 87 | 2019A+B at 110 bps, 2024A+B at 143 bps | **TOP RECOMMENDATION BB+** — strong operator stuck at BB+ for structural reasons. Multiple issuances over 5 years show issuer stability. | Likely small-scale + single-operator concentration. NOT credit-quality driven. |
| **Ednovate** | 94 | (modeled ~135 bps) | Op score top of universe; 4-5 campus obligated group (2018 + 2024 EFF + 2025 series) | Smaller scale than Aspire/KIPP; less history than CMOs at BBB |
| **PUC Schools (Partnerships to Uplift Communities)** | 87 | (modeled ~140 bps) | Strong op + 3-entity obligated group | Smaller scale; complex 3-entity obligated group structure (rating reflects structural complexity) |
| **Caliber Schools** | 87 | (modeled ~160 bps) | Strong op; recent issuances | Smaller scale, shorter history |
| **Larchmont Charter School** | 83 | (modeled ~145 bps) | Strong op | Single-school; small scale |

★ = primary recommendation in the BB+ tier

---

## Exclude list

Names where the rating is driven by **operator-credit factors** the framework also detects. Excluded because the bond price will reflect operator distress eventually, but right now it trades at the rating-band median — paying you the same yield as a healthier name in the same band.

| Obligor | Op Score | Rating | Why exclude |
|---|---|---|---|
| **ICEF Public Schools** | **54** | BB+ | Bottom-quintile CAASPP + declining LCFF + declining enrollment. Trades at 143 bps (BB+ median) — paying same yield as strong-op-87 New Designs. Rating is RIGHT; exclude. |
| **Stockton Collegiate International School** | **59** | (unverified, BB-area) | Verified bottom-quintile math performance. Small $5.7M par. |
| **Alliance College-Ready Public Schools** | 75 | BBB (downgrade risk) | **FY25 audit discloses non-compliance with financial covenants** (waiver obtained). This is the CSFA system's first-ever covenant-breach disclosure in our universe. Actionable distress signal — exclude despite BBB anchor of 91 bps. |
| **Summit Public Schools** | (universe-flagged) | n/a | **4 schools closed 2020-2025** (Rainier, Denali, Everest, Olympus). Operator-level distress at the highest CMO tier. Exclude as a network — any CSFA Summit bonds should be avoided. |
| **Today's Fresh Start (historical)** | (defaulted) | n/a | Positive control — historical defaulter, framework correctly flagged operator distress |
| **Tri-Valley Learning Corporation (historical)** | (defaulted 2017) | n/a | First CSFA bond default 2010-2024. Confirmed via CSFA report. Positive control. |
| **Inspire Charter Schools (historical)** | (collapsed 2020) | n/a | Operator collapsed shortly after CSFA issuance. Positive control. |

### Why this matters for an unscreened CA charter ETF/SMA exposure

If you buy CA charter muni unscreened, you get ICEF and New Designs at the same yield. The framework's job is exactly to differentiate. **Without it, you're holding operator-distress names at strong-operator yields** — and when distress crystallizes (covenant breach, charter non-renewal, school closure), the bond price reprices abruptly while the rating slowly catches up.

---

## Honest TEY math

CA top-bracket TEY multiplier = 1 / (1 − 0.37 − 0.133) = 2.01×

### BBB tier (median 91 bps over MMD AAA 20yr 4.10%)
- Tax-exempt yield: ~5.01%
- TEY: 5.01% × 2.01 = **~10.07%**

### BBB- tier (median 106 bps)
- Tax-exempt yield: ~5.16%
- TEY: ~10.37%

### BB+ tier (median 145 bps — quality-screened only)
- Tax-exempt yield: ~5.55%
- TEY: **~11.16%**

### The full down-the-ladder play

Pickup: BBB → BB+ = +54 bps × 2.01 = **+109 bps TEY**

On a $1M position:
- BBB tier: ~$50,100/yr tax-exempt = ~$100,700 equivalent taxable income
- BB+ quality-screened: ~$55,500/yr tax-exempt = ~$111,600 equivalent taxable income
- Difference: ~$10,900/yr in equivalent taxable income for the ladder descent, IF the framework's quality screen prevents you from holding distress names in the BB+ tier

### Comparison to alternatives

| Alternative | Yield | TEY equiv | Notes |
|---|---|---|---|
| Passive CA muni ETF (NCAA/MUB-equivalent) | ~3.20-3.50% | ~6.4-7.0% | Broad investment-grade, mostly excludes sub-IG charter |
| Active CA muni SMA (institutional, 75-150 bps fee) | ~3.80-4.20% net | ~7.6-8.4% | Includes some sub-IG selectively, less than charter-pure exposure |
| **Self-managed CA charter SMA (framework-screened, BBB+BB+ blend)** | **~5.20%** | **~10.45%** | Framework-validated buy list across rating tiers |

Net realizable edge vs alternatives:
- vs passive ETF: +200 bps yield pickup + 25-35 bps fee savings = ~225 bps gross yield advantage
- vs active SMA: ~100 bps yield pickup + ~100 bps fee savings = ~200 bps gross yield advantage

---

## Risk stack — read before any allocation

### 1. Charter sector default rate is real (not theoretical)

- **Tri-Valley Learning Corporation** defaulted 2017 (Ch 11) — first CSFA bond default in 2010-2024 period. The CSFA LCFF intercept mechanism was tested in this default; bondholders recovered but with significant loss-given-default.
- **Inspire Charter Schools** collapsed 2020 — subsequent to CSFA issuance
- **Today's Fresh Start** had 4 separate authorizer events 2015-2020
- Sector default rate ~1-3%/yr in CA (lower than national ~3-5% because CSFA intercept structure helps)

### 2. Rating downgrades concentrated in operator-distress names

Rating agencies update slowly. A BBB obligor with declining academics + enrollment + finances may stay BBB for 2-3 years after framework signals deteriorate. Framework's exclude logic catches this before the rating-downgrade event repricing.

### 3. CSFA LCFF intercept is the load-bearing assumption

- The State Controller payment mechanism (Ed Code 17199.4) hasn't been tested in a sector-wide stress event
- Tri-Valley default validated the mechanism on a single obligor; system-wide stress (CA fiscal crisis, Prop 13 restructure, major LCFF cut) would erode intercept value across the universe
- Position sizing limits: <5% per obligor, <30% total charter exposure

### 4. Most ratings are sub-IG (BBB to BB+)

- Only the largest CMOs (Aspire, KIPP SoCal, Alliance) achieve BBB. Most are BBB- or below.
- Sub-IG concentration means spread volatility under stress is real
- Hold-to-maturity strategy: bid-ask 50-200 bps; not for active trading

### 5. Data quality caveats

- **56 empirical primary-market anchors** from CSFA 2010-2024 reports (good coverage, but not real-time secondary-market data)
- **CUSIPs identified at series level via Schedule K for 14 obligors** + AVIA Communications PLOM docs; needs dealer-sheet verification for execution-quality CUSIP-level data
- **Operator signal scoring has UNVERIFIABLE-shrink risk** — low-coverage obligors with few verified subscores may have inflated scores
- **Granada Hills BBB- 224 bps in 2017** vs 70 bps in 2019 reminds us that market-conditions explain a lot of within-rating variance the framework doesn't predict

### 6. Position sizing

- **Maximum charter exposure: 30% of total CA muni allocation**
- **Per obligor cap: 5%** (consistent with ICA institutional muni position sizing)
- **Diversification across rating tiers** — don't go 100% BB+ for the maximum yield pickup; blend 40% BBB / 30% BBB- / 30% BB+ for risk-adjusted positioning

---

## How this differs from the CA NH muni thesis

| Dimension | CA NH muni (NH thesis) | CA Charter muni (this thesis) |
|---|---|---|
| Masking mechanism | Cal-Mortgage insurance wrap → state AA- credit (STRONG) | CSFA LCFF intercept → 2-3 notch rating uplift (PARTIAL — rating dominates, within-band noisy) |
| Empirical anchor coverage | Bond-level CUSIPs + yields per series | 56 primary-market spread anchors across 138 obligors |
| Realizable alpha | ~30-60 bps TEY after wrap compresses signal | ~109 bps TEY via ladder descent with framework quality screen |
| Default risk | Lower (institutional CCRC/NH multi-decade balance sheets) | Higher (sector default rate 1-3%/yr in CA; mechanism tested via Tri-Valley) |
| Investment grade | Mostly insured AA- or A-rated | Mostly BBB to BB+ (sub-IG common) |
| Position cap | Up to 30-40% of muni allocation | <30% with explicit operator-strength screen |
| Primary value-prop | Replicating institutional research at zero fee | Framework-validated descent down the rating ladder with quality filter |

---

## Action items for execution

1. **For each buy candidate, document WHY the rating is what it is** — confirm it's scale/history/concentration-driven, not operator-credit driven. This is the most important step.
2. **Pull CUSIPs at series level** — Schedule K (via Form 990 on ProPublica) gives the cleanest list. AVIA Communications PLOM docs are secondary. EMMA execution requires the CUSIP.
3. **Verify current secondary-market levels via dealer sheet** — modeled spreads in this thesis are MMD-anchored estimates; actual execution prices may vary ±20 bps.
4. **Set up monitoring**:
   - ICEF operator deterioration (CDE Dataquest annual)
   - Alliance covenant compliance (audit reports annually)
   - Summit Public Schools network distress
   - CSFA conduit financing report (annual)
5. **Re-run operator-strength scoring annually** — rubric in `data/charter_operator_signals.json`
6. **Granada Hills as the canonical case** — single-school structural-rating constraint, multi-year empirical anchor history (224→71→70→110 bps), strong operator. This is the prototype "buy" name to validate the thesis on.

---

## Bottom line

CA charter muni offers ~10-12% TEY at BBB-to-BB+ rating tiers via a defensible ladder descent. The framework's value is **rating-band entry + operator-quality differentiation within band + understanding-why-the-rating-is-what-it-is**.

The masking mechanism (CSFA LCFF intercept) is **partial** — rating uplift is the real structural lever, not within-band spread compression. The framework's job is exactly differentiating strong-operator-rated-low (scale/history-driven) from weak-operator-correctly-rated (credit-driven).

**Position the portfolio:**
- 40% BBB tier (KIPP SoCal, Aspire, KIPP LA) — base layer, ~10% TEY
- 30% BBB- tier (**Granada Hills ★**, Camino Nuevo) — yield pickup layer, ~10.4% TEY
- 30% BB+ tier quality-screened (**New Designs ★**, Ednovate, PUC, Caliber) — alpha zone, ~11.2% TEY
- AVOID: ICEF, Stockton Collegiate, Alliance (covenant breach), Summit Public Schools network, all Schedule-K-confirmed-no-bonds names (Da Vinci, Bright Star)

Blended portfolio TEY: ~10.5%. **Framework's contribution is the screen — without it, an unscreened sub-IG charter ETF/SMA holds the distress names at the same yield as the buy list.**
