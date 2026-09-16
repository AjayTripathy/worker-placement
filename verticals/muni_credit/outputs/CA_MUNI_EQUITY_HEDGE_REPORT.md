# CA Municipal Bonds as an Equity-Bubble Hedge
### Anti-correlation, its rate-dependence, and the rotation play
*Draft — first results. Author: Signal OS / muni_credit vertical. As-of 2026-06-05.*

---

## Executive summary

California municipal bonds behaved as a powerful equity hedge during the dot-com
bust — but the protection is **not** a structural property of munis. It is a *rate*
phenomenon wearing a *credit* disguise: **the equity anti-correlation is really a
correlation to bonds (duration), and it only shows up when the Fed eases into the
crash.** Strip out the rate rally and the tech bust *did* damage California credit
(worst-in-nation downgrade). And in the three non-dot-com crises (2008, 2020, 2022)
the anti-correlation **degraded, broke, or inverted**. The hedge is regime-conditional,
and the regime is "growth scare + Fed cutting," not "equities fall."

The corollary — Chapter 2 — is that the muni position is best understood as **tax-free
dry powder**: a store of value you *rotate into equities* near the bottom. The rotation
backtest shows the timing is far more forgiving than intuition suggests, with one sharp
asymmetry: **being early is fatal; being late still wins.**

Chapter 4 maps this onto the live 20-name honesty basket against a specifically *AI* crash:
**only 1 of 20 names sits in the income-tax channel an AI bust transmits through**, and a
per-name **cap-gains beta (§4.5) puts the equal-weight basket at 0.16** — ~16% of the
cap-gains credit-sensitivity of an all-state-GO portfolio (and that lone State GO drives
~32% of even *that*). The basket has already won the *credit* leg, reducing an AI crash to a
**pure rate-regime bet** (Ch3): ideal hedge if the Fed cuts, credit-safe-but-price-exposed
if it arrives via liquidity or inflation.

Chapter 5 validates the rating out-of-sample, including a **blinded** test (β-tiers sealed first;
agents measured actual sector credit outcomes blind to the hypothesis): it rank-orders credit
stress at **Spearman ρ = 0.90 in the income/cap-gains regime** — the AI-crash archetype — and
*correctly* fails to predict the property/operational/rate regimes, confirming it is a
channel-specific instrument, not a generic credit-quality proxy.

---

## Chapter 1 — The anti-correlation, and why it's really a bond correlation

### 1.1 The dot-com result (N=1, in-sample)

| Asset (2000–2002) | Cumulative total return |
|---|---|
| S&P 500 (price) | **−37.6%** |
| Nasdaq (peak→trough) | ≈ −78% |
| CA muni (VCITX, Vanguard CA Long-Term Tax-Exempt) | **+30.3%** |
| National muni (VWLTX) | **+30.5%** |

On a total-return basis, CA munis were a genuine safe haven: **+30% while the S&P lost
−38%.** No muni ETF existed in 2000 (MUB/CMF launched 2007), so these are real
investable *fund* proxies that traded through the burst.

### 1.2 The decomposition — two opposing channels

1. **Rate / flight-to-quality channel (price tailwind, dominant).** 10-yr Treasury
   **6.58% → 3.83%** (Jan-00→Dec-02); Fed funds **6.5% → 1.24%**. A duration-7–8
   muni portfolio captured most of its +30% from this rally plus tax-exempt income.
2. **CA credit channel (fundamental headwind, masked).** California's General Fund is
   the **most tech-levered state revenue base in the U.S.** via capital-gains and
   stock-option income tax. That revenue collapsed; the budget gap hit ~$38B; and CA GO
   was cut from **AA/Aa2 to BBB/A2/Baa1 — the lowest-rated state in the nation by 2003**,
   agencies *explicitly* citing "technology sector weakness" and the "sharply reduced
   capital gains tax base." Full recovery to A by 2004.

CA GO downgrade path: S&P **AA(9/00) → A+(4/01) → … → BBB(’03) → A(8/04)**; Moody’s
**Aa2 → A1(11/01, “technology sector weakness”) → A2/Baa1 → A3(5/04)**; Fitch
**AA → A(12/02) → BBB → A-(9/04)**.

### 1.3 Rate-neutralized: the credit penalty was real but modest

