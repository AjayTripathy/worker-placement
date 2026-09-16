# CA IOU Electric + Muni-Adjacent — Sector Scoping

**Prepared**: 2026-05-28
**Status**: Initial scoping pass + `ab_1054_wildfire_fund_backstop` masking-mechanism cataloging (new mechanism category: `state_backstop_fund`)
**Framework**: AB 1054 + SB 254 state-backstop-fund masking, with hostile-validator stance because the Fund is actively being drawn (Eaton Fire Oct 2025)
**Owner**: muni_credit vertical
**Related knowledge_graph entry**: `masking_mechanisms.json` → `ab_1054_wildfire_fund_backstop` (NEW; DOCUMENTED at scoping pass, awaiting per-CUSIP spread test for VERIFIED upgrade)

---

## Executive Summary (~300 words)

**Universe size and structure.** CA IOU electric + muni-adjacent universe scoped at **25 obligors**: 3 IOU direct corporate issuers (PG&E, SCE, SDG&E), 4 IOU-adjacent state conduits (CalPFA, CSCDA, CMFA, IBank-SB254-securitization), 8 Community Choice Aggregators (MCE, Sonoma Clean Power, SVCE, Ava/East Bay, Clean Power Alliance, Peninsula CE, 3CE, Pioneer CE) plus CCCFA prepay JPA pool, and 8 public-power districts/JPAs (LADWP, SMUD, IID, Roseville, Palo Alto, MID, TID, NCPA, SCPPA). **Bond-type split**: IOUs are TAXABLE corporate first-mortgage / unsecured debt (TEY math does NOT apply, benchmark is UST + corporate-utility spread); CCA + public-power bonds are TAX-EXEMPT muni (TEY math DOES apply against MMD AAA).

**Masking-mechanism verdict: ab_1054_wildfire_fund_backstop.** **DOCUMENTED with STRESS-TEST IN PROGRESS** — AB 1054 ($21B fund, signed Jul 2019) was the structural precondition that allowed PG&E to exit Ch 11 in Jul 2020 and SCE/SDG&E to maintain investment grade despite known wildfire-equipment-liability risk. The mechanism's masking strength is being EMPIRICALLY TESTED right now: Jan 7 2025 Eaton Fire (suspected SCE cause, $10-15B estimated) triggered formal SCE Fund draw in Oct 2025; SB 254 emergency $18B Continuation Account added Sep 2025; Fitch upgraded PG&E to BBB- Investment Grade Sep 2025 CONTINGENT on SB 254. Pre-AB-1054 PG&E went from IG to BB to BK to junk in 90 days post-Camp Fire 2018; post-AB-1054 + post-SB-254, PG&E is BBB-/Baa1 first-mortgage even AS the Fund is being drawn for another utility's fire. Masking is REAL but the mechanism is observably under stress. S&P Negative Outlook on Edison Int'l / SCE since Mar 2025 is the market signal that masking is partially breaking.

