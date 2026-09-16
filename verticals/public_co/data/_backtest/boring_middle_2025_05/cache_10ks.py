"""Cache pre-2025-05-15 10-K filings for each Tier 2 universe name.

Uses verticals.public_co.edgar.pull to download the most recent 10-K
filed BEFORE 2025-05-15 for each ticker. Builds the agent_manifest
mapping each ticker to its CIK + cached filing path + filing date.

Outputs:
  - verticals/public_co/data/<ticker_lower>/filings_2025_05_15/<accession>_10K.txt  (cached)
  - tier2_agent_manifest.json  (blinded — agent-facing)
  - _unblinded/tier2_agent_manifest_full.json  (with forward_return joined — synthesis only)

Run:
    python3 verticals/public_co/data/_backtest/boring_middle_2025_05/cache_10ks.py
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
PUBLIC_CO = HERE.parents[2]
DATA = PUBLIC_CO / "data"

# Import the existing EDGAR helper
sys.path.insert(0, str(HERE.parents[4]))  # signalos repo root
from verticals.public_co import edgar  # noqa: E402


CUTOFF = "2025-05-15"


def latest_10k_pre_cutoff(cik: str):
    """Return the most recent 10-K filing dict (filed_date <= CUTOFF), or None."""
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
    out_dir = DATA / tkl / "filings_2025_05_15"
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
    blinded_ts = json.loads((HERE / "tier2_test_set.json").read_text())

    print(f"Caching 10-Ks for {len(blinded_ts)} Tier 2 names...")
    print()

    manifest_blinded = {}
    manifest_full = {}
    for i, r in enumerate(blinded_ts):
        tk = r["ticker"]
        cik = r["cik"]
        result = cache_one(tk, cik)
        entry_blinded = {
            "company": r.get("company", ""),
            "cik": cik,
            "sector": r.get("sector", ""),
            "industry": r.get("industry", ""),
            "drawdown_2025_05_15": r["drawdown_2025_05_15"],
            "price_2025_05_15": r["price_2025_05_15"],
            "group": "boring_middle",
            **{k: v for k, v in result.items() if k != "status"},
            "cache_status": result["status"],
        }
        manifest_blinded[tk] = entry_blinded
        manifest_full[tk] = {**entry_blinded}  # forward_return joined below

        status_tag = result["status"]
        size_tag = f' {result.get("bytes", 0)//1024}KB' if result.get("bytes") else ''
        print(f"  [{i+1:>2}/{len(blinded_ts)}] {tk:6}  cik={cik}  {status_tag}{size_tag}")
        time.sleep(0.15)

    # Join forward_return into the unblinded manifest
    unblinded_ts = json.loads((HERE / "_unblinded" / "tier2_test_set.json").read_text())
    for r in unblinded_ts:
        if r["ticker"] in manifest_full:
            manifest_full[r["ticker"]]["forward_return"] = r["forward_return"]
            manifest_full[r["ticker"]]["price_2026_05_15"] = r["price_2026_05_15"]

    (HERE / "tier2_agent_manifest.json").write_text(json.dumps(manifest_blinded, indent=2))
    (HERE / "_unblinded" / "tier2_agent_manifest_full.json").write_text(json.dumps(manifest_full, indent=2))

    # Summary
    n_ok = sum(1 for v in manifest_blinded.values() if v["cache_status"] in ("cached", "downloaded"))
    print()
    print(f"OK: {n_ok}/{len(blinded_ts)} have cached 10-K")
    bad = [(tk, v["cache_status"]) for tk, v in manifest_blinded.items()
           if v["cache_status"] not in ("cached", "downloaded")]
    if bad:
        print("Issues:")
        for tk, s in bad:
            print(f"  {tk}: {s}")


if __name__ == "__main__":
    main()
