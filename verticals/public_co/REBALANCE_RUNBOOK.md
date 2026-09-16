# J-Book Exposure — Rebalance Runbook

*How to refresh the framework's basket at each PB cycle. Designed for the FY28 PB release (~Feb-May 2027).*

---

## Pre-cycle: watch for the release

Run the watcher periodically — daily during the FY28 PB window (Feb-May 2027):

```bash
PYTHONPATH=. python3 -m verticals.public_co.scripts.watch_pb_release
```

Exit code 0 = FY28 content detected (proceed to ingest). Exit code 1 = no new content yet.

For automation, schedule with launchd / cron:
```bash
# Daily at 9:30 ET starting Feb 1, 2027
30 9 * * * cd /path/to/signalos && PYTHONPATH=. python3 -m verticals.public_co.scripts.watch_pb_release
```

Snapshot of last poll: `data/_jbook_exposure_cohort/PB_RELEASE_DETECTED.json`.

---

## When the FY28 PB drops

### Step 1: Save the snapshot (preserves what's currently live)

```bash
cp verticals/public_co/data/_jbook_exposure_cohort/forward_test_FY27_FY28.json \
   verticals/public_co/data/_jbook_exposure_cohort/forward_test_FY27_FY28.json.prior.json
cp verticals/public_co/data/_jbook_exposure_cohort_2024/matrix.json \
   verticals/public_co/data/_jbook_exposure_cohort_2024/matrix.PRIOR.json
```

### Step 2: Download the new PB PDFs

Place them in `~/Desktop/jbooks_fy28/`. Expected sources:
- comptroller.war.gov FY28 page (DARPA, MDA, SOCOM, OSD, Procurement)
- saffm.hq.af.mil FY28 page (AF + Space Force RDT&E vols)
- If sites are slow / blocked, use the Wayback Machine CDX API (we've done this before)

### Step 3: Run the rebalance pipeline (Phase 1 — automated)

```bash
PYTHONPATH=. python3 -m verticals.public_co.scripts.rebalance \
    --pb-date 2027-03-15 \
    --pdf-dir ~/Desktop/jbooks_fy28 \
    --phase all
```

This executes:
1. **ingest_pdfs** — parses each new PDF, adds programs to `data/_jbook_data/programs.json`
2. **extract_narrative** — pulls per-PE narrative text from source PDFs
3. **backfill_contractors** — LLM-extracts primary contractors from each narrative
4. **rebuild_index** — refreshes `by_entity.json`
5. **prep_subagents** — writes 32 per-ticker prompts to `/tmp/prompt_<TICKER>_jbook_2027.txt`

The pipeline STOPS after prep_subagents because subagents must be launched through Claude Code's Agent tool (not from CLI).

### Step 4: Launch the subagents (Claude Code session)

Open a Claude Code session and instruct it to launch all 32 cohort subagents in parallel batches:

> "Launch subagents for the FY28 rebalance. For each ticker in the cohort, read the prompt file at /tmp/prompt_<TICKER>_jbook_2027.txt and pass it to Agent({prompt: ..., run_in_background: true}). Batch 8 at a time to stay under Anthropic's parallel-task limit. The prompts are already constructed with cutoff_date=2027-03-15."

Wait for all 32 to complete (~45-90 min). Each subagent writes `<TICKER>.jbook.2027.{input,scores}.json` to `data/_local/`.

### Step 5: Phase 2 — aggregate + report + diff

```bash
# Aggregate into matrix
PYTHONPATH=. python3 -m verticals.public_co.jbook_exposure_aggregate

# Rebuild forward-test prescription with new vintage
PYTHONPATH=. python3 -m verticals.public_co.scripts.build_forward_test

# Diff against prior basket
PYTHONPATH=. python3 -m verticals.public_co.scripts.diff_baskets \
    --prior verticals/public_co/data/_jbook_exposure_cohort/forward_test_FY27_FY28.json.prior.json

# Generate full PDF report
PYTHONPATH=. python3 -m verticals.public_co.scripts.generate_forward_report
```

Outputs:
- `~/Desktop/JBOOK_FORWARD_LONG_REPORT.md` and `.pdf` (refreshed for FY28)
- `data/_jbook_exposure_cohort/REBALANCE_DIFF.md` (ADDED / REMOVED / MOVED lists)

### Step 6: Execute the rebalance trade

Read the REBALANCE_DIFF.md and execute:
- **ADDED to LONG**: open positions
- **REMOVED from LONG**: close positions
- **MOVED between buckets**: adjust per new bucket
- **Unchanged**: hold

Entry is T-60 days before the new FY28 PB. If the FY28 PB has already dropped, the canonical entry was 60 days ago — execute immediately (you're entering late by N days, where N = days since PB - 60).

---

## Expected timing for FY28 cycle

| Event | Estimated date |
|---|---|
| FY28 PB submission target (statutory) | First Mon of Feb 2027 |
| Realistic earliest (Biden-style) | Mar 2027 |
| Realistic latest (Trump 2.0 pattern) | Jun 2027 |
| **Best guess** | **Mar–May 2027** |
| Canonical T-60 entry window | Dec 2026 – Mar 2027 |
| Hold-to date | FY28 PB release |

---

## Failure-mode checks before going live

1. **Did the subagent runs all complete?** Check `data/_local/` — should have 32 pairs of `.jbook.2027.input.json` + `.jbook.2027.scores.json` files.
2. **Did the aggregator produce the matrix?** Check `data/_jbook_exposure_cohort/matrix.json` has all 32 entries with `"status": "OK"`.
3. **Did the diff show drastic moves?** Many ADDs and REMOVEs (>10 each) suggests vintage drift or a corpus issue — investigate before trading.
4. **Are the J-Book hit rates similar to prior cycle?** If most tickers come back with hit rates lower than prior, the new FY28 corpus may have parsing issues. Re-run ingest_pdfs with --verbose.

---

## Re-baselining (every 2-3 cycles)

The strategy's calibration constants (LONG_THRESHOLD=0.20, SHORT_THRESHOLD=0.50) should be re-validated periodically. Re-run the multi-cycle backtest (`backtest_pair_trade.py`, `backtest_compound_regime.py`) with the expanded dataset every 2-3 cycles to confirm the thresholds still optimize for cross-sectional alpha.

If a single cycle materially dilutes the alpha (e.g., FY28 pair return is < +10%), don't immediately adjust thresholds — wait for the next cycle to confirm whether it's a one-off or a regime shift.
