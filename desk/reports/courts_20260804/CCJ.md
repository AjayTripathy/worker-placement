# CCJ — Cameco | court_queue_20260804 tier-2 FALLING | 2026-08-03

**VERDICT: FRAME-REJECT 1/10 — beta in costume, per the AEM template.**
**This name is also the batch's decisive GATE DEFECT: the factor-costume gate ran against the
wrong proxy and let CCJ into the queue. It should never have been courted.**

## Tape basis
IBKR live 2026-08-03 **$89.97** (+0.28%). Friday 07-31 close 86.38. 52w range 68.98–135.18
(IBKR intraday). 3y high 134.09 close-basis 2026-01-28 = **−36%**. 52w low 70.47 set 2025-08-20 →
**+28% off a 345-day-old low** — CCJ is *not* making new lows on any 52-week definition.
Next print 2026-10-30.

## Cause-check — there is no company event
Q2-2026 reported 2026-07-31 (Business Wire): *"Year-to-Date Performance on Track; Production
Outlook Unchanged."* EPS missed by $0.13; **revenue outlook was RAISED**; and per Investing.com's
transcript coverage, **shares ROSE on the print**. A drawdown with no adverse company event and a
rising post-print tape is a price fact, not a business fact.

## The decomposition (AEM template, run before any quality claim)
| window | CCJ | URA | URNM |
|---|---|---|---|
| 3-month | **−29.8%** | −30.8% | −29.1% |
| 6-month | **−35.4%** | −34.1% | −40.1% |
| 12-month | **+11.1%** | −1.1% | +4.7% |

Regression of daily returns, 3-year window:

| proxy | beta | raw DD | residual DD | **residual share** | gate |
|---|---|---|---|---|---|
| **XLE** (what the screen used) | 0.34 | −40.0% | −41.1% | **1.03** | passes — no demote |
| **URA** (correct) | **1.01** | −40.0% | **−20.3%** | **0.51** | **FAILS the 0.60 threshold** |
| URNM | 0.94 | −40.0% | −20.3% | **0.51** | FAILS |

**Beta to uranium is 1.01 and roughly half the drawdown disappears when the uranium factor is
removed. The −36% is the U3O8 tape.** Frame-reject: there is no company-specific de-rate to court.

## GATE DEFECT — the systems finding (highest-value output of this name)
`verticals/generators/quality_drawdown.py` line ~125:

```
FACTOR_PROXY = {
    "Basic Materials": "GLD", "Energy": "XLE", "Real Estate": "VNQ",
    "Utilities": "XLU", "Financial Services": "XLF",
}
```

The map is keyed on the yfinance **sector**. CCJ's sector is `"Energy"` → **XLE (oil & gas)**.
CCJ's **industry is literally `"Uranium"`**. Uranium has essentially no relationship to XLE, so
the regression returned a residual share of 1.03, `factor_costume` evaluated FALSE, the ×0.30
demote never fired, and CCJ entered the queue at score **68.9**.

**With the correct proxy: residual share 0.51 → `factor_costume` TRUE → 68.9 × 0.30 = 20.7.**
CCJ would not have appeared on the list at all.

This is the AEM lesson recurring inside the gate that was *built from* AEM. The gate is correct;
its lookup is too coarse. **Fix: an industry→proxy map consulted BEFORE the sector map**, e.g.
`Uranium→URA, Gold→GLD, Silver→SLV, Copper→COPX, Steel→SLX, Lithium→LIT, Coal→KOL, Shipping→BDRY,
Aluminum→XME`. One dictionary and one lookup-order change.

## It also fails the frame on its own terms
The tier-1/2 frame is quality-at-own-history-discount. CCJ: trailing P/E **84.6x**, forward P/E
**47.2x**, free cash flow **$50M against a $39.1B market cap** (0.13% FCF yield), gross margin 35%,
revenue growth **−7.2%**, earnings growth −92%. There is no history-discount here — it is a
commodity producer at a peak-cycle multiple whose commodity is falling. Even if one wanted uranium
exposure, the vehicle question (CCJ vs URA vs the physical trust) is a different court entirely.

## Scenarios (nominal — no position, no band)
bear 60 (U3O8 continues lower, Westinghouse equity income compresses) p 0.35 · base 88 (spot
stabilises) p 0.45 · bull 130 (contracting cycle re-tightens) p 0.20 → **e_fv $86.6** vs $89.97 =
**−3.7%**. The distribution is the uranium price distribution wearing a ticker.

## Kill / re-court trigger
Re-court **only** if the residual drawdown against URA exceeds 0.60 — i.e. only if CCJ decouples
from its own commodity. Absent that, this is a commodity view, and commodity views are taken in the
commodity, not in a 47x-forward equity.

## Freezable call
**CCJ | 2026-10-30 | CCJ's 3-month return through the Q3 print stays within ±8pp of URA's
3-month return (i.e. it remains factor-dominated) | our_p 0.80.**

## UNVERIFIABLE / gaps
- **No XBRL.** Cameco is a Canadian filer (40-F/6-K) and `data.sec.gov/api/xbrl/companyfacts` for
  CIK 1009001 returned no us-gaap facts. All fundamentals here are yfinance-sourced, not audited-
  primary. For a REJECT that is tolerable; it would not be for a BUY.
- The Q2-2026 MD&A, the Westinghouse equity-accounting contribution, and the 2026 contracting book
  were not read. Unnecessary given the frame-reject, but the gap is real and named.
