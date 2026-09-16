# CDRE — Cadre Holdings Deep Dive

_As of 2026-05-24 · Price $30.31 · Market cap ~$1.17B · 10-K filed 2026-03-10, FY ended 2025-12-31_

## DISCLAIMER

Algorithmic research output, not investment, fiduciary, or tax advice. The author is **not** a fiduciary or licensed advisor. Framework composite scores measure *claim verifiability* against M-sources at a point in time; they are not buy/sell recommendations. Position decisions are the reader's responsibility.

## TL;DR

The Signal OS framework scores CDRE **composite 0.000 LONG** at trough (+11% above 52w low, −34% from 52w high). The score is technically clean — 7 PASS / 3 UNVERIFIABLE / 0 negative across 10 claims — but **masks a real organic-revenue issue the framework wasn't built to catch**:

> Reported FY25 revenue growth was +$42.7M (+7.5%). **Zircaloy alone (acquired April 2025) contributed $49.2M.** Organic revenue was approximately **−$6.5M (−1.1%)**.

The bull setup is genuine — trough price, diversified federal customer base, real nuclear-safety TAM, no insider distress, dividend-paying — but the growth narrative depends on the **acquisition rollup continuing to compound** (ICOR 2023 → Alpha Safety 2024 → Zircaloy 2025 → TYR Tactical January 2026). Leverage is rising into a tighter 3.5x covenant. This is a **small-position asymmetric long**, not the framework-purity LONG it scores.

## Headline framework verdict

| | Value |
|---|---|
| Composite | **0.000** |
| Tier | **LONG** (≤ 0.20 threshold) |
| Claims | 10 (7 PASS / 0 MODERATE / 0 SEVERE / 0 RED / 3 UNVERIFIABLE) |
| Drawdown | −34.2% from 52w high $46.07 |
| Distance above 52w low | +10.7% above $27.38 |
| Market cap | $1.17B (SMALL) |

## What the framework caught (the seven PASS claims)

1. **Diversified federal customer base.** DoW, DoS, DoJ, DoI, DHS, DoC, DoE + 100+ foreign agencies. No single customer >10% of revenue. **Verified** via the 10-K customer disclosure.

2. **Globally leading EOD-technician equipment** position (Cadre/Med-Eng). USAspending corroborates: Med-Eng has 21 DoD/DoJ/DHS awards totaling $16.8M directly visible.

3. **Backlog growth $61M YoY to $189.8M** driven by Zircaloy ($51.3M), global EOD ($12.5M), chemiluminescent ($3.7M). **Disclosed and consistent.**

4. **TYR Tactical acquisition** (Jan 2026, $174M total = $150M cash + $24M stock). **Disclosed.**

5. **R&D growth** from $7.0M (FY23) → $8.4M (FY24) → $11.4M (FY25). **Disclosed.**

6. **HQ + manufacturing** at Jacksonville, FL. **Verified.**

7. **Debt $307.3M with PNC credit agreement;** leverage covenant 4.0x → 3.5x step-down after Mar-31-2026; "in compliance." **Disclosed.**

## What the framework couldn't verify (the three UNVERIFIABLE claims)

These were marked UNVERIFIABLE because Pentagon J-Book is DoD-only and doesn't see DoE/NNSA. **But they ARE in the 10-K** — the framework simply doesn't have a DoE budget M-source built for them yet. They aren't methodologically wrong claims; they're coverage gaps.

1. **Nuclear safety TAM $3-6B.** Disclosed in MD&A as management estimate based on "the need for our products by the U.S. government and the U.S. commercial nuclear market."

2. **DoE EM remediation pipeline $545B liability backlog.** Disclosed in MD&A: "The total environmental liability is estimated at $545 billion."

3. **80 plutonium pits per year by 2030 mandate.** Disclosed in MD&A: "the recent mandate of the DoE to increase production to 80 plutonium pits per year by 2030, which has not occurred regularly since 1989."

These are real disclosed market-size narratives. **To convert them PASS, we'd need a `doe_em_budget` or `nnsa_pits_tracker` M-source** (analogous to `pentagon_jbook` for DoE).

## What the framework MISSED — the bear case

### 1. Organic revenue is roughly flat-to-negative

| Line item | Δ FY24→FY25 |
|---|---:|
| Reported revenue | +$42.7M (+7.5%) |
| Zircaloy contribution | +$49.2M |
| **Implied organic** | **−$6.5M (−1.1%)** |

