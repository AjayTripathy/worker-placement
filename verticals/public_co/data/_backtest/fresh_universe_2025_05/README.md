# Fresh-Universe Framework Alpha Test — Setup (v2, shortable)

## What changed from v1

v1 setup had 15 names from the AIRO signature at $100M-$500M mcap. After
checking shortability at the 2025-05-15 cutoff, **only 4 of 15 were
shortable** (price ≥ $5, daily $vol ≥ $1M). The unshortable subset
contained most of the catastrophic shorts (LBUY -99%, VIVK -99%, GNPX
-93%, etc.) — confirming the structural friction-as-moat property.

v2 expands the mcap band to $100M-$2B, including 7 more names from the
$500M-$2B tier. After re-applying the shortability filter, **8 names
survive** as a real testable universe.

## Universe (8 shortable names)

| TK   | Industry              | Entry $   | Daily $vol | 12mo return  |
|------|-----------------------|----------:|-----------:|-------------:|
| LRHC | Real-estate brokerage |    $1,120 |     $1.9M  | **-99.9%**   |
| KULR | Energy storage / BTC  |    $11.84 |     $16M   | -69.6%       |
| HDSN | Refrigerants          |     $7.88 |     $4M    | -37.6%       |
| PESI | Hazmat / nuclear      |     $9.57 |     $1.5M  | +1.8%        |
| CWCO | Water utility         |    $25.62 |     $2.9M  | +13.1%       |
| CDNA | Diagnostic biotech    |    $16.10 |     $19M   | +24.0%       |
| ALMU | Compound semis        |    $12.22 |     $3.3M  | **+103.4%**  |
| KLIC | Semi packaging eq.    |    $33.51 |     $23M   | **+204.5%**  |

**Mean: +17.5% (so short basket = -17.5%). Median: +18%.**

Returns are bimodal — 3 catastrophic shorts (LRHC, KULR, HDSN), 3 mild
positives (PESI, CWCO, CDNA), 2 catalyst rallies (KLIC, ALMU). The
catalyst rallies dominate the mean despite the median being neutral-
positive. Equal-weight short basket loses to long basket of these names.

## What the framework test decides

The test question becomes specific: **can the framework's multi-source
aggregation correctly suppress the catalyst-rally names (KLIC, ALMU,
maybe CDNA) while keeping the catastrophic shorts (LRHC, KULR, HDSN)?**

If yes → real multi-source alpha beyond the single-signal screen.
If no  → framework rediscovers known disclosure-quality factor exposure.

## Forward-bet rule applied

After scoring, each name gets:
  - composite_score, severity_counts
  - is_truth_signal(row) — dual-gate emit rule
  - discovery_advantage tier (HIGH/MED/LOW/UNKNOWN)
  - Final emit = truth_signal AND DA tier in {HIGH, MED}

The 8 names will fall into 4 buckets:
  - **emit + DA HIGH/MED** → the framework's pick
  - emit + DA LOW         → crowded already (suppressed)
  - no_emit               → framework says don't short
  - DA UNKNOWN            → data gap (suppress)

We then compute pair P&L on the framework's emit subset vs. the
complementary subset, and compare to the full-8 basket baseline.

## Infrastructure status

| Artifact | Status |
|----------|--------|
| Cohort module `fresh_universe_cohort.py` | ✅ (8 members, correct CIKs) |
| Pre-2025-05-15 10-Ks fetched               | ✅ (all 8) |
| Planner prompts emitted                    | ✅ (`/tmp/planner_b1_fresh_universe_2025_05_15_*.txt`) |
| Backtest output dir                        | ✅ (`data/_backtest/2025_05_15/`) |
| Forward 12mo returns                       | ✅ (already on disk from v0 AIRO backtest) |

## To run the test

### Phase 1: 8 planner subagents (parallel)

Launch one Agent subagent per ticker, prompting it to follow the file at
`/tmp/planner_b1_fresh_universe_2025_05_15_{TK}.txt`. Each subagent will:
- Read its prompt + the historical 10-K from `data/{tk}/filings_2025_05_15/`
- Generate a plan.json at `data/_backtest/2025_05_15/{TK}.plan.json`
- Run time: ~10-30 min per subagent (each reads ~250K-500K input tokens)
- Cost: ~$0.50-$2 per planner × 8 = ~$4-$16 LLM cost total

### Phase 2: plan_executor

```bash
PYTHONPATH=. python3 -m verticals.public_co.plan_executor \
    --tickers LRHC KULR HDSN PESI CWCO CDNA ALMU KLIC \
    --data-dir verticals/public_co/data/_backtest/2025_05_15
```

### Phase 3: scoring

```bash
PYTHONPATH=. python3 -m verticals.public_co.deterministic_scorer \
    LRHC KULR HDSN PESI CWCO CDNA ALMU KLIC
```

### Phase 4: analysis script (to write)

Take scored matrix, compute `is_truth_signal` + DA filter, bucket
names, compute pair P&L per bucket against IWM and sector ETFs.