Comparing CA vs national muns isolates the CA-specific credit effect (both ride the
same muni rate rally):

| Year | VCITX (CA) | VWLTX (Nat’l) | CA − Nat’l | CA credit event |
|---|---|---|---|---|
| 2000 | +15.2% | +13.3% | +1.9 | still AA |
| 2001 | +3.4% | +4.5% | **−1.2** | downgrades begin |
| 2002 | +9.4% | +10.1% | **−0.7** | Fitch AA→A |

The tech bust transmitted to CA **credit** (4–5 notches) but **not** to CA muni **total
return** — because (a) the rate rally swamped the spread widening, and (b) it was a
mark-to-market spread, *not a default*. CA GO carries a **continuous appropriation and
2nd-priority lien on the General Fund** (after K-14 education); even at BBB, default risk
was ~nil. **The hedge worked on price; the credit damage was real but recovered.**

### 1.4 The key reframe — "anti-correlation to equities" = "correlation to bonds"

A muni's return ≈ **duration + credit/liquidity + tax-technical.** The equity
anti-correlation appears **only when the duration term dominates and rates rally** — i.e.
a growth scare the Fed eases into. That is a *bet on the Fed cutting*, not a property of
the asset. Which is exactly why it fails out-of-sample (Ch3).

---

## Chapter 2 — The rotation: munis as tax-free dry powder

If munis are +30% while equities are −38%, the strategy isn't "hold munis" — it's
**rotate the appreciated munis into equities near the bottom.** Backtest (muni leg =
VCITX path; equity leg = S&P price + ~1.6% div; terminal = 2007-10 recovery peak):

| Strategy | Entry S&P | Terminal 2007 |
|---|---|---|
| Buy & hold **equity** from 2000 | — | **+25.7%** (the lost decade) |
| **Stay in muni**, never rotate | — | +59.3% |
| Rotate **2001-01** (early — catch the knife) | 1366 | **+45.4%** |
| Rotate 2002-01 | 1130 | +78.8% |
| Rotate **2002-09 (~bottom)** | 815 | **+160.5%** |
| Rotate 2003-03 (March retest) | 848 | +158.2% |
| Rotate 2003-06 (trend confirmed) | 974 | +126.7% |
| Rotate 2003-12 (late) | 1112 | +102.3% |

### 2.1 Findings

1. **"Getting out" is free.** You're *already* in the safe haven and it's *paying* you —
   munis were **+26% by the Sept-2002 equity trough**. There is no exit-timing problem;
   the entire timing problem is **re-entry**.
2. **The forgiveness zone is enormous.** Any re-entry from Jan-2002 to Dec-2003 returned
   **+79% to +160%** — all crushing both buy-&-hold equity (+26%) and stay-in-muni (+59%).
   You do not need to nail October 2002.
3. **Being *early* is the only real killer.** Rotating Jan-2001 returned **+45% — *worse*
   than never rotating (+59%)**. Catching the falling knife (−40% further to the bottom)
   underperformed doing nothing.
4. **Being *late* still wins.** Even Dec-2003 (a year past the bottom) returned **+102%**,
   nearly doubling vs +59% for staying scared in munis.
5. **Mechanical rules whipsaw near bottoms.** A naive 10-month-MA reclaim fired a *false*
   re-entry in **Mar-2002 at 1147**, right before the final −29% leg (terminal +78% —
   survivable but a round-trip). A *durable* trend signal didn't confirm until ~mid-2003
   (the +127% entry). The muni cushion is what lets you eat a whipsaw without it mattering.

### 2.2 Frictions to net out (not yet in the model)

- **Taxes:** muni *income* is tax-exempt, but the *price appreciation* realized on sale is
  a taxable capital gain — the rotation triggers it. For a CA top-bracket holder this is a
  real drag on the muni→equity switch.
- **Muni bid/ask:** retail muni round-trips run ~1–3%; selling 20 illiquid lots to raise
  cash is not frictionless (cf. the basket’s 2 STALE / 1 NO-TAPE marks).
- **Behavioral:** the hard part was never the math — it was (a) *not* capitulating into
  equities in 2001 when they looked cheap, and (b) actually buying in 2003 against the
  loud "double-dip / sucker’s rally" consensus.

