"""accum_4625 — Atomix envelope #4 (clean-court minimum-starter, ratified 2026-08-21).

Court basis: road-marking safety paint (municipal mandate moat), ~75.8% net cash claimed, P/B
0.37 live — CHEAPER than the foreign court knew. Open item carried into the gates: Jan-Mar NP
(¥676M) exceeded OP (¥206M) — identify the non-operating gain before trusting FCF claims; that is
an ADD-gate question, not a starter-blocker, under the ratified default.
THIN ($27k/day): 1 lot/day at ~2% participation — a ~5-session build to 500 sh (~$2.5k, 0.25%).
The build-time is stated because un-stated build times were the liquidity-eviction lesson.
"""
from desk.jp_accum_core import build

CFG = dict(symbol="4625", ticker="4625.T", target_sh=500, ceiling=815, pause_below=720,
           state_file="accum_4625_state.json", client_id=68, max_lots=1)
run, plan_chunk = build(CFG)
