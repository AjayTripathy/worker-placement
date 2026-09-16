"""Cache pre-2026-05-26 10-K filings for forward-test universe.

Most recent 10-K filed before cutoff (typically FY2025 10-K filed Q1 2026).
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
PUBLIC_CO = HERE.parents[2]
DATA = PUBLIC_CO / "data"

sys.path.insert(0, str(HERE.parents[4]))
from verticals.public_co import edgar

CUTOFF = "2026-05-25"


def latest_10k_pre_cutoff(cik: str):
    _, filings = edgar.list_filings(cik)
    candidates = [f for f in filings
                  if f.get("form") in ("10-K", "10-K/A") and (f.get("filing_date") or "") <= CUTOFF]
    if not candidates:
        return None
    candidates.sort(key=lambda f: f["filing_date"], reverse=True)
    return candidates[0]


def cache_one(ticker: str, cik: str) -> dict:
    if not cik or cik == 'None':
        return {"status": "no_cik"}
    tkl = ticker.lower()
    out_dir = DATA / tkl / "filings_2026_05_25"
    out_dir.mkdir(parents=True, exist_ok=True)

    filing = latest_10k_pre_cutoff(cik)
    if filing is None:
        return {"status": "no_pre_cutoff_10k"}
    accession = filing["accession"]
    primary = filing["primary_document"]
    out_path = out_dir / f"{accession}_10K.txt"
    if out_path.exists() and out_path.stat().st_size > 50_000:
        return {"status": "cached", "filing_path": str(out_path.relative_to(PUBLIC_CO.parents[1])),
                "filing_date": filing["filing_date"], "accession": accession}
    text = edgar.fetch_filing_text(cik, accession, primary)
    if not text:
        return {"status": "fetch_failed", "accession": accession}
    out_path.write_text(text)
    return {"status": "downloaded", "filing_path": str(out_path.relative_to(PUBLIC_CO.parents[1])),
            "filing_date": filing["filing_date"], "accession": accession, "bytes": len(text)}


def main():
    universe = json.loads((HERE / "forward_test_set.json").read_text())
    print(f"Caching pre-{CUTOFF} 10-Ks for {len(universe)} names...")
    print()

    manifest = {}
    for i, r in enumerate(universe):
        tk = r["ticker"]
        cik = r.get("cik", "")
        result = cache_one(tk, cik)
        entry = {
            "company": r.get("company", ""), "cik": cik,
            "sector": r.get("sector", ""), "industry": r.get("industry", ""),
            "drawdown_2026_05_25": r["drawdown_2026_05_25"],
            "price_2026_05_25": r["price_2026_05_25"],
            "group": "forward_test_2026",
            **{k: v for k, v in result.items() if k != "status"},
            "cache_status": result["status"],
        }
        manifest[tk] = entry
        size_tag = f' {result.get("bytes", 0)//1024}KB' if result.get("bytes") else ''
        print(f"  [{i+1:>2}/{len(universe)}] {tk:6}  cik={cik or 'n/a':>10}  {result['status']}{size_tag}")
        time.sleep(0.15)

    (HERE / "forward_agent_manifest.json").write_text(json.dumps(manifest, indent=2))

    n_ok = sum(1 for v in manifest.values() if v.get("cache_status") in ("cached", "downloaded"))
    print()
    print(f"OK: {n_ok}/{len(universe)} have cached 10-K")
    bad = [(tk, v.get("cache_status")) for tk, v in manifest.items()
           if v.get("cache_status") not in ("cached", "downloaded")]
    if bad:
        print("Issues:")
        for tk, s in bad:
            print(f"  {tk}: {s}")


if __name__ == "__main__":
    main()
