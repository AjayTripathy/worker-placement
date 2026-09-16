"""Cache pre-2024-05-15 10-K filings for each Tier 3 name.

Same pattern as Tier 2's cache_10ks but with cutoff 2024-05-15. Filings
are stored in `verticals/public_co/data/<ticker_lower>/filings_2024_05_15/`
to keep them separate from the Tier 1/Tier 2 cache.
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

CUTOFF = "2024-05-15"


def latest_10k_pre_cutoff(cik: str):
    _, filings = edgar.list_filings(cik)
    candidates = [
        f for f in filings
        if f.get("form") in ("10-K", "10-K/A") and (f.get("filing_date") or "") <= CUTOFF
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda f: f["filing_date"], reverse=True)
    return candidates[0]


def cache_one(ticker: str, cik: str) -> dict:
    tkl = ticker.lower()
    out_dir = DATA / tkl / "filings_2024_05_15"
    out_dir.mkdir(parents=True, exist_ok=True)

    filing = latest_10k_pre_cutoff(cik)
    if filing is None:
        return {"status": "no_pre_cutoff_10k"}

    accession = filing["accession"]
    primary = filing["primary_document"]
    out_path = out_dir / f"{accession}_10K.txt"

    if out_path.exists() and out_path.stat().st_size > 50_000:
        return {
            "status": "cached",
            "filing_path": str(out_path.relative_to(PUBLIC_CO.parents[1])),
            "filing_date": filing["filing_date"],
            "accession": accession,
        }

    text = edgar.fetch_filing_text(cik, accession, primary)
    if not text:
        return {"status": "fetch_failed", "accession": accession}
    out_path.write_text(text)
    return {
        "status": "downloaded",
        "filing_path": str(out_path.relative_to(PUBLIC_CO.parents[1])),
        "filing_date": filing["filing_date"],
        "accession": accession,
        "bytes": len(text),
    }


def main():
    blinded = json.loads((HERE / "tier3_test_set.json").read_text())
    print(f"Caching pre-{CUTOFF} 10-Ks for {len(blinded)} Tier 3 names...")
    print()

    manifest_blinded = {}
    manifest_full = {}
    for i, r in enumerate(blinded):
        tk = r["ticker"]
        cik = r.get("cik", "")
        if not cik:
            print(f"  [{i+1:>2}/{len(blinded)}] {tk:6}  NO_CIK (skipping)")
            manifest_blinded[tk] = {"cache_status": "no_cik"}
            continue
        result = cache_one(tk, cik)
        entry = {
            "company": r.get("company", ""),
            "cik": cik,
            "sector": r.get("sector", ""),
            "industry": r.get("industry", ""),
            "drawdown_2024_05_15": r["drawdown_2024_05_15"],
            "price_2024_05_15": r["price_2024_05_15"],
            "group": "walk_forward_2024",
            **{k: v for k, v in result.items() if k != "status"},
            "cache_status": result["status"],
        }
        manifest_blinded[tk] = entry
        manifest_full[tk] = {**entry}

        size_tag = f' {result.get("bytes", 0)//1024}KB' if result.get("bytes") else ''
        print(f"  [{i+1:>2}/{len(blinded)}] {tk:6}  cik={cik}  {result['status']}{size_tag}")
        time.sleep(0.15)

    full = json.loads((HERE / "_unblinded" / "tier3_test_set.json").read_text())
    for r in full:
        if r["ticker"] in manifest_full:
            manifest_full[r["ticker"]]["forward_return"] = r["forward_return"]
            manifest_full[r["ticker"]]["price_2025_05_15"] = r["price_2025_05_15"]
            if r.get("delisted_before_measurement"):
                manifest_full[r["ticker"]]["delisted_before_measurement"] = True

    (HERE / "tier3_agent_manifest.json").write_text(json.dumps(manifest_blinded, indent=2))
    (HERE / "_unblinded" / "tier3_agent_manifest_full.json").write_text(json.dumps(manifest_full, indent=2))

    n_ok = sum(1 for v in manifest_blinded.values() if v.get("cache_status") in ("cached", "downloaded"))
    print()
    print(f"OK: {n_ok}/{len(blinded)} have cached 10-K")
    bad = [(tk, v.get("cache_status")) for tk, v in manifest_blinded.items()
           if v.get("cache_status") not in ("cached", "downloaded")]
    if bad:
        print("Issues:")
        for tk, s in bad:
            print(f"  {tk}: {s}")


if __name__ == "__main__":
    main()
