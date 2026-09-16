# J — Jacobs Solutions Deep Dive

_As of 2026-05-24 · Price $114.69 · Market cap ~$13.5B · 10-K filed 2025-11-20 (FY ended 2025-09-26)_

## DISCLAIMER

Algorithmic research output, not investment, fiduciary, or tax advice. Position decisions are the reader's responsibility.

## TL;DR

Framework scores J **0.200 LONG** at trough (+7% above 52w low, −30% from high). The composite is correct but **the company has fundamentally changed**: on September 27, 2024 J spun off Critical Mission Solutions (CMS) + Cyber & Intelligence (C&I) to **Amentum (AMTM)** via Reverse Morris Trust. Post-spin J is **NOT a defense services prime**:

- **Only 8% federal revenue** (down from 10% pre-spin; was the cohort's defense-services tag pre-spin)
- Three segments now: **Critical Infrastructure, Water & Environmental, Life Sciences & Advanced Manufacturing** + 65%-owned **PA Consulting** (UK-based)
- Federal-spending-review risk is minimal (8% federal)
- PA Consulting is high-margin (20% op margin)

The cohort metadata-attributed claims (J-3, J-4, J-5) reference Jacobs Technology PE numbers that **now belong to Amentum, not J**. These should be NOT_IN_FILING per the framework's auto-reclassifier. The "real" J composite after rebucketing is even cleaner than 0.200.

**Insider activity flag**: signal returns `CLUSTERED_DISCRETIONARY` but on inspection only **1 of 24 proximate sales is discretionary** (the other 23 are 10b5-1). This appears to be a false-positive signal — much weaker than CACI's 9-of-10 discretionary. **Treat as clean, not as warning** but note the signal-calibration issue.

The bear case is leveraged-recap mechanics — Jacobs funded $754M in FY25 buybacks with $887M of new debt. Classic post-spinoff capital structure remix.

**Net view: moderate-conviction LONG** (3% portfolio weight). Less attractive than BAH on capital return, less moat than HII, but a clean post-spin pure-play infrastructure consulting story at trough.

## Headline framework verdict

| | Value |
|---|---|
| Composite | **0.200** |
| Tier | **LONG** (borderline; threshold = 0.20) |
| Claims | 8 (5 PASS / 1 MODERATE / 0 SEVERE / 0 RED / 2 UNVERIFIABLE) |
| Drawdown | −30.3% from 52w high $164.44 |
| Distance above 52w low | +6.9% above $107.27 |
| Market cap | $13.5B (LARGE) |
| `insider_vs_calendar` | `CLUSTERED_DISCRETIONARY` (but 1/24 discretionary — likely false positive) |
| Federal direct-prime (USAspending FY23-25) | $10.7B / 2,874 awards |

## The Reverse Morris Trust transaction (the headline event)

**September 27, 2024**: J completed RMT spinoff:
- CMS (Critical Mission Solutions) → Amentum
- C&I (Cyber & Intelligence, formerly part of Divergent Solutions DVS) → Amentum
- AMTM trades NYSE as separate public company

Implications for J's remaining business:
- **Lost**: defense services / cyber / IC services contracting (the cohort thesis)
- **Retained**: Infrastructure consulting, Water & Environmental, Life Sciences, PA Consulting
- **Residual exposure**: J still holds AMTM shares — $227.3M FY25 mark-to-market LOSS on the position + $26M TSA charges (transition services agreement winding down)

## Financial snapshot (FY25 ended September 26, 2025)

| | FY25 | Notes |
|---|---:|---|
| Revenue from continuing ops | **$11,501M** | I&AF $10,323M + PA Consulting $1,178M |
| I&AF op profit | $798M (7.7% margin) | infrastructure consulting / engineering |
| PA Consulting op profit | $239M (20.3% margin) | high-margin UK consulting |
| Total segment op profit | **$1,038M** | |
| Restructuring/transaction charges | −$193M | mostly RMT-related |
| Net earnings (est continuing ops) | ~$700-800M | computed |
| Cash + equivalents | **$1,240M** | up $91M YoY |
| Long-term debt | **$2,236M** | up $888M YoY |
| Revolver capacity available | $1,850M of $2,250M | |
| **Share repurchases FY25** | **$754M** | |
| **Dividends per share FY25** | **$1.25 forward** | $0.29 → $0.32/qtr increase |

**Leveraged recap pattern**: $754M buyback + ~$170M dividends + working capital = ~$1B capital return funded substantially via $887M new debt + $750M term loan facility. Cash actually went up because operating cash flow + new debt issuance > capital return.

This is the post-spin capital structure remix — common after RMTs. The question is whether it's a one-time recap or ongoing leveraged-buyback strategy.

## What the framework caught

| Claim | Verdict | Notes |
|---|---|---|
| J-1 Reverse Morris Trust spinoff (2024-09-27) | PASS | Disclosed |
| J-2 Federal gov 8% of FY25 revenue (down from 10%) | PASS | Disclosed |
| **J-3 Jacobs Technology on PE 0604879C (MDA BMD Sensor Test)** | **UNVERIFIABLE** | Cohort metadata; **Jacobs Technology now Amentum** — should be NOT_IN_FILING |
| **J-4 Jacobs Technology IRES on PE 0604102C (Guam Defense MDA)** | **UNVERIFIABLE** | Same — Amentum, not J |
| **J-5 Cohort metadata: hypersonic test / NNSA / AF Test Range modernization** | **UNVERIFIABLE** | Cohort-attributed to pre-spin J |
| **J-6 FY25 $26M TSA charges + $227.3M AMTM mark-to-market loss** | **MODERATE** | One-time spin-related items |
| J-7 Continuing ops end markets | PASS | Infrastructure / Water / Life Sciences / PA Consulting |
| J-8 PA Consulting $1.27B rev / $278.5M op profit | PASS | High-margin segment |

**Critical**: Claims J-3, J-4, J-5 all reference businesses that no longer exist at J. The auto-reclassifier should put these in `NOT_IN_FILING`. Doing so doesn't change the composite (UNVERIFIABLE and NOT_IN_FILING both exclude from denominator).

The single MODERATE (J-6) is appropriately flagged — but it's one-time, not structural.

## Insider activity — likely false-positive signal

`insider_vs_calendar` returns `CLUSTERED_DISCRETIONARY` but the underlying counts:

| Metric | Value |
|---|---|
| Form 4 filings (12mo) | 61 |
| Total insider sales | 50 |
| Total sale value | $94.8M |
| Proximate to budget events | 24 |
| **Discretionary proximate** | **1** of 24 |
| 10b5-1 proximate | 23 of 24 |
| Unique discretionary owners | 9 |
| Signal | `CLUSTERED_DISCRETIONARY` |

**Compare to CACI**: 9 of 10 discretionary, 2 owners, all clustered within 7 days of FY27 J-Book. **Compare to J**: 1 of 24 discretionary, 9 owners across various events.

The framework's signal logic appears to trigger on **unique owner count** even when the discretionary share is minimal. This looks like a false positive for J. Worth noting that the **signal calibration needs review** — the same signal name on CACI (real distress pattern) and J (essentially clean 10b5-1 program) is misleading.

For J specifically: treat insider activity as **CLEAN** for thesis purposes.

## Valuation

| Metric | Value |
|---|---:|
| Market cap | $13.5B |
| Diluted shares | ~118M |
| Total debt | $2.24B |
| Cash | $1.24B |
| Enterprise value | ~$14.5B |
| FY25 revenue (continuing ops) | $11.5B |
| EV / Revenue | 1.3x |
| FY25 net earnings (continuing, est) | ~$750M |
| **P / E (LTM cont. ops)** | **~18x** |
| Estimated FY25 EBITDA | ~$1.2B (op profit $1,038M + restructuring + D&A) |
| **EV / EBITDA** | **~12x** |
| Dividend yield | **1.1%** ($1.25/yr / $114.69) |
| Backlog (est) | ~$30B+ |

For context: infrastructure consulting peers (AECOM, WSP, Fluor) trade 18-25x P/E. PA Consulting peer pure-plays (Accenture 25x, Capgemini 16x) trade similar. **J at 18x is fair** — neither cheap nor expensive for the mix.

## What would need to be true for the LONG to work

1. **Federal exposure stays at 8%** — if J starts winning DoD work again post-spin, the simplicity-of-thesis breaks (currently the appeal is "not a defense services prime").

2. **AMTM mark-to-market stabilizes** or J monetizes the position. Currently a recurring negative variable.

3. **PA Consulting margin holds 20%+** — it's the high-quality segment.

4. **Buyback financing transitions from debt to cash flow**. The $887M debt increase to fund $754M buyback is a one-time pattern; if it continues, leverage drift becomes a problem.

5. **No major contract loss in I&AF segment**. Infrastructure consulting is generally durable but recession-sensitive.

## What would invalidate the LONG

- **Federal segment grows back** — would mean J is re-entering the defense services lane and the spinoff thesis breaks
- **PA Consulting margin compression** below 15%
- **Continued debt-funded buyback** with negative organic FCF
- **AMTM stake adds another mark-to-market loss > $200M**
- **Backlog growth turns negative**

## Head-to-head vs cohort LONGs

| | J | BAH | HII | CDRE |
|---|---|---|---|---|
| Composite | 0.200 | 0.091 | 0.000 | 0.000 |
| Drawdown | −30% | −39% | −29% | −34% |
| Above 52w low | **+7%** (best trough proximity) | +10% | +44% | +11% |
| Federal revenue % | **8%** (lowest exposure) | ~85% | 81% | indirect |
| Revenue growth | n/d (post-spin) | +12% | +8% | +7.5% (organic −1%) |
| Net income growth | n/d | +54% | +10% | +22% |
| P/E | 18x | 10x | 20x | 21x |
| Dividend yield | 1.1% | **2.8%** | 1.7% | 1.3% |
| Buyback financing | leveraged | from CFO | balanced | none active |
| Federal-spending-review risk | **minimal** | high | low (statutory) | low (indirect) |

J's edge in this cohort:
- **Lowest federal exposure** = least at risk from federal-spending-review
- **Tightest trough** (+7% above 52w low — most asymmetric)

J's drawbacks:
- **Leveraged recap** financing buybacks vs BAH/HII funding from CFO
- **Lower yield** than BAH (2.8%) or HII (1.7%)
- **AMTM mark-to-market** is a recurring negative variable

## Position-sizing recommendation

**Moderate-conviction LONG** (2-3% portfolio weight). Less compelling than BAH (capital return cushion) or HII (structural moat), but a clean post-spin pure-play infrastructure consulting story with:
- Tightest trough proximity (+7% above 52w low)
- Lowest federal-spending-review exposure (8% federal)
- High-quality PA Consulting segment (20% margin)
- Reasonable 18x P/E for mix

**The cleanest pair candidate**: J / AMTM. J's continuing ops are now infrastructure consulting; AMTM is the spin-off federal services prime. If federal spending review hits services hard, AMTM underperforms while J's 8% federal exposure is bounded. Long J / short AMTM is an explicit bet on the spinoff thesis being correctly differentiated.

## Framework improvement triggered

1. **NOT_IN_FILING reclassifier for post-spin claims**: Claims J-3/J-4/J-5 reference Jacobs Technology PE work that now belongs to Amentum. The auto-reclassifier should catch "now part of [spinco]" language and flag as NOT_IN_FILING.

2. **`spin_off_tracker`** M-source: given a company, identify recent RMT/spinoff events and the post-spin segment composition. Would have flagged J as fundamentally different from the cohort's defense-services thesis.

3. **`insider_signal_calibration`**: J shows `CLUSTERED_DISCRETIONARY` with 1/24 discretionary. CACI shows the same signal with 9/10 discretionary. The current signal logic over-fires on unique owner count. Should weight by discretionary share.

4. **`leveraged_recap_detector`**: flag when share buyback financing is dominated by new debt issuance with negligible organic FCF cover. J's $887M debt increase for $754M buyback is the canonical pattern.

## Files & data

- Scores: `verticals/public_co/data/_local/J.jbook.scores.json`
- 10-K: `verticals/public_co/data/j/filings/0001628280-25-053316_10-K.txt` (filed 2025-11-20)
- USAspending: $10.65B / 2,874 awards (FY23-25, includes pre-spin Jacobs Technology)
- Insider signal: `CLUSTERED_DISCRETIONARY` but 1/24 discretionary — likely false positive
