"""Systematic forward-catalyst sweep — reproducible replacement for the
hand-curated _SPECS list in live_catalysts.py.

Two public registries, GET-only:
  1. ClinicalTrials.gov v2 — every industry-sponsored Phase 3 (incl. Phase 2/3)
     interventional trial whose PRIMARY COMPLETION DATE falls in a forward window
     and whose status is still open/unreported. That set IS the universe of
     upcoming pivotal readouts; no analyst hand-picking.
  2. SEC EDGAR company_tickers.json — maps a CT.gov lead-sponsor NAME to a
     US-listed TICKER + CIK, so we keep only names the honesty screen can run on
     (it needs an EDGAR CIK for the 8-K corpus). Non-US / private sponsors fall
     out here, by design.

PDUFA / regulatory decisions are intentionally OUT of scope: this sweeps trial
READOUTS only (the strong fit for the honesty screen).

Run: python3 -m verticals.public_biotech.catalyst_sweep [--start 2026-06-01]
     [--end 2026-12-31] [--phase2]
Prints two tables to stdout: (A) resolved US-listed readouts, and (B) the diff —
readouts NOT already in live_catalysts._SPECS.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

import httpx

_HEADERS = {"User-Agent": "signalos research 4tripathy@gmail.com"}
_V2 = "https://clinicaltrials.gov/api/v2/studies"
_EDGAR_TICKERS = "https://www.sec.gov/files/company_tickers.json"

# Open / not-yet-reported statuses. A readout is "upcoming" if the trial is still
# running or just finished but has not posted results.
_OPEN_STATUS = ("RECRUITING", "ACTIVE_NOT_RECRUITING",
                "ENROLLING_BY_INVITATION", "COMPLETED")

_FIELDS = ",".join([
    "NCTId", "BriefTitle", "Phase", "OverallStatus", "Condition",
    "InterventionName", "InterventionType", "LeadSponsorName", "LeadSponsorClass",
    "PrimaryCompletionDate", "EnrollmentCount",
])

# An investable trial catalyst is a therapeutic readout: at least one DRUG /
# BIOLOGICAL / GENETIC intervention. Pure DEVICE / DIETARY_SUPPLEMENT / consumer
# (toothpaste, mouthwash) and BEHAVIORAL/PROCEDURE-only studies are not.
_DRUG_TYPES = {"DRUG", "BIOLOGICAL", "GENETIC"}

# Conditions/interventions that pass the type gate but aren't a value-inflection
# catalyst: PK/PD/bioequivalence bridging studies, healthy-volunteer work, and
# consumer/oral-care endpoints (a large-cap CPG running a "Phase 3" toothpaste).
_NONCATALYST_RE = re.compile(
    r"pharmacokinetic|pharmacodynamic|bioequivalence|bioavailability|"
    r"healthy (volunteer|subject|participant)|oral malodor|dentin|toothpaste|"
    r"mouthwash|halitosis|gingivitis|dental plaque|sunscreen|cosmetic",
    re.I)

# Market-cap buckets (USD). Large-caps are excluded from the binary-catalyst
# screen: a single readout is immaterial to a >$10B issuer's price.
_CAP_LARGE = 10e9
_CAP_MID = 2e9
_CAP_SMALL = 300e6

# Corporate-suffix / filler tokens stripped before matching a CT.gov sponsor name
# against an EDGAR company name. Kept deliberately small: stripping descriptive
# words like "pharmaceuticals"/"therapeutics" would collide distinct issuers.
_SUFFIX = {
    "inc", "incorporated", "corp", "corporation", "co", "company", "ltd",
    "limited", "plc", "llc", "lp", "sa", "ag", "nv", "ab", "as", "oyj",
    "holdings", "holding", "group", "the", "and",
}


def _norm(name: str) -> str:
    toks = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower()).split()
    return " ".join(t for t in toks if t not in _SUFFIX)


def fetch_forward_trials(start: str, end: str, *, include_phase2: bool = False,
                         verbose: bool = True) -> list[dict]:
    """All industry-sponsored pivotal trials with primary completion in [start,end]."""
    phase = "(PHASE3 OR PHASE2)" if include_phase2 else "PHASE3"
    adv = (f"AREA[StudyType]INTERVENTIONAL AND AREA[Phase]{phase} "
           f"AND AREA[PrimaryCompletionDate]RANGE[{start},{end}] "
           f"AND AREA[LeadSponsorClass]INDUSTRY")
    out: list[dict] = []
    token = None
    with httpx.Client(timeout=60, headers=_HEADERS) as c:
        while True:
            params = {"filter.advanced": adv, "fields": _FIELDS,
                      "pageSize": "200", "format": "json"}
            if token:
                params["pageToken"] = token
            r = c.get(_V2, params=params)
            r.raise_for_status()
            d = r.json()
            for s in d.get("studies", []):
                out.append(_flatten(s))
            token = d.get("nextPageToken")
            if verbose:
                print(f"  ...{len(out)} trials", file=sys.stderr)
            if not token:
                break
    return out


def _flatten(study: dict) -> dict:
    p = study.get("protocolSection", {})
    idm = p.get("identificationModule", {})
    dm = p.get("designModule", {})
    stm = p.get("statusModule", {})
    spm = p.get("sponsorCollaboratorsModule", {})
    lead = (spm.get("leadSponsor", {}) or {})
    return {
        "nct": idm.get("nctId", ""),
        "title": idm.get("briefTitle", ""),
        "phase": "/".join(dm.get("phases", []) or []),
        "status": stm.get("overallStatus", ""),
        "pcd": (stm.get("primaryCompletionDateStruct", {}) or {}).get("date", ""),
        "enroll": (dm.get("enrollmentInfo", {}) or {}).get("count", ""),
        "conditions": (p.get("conditionsModule", {}) or {}).get("conditions", []),
        "interventions": [i.get("name", "") for i in
                          (p.get("armsInterventionsModule", {}) or {}).get("interventions", [])],
        "intervention_types": [i.get("type", "") for i in
                          (p.get("armsInterventionsModule", {}) or {}).get("interventions", [])],
        "sponsor": lead.get("name", ""),
    }


def is_therapeutic_catalyst(t: dict) -> bool:
    """Drug/biologic readout, not a device/consumer/PK/healthy-volunteer study."""
    if not (set(t.get("intervention_types", [])) & _DRUG_TYPES):
        return False
    hay = " ".join(t.get("conditions", []) + t.get("interventions", []))
    return not _NONCATALYST_RE.search(hay)


def load_edgar_map() -> dict[str, dict]:
    """normalized-company-name -> {ticker, cik, name}. US-listed issuers only."""
    with httpx.Client(timeout=60, headers=_HEADERS) as c:
        r = c.get(_EDGAR_TICKERS)
        r.raise_for_status()
        raw = r.json()
    m: dict[str, dict] = {}
    for row in raw.values():
        norm = _norm(row["title"])
        if not norm:
            continue
        # First ticker wins; EDGAR lists the primary common share first.
        m.setdefault(norm, {"ticker": row["ticker"],
                            "cik": str(row["cik_str"]).zfill(10),
                            "name": row["title"]})
    return m


def resolve_sponsor(sponsor: str, edgar: dict[str, dict]) -> dict | None:
    """Match a CT.gov sponsor to a US-listed issuer. Exact normalized match, or a
    containment match where the shorter normalized name is a full token-prefix of
    the longer — strict enough to avoid 'Bristol' vs 'Bristol Myers' type slips."""
    key = _norm(sponsor)
    if not key:
        return None
    if key in edgar:
        return edgar[key]
    kt = key.split()
    for ek, ev in edgar.items():
        et = ek.split()
        if not et:
            continue
        n = min(len(kt), len(et))
        if n >= 1 and kt[:n] == et[:n] and abs(len(kt) - len(et)) <= 1:
            return ev
    return None


def _price(ticker: str) -> float | None:
    try:
        with httpx.Client(timeout=20, headers={"User-Agent": "Mozilla/5.0"}) as c:
            r = c.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}")
            meta = r.json()["chart"]["result"][0]["meta"]
            return meta.get("regularMarketPrice")
    except Exception:
        return None


def _shares(cik: str) -> float | None:
    url = (f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}"
           f"/dei/EntityCommonStockSharesOutstanding.json")
    try:
        with httpx.Client(timeout=30, headers=_HEADERS) as c:
            r = c.get(url)
            if r.status_code != 200:
                return None
            units = r.json()["units"]["shares"]
            return sorted(units, key=lambda x: x["end"])[-1]["val"]
    except Exception:
        return None


def market_cap(ticker: str, cik: str) -> float | None:
    p, s = _price(ticker), _shares(cik)
    return p * s if (p and s) else None


def _cap_bucket(cap: float | None) -> str:
    if cap is None:
        return "?"
    if cap >= _CAP_LARGE:
        return "large"
    if cap >= _CAP_MID:
        return "mid"
    if cap >= _CAP_SMALL:
        return "small"
    return "micro"


def _existing_companies() -> set[str]:
    from .live_catalysts import LIVE_CASES
    return {_norm(c.company) for c in LIVE_CASES.values()}


def _existing_ncts() -> set[str]:
    from .live_catalysts import LIVE_CASES
    return {n for c in LIVE_CASES.values() for n in c.nct_ids}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-06-01")
    ap.add_argument("--end", default="2026-12-31")
    ap.add_argument("--phase2", action="store_true",
                    help="also include pure Phase 2 (noisier; default Phase 3 + 2/3 only)")
    ap.add_argument("--max-cap", type=float, default=10.0,
                    help="exclude issuers with market cap above this many $B (default 10)")
    ap.add_argument("--no-cap", action="store_true",
                    help="skip market-cap fetch (therapeutic filter only)")
    args = ap.parse_args()

    print(f"[sweep] CT.gov industry pivotal readouts, pcd {args.start}..{args.end}",
          file=sys.stderr)
    trials = fetch_forward_trials(args.start, args.end, include_phase2=args.phase2)

    # Therapeutic filter: drug/biologic readouts, not device/consumer/PK studies.
    therapeutic = [t for t in trials if is_therapeutic_catalyst(t)]
    print(f"[sweep] {len(trials)} trials -> {len(therapeutic)} therapeutic; "
          f"loading EDGAR ticker map", file=sys.stderr)
    edgar = load_edgar_map()

    # Resolve to US-listed issuers, keep the earliest-pcd trial per ticker.
    by_ticker: dict[str, dict] = {}
    for t in therapeutic:
        hit = resolve_sponsor(t["sponsor"], edgar)
        if not hit:
            continue
        t = {**t, "ticker": hit["ticker"], "cik": hit["cik"], "issuer": hit["name"]}
        cur = by_ticker.get(hit["ticker"])
        if cur is None or (t["pcd"] and t["pcd"] < cur["pcd"]):
            by_ticker[hit["ticker"]] = t

    rows = sorted(by_ticker.values(), key=lambda r: r["pcd"])

    # Attach market cap (price x shares) unless suppressed.
    if not args.no_cap:
        print(f"[sweep] fetching market caps for {len(rows)} issuers", file=sys.stderr)
        for r in rows:
            r["mktcap"] = market_cap(r["ticker"], r["cik"])
            r["bucket"] = _cap_bucket(r["mktcap"])
    else:
        for r in rows:
            r["mktcap"], r["bucket"] = None, "?"

    have_co = _existing_companies()
    have_nct = _existing_ncts()

    def _is_new(r: dict) -> bool:
        return _norm(r["issuer"]) not in have_co and r["nct"] not in have_nct

    def _capB(r: dict) -> str:
        return f"{r['mktcap']/1e9:5.1f}B" if r.get("mktcap") else "  ?  "

    # Require a KNOWN cap under the ceiling. A None cap is almost always a foreign
    # ADR (no SEC shares-outstanding concept) — which is also a 6-K filer the 8-K
    # honesty screen can't run on, so excluding it from the screenable set is
    # correct on both counts.
    cap_ceiling = args.max_cap * 1e9
    screenable = [r for r in rows if r.get("mktcap") and r["mktcap"] < cap_ceiling]

    print(f"\n==== (A) THERAPEUTIC FORWARD READOUTS, US-LISTED  (n={len(rows)}) ====")
    for r in rows:
        tag = "NEW" if _is_new(r) else "   "
        cond = "; ".join(r["conditions"][:2])[:40]
        print(f"  {tag} {r['ticker']:<6} {_capB(r)} {r['bucket']:<5} {r['pcd']:<10} "
              f"{r['nct']:<12} {r['issuer'][:22]:<22} {cond}")

    new_screen = [r for r in screenable if _is_new(r)]
    print(f"\n==== (B) SCREENABLE BINARIES  (cap<${args.max_cap:.0f}B, NEW, "
          f"n={len(new_screen)}) ====")
    for r in new_screen:
        cond = "; ".join(r["conditions"][:2])[:44]
        intr = "; ".join(r["interventions"][:2])[:32]
        print(f"  {r['ticker']:<6} {_capB(r)} {r['bucket']:<5} {r['pcd']:<10} "
              f"{r['nct']:<12} n={str(r['enroll']):<6} {r['issuer'][:22]:<22}\n"
              f"         {cond}  |  {intr}")

    json.dump({"all": rows, "screenable_new": new_screen},
              open("/tmp/catalyst_sweep.json", "w"), indent=2, default=str)
    print(f"\n[sweep] wrote /tmp/catalyst_sweep.json", file=sys.stderr)


if __name__ == "__main__":
    main()
