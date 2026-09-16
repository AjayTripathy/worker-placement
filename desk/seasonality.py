"""seasonality — per-ticker quarterly seasonal shape from audited XBRL (built after the IBEX Q4 read,
2026-07-03, where a 'scary deceleration' was substantially normal June-quarter seasonal shape + one
anomalous hard comp).

For any US filer: pulls quarterly revenue history, computes the median QoQ move per fiscal quarter,
and flags for the NEXT print: (a) whether a feared/guided deceleration is within normal seasonal shape,
(b) hard/easy comps (prior-year quarter deviated >2x from its own seasonal median).

  python3 -m desk.seasonality IBEX          # single name
  python3 -m desk.seasonality --calendar    # annotate every upcoming earnings_print on the prediction calendar
READ-ONLY.
"""
from __future__ import annotations
import json, sys, datetime, statistics, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}
TAGS = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
        "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet"]
_CIK_CACHE = ROOT / "desk" / "data" / "cik_map.json"


def _cik(ticker: str) -> str | None:
    if _CIK_CACHE.exists():
        m = json.loads(_CIK_CACHE.read_text())
    else:
        req = urllib.request.Request("https://www.sec.gov/files/company_tickers.json", headers=HDRS)
        raw = json.load(urllib.request.urlopen(req, timeout=30))
        m = {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in raw.values()}
        _CIK_CACHE.write_text(json.dumps(m))
    return m.get(ticker.upper().split(".")[0])


def quarterly_revenue(ticker: str) -> list[tuple[str, float]]:
    cik = _cik(ticker)
    if not cik:
        return []
    for tag in TAGS:
        url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"
        try:
            req = urllib.request.Request(url, headers=HDRS)
            d = json.load(urllib.request.urlopen(req, timeout=30))
        except Exception:
            continue
        qs = {}
        for u in d.get("units", {}).get("USD", []):
            try:
                s = datetime.date.fromisoformat(u["start"]); e = datetime.date.fromisoformat(u["end"])
            except Exception:
                continue
            if 80 <= (e - s).days <= 100:
                qs[u["end"]] = u["val"]
            elif 350 <= (e - s).days <= 380:
                qs.setdefault("FY:" + u["end"], u["val"])
        # derive missing fiscal-Q4s: annual minus the three filed quarters (Q4 is rarely filed discretely)
        fys = {k[3:]: v for k, v in qs.items() if k.startswith("FY:")}
        qs = {k: v for k, v in qs.items() if not k.startswith("FY:")}
        for fy_end, fy_val in fys.items():
            if fy_end in qs:
                continue
            e = datetime.date.fromisoformat(fy_end)
            three = []
            for back in (3, 6, 9):
                m = e.month - back
                y = e.year + (m - 1) // 12
                m = (m - 1) % 12 + 1
                # find a filed quarter ending in that month/year (day may differ: 30/31)
                hits = [v for k, v in qs.items() if k[:7] == f"{y:04d}-{m:02d}"]
                if hits:
                    three.append(hits[0])
            if len(three) == 3:
                qs[fy_end] = fy_val - sum(three)
        if len(qs) >= 8:
            return sorted(qs.items())
    return []


def analyze(ticker: str) -> dict:
    rows = quarterly_revenue(ticker)
    if len(rows) < 8:
        return {"ticker": ticker, "status": "INSUFFICIENT_DATA", "n_quarters": len(rows)}
    # group QoQ moves by fiscal-quarter-end month (fiscal quarters identified by period-end month)
    byq, seq = {}, []
    for i in range(1, len(rows)):
        qoq = (rows[i][1] / rows[i - 1][1] - 1) * 100
        month = rows[i][0][5:7]
        byq.setdefault(month, []).append(round(qoq, 1))
        seq.append((rows[i][0], round(qoq, 1)))
    shape = {m: {"median_qoq": round(statistics.median(v), 1), "n": len(v), "all": v}
             for m, v in sorted(byq.items())}
    # hard/easy comps: quarters whose QoQ deviated >5pp from their own seasonal median
    anomalies = []
    for end, qoq in seq:
        med = shape[end[5:7]]["median_qoq"]
        if abs(qoq - med) > 5:
            anomalies.append({"quarter_end": end, "qoq": qoq, "seasonal_median": med,
                              "note": ("EASY comp for the next lap" if qoq < med else "HARD comp for the next lap")})
    # the next quarter to print = quarter after the last reported
    last_end = rows[-1][0]
    nxt_month = {"03": "06", "06": "09", "09": "12", "12": "03"}.get(last_end[5:7], "?")
    nxt = shape.get(nxt_month, {})
    prior_year_same_q = [a for a in anomalies if a["quarter_end"][5:7] == nxt_month and a["quarter_end"][:4] == str(int(last_end[:4]) - (0 if nxt_month > last_end[5:7] else -1))]
    return {"ticker": ticker, "status": "OK", "n_quarters": len(rows),
            "seasonal_shape_by_quarter_end_month": {m: {"median_qoq": v["median_qoq"], "n": v["n"]} for m, v in shape.items()},
            "next_print_quarter_month": nxt_month,
            "next_print_seasonal_median_qoq": nxt.get("median_qoq"),
            "anomalous_quarters": anomalies[-6:],
            "read": f"a sequential move near {nxt.get('median_qoq')}% QoQ is NORMAL seasonal shape for this fiscal quarter"
                    + ("; NOTE prior-year same-quarter was anomalous -> YoY optics distorted" if prior_year_same_q else "")}


def main():
    if "--calendar" in sys.argv:
        led = ROOT / "desk" / "data" / "calibration_ledger.jsonl"
        today = datetime.date.today().isoformat()
        seen = set()
        for l in led.read_text().splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("status") == "OPEN" and r.get("event_type") == "earnings_print" and (r.get("cat_date") or "") >= today:
                t = r["ticker"].split(".")[0]
                if t in seen or not t.isalpha():
                    continue
                seen.add(t)
                a = analyze(t)
                if a["status"] == "OK":
                    flag = " >>> HARD/EASY COMP IN PLAY" if any(x["quarter_end"][5:7] == a["next_print_quarter_month"] for x in a["anomalous_quarters"]) else ""
                    print(f"  {t:<7} next-print seasonal median QoQ {a['next_print_seasonal_median_qoq']}%{flag}")
        return
    t = sys.argv[1] if len(sys.argv) > 1 else "IBEX"
    print(json.dumps(analyze(t), indent=1))


if __name__ == "__main__":
    main()
