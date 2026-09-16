"""
End-to-end cohort filings refresh — always pulls current EDGAR data, picks
the right filing, validates freshness, and writes a `current_filing.json`
that the subagent prompt builder reads directly.

This replaces the fragile prior flow where:
  - `filings_index.json` could be stale relative to the cutoff
  - `filings/` directory could hold old downloads from prior runs
  - The subagent silently scored whichever file it found on disk
  - Nothing checked that the picked filing was actually current

Usage:
    python3 -m verticals.public_co.scripts.refresh_cohort_filings \\
        --cutoff 2026-05-20

    # Or specific tickers / cohorts:
    python3 -m verticals.public_co.scripts.refresh_cohort_filings \\
        --cutoff 2026-05-20 --tickers AVAV LMT NOC

    # Or different staleness tolerance:
    python3 -m verticals.public_co.scripts.refresh_cohort_filings \\
        --cutoff 2026-05-20 --max-age-months 18

For each ticker:
  1. Hits EDGAR submissions API live (no cache)
  2. Picks the most-recent-pre-cutoff filing, preferring 10-K > 20-F > 40-F,
     falling back to 10-Q only if no annual form is within tolerance
  3. ASSERTS the picked filing's filing_date is within max-age-months of cutoff.
     If not: prints a loud failure for this ticker, exits non-zero at the end.
  4. Downloads filing text to data/<ticker>/filings/<acc>_<form>.txt
  5. Rewrites data/<ticker>/filings_index.json with the full pre-cutoff list
  6. Writes data/<ticker>/current_filing.json — the validated pick + path + age
  7. Emits a manifest summary at the end

Exit codes:
  0 = every ticker validated and downloaded
  1 = one or more tickers had no acceptable filing within max-age-months
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from verticals.public_co.edgar import fetch_filing_clean, list_filings

HERE = Path(__file__).resolve().parent
PUBLIC_CO = HERE.parent
DATA = PUBLIC_CO / "data"

PRIMARY_ANNUAL_FORMS = ("10-K", "20-F", "40-F")
FALLBACK_FORMS = ("10-Q",)


def _months_between(a_iso: str, b_iso: str) -> float:
    a = datetime.fromisoformat(a_iso)
    b = datetime.fromisoformat(b_iso)
    return abs((b - a).days) / 30.4375


def _pick(filings: list[dict], cutoff: str, max_age_months: float
          ) -> tuple[dict | None, bool, str]:
    """Pick the most-recent-pre-cutoff filing within max-age-months.

    Returns (picked, used_fallback, reason). picked is None if nothing qualifies.
    """
    pre = [f for f in filings if f["filing_date"] <= cutoff]
    pre.sort(key=lambda r: r["filing_date"], reverse=True)

    annuals = [f for f in pre if f["form"] in PRIMARY_ANNUAL_FORMS]
    if annuals:
        latest_annual = annuals[0]
        age = _months_between(latest_annual["filing_date"], cutoff)
        if age <= max_age_months:
            return latest_annual, False, f"primary {latest_annual['form']} within tolerance"

    fallbacks = [f for f in pre if f["form"] in FALLBACK_FORMS]
    if fallbacks:
        latest_fb = fallbacks[0]
        age = _months_between(latest_fb["filing_date"], cutoff)
        if age <= max_age_months:
            return latest_fb, True, f"fallback {latest_fb['form']} ({age:.1f}mo) — no annual within tolerance"

    if annuals:
        a = annuals[0]
        age = _months_between(a["filing_date"], cutoff)
        return None, False, (
            f"most recent annual {a['form']} dated {a['filing_date']} is "
            f"{age:.1f} months old — exceeds tolerance of {max_age_months} months"
        )
    return None, False, "no pre-cutoff filings found at all"


def refresh_one(ticker: str, cik: str, cutoff: str, max_age_months: float,
                 force: bool = False) -> dict:
    """Refresh one ticker. Returns a manifest entry."""
    out_dir = DATA / ticker.lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    filings_dir = out_dir / "filings"
    filings_dir.mkdir(exist_ok=True)

    try:
        company_name, rows = list_filings(cik)
    except Exception as e:
        return {"ticker": ticker, "status": "edgar_fetch_failed", "error": str(e)}

    pre_cutoff = [r for r in rows if r["filing_date"] <= cutoff]
    for r in pre_cutoff:
        r["cik"] = cik
        r["company"] = company_name

    (out_dir / "filings_index.json").write_text(json.dumps(pre_cutoff, indent=2))

    picked, used_fallback, reason = _pick(pre_cutoff, cutoff, max_age_months)
    if picked is None:
        # Write a marker explaining the failure and bail
        (out_dir / "current_filing.json").write_text(json.dumps({
            "ticker": ticker, "cik": cik, "cutoff": cutoff,
            "status": "no_acceptable_filing", "reason": reason,
        }, indent=2))
        return {"ticker": ticker, "status": "no_acceptable_filing", "reason": reason}

    # Download the picked filing (idempotent unless --force)
    form_safe = picked["form"].replace("/", "_").replace(" ", "_")
    out_path = filings_dir / f"{picked['accession']}_{form_safe}.txt"
    downloaded = False
    if not out_path.exists() or out_path.stat().st_size < 1000 or force:
        text = fetch_filing_clean(cik, picked["accession"], picked["primary_document"])
        if not text:
            return {"ticker": ticker, "status": "download_failed",
                    "picked": picked, "out_path": str(out_path)}
        out_path.write_text(text)
        downloaded = True

    age_days = (datetime.fromisoformat(cutoff) -
                 datetime.fromisoformat(picked["filing_date"])).days

    current_filing = {
        "ticker": ticker,
        "cik": cik,
        "company": company_name,
        "cutoff": cutoff,
        "picked": picked,
        "filing_path": str(out_path),
        "filing_form": picked["form"],
        "filing_date": picked["filing_date"],
        "filing_age_days": age_days,
        "fallback_used": used_fallback,
        "max_age_months_allowed": max_age_months,
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
        "selection_reason": reason,
    }
    (out_dir / "current_filing.json").write_text(json.dumps(current_filing, indent=2))

    return {
        "ticker": ticker, "status": "ok",
        "form": picked["form"], "filing_date": picked["filing_date"],
        "age_days": age_days, "downloaded": downloaded,
        "fallback_used": used_fallback, "n_chars_on_disk": out_path.stat().st_size,
    }


def _resolve_cohort(cohort_module: str) -> list[tuple[str, str]]:
    """Import COHORT from given module path, return list of (ticker, cik)."""
    mod = importlib.import_module(cohort_module)
    pairs = []
    for member in getattr(mod, "COHORT", []):
        try:
            cik = member.cik  # property that calls cik_for()
        except Exception as e:
            print(f"  ! {member.ticker}: cik resolution failed — {e}", file=sys.stderr)
            continue
        pairs.append((member.ticker.upper(), cik))
    return pairs


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cutoff", required=True, help="ISO date, e.g. 2026-05-20")
    ap.add_argument("--cohort", default="verticals.public_co.jbook_exposure_cohort",
                     help="Cohort module path (default jbook_exposure_cohort)")
    ap.add_argument("--tickers", nargs="*",
                     help="Explicit tickers (resolves CIK from cohort module)")
    ap.add_argument("--max-age-months", type=float, default=14.0,
                     help="Maximum months between filing_date and cutoff (default 14)")
    ap.add_argument("--force", action="store_true",
                     help="Re-download even if file already on disk")
    ap.add_argument("--sleep", type=float, default=0.2,
                     help="Seconds between EDGAR calls (default 0.2)")
    args = ap.parse_args()

    cohort = _resolve_cohort(args.cohort)
    cik_map = {t: c for t, c in cohort}

    if args.tickers:
        work = [(t.upper(), cik_map.get(t.upper(), "")) for t in args.tickers]
        missing = [t for t, c in work if not c]
        if missing:
            print(f"ERROR: tickers not in {args.cohort}: {missing}", file=sys.stderr)
            sys.exit(2)
    else:
        work = cohort

    print(f"\nRefreshing {len(work)} tickers against cutoff {args.cutoff}",
           file=sys.stderr)
    print(f"  max-age-months: {args.max_age_months}", file=sys.stderr)
    print(f"  force redownload: {args.force}\n", file=sys.stderr)

    manifest = []
    failures = []
    for tk, cik in work:
        r = refresh_one(tk, cik, args.cutoff, args.max_age_months, force=args.force)
        manifest.append(r)
        st = r["status"]
        if st == "ok":
            dl = "DL" if r.get("downloaded") else "  "
            fb = " [FALLBACK]" if r.get("fallback_used") else ""
            print(f"  {tk:<7} {dl}  {r['form']:<5} {r['filing_date']}  "
                  f"age={r['age_days']}d{fb}", file=sys.stderr)
        else:
            failures.append((tk, st, r.get("reason") or r.get("error") or ""))
            print(f"  {tk:<7} !!  {st}: {r.get('reason') or r.get('error')}",
                  file=sys.stderr)
        time.sleep(args.sleep)

    manifest_path = DATA / "_jbook_exposure_cohort" / f"refresh_manifest_{args.cutoff}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({
        "cutoff": args.cutoff,
        "max_age_months": args.max_age_months,
        "n_tickers": len(work),
        "n_ok": sum(1 for r in manifest if r["status"] == "ok"),
        "n_failed": len(failures),
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
        "results": manifest,
    }, indent=2))

    print(f"\n{'='*70}", file=sys.stderr)
    print(f"Manifest: {manifest_path}", file=sys.stderr)
    print(f"OK: {sum(1 for r in manifest if r['status'] == 'ok')}/{len(work)}",
           file=sys.stderr)
    if failures:
        print(f"\nFAILURES ({len(failures)}):", file=sys.stderr)
        for tk, st, reason in failures:
            print(f"  {tk}: {st} — {reason}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
