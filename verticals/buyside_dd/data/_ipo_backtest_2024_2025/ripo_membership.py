"""Did the framework's exclusion just reinvent RIPO's selection rule?

RIPO (Renaissance IPO ETF) selects on size/liquidity — it includes only the
larger, mostly US-listed new issues. If the names it actually held had a low
catastrophe rate, then "exclude foreign micro-cap IPOs" adds nothing over
buying the passive product.

Survivorship-aware membership: union of the US 'Renaissance IPO ETF' holdings
across EVERY quarter-end N-PORT (2024-03 .. 2026-03), so names that entered and
were later dropped still count as 'ever held'. Source = the fund's own N-PORT-P
filings on EDGAR (CIK 1026634). Matched to the cohort by normalized name.

Run: python3 verticals/buyside_dd/data/_ipo_backtest_2024_2025/ripo_membership.py
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "ripo_membership.json"
FUND_CIK = 1026634
UA = {"User-Agent": "SignalOS research 4tripathy@gmail.com"}

SUFFIXES = {"INC", "CORP", "CORPORATION", "LTD", "LIMITED", "LLC", "PLC", "CO",
            "GROUP", "HOLDINGS", "HOLDING", "SA", "AG", "NV", "PARENT",
            "TECHNOLOGIES", "INTERNATIONAL", "THE", "CLASS", "A", "COMPANY"}


def _get(url: str, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def norm(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9 ]", " ", (name or "").upper())
    toks = [t for t in s.split() if t and t not in SUFFIXES]
    return " ".join(toks)


def nport_accessions() -> list[tuple[str, str]]:
    d = json.loads(_get(f"https://data.sec.gov/submissions/CIK{FUND_CIK:010d}.json"))
    r = d["filings"]["recent"]
    out = []
    for i, f in enumerate(r["form"]):
        if "NPORT" in f.upper():
            out.append((r["accessionNumber"][i], r.get("reportDate", [""])[i] if i < len(r["reportDate"]) else ""))
    return out


def us_ipo_holdings(acc: str) -> tuple[str, list[str]] | None:
    a = acc.replace("-", "")
    x = _get(f"https://www.sec.gov/Archives/edgar/data/{FUND_CIK}/{a}/primary_doc.xml")
    m = re.search(r"<seriesName>(.*?)</seriesName>", x)
    series = m.group(1) if m else "?"
    if series.strip() != "Renaissance IPO ETF":
        return None  # skip International fund
    names = re.findall(r"<invstOrSec>.*?<name>(.*?)</name>", x, re.S)
    return series, names


def main():
    accs = nport_accessions()
    print(f"N-PORT filings: {len(accs)}", file=sys.stderr)
    ever_held: dict[str, str] = {}   # normalized name -> first report date seen
    quarters_used = []
    for acc, rdate in accs:
        if rdate and rdate < "2024-03-01":
            continue
        try:
            res = us_ipo_holdings(acc)
        except Exception as e:
            print(f"  ERR {acc}: {e}", file=sys.stderr)
            continue
        if res is None:
            continue
        _series, names = res
        quarters_used.append(rdate)
        for nm in names:
            k = norm(nm)
            if k and (k not in ever_held or rdate < ever_held[k]):
                ever_held[k] = rdate
        time.sleep(0.15)

    print(f"US IPO ETF quarter-ends used: {sorted(set(quarters_used))}", file=sys.stderr)
    print(f"Distinct names ever held: {len(ever_held)}", file=sys.stderr)

    cohort = json.loads((HERE / "cohort.json").read_text())["cohort"]
    outs = {o["cik"]: o for o in json.loads((HERE / "outcomes.json").read_text())["labels"]}

    in_ripo, not_in_ripo = [], []
    for rec in cohort:
        o = outs.get(rec["cik"], {})
        keys = {norm(rec["company_name"]), norm(rec.get("name_official") or "")}
        hit = next((ever_held[k] for k in keys if k in ever_held), None)
        r = o.get("r_current")
        if r is None and o.get("delisted_no_price"):
            r = -1.0  # adverse delist, no price; merger no-price stays None (excluded)
        row = {"cik": rec["cik"], "ticker": (rec["tickers"] or [None])[0],
               "name": rec["company_name"], "ipo_date": rec["ipo_date"],
               "r_current": r, "catastrophe": bool(o.get("catastrophe")),
               "ripo_first_seen": hit}
        (in_ripo if hit else not_in_ripo).append(row)

    def stats(rows):
        rets = [r["r_current"] for r in rows if r["r_current"] is not None]
        cats = sum(r["catastrophe"] for r in rows)
        return {
            "n": len(rows),
            "catastrophe_rate": round(cats / len(rows), 3) if rows else None,
            "mean_return": round(sum(rets) / len(rets), 4) if rets else None,
            "median_return": round(sorted(rets)[len(rets)//2], 4) if rets else None,
            "pct_positive": round(sum(1 for x in rets if x > 0) / len(rets), 3) if rets else None,
        }

    results = {
        "ripo_quarter_ends_used": sorted(set(quarters_used)),
        "ripo_distinct_names_ever_held": len(ever_held),
        "cohort_n": len(cohort),
        "cohort_in_ripo": stats(in_ripo),
        "cohort_not_in_ripo": stats(not_in_ripo),
        "in_ripo_names": sorted(r["name"] for r in in_ripo),
    }
    OUT.write_text(json.dumps(results, indent=2))

    print("\n=== COHORT vs RIPO ACTUAL HOLDINGS ===")
    print(f"RIPO ever-held distinct names (2024-03..2026-03): {len(ever_held)}")
    print(f"Cohort names that EVER entered RIPO: {results['cohort_in_ripo']['n']} / {len(cohort)}")
    print(f"\n{'segment':<22}{'n':<6}{'cat_rate':<10}{'mean':<10}{'median':<10}{'%pos'}")
    for lab, s in [("in RIPO", results["cohort_in_ripo"]), ("NOT in RIPO", results["cohort_not_in_ripo"])]:
        print(f"{lab:<22}{s['n']:<6}{s['catastrophe_rate']:<10}{s['mean_return']:<10}{s['median_return']:<10}{s['pct_positive']}")
    print(f"\nNames in RIPO ∩ cohort: {results['in_ripo_names']}")
    print(f"\nWrote {OUT.name}")


if __name__ == "__main__":
    main()
