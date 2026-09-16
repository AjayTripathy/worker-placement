# Social-Thesis Engine — daily scheduling

The engine is READ-ONLY (surfaces + paper-tracks candidates; never places orders). `daily.py`
runs the full cycle: triage → forward scorer → diligence pass on any queued candidates.

## Durable 8-week run (recommended) — OS crontab

The in-session CronCreate job (id d9dbdc32) is session-bound and auto-expires in 7 days, so for the
full forward paper track use a real OS cron entry. Run `crontab -e` and add (weekdays, 1:13pm —
adjust to just after the 4pm-ET close in YOUR timezone):

```
13 13 * * 1-5 cd /Users/ajay/exalted/signalos/verticals/social_thesis_engine && /usr/bin/python3 daily.py 10 >> outputs/cron.log 2>&1
```

Notes:
- **TWS must be running** at fire time for the IV-richness step; without it, the IV column logs as
  UNAVAILABLE (social + conditioning still log, so the row is partial but not lost).
- The **diligence pass** auto-runs only if the `claude` CLI is on PATH (it shells `claude -p
  --agent signalos-quant-analyst` per queued candidate). If absent, candidates sit in
  `outputs/needs_diligence.json` for manual/orchestrator processing.
- Output accrues to `outputs/social_thesis_log.jsonl` (candidates + matched controls),
  `outputs/social_thesis_scored.jsonl` (realized-vol-vs-implied once rows mature at 21d), and
  `outputs/cron.log`.

## Evaluate at ≥ 8 weeks (SPEC §7)

```
python3 score_log.py     # vol_seller_win_rate + avg(IV − realized vol) for engine vs CONTROL
```
SCALE only if the SELL_VOL arm shows positive avg(IV−RV), beats the matched CONTROL, and the
squeeze-fuel veto recorded zero blow-throughs. Else KILL (negative result still encodes the
microstructure: does social attention predict overpriced vol?).
