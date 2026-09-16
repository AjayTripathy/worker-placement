# Lordstown backtest

Pipeline scripts moved to the shared harness at `verticals/public_co/`.

Run with:

    python3 -m verticals.public_co.runner ride            # all phases
    python3 -m verticals.public_co.runner ride --phase m  # M queries only

Config: `verticals/public_co/configs/ride.py`
Outputs: `verticals/public_co/data/ride/`

This directory keeps the published case study (`CASE_STUDY.md`) and the
pre-refactor evidence/findings JSON in `data/` for historical reference.
