"""score_log — stamp realized outcomes on matured social_thesis_log rows (SPEC.md §6/§7).

Core metric (structure-agnostic, directly tests the hypothesis): for each logged candidate, over
the paper holding window, compute REALIZED vol and compare to the ENTRY IV. The premium-seller
WINS when realized < implied (the IV was genuinely rich). This is the §7 kill check
("realized vol >= implied on the sold names -> IV wasn't rich -> kill"). Also records the realized
underlying move (for the directional arm) and aggregates ENGINE vs matched CONTROL.

Idempotent: rows already scored (by asof+ticker+action) are skipped. Uses yfinance daily closes.
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE / "outputs" / "social_thesis_log.jsonl"
SCORED = HERE / "outputs" / "social_thesis_scored.jsonl"
HOLD_DAYS = 21          # paper holding window (~one monthly expiry cycle)


def _read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def _realized_vol_and_move(ticker: str, start: date, end: date):
    """Annualized realized vol of daily log-returns + total move over [start, end], via yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        return None, None, "yfinance not installed"
    try:
        df = yf.download(ticker, start=start.isoformat(),
                         end=(end + timedelta(days=2)).isoformat(),
                         progress=False, auto_adjust=True)
        if df is None or len(df) < 3:
            return None, None, "insufficient bars"
        closes = [float(x) for x in df["Close"].dropna().values.tolist()]
        rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
        if not rets:
            return None, None, "no returns"
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / max(len(rets) - 1, 1)
        realized_vol = math.sqrt(var) * math.sqrt(252)            # annualized
        move = closes[-1] / closes[0] - 1
        return round(realized_vol, 3), round(move, 4), None
    except Exception as e:
        return None, None, str(e)[:80]


def run(asof_today: str | None = None) -> dict:
    today = date.fromisoformat(asof_today) if asof_today else None
    if today is None:
        # no Date.now in some envs; derive from the newest log row as a safe default
        rows = _read_jsonl(LOG)
        today = max((date.fromisoformat(r["asof"]) for r in rows), default=date(2026, 6, 25))
    rows = _read_jsonl(LOG)
    already = {(r["asof"], r["ticker"], r.get("action")) for r in _read_jsonl(SCORED)}

    matured, scored_now = 0, []
    for r in rows:
        key = (r["asof"], r["ticker"], r.get("action"))
        if key in already:
            continue
        entry = date.fromisoformat(r["asof"])
        exit_d = entry + timedelta(days=HOLD_DAYS)
        if exit_d > today:
            continue  # not matured yet
        matured += 1
        rv, move, err = _realized_vol_and_move(r["ticker"], entry, exit_d)
        iv = r.get("iv")
        out = {**{k: r.get(k) for k in ("asof", "ticker", "action", "iv", "iv_hv", "regime")},
               "exit_date": exit_d.isoformat(), "realized_vol": rv, "realized_move": move,
               "error": err}
        if rv is not None and iv:
            out["vol_seller_win"] = bool(rv < iv)
            out["iv_minus_rv"] = round(iv - rv, 3)        # >0 = seller had edge
        scored_now.append(out)

    if scored_now:
        with open(SCORED, "a") as f:
            for s in scored_now:
                f.write(json.dumps(s, default=str) + "\n")

    # aggregate over ALL scored (engine sell-vol vs control)
    allscored = _read_jsonl(SCORED)
    def agg(action_set):
        s = [x for x in allscored if x.get("action") in action_set and "vol_seller_win" in x]
        wins = sum(1 for x in s if x["vol_seller_win"])
        edge = (sum(x["iv_minus_rv"] for x in s) / len(s)) if s else None
        return {"n": len(s), "vol_seller_win_rate": round(wins / len(s), 3) if s else None,
                "avg_iv_minus_rv": round(edge, 3) if edge is not None else None}
    summary = {
        "today": today.isoformat(), "n_log_rows": len(rows),
        "matured_this_run": matured, "newly_scored": len(scored_now),
        "engine_sell_vol": agg({"SELL_VOL_CANDIDATE"}),
        "control": agg({"CONTROL"}),
        "directional": agg({"DIRECTIONAL_CANDIDATE"}),
    }
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    import sys
    run(sys.argv[1] if len(sys.argv) > 1 else None)
