# Hospital Muni Signals — Classification Accuracy Backtest

**Run date**: 2026-05-27
**Snapshot date**: 2022-12-31
**Forward window**: 2023-Q1 through 2025-Q1
**Sample**: 84 hospital muni obligors with primary-source-verified rating outcomes
**Question**: Do our signals predict rating-action deterioration better than baseline?

---

## Bottom-line verdict

**One signal beats baseline. Two do not.**

| Signal | n evaluable | Precision | Recall | Accuracy | Baseline | **Lift** |
|---|---|---|---|---|---|---|
| **Covenant tripwire** (LOOSE) | 12 | 67% | 67% | 67% | 50% | **+17 pp** ✓ |
| **Composite STRONG_SELL** (LOOSE) | 36 | 38% | 42% | 58% | 67% | **−8 pp** ✗ |
| **Composite STRONG_SELL** (STRICT) | 36 | 23% | 30% | 53% | 72% | **−19 pp** ✗ |
| **R/f/M honesty SUSPECT** (LOOSE) | 34 | 50% | 9% | 68% | 68% | **0 pp** — |
| **Covenant tripwire** (STRICT) | 12 | 33% | 50% | 50% | 67% | **−17 pp** ✗ |

Tripwire LOOSE is the only result above baseline. STRICT (formal-downgrade-only) underperforms because both tripwire and composite fire on outlook revisions more often than formal downgrades — the agencies are slower than the signals.

---

## What "LOOSE" vs "STRICT" means

- **LOOSE deterioration**: DOWNGRADE, MULTI_DOWNGRADE, DEFAULT, **or** AFFIRM_NEGATIVE_OUTLOOK
- **STRICT deterioration**: only DOWNGRADE, MULTI_DOWNGRADE, DEFAULT

We focus on LOOSE because outlook revisions ARE rating actions and they DO move bond spreads (though less than formal downgrades).

---

## Universe outcome distribution (n=84)

| Outcome | n | % |
|---|---|---|
| AFFIRM_STABLE | 40 | 48% |
| DOWNGRADE | 13 | 15% |
| UPGRADE | 12 | 14% |
| MULTI_DOWNGRADE | 7 | 8% |
| AFFIRM_NEGATIVE_OUTLOOK | 4 | 5% |
| DEFAULT | 2 | 2% |
| AFFIRM_POSITIVE_OUTLOOK | 2 | 2% |
| UNVERIFIABLE / unknown | 4 | 5% |

**Base rate of deterioration (LOOSE): ~33%** — roughly 1 in 3 hospital muni obligors deteriorated in the 27-month window.

---

## Signal #1: 4-axis composite STRONG_SELL (≤ −2.0 notches)

**Verdict: WORSE THAN BASELINE on the verified outcomes.**

| Metric | LOOSE | STRICT |
|---|---|---|
| n evaluable | 36 | 36 |
| TP | 5 | 3 |
| FP | 8 | 10 |
| TN | 16 | 16 |
| FN | 7 | 7 |
| Precision | 38% | 23% |
| Recall | 42% | 30% |
| Accuracy | 58% | 53% |
| Baseline (always predict stable) | 67% | 72% |
| **Lift over baseline** | **−8 pp** | **−19 pp** |

