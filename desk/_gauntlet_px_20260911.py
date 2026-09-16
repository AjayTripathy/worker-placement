"""Throwaway: 2026-09-11 gauntlet — HOFT price + EDGAR recall check on undetected names."""
import json
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, "desk")
import _gauntlet_fetch as g  # noqa: E402

if __name__ == "__main__":
    import yfinance as yf

    for t in ["HOFT"]:
        h = yf.Ticker(t).history(period="3mo", auto_adjust=False)
        if h.empty:
            print(t, "NO DATA")
            continue
        c = h["Close"]
        print("==", t, "last 6 closes:", [(str(i.date()), round(v, 2)) for i, v in list(c.items())[-6:]])
        try:
            fi = yf.Ticker(t).fast_info
            print("   fast_info last:", fi.get("lastPrice"), "prevClose:", fi.get("previousClose"))
        except Exception as e:
            print("   fast_info ERR", e)

    cik = json.load(open("desk/data/cik_map.json"))
    for t in ["PL", "COO", "GIII"]:
        c = cik.get(t)
        print("==", t, "CIK", c)
        if not c:
            continue
        for r in g.edgar_recent(c, n=6):
            print("   ", r)
