# Resume token — small-cap honesty backtest

Last touched: 2026-05-25. Tier 1 controls complete. See
`TIER1_RESULTS.md` for the full report.

## Tier 1 — done

| test | result | verdict |
|---|---|---|
| B. Random-LONG placebo | framework at 99.91 pct, p=0.0009, z=+3.36 | strong: picks beat random within universe |
| A. Deterministic-screen ablation | det basket +15.4% vs framework +64.6%; +49 pp gap robust across 10 threshold variants | strong: LLM adds value beyond rule-based filters |
| C. Blinding-leak audit | 47% of pilots quote realized fwd return in narrative; severities appear NOT rigged (non-leakers have stronger composite-vs-return correlation) | mixed: cosmetic leak confirmed, severity contamination unlikely |

## Methodology hole — PATCHED 2026-05-25

The leak was: `combined_test_set.json`, `agent_manifest.json`,
`test_universe.json`, `control_survivors.json`, and `sp600_removals.json`
all contained post-cutoff fields (`forward_return`, `price_2026_05_15`,
`date_removed`, `reason`, `date`). `AGENT_INSTRUCTIONS.md` literally
told agents to read `forward_return` from the manifest.

Patch:
- Unblinded sources moved to `_unblinded/` with a README warning.
- Top-of-directory views regenerated as blinded by `build_blinded.py`
  (strips the five leak fields). Agents read these.
- `synthesize.py` updated to load measurement data from `_unblinded/`.
- `AGENT_INSTRUCTIONS.md` + `AGENT_PROMPT_TEMPLATE.md` updated: removed
  `forward_return` reference; added explicit prohibition on reading
  `_unblinded/`, `synthesis.json`, or other agents' pilot files; added
  summary content guidance ("must not cite forward returns").
- `verify_blinded.py` asserts no leak field appears in any agent-facing
  JSON. Run before each scoring session.

Residual leak: the `group` label ("delisted_or_distressed" vs
"control_survivor") is itself post-cutoff information by construction.
Keeping it preserves the experimental design as specified, but agents
still see which side of the split they're on. To remove this, Tier 2
should also build a `group`-stripped manifest.

The existing pilot scores were generated BEFORE this patch. Their
narratives are contaminated (47% leak rate, see TIER1_RESULTS.md) but
severity assignments appear unaffected. Headline +64.6% LOOSE_LONG
return is probably representative; any rerun should redo scoring under
the patched prompts.

## Next step — Tier 2

Boring-middle out-of-sample. The 66-name universe is a distressed
cohort with fat upside tails (universe mean +7%, max above +260%).
+64.6% is unusual relative to this universe (rejected by placebo)
but the universe itself is unusual relative to the broader S&P 600.
A LONG basket built from "boring middle" S&P 600 names won't have
the same fat-tail upside; testing whether the framework's LONG picks
still beat by ~30+ pp on a less-skewed universe is the next test.

Approximate scope: 30-50 non-distressed S&P 600 names with
drawdown_2025_05_15 in -10% to -25% range, score via blinded prompt,
measure basket return vs IJR same window.

## Existing infra to reuse

- `synthesize.py` — deterministic composite + tiering + survivorship-aware baselines + alpha math
- `agent_manifest.json` — per-ticker CIK + filing paths for all 65 scoreable names
- All 10-Ks + most pre-cutoff 10-Qs already cached in `verticals/public_co/data/<ticker>/filings_2025_05_15/`
- `verticals/public_co/m_sources/going_concern_detector.py`, `auditor_change_tracker.py` — already cutoff-aware deterministic m-sources
- `tier1_test_A_ablation.py`, `tier1_test_A_sensitivity.py`, `tier1_test_B_placebo.py` — Tier 1 scripts (regenerate results JSON)

## Do not

- Re-launch the 38 subagents — they're complete and committed
- Trust agent self-reported `composite` field; always use the deterministic recompute in synthesize.py
- Treat 66 universe as representative S&P 600 — it's a curated distressed cohort
- Hand any agent the un-blinded `combined_test_set.json` until the leak is patched
