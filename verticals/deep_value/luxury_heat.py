"""luxury_heat — brand ATTENTION index for the luxury book, normalized winner-vs-loser, backtestable.

Instrument: Wikipedia monthly pageviews per brand article (free, no auth, history to 2015) — the cleanest
long-history attention proxy we have. Heat(brand, quarter) = quarterly avg monthly pageviews; the SIGNAL is
YoY % change in heat (kills seasonality + article-level constants), z-scored vs the luxury cohort per quarter
(kills sector-wide attention waves — the LVMH-winner vs Kering-loser normalization).

Two uses:
  1. BACKTEST: does heat_yoy in quarter Q (or Q-1) track/lead the brand's printed comparable growth in Q?
     Ground truth series lives in data/luxury_comps_groundtruth.json (built from company releases).
  2. NOWCAST: the current quarter's heat z-score for a name about to print (BRBY Jul-17) — is its attention
     trajectory sitting with the winner cohort or the loser cohort?

  python3 verticals/deep_value/luxury_heat.py            # nowcast cross-section + (if ground truth present) backtest
READ-ONLY; no orders.
"""
from __future__ import annotations
import json, datetime, statistics, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
GT = HERE / "data" / "luxury_comps_groundtruth.json"
TRENDS = HERE / "data" / "luxury_trends_quarterly.json"   # Google Trends 5y weekly -> quarterly (Chrome-intercepted)
OUT = HERE / "data" / "luxury_heat.json"
UA = {"User-Agent": "signalos-research/1.0 (private research; contact: desk)"}

# brand -> the en.wikipedia article that carries its attention (checked titles)
BRANDS = {
    "Burberry": "Burberry",
    "Louis Vuitton": "Louis_Vuitton",
    "Dior": "Dior",
    "Hermès": "Hermès",
    "Gucci": "Gucci",
    "Saint Laurent": "Yves_Saint_Laurent_(brand)",
    "Coach": "Coach_New_York",
    "Miu Miu": "Miu_Miu",
    "Prada": "Prada",
    "Moncler": "Moncler",
}
WINNERS = {"Louis Vuitton", "Dior", "Hermès", "Coach", "Miu Miu"}   # printed-comp winners over the window
LOSERS = {"Gucci", "Saint Laurent"}                                  # printed-comp losers
START = "2022010100"


def _monthly(article: str) -> dict:
    """{'YYYY-MM': views} for the article, user traffic only (bots excluded)."""
    end = datetime.date.today().strftime("%Y%m%d") + "00"
    url = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
           f"all-access/user/{urllib.request.quote(article)}/monthly/{START}/{end}")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        items = json.load(r).get("items", [])
    return {f"{it['timestamp'][:4]}-{it['timestamp'][4:6]}": it["views"] for it in items}


def _quarterly(monthly: dict) -> dict:
    """{'2024Q1': avg monthly views} — partial current quarter uses the months available."""
    q = {}
    for ym, v in monthly.items():
        y, m = ym.split("-")
        key = f"{y}Q{(int(m) - 1) // 3 + 1}"
        q.setdefault(key, []).append(v)
    return {k: round(statistics.mean(v)) for k, v in sorted(q.items())}


def _yoy(q: dict) -> dict:
    out = {}
    for k, v in q.items():
        prev = f"{int(k[:4]) - 1}{k[4:]}"
        if prev in q and q[prev]:
            out[k] = round((v / q[prev] - 1) * 100, 1)
    return out


def build() -> dict:
    heat, quarters = {}, set()
    for brand, art in BRANDS.items():
        try:
            q = _quarterly(_monthly(art))
            heat[brand] = {"quarterly_views": q, "heat_yoy_pct": _yoy(q)}
            quarters |= set(heat[brand]["heat_yoy_pct"])
        except Exception as e:
            heat[brand] = {"error": f"{type(e).__name__}: {e}"}
    # cohort z-score per quarter (normalizes sector-wide attention waves)
    for qtr in sorted(quarters):
        vals = {b: h["heat_yoy_pct"][qtr] for b, h in heat.items()
                if "heat_yoy_pct" in h and qtr in h["heat_yoy_pct"]}
        if len(vals) < 4:
            continue
        mu, sd = statistics.mean(vals.values()), statistics.pstdev(vals.values()) or 1.0
        for b, v in vals.items():
            heat[b].setdefault("heat_z", {})[qtr] = round((v - mu) / sd, 2)
    return heat


def trends_heat() -> dict:
    """Instrument #2: Google Trends search interest (cross-normalized by Google across the 5 compared terms).
    Closer to purchase intent than Wikipedia (people search brands to shop); same YoY transform."""
    if not TRENDS.exists():
        return {}
    rows = json.loads(TRENDS.read_text())
    out = {}
    brands = sorted({b for q in rows.values() for b in q})
    for b in brands:
        q = {k: v[b] for k, v in rows.items() if b in v}
        out[b] = {"quarterly_interest": q, "heat_yoy_pct": _yoy(q)}
    return out


