"""social_lift_backtest — builds the PRE-REGISTERED social-lift predictor panel from the daily virality
logs, reports readiness, and computes the rank-IC once earnings targets are joined. See
SOCIAL_LIFT_BACKTEST_SPEC.md (locked design — do not retune predictor/target after seeing results).

Predictor: social_score(ticker, Q) = quarterly mean of daily [Σ views of that ticker's mapped, confirmed
trending brand-hashtags], z-scored within quarter. Target (joined later): revenue surprise vs pre-print
consensus (+ post-print returns). H2 (load-bearing): brand-owner IC > ODM IC.
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = [HERE / "beauty_velocity_log.jsonl"]
ODM_TICKERS = {"241710.KQ", "192820.KS", "161890.KS"}  # the rest of the mapped names = brand-owner cohort
MIN_DAYS_PER_Q = 25          # a (ticker,Q) needs this many logged days to count (point-in-time coverage)
MIN_N_PER_COHORT = 30        # locked power floor before any go/no-go (see spec)


def _vnum(s):
    m = {"K": 1e3, "M": 1e6, "B": 1e9}
    try:
        return float(str(s)[:-1]) * m[str(s)[-1]] if s and str(s)[-1] in m else float(s or 0)
    except Exception:
        return 0.0


def _quarter(asof: str) -> str:
    y, mth = int(asof[:4]), int(asof[5:7])
    return f"{y}-Q{(mth - 1) // 3 + 1}"


def build_panel():
    """(ticker, quarter) -> {sum_views_by_day, days, brands, cohort}."""
    daily = defaultdict(lambda: defaultdict(float))   # (tkr,Q) -> {date: sum_views}
    brands = defaultdict(set)
    for lp in LOGS:
        if not lp.exists():
            continue
        for line in lp.read_text().splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            asof = rec.get("asof")
            if not asof:
                continue
            q = _quarter(asof)
            for m in rec.get("mapped", []):
                tk = m.get("ticker")
                if not tk:
                    continue
                daily[(tk, q)][asof] += _vnum(m.get("views"))
                brands[(tk, q)].add(m.get("tag"))
    panel = {}
    for (tk, q), bydate in daily.items():
        days = len(bydate)
        panel[(tk, q)] = {"ticker": tk, "quarter": q,
                          "social_score": round(sum(bydate.values()) / days, 1) if days else 0.0,
                          "days": days, "n_brands": len(brands[(tk, q)]),
                          "cohort": "ODM" if tk in ODM_TICKERS else "brand_owner"}
    return panel


def _spearman(xs, ys):
    n = len(xs)
    if n < 4:
        return None
    def rank(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        for pos, i in enumerate(order):
            r[i] = pos
        return r
    rx, ry = rank(xs), rank(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    den = (sum((rx[i] - mx) ** 2 for i in range(n)) * sum((ry[i] - my) ** 2 for i in range(n))) ** 0.5
    return round(num / den, 3) if den else None


def compute_ic(panel, targets):
    """targets: {(ticker,quarter): revenue_surprise}. Z-scores social_score within quarter, then rank-IC
    vs surprise, per cohort + the H2 contrast. Returns {} until targets exist."""
    # z-score within quarter
    byq = defaultdict(list)
    for k, v in panel.items():
        if v["days"] >= MIN_DAYS_PER_Q and k in targets:
            byq[v["quarter"]].append((k, v))
    pairs = []  # (cohort, z_social, surprise)
    for q, items in byq.items():
        ss = [v["social_score"] for _, v in items]
        mu = sum(ss) / len(ss); sd = (sum((s - mu) ** 2 for s in ss) / len(ss)) ** 0.5 or 1.0
        for (k, v), s in zip(items, ss):
            pairs.append((v["cohort"], (s - mu) / sd, targets[k]))
    out = {}
    for coh in ("brand_owner", "ODM", "ALL"):
        sub = [(z, t) for c, z, t in pairs if coh == "ALL" or c == coh]
        out[coh] = {"n": len(sub), "rank_ic": _spearman([z for z, _ in sub], [t for _, t in sub]) if len(sub) >= 4 else None}
    if out["brand_owner"]["rank_ic"] is not None and out["ODM"]["rank_ic"] is not None:
        out["H2_contrast(bo-odm)"] = round(out["brand_owner"]["rank_ic"] - out["ODM"]["rank_ic"], 3)
    return out


def report():
    panel = build_panel()
    # save the accumulating panel snapshot
    snap = HERE / "social_lift_panel.json"
    snap.write_text(json.dumps([panel[k] for k in sorted(panel)], indent=2, default=str))
    qualifying = {k: v for k, v in panel.items() if v["days"] >= MIN_DAYS_PER_Q}
    bo = sum(1 for v in qualifying.values() if v["cohort"] == "brand_owner")
    odm = sum(1 for v in qualifying.values() if v["cohort"] == "ODM")
    days_total = len({v["quarter"] + str(i) for i, v in enumerate(panel.values())}) if panel else 0
    all_days = set()
    for lp in LOGS:
        if lp.exists():
            for line in lp.read_text().splitlines():
                if line.strip():
                    try: all_days.add(json.loads(line)["asof"])
                    except Exception: pass

    print("=== SOCIAL-LIFT BACKTEST — readiness (pre-registered; see SOCIAL_LIFT_BACKTEST_SPEC.md) ===")
    print(f"  virality-log coverage: {len(all_days)} distinct days  ({min(all_days) if all_days else '—'} -> {max(all_days) if all_days else '—'})")
    print(f"  predictor panel: {len(panel)} (ticker,quarter) cells; {len(qualifying)} with >= {MIN_DAYS_PER_Q} days")
    print(f"     qualifying by cohort:  brand_owner={bo}  ODM={odm}  (need >= {MIN_N_PER_COHORT} each for go/no-go)")
    # show the current (under-construction) panel
    for v in sorted(panel.values(), key=lambda x: (-x["days"], x["ticker"]))[:12]:
        print(f"     {v['ticker']:<11} {v['quarter']}  score~{v['social_score']:>12,.0f}v/day  "
              f"days={v['days']:<3} brands={v['n_brands']} [{v['cohort']}]")

    # targets not yet available (no completed prints joined while only this-quarter history exists)
    ic = compute_ic(panel, targets={})
    print("\n  TARGETS joined: 0 (no earnings surprises wired yet).")
    enough = bo >= MIN_N_PER_COHORT and odm >= MIN_N_PER_COHORT
    print(f"  STATUS: {'READY — wire targets and run compute_ic' if enough else 'ACCUMULATING — underpowered, do NOT interpret'}")
    print("  Timeline (per spec): first full predictor quarter = Q3-2026 (Jul-Sep) -> Q3 prints Oct-Nov 2026 "
          "= first joinable cohort (N~10-15, directional peek only). Powered (N>=30/cohort) ~mid-2027.")
    print("  NEXT: keep the daily virality cron running; after Q3 prints, join {revenue surprise} per "
          "(ticker,quarter) via IBKR/agents and re-run. Panel snapshot -> social_lift_panel.json")
    return panel, ic


if __name__ == "__main__":
    report()
