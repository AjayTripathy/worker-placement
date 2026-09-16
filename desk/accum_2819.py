"""accum_2819 — Ebara Foods envelope #3 (clean-court minimum-starter, ratified 2026-08-21).

Court basis: Q1 4x NP verified EXACTLY (¥639M vs ¥163M; honest number is OP +20%); P/B 0.69,
equity ratio 71%, near-zero debt verified; dividend 1.93% (court's 3.3% refuted — carry is NOT
the reason to own it). Seasonal: Jan-Mar is an operating LOSS every year; Oct-Dec carries.
All findings risk/timing-class -> starter default. Sizing ~0.3% ($3.3k): 200 sh at ~¥2,597.
"""
from desk.jp_accum_core import build

CFG = dict(symbol="2819", ticker="2819.T", target_sh=200, ceiling=2700, pause_below=2390,
           state_file="accum_2819_state.json", client_id=67, max_lots=1)
run, plan_chunk = build(CFG)
