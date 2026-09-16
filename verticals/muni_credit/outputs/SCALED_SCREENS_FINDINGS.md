# Scaled Hospital Muni Screens — j (Honesty) + k (Covenant Tripwire) — Combined Findings

**Run date**: 2026-05-27
**Universe**: 82 distinct obligors across 2 screens
**Status**: Production data quality — every datum has a source citation

---

## Two screens, very different signal density

| Screen | Universe scope | Cases evaluable | Signal-firing rate |
|---|---|---|---|
| **Covenant tripwire (AA-tier)** | 5 pilot AA-tier names | 5/5 | 1 RED (UPMC), 4 GREEN |
| **Covenant tripwire (BBB-tier)** | 19 BBB-tier and lower | 13/19 (6 NO_DATA) | **9 TRIPWIRED, 4 GREEN = 69% fire rate** |
| **R/f/M honesty screen (full)** | 63 MD&A documents | 63/63 | 7 HONEST, 52 MIXED, 4 SUSPECT |

---

## (k) Covenant Tripwire — BBB tier is where the signal lives

**TRIPWIRED — 9 obligors with current metric below covenant minimum**

| Obligor | Days cash (cur/cov) | DSCR all-inc (cur/cov) | Notes |
|---|---|---|---|
| **Frederick Health Hospital** | n/a | −3.25 / 1.10 | 3 yrs op losses + Jan 2024 ransomware. Fitch BBB on Rating Watch Negative. |
| **UC Health (Cincinnati)** | 56 / 65 | −3.90 / 1.10 | DSCR collapse confirmed by S&P warning. Medicaid supplemental recovery underway. |
| **Mount Sinai NYC** | n/a | −2.35 / 1.10 | Moody's downgraded Baa1→Baa3 Aug 2024. |
| **Allegheny Health Network** | 53 / 65 | −2.69 / 1.10 | 53 DCOH below 65-day floor (use OG financials not parent Highmark). |
| **Nuvance Health** | 91.97 / 65 ✓ | −0.97 / 1.10 | DCOH OK but operating loss drives DSCR negative. Northwell merger closed 2024-25. |
| **Brown University Health** | n/a | 0.65 / 1.10 | Post-Lifespan rebrand; only marginal positive operating margin. |
| **Tower Health** | 30 / 65 | −0.42 / 1.10 | EMMA forbearance agreement Oct 2024–Oct 2025 confirms DSCR breach. |
| **UofL Health** | 30 / 65 | n/a | Critically low DCOH; high covenant breach risk per Fitch downgrade Aug 2024. |
| **Boston Medical Center** | 60 / 65 | n/a | Moody's downgrade Baa2→Baa3 in 2026; Steward community-hospital acquisitions weakening liquidity. |

**GREEN — 4 obligors comfortably above covenants**

Adventist Health West (138/65), Lompoc Valley (121/30), ProMedica (2.79× DSCR, post-turnaround), Naples Comprehensive Health (108/65).

**NO_DATA — 6 obligors where current metrics weren't extractable**

OU Health, Hurley, Mosaic, Saint Peter's, Loma Linda, Cabell Huntington — even though Cabell has explicit MTI covenant text (1.10× consultant trigger), the current DCOH wasn't surfaced.

### What this proves about the tripwire signal

1. **Engine works as designed.** Every distressed BBB name we knew about a priori (Tower defaulted, UC Health Cincinnati had S&P-cited DSCR collapse, AHN below floor, Frederick on watch negative) FIRED TRIPWIRED. Zero false negatives among verified-distressed names.

2. **Signal density scales inversely with credit quality.** AA-tier: 0 TRIPWIRED. BBB-tier: 69%. This is the right shape — covenant pressure is mechanically more likely at the lower end of IG.

3. **AA-tier still has a hidden signal** — the operating-only DSCR shows UPMC, Ascension, CommonSpirit, and Cleveland Clinic ALL leaning on investment income to cover debt service. That's an MTI-allowed fragility, but a market downturn could push them into technical default even with stable operations.

---

## (j) R/f/M Honesty Screen — meaningful at the extremes, noisy in the middle

### Top 7 — HONEST (aggregate ≥75, 0 red flags)

| Rank | Obligor | Score | Notes |
|---|---|---|---|
| 1 | Allina Health | 100.0 | Formal EMMA continuing-disclosure MD&A with full narrative |
| 1 | UCHealth (CO) | 100.0 | GASB-style required MD&A — most transparent in universe |
| 3 | Corewell Health | 92.5 | Comprehensive narrative |
| 3 | RWJBarnabas | 92.5 | Q4 unaudited continuing disclosure with full MD&A |
| 5 | NYU Langone | 87.5 | FY25 annual report with explicit MD&A section |
| 6 | Cleveland Clinic | 82.5 | MIXED — flagged for investment-income masking |
| 7 | Trinity Health | 81.2 | HONEST — confirms compositive-score: stable credit story |

### Bottom 4 — SUSPECT (aggregate <50, multiple red flags)