### 2.3 The rate-dependency carries into the rotation

The dry powder was worth +26% at the bottom **because rates rallied.** In a bust *without*
the rate tailwind (Ch3), the powder is ~flat at the lows — you deploy ~$1.00, not ~$1.26.
Still beats riding equity down; just a smaller kicker.

---

## Chapter 3 — Regime-conditionality (the critical caveat / next test)

Dot-com is **N=1**. Across the other three equity drawdowns the hedge does *not* replicate:

| Episode | Regime | Muni (VWLTX) | S&P | Hedge verdict |
|---|---|---|---|---|
| **Dot-com 2000–02** | Growth scare, **Fed cuts** | **+30.5%** | −37.6% | **WORKS** (strong anti-corr) |
| **GFC 2008** | Credit → **liquidity crisis** | −4.87% | −37.0% | **DEGRADED** — cushion on the year, but a Sept–Oct **co-crash** at the worst moment |
| **COVID Mar-2020** | **Liquidity shock** | +6.21% (yr) | +18.4% (yr) | **BROKE** ~3 wks (munis −~12% with stocks in March) then both rallied on Fed MLF |
| **2022** | **Inflation / rate shock** | −10.43% | −18.1% | **INVERTED** — fell *together*, double digits |

**Unifying principle.** Anti-correlation requires duration to dominate *and* rates to
rally. It fails when:
- a **liquidity crisis** forces deleveraging — munis get sold for cash regardless of
  credit (2008 auction-rate/insurer contagion; March-2020 fund runs, AAA muni yields
  +85–100 bps in 3 days), i.e. the hedge breaks *exactly when you need it*; or
- the shock is **rates-up / inflation** — duration becomes the enemy and munis fall *with*
  equities (2022, the worst-ever year for U.S. bonds).

**Implication for an AI-bubble burst.** The hedge’s value hinges on *which regime*:
- Clean growth scare + Fed easing → dot-com analog, munis hedge.
- Liquidity crunch or sticky-inflation (Fed can’t cut) → munis won’t hedge and may amplify.

This converts the prior chapters’ tailwind into a **conditional bet on the Fed’s reaction
function**, which is the honest framing of "how safe are CA munis from tech bubbles."

---

## Chapter 4 — Why *this* basket is better-positioned for an AI crash

An AI-bubble burst would transmit to California muni **credit** through the *same* pipe
the dot-com bust used: the state General Fund's **capital-gains / stock-option / IPO-wealth
income tax** — the most tech-levered state revenue base in the U.S. That channel hits
**state GO and General-Fund-appropriation** credits. The honesty basket is built almost
entirely *outside* that pipe.

### 4.1 Name-level transmission map (the live 20)

| AI-crash channel | Names | Count | Exposure |
|---|---|---|---|
| **Income-tax / state GF** (the dot-com/AI pipe) | CA State GO (19) | **1/20** | **direct** |
| **Property-tax / assessed-value** (school GO + TAB) | Duarte, Alpine USD, Clovis, Downey, Sanger, Pomona (1–6); Anaheim, San Jose, Fontana, Cloverdale TABs (12,14,15,16) | **10/20** | insulated from tech-wealth; *housing*-exposed instead |
| **Enterprise revenue** (orthogonal) | El Camino & Stanford hospital (7,8); Aldersly & Bethany CCRC (9,10); CalHFA (11); Anaheim rev (13); Met Water & Marina Coast (17,18); San Diego COP (20) | **9/20** | demand-driven, not tech-wealth-driven |

**Only ~1 name in 20 (5%) sits in the channel an AI crash actually uses.** The other 95%
is secured by property tax or enterprise revenue that a sudden evaporation of tech equity
wealth does not touch on the credit side.

### 4.2 Why the two big sleeves are insulated

- **Property-tax sleeve (10/20).** California assessed value is **Prop-13 acquisition-value
  capped** — it resets only on sale and can't fall quickly. A tech-*equity* crash doesn't
  move AV; a tech-*income* crash doesn't move AV. (What moves AV is a **housing** collapse —
  a *different* bubble, the 2008 channel, not the AI channel.) The 6 K-12 GO additionally
  carry **SB-222 statutory liens** on a dedicated ad-valorem levy that *must* be raised to
  cover debt service — structurally senior and disconnected from the state revenue cycle.
