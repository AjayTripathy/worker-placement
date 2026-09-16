# Nikola backtest

Pipeline scripts moved to the shared harness at `verticals/public_co/`.

Run with:

    python3 -m verticals.public_co.runner nkla            # all phases
    python3 -m verticals.public_co.runner nkla --phase m  # M queries only

Config: `verticals/public_co/configs/nkla.py`
Outputs: `verticals/public_co/data/nkla/`

This directory keeps the published case study (`CASE_STUDY.md`) and the
pre-refactor evidence/findings JSON in `data/` for historical reference.