**What this means**: the composite signal was claimed to be "97% hit rate / 11-of-11 downgrades predicted" in the original tearsheet. **That number was an artifact of hand-curated outcomes that we now know were wrong on ~80% of the pilot 5**. With verified outcomes, the composite is **worse than always predicting "stable"** — it has too many false positives (8 of 13 SELL signals didn't deteriorate).

Why? Two reasons:
1. The composite favors deteriorating credits, but most credits are stable — it picks the "leaning bear" reflexively even when nothing changes
2. The agencies are slower than the composite implies. The composite predicts formal downgrades; reality is more often outlook revisions or stable affirmations

---

## Signal #2: Covenant tripwire (TRIPWIRED or RED tier)

**Verdict: WORKS at LOOSE threshold (+17 pp lift over baseline), small sample (n=12 evaluable).**

| Metric | LOOSE | STRICT |
|---|---|---|
| n evaluable | 12 | 12 |
| TP | 4 | 2 |
| FP | 2 | 4 |
| TN | 4 | 4 |
| FN | 2 | 2 |
| Precision | 67% | 33% |
| Recall | 67% | 50% |
| Accuracy | 67% | 50% |
| Baseline (always predict deterioration) | 50% | 67% |
| **Lift over baseline** | **+17 pp** | **−17 pp** |

**What this means**: when the tripwire fires, **2 out of 3 times** the obligor actually has a negative outlook revision or worse in the next 24 months. **2 of 3 actual deteriorations** in the evaluable BBB universe are flagged.

**The big asterisk: n=12.** That's tiny. With this sample, 95% CI on 67% accuracy is roughly **40-85%**. Calling the signal "real" is provisional — we'd want n≥40 evaluable cases to claim it confidently. The 12 unknowns are mostly BBB obligors where we couldn't extract current metrics from public sources.

**Specific cases (verified true positives)**:
- UC Health Cincinnati: TRIPWIRED → MULTI_DOWNGRADE (Moody's A3→Baa3, 3 notches)
- Frederick Health: TRIPWIRED → DOWNGRADE (Fitch A-→BBB+)
- Mount Sinai NYC: TRIPWIRED → MULTI_DOWNGRADE (Moody's Baa1→Baa3, 2 notches)
- Tower Health: TRIPWIRED → DEFAULT (distressed exchange Sept 2024)

**False positives (signal fired, outcome stable)**:
- Allegheny Health Network: TRIPWIRED → AFFIRM_STABLE
- Brown University Health: TRIPWIRED → AFFIRM_POSITIVE_OUTLOOK
- (Probably because these had low DCOH/DSCR but managed it without rating action)

---

## Signal #3: R/f/M honesty SUSPECT

**Verdict: ZERO LIFT over baseline. Fires too rarely (only 2 obligors) to have meaningful predictive power.**

| Metric | LOOSE | STRICT |
|---|---|---|
| n evaluable | 34 | 34 |
| TP | 1 | 1 |
| FP | 1 | 1 |
| TN | 22 | 24 |
| FN | 10 | 8 |
| Precision | 50% | 50% |
| Recall | 9% | 11% |
| Accuracy | 68% | 74% |
| Baseline (always predict stable) | 68% | 74% |
| **Lift over baseline** | **0 pp** | **0 pp** |

**What this means**: the SUSPECT tier fires on only 2 obligors (Ascension + Houston Methodist) out of the 34 with matched outcomes. Ascension's outcome was AFFIRM_NEGATIVE_OUTLOOK (true positive), Houston Methodist's outcome was AFFIRM_STABLE (false positive). The signal **doesn't fire often enough to catch the 10 deteriorations** that occurred — recall of 9%.

The honesty screen's value is **qualitative diagnostic**, not predictive. Identifying that Ascension's MD&A had Mode B framing concerns is useful for a buyside analyst doing a deep dive on one credit, but it doesn't aggregate into a usable screen at sample size.

---

## Honest summary of what we built

| Claim from prior tearsheet | Verified reality |
|---|---|
| "97% directional hit rate on 24-month forward backtest" | **38-58% accuracy depending on threshold**; below baseline at strict, marginally above at loose |
| "11 of 11 actual rating downgrades flagged" | Composite caught ~3-5 of 12 verified downgrades in this universe (25-40% recall) |
| "Two of two defaults correctly excluded via override" | True — system_distress_axis still correctly excluded Tower + Steward |
| "Covenant tripwire flags near-term technical default" | **+17 pp lift over baseline**, but n=12 only — provisional but real signal |
| "R/f/M honesty screen predicts deterioration" | Not at scale. Useful for one-credit deep dives, not as a portfolio screen |

---

## What's defensible

1. **Covenant tripwire on BBB-tier obligors** — the only signal with measurable lift. n=12 limits confidence but every distressed name we knew about a priori (UC Health Cincinnati, Frederick, Mount Sinai, Tower) was caught. Worth running and expanding the universe.

2. **System distress axis override** — correctly excluded Tower from a STRONG_BUY signal that would have lost money. Risk management value confirmed.

3. **R/f/M honesty as a single-credit deep-dive tool** — Ascension finding validated qualitatively even though the screen has 9% recall at portfolio level.

## What is NOT defensible

1. **The original "97% hit rate" claim** — it was wrong because the outcomes file was hand-curated and ~60% inaccurate on the pilot sample.
2. **The 4-axis composite as a SELL screen** — empirically worse than baseline on verified outcomes.
3. **The honesty screener as a portfolio-level signal** — too sparse to fire on enough names.

---

## What to do next

1. **Expand BBB-tier evaluable universe** — the 12 unknowns are mostly BBB names where current metrics weren't extractable. Pulling those (CAFR + HCRIS via LLM extraction) would push n to ~30 and tighten CIs on the tripwire signal.
2. **Re-examine the composite scoring methodology** — the SELL signal is firing on too many names that turn out stable. Either narrow the threshold or rebuild the underlying score weights against verified outcomes.
3. **Stop publishing the composite hit-rate number** until it's been rebuilt against verified outcomes.
4. **Strike or rewrite the tearsheet** — the central claim is no longer supported.

---

## Files

- `outputs/classification_accuracy_results.json` — full per-signal confusion matrices and per-obligor detail
- `data/verified_outcomes_2023_2025/per_obligor/*.json` — 84 source-cited verified outcome records
- `classification_accuracy.py` — analyzer (reproducible)