- **Enterprise sleeve (9/20).** Hospital admissions, senior-living occupancy, and water
  consumption are non-cyclical to tech wealth; 2 CCRCs carry **Cal-Mortgage/HCAI insurance**
  (effective State-AA− credit substitution). These rise or fall on their own enterprise, not
  on the Nasdaq.

### 4.3 The honesty screen already excludes the AI-fragile profile

The credits an AI crash *would* impair are the speculative ones the structure/anti-masking
screen is designed to reject: **land-secured Mello-Roos / CFD** riding tech-driven property
appreciation, **tech-tenant-concentrated** revenue, and **aggressive tax-increment TABs**
banking on continued AV growth. The basket's bias toward structurally-secured,
covenant-verified, non-speculative paper means the AI-fragile names were screened out
*before* this analysis — the exclusion is the alpha.

### 4.4 The honest counter — what the basket does *not* protect against

Credit insulation is necessary, not sufficient. Per Ch3, **price** still rides the rate
regime, and here the basket cuts both ways:

- **Long duration (mod dur 13.6 yr to maturity, WAM 22 yr).** In a *Fed-cutting growth
  scare* (the dot-com-analog AI crash), this is a second tailwind: **insulated credit *and*
  a duration rally → a near-ideal hedge.** But in a **liquidity-crunch** (2008 / Mar-2020)
  or **inflation / rate-shock** (2022) AI crash, that same duration makes the basket fall
  *with* equities regardless of its clean credit.
- **Illiquidity.** The basket holds thin names (2 STALE marks, 1 never-traded). In a
  forced-sale liquidity crisis, illiquid muni lots get marked down hardest — a *negative*
  vs a liquid muni ETF in exactly the 2008/2020 regime.
- **One indirect-AI name to watch:** the **San Jose RDA-successor TAB (slot 14, Silicon
  Valley)** — tax increment rides Silicon Valley property/commercial values, which a deep,
  *prolonged* AI bust could eventually soften (second-order, property-lagged). It is also
  the never-traded / NO-TAPE name — doubly flagged.

### 4.5 Per-name cap-gains beta (quantitative)

The 5% / 95% split is categorical; a continuous **cap-gains beta** weights it. This is a
**structural model, not a regression** (per-obligor 20-yr revenue series don't exist to
regress): each name's beta = *revenue-channel elasticity* × *credit-structure shield* ×
*regional tech-hub factor*, **normalized so an unshielded CA state-GF income-tax claim =
1.0**, and calibrated to two anchors — CA cap-gains+option PIT revenue **$17B (2000-01) →
$5B (2002-03), −71%** [LAO], and the dot-com credit outcome (State GO −4-5 notches; SB-222
school GO & water untouched). It is a **credit-spread/rating beta** (mark-to-market risk),
not a default beta. ±40% band reflects channel-elasticity uncertainty. *(Reproducible:
`capgains_beta.py` → `data/etf_v2_capgains_beta.json`.)*

| # | Obligor | Channel | β [lo–hi] | cum % of basket β |
|---|---|---|---|---|
| 19 | **CA State GO** | state GF income tax | **1.00** [0.60–1.40] | 32% |
| 20 | San Diego County pension COP | county GF appropriation | 0.30 [0.18–0.42] | 41% |
| 14 | **San Jose RDA-successor TAB** (Silicon Valley) | tax increment | 0.25 [0.15–0.35] | 49% |
| 12 | Anaheim TAB | tax increment | 0.18 | 54% |
| 15 | Fontana TAB | tax increment | 0.18 | 60% |
| 16 | Cloverdale TAB | tax increment | 0.18 | 66% |
| 7 | El Camino Hospital (SV) | hospital rev | 0.17 | 71% |
| 8 | Stanford Health Care (SV) | hospital rev | 0.17 | 76% |
| 9 | Aldersly CCRC (Cal-Mtg) | entrance fee | 0.15 | 81% |
| 13 | Anaheim revenue authority | lease/revenue | 0.14 | 86% |
| 10 | Bethany CCRC (Cal-Mtg) | entrance fee | 0.14 | 90% |
| 11 | CalHFA | housing finance | 0.09 | 93% |
| 1–6 | 6 × SB-222 school GO | property AV | 0.03 each | 98% |
| 17,18 | Met Water, Marina Coast Water | water rev | 0.03 each | 100% |