Explicit lines from MD&A:
- "decline in EOD products and **existing nuclear safety products**"
- "reductions of **$7.7M from existing nuclear safety products**"
- "higher demand for duty gear products" (+$1.6M)
- "chemiluminescent products" (+$3.7M)
- "global EOD" (+$12.5M)

The framework's MODERATE_UNDERDELIVERY heuristic doesn't trigger on disclosed organic-decline-masked-by-acquisition because that's a financial-quality pattern, not a Pentagon J-Book pattern.

### 2. Backlog quality

The +$61M YoY backlog growth is **largely acquired backlog from Zircaloy** ($51.3M). Stripping that, organic backlog grew only ~$10M — broadly consistent with the organic-revenue stall.

### 3. Leverage trajectory

| | FY24 | FY25 | Pro-forma post-TYR |
|---|---:|---:|---:|
| Outstanding debt | $223.2M | $307.3M | ~$482M est. |
| EBITDA | $104.8M | $111.7M | ~$130-140M est. |
| **Net leverage** | **~2.1x** | **~2.7x** | **~3.4-3.7x** |

Net leverage covenant: **4.00x through Q1 2026, then 3.50x thereafter.** That step-down is **now in effect** (Q2 2026). Pro-forma post-TYR leverage is uncomfortably close to or potentially exceeding the 3.50x covenant depending on actual TYR EBITDA contribution.

The 10-K's "in compliance" statement is for Q4 FY25 (i.e., Dec 31, 2025 — before TYR closed). The Q1 FY26 10-Q (due ~May 2026) will be the first post-TYR / post-step-down disclosure. **Material covenant-pressure risk** if TYR EBITDA underwhelms.

### 4. Acquisition-rollup dependence

