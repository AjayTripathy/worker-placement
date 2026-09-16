#!/bin/bash
# Headless morning judgment (Tier 3): runs Claude Code non-interactively on PACK DAYS after the
# sentinel detects a print. Adjudicates against the pack, grades the frozen call, writes the
# recommended order parameters, notifies. CAVEATS (why staging stays semi-manual):
#  - claude.ai-connected MCP servers (the IBKR instruction tool) may be unavailable headless;
#    the run therefore WRITES desk/data/gauntlet_verdicts.json with exact order params instead
#    of staging — the user places from the notification, or the next interactive session stages.
#  - Cost: one headless run per pack day (~10-30 min of agent work).
cd /Users/ajay/exalted/signalos
FLAGS=desk/data/gauntlet_flags.json
[ -f "$FLAGS" ] || exit 0
python3 -c "import json,datetime,sys; d=json.load(open('$FLAGS')); sys.exit(0 if (d.get('date')==datetime.date.today().isoformat() and any(e['print_detected'] for e in d['events'])) else 1)" || exit 0
claude -p "$(cat ops/gauntlet_morning_prompt.md)" --permission-mode acceptEdits >> logs/gauntlet_headless.log 2>&1
