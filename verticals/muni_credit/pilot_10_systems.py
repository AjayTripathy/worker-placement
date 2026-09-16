"""10-name hospital muni pilot — proof of concept.

For each of 10 large US hospital systems with known credit ratings:
  1. Search CMS HCRIS hospital cost reports by facility-name substring
  2. Pull operating margin trajectory across the system's CCNs
  3. Score our composite credit signal
  4. Compare to known Moody's/S&P explicit ratings
  5. Identify divergences

Output: data/pilot_10_results.json
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx

HERE = Path(__file__).parent
OUT = HERE / "outputs" / "pilot_10_results.json"
HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

# Known rating approximations as of late-2024/early-2025
# Sources: Moody's MIS, S&P Global Ratings publicly-issued rating actions
# Format: (system_name, search_substring, moodys, sp, fitch, notes)
SYSTEMS = [
    # (system_name, primary_search, alt_searches, moodys, sp, fitch, notes)
    ("Mayo Clinic",              ["Mayo Clinic"],                                 "Aa2",  "AA",   "AA",   "MN; AAA-tier academic medical"),
    ("Cleveland Clinic",         ["Cleveland Clinic"],                            "Aa2",  "AA",   "AA",  "OH; major academic"),
    ("Memorial Sloan Kettering", ["Memorial Hospital for Cancer", "Memorial Sloan-Kettering"], "Aa3",  "AA-",  "AA",   "NY; cancer-focused"),
    ("Northwell Health",         ["North Shore University Hospital", "Long Island Jewish"], "A3",   "A-",   "A",    "NY; rebranded from North Shore-LIJ"),
    ("Sutter Health",            ["Sutter"],                                       "A1",   "A+",   None,   "CA; large NorCal system"),
    ("Banner Health",            ["Banner"],                                       "A1",   "A+",   "A+",   "AZ; large SW system"),
    ("AdventHealth",             ["AdventHealth"],                                 "Aa3",  "AA-",  "AA-",  "FL; rebranded 2019 from Adventist"),
    ("CommonSpirit Health",      ["CommonSpirit", "Dignity Health", "CHI Health"], "Baa1", "BBB+", "BBB+", "IL; merger of Dignity + CHI"),
    ("Trinity Health",           ["Mercy Health", "Saint Joseph Mercy", "St Mary Mercy"],          "Aa3",  "AA-",  "AA-",  "MI; Trinity owns Mercy Health hospitals"),
    ("Providence St Joseph",     ["Providence St", "Providence Health", "St Joseph Health"], "A2",   "A+",   "AA-",  "WA; large Catholic-affiliated"),
]


def _rating_to_score(moodys: str | None, sp: str | None, fitch: str | None) -> tuple[int, str]:
    """Map letter ratings to a 0-100 score; return (score, consensus_letter)."""
    # Moody's-like → numeric (Aaa=100, Aaa=95, etc.)
    moody_map = {"Aaa": 100, "Aa1": 95, "Aa2": 92, "Aa3": 89,
                  "A1": 85, "A2": 82, "A3": 79,
                  "Baa1": 75, "Baa2": 72, "Baa3": 69,
                  "Ba1": 65, "Ba2": 62, "Ba3": 59,
                  "B1": 55, "B2": 52, "B3": 49}
    sp_map = {"AAA": 100, "AA+": 95, "AA": 92, "AA-": 89,
              "A+": 85, "A": 82, "A-": 79,
              "BBB+": 75, "BBB": 72, "BBB-": 69,
              "BB+": 65, "BB": 62, "BB-": 59,
              "B+": 55, "B": 52, "B-": 49}
    scores = []
    if moodys and moodys in moody_map: scores.append(moody_map[moodys])
    if sp and sp in sp_map: scores.append(sp_map[sp])
    if fitch and fitch in sp_map: scores.append(sp_map[fitch])
    avg = sum(scores) / len(scores) if scores else 0
    # Map back to consensus letter (use S&P scale)
    for letter, score in sorted(sp_map.items(), key=lambda x: -x[1]):
        if avg >= score:
            return int(avg), letter
    return int(avg), "B-"


def _search_cms_facilities(query: str) -> dict:
    """Search CMS HCRIS hospital + SNF datasets for facilities matching query.

    Hospital dataset column = 'Hospital Name'; SNF = 'Facility Name'.
    Hospital net income column = 'Net Income'; SNF = 'Net Income from service to patients'.
    """
    from verticals.public_co.m_sources.cms_cost_reports import DATASETS

    SCHEMA = {
        "hospital":    {"name_col": "Hospital Name",  "income_col": "Net Income"},
        "snf":         {"name_col": "Facility Name",  "income_col": "Net Income from service to patients"},
        "home_health": {"name_col": "Facility Name",  "income_col": "Net Income"},
    }

    out = {"hospital": [], "snf": [], "home_health": []}
    for ftype in ("hospital", "snf", "home_health"):
        uuid = DATASETS[ftype]
        name_col = SCHEMA[ftype]["name_col"]
        income_col = SCHEMA[ftype]["income_col"]
        try:
            with httpx.Client(headers=HEADERS, timeout=30) as c:
                r = c.get(f"https://data.cms.gov/data-api/v1/dataset/{uuid}/data",
                          params={
                              f"filter[{name_col}][condition][path]":     name_col,
                              f"filter[{name_col}][condition][operator]": "CONTAINS",
                              f"filter[{name_col}][condition][value]":    query,
                              "size": 200,
                          })
                if r.status_code != 200: continue
                rows = r.json()
                if not isinstance(rows, list): continue
                for row in rows:
                    ccn = row.get("Provider CCN") or row.get("CCN")
                    if not ccn: continue
                    out[ftype].append({
                        "ccn":          str(ccn),
                        "facility":     row.get(name_col),
                        "state":        row.get("State Code"),
                        "city":         row.get("City"),
                        "fy_end":       row.get("Fiscal Year End Date"),
                        "net_pat_rev":  row.get("Net Patient Revenue"),
                        "net_income":   row.get(income_col),
                        "operating_expense": row.get("Less Total Operating Expense"),
                    })
        except Exception:
            continue
    return out


def _safe_float(v):
    try:
        return float(v) if v not in (None, "") else None
    except: return None


def _compute_margin(rows: list) -> tuple[float | None, float, int]:
    """NPR-weighted operating margin = (NPR - OpExp) / NPR.

    Prefer (NPR - Less Total Operating Expense) over Net Income because
    Net Income includes non-operating items (investment gains, etc.).
    Fall back to Net Income / NPR if OpExp missing.
    """
    contribs = []
    weights = []
    for r in rows:
        npr = _safe_float(r.get("net_pat_rev"))
        if npr is None or npr <= 0: continue
        opex = _safe_float(r.get("operating_expense"))
        ni = _safe_float(r.get("net_income"))
        if opex is not None:
            operating_income = npr - opex
        elif ni is not None:
            operating_income = ni
        else:
            continue
        contribs.append(operating_income)
        weights.append(npr)
    if not weights: return None, 0, 0
    return sum(contribs) / sum(weights) * 100, sum(weights), len(weights)


def _score_to_implied_rating(margin_pct: float | None, days_cash_proxy: float | None = None) -> tuple[int, str]:
    """Map operating-margin signal to implied letter rating + numeric score."""
    if margin_pct is None: return 0, "UNVERIFIABLE"
    # Simple single-axis mapping (full MVP would be 4-axis)
    if margin_pct >= 5: return 92, "AA"
    if margin_pct >= 2: return 85, "A+"
    if margin_pct >= 0: return 82, "A"
    if margin_pct >= -3: return 75, "BBB+"
    if margin_pct >= -6: return 72, "BBB"
    if margin_pct >= -10: return 65, "BB+"
    return 55, "B+"


def run_one(name: str, queries: list[str], moodys: str, sp: str, fitch: str | None, notes: str) -> dict:
    print(f"\n=== {name} (queries={queries}) ===", file=sys.stderr)
    # Merge facility lists across all query variants, dedupe by CCN
    matches = {"hospital": [], "snf": [], "home_health": []}
    seen_ccns_per_type = {"hospital": set(), "snf": set(), "home_health": set()}
    for q in queries:
        m = _search_cms_facilities(q)
        for ftype in matches:
            for row in m[ftype]:
                ccn = row["ccn"]
                if ccn not in seen_ccns_per_type[ftype]:
                    seen_ccns_per_type[ftype].add(ccn)
                    matches[ftype].append(row)
    n_hospitals = len(matches["hospital"])
    n_snf = len(matches["snf"])
    print(f"  CMS HCRIS matches: {n_hospitals} hospital, {n_snf} SNF, {len(matches['home_health'])} HH",
          file=sys.stderr)

    # Group hospital facilities by most-recent fiscal year
    hosp = matches["hospital"]
    if hosp:
        # Take most recent FY per CCN
        latest_per_ccn = {}
        for r in hosp:
            ccn = r["ccn"]
            fy = r.get("fy_end") or ""
            if ccn not in latest_per_ccn or fy > latest_per_ccn[ccn].get("fy_end",""):
                latest_per_ccn[ccn] = r
        latest_rows = list(latest_per_ccn.values())
        margin_latest, total_npr, n_facil = _compute_margin(latest_rows)
        # Prior year for trend
        prior_rows = [r for r in hosp if r["ccn"] in latest_per_ccn
                       and r["fy_end"] != latest_per_ccn[r["ccn"]].get("fy_end")]
        margin_prior, _, _ = _compute_margin(prior_rows)
        margin_delta = (margin_latest - margin_prior) if (margin_latest is not None and margin_prior is not None) else None
    else:
        margin_latest = margin_prior = margin_delta = None
        total_npr = 0
        n_facil = 0

    # Rating
    rating_score, rating_consensus = _rating_to_score(moodys, sp, fitch)
    our_score, our_implied = _score_to_implied_rating(margin_latest)
    divergence_notches = (our_score - rating_score) / 3  # ~3 score points per notch

    return {
        "system": name,
        "search_queries": queries,
        "notes": notes,
        "ratings": {
            "moodys": moodys, "sp": sp, "fitch": fitch,
            "score": rating_score, "consensus_letter": rating_consensus,
        },
        "cms_data": {
            "n_hospital_facilities": n_facil,
            "total_net_patient_rev_latest_fy": round(total_npr, 0) if total_npr else 0,
            "weighted_operating_margin_latest_pct": round(margin_latest, 2) if margin_latest is not None else None,
            "weighted_operating_margin_prior_pct": round(margin_prior, 2) if margin_prior is not None else None,
            "margin_yoy_delta_pp": round(margin_delta, 2) if margin_delta is not None else None,
        },
        "our_score": {
            "score": our_score,
            "implied_letter": our_implied,
        },
        "divergence": {
            "notches": round(divergence_notches, 1),
            "signal": (
                "STRONG_BUY" if divergence_notches >= 2 else
                "WEAK_BUY"   if divergence_notches >= 0.5 else
                "CONSENSUS"  if abs(divergence_notches) < 0.5 else
                "WEAK_SELL"  if divergence_notches > -2 else
                "STRONG_SELL"
            ),
        },
    }


def main():
    t0 = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(run_one, *s): s[0] for s in SYSTEMS}
        for fut in as_completed(futures):
            results.append(fut.result())

    # Sort by divergence (most under-rated first)
    results.sort(key=lambda r: -r["divergence"]["notches"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "run_date": "2026-05-27",
        "n_systems": len(results),
        "elapsed_seconds": round(time.time() - t0, 1),
        "results": results,
    }, indent=2, default=str))

    print(f"\n{'='*100}", file=sys.stderr)
    print(f"DONE in {time.time()-t0:.1f}s — {len(results)} systems analyzed", file=sys.stderr)
    print(f"{'='*100}\n", file=sys.stderr)

    # Print summary table
    print(f"{'System':<28} {'Explicit':<10} {'Our':<10} {'Margin%':<10} {'YoY pp':<8} {'Divergence':<14} {'Signal':<14}")
    print("-" * 110)
    for r in results:
        m = r["cms_data"]["weighted_operating_margin_latest_pct"]
        d = r["cms_data"]["margin_yoy_delta_pp"]
        print(f"{r['system']:<28} "
              f"{r['ratings']['consensus_letter']:<10} "
              f"{r['our_score']['implied_letter']:<10} "
              f"{f'{m:+.2f}' if m is not None else 'n/a':<10} "
              f"{f'{d:+.2f}' if d is not None else 'n/a':<8} "
              f"{r['divergence']['notches']:+.1f} notch{'':<6} "
              f"{r['divergence']['signal']}")


if __name__ == "__main__":
    main()
