"""Throwaway: 2026-09-11 gauntlet — pull HOFT Q2 FY27 8-K/10-Q primary docs."""
import json
import re
import sys

sys.path.insert(0, "desk")
import _gauntlet_fetch as g  # noqa: E402

CIK = "1077688"
ACC = "0001171843-26-005988"

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "index"
    if mode == "index":
        for r in g.edgar_recent(CIK, n=12):
            print(r)
        idx = g.get("https://www.sec.gov/Archives/edgar/data/%s/%s/" % (CIK, ACC.replace("-", "")))
        print("---INDEX---")
        print(re.findall(r'href="([^"]+\.(?:htm|html|pdf|xml))"', idx or "")[:30])
    elif mode == "doc":
        url = sys.argv[2]
        html = g.get(url)
        t = g.text(html)
        out = sys.argv[3] if len(sys.argv) > 3 else None
        if out:
            open(out, "w").write(t)
            print("wrote", out, len(t))
        else:
            print(t[:20000])