def backtest(heat: dict) -> dict:
    """Join heat_yoy / heat_z against the printed comp series; correlate same-quarter and heat LEADING by 1q."""
    if not GT.exists():
        return {"note": "no ground truth yet (data/luxury_comps_groundtruth.json) — nowcast only"}
    gt = json.loads(GT.read_text()).get("brands", {})
    th = trends_heat()
    pairs_same, pairs_lead, tpairs_same, tpairs_lead = [], [], [], []
    per_brand = {}
    for brand, g in gt.items():
        h = heat.get(brand, {})
        hy = h.get("heat_yoy_pct", {})
        ty = th.get(brand, {}).get("heat_yoy_pct", {})
        rows = []
        for pt in g.get("series", []):
            cq, gr = pt.get("cq"), pt.get("growth_pct")
            if gr is None:
                continue
            y, qn = int(cq[:4]), int(cq[-1])
            prevq = f"{y - 1}Q4" if qn == 1 else f"{y}Q{qn - 1}"
            if cq in hy:
                pairs_same.append((hy[cq], gr)); rows.append({"cq": cq, "heat_yoy": hy[cq], "trends_yoy": ty.get(cq), "growth": gr})
            if prevq in hy:
                pairs_lead.append((hy[prevq], gr))
            if cq in ty:
                tpairs_same.append((ty[cq], gr))
            if prevq in ty:
                tpairs_lead.append((ty[prevq], gr))
        per_brand[brand] = rows
    def _corr(pairs):
        if len(pairs) < 8:
            return None
        xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
        mx, my = statistics.mean(xs), statistics.mean(ys)
        num = sum((x - mx) * (y - my) for x, y in pairs)
        den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
        return round(num / den, 3) if den else None
    return {"wikipedia": {"n_same": len(pairs_same), "corr_same_quarter": _corr(pairs_same),
                          "n_lead": len(pairs_lead), "corr_heat_leads_1q": _corr(pairs_lead)},
            "google_trends": {"n_same": len(tpairs_same), "corr_same_quarter": _corr(tpairs_same),
                              "n_lead": len(tpairs_lead), "corr_heat_leads_1q": _corr(tpairs_lead)},
            "per_brand": per_brand}


def main():
    today = datetime.date.today()
    heat = build()
    bt = backtest(heat)
    cur_q = f"{today.year}Q{(today.month - 1) // 3 + 1}"
    prev_q = f"{today.year}Q{(today.month - 1) // 3}" if today.month > 3 else f"{today.year - 1}Q4"

    print(f"=== LUXURY BRAND-HEAT INDEX  {today}  (Wikipedia attention, YoY, cohort-z) ===")
    print(f"  {'brand':<14}{'cohort':<8}{prev_q + ' yoy':>10}{'z':>6}{cur_q + ' yoy':>10}{'z':>6}")
    for b in BRANDS:
        h = heat.get(b, {})
        if "error" in h:
            print(f"  {b:<14} ERROR {h['error'][:50]}"); continue
        co = "WIN" if b in WINNERS else "LOSE" if b in LOSERS else "?"
        py, pz = h["heat_yoy_pct"].get(prev_q), h.get("heat_z", {}).get(prev_q)
        cy, cz = h["heat_yoy_pct"].get(cur_q), h.get("heat_z", {}).get(cur_q)
        fmt = lambda x: ("–" if x is None else f"{x:+}")
        print(f"  {b:<14}{co:<8}{fmt(py):>10}{fmt(pz):>6}{fmt(cy):>10}{fmt(cz):>6}")
    th = trends_heat()
    if th:
        print(f"\n  GOOGLE TRENDS (instrument #2, cross-normalized search interest) YoY:")
        for b, d in th.items():
            hy = d["heat_yoy_pct"]
            last2 = sorted(hy)[-2:]
            print(f"   {b:<14}" + "  ".join(f"{k} {hy[k]:+.0f}%" for k in last2))
    if "wikipedia" in bt:
        w, g = bt["wikipedia"], bt["google_trends"]
        print(f"\n  BACKTEST vs printed comps:")
        print(f"   wikipedia    same-q corr {w['corr_same_quarter']} (n={w['n_same']}) | leads-1q {w['corr_heat_leads_1q']} (n={w['n_lead']})")
        print(f"   googletrends same-q corr {g['corr_same_quarter']} (n={g['n_same']}) | leads-1q {g['corr_heat_leads_1q']} (n={g['n_lead']})")
    else:
        print(f"\n  {bt['note']}")
    OUT.write_text(json.dumps({"asof": today.isoformat(), "heat": heat, "backtest": bt}, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
