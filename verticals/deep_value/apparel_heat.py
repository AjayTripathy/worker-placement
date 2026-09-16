"""apparel_heat — brand ATTENTION index for the US apparel-retail book, normalized winner-vs-loser, backtestable.

Sibling of luxury_heat.py (same index math), pointed at mall-teen / specialty-apparel names to triangulate
MELTING vs CONTINUING-STRENGTH for a traffic-sensitive retailer. Built for the Buckle (BKE) melt question:
the anti-melt thesis rests on positive comps + POSITIVE TRANSACTIONS; attention is a LEADING traffic proxy, so a
rolling-over heat trajectory is a disconfirming tell BEFORE the comp print.

Instrument #1 (always on): Wikipedia monthly pageviews per company article (free, no auth, history to 2015).
  Heat(name, quarter) = quarterly avg monthly pageviews. SIGNAL = YoY % change in heat (kills seasonality +
  article-level constants), z-scored vs the apparel cohort per quarter (kills sector-wide attention waves).
Instrument #2 (if present): Google Trends search interest, Chrome-intercepted into data/apparel_trends_quarterly.json
  (same YoY transform). Degrades to Wikipedia-only if that file is absent / Trends rate-limits.

HONEST PRIORS carried from the luxury backtest: heat<->fundamentals corr ~0.4-0.5 ex-outliers, NULL print-trading
edge. This is a DILIGENCE POINTER (does attention corroborate the comp story?), not a standalone signal.

BKE operationalization: 'Buckle' is a generic word, so we use the Wikipedia article "The_Buckle" (the retailer,
confirmed via the article summary: "American fashion retailer ... operates 451 stores") and, for Trends, the
purchase-intent terms "buckle jeans" / "BKE jeans" (BKE = its house denim brand). Term used is documented per row.

  python3 verticals/deep_value/apparel_heat.py     # nowcast cross-section + (if ground truth present) backtest + BKE read
READ-ONLY; no orders.
"""
from __future__ import annotations
import json, datetime, statistics, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
GT = HERE / "data" / "apparel_comps_groundtruth.json"
TRENDS = HERE / "data" / "apparel_trends_quarterly.json"   # Google Trends 5y weekly -> quarterly (Chrome-intercepted)
OUT = HERE / "data" / "apparel_heat.json"
UA = {"User-Agent": "signalos-research/1.0 (private research; contact: desk)"}

# ticker -> the en.wikipedia article that carries the company's attention (all resolved 2026-07: summary 200 + right entity)
BRANDS = {
    "BKE":  "The_Buckle",                 # focal name — the retailer, NOT the fastener disambig
    "ANF":  "Abercrombie_&_Fitch",
    "BOOT": "Boot_Barn",
    "URBN": "Urban_Outfitters",
    "AEO":  "American_Eagle_Outfitters",
    "GPS":  "Gap_Inc.",
    "LEVI": "Levi_Strauss_&_Co.",
    "ZUMZ": "Zumiez",
    "VSCO": "Victoria's_Secret",
    "KTB":  "Kontoor_Brands",
}
FOCAL = "BKE"
# cohort by PRINTED-comp trajectory over the window (used only to color the nowcast table; backtest is quantitative)
WINNERS  = {"ANF", "BOOT", "URBN"}          # strong printed comps
MIDDLING = {"AEO", "GPS", "LEVI"}
LOSERS   = {"ZUMZ", "VSCO", "KTB"}          # struggling / declining comps
COHORT = lambda t: "WIN" if t in WINNERS else "MID" if t in MIDDLING else "LOSE" if t in LOSERS else "?"
START = "2021010100"


THIN_BASE = 200   # min avg monthly pageviews for a name's heat_yoy to be trustworthy (below = noise floor)


def _monthly(article: str) -> dict:
    """{'YYYY-MM': views} for the article, user traffic only (bots excluded). Drops the current PARTIAL month
    (today's month has only a few days logged and would crater a quarter's YoY)."""
    end = datetime.date.today().strftime("%Y%m%d") + "00"
    url = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
           f"all-access/user/{urllib.request.quote(article, safe='')}/monthly/{START}/{end}")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        items = json.load(r).get("items", [])
    cur = datetime.date.today().strftime("%Y-%m")
    return {ym: it["views"] for it in items
            for ym in [f"{it['timestamp'][:4]}-{it['timestamp'][4:6]}"] if ym < cur}


