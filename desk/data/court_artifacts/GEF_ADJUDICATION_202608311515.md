# ADJUDICATION — GEF / GEF.B (Greif Inc dual-class spread) — 2026-08-31

**Ruling: KILLED (instrument thesis) — the 1st-percentile A/B spread is STRUCTURAL, not a
dislocation. Refutability bench SUSTAINED in full, with one strengthener it missed. First
dual_class_screen court: the generator found a real extreme and the extreme has a legal
explanation — screen amendment mandated below.**

## Tier re-verification (adjudicator; bench was SEC-403'd and IBKR-denied)

1. **Charter (10-K Ex-4.3, read at primary via proxy) — VERIFIED VERBATIM.** Dividend
   proportion "$0.01 per share to the holders of Class A ... $0.015 per share to the holders
   of Class B"; Class A cumulative (base $0.01/yr), gains votes only if four quarterly
   cumulative dividends default; Class B holds all general votes; liquidation pro rata after
   token $0.15625 preferences; **"no preemptive, conversion, or other subscription rights"**
   — no sunset, no collapse provision. The fair-ratio band [1.00, 1.50] is charter law.
2. **STRENGTHENER the bench missed (10-Q Note 10):** the **earnings allocation itself**
   follows the same 1:1.5 proportion — EPS_B ≡ 1.5 × EPS_A by accounting construction. The
   spread isn't merely dividend-driven; the entire per-share income statement is ratioed.
3. **Live tape (IBKR gateway, both classes):** A (4812174) $83.07 −1.2%; B (4812176) $106.35
   −1.1%. Ratio 1.280 → spread −21.9%. IBKR prior closes 84.08 / 107.53 reconcile the bench's
   vendor closes to the cent — its bar work stands. ADV: A $20.8M/day, B $9.5M/day (both legs
   executable outright at our rail; the pair's problem was never liquidity).
4. **Share counts / buyback skew (10-Q cover + repurchase note) — VERIFIED.** A 24,808,643 /
   B 21,359,678 (7/27/26); repurchases 9mo FY26: **1,813,600 Class A vs 371,449 Class B**
   ($151.4M). Vendor trap confirmed again: stockanalysis prints one combined share count on
   both tickers (~23% overstated per class) — vendor-artifact family member #5, new evidence.

## Why the pair dies (all four adjudication tests)

(a) **Spread real?** Yes — bar-confirmed at −21.9%, 1st percentile of 6y history.
(b) **Mechanism?** Yes, and it's *legal*, not behavioral: charter fixes cash claims at 1:1.5.
    Ratio 1.28 sits INSIDE the [1.00, 1.50] fair band, 60% of the way to the cap. The 6-year
    near-parity mean was the anomaly — a legacy regime the $1.8B PCA containerboard sale and
    3.1x→1.1x deleveraging destroyed. Percentile-vs-own-history reverts to a dead regime.
(c) **Convergence path?** None. No conversion right, no sunset, negative carry before borrow
    (short B pays 3.46%, long A earns 2.95%), B ~45% family-held. A spread with no forcing
    mechanism is a statistic, not a trade.
(d) **Executability?** Both legs fine outright; moot for the pair, which fails on (b)/(c).

## What survives (routed, not ruled here)

**Outright Class A fundamentals question**: 8.4x EV/EBITDA, 1.1x net leverage, FY26 guide
EBITDA $615–635M / FCF $305–325M, buyback restarting and historically 5:1 skewed to A —
A captures the retained-cash strip the market prices at ~10% while the dividend strip trades
at 5.3%. PROPOSED: enqueue a standard fundamentals court sourced `gef_adjudication_survivor`
if the desk wants the name; nothing about the spread itself justifies risk.

## Dispositions

- **Calibration freeze:** GEF-RATIO|2027-02-26: P(bar-computed B/A close ratio ≥ 1.20) = 0.75
  — grades the structural no-reversion thesis against the screen's mean-reversion premise.
- **KG — generator amendment (MANDATED):** `dual_class_screen` must consult a per-name
  charter-claims map (dividend ratio, earnings-allocation ratio, conversion/sunset rights)
  and flag only spreads OUTSIDE the charter-implied fair band, or extremes in classes with
  IDENTICAL cash claims. GEF at ratio 1.28 inside [1.00, 1.50] must not re-fire.
- **KG — vendor-artifact family evidence row:** dual-class combined-share-count misprint
  (both Greif tickers show ~56.85M shares; true 24.8M + 21.4M split, caps off by ~$0.4B).
- **Runner tickets (pack defects):** (i) pack `ibkr_gw` px 87.195 was ~2wk stale (true close
  84.08) — 3pp error on the exact quantity screened; (ii) pack next-print 2026-10-28 is
  yfinance legacy of the OLD Oct-31 FYE — Greif moved FYE to Sept 30; next print ~early-Nov
  2026, unconfirmed, no PR yet.
- **Drains:** B short borrow unverified (moot — pair killed); FY26 Q4 print date watch.

Sources: 10-K Ex-4.3 (charter); 10-Q 6/30/26 acc. 0001628280-26-050547 (cover counts, Note 10
allocation, repurchase note); dividend PR 8/25/26 ($0.62 A / $0.93 B = 1.5000x); Q3 FY26
release 7/28/26 (leverage, guide); IBKR live tape both classes 2026-08-31.
