"""conditions — the financial-conditions GATE: the necessary (not sufficient) condition for a deal
cycle. Cheap financing + calm equity vol = the window CAN open; it doesn't mean it has. Free FRED data.

  HY OAS  (BAMLH0A0HYM2)  credit spread — tight = LBO/M&A financing available. The dominant gate.
  IG OAS  (BAMLC0A0CM)    investment-grade spread — corroborates.
  VIX     (VIXCLS)        equity vol — sustained <20 = IPO window can open.

Series are returned as monthly-last values so they align with the EDGAR monthly pipeline.
"""
from __future__ import annotations
import urllib.request, collections
from pathlib import Path

HDRS = {"User-Agent": "signalos-dealcycle research 4tripathy@gmail.com"}
SERIES = {"hy_oas": "BAMLH0A0HYM2", "ig_oas": "BAMLC0A0CM", "vix": "VIXCLS"}


def _fred_csv(series_id: str) -> list[tuple[str, float]]:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    txt = urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=30).read().decode()
    out = []
    for row in txt.strip().splitlines()[1:]:
        d, v = row.split(",")
        if v not in (".", ""):
            out.append((d, float(v)))
    return out


def latest() -> dict:
    """Current value + 1-month change for each gate series."""
    out = {}
    for k, sid in SERIES.items():
        try:
            s = _fred_csv(sid)
            last_d, last_v = s[-1]
            chg = last_v - s[-22][1] if len(s) > 22 else None     # ~1mo of trading days
            out[k] = {"value": round(last_v, 2), "date": last_d, "chg_1m": round(chg, 2) if chg is not None else None}
        except Exception as e:
            out[k] = {"value": None, "error": str(e)}
    return out


def monthly_series(series_key: str, start_ym: str, end_ym: str) -> dict[str, float]:
    """Month-end last value for a FRED series, keyed 'YYYY-MM' (for lead-lag alignment)."""
    s = _fred_csv(SERIES[series_key])
    by_month: dict[str, float] = collections.OrderedDict()
    for d, v in s:
        ym = d[:7]
        if start_ym <= ym <= end_ym:
            by_month[ym] = v          # last write per month = month-end-ish
    return dict(by_month)


def gate_state(c: dict | None = None) -> tuple[str, str]:
    """OPEN / TIGHTENING / FROZEN from the live gate. HY OAS is the dominant driver."""
    c = c or latest()
    hy = c.get("hy_oas", {}).get("value")
    vix = c.get("vix", {}).get("value")
    if hy is None:
        return "UNKNOWN", "no HY data"
    if hy < 3.5 and (vix is None or vix < 22):
        return "OPEN", f"HY {hy}% tight, VIX {vix} calm — financing available"
    if hy < 5.0:
        return "TIGHTENING", f"HY {hy}% / VIX {vix} — financing OK but watch"
    return "FROZEN", f"HY {hy}% wide — financing constrained"


if __name__ == "__main__":
    import json
    c = latest()
    print(json.dumps(c, indent=1))
    print("GATE:", *gate_state(c))
