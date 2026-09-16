> Court lane: tier-2 small/misc EXHAUSTED tail (scores 17-39), COURT_QUEUE_20260804.
> Date 2026-08-03. Price basis: **IBKR daily close 2026-08-03, TRADES/RTH, ib_insync bars**.

# ARIS — Aris Mining | 1/10 FRAME-REJECT (90% of the drawdown is GDX)
**live 14.39** (IBKR close 08-03) · cap ~$2.97B · **printed Q2 2026-07-29 — not print-blocked**

## FINDING 0 — ENTITY RESOLUTION: the ticker was recycled
The lane brief carried **"ARIS = produced-water midstream"**. **REFUTED.** IBKR `search_contracts`
resolves NYSE `ARIS` (conid **588206703**) to **ARIS MINING CORP**, a Colombia/Guyana **gold**
producer, dual-listed TSE:ARIS (conid 588206705). Aris Water Solutions now appears only as
**`ARIS.OLD`** plus four `CORPACT` tender lines (`ARIS.STK / ARIS.MIX / ARIS.CSH / ARIS.PRO`) — it
was **acquired via tender and the symbol was reassigned.**
Consequences: (1) the sector/industry the screen scored ("Basic Materials / Gold") is right, but the
lane's premise was wrong; (2) **anyone carrying an ARIS price history across the tender boundary is
splicing two different companies.** Log this as a ticker-recycling trap alongside the TCOM
currency-basis and ADIG when-issued lessons.

## The gold-complex tape (the shared denominator for ARIS / MUX / SII)
Adjusted closes, 2026-08-03 vs the 52-week high:

| | last | 52w high | off high | 3m | 1y |
|---|---:|---:|---:|---:|---:|
| GLD | 371.54 | 495.90 (2026-01-29) | **−25.1%** | −12.2% | +20.2% |
| GDX | 74.10 | 115.84 (2026-02-27) | **−36.0%** | −14.9% | +42.3% |
| GDXJ | 95.39 | 156.19 (2026-02-27) | **−38.9%** | −17.3% | +50.1% |
| SIL | 73.75 | 117.87 (2026-02-27) | −37.4% | −16.7% | +56.9% |
| SLV | 52.36 | 105.60 (2026-01-28) | −50.4% | −23.3% | +55.9% |

**The entire precious-metals complex is 36-39% off a Jan/Feb-2026 spike high.** Every "quality
drawdown" in this cohort's PM names is dated to within a month of the GDX/GDXJ peak (ARIS 02-27 —
*the exact GDX peak day*; SII 03-10; MUX 01-28). Three names, one drawdown.

## (a) PATH CHECK
52w low 6.74 (2025-08-19, 346 days) → **+113.5% off the low**; 52w/3y high 22.68 (**2026-02-27**) →
**−36.6%**; **0.0% off its 60-day low** (it closed AT the 60-day low on 07-31); 3m −25.3%; YTD −17.7%.

**GATE VERDICTS:**
- **EXHAUSTED = MECHANICALLY WRONG.** It fired on `HARD_OFF_LOW` (>50% off any low). ARIS is
  literally sitting on its 60-day low — the opposite of an exhausted bounce. The flag has no
  distance-from-high term (same defect as BRZE).
- **falling = RIGHT** (0.0% off the 60-day low is the most literal true positive in the batch).
- The reject is neither of those. It is the factor.

## (b) THE FRAME TEST — decisive
Episode decomposition, **2026-02-27 (the drawdown peak) → 2026-08-03**, betas fitted on the
**pre-window** 3y daily returns:

| proxy | beta (pre) | factor-explained | residual | factor share |
|---|---:|---:|---:|---:|
| **GDX** | 1.07 | **−37.0%** | **−5.6%** | **0.90** |
| GDXJ | 0.97 | −36.8% | −5.8% | 0.90 |
| GLD | 1.62 | −33.3% | −10.7% | 0.81 |

Total episode −41.1%. **90% of it is the gold-miner index.** This is the AEM lesson, and it is a
frame-reject: you are not buying a de-rated business, you are buying GDX with single-name risk
stapled on.

### Why the screen's own `factor_costume` gate missed it (a NEW gate defect)
`quality_drawdown.py:271` computes `factor_costume` from the **3-year maximum residual drawdown**
(`resid_dd / dd < 0.60`). Run that way: **ARIS residual share 0.73 vs GDX / 0.75 vs GDXJ / 1.06 vs
GLD — no fire.** Run on the **episode window**: **0.90 — a screaming fire.**
The two methods disagree because 3y-max-residual-DD answers *"has this name ever underperformed the
factor?"* (yes — 2023-24), not *"is THIS drawdown the factor?"* (yes — overwhelmingly).
**This is distinct from, and additional to, the sibling lane's CCJ finding.** The sibling found the
*lookup* was too coarse (sector→XLE instead of industry→URA). Here the lookup is fine
(Basic Materials→GLD is in the map) and the **method** still inverts the answer. Fixing the industry
map alone would NOT have caught ARIS or MUX.

## (c) ESTIMATE DIRECTION — derailment, and fast
Consensus EPS, current vs 90d / 7d ago: FY0 **2.145 vs 2.418 (−11.3%)**; FY+1 **3.012 vs 3.533
(−14.7% over 90d, and −8.7% in the last SEVEN days)**. Under the sibling lane's DERAIL replacement
(FY+1 EPS −3%/90d) ARIS fires hard. Estimates are being cut into the falling gold price — the
textbook derailment signature, mechanically produced by the commodity.

## (d) CAUSE-CHECK (company events, all secondary to the factor)
- **2026-07-29 Q2 2026 results.** Tape read: *"Aris Mining stock price slide clashes with profit
  surge"* — profits up, stock down, because the stock trades the metal.
- **2026-07-30: filed a WKSI base shelf prospectus** (Canada + US). A live, unquantified equity/debt
  overhang on a name already 37% off its high.
- **2026-07-29: first gold from the 5,000-tpd Segovia plant expansion guided Q4 2026**; 500k oz
  output target. Real operational progress — and it did not stop the stock.
- BMO **cut** its target to $29.24 while maintaining Buy (07-31) — sell-side marking to the metal.

## Scenarios (all three are gold-price scenarios wearing an equity's clothes)
| | p | fv | logic |
|---|---|---|---|
| bear | 0.35 | 9.50 | GDX retests the 2025 base, estimates keep getting cut, shelf is drawn |
| base | 0.45 | 15.00 | gold stabilises here, Segovia ramps on time |
| bull | 0.20 | 23.00 | gold re-approaches the Jan-26 high; 500k oz delivered |

**e_fv $14.68 vs $14.39 → edge +2.0%. Inside the noise, and the variance is entirely the metal.**

## VERDICT — 1/10 FRAME-REJECT
**Route the decision, don't pick the stock.** If the desk wants the −36% gold-complex drawdown, the
instrument is a sleeve-level decision on GDX/GDXJ/PHYS adjudicated against the existing PM ballast
doctrine — not single-name Colombian mining risk with a fresh shelf and estimates falling 8.7% a week.

## Kills / re-look
Re-look only if (a) the sleeve-level PM decision is taken affirmatively AND (b) ARIS's residual-to-GDX
share on a fresh episode window exceeds 0.40 (i.e. it starts trading on its own news).

## Freezable (gate-test, factor-costume calibration)
**ARIS | 2026-12-31 — bar: ARIS total return from the 08-03 close lands within ±8pp of GDXJ's over
the same window. our_p 0.65.**
