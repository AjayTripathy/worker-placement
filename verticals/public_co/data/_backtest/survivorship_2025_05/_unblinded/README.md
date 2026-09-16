# _unblinded/ — DO NOT READ DURING SCORING

This directory contains the **unblinded** test-set sources for the
2025-05-15 survivorship-bias backtest. Every file here contains
**post-cutoff outcomes**: realized forward returns and 2026-05-15
prices. Reading any of these files while scoring would contaminate
the experiment.

## Who reads what

| File | Read by |
|---|---|
| `_unblinded/combined_test_set.json` | `synthesize.py` only (joins forward_return for basket math) |
| `_unblinded/agent_manifest.json` | nothing — kept for provenance |
| `_unblinded/test_universe.json` | nothing — kept for provenance |
| `_unblinded/control_survivors.json` | nothing — kept for provenance |
| `_unblinded/sp600_removals.json` | nothing — kept for provenance |

The blinded views at the top of the backtest directory (same filenames)
are what scoring agents are pointed at. They are regenerated from this
directory by `build_blinded.py` and have post-cutoff fields stripped:
`forward_return`, `price_2026_05_15`, `date_removed`, `reason`, `date`.

## Rule

If you are scoring a pilot, you do not read this directory. If you are
running `synthesize.py` or another measurement script that needs realized
returns, you may read `combined_test_set.json` here. Nothing else should
touch these files.

The `verify_blinded.py` script at the top of the backtest directory
checks the blinded views and will fail if a post-cutoff field leaks
into them.