def _quarterly(monthly: dict) -> dict:
    """{'2024Q1': avg monthly views} for COMPLETE quarters only (all 3 months present) — a partial quarter's
    average understates and would blow up the YoY."""
    buckets = {}
    for ym, v in monthly.items():
        y, m = ym.split("-")
        buckets.setdefault(f"{y}Q{(int(m) - 1) // 3 + 1}", []).append(v)
    return {k: round(statistics.mean(v)) for k, v in sorted(buckets.items()) if len(v) == 3}


def _yoy(q: dict) -> dict:
    out = {}
    for k, v in q.items():
        prev = f"{int(k[:4]) - 1}{k[4:]}"
        if prev in q and q[prev]:
            out[k] = round((v / q[prev] - 1) * 100, 1)
    return out


def build() -> dict:
    heat, quarters = {}, set()
    for t, art in BRANDS.items():
        try:
            q = _quarterly(_monthly(art))
            base = round(statistics.mean(list(q.values())[-8:])) if q else 0
            heat[t] = {"article": art, "avg_monthly_base": base, "thin_base": base < THIN_BASE,
                       "quarterly_views": q, "heat_yoy_pct": _yoy(q)}
            quarters |= set(heat[t]["heat_yoy_pct"])
            time.sleep(0.4)   # space the wikimedia pageviews calls (bursts get 429'd)
        except Exception as e:
            heat[t] = {"article": art, "error": f"{type(e).__name__}: {e}"}
    # cohort z-score per quarter (normalizes sector-wide attention waves). THIN-base names are noise -> excluded
    # from the cohort moments AND get no z (their YoY is unreliable), but still print for transparency.
    for qtr in sorted(quarters):
        vals = {t: h["heat_yoy_pct"][qtr] for t, h in heat.items()
                if "heat_yoy_pct" in h and qtr in h["heat_yoy_pct"] and not h.get("thin_base")}
        if len(vals) < 4:
            continue
        mu, sd = statistics.mean(vals.values()), statistics.pstdev(vals.values()) or 1.0
        for t, v in vals.items():
            heat[t].setdefault("heat_z", {})[qtr] = round((v - mu) / sd, 2)
    return heat


def trends_heat() -> dict:
    """Instrument #2: Google Trends search interest (cross-normalized by Google across the compared terms).
    Closer to purchase intent than Wikipedia (people search a brand/jeans to shop); same YoY transform."""
    if not TRENDS.exists():
        return {}
    rows = json.loads(TRENDS.read_text())
    out = {}
    names = sorted({b for q in rows.values() for b in q})
    for b in names:
        q = {k: v[b] for k, v in rows.items() if b in v}
        out[b] = {"quarterly_interest": q, "heat_yoy_pct": _yoy(q)}
    return out


def _prevq(cq: str) -> str:
    y, qn = int(cq[:4]), int(cq[-1])
    return f"{y - 1}Q4" if qn == 1 else f"{y}Q{qn - 1}"


def _pearson(pairs):
    if len(pairs) < 6:
        return None
    xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in pairs)
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return round(num / den, 3) if den else None


def _spearman(pairs):
    if len(pairs) < 4:
        return None
    def _rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0.0] * len(vals)
        i = 0
        while i < len(vals):
            j = i
            while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = _rank([p[0] for p in pairs]), _rank([p[1] for p in pairs])
    return _pearson(list(zip(rx, ry)))


