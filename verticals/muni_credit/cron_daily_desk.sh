#!/bin/bash
# Daily muni desk run (OS-level, durable) — staging + monitoring only, NEVER places orders.
# Runs the data pipeline regardless of whether Claude is open. The agent-reasoning report still
# happens via the Claude session cron when it's running; this guarantees the scripts execute.
cd /Users/ajay/exalted/signalos/verticals/muni_credit || exit 1
PY=/usr/bin/python3
LOG="outputs/cron_daily_$(date +%Y%m%d).log"
{
  echo "=== DAILY DESK RUN $(date) ==="
  echo "-- remark_buylist (needs TWS) --"
  $PY -u remark_buylist.py 2>&1 || echo "remark_buylist FAILED (TWS down?) — continuing"
  echo "-- cd_monitor --"
  $PY -u cd_monitor.py 2>&1 || echo "cd_monitor FAILED — continuing"
  echo "-- refresh CDE interim certifications (catch AB-1200 downgrades; was a cycle stale -> missed Antioch) --"
  $PY -c "import school_go_issuer_credit as SC; print('cert-refresh:', SC.refresh_certifications())" 2>&1 || echo "cert-refresh FAILED — continuing"
  echo "-- bond_scanner (append want-list) --"
  $PY -u bond_scanner.py --append-wantlist --max-new 80 2>&1 || echo "bond_scanner FAILED — continuing"
  echo "-- underwrite new scanner finds (fire x EQ x AI x credit; cap 60/day so the queue drains) --"
  NEW=$($PY -c "import json;wl={r['cusip'] for r in json.load(open('outputs/SCANNER_STANDING_WANTLIST.json'))};uw={r['cusip']:r for r in json.load(open('outputs/underwriting_candidates.json'))};print(' '.join(sorted(c for c in wl if c not in uw or uw[c].get('fire_score') is None)[:60]))" 2>/dev/null)
  if [ -n "$NEW" ]; then $PY -u underwrite_candidates.py --cheap $NEW 2>&1 | tail -1 || echo "underwrite FAILED — continuing"
  else echo "no un-screened names (queue empty)"; fi
  echo "-- refresh current AV/coverage for DDs flagged UNVERIFIABLE (serial/throttled; skips VERIFIED) --"
  echo "   (re-pulls latest CDD annual report -> current-FY AV + delinquency via cdd_financials; resolves"
  echo "    EMMA-403 stale flags. Runs BEFORE the master so it merges in same-night. Quarterly: run"
  echo "    'refresh_current_state.py --fresh' to catch newly-posted annual filings)"
  $PY -u refresh_current_state.py 2>&1 | tail -25 || echo "refresh_current_state FAILED — continuing"
  echo "-- build_diligence_master (consolidate all screens + merge verified current-state AV/coverage) --"
  $PY -u build_diligence_master.py 2>&1 || echo "build_diligence_master FAILED — continuing"
  echo "-- scrape EMMA New Issue Calendar (browser) -> refresh data/ca_newissue_calendar.csv --"
  $PY -u scrape_emma_newissues.py 2>&1 | tail -2 || echo "EMMA new-issue scrape FAILED -- continuing"
  echo "-- new-issue watch (alert on upcoming CA deals that fit the book; drop broker calendar at data/ca_newissue_calendar.csv) --"
  $PY -u new_issue_watch.py 2>&1 | tail -3 || echo "new_issue_watch FAILED -- continuing"
  echo "=== DONE $(date) ==="
} >> "$LOG" 2>&1