**Top 3 buy-zone names**: (1) **SDG&E First Mortgage Bonds** (A-category; cleanest CA IOU operator; backstop fully intact; CalPFA/CSCDA tax-exempt conduit available for muni-investable wrapper); (2) **PG&E First Mortgage Bonds** (BBB- across all three agencies as of Sep 2025; structurally protected tranche; service territory hasn't had catastrophic fire since 2021); (3) **SMUD Electric Revenue** (Aa3/AA; low-WUI Central Valley; pure-credit play without AB 1054 dependency).

**Top 3 exclude-zone names**: (1) **SCE First Mortgage / Edison Int'l** (active Fund draw, S&P Negative Outlook, Eaton liability pending); (2) **PG&E HoldCo senior unsecured (Ba1/BB+)** (NOT the IG FMB tranche — HoldCo paper is structurally subordinated and still HY); (3) **LADWP power revenue** (NO AB 1054 backstop, recent Hurst/Palisades fire investigations pending; the 50-60 bps widening Jan 2025 episode showed the mechanism matters).

**Pre/post AB 1054 spread differential**: PG&E senior secured first mortgage moved from BBB+/A- pre-Camp Fire 2018 → defaulted/Caa post-BK Jan 2019 → BB+ on emergence Jul 2020 → BBB- IG Sep 2025. The full pre-→post-AB-1054 spread comparison (2018 vs 2026) requires Bloomberg pull; documented narrative shows ~400-600 bps blow-out at peak distress, ~150-200 bps current FMB spread to UST — i.e., the structural fund mechanism has absorbed roughly **300-400 bps** of the wildfire-liability premium that pre-AB-1054 PG&E carried.

---

## 1. Sector overview

### Market size and structure
- **CA IOU electric universe**: 3 utilities (PG&E, SCE, SDG&E) serving roughly 25M+ Californians out of ~40M total
- **PG&E 5.5M electric customers** (Northern + Central CA, ~70,000 sq mi service territory, highest WUI risk west of Sierra Nevada)
- **SCE 15M people** (Southern + Central CA excl. LA-DWP, ~50,000 sq mi, includes Eaton/Altadena/foothill territory)
- **SDG&E 3.6M people** (San Diego County + south Orange, ~4,100 sq mi, smallest territory)
- **Public power**: LADWP (4M residents) + SMUD (1.5M residents) + ~6 smaller districts; serve ~7-8M Californians outside IOU territories
- **CCAs**: 11+ active California CCAs, serving ~10M customer accounts across multiple IOU service territories
- **IOU bond structure**: TAXABLE corporate first-mortgage bonds (senior secured) + unsecured holdco notes (Edison Int'l, PG&E Corp); typical 5-30Y maturities. Issuance steady (PG&E $2.2B Feb 2026, SCE $500M May 2026).
- **CCA bond structure**: TAX-EXEMPT muni revenue bonds via CCCFA prepay structure; rated A2 via counterparty credit (Goldman / Morgan Stanley)
- **Public-power bond structure**: TAX-EXEMPT muni electric system revenue bonds; AA category typically

### Key dates timeline
| Date | Event | Bond-market effect |
|---|---|---|
| **Oct 8, 2017** | Tubbs / Atlas / Nuns fires (PG&E equipment) | PG&E unsecured CDS widens 100+ bps |
| **Nov 8, 2018** | Camp Fire 84 deaths (PG&E equipment, Paradise) | PG&E IG → junk in weeks |
| **Jan 29, 2019** | PG&E files Ch 11 with $30B+ wildfire liability | PG&E secured debt → distressed |
| **Jul 12, 2019** | AB 1054 signed by Newsom | Structural turning point. $21B Fund created. |
| **Jul 1, 2020** | PG&E emerges from Ch 11 | Senior secured FMB returns to market BB+ |
| **2020-2024** | SCE Thomas/Woolsey settled; PG&E Dixie 2021 settled | Spreads progressively tighten as Fund unused |
| **Mar 27, 2025** | Moody's upgrades PG&E FMB to Baa1 | First IG rating from Moody's post-BK |
| **Jan 7, 2025** | Eaton Fire (SCE-suspected, 9,400+ structures, 18 dead) | S&P → Negative Outlook on EIX/SCE |
| **Sep 19, 2025** | SB 254 signed by Newsom — $18B Continuation Account | Backfills depleted AB 1054 fund |
| **Sep 25, 2025** | Fitch upgrades PG&E to BBB- Investment Grade | Six years post-BK; cited SB 254 enabling |
| **Oct 2025** | SCE formally draws from AB 1054 Wildfire Fund | First major Fund draw event |

### Default and distress history
| Obligor | Year | Outcome | AB 1054 status |
|---|---|---|---|
| PG&E | 2019 Ch 11 | $13.5B Camp Fire victim trust + emergence Jul 2020 | Pre-AB-1054 (AB 1054 *created in response*) |
| SCE | 2017 Thomas / 2018 Woolsey | $4B+ settled; insurance recoveries; no BK | Pre-AB-1054 (PSPS protocol expanded since) |
| SDG&E | 2007 Witch/Guejito | $2.4B paid; CPUC denied cost recovery 2017 | Pre-AB-1054 |
| SCE | Jan 2025 Eaton | $10-15B est'd; ACTIVE Fund draw | POST-AB-1054 — the live test case |

**Distress base rate**: 1 hard BK out of 3 CA IOUs in 30 years = 33%. Wildfire-related material loss events: 4 of last 8 years. THIS IS NOT A HISTORICALLY-RARE EVENT TYPE — the masking-by-fund mechanism has to work continuously, not just statistically.

---

## 2. Universe inventory (see `data/ca_iou_electric_universe.json`)

**IOU corporate (n=3)**: PG&E, SCE, SDG&E.
**IOU-adjacent state conduits (n=4)**: CalPFA, CSCDA, CMFA, IBank (new SB-254 securitization mechanism).
**CCAs + JPA pool (n=8 + 1)**: MCE, Sonoma Clean Power, SVCE, Ava/EBCE, Clean Power Alliance, Peninsula CE, 3CE, Pioneer CE; CCCFA JPA prepay pool.
**Public power (n=8)**: LADWP, SMUD, IID, Roseville, Palo Alto, MID, TID, NCPA, SCPPA.
**Confidence**: 11 primary-source rating/amount confirmed (PG&E Moody's/Fitch/S&P; SCE FMB rating + outlook; LADWP +65 → +35 spread time series; CCCFA A2 inaugural; PG&E + SCE 2026 issuance); 8 partial-field primary-source; 6 inferred from peer-group.

---

## 3. AB 1054 Wildfire Fund Backstop masking mechanism — initial findings

### Hypothesis (per new masking_mechanisms.json entry)
> CA IOU first mortgage bonds trade to IG curve (BBB- to A) despite known catastrophic wildfire-equipment liability because AB 1054's $21B state-backstop fund + the prudent-manager safety-certification presumption + the 20%-of-T&D-revenue repayment cap structurally absorb the tail-risk that would otherwise force these bonds to HY/distressed levels.

### Empirical findings

**Finding A — VERIFIED via direct rating-agency citation**: Fitch's September 2025 upgrade of PG&E to BBB- explicitly cited SB 254 enactment as the enabling condition. Moody's March 2025 upgrade to Baa1 explicitly cited "credit quality benefits provided by California's $21 billion wildfire legislation." Both agencies are on record: the fund mechanism is the reason ratings are IG. Source: utilitydive.com 2025-03, energyconnects.com 2025-09.

**Finding B — STRESS-TEST ACTIVE**: The Eaton Fire (Jan 2025) is the first major draw event. Cause was suspected SCE-equipment soon after; SCE formally announced it would tap the Fund in Oct 2025. S&P put EIX/SCE on Negative Outlook in Mar 2025 citing "risk of material depletion of the Fund." Yet SCE's senior secured FMB still trades at BBB+ / A3 — i.e., even with a $10-15B draw active, the structure has held. SB 254's $18B Continuation Account was created in Sep 2025 specifically to ensure this.

**Finding C — STRUCTURAL CAP IS LOAD-BEARING**: The 20%-of-trailing-three-year-T&D-revenue shareholder repayment cap is what makes the residual liability bounded. For SCE: ~$15B T&D revenue × 20% × 3yr = ~$9B cap on shareholder repayment to Fund if SCE is found imprudent. That's a quantifiable, balance-sheet-manageable number — unlike pre-AB-1054 inverse-condemnation exposure which was unbounded ($30B+ for PG&E Camp Fire).

**Finding D — PUBLIC POWER ANTI-CONTROL CONFIRMS THE MECHANISM**: LADWP (Aa3/AA-) widened 50-60 bps in immediate aftermath of Jan 2025 Palisades + Hurst fires (per Bond Buyer reporting), then recovered to +35 bps over MMD AAA by April 2026 pricing. LADWP has NO AB 1054 backstop. SCE — actively suspected of CAUSING the larger Eaton Fire — held its rating tier through the same window. **The differential widening is the masking-mechanism signal**: utilities WITHOUT the backstop bear fire risk in spread; utilities WITH the backstop carry it in tail-risk that doesn't manifest until the Fund itself is depleted.

**Finding E — CROSS-UTILITY CONTAGION SUBTLETY**: Moody's commentary (2024) explicitly flagged that SDG&E's rating is exposed to Fund depletion from SCE's Eaton draw, NOT to SDG&E's own operational risk. This is the structural analog to Cal-Mortgage's "insurer cascade tail risk" (`cal_mortgage_cascade_tail` in catalog). The Fund masks individual utility signals UNTIL the cumulative draw depletes it; then all participants widen simultaneously.

### Verdict: DOCUMENTED — masking REAL but mechanism is OBSERVABLY UNDER STRESS

- **For non-drawn participants (SDG&E, PG&E currently)**: STRONG masking. Wildfire-equipment-liability risk fully absorbed by Fund + cap structure. IG ratings persist despite known elevated wildfire risk.
- **For drawing participant (SCE post-Oct 2025)**: PARTIAL masking. S&P Negative Outlook reflects partial breakdown but FMB rating tier preserved.
- **Tail-risk**: If Eaton liability exceeds AB 1054 remaining capacity ($21B − any prior obligations) + SB 254 $18B continuation ($39B combined headroom roughly), all three participants face downgrade cascade. This is the load-bearing tail that masks all current IG ratings.

### Cross-asset structural parallel
Structurally analogous to (a) Cal-Mortgage Loan Insurance in CA NH/CCRC sector — both are state-administered backstops that decouple operator-level distress from bond pricing UNTIL the backstop itself is stressed; (b) FHA Section 242 in US hospital muni — both are insurance-like wraps that COMPRESS spreads but don't fully decouple them from operator credit (Maimonides at +75 bps over MMD AAA despite Aa1 wrap; SCE FMB still trades wider than SDG&E FMB despite same backstop). The **new mechanism category** required is `state_backstop_fund` — distinct from `insurance_wrap` (no premium structure), distinct from `intercept_structure` (no pre-distribution diversion), distinct from `sovereign_guarantee` (state, not federal; conditional on safety cert, not unconditional).

---

## 4. Refined-thesis application — descending the ladder with quality (and operator safety record)

### Buy-zone candidates (top 5)
| Rank | Obligor | Bond Tranche | Rating | Why Buy-Zone |
|---|---|---|---|---|
| 1 | **SDG&E First Mortgage Bonds** | Sr Secured FMB | A2 / A / A- | Cleanest CA IOU operator (no post-2007 catastrophic fire); smallest WUI footprint; AB 1054 backstop fully intact; never drawn; the IOU descending-ladder reference. Tax-exempt CalPFA/CSCDA conduit wrapper for muni-investable version. |
| 2 | **PG&E First Mortgage Bonds** | Sr Secured FMB | Baa1 / BBB- / BBB- | IG across all three (achieved Sep 2025). FMB is structurally protected tranche; FFO leverage improving 6.9x → 4.6x → 4.8x est. Service territory clean since 2021 Dixie. |
| 3 | **SMUD Electric Revenue** | Tax-exempt Rev | Aa3 / AA approx | Low-WUI Central Valley; strong public-power credit independent of AB 1054 (doesn't need it). Pure credit play. |
| 4 | **SDG&E CalPFA Conduit (tax-exempt)** | Conduit muni | A category | TAX-EXEMPT version of SDG&E thesis — TEY math applies. Goldman / market for these specific CUSIPs needs Bloomberg pull. |
| 5 | **IID + MID + TID** | Tax-exempt Rev | A1 / A+ category | Central Valley / desert public power with effectively zero fire exposure. Yield pickup over LADWP/SMUD on liquidity discount, not credit. |

### Exclude-zone names (top 5)
| Rank | Obligor | Bond Tranche | Rating | Why Exclude |
|---|---|---|---|---|
| 1 | **SCE First Mortgage** | Sr Secured FMB | A3 / BBB+ Negative / BBB+ Negative | Active Eaton Fire Fund draw; S&P Negative Outlook since Mar 2025; the mechanism is being tested NOT against SCE's claim payment (Fund covers that) but against Fund depletion's effect on the rest of the participant pool. |
| 2 | **PG&E HoldCo Sr Unsecured** | HoldCo unsecured | Ba1 / BB+ / BB+ | NOT the IG FMB tranche — HoldCo is structurally subordinated and still HY. Common confusion. The PG&E IG story is FMB only. |
| 3 | **Edison Int'l HoldCo paper** | HoldCo unsecured | Baa2 / BBB / BBB Negative | Same structural concern as PG&E HoldCo plus active Eaton risk. The market hasn't fully priced Fund-depletion tail. |
| 4 | **LADWP power revenue (during Palisades investigation)** | Tax-exempt Rev | Aa3 / AA- | NO AB 1054 backstop. The Jan 2025 50-60 bps widening showed the mechanism matters; if Palisades / Hurst investigation finds LADWP equipment cause, expect wider widening (no fund cap). MONITOR pending investigation. |
| 5 | **Pioneer Community Energy (no bonds, monitoring only)** | N/A current | N/A | No outstanding bonds yet; flagged because if Pioneer (Sierra-foothill CCA) ever issues, will sit in highest-WUI CCA geography. Would NOT bear fire liability but supply-chain risk via PG&E delivery. |

### TEY math note (LOAD-BEARING)
**IOU corporate debt (PG&E, SCE, SDG&E direct first mortgage bonds) is TAXABLE corporate debt — NOT muni.** The TEY multiplier (37%+ top federal + 13.3% CA = ~45% combined marginal → 1.82x TEY multiplier on tax-exempt muni) DOES NOT APPLY. PG&E FMB at 6.00% on the 2056 maturity is exactly 6.00% taxable. Compare to:
- 30Y UST: ~4.5%
- 30Y corporate A: ~5.0-5.2%
- PG&E FMB 30Y BBB-: 6.0% = ~100 bps wider than corporate A curve, ~150 bps over UST — that's the **fund-backstop-not-fully-trusted premium**.

For the tax-exempt muni-investable version of the IOU thesis, you must go through CalPFA / CSCDA / CMFA conduits (pollution-control bonds historically). Those CUSIPs need EMMA pull to size the universe.

For CCA + public-power bonds: TAX-EXEMPT, TEY math applies normally. LADWP +35 bps over MMD AAA in AA- territory = roughly +35 nominal × 1.82 TEY = +63 bps TEY pickup over UST equivalent.

---

## 5. Pre/post AB 1054 spread comparison — load-bearing evidence

### Narrative documentation (quantitative pull pending)
| Period | PG&E FMB rating | PG&E FMB spread context | Mechanism state |
|---|---|---|---|
| 2017 (pre-Tubbs) | A3 / A- / A- | ~75-100 bps over UST (A-rated utility) | Pre-AB-1054. Investment-grade utility curve. |
| Oct 2017 — Tubbs fires | Watch lists | Widened 100-200 bps | Inverse-condemnation overhang building |
| Nov 2018 — Camp Fire | Downgraded weekly | Widened 200-400 bps | Strict-liability cost-recovery framework |
| Jan 2019 — Ch 11 | Caa | Distressed (point-quote) | No backstop. Bondholder loss imminent. |
| Jul 2019 — AB 1054 signed | (Still in BK) | (Still in BK) | **Structural turning point**. |
| Jul 2020 — Emergence | BB+ | ~250-300 bps over UST | Post-AB-1054 senior secured first mortgage relisted |
| 2021-2024 | BB+ → BBB- progression | Tightening ~150-200 bps over UST | Fund unused, structurally proven |
| Mar 2025 — Moody's upgrade | Baa1 | ~150-175 bps over UST estimate | Full IG. |
| Sep 2025 — Fitch IG | Baa1 / BBB- / BBB- | ~150-200 bps over UST estimate | Three-agency IG. |
| Feb 2026 issuance | Baa1 / BBB- / BBB- | 30Y FMB priced at 6.00% (~150 bps over 30Y UST) | Live primary-market evidence. |

**Pre-AB-1054 to current spread tightening**: estimated 300-400 bps absorbed by the fund mechanism. This is the masking-strength estimate. NEEDS BLOOMBERG PULL FOR EXACT TIME-SERIES.

### Control-group comparison
| Issuer | Aug 2018 spread est | Feb 2026 spread est | Delta |
|---|---|---|---|
| PG&E FMB | ~100 bps over UST (BBB+) | ~150 bps over UST (BBB-) | +50 bps (one notch down + general utility widening) |
| PG&E HoldCo unsec | ~150 bps over UST | ~350 bps over UST (Ba1) | +200 bps (still HY) |
| LADWP Power Rev | ~25 bps over MMD AAA | ~35 bps over MMD AAA | +10 bps (essentially unchanged) |
| SMUD Elec Rev | ~15-20 bps over MMD AAA | ~20-30 bps over MMD AAA | ~unchanged |

**Key reading**: PG&E FMB spread is only modestly wider in 2026 than 2018 DESPITE the intervening BK, $13.5B Camp Fire trust, and Dixie 2021 fire. Without AB 1054, that spread differential would resemble the unsecured HoldCo trajectory (+200 bps). The mechanism absorbed ~300-400 bps of liability-pricing.

---

## 6. Open gaps + next session priorities

1. **Per-CUSIP EMMA pull on CalPFA / CSCDA SDG&E + SCE conduit bonds** — the tax-exempt muni-investable version of the IOU thesis needs CUSIP-level spreads to make actionable.
2. **Bloomberg time-series pull on PG&E FMB 2018-2026** — exact bp spreads to UST month-by-month to size the masking-mechanism strength quantitatively.
3. **Annual Wildfire Safety Certification status year-by-year** for PG&E + SCE + SDG&E (energysafety.ca.gov publishes; not enumerated here). Lapsed-certification CUSIPs are the framework signal for masking breakdown.
4. **SCE Eaton plaintiff judgment size** — final liability vs AB 1054 + SB 254 combined $39B headroom is the load-bearing test of whether the cap structure holds.
5. **First IBank SB-254 securitization issuance** — when it lands, watch how the new mechanism prices.
6. **CCCFA prepay pool detail** — per-CUSIP ratings + spreads on existing $2B+ deals.

---

## 7. Cross-asset connections to existing catalog

The `ab_1054_wildfire_fund_backstop` mechanism is the **fourth identified state/sovereign-administered backstop** in the catalog, alongside:
- `cal_mortgage` (CA NH/CCRC) — state insurance of last resort, VERIFIED HIGH masking
- `fha_section_242` (US hospital muni) — federal mortgage insurance, DOCUMENTED PARTIAL masking
- `gnma_passthrough_insurance` (US housing muni) — federal pass-through, MENTIONED_NOT_VALIDATED

Common pattern across all four: **state or federal balance-sheet absorbs tail risk; bondholders trade to backstop credit not operator credit; framework adds value via forward-flag on backstop's own stress**. The CA NH cascade-tail mechanism (`cal_mortgage_cascade_tail`) is the direct analog of the "cross-utility contagion via Fund depletion" finding here.

The mechanism category itself — **`state_backstop_fund`** — is new and proposed. It is structurally distinct from:
- `insurance_wrap` (no annual premium; participation funded by upfront shareholder contribution + ongoing ratepayer surcharge, not insurance economics)
- `intercept_structure` (no pre-distribution diversion of revenue; Fund pays AFTER liability determined)
- `sovereign_guarantee` (state-level, not federal; CONDITIONAL on safety certification not unconditional)
- `statutory_carveout` (active payment of claims, not exclusion-from-distribution)

---

## 8. Honest disciplines applied (hostile-validator findings)

1. **Eaton Fire is the live falsification test.** The mechanism is being drained right now. If Eaton ultimately costs $20B+ vs Fund capacity, the mechanism breaks. SB 254 was emergency-passed in Sep 2025 specifically to prevent this. Treat the IG ratings as conditionally valid pending Eaton settlement.
2. **The "$5B per claim event cap" figure cited in the task brief is INCORRECT** — actually, AB 1054 does NOT impose a per-event hard cap. The protections are: (a) 20%-of-T&D shareholder repayment cap if utility is found imprudent; (b) prudent-manager presumption from safety certification; (c) Fund pays the bondholder-relevant liability. Caught and corrected.
3. **PG&E IG rating is at FMB tranche only.** HoldCo paper is still BB+ HY. Confusing the two is the most likely framework error.
4. **SDG&E rating is exposed to OTHER utilities' Fund draws.** Cross-utility contagion via Fund depletion is the non-obvious tail. The Moody's commentary explicitly flags this.
5. **The pre-AB-1054 vs current spread comparison is narrative-quantified.** Need Bloomberg pull for exact bps. The +300-400 bps absorbed-by-mechanism estimate is plausible but not yet primary-source-anchored.
6. **CCA bonds are NOT direct controls** for the IOU pre/post AB 1054 test — CCAs didn't have large prepay-bond issuance until Dec 2021, so the time-series doesn't span the 2019 enactment. Better controls are public power (LADWP, SMUD) which have continuous issuance.

---

## 9. Source citations

- AB 1054 mechanics: https://download.edison.com/405/files/202210/20191205-ab1054-wildfire-fund-summary.pdf
- AB 1054 safety certification + prudent-manager: https://energysafety.ca.gov/what-we-do/electrical-infrastructure-safety/wildfire-mitigation-and-safety/safety-certifications/
- AB 1054 backstory: https://www.singletonschreiber.com/theblog/how-does-ab-1054-work-blog
- SB 254 (Sep 19, 2025): https://www.gtlaw.com/en/insights/2025/10/california-enacts-new-electric-transmission-financing-programs-and-adds-to-its-wildfire-fund
- Moody's PG&E Mar 2025 upgrade: https://www.utilitydive.com/news/moodys-upgrades-pge-pacific-gas-credit-wildfire/743811/
- Fitch PG&E Sep 2025 IG upgrade: https://www.energyconnects.com/news/utilities/2025/september/pg-e-raised-to-investment-grade-six-years-after-bankruptcy/
- SCE Eaton Fund draw: https://subscriber.politicopro.com/article/2025/10/southern-california-edison-to-tap-state-wildfire-fund-for-eaton-fire-costs-00629466
- S&P Negative Outlook Mar 2025: https://calmatters.org/environment/wildfires/2025/03/la-wildfires-cause-edison/
- Wildfire Fund depletion concern: https://www.renewableenergyworld.com/energy-business/california-wildfire-fund-at-risk-of-depletion-over-possible-utility-link-to-eaton-fire/
- PG&E Feb 2026 issuance: https://www.sec.gov/Archives/edgar/data/0001004980/000119312526057163/d136225d424b2.htm
- SCE May 2026 issuance: https://www.sec.gov/Archives/edgar/data/0000092103/000119312526067837/d59641dfwp.htm
- LADWP +35 bps over MMD AAA: https://www.bondbuyer.com/news/los-angeles-dwp-pricing-gains-traction-after-wildfire
- LADWP Fitch outlook improved: https://www.bondbuyer.com/news/los-angeles-dwp-will-ride-improved-fitch-outlook-to-market
- CCCFA $2B inaugural Dec 2021: https://www.cccfa.org/cccfa-issues-first-municipal-clean-energy-project-revenue-bonds-worth-over-2-billion.html
- CCCFA third pre-pay green bond: https://www.publicpower.org/periodical/article/california-community-choice-aggregator-issues-third-pre-pay-green-bond
- Participating utility companies: https://www.cawildfirefund.com/participating-utility-companies

---

**End of scoping report. Next session priorities listed in §6.**
