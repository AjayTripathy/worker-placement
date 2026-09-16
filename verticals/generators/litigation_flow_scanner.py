"""litigation_flow_scanner — Stage 0b generator: NEW material federal suits, whole docket (CourtListener).

Inverts the litigation_screen verifier: instead of checking a named principal, scan the last N days of NEW
federal-district dockets in the MATERIAL nature-of-suit categories (securities fraud 850, RICO 470, False
Claims/qui tam 375/376, franchise 895-ish, investor classes) and surface PUBLIC-COMPANY defendants as
short/avoid seeds. Exclusion is the product: these seeds mostly protect capital.

  python3 verticals/generators/litigation_flow_scanner.py [--days 7]
Writes data/NEW_LITIGATION.json. READ-ONLY; free CourtListener API (no auth needed at modest volume).
"""
from __future__ import annotations
import json, datetime, argparse, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "NEW_LITIGATION.json"
CL = "https://www.courtlistener.com/api/rest/v4/search/"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}
# material nature-of-suit fielded queries (the anonymous SEARCH endpoint; /dockets/ requires auth)
NOS = {'suitNature:"securities"': "securities/commodities/exchange", 'suitNature:"racketeer"': "RICO",
       'suitNature:"false claims"': "False Claims Act", 'suitNature:"qui tam"': "qui tam (31 USC 3729)"}
CORP = ("INC", "CORP", "LLC", "LTD", "CO.", "COMPANY", "PLC", "HOLDINGS", "GROUP", "TECHNOLOGIES", "PHARMA")


def _fetch(nos_q: str, since: str) -> list[dict]:
    out, url = [], (CL + "?" + urllib.parse.urlencode({
        "type": "r", "q": nos_q, "filed_after": since, "order_by": "dateFiled desc"}))
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.load(r)
        except Exception:
            break
        out.extend(d.get("results", []))
        url = d.get("next")
        if not url:
            break
    return out


def _corp_defendants(case_name: str) -> list[str]:
    """Corporate-looking defendant names from 'X v. Y' (crude; SignalOS resolves properly downstream)."""
    if " v. " not in (case_name or ""):
        return []
    tail = case_name.split(" v. ", 1)[1]
    return [p.strip() for p in tail.split(" et al")[0].split(";")
            if any(k in p.upper() for k in CORP)][:3]


def scan(days: int) -> dict:
    since = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    rows = []
    for code, label in NOS.items():
        for d in _fetch(code, since):
            defs = _corp_defendants(d.get("caseName", ""))
            if not defs:
                continue
            rows.append({"filed": d.get("dateFiled", "")[:10], "nos": label, "court": d.get("court_id") or d.get("court", ""),
                         "case": (d.get("caseName") or "")[:90], "corp_defendants": defs,
                         "docket": f"https://www.courtlistener.com{d.get('docket_absolute_url') or d.get('absolute_url','')}"})
    rows.sort(key=lambda r: (r["filed"] or ""), reverse=True)
    return {"asof": datetime.date.today().isoformat(), "since": since, "n_material_suits": len(rows), "suits": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    res = scan(a.days)
    print(f"=== NEW-LITIGATION SCANNER  {res['asof']}  ({res['n_material_suits']} material federal suits w/ corporate defendants since {res['since']}) ===")
    for r in res["suits"][:15]:
        print(f"   {r['filed']}  [{r['nos'][:22]:<22}] {r['case'][:66]}")
    if res["n_material_suits"] > 15:
        print(f"   ... +{res['n_material_suits']-15} more in the JSON")
    print("  PROMOTE: SignalOS resolves corporate defendants -> tickers; PUBLIC defendants = avoid/short seeds; exclusion is the product.")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
