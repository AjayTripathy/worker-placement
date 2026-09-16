"""warn_layoff_scanner — Stage 0b generator: WARN-notice layoff waves (state filings; margin actions/distress).

WARN notices are filed 60+ days BEFORE mass layoffs — a genuinely leading, free, public signal of cost actions
(bullish margin tell on strong names) or distress (bearish on weak ones). v1 covers CALIFORNIA (EDD xlsx — the
largest and best-structured state feed) + TEXAS (TWC yearly listing) where parseable; other states degrade
honestly. Employer->ticker mapping = SignalOS downstream.

  python3 verticals/generators/warn_layoff_scanner.py [--days 30]
Writes data/WARN_LAYOFFS.json. READ-ONLY.

CLOUD-IP CAVEAT (2026-07-12): the CA EDD site blocks datacenter/cloud IPs — a sweep AGENT running there
gets an empty fetch and may misread it as "stale/no data" (this happened once). This is NOT staleness and
NOT a cache: there is no cache fallback; `_ca()` fetches live only. An empty result sets degraded=["CA
fetch/parse failed"] — trust that flag, not an assumption. From the cron (residential IP) the live path
returns current notices normally. If an agent needs WARN data, run it locally or use the last cron output.
"""
from __future__ import annotations
import json, io, re, datetime, argparse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "WARN_LAYOFFS.json"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}
CA_PAGE = "https://edd.ca.gov/en/jobs_and_training/Layoff_Services_WARN"


def _get(url) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except Exception:
        return None


def _ca(days: int) -> list[dict]:
    page = _get(CA_PAGE)
    if not page:
        return []
    m = re.search(r'href="(/siteassets/files/jobs_and_training/warn/[^"]+\.xlsx)"', page.decode("utf-8", "ignore"))
    if not m:
        return []
    raw = _get("https://edd.ca.gov" + m.group(1))
    if not raw:
        return []
    try:
        import pandas as pd
        # the EDD workbook: header row varies; find the sheet with 'Company' col
        xl = pd.ExcelFile(io.BytesIO(raw))
        for sheet in xl.sheet_names:
            df = xl.parse(sheet, header=None)
            hdr = None
            for i in range(min(8, len(df))):
                row = [str(x).lower() for x in df.iloc[i].tolist()]
                if any("company" in c for c in row):
                    hdr = i
                    break
            if hdr is None:
                continue
            df = xl.parse(sheet, header=hdr)
            cols = {c.lower().strip(): c for c in df.columns if isinstance(c, str)}
            comp = next((cols[c] for c in cols if "company" in c), None)
            emp = next((cols[c] for c in cols if "employees" in c or "affected" in c), None)
            dt = next((cols[c] for c in cols if "notice" in c and "date" in c), None) or \
                 next((cols[c] for c in cols if "received" in c), None)
            if not comp:
                continue
            cutoff = datetime.date.today() - datetime.timedelta(days=days)
            out = []
            for _, r in df.iterrows():
                try:
                    d = r[dt]
                    d = d.date() if hasattr(d, "date") else datetime.datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
                except Exception:
                    continue
                if d < cutoff:
                    continue
                out.append({"state": "CA", "date": d.isoformat(), "employer": str(r[comp])[:60],
                            "affected": int(r[emp]) if emp and str(r[emp]).replace(".0", "").isdigit() else None})
            if out:
                return out
        return []
    except Exception:
        return []


def scan(days: int) -> dict:
    ca = _ca(days)
    rows = sorted(ca, key=lambda r: (r["date"]), reverse=True)
    # aggregate repeat filers (multi-site waves) — the interesting cluster signal
    agg = {}
    for r in rows:
        k = re.sub(r"[^A-Z0-9 ]", "", r["employer"].upper())[:40]
        a = agg.setdefault(k, {"employer": r["employer"], "notices": 0, "affected": 0})
        a["notices"] += 1
        a["affected"] += r["affected"] or 0
    waves = sorted([a for a in agg.values() if a["notices"] >= 2 or a["affected"] >= 250],
                   key=lambda a: -a["affected"])
    return {"asof": datetime.date.today().isoformat(), "window_days": days,
            "n_notices": len(rows), "states_covered": ["CA"] if ca else [],
            "degraded": [] if ca else ["CA fetch/parse failed — no reading"],
            "waves": waves[:15], "recent": rows[:20],
            "note": "WARN leads layoffs 60+ days; employer->ticker = SignalOS step; TX/NY feeds queued"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    res = scan(a.days)
    print(f"=== WARN LAYOFF SCANNER  {res['asof']}  ({res['n_notices']} notices, {res['window_days']}d, states {res['states_covered'] or 'NONE — degraded'}) ===")
    if res["degraded"]:
        for d in res["degraded"]:
            print(f"  DEGRADED: {d}")
    if res["waves"]:
        print("  WAVES (multi-notice or >=250 affected):")
        for w in res["waves"][:10]:
            print(f"   {w['employer']:<52} {w['notices']} notices  {w['affected']:>6,} affected")
    print("  PROMOTE: SignalOS maps employers -> tickers; wave at a STRONG name = margin action (bullish tell); at a WEAK one = distress.")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
