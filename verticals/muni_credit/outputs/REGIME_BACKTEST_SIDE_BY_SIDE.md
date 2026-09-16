# Two-Regime Backtest: CA Muni Duration vs Equities
### Dot-com (Fed-cutting growth scare) vs 2022 (Fed-hiking rate shock) — side by side
*Signal OS / muni_credit · 2026-06-06 · folds into CA_MUNI_EQUITY_HEDGE_REPORT.md Ch3*

## The two regimes, same assets

| Asset (≈ duration) | **Dot-com 2000–02** (Fed 6.5%→1.0%, growth scare) | **2022** (Fed 0.08%→4.4%, rate shock) | Data quality |
|---|---|---|---|
| Fed funds / 10yr move | cut to 1.0% · 10yr **−275 bp** | hiked to 4.4% · 10yr **+225 bp** | real (FRED) |
| **S&P 500** | **−37.6%** (3-yr cum) | **−18.1%** | real |
| CA muni VCITX (dur ~7) | **+30.3%** | ≈ −10% | real (’00–02) |
| Nat'l muni VWLTX (dur ~7.5) | **+30.5%** | **−10.4%** | real |
| HY muni VWAHX (dur ~7) | **+25.2%** | **−11.8%** | real |
| **Max-dur muni sleeve (dur 14.5)** | **~+30–40%** *(estimate — bonds didn't exist in 2000)* | **−20% to −32%** *(range; see note)* | mixed |
| Long Treasury VUSTX (dur ~16) | **+44.4%** | **−29.6%** | real |
| Treasury STRIPS / EDV (dur ~30) | n/a (post-2002) | **−39.9%** | real |

*Sleeve 2022 = actual EMMA trade prices: CA State GO −38.1%, Duarte −34.3%, Pomona −31.7% (3 of 6
traded a full year; Alpine/Bethany/Sanger were too illiquid to mark). Sleeve dot-com is
duration-inferred, NOT actual.*

## Conclusions (each tagged with its evidence — for audit)

**C1 — The equity-correlation SIGN is set by the Fed's direction, not the asset.** Same bonds:
strongly *negative* correlation with equities when the Fed cut (dot-com: munis +25–44% while S&P
−38%), strongly *positive* when the Fed hiked (2022: munis −10 to −40% alongside S&P −18%).
*Evidence: real fund + index returns both regimes. Robust.*

**C2 — Magnitude scales with duration, in BOTH directions — duration is leverage on the rate move,
not protection.** Dot-com: dur-16 VUSTX (+44%) > dur-7.5 VWLTX (+30%). 2022: dur-30 STRIPS (−40%)
< dur-16 VUSTX (−30%) ≈ dur-14.5 sleeve (−30%) < dur-7.5 VWLTX (−10%). *Evidence: monotonic in
duration across 5 real instruments in 2022; directionally in dot-com.*

**C3 — In a rate-shock crash the long-duration "hedge" loses MORE than equities.** 2022: the sleeve
(−30%), VUSTX (−30%), and STRIPS (−40%) all fell *harder* than the S&P (−18%). The hedge became the
single worst position. *Evidence: real 2022 returns + sleeve EMMA. Robust.*

**C4 — CA munis are a tax-wrapped version of the Treasury rate bet.** VWLTX tracks VUSTX
directionally in both regimes (both up double digits dot-com, both down double digits 2022); munis
add tax-exempt carry + some credit/liquidity noise, but the rate-direction beta dominates.
*Evidence: muni and Treasury funds move together both regimes. Strong.*

**C5 — You cannot pre-select the regime, and it's adversely correlated with the crash type.** The
crash type (growth-scare vs rate-shock vs liquidity) decides whether the position hedges or
amplifies, and it's unknowable ex ante. Worse: a long-duration muni "hedge" fails precisely in the
*inflationary* crashes where the Fed CAN'T cut — i.e. it's least reliable exactly when you'd most
want protection. *Evidence: 2 regimes here + 2008/2020 OOS (degraded/broke, Ch3). Directional,
N small.*

**C6 — Residual honest value: it's an income holding, not a hedge.** Tax-exempt income accrued in
both regimes (~5%/yr); for a buy-and-hold CA holder with good credit (school-GO), the 2022 −30%
mark is paper, not a realized loss. *Evidence: coupon income is contractual; credit held (no
muni defaults in the sleeve). Fair.*

## Caveats (honest ledger)
- **N = 2 regimes** in this table (the OOS 2008/2020 in Ch3 add support but aren't shown here).
- **Horizon mismatch:** dot-com is **3-yr cumulative**, 2022 is **1-yr** (the dot-com bear ran ~3
  years; 2022 ~1). Annualized, dot-com muni ≈ +9%/yr.
- **The sleeve's dot-com cell is an ESTIMATE** (bonds didn't exist in 2000) — only its 2022 number
  is actual EMMA. Conclusions lean on the *real* cells (funds, VUSTX, S&P, sleeve-2022), not the
  estimate.
- Returns are total return except S&P/sleeve-EMMA noted; dur figures are approximate.

## ⚠ Hostile-review corrections (R/f(M) panel, 2026-06-06) — conclusions downgraded

A hostile R/f(M) audit of C1–C6 (file-access, verified vs the data) found most are overstated.
Corrected status:

- **Sleeve 2022 "−30%" was hand-picked, not reproducible.** The methods give a **range −20% to
  −32%**: duration-scaled fund estimate −20% (total); the 3 bonds that traded a full year fell
  −32 to −38% price (≈ −32% total with income); **3 of 6 names were too illiquid to mark at all**
  (Alpine's +4.27% was a 6-week mid-year window, not a full-year return — excluded as
  non-comparable, but the report shouldn't have implied a single "−30%"). Table corrected.
- **C1 / C5 — DOWNGRADED to hypothesis.** "Fed direction sets the correlation sign" is **N=2
  correlation, not causation**, and **confounded**: 2022's positive muni-equity correlation is
  explained by a *common inflation factor* hitting both, not "the Fed hiking." It is also
  **contradicted by our own Ch3 OOS**: in 2008/2020 the Fed *cut* yet munis co-crashed (liquidity).
  The honest variable is **"duration-dominant AND a disinflationary / flight-to-quality shock,"**
  not Fed direction per se. C1 and C5 partly contradict each other.
- **C2 — NARROWED.** The robust result is **2022 duration-monotonicity across 5 *real* instruments**
  (STRIPS −40 < VUSTX −30 ≈ sleeve < VWLTX −10). "Both directions" is oversold — the up-leg rests
  on one real VUSTX>VWLTX pair plus the (estimated) dot-com sleeve cell.
- **C3 — NARROWED to the Treasury cells.** "Long-duration fell harder than equities in 2022" is
  robust and horizon-fair for **VUSTX (−30%) and STRIPS (−40%) vs S&P (−18%)**. The *muni-sleeve*
  version holds only at the pessimistic end of its −20/−32% range.
- **C4 — CUT.** "Munis = a tax-wrapped Treasury bet" **contradicts this project's own thesis**: in
  dot-com CA muni *credit* decoupled from Treasuries (AA→BBB, worst-in-nation) — the cap-gains
  credit channel (the whole β-CapGains point) is a *separate, regime-specific* signal, not "noise."
  Munis ≈ a tax-wrapped Treasury duration bet **on price**, *plus* a credit channel that decouples.
- **C6 — DOWNGRADED.** "The −30% is paper" is a mark-to-market fallacy: it ignores **opportunity
  cost** (capital locked at a 2.97% coupon while reinvestment yields repriced to ~5%), **duration
  risk** for any horizon < ~15yr, and that the **illiquidity making it "unrealized" is itself the
  cost** (you can't sell), not a comfort.

**The one audit-clean takeaway:** *long duration is a rate bet, not an equity hedge; in the 2022
rate-shock episode long-duration Treasuries (real, verifiable) fell harder than equities, monotone
in duration.* Everything stronger than that is N=2, confounded, or contradicts the project's own
credit work.

*Sources: FRED (rates), Yahoo Finance (VCITX/VWLTX/VWAHX/VUSTX/S&P), EMMA RTRS (sleeve prices),
`data/stress2022.json`, `data/anticorr_sleeve.json`.*
