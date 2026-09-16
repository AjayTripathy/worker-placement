"""Price pulls for the 2026-08-18 gauntlet adjudication (HIVE close gate, BULL 52w roll-off)."""
import warnings

warnings.filterwarnings("ignore")
import datetime

import yfinance as yf

for t in ["HIVE", "BULL", "RDDT", "SUJA", "KLAR"]:
    h = yf.Ticker(t).history(period="1y", auto_adjust=False)
    if h.empty:
        print(t, "NO DATA")
        continue
    c = h["Close"]
    print("==", t, "last 6 closes:", [(str(i.date()), round(v, 2)) for i, v in list(c.items())[-6:]])
    print("   window", str(c.index[0].date()), "->", str(c.index[-1].date()))
    print("   52w high", round(c.max(), 2), "on", str(c.idxmax().date()),
          "| 52w low", round(c.min(), 2), "on", str(c.idxmin().date()))
    cut = c.index[0] + datetime.timedelta(days=3)
    c2 = c[c.index > cut]
    print("   high excluding oldest 3 calendar days:", round(c2.max(), 2), "on", str(c2.idxmax().date()))
