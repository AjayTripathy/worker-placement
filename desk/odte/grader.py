"""Nightly 0DTE scoreboard: every template vs the T1 climatology benchmark, plus the live book
reconciled against its own ledger. Writes desk/data/odte/scoreboard.json and the UI copy; emails a
one-screen digest on days with sessions. Graduation rule lives in doctrine.GRADUATION_RULE.

Pooling rule: sessions are pooled per (template, hash) — a re-pre-registered template starts its
60-session clock again. The benchmark is always T1_MECH at the current hash.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import statistics as st

from desk.odte.doctrine import (SCOREBOARD, UI_BOARD, TEMPLATES, BENCHMARK_TEMPLATE, GRADUATION_SESSIONS, GRADUATION_RULE,
                                LIVE_TEMPLATE, template_hash)
from desk.odte.shadow import read_ledger
from desk.odte.rail import read_live


def _traded(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r.get("pnl_usd") is not None]


def stats(rows: list[dict]) -> dict:
    t = sorted(_traded(rows), key=lambda r: r["date"])
    pnl = [float(r["pnl_usd"]) for r in t]
    n = len(pnl)
    if n == 0:
        return {"sessions": len(rows), "traded": 0}
    cum = 0.0; peak = 0.0; mdd = 0.0
    for x in pnl:
        cum += x; peak = max(peak, cum); mdd = min(mdd, cum - peak)
    sd = st.pstdev(pnl) if n > 1 else 0.0
    return {"sessions": len(rows), "traded": n, "no_entry": len(rows) - n, "win_rate": round(sum(1 for x in pnl if x > 0) / n, 3),
            "mean_usd": round(st.mean(pnl), 2), "sd_usd": round(sd, 2), "total_usd": round(sum(pnl), 2), "max_dd_usd": round(mdd, 2),
            "sharpe_daily": round(st.mean(pnl) / sd, 3) if sd > 0 else None,
            "worst5": [{"date": r["date"], "pnl_usd": r["pnl_usd"], "reason": r.get("reason")} for r in sorted(t, key=lambda r: float(r["pnl_usd"]))[:5]],
            "stops": sum(1 for r in t if r.get("reason") == "CLOSE_STOP"), "settled": sum(1 for r in t if r.get("reason") == "SETTLED"),
            "time_exits": sum(1 for r in t if r.get("reason") == "CLOSE_TIME"),
            "delayed_data_sessions": sum(1 for r in t if r.get("data_type") == "delayed")}


def _session_return(row: dict) -> float | None:
    if row.get("pnl_usd") is not None:
        return float(row["pnl_usd"])
    if row.get("reason") == "NO_ENTRY" and row.get("skip_kind") == "strategy_cash":
        return 0.0
    return None


def vs_benchmark(rows: list[dict], bench: list[dict]) -> dict:
    """Common observed calendar, including deliberate cash days as zero return.

    Missing-data days (including unclassified legacy skips) are not zero returns.
    """
    b = {r["date"]: _session_return(r) for r in bench}
    pairs = [(r, _session_return(r)) for r in rows]
    pairs = [(r, value) for r, value in pairs if value is not None and b.get(r["date"]) is not None]
    d = [value - b[r["date"]] for r, value in pairs]
    out = {"paired": len(d), "cash_sessions": sum(r.get("reason") == "NO_ENTRY" for r, _ in pairs)}
    if len(d) < 2:
        return out
    sd = st.stdev(d)
    return {**out, "mean_diff_usd": round(st.mean(d), 2),
            "t_stat": round(st.mean(d) / (sd / math.sqrt(len(d))), 2) if sd > 0 else None}


def graduation(ts: dict, vb: dict, bench_stats: dict) -> dict:
    ok_n = vb.get("paired", 0) >= GRADUATION_SESSIONS
    ok_t = (vb.get("t_stat") or 0) >= 2.0
    ok_dd = ts.get("max_dd_usd") is not None and bench_stats.get("max_dd_usd") is not None and ts["max_dd_usd"] >= 2 * bench_stats["max_dd_usd"]
    return {"graduated": bool(ok_n and ok_t and ok_dd), "sessions_ok": ok_n, "tstat_ok": ok_t, "drawdown_ok": ok_dd, "rule": GRADUATION_RULE}


def build() -> dict:
    shadow = read_ledger(); live = read_live()
    out = {"built_utc": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "benchmark": BENCHMARK_TEMPLATE,
           "live_template": LIVE_TEMPLATE, "templates": {}, "live": {}}
    by = {}
    for r in shadow:
        by.setdefault((r["template"], r.get("hash")), []).append(r)
    bench_rows = by.get((BENCHMARK_TEMPLATE, template_hash(BENCHMARK_TEMPLATE)), [])
    bench_stats = stats(bench_rows)
    for name in TEMPLATES:
        h = template_hash(name); rows = by.get((name, h), [])
        s = stats(rows); vb = vs_benchmark(rows, bench_rows) if name != BENCHMARK_TEMPLATE else {}
        out["templates"][name] = {"hash": h, "claim": TEMPLATES[name]["claim"], **s, "vs_benchmark": vb,
                                  "graduation": graduation(s, vb, bench_stats) if name != BENCHMARK_TEMPLATE else {"benchmark": True}}
        stale = [k for k in by if k[0] == name and k[1] != h]
        if stale:
            out["templates"][name]["superseded_hashes"] = [{"hash": k[1], "sessions": len(by[k])} for k in stale]
    ls = stats(live)
    out["live"] = {**ls, "pnl_basis": "net_after_reported_commissions",
                   "pending_accounting": sum(r.get("accounting_status", "").startswith("pending") for r in live), "shadow_twin": stats(by.get((LIVE_TEMPLATE, template_hash(LIVE_TEMPLATE)), [])),
                   "slippage_vs_shadow_usd": _slippage(live, by.get((LIVE_TEMPLATE, template_hash(LIVE_TEMPLATE)), [])),
                   "execution": execution_stats(live, by.get((LIVE_TEMPLATE, template_hash(LIVE_TEMPLATE)), []))}
    from desk.odte import doctrine, text_overlay
    try:
        out["text_overlay"] = text_overlay.report(doctrine.DATA / "text_overlay", shadow_rows=shadow)
    except Exception as exc:
        out["text_overlay"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}", "live_enabled": False}
    SCOREBOARD.parent.mkdir(parents=True, exist_ok=True); SCOREBOARD.write_text(json.dumps(out, indent=1))
    try:
        UI_BOARD.write_text(json.dumps(out, indent=1))
    except Exception:
        pass
    return out


def _slippage(live: list[dict], twin: list[dict]) -> float | None:
    t = {r["date"]: float(r["pnl_usd"]) for r in _traded(twin)}
    d = [float(r["pnl_usd"]) - t[r["date"]] for r in _traded(live) if r["date"] in t]
    return round(st.mean(d), 2) if d else None


def execution_stats(live: list[dict], twin: list[dict]) -> dict:
    """The maker experiment's own numbers: how often the posted order filled, what it earned over
    the touch, and the live credit against the shadow twin's touch credit on the same date."""
    posted = [r for r in live if (r.get("maker") or {}).get("attempt")]
    filled = [r for r in posted if r.get("credit") is not None and r.get("reason") not in ("NO_FILL", "NO_ENTRY")]
    edges = [float(r["maker_edge"]) for r in filled if r.get("maker_edge") is not None]
    twin_credit = {r["date"]: float(r["credit"]) for r in twin if r.get("credit") is not None}
    vs_twin = [float(r["credit"]) - twin_credit[r["date"]] for r in filled if r["date"] in twin_credit]
    stood_down = [r for r in live if r.get("reason") == "NO_ENTRY" and ((r.get("policy") or {}).get("decision") or {}).get("arm")]
    by_arm = {}
    for r in live:
        a = ((r.get("policy") or {}).get("decision") or {}).get("arm")
        if a:
            by_arm.setdefault(a, {"sessions": 0, "takes": 0}); by_arm[a]["sessions"] += 1
            by_arm[a]["takes"] += int(((r.get("policy") or {}).get("decision") or {}).get("take", False))
    return {"maker_posts": len(posted), "maker_fills": len(filled), "fill_rate": round(len(filled) / len(posted), 3) if posted else None,
            "mean_maker_edge_vs_touch_usd": round(st.mean(edges) * 100, 2) if edges else None,
            "mean_live_credit_minus_twin_touch_usd": round(st.mean(vs_twin) * 100, 2) if vs_twin else None,
            "selector_stand_downs": len(stood_down), "followed_arms": by_arm}