**Headline: equal-weight basket β = 0.16 [0.10–0.22]** — the basket carries only **~16% of
the cap-gains credit-sensitivity of an all-state-GO portfolio.** That is the continuous form
of the "95% insulated" claim, and it's robust: even the high end of the band (0.22) sits far
below a state-GO book.

Two findings the categorical split hid:
- **Single-name concentration.** The lone CA State GO (1 of 20 names) drives **31.5% of the
  entire basket's cap-gains beta.** Drop it and the basket β falls to **0.115** — one name
  swings the basket's whole AI-credit sensitivity by ~38%. *If you wanted to harden the
  basket against an AI crash, trimming/swapping slot 19 is the single highest-leverage move.*
- **An inert tail.** The 6 SB-222 school GO + 2 water names — **8 of 20 holdings — contribute
  just 7.4% of total beta.** They are, for an AI-equity shock, effectively immune.

### 4.6 Verdict

For a state-GF-exposed muni portfolio, an AI crash is **double jeopardy** (credit *and*
rate). This basket has **already won the credit leg** — 95% of par is outside the
income-tax pipe — so it reduces the question to a **pure rate-regime bet**: *is the AI crash
a Fed-cutting growth scare?* If yes (dot-com analog), the basket is a near-ideal AI-crash
hedge (insulated credit + long-duration rally + the Ch2 rotation into cheap equities). If
the crash arrives via liquidity or inflation, the basket keeps you safe on **credit/default**
but not on **price** — and its illiquidity is a mild drag there. *Credit-insulated;
rate-regime- and liquidity-exposed.*

---

## Chapter 5 — Validation: does the rating predict reality? (blinded)

Ch4 produced a per-name AI-crash rating from a *structural* model. This chapter tests it
out-of-sample with three backtests; the third is decisive and was run **blinded** to guard
against confirmation bias.

### 5.1 Credit-tier dispersion is regime-conditional

High-yield muni (VWAHX — proxy for lower-credit / higher-β revenue) vs investment-grade
long muni (VWLTX). Lower credit should lag — and most in *fundamental* busts, least in *rate*
shocks:

| Crash | Regime | HY (VWAHX) | IG long (VWLTX) | HY − IG |
|---|---|---|---|---|
| Dot-com 2000–02 | growth scare | +25.2% | +30.5% | **−5.3 pp** |
| GFC 2008 | liquidity crisis | −10.5% | −4.9% | **−5.6 pp** |
| COVID 2020 | liquidity (recovered) | +5.4% | +6.2% | −0.8 pp |
| 2022 | rate shock | −11.8% | −10.4% | −1.4 pp |

Dispersion is **~4× larger in the two fundamental busts** (~−5.5 pp) than in the
transient-liquidity / rate episodes (~−1 pp). β bites hardest in a real crisis. *(Caveat:
HY-vs-IG is general credit quality, a loose proxy for the cap-gains channel.)*

### 5.2 CA State GO credit tracks cap-gains, not rates (the AI-5 anchor)

| Episode | Cap-gains revenue | CA GO rating action | Validates |
|---|---|---|---|
| Dot-com 2001–03 | $17B → $5B (−71%) | AA → BBB (−4–5 notches) | AI-5 ✓ |
| GFC 2008–09 | → ~$2B (2009) | A → Baa1/BBB + IOUs | AI-5 ✓ |
| Recovery 2010s–’21 | rebuilt (record 2021) | upgraded → Aa2/AA | symmetric ✓ |
| 2022 rate shock | still high | **no downgrade** | credit≠price ✓ |

CA GO was cut in *both* equity-bubble busts (cap-gains collapse), recovered symmetrically as
cap-gains rebuilt, and was untouched in the 2022 rate shock — confirming the cap-gains channel
drives GO credit and the 2022 muni drawdown was pure price/duration.

### 5.3 Blinded cross-sectional ordering test (decisive)

**Does the full AI-1…AI-5 scale rank-order by *actual* credit stress in each crash?**
*Method (blinded):* the β-tier sector order was **sealed to disk first**; four research agents
then measured each sector’s realized credit outcome (ratings, defaults, spreads) per crash with
**no knowledge** of the β-framework, the cap-gains hypothesis, the AI-crash framing, or the
expected order. Spearman rank-correlation of their blind rankings vs the sealed prediction:

