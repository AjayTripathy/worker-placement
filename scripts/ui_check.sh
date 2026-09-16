#!/bin/bash
# UI pre-change gate — run BEFORE and AFTER any edit to desk/ui/static/*. Exits non-zero on failure.
# (Two find()==-1 splices shipped garbage past </html> on 2026-07-02; this gate makes that impossible.)
set -e
cd "$(dirname "$0")/.."
python3 -m pytest tests/test_ui_integrity.py tests/test_sanitizer_and_health.py -q
echo "UI gate: PASS"
