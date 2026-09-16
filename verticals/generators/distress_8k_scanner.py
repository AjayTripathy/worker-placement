"""distress_8k_scanner — Stage 0b generator: DISTRESS-TELL filings, whole market (EDGAR full-text search).

Scans the last N days for the classic tells: Item 4.01 auditor changes, NT 10-K/NT 10-Q late filings,
credit-agreement amendments/waivers, and going-concern language in 8-Ks. Each hit is an avoid/short seed or a
dislocation-buy candidate (a headline that DOESN'T reach the asset — the muni-dislocation pattern, equities
edition). Exclusion is the product.

  python3 verticals/generators/distress_8k_scanner.py [--days 7]
Writes data/DISTRESS_8K.json. Uses efts.sec.gov full-text search (free, SEC-compliant UA). READ-ONLY.
"""
from __future__ import annotations
import json, datetime, argparse, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "DISTRESS_8K.json"
EFTS = "https://efts.sec.gov/LATEST/search-index?"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}
QUERIES = [
    ("auditor_change", {"q": '"Item 4.01"', "forms": "8-K"}),
    ("late_10K", {"q": "", "forms": "NT 10-K"}),
    ("late_10Q", {"q": "", "forms": "NT 10-Q"}),
    ("covenant_waiver", {"q": '"waiver" "credit agreement"', "forms": "8-K"}),
    ("going_concern_8k", {"q": '"substantial doubt" "going concern"', "forms": "8-K"}),
]


def _search(q: dict, since: str) -> list[dict]:
    params = {"dateRange": "custom", "startdt": since, "enddt": datetime.date.today().isoformat(),
              "forms": q["forms"]}
    if q["q"]:
        params["q"] = q["q"]
    url = EFTS + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers=HDRS)
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.load(r)
    except Exception:
        return []
    out = []
    for hit in d.get("hits", {}).get("hits", [])[:40]:
        s = hit.get("_source", {})
        names = s.get("display_names") or []
        out.append({"filed": s.get("file_date"), "company": (names[0] if names else "")[:70],
                    "form": s.get("file_type") or s.get("root_forms", [""])[0],
                    "accession": s.get("_id", hit.get("_id", ""))[:30]})
    return out


def scan(days: int) -> dict:
    since = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    res = {}
    for label, q in QUERIES:
        res[label] = _search(q, since)
    total = sum(len(v) for v in res.values())
    return {"asof": datetime.date.today().isoformat(), "since": since, "n_hits": total, "by_tell": res}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    res = scan(a.days)
    print(f"=== 8-K DISTRESS SCANNER  {res['asof']}  ({res['n_hits']} tells since {res['since']}) ===")
    for label, hits in res["by_tell"].items():
        if not hits:
            continue
        print(f"  {label} ({len(hits)}):")
        for h in hits[:6]:
            print(f"   {h['filed']}  {h['company'][:56]:<56} {h['form']}")
        if len(hits) > 6:
            print(f"   ... +{len(hits)-6} more")
    print("  PROMOTE: avoid/short seeds; ALSO check each vs the dislocation-buy pattern (headline that doesn't reach the asset).")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
