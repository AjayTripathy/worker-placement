"""accum_7239 — Tachi-S envelope #2 (clean-court minimum-starter, ratified 2026-08-21).

Court basis: imported Antigravity benches + desk verification 2026-08-20 — the one TSE PRIME name
at scale, where the reform mechanism actually applies; live yield 4.94% verified BETTER than
claimed. All findings risk/timing-class -> starter default. Pre-flight still owed before any ADD
beyond this starter: AAGS CB-allottee verify; Nissan-chain concentration vs held 7222.
Sizing 0.5% ($5k): 300 sh at ~¥2,329. Deep liquidity ($1.2M/day) — chunks are politeness here.
"""
from desk.jp_accum_core import build

CFG = dict(symbol="7239", ticker="7239.T", target_sh=300, ceiling=2420, pause_below=2140,
           state_file="accum_7239_state.json", client_id=66)
run, plan_chunk = build(CFG)
