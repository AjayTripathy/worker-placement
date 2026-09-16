"""attention_divergence_scanner — Stage 0b generator: ATTENTION anomalies across the research universe
(Wikipedia pageviews, the backtested instrument from the luxury-heat work).

Generalizes the BRBY method: per name, YoY change in quarterly Wikipedia attention, z-scored across the
universe. HONESTY (from the luxury backtest): attention correlates with fundamentals only MODESTLY
(~0.4-0.5 ex-outliers) and has NO print-trading edge (priced-in test was NULL) — so anomalies here are
diligence pointers, not signals. The demand-vs-drama disambiguation (search-up/news-down) needs the Google
Trends leg, which rate-limits — flagged as the MANUAL second step on any anomaly worth chasing.

Universe = research_ledger names (their wiki articles resolved via opensearch, cached).

  python3 verticals/generators/attention_divergence_scanner.py
Writes data/ATTENTION_ANOMALIES.json. READ-ONLY.
"""
from __future__ import annotations
import json, datetime, statistics, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CACHE = HERE / "data" / "wiki_title_cache.json"
OUT = HERE / "data" / "ATTENTION_ANOMALIES.json"
UA = {"User-Agent": "signalos-research/1.0 (private research)"}


def _get(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except Exception:
        return None


def _resolve_title(name: str, cache: dict) -> str | None:
    if name in cache:
        return cache[name]
    q = urllib.parse.urlencode({"action": "opensearch", "search": name, "limit": 1, "format": "json"})
    d = _get(f"https://en.wikipedia.org/w/api.php?{q}")
    title = (d[1][0].replace(" ", "_") if d and d[1] else None)
    cache[name] = title
    return title


def _monthly(title: str) -> dict:
    end = datetime.date.today().strftime("%Y%m%d") + "00"
    d = _get(f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
             f"all-access/user/{urllib.parse.quote(title)}/monthly/2023010100/{end}")
    return {f"{i['timestamp'][:4]}-{i['timestamp'][4:6]}": i["views"] for i in (d or {}).get("items", [])}


def scan() -> dict:
    led = json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text()).get("names", [])
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    today = datetime.date.today()
    rows = []
    for n in led:
        name = n.get("name") or n["ticker"]
        title = _resolve_title(name.split("(")[0].strip(), cache)
        if not title:
            continue
        m = _monthly(title)
        if len(m) < 15:
            continue
        q = {}
        for ym, v in m.items():
            key = f"{ym[:4]}Q{(int(ym[5:7]) - 1) // 3 + 1}"
            q.setdefault(key, []).append(v)
        qa = {k: statistics.mean(v) for k, v in q.items()}
        # drop the CURRENT in-progress quarter — 1-2 days of data compared as a full quarter fabricates -95% "declines"
        now_q = f"{today.year}Q{(today.month - 1) // 3 + 1}"
        qa.pop(now_q, None)
        ks = sorted(qa)
        if len(ks) < 6:
            continue
        cur, prior = ks[-1], f"{int(ks[-1][:4]) - 1}{ks[-1][4:]}"
        prev, prev_prior = ks[-2], f"{int(ks[-2][:4]) - 1}{ks[-2][4:]}"
        if prior not in qa or prev_prior not in qa or not qa[prior] or not qa[prev_prior]:
            continue
        yoy = (qa[cur] / qa[prior] - 1) * 100
        yoy_prev = (qa[prev] / qa[prev_prior] - 1) * 100
        rows.append({"ticker": n["ticker"], "name": name[:40], "wiki": title,
                     "yoy_pct": round(yoy, 1), "accel_pp": round(yoy - yoy_prev, 1),
                     "views_mo": round(qa[cur])})
    CACHE.write_text(json.dumps(cache))
    if len(rows) >= 6:
        mu = statistics.mean(r["accel_pp"] for r in rows)
        sd = statistics.pstdev(r["accel_pp"] for r in rows) or 1
        for r in rows:
            r["z"] = round((r["accel_pp"] - mu) / sd, 2)
    rows.sort(key=lambda r: -r["accel_pp"])
    return {"asof": today.isoformat(), "n_names": len(rows), "hot": rows[:10], "cold": rows[-8:][::-1],
            "note": "diligence pointers only (backtest: ~0.4-0.5 corr to fundamentals, NULL print edge); demand-vs-drama check (search-up/news-down) = manual Trends step on anything worth chasing"}


def main():
    res = scan()
    print(f"=== ATTENTION-DIVERGENCE SCANNER  {res['asof']}  ({res['n_names']} ledger names with wiki series) ===")
    print("  HOT (attention accelerating):")
    for r in res["hot"]:
        print(f"   {r['ticker']:<9} {r['name']:<38} yoy {r['yoy_pct']:+8.1f}%  accel {r['accel_pp']:+8.1f}pp  z{r.get('z', 0):+5.1f}")
    print("  COLD (attention rolling over):")
    for r in res["cold"]:
        print(f"   {r['ticker']:<9} {r['name']:<38} yoy {r['yoy_pct']:+8.1f}%  accel {r['accel_pp']:+8.1f}pp  z{r.get('z', 0):+5.1f}")
    print(f"  {res['note']}")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