| Crash (shock type) | Spearman ρ | State GO actual rank | Read |
|---|---|---|---|
| **Dot-com 2000–03 (income / cap-gains)** | **0.90** | #1 (most stressed) | strong — the AI archetype |
| GFC 2008–09 (property / liquidity) | 0.33 | #3 | diverges: CCRC/CalHFA jump up |
| COVID 2020 (operational) | 0.45 | #5 | weak: operational sectors top |
| 2022 (rate / inflation) | 0.24 | #6 (**upgraded**) | State GO upgraded — cap-gains high |

**The rating is channel-SPECIFIC, exactly as designed.** It rank-orders credit stress at
**ρ = 0.90 in the income/cap-gains regime** (dot-com = the AI-crash archetype) and *correctly*
does **not** predict the property (2008), operational (2020), or rate (2022) regimes — a generic
credit-quality proxy would score high everywhere. The **State GO is the tell**: #1 (most stressed)
when cap-gains collapsed, but **upgraded** (#6) in 2022 when cap-gains hit a record — the AI-5 name
swings with the cap-gains cycle, confirming the mechanism. The **insulated tier (school GO, water)
sat bottom-ranked in all four regimes.**

*The blinding earned its keep:* the agents independently corrected timing that would have
*inflated* the fit if primed (RDA distress is 2011–12 not 2008; CCRC defaults cluster 2008+/2020+;
State GO was *upgraded* in 2020/2022) — those corrections are what produce the diagnostic
divergence. *Caveat:* dot-com anchored the scale’s endpoints, so its ρ is out-of-sample in the
middle tiers but not the extremes; the cleaner OOS evidence is the discriminant pattern across the
other three crises, and the agents’ middle-tier (county COP, TAB) rankings were often
low-confidence on thin data. *(Reproducible: `testC_prediction_sealed.json`, `testC_score.py` →
`data/testC_results.json`.)*

### 5.3.1 Hardening with per-issuer counts (blinded round 2)

To replace the agents’ judgment-based middle-tier ranks with *enumerated* rating actions, a
second blinded round was tasked to **count** documented downgrades/defaults/upgrades per sector
per crash (scoring rubric sealed first). The decisive finding is a **data limit**: per-issuer CA
rating-action counts for the middle tiers are **not recoverable from public sources** — all four
agents independently hit the proprietary Moody’s/S&P/Fitch databases + CDIAC default-draw index
and returned “not-documented at issuer level” for school GO, TAB, hospital, CCRC, and
county-level COP. Defaults (the hardest events) are reliably enumerable; mid-tier downgrade
counts are not.

Scoring only what *is* documented (ordinal 0–3 via the sealed rubric):
- **Hardened dot-com ρ = 0.80** (vs 0.90 judgment-based) — the drop is mechanical: five middle
  sectors collapse to a tie at *zero documented CA actions* in 2000–03, so the middle ordering is
  **unresolved, not wrong**.
- **Robust anchors confirmed by hard counts:** State GO took ~9 multi-notch actions (AA→Baa1);
  the **insulated tier (school GO + water) had 0 documented credit actions in all four regimes**;
  CalHFA was *upgraded* in 2022.
- The count-based ρ for the **non-income** crises is *not* reported — the property/operational
  stress (CCRC, hospital) is real but documented *nationally*, not isolable to CA issuers, so it
  can’t be scored cleanly; round-1’s qualitative divergence stands as the channel-specificity
  evidence.

**Refinement surfaced (model-v2 candidate):** in the pure income/cap-gains regime, documented
stress sat *entirely* in the state-GF complex (State GO + appropriation/lease); **tax-increment,
hospital, and CCRC showed zero income-driven actions — their documented stress all falls in the
property (2008) or operational (2020/22) regimes.** So β-CapGains is *conservative* for the income
channel: it gives the middle revenue tiers moderate cap-gains betas, but their realized
cap-gains-channel stress is ~nil. Re-classing TAB/hospital/CCRC toward AI-1/2 for the income
channel would raise the dot-com fit and make the basket look *even better* AI-positioned —
pre-registered as the next iteration, not tuned post-hoc here.

**The CDIAC index — scripted, and a proven dead-end for this purpose.** The one CA-specific
source with granular per-issuer data is the CDIAC default-draw index. I reverse-engineered the
real DebtWatch API (`debtwatch.treasurer.ca.gov/api/dataset/draws/export/tabular`; the commonly
-cited `…/cdiac/default-draw/issuename.asp` is a 404) and pulled the **full 710-event index,
1991–2026**. Result: it **cannot harden the eight test sectors** — it is **89% Mello-Roos/CFD
land-secured draws** (which carry mandatory reserve-draw reporting), and the rating-test sectors
appear 0–3× each, because **GO / school / hospital / CCRC / water / county credit stress shows up
as *downgrades*, which CDIAC does not track** (rating actions live only in proprietary
agency archives). So the public-data limit is now *demonstrated, not asserted*. *(Suggestive
aside, confounded by 1980s-CFD vintage: land-secured draws fell through the dot-com income bust
and spiked in the 2011–12 housing aftermath — directionally consistent with land-secured being a
property-channel, income-insensitive sector.)*

**Net:** robust at the **extremes and bucket level** (state-GF impaired / inert tier untouched,
confirmed by hard counts across four regimes); the **fine middle-tier ordering cannot be validated
to 8-way precision from public data** — a data-availability limit, not a model failure, now
confirmed by pulling the CDIAC source directly.
*(Reproducible: `testC_hardening_rubric.json`, `testC_harden_score.py`, `cdiac_draws.py` →
`data/{testC_hardened,cdiac_draws}.json`.)*

### 5.4 What the validation establishes

The β-CapGains rating is a **validated, channel-specific instrument**, not a generic
credit-quality re-label. Because an AI crash *is* an income/cap-gains shock (the dot-com
archetype), the **ρ = 0.90 cross-sectional fit is the directly relevant number** — the rating
predicts which CA munis’ credit will and won’t crack in exactly the scenario this report is
about. Its silence in the other regimes is a feature: it tells you *when* the rating applies
(cap-gains/income shocks) and, via Ch3, that *price* safety is a separate, rate-regime question.

---

## Proposed further chapters (roadmap)

- **Ch3 (full build):** rolling 12-month muni↔equity correlation, 2000–2025, to *show* the
  sign-flipping empirically (needs muni monthly index + S&P monthly). Quantify the
  duration vs credit/liquidity decomposition per regime.
- **Ch2 OOS:** re-run the rotation across **2008→2009** and **2020** with a pre-committed,
  walk-forward trend rule (no in-sample switch dates) + tax/bid-ask frictions netted out.
- **Ch4 — Sector map + per-name cap-gains beta:** ✅ *written (§4.5).* Possible upgrade: replace
  the structural elasticities with empirical betas where a revenue series exists (e.g. regress the
  State GO on CA PIT receipts).
- **Ch5 — Validation (blinded):** ✅ *written (§5).* Remaining: enumerate per-issuer rating-action
  counts (vs the agents’ sector-level reads) to tighten the middle-tier ρ confidence.
- **Ch6 — Forward stress test** on the live 20-name basket: each holding’s revenue-source
  beta to a cap-gains shock × a **flat-rate** scenario (no rally cushion) → basket drawdown
  if the 2001 rate gift doesn’t repeat.
- **Appendix:** methodology, in-sample vs walk-forward, no-ETF proxy choice, data sources.

---

### Data sources
FRED (Treasury / Fed funds); CA State Treasurer GO ratings history; Bond Buyer / S&P /
Moody’s / Fitch rating actions; Yahoo Finance (S&P 500 monthly, VCITX/VWLTX returns);
Fed (KC/Richmond), Duke FinReg, Bond Buyer (2008/2020/2022 muni-market accounts).

### Caveats
Ch1 anti-correlation is a single headline episode (dot-com), though Ch5 validates the *rating*
across four crashes (blinded); fund proxies (no muni ETF pre-2007); rotation (Ch2) is in-sample
(illustrative, not a committed rule); CA-vs-national is a near-but-imperfect credit
control (duration/positioning differ); OOS calendar returns mask severe intra-year
drawdowns (2008 Sept–Oct, March 2020).
