# Social-Lift Overlay — PRE-REGISTERED Backtest Spec

*Locked 2026-06-26, BEFORE the data exists. Status: PRE-REGISTERED / data accumulating. The point of locking now is to prevent p-hacking the overlay into looking predictive after the fact — same discipline as the frontrun/MAUDE pilots. Do NOT edit the predictor/target/success definitions after seeing results; if the design is wrong, version it (v2) with a dated note, don't silently retune.*

## The question
Does the TikTok virality of a company's brand(s), observed in near-real-time, **predict that company's next earnings result (and post-print return) beyond what's already priced** — and is the effect **stronger for brand-owners than for ODMs**? (The whole "social lift on Cosmecca" premise rests on this; today it's an assumption, not a measured edge.)

## Hypotheses (directional, locked)
- **H1 (signal):** cross-sectionally, higher in-quarter social_score → positive revenue surprise vs consensus for that quarter, and positive post-print drift. Predicted IC > 0.
- **H2 (the contrast — the load-bearing one):** **brand-owner cohort IC > ODM cohort IC.** Rationale: for a brand-owner the viral brand IS a material slice of revenue; for a diversified ODM (top-5 customers <35%) any single viral brand is diluted to near-noise. If H2 fails (ODM IC ≈ brand-owner IC), the "map virality → ODM" thesis is wrong and we stop applying social-lift to Cosmecca/Cosmax.

## Predictor (LOCKED)
`social_score(ticker, Q)` = the quarterly mean of the daily [Σ TikTok-CC views of that ticker's *mapped, confirmed* trending brand-hashtags], from `beauty_velocity_log.jsonl`. Cross-sectionally **z-scored within each quarter** (so it's a relative, not absolute, signal). Confirmed = registry brand_owner OR openFDA-confirmed ODM link only (NO speculative links — cf. the Dr. Melaxin artifact that manufactured a spurious +1.5%). Robustness variants (report but H1/H2 judged on the primary): (a) Σ views, (b) Δ-velocity (in-Q mean vs prior-Q mean), (c) count of distinct trending brands.

## Target (LOCKED)
- **Primary:** revenue surprise = (actual quarter revenue − pre-print consensus) / consensus, point-in-time consensus snapshotted BEFORE the print.
- **Robustness:** 1-day and 20-trading-day post-print stock return (the tradeable form).
- For ODMs, also test the **segment** target (the export/US-indie segment revenue, the leg actually exposed to the viral brands) — a cleaner test than group revenue.

## Timing / lag (LOCKED, no-leak)
- social_score for quarter Q uses ONLY days within Q (all knowable by Q-end, before the print).
- It predicts the **quarter-Q print** (reported ~45 days after Q-end). Robustness: also test predicting **Q+1** (a slower demand→shipment→recognition lag for ODMs).
- Consensus = the last pre-print estimate. Returns measured from the print date forward. No future data in any predictor.

## Cohorts
- **Brand-owner:** ELF, APR, and any mapped brand_owner ticker (EL, OR.PA, BEI.DE, 090430.KS, 4911.T, TXRH/CMG/CROX/LULU/SN/… as they trend).
- **ODM:** Cosmecca (241710), Cosmax (192820), Kolmar (161890) — via their confirmed customer-brands.

## Success / kill criteria (LOCKED)
- **Real signal:** primary rank-IC (Spearman) > +0.15 with the predicted sign, hit-rate > 55%, AND H2 holds (brand-owner IC − ODM IC > 0.10), over **N ≥ 30 company-quarters per cohort**.
- **Kill (for that cohort):** IC ≈ 0 (|IC| < 0.05) or wrong-signed after N ≥ 30 → stop using social-lift for that cohort. Specifically, if **ODM IC fails**, set the Cosmecca social-lift coefficient permanently to 0 (the model already defaults ~neutral; this would confirm it).
- **Multiple-comparisons guard:** the PRIMARY test is {primary predictor × revenue-surprise target × the H2 contrast}. The robustness variants are descriptive only; we do NOT promote a variant to "the result" if the primary fails.

## Power / timeline (honest)
Daily logging started 2026-06-26. Predictor needs a full quarter of history:
- **Q3-2026** (Jul-Sep) = first full predictor quarter → **Q3 prints land Oct-Nov 2026** = first joinable cohort (N ~10-15 names, UNDERPOWERED — directional peek only, no go/no-go).
- **Powered backtest (N≥30/cohort): ~mid-2027** (Q3'26 + Q4'26 + Q1'27 cohorts). Until then: accumulate, do not over-interpret.

## What we will NOT do
No peeking-and-retuning, no dropping inconvenient names, no swapping the target after seeing the IC, no claiming a robustness variant as the headline. If N is too small we say "underpowered" and wait. Companion harness: `social_lift_backtest.py` (builds the predictor panel from the logs, reports readiness, computes the IC once targets are joined).
