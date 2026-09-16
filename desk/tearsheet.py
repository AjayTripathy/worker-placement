"""tearsheet — per-sleeve realized trade statistics, with an N-gate that SUPPRESSES
distributional metrics (Sharpe/Sortino/alpha/beta) until a sleeve has enough closed
trades to make them mean anything.

Born 2026-07-09. The MFP trade's 'Sharpe ~23 / beta -2.56' were n=3 artifacts. The rule:
robust small-N stats (hit-rate, profit factor, avg win/loss, MAE/MFE, return-to-heat) are
shown always; ratio metrics that need a return distribution are shown ONLY at N >= MIN_DIST_N,
otherwise a 'suppressed — need N' placeholder. Never show a spurious 23-Sharpe again.

Reads desk/data/closed_trades.json (each trade carries ret_pct, realized_usd, mae_pct, mfe_pct).

    from desk.tearsheet import sleeve_stats, MIN_DIST_N
"""
from __future__ import annotations

from statistics import mean, pstdev

MIN_DIST_N = 20    # Sharpe/Sortino/alpha/beta require at least this many closed trades
THIN_N = 5         # below this, even the robust stats are flagged 'thin — directional only'


def sleeve_stats(trades: list[dict]) -> dict | None:
    """Realized stats for a list of closed-trade dicts. None if empty."""
    n = len(trades)
    if not n:
        return None
    rets = [t["ret_pct"] for t in trades]
    usd = [t.get("realized_usd", 0) or 0 for t in trades]
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    gains = sum(x for x in usd if x > 0)
    losspool = -sum(x for x in usd if x < 0)
    maes = [t["mae_pct"] for t in trades if t.get("mae_pct") is not None]
    mfes = [t["mfe_pct"] for t in trades if t.get("mfe_pct") is not None]
    e2h = [t["ret_pct"] / abs(t["mae_pct"]) for t in trades if t.get("mae_pct")]

    dist_ok = n >= MIN_DIST_N
    # trade-level Sharpe = mean/stdev of per-trade returns — only computed once N clears the gate
    sharpe = (mean(rets) / pstdev(rets)) if (dist_ok and pstdev(rets) > 0) else None

    return {
        "n": n,
        "thin": n < THIN_N,
        "hit": len(wins) / n,
        "avg_win": mean(wins) if wins else 0.0,
        "avg_loss": mean(losses) if losses else 0.0,
        "winloss": (mean(wins) / abs(mean(losses))) if (wins and losses) else None,
        "pf": (gains / losspool) if losspool > 0 else None,   # None = no losses yet (infinite)
        "avg_ret": mean(rets),
        "total_usd": sum(usd),
        "avg_mae": mean(maes) if maes else None,
        "avg_mfe": mean(mfes) if mfes else None,
        "avg_e2h": mean(e2h) if e2h else None,
        "dist_ok": dist_ok,
        "sharpe": sharpe,   # None until N >= MIN_DIST_N
    }