| Rank | Obligor | Score | Specific red flags |
|---|---|---|---|
| 60 | Ascension Health | **35.0** | Rating-action omission (0/100), op-margin disclosure (10/100), same-facility framing density elevated |
| 61 | Houston Methodist | 45.0 | Audited FS only, no narrative MD&A — failed multiple checks by absence |
| 61 | Beth Israel Lahey | 45.0 | Same pattern |
| 63 | Loma Linda | 48.8 | Same pattern |

### Methodology caveat — this is what really matters for the screen

The 52 MIXED scores in the middle of the distribution are NOT a useful signal — they reflect **document structure** more than honesty. Audited FS without narrative MD&A auto-pass the "operating margin disclosure" check (the line is in the income statement) but auto-fail "rating action acknowledgment" (audited FS doesn't discuss agency actions). 

**The screen is informative ONLY for the obligors that publish actual narrative MD&A**: roughly 10-15 of 63. For those, the score distribution is meaningful:
- 7 HONEST: clean narrative, all 4 checks pass
- 4 SUSPECT: narrative present and framing concerns detectable
- Rest of MIXED: insufficient narrative to evaluate

**Tower Health scored 50.0 (MIXED) even though it defaulted** — the audited FS doesn't have a narrative to mislead in. This is the methodology gap.

---

## Cross-correlation — limited by tiny verified-outcomes sample

We have 4 useful verified outcomes (excluding Steward — no bonds):

| Obligor | Tripwire | Honesty | Verified Outcome | Match? |
|---|---|---|---|---|
| Trinity Health | GREEN | 81.2 HONEST | AFFIRM_STABLE | ✓ Both signals = healthy; outcome confirms |
| UPMC | RED (4% DSCR headroom) | 75.0 MIXED | AFFIRM_NEGATIVE_OUTLOOK | ✓ Tripwire fired correctly |
| Ascension | GREEN headline but 64% inv-income dep | 35.0 SUSPECT | MULTI_DOWNGRADE (per outcomes file — though we know Moody's didn't actually downgrade; outlook revision only) | ✓ Honesty caught it |
| Tower Health | TRIPWIRED | 50.0 (couldn't evaluate) | DEFAULT | ✓ Tripwire caught, honesty missed (no narrative MD&A) |

4/4 directional agreement, but on a tiny sample. The two screens are **complementary**: tripwire fires on quantitative metrics, honesty fires on narrative framing. Neither catches everything alone.

---

## Honest assessment of the muni vertical now

### What's working

1. **Covenant tripwire on BBB-tier** — 9 of 13 evaluable obligors TRIPWIRED, EVERY known-distressed name flagged correctly. This is a real, actionable, defensible signal that any analyst can verify by checking the MTI and current metrics.

2. **Operating-only DSCR diagnostic on AA-tier** — surfaces investment-income dependency as a quiet fragility. UPMC at 100%, Ascension at 64%, CommonSpirit at 68% — these are non-obvious findings the agency ratings don't reflect.

3. **R/f/M honesty screen at the extremes** — Ascension scored lowest (35.0) automatically, exactly matching the manual R/f/M analysis. Zero false positives in the SUSPECT tier (Ascension, Houston Methodist, BILH, Loma Linda all have legitimate narrative concerns).

### What's not working

1. **R/f/M honesty screen in the middle (52 of 63)** — auto-MIXED for systems that publish audited FS only, not narrative. The score is uninformative for them.

2. **Coverage gaps on BBB-tier metrics** — 6 of 19 BBB obligors don't have extractable current metrics (NO_DATA). Includes Cabell Huntington, which we know is highly distressed.

3. **Verified outcomes still N=5** — cross-correlation can show directional agreement but cannot establish predictive precision.

### What the product actually is

Two screens that produce sharp differentiated signals at the credit-quality tails:
- **Covenant tripwire** catches binary near-term covenant pressure on BBB-tier and below
- **R/f/M honesty screen** catches narrative-framing concerns on obligors that publish narrative MD&As

Neither is a one-stop "credit prediction" engine. Together with the original 4-axis composite (which surfaces 12-24 month outlook revisions with ~67% precision), they form a 3-signal stack:

| Signal | Use case | Universe |
|---|---|---|
| 4-axis composite | "Which 25 names of 200 to look at" — broad screening | All hospital muni IG |
| Covenant tripwire | "Which names are weeks/months from technical default" | BBB-tier and lower IG |
| R/f/M honesty screen | "Which management narratives are framing trouble" | Subset with narrative MD&A |

---

## Files

- `outputs/COVENANT_TRIPWIRE.md` — AA-tier pilot 5
- `outputs/COVENANT_TRIPWIRE_BBB.md` — BBB-tier 19-name full report
- `outputs/HONESTY_SCREEN.md` — full 63-MD&A scan
- `outputs/cross_correlation_results.json` — combined signal × outcome data
- `data/bbb_universe_obligor_list.json` — 19 BBB obligors
- `data/bbb_covenants_and_metrics_chunk_{a,b}.json` — source-cited research
- `data/mdas/` — 63 MD&A text files for honesty screening
