# GATE GRADE — tier-2 FALLING cohort (DECK COIN WLDN TUYA CCJ QCOM TMUS) | 2026-08-03

Second deliverable of the batch: did the FALLING gate earn its keep, or did it nearly bury a real
setup? Verdict: **the falling gate is mislabelled and roughly half-right; the gate that actually
failed is the factor-costume gate.**

---

## FINDING 1 — the flag's stated meaning does not match its code

`COURT_QUEUE_20260804.json` says: *"FALLING = still making new lows."*

`verticals/generators/quality_drawdown.py:286,391`:
```python
last60 = h.tail(60)
basing = float(last60.iloc[-1]) > float(last60.min()) * 1.05
...
if not r["basing"]:  fl.append("falling")
```

**"falling" actually means: the last close is within 5% of the minimum of the last 60 sessions.**

Three consequences:
1. **It is blind to 52-week structure.** A name +26% off a 268-day-old low and a name +7% off an
   11-day-old low receive the identical flag. Those are opposite setups.
2. **The 5% threshold is knife-edge** for a penalty that swings the score component from 1.00 to
   0.45 (15% of the raw score). A 4%-off-the-low name is "falling"; a 6%-off name is "basing".
3. **There is no slope term.** A stock flat for 60 days at the bottom of its range is "falling"
   with zero downward momentum.

This is the same class of error the desk grades companies on — a marketed takeaway diverging from
the underlying data — occurring inside our own screen.

---

## FINDING 2 — scorecard against the *stated* definition

52-week structure from IBKR `misc_statistics` + bars, as of the 2026-08-03 close:

| name | live | % off 52w low | days since low | genuinely making new lows? | gate verdict |
|---|---:|---:|---:|---|---|
| **DECK** | 99.50 | **+26%** | **268** | **NO** — rangebound 80–125 for a year | **GATE WRONG (false-falling)** |
| **CCJ** | 89.97 | **+28%** | **345** | **NO** | right by accident — the real reject is factor-costume, which the gates MISSED |
| **QCOM** | 151.57 | +22% | 115 | NO on 52w, but re-breaking hard (−19% in a month) | approximately right |
| **COIN** | 148.36 | +5% | 168 | **YES** (fresh 20-day low 07-31) | **GATE RIGHT** |
| **WLDN** | 73.59 | +10% | 98 | **YES** (fresh low 07-29) | **GATE RIGHT** — print in 3 days |
| **TMUS** | 177.09 | +7% | 31 | **YES** | **GATE WRONG-ish — nearly buried the best name in the batch** |
| **TUYA** | 1.73 | +7% | **11** | **YES** — the most literal | right |

**Tally: 4 right · 2 wrong (DECK false-falling; TMUS nearly buried) · 1 right-for-the-wrong-reason.**

**Was courting a waste without a catalyst?** No — and this is the useful part. **Six of seven names
had a nameable, dated cause within twelve days of the screen**: five earnings prints (DECK 07-23,
TMUS 07-23, QCOM 07-29, COIN 07-30, CCJ 07-31) plus one commodity tape (CCJ) and one imminent
print (WLDN 08-06). Only TUYA had no locatable event. **The "named catalyst" requirement was cheap
to satisfy and buried nothing on its own** — a falling-flag cohort courted in the two weeks after
earnings season is a high-yield cohort, not a low-yield one.

**Where the gate cost us:** TMUS. A defensive telco at a 9.8% FCF yield that *raised* its cash
guidance was flagged FALLING **and** GUIDE-DECEL and scored **42.5 — dead last of the 79-name
queue**. Both flags are technically true and both are misleading: it is 7% off a 31-day low
*because the market punished a subscriber count while the economics improved*, and its forward
revenue decelerates *because the UScellular acquisition anniversaries out*. Two mechanically-
correct flags stacked to bury the batch's only ownable name.

---

## FINDING 3 (decisive) — the factor-costume gate ran the wrong proxy on CCJ

`quality_drawdown.py:125`:
```python
FACTOR_PROXY = {
    "Basic Materials": "GLD", "Energy": "XLE", "Real Estate": "VNQ",
    "Utilities": "XLU", "Financial Services": "XLF",
}
```
Keyed on yfinance **sector**. CCJ's sector is `"Energy"` → **XLE**. CCJ's **industry is `"Uranium"`**.

3-year daily-return regressions run this session:

| proxy | beta | raw DD | residual DD | residual share | `factor_costume` |
|---|---:|---:|---:|---:|---|
| **XLE** (what ran) | 0.34 | −40.0% | −41.1% | **1.03** | FALSE — no demote |
| **URA** (correct) | **1.01** | −40.0% | −20.3% | **0.51** | **TRUE** (threshold 0.60) |
| URNM | 0.94 | −40.0% | −20.3% | **0.51** | TRUE |

**CCJ scored 68.9 and entered the queue. With the correct proxy: 68.9 × 0.30 = 20.7 — it never
appears.** This is the AEM lesson recurring inside the gate that was built from AEM. The gate logic
is right; the lookup is too coarse.

**The gate also produced a valuable true-negative on COIN** — worth recording, because absence of
masking is itself a finding. Residual-drawdown share for COIN: **1.10 vs XLF, 1.18 vs ^NDX,
1.33 vs HOOD.** The drawdown *grows* when factors are removed. COIN is genuinely idiosyncratic, and
the anti-costume result is what disqualifies it.

---

## THREE CONCRETE FIXES

1. **Industry→proxy map, consulted BEFORE the sector map** (fixes CCJ):
   `Uranium→URA, Gold→GLD, Silver→SLV, Copper→COPX, Steel→SLX, Lithium→LIT, Coal→KOL,
   Aluminum→XME, Shipping→BDRY, Oil & Gas E&P→XOP`. One dict, one lookup-order change.
   Validation: CCJ residual share must move 1.03 → 0.51 and its score 68.9 → 20.7.

2. **Retire the binary `basing`; use the 52-week structure already computed.** The fields
   `pct_off_52w_low` and `days_since_52w_low` exist in the same return dict. Define
   `falling = (pct_off_52w_low < 10) and (days_since_52w_low < 90)`. Under that rule DECK and CCJ
   de-flag, QCOM softens, and COIN/WLDN/TUYA/TMUS keep the flag — which matches the hand grading
   above exactly. **Also fix the queue prose to state what the flag measures.**

3. **Make GUIDE-DECEL M&A-aware.** TMUS's forward-vs-trailing ratio breaks the 0.60 floor purely
   because an acquisition anniversaries out of the trailing base. Suppress or annotate the flag
   when a material acquisition closed inside the trailing-twelve-month window — the same
   suppression logic already applied to `earn_note` for FX/one-offs at lines 250-257.

---

## Batch outcome
7 courted · **0 at ≥6/10 (no red team required)** · 1 at 5/10 RP_FAIR with a band (TMUS) ·
1 at 5/10 with a below-market band (DECK) · 1 at 4/10 blocked by an imminent print (WLDN) ·
4 rejects (QCOM 3, COIN 2, TUYA 2, CCJ 1).
**One live-position doctrine update (QCOM: fv_base 159 → 145; the Aug-28 145p flagged to the
principal as now converting at fair rather than below it).**