| Acquisition | Date | Value | Domain |
|---|---|---:|---|
| ICOR Technology | Q4 2023 | ~$45M | EOD |
| Alpha Safety | Q4 2024 | ~$110M | Nuclear |
| Zircaloy (Carr's Engineering ex-Chirton + US) | Apr 2025 | $98.9M | Nuclear |
| TYR Tactical | Jan 2026 | $174M | Body armor / tactical |

Four acquisitions in ~24 months totaling ~$428M. Each one represents 5-15% of pre-acquisition market cap. The four are coherent with Cadre's stated verticals (EOD / nuclear / body armor) — `acq_coherence` would return COHERENT_ROLLUP not the incoherent-rollup IONQ pattern.

But the **dependence** is structural: organic revenue ~flat → growth must come from M&A → leverage rises → covenants tighten → next acquisition must be smaller or hit immediate synergies. The escalating deal sizes (45→110→99→174 $M) suggest the pace will need to slow or shift to bolt-ons.

### 5. Federal direct-prime footprint is tiny

USAspending shows Cadre's named subsidiaries have only $23M aggregate direct DoD/DoJ/DHS prime contracts over the multi-year window. The 10-K's "DoW, DoS, DoJ, DoI, DHS, DoC, DoE" customer list is real but mostly flows through **indirect channels** (state agency distributors, GSA Schedule resellers, prime contractors using Cadre product). This means:
- **Bull read:** Cadre is upstream of the prime-contractor visibility plane; framework can't easily quantify their actual federal exposure
- **Bear read:** "diversified federal customer base" is partially marketing language; direct prime visibility is thin

### 6. Insider activity (for context, not a red flag)

4 insider sales totaling $12.15M over the prior 365 days. **Zero proximate to budget events** — the IONQ-pattern insider-distress signal does NOT fire. But $12.15M = ~1% of market cap sold by insiders in 1 year is non-trivial. Compare to a no-sales year for a comparable.

`insider_vs_calendar` signal: **NO_PROXIMATE_SALES** — clean.

## Valuation context

| Metric | Value |
|---|---:|
| Price | $30.31 |
| Market cap | ~$1.17B (38.7M shares × $30.31) |
| Total debt (FY25) | $307.3M |
| Cash | ~$110M (estimate) |
| Enterprise value | ~$1.37B (pre-TYR) |
| Pro-forma EV post-TYR | ~$1.55-1.65B |
| FY25 EBITDA | $111.7M (18.3% margin) |
| Pro-forma EBITDA | ~$130-140M (estimate) |
| **EV / EBITDA (TTM)** | **12.3x** pre-TYR |
| **EV / EBITDA (PF)** | **~11.0-12.7x** post-TYR |
| Dividend | $0.40/year ($0.10/quarter, +5% increase Jan 2026) |
| Yield | 1.3% |

For a serial defense/safety rollup with mid-teens EBITDA growth (mostly acquired), 11-12x EV/EBITDA is **mid-range** — not cheap, not expensive. Comparable rollups (HEI, MOG-A, CW) trade 18-25x EBITDA but are larger and more diversified.

## What would need to be true for the LONG to work

The setup is asymmetric IF the following hold over the next 12-18 months:

1. **TYR Tactical integrates well.** $174M deal closed Jan 2026; first material EBITDA contribution shows in Q3-Q4 2026 prints. Tactical body armor commands high gross margin (often 35-45%) if execution is clean.

2. **Leverage step-down covenant is maintainable.** Pro-forma 3.4-3.7x is uncomfortably close to 3.5x. Either Q1/Q2 2026 results need to show ample headroom, OR management needs to use the "material acquisition" covenant flexibility provision (allows temporary increase).

3. **Organic revenue stabilizes by FY26.** The FY25 organic decline was specifically: existing nuclear safety −$7.7M + EOD decline (size undisclosed). A return to flat-or-positive organic in FY26 would prove the rollup isn't masking secular decline.

4. **No major insider event.** $12.15M sold over 12 months is the boundary. If this accelerates to clustered insider distribution (especially aligned with covenant pressure), the IONQ-pattern detector would fire.

5. **Trough holds.** Trading +11% above 52w low. If the stock breaks below $27.38, the technical asymmetric setup is broken; need to reassess.

## What would invalidate the LONG

- **Covenant breach** in Q2 or Q3 2026 prints (post step-down). Would force restructuring.
- **TYR Tactical integration issues** — large deal in a slightly-adjacent product (tactical body armor, not Safariland's LE body armor). Different distribution channel, different customer base.
- **State Department / federal procurement reorganization impact** (similar to what PSN-002 disclosed) hitting any of Cadre's federal channels.
- **Existing nuclear safety segment decline accelerates** (FY26 −$10M+ vs Zircaloy/TYR not offsetting).
- **Acceleration of insider sales** to clustered/concentrated pattern.

## Position-sizing recommendation

Treat as **small-position asymmetric long** (1-2% portfolio weight, not 4-5%). The framework's 0.000 score is technically clean but doesn't price the organic-decline + leverage + rollup-dependence risks. Trough proximity (+11% above 52w low) gives a bounded downside, but a covenant breach or TYR integration miss would break the structural setup.

**Better-than-CDRE setup** in the cohort: BAH at 0.091 LONG composite, −39% drawdown, $9.4B mid-cap with diversified IDIQ-portfolio operational model. BAH has the same trough optionality with a more defensible growth profile.

**Pair candidate** for CDRE: long CDRE / short DCO (Ducommun, MOD 1.000 SHORT in cohort) — both small-cap defense suppliers; CDRE has cleaner framework signal while DCO scored worst. This is a relative-value pair, not β-neutral.

## Framework improvement notes triggered by this deep dive

1. **Build `organic_revenue_decomposer`** — given disclosed revenue + named acquisition contributions, compute implied organic growth. Should have caught CDRE's −1.1% organic.

2. **Build `doe_em_budget` M-source** — parallels `pentagon_jbook` but for DoE EM remediation + NNSA budget. Would resolve CDRE C3/C4 to PASS or MODERATE with real signal.

3. **Build `covenant_pressure_tracker`** — given pro-forma debt + EBITDA + step-down schedule, flag covenant-headroom < 15%. Would have flagged CDRE post-TYR.

4. **Build `rollup_velocity_meter`** — track acquisition pace + deal-size escalation. CDRE's 4 deals in 24mo escalating from $45→$174M is the pattern to detect.

## Files & data

- Scores: `verticals/public_co/data/_local/CDRE.jbook.scores.json`
- Input: `verticals/public_co/data/_local/CDRE.jbook.input.json`
- 10-K: `verticals/public_co/data/cdre/filings/0001104659-26-025862_10-K.txt` (filed 2026-03-10)
- M-source results: usaspending (above), insider_vs_calendar (NO_PROXIMATE_SALES)