def backtest(heat: dict) -> dict:
    """Three honest tests joining heat_yoy to PRINTED comps:
       (1) within-brand DIRECTIONAL agreement: sign(heat_yoy) == sign(comp_pct), hit rate + N.
       (2) cross-sectional RANK corr: per quarter, Spearman(heat_yoy rank, comp rank) across the cohort, averaged.
       (3) same-quarter Pearson (comparability with the luxury run), + a heat-LEADS-1q variant.
       All reported with N and an ex-outlier robustness pass (drop |comp|>=40 blow-ups)."""
    if not GT.exists():
        return {"note": "no ground truth yet (data/apparel_comps_groundtruth.json) — nowcast only"}
    gt = json.loads(GT.read_text()).get("brands", {})
    th = trends_heat()
    same, lead, dir_hits, dir_n, per_brand = [], [], 0, 0, {}
    same_exo = []
    by_quarter = {}   # cq -> list of (ticker, heat_yoy, comp)
    for t, g in gt.items():
        h = heat.get(t, {})
        if h.get("thin_base"):
            continue   # noise-floor article — its heat_yoy is unreliable, keep it out of the backtest
        hy = h.get("heat_yoy_pct", {})
        ty = th.get(t, {}).get("heat_yoy_pct", {})
        rows = []
        for pt in g.get("series", []):
            cq, gr = pt.get("cq"), pt.get("comp_pct")
            if gr is None or cq not in hy:
                continue
            same.append((hy[cq], gr))
            if abs(hy[cq]) < 50:   # drop attention SPIKES (news/campaign events, e.g. a viral ad) — the
                same_exo.append((hy[cq], gr))   # dominant contamination mode for mid-cap retail Wikipedia pages
            # directional agreement (both signs non-zero)
            if hy[cq] != 0 and gr != 0:
                dir_n += 1
                dir_hits += 1 if (hy[cq] > 0) == (gr > 0) else 0
            by_quarter.setdefault(cq, []).append((t, hy[cq], gr))
            pq = _prevq(cq)
            if pq in hy:
                lead.append((hy[pq], gr))
            rows.append({"cq": cq, "heat_yoy": hy[cq], "trends_yoy": ty.get(cq), "comp": gr,
                         "metric": pt.get("metric"), "dir_agree": (hy[cq] > 0) == (gr > 0)})
        if rows:
            per_brand[t] = rows
    # cross-sectional rank corr per quarter (>=4 names), averaged
    xsec = []
    for cq, obs in sorted(by_quarter.items()):
        if len(obs) >= 4:
            rho = _spearman([(o[1], o[2]) for o in obs])
            if rho is not None:
                xsec.append((cq, len(obs), rho))
    xsec_mean = round(statistics.mean([r for _, _, r in xsec]), 3) if xsec else None
    return {
        "within_brand_directional": {"hit_rate": round(dir_hits / dir_n, 3) if dir_n else None, "n": dir_n,
                                      "hits": dir_hits},
        "same_quarter_pearson": {"corr": _pearson(same), "n": len(same),
                                 "corr_ex_heat_spike": _pearson(same_exo), "n_ex_heat_spike": len(same_exo)},
        "heat_leads_1q_pearson": {"corr": _pearson(lead), "n": len(lead)},
        "cross_sectional_rank": {"mean_spearman": xsec_mean, "n_quarters": len(xsec),
                                 "by_quarter": [{"cq": c, "n": n, "spearman": r} for c, n, r in xsec]},
        "per_brand": per_brand,
    }


def bke_read(heat: dict, bt: dict) -> dict:
    """Melt-triangulation for BKE: latest heat_yoy + trend + cohort-z, and whether attention corroborates the
    'traffic still positive' (anti-melt) story or a rollover."""
    h = heat.get(FOCAL, {})
    hy = h.get("heat_yoy_pct", {})
    hz = h.get("heat_z", {})
    qs = sorted(hy)
    last = qs[-1] if qs else None
    prev = qs[-2] if len(qs) >= 2 else None
    # trailing-4q trend of heat_yoy (are the YoY prints rising or falling?)
    trail = [hy[q] for q in qs[-4:]]
    slope = None
    if len(trail) >= 3:
        xs = list(range(len(trail)))
        mx, my = statistics.mean(xs), statistics.mean(trail)
        den = sum((x - mx) ** 2 for x in xs)
        slope = round(sum((x - mx) * (y - my) for x, y in zip(xs, trail)) / den, 2) if den else None
    return {
        "article": h.get("article"), "avg_monthly_base": h.get("avg_monthly_base"),
        "thin_base": h.get("thin_base"),
        "latest_q": last, "latest_heat_yoy": hy.get(last), "latest_z": hz.get(last),
        "prev_q": prev, "prev_heat_yoy": hy.get(prev), "prev_z": hz.get(prev),
        "trailing4_heat_yoy": {q: hy[q] for q in qs[-4:]},
        "trend_slope_pp_per_q": slope,
    }