def digest(out: dict) -> str:
    L = [f"0DTE scoreboard {out['built_utc'][:10]} — benchmark {out['benchmark']}"]
    for n, s in out["templates"].items():
        if s.get("traded"):
            L.append(f"  {n:12s} n={s['traded']:3d} win {s['win_rate']:.0%} mean ${s['mean_usd']:+.0f} total ${s['total_usd']:+.0f} "
                     f"maxDD ${s['max_dd_usd']:+.0f} stops {s['stops']} " + (f"vs T1 t={s['vs_benchmark'].get('t_stat')}" if s.get("vs_benchmark") else ""))
        else:
            L.append(f"  {n:12s} no traded sessions yet ({s.get('sessions', 0)} recorded)")
    lv = out["live"]
    L.append(f"  LIVE         n={lv.get('traded', 0)} total ${lv.get('total_usd', 0):+.0f} slippage vs shadow ${lv.get('slippage_vs_shadow_usd')}")
    text = out.get("text_overlay", {})
    if text.get("status") != "not_registered":
        L.append(f"  TEXT SHADOW  {text.get('status')} paired={text.get('paired_forecasts', 0)} "
                 f"failed={text.get('forecast_failures', 0)} missing={text.get('missing_forecasts_at_entry', 0)}; "
                 "pilot only, no live promotion")
        for group in text.get("calibration_by_submitter_agent", []):
            L.append(f"    {group['submitter']} / {group['agent']} / {group['requested_model']}: "
                     f"n={group['resolved']} stop Brier={group['stop']['brier']} severe Brier={group['severe']['brier']}")
    return "\n".join(L)


if __name__ == "__main__":
    o = build(); txt = digest(o); print(txt)
    today = dt.date.today().isoformat()
    if any(r.get("date") == today for r in read_ledger()):
        try:
            from desk.mailer import send_raw
            send_raw(f"0DTE scoreboard — {today}", txt)
        except Exception as e:
            print(f"[odte.grader] mail failed: {e}")
