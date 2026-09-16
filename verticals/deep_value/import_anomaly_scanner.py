"""import_anomaly_scanner — INVERTED thesis generation (pipeline Stage 0b): scan the ENTIRE US import
universe (Census int'l-trade, all ~1,200 HS4 categories, monthly, ~5wk lag) for acceleration anomalies,
and surface the movers as THESIS SEEDS — data first, idea second.

The physical-truth logic (per the microstructure doctrine): import flows LEAD revenue prints by ~a quarter
for import-dependent businesses. A category accelerating hard = somebody's volumes are inflecting before
any filing says so; a category rolling over = the SILICON2/EOLS-style deceleration tell. The scanner finds
the categories; a SignalOS pass then maps categories -> entities (customs-BOL consignees) -> tradeable
vehicles (brand owner / ODM / distributor / supplier) and drafts the seed, which enters the pipeline at
Stage 1 (trap-screen) like any other candidate.

Metrics per HS4: t3 = trailing-3-completed-months import value; yoy = t3 vs same window last year;
accel = yoy(now) - yoy(3 months earlier). Floor: t3 >= $150M (too-small categories can't move a public co).
Monthly cache -> only new months are fetched. Census key from ~/.census_key or CENSUS_KEY.

  python3 verticals/deep_value/import_anomaly_scanner.py            # scan + rank + seed list
READ-ONLY; writes data/import_hs4_cache.json + data/IMPORT_ANOMALIES.json.
"""
from __future__ import annotations
import json, os, datetime, statistics, urllib.request, urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys
DIRECTION = "exports" if "--exports" in sys.argv else "imports"
API = f"https://api.census.gov/data/timeseries/intltrade/{DIRECTION}/hs"
CACHE = HERE / "data" / ("export_hs4_cache.json" if DIRECTION == "exports" else "import_hs4_cache.json")
OUT = HERE / "data" / ("EXPORT_ANOMALIES.json" if DIRECTION == "exports" else "IMPORT_ANOMALIES.json")
MONTHS_BACK = 30
MIN_T3_USD = 150e6
TOP_UP, TOP_DOWN = 15, 10


def _key() -> str | None:
    k = os.environ.get("CENSUS_KEY", "").strip()
    if k:
        return k
    f = Path.home() / ".census_key"
    return f.read_text().strip() if f.exists() else None


def _fetch_month(ym: str, key: str) -> dict | None:
    """{hs4: {'desc':..., 'val': $}} for one month, or None if the month isn't published yet."""
    q = urllib.parse.urlencode({"get": ("E_COMMODITY,E_COMMODITY_SDESC,ALL_VAL_MO" if DIRECTION == "exports" else "I_COMMODITY,I_COMMODITY_SDESC,GEN_VAL_MO"),
                                "time": ym, "COMM_LVL": "HS4", "key": key})
    try:
        with urllib.request.urlopen(f"{API}?{q}", timeout=60) as r:
            rows = json.load(r)
    except Exception:
        return None
    out = {}
    for c, desc, v, *_rest in rows[1:]:
        try:
            out[c] = {"desc": desc[:70], "val": out.get(c, {}).get("val", 0) + int(v)}
        except (ValueError, TypeError):
            pass
    return out or None


def load_series() -> dict:
    """Ensure the cache covers the trailing window; fetch only missing months. Returns {ym: {hs4:{desc,val}}}."""
    key = _key()
    assert key, "Census key required (~/.census_key or CENSUS_KEY)"
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    today = datetime.date.today()
    months = []
    y, m = today.year, today.month
    for _ in range(MONTHS_BACK + 3):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        months.append(f"{y}-{m:02d}")
    fetched = 0
    for ym in months:
        if ym in cache:
            continue
        d = _fetch_month(ym, key)
        if d:
            cache[ym] = d
            fetched += 1
        elif months.index(ym) > 2:      # older month missing = real API problem, not publication lag
            break
    if fetched:
        CACHE.write_text(json.dumps(cache))
    return cache


def scan() -> dict:
    cache = load_series()
    months = sorted(cache)                      # ascending
    if len(months) < 18:
        return {"error": f"only {len(months)} months cached — need >=18 for yoy+accel"}
    latest3, prior_yr3 = months[-3:], months[-15:-12]
    earlier3, earlier_prior3 = months[-6:-3], months[-18:-15]

    def t3(hs, mset):
        vals = [cache[m].get(hs, {}).get("val") for m in mset]
        return sum(v for v in vals if v) if all(v is not None for v in vals) else None

    all_hs = set().union(*[set(cache[m]) for m in latest3])
    rows = []
    for hs in all_hs:
        a, b = t3(hs, latest3), t3(hs, prior_yr3)
        c, d = t3(hs, earlier3), t3(hs, earlier_prior3)
        if not (a and b and c and d) or a < MIN_T3_USD:
            continue
        yoy_now = (a / b - 1) * 100
        yoy_prev = (c / d - 1) * 100
        rows.append({"hs4": hs, "desc": cache[latest3[-1]].get(hs, cache[latest3[0]].get(hs, {})).get("desc", ""),
                     "t3_usd_m": round(a / 1e6), "yoy_pct": round(yoy_now, 1),
                     "yoy_prev_pct": round(yoy_prev, 1), "accel_pp": round(yoy_now - yoy_prev, 1)})
    mu = statistics.mean(r["accel_pp"] for r in rows)
    sd = statistics.pstdev(r["accel_pp"] for r in rows) or 1
    for r in rows:
        r["accel_z"] = round((r["accel_pp"] - mu) / sd, 2)
    rows.sort(key=lambda r: -r["accel_pp"])
    return {"asof": datetime.date.today().isoformat(), "window": f"{latest3[0]}..{latest3[-1]}",
            "n_categories": len(rows), "accelerating": rows[:TOP_UP], "decelerating": rows[-TOP_DOWN:][::-1]}


def main():
    res = scan()
    if "error" in res:
        print(f"=== IMPORT ANOMALY SCANNER — {res['error']} ===")
        return
    print(f"=== IMPORT ANOMALY SCANNER  {res['asof']}  (window {res['window']}; {res['n_categories']} HS4 categories >= ${MIN_T3_USD/1e6:.0f}M/qtr) ===")
    print(f"  TOP ACCELERATING (thesis-seed candidates — who benefits/supplies/distributes?):")
    for r in res["accelerating"]:
        print(f"   {r['hs4']}  {r['desc'][:52]:<52} t3 ${r['t3_usd_m']:>6,}M  yoy {r['yoy_pct']:+7.1f}%  accel {r['accel_pp']:+7.1f}pp  z{r['accel_z']:+5.1f}")
    print(f"  TOP DECELERATING (rollover tells — who's exposed?):")
    for r in res["decelerating"]:
        print(f"   {r['hs4']}  {r['desc'][:52]:<52} t3 ${r['t3_usd_m']:>6,}M  yoy {r['yoy_pct']:+7.1f}%  accel {r['accel_pp']:+7.1f}pp  z{r['accel_z']:+5.1f}")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"  PROMOTE: hand the top movers to a SignalOS vehicle-mapping pass (category -> consignees -> tickers -> seed).")
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
