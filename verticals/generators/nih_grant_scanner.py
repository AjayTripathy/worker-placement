"""nih_grant_scanner — Stage 0b generator: NIH SBIR/STTR grant flow to COMPANIES (RePORTER).

Non-dilutive funding to small biotechs = runway + scientific validation, disclosed months before any filing
mentions it. Scan SBIR/STTR awards (activity codes R43/R44/U43/U44/R41/R42) by organization, trailing fiscal
year vs prior, rank the movers. Org->ticker = SignalOS step (most are private — the PUBLIC ones are the seeds;
private clusters = watchlist for IPOs, the beauty-radar pattern).

  python3 verticals/generators/nih_grant_scanner.py
Writes data/NIH_GRANT_FLOW.json. Free API. READ-ONLY.
"""
from __future__ import annotations
import json, datetime, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "NIH_GRANT_FLOW.json"
API = "https://api.reporter.nih.gov/v2/projects/search"
CODES = ["R43", "R44", "U43", "U44", "R41", "R42"]


def _year(fy: int) -> dict:
    """{org: total_$} for SBIR/STTR awards in fiscal year fy."""
    out, offset = {}, 0
    while offset < 14500:
        body = {"criteria": {"fiscal_years": [fy], "activity_codes": CODES},
                "include_fields": ["Organization", "AwardAmount"], "limit": 500, "offset": offset}
        req = urllib.request.Request(API, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "signalos-research 4tripathy@gmail.com"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.load(r)
        except Exception:
            break
        res = d.get("results", [])
        for p in res:
            org = ((p.get("organization") or {}).get("org_name") or "").upper()[:60]
            if org:
                out[org] = out.get(org, 0) + (p.get("award_amount") or 0)
        if len(res) < 500:
            break
        offset += 500
    return out


def scan() -> dict:
    fy = datetime.date.today().year          # federal FY (Oct-Sep); current-year partial vs full prior is noted
    cur, prv = _year(fy), _year(fy - 1)
    rows = []
    for org, v in cur.items():
        if v < 1e6:
            continue
        rows.append({"org": org.title(), "cur_usd_m": round(v / 1e6, 1),
                     "prior_usd_m": round(prv.get(org, 0) / 1e6, 1)})
    rows.sort(key=lambda r: -(r["cur_usd_m"] - r["prior_usd_m"]))
    return {"asof": datetime.date.today().isoformat(), "fy": fy,
            "note": f"FY{fy} is PARTIAL (Oct-{datetime.date.today():%b}) vs full FY{fy-1} — deltas understate; org->ticker = SignalOS; private clusters = IPO watchlist",
            "n_orgs": len(rows), "movers": rows[:20]}


def main():
    res = scan()
    print(f"=== NIH SBIR/STTR GRANT-FLOW SCANNER  {res['asof']}  (FY{res['fy']} partial, {res['n_orgs']} orgs >= $1M) ===")
    for r in res["movers"][:14]:
        print(f"   {r['org']:<56} ${r['cur_usd_m']:>6}M  (prior ${r['prior_usd_m']}M)")
    print(f"  {res['note']}")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