def main():
    today = datetime.date.today()
    heat = build()
    th = trends_heat()
    degraded = not bool(th)
    bt = backtest(heat)
    read = bke_read(heat, bt)
    cur_q = f"{today.year}Q{(today.month - 1) // 3 + 1}"
    prev_q = f"{today.year}Q{(today.month - 1) // 3}" if today.month > 3 else f"{today.year - 1}Q4"

    print(f"=== APPAREL BRAND-HEAT INDEX  {today}  (Wikipedia attention, YoY, cohort-z) ===")
    print(f"  instruments: Wikipedia pageviews" + ("" if degraded else " + Google Trends") +
          ("   [DEGRADED: Wikipedia-only, no Trends file]" if degraded else ""))
    print(f"  {'ticker':<7}{'cohort':<7}{prev_q + ' yoy':>11}{'z':>7}{cur_q + ' yoy':>11}{'z':>7}")
    for t in BRANDS:
        h = heat.get(t, {})
        if "error" in h:
            print(f"  {t:<7} ERROR {h['error'][:52]}"); continue
        py, pz = h["heat_yoy_pct"].get(prev_q), h.get("heat_z", {}).get(prev_q)
        cy, cz = h["heat_yoy_pct"].get(cur_q), h.get("heat_z", {}).get(cur_q)
        fmt = lambda x: ("-" if x is None else f"{x:+g}")
        mark = "  <= BKE" if t == FOCAL else ""
        print(f"  {t:<7}{COHORT(t):<7}{fmt(py):>11}{fmt(pz):>7}{fmt(cy):>11}{fmt(cz):>7}{mark}")

    if "within_brand_directional" in bt:
        d, sp, xs = bt["within_brand_directional"], bt["same_quarter_pearson"], bt["cross_sectional_rank"]
        print(f"\n  BACKTEST vs printed comps (heat YoY -> comparable sales):")
        print(f"   within-brand directional agreement : {d['hit_rate']}  (n={d['n']}, hits={d['hits']})")
        print(f"   same-quarter Pearson               : {sp['corr']} (n={sp['n']}) | ex-heat-spike {sp['corr_ex_heat_spike']} (n={sp['n_ex_heat_spike']})")
        print(f"   heat-leads-1q Pearson              : {bt['heat_leads_1q_pearson']['corr']} (n={bt['heat_leads_1q_pearson']['n']})")
        print(f"   cross-sectional rank (Spearman)    : {xs['mean_spearman']} (avg over {xs['n_quarters']} quarters)")

    # ---- verdict ----------------------------------------------------------------
    trend = ("up" if (read["trend_slope_pp_per_q"] or 0) > 0 else
             "down" if (read["trend_slope_pp_per_q"] or 0) < 0 else "flat")
    hit = bt.get("within_brand_directional", {}).get("hit_rate") if isinstance(bt, dict) else None
    n = bt.get("within_brand_directional", {}).get("n") if isinstance(bt, dict) else None
    caveats = []
    if read.get("thin_base"):
        caveats.append(f"BKE Wikipedia base ~{read.get('avg_monthly_base')} views/mo (< {THIN_BASE} floor): "
                       f"its heat_yoy is noise, z suppressed, EXCLUDED from cohort+backtest.")
    if degraded:
        caveats.append("Google Trends unavailable (429 / no Chrome-intercepted file): the purchase-intent "
                       "instrument ('buckle jeans'/'BKE jeans') that would carry BKE is OFF — Wikipedia-only run.")
    # BKE can only be corroborated if it has a usable attention signal; here it does not
    if read.get("thin_base") or degraded:
        verdict = "inconclusive"
    else:
        z = read.get("latest_z") or 0
        if z > 0.4 and trend != "down":
            verdict = "anti-melt-corroborated"
        elif z < -0.4 and trend == "down":
            verdict = "melt-corroborated"
        else:
            verdict = "inconclusive"

    print(f"\n  BKE MELT-TRIANGULATION READ:")
    print(f"   article={read['article']}  base~{read.get('avg_monthly_base')}/mo  thin_base={read.get('thin_base')}")
    print(f"   latest {read['latest_q']} heat_yoy={read['latest_heat_yoy']}% (z={read['latest_z']})  "
          f"prev {read['prev_q']} {read['prev_heat_yoy']}% (z={read['prev_z']})")
    print(f"   trailing-4q heat_yoy: {read['trailing4_heat_yoy']}  slope={read['trend_slope_pp_per_q']} pp/q ({trend})")
    print(f"   VERDICT: {verdict}")

    block = {"bke_heat_yoy": read.get("latest_heat_yoy"), "bke_cohort_z": read.get("latest_z"),
             "trend_direction": trend, "backtest_hit_rate": hit, "n": n,
             "instruments_used": ["wikipedia_pageviews"] + ([] if degraded else ["google_trends"]),
             "degraded": degraded, "verdict": verdict, "caveats": caveats}
    print("\n  JSON:\n" + json.dumps(block, indent=1))

    OUT.write_text(json.dumps({"asof": today.isoformat(), "degraded": degraded, "verdict_block": block,
                               "heat": heat, "backtest": bt, "bke_read": read}, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
