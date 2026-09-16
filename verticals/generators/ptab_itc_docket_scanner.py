"""ptab_itc_docket_scanner — Stage 0b INFO/LATENCY: the patent-validity & tariff-ruling docket nowcast.

THESIS (INFO-class, latency edge): two administrative dockets move single small caps on a PUBLISHED
calendar the market doesn't price until the press release — because nobody reads PTAB / ITC.

  LEG 1 — PTAB (patent VALIDITY).  A petitioner files an inter-partes / post-grant review (IPR/PGR)
     against a patent. When the Board INSTITUTES, the statute (35 U.S.C. §316(a)(11)) requires a
     FINAL WRITTEN DECISION within ~12 months of institution (18 months max for good cause). That FWD
     confirms or kills the patent's claims — a binary that re-rates a one-patent small cap. The
     institution date is public; the FWD-due window is therefore a KNOWN forward date the tape ignores.

  LEG 2 — ITC Section 337 (tariff / import EXCLUSION).  A complainant alleges infringing imports under
     §337 of the Tariff Act of 1930. Institution starts a ~16-18 month clock to a final determination;
     a violation finding yields a Limited Exclusion Order / cease-and-desist that can bar a respondent's
     product from the U.S. — again a binary on a published docket. Institution notices (docket 337-TA-XXXX,
     complainant, patents, sometimes respondents) are published in the Federal Register.

The edge is LATENCY, not prediction: the docket DATE is public and un-priced. Outcomes are ~coin-flip,
so this is an INFO generator that TIMES the catalyst and NAMES the tradeable party — sizing is a
convexity/defined-risk decision downstream, never a directional call here.

CATALYST-IDENTITY DISCIPLINE: every row binds to the SPECIFIC docket number (337-TA-#### or the PTAB
IPR/PGR trial number). We do NOT mis-bind a ruling to a company's "flagship" case — the party names come
straight from the docket record.

DATA SOURCES (all keyless except PTAB, see caveats):
  · ITC  — Federal Register API (federalregister.gov, keyless, reliable). Real 337-TA institution notices.
  · PTAB — USPTO Open Data Portal PTAB Trials API (api.uspto.gov). As of 2026-06 the ODP requires a (free,
           self-serve) API key; set env USPTO_ODP_KEY to enable this leg. Without it the PTAB leg reports
           UNAVAILABLE honestly — the legacy keyless developer.uspto.gov PTAB API was decommissioned.

    python3 verticals/generators/ptab_itc_docket_scanner.py
Writes data/PTAB_ITC_DOCKET.json. READ-ONLY — never an order. NO fabricated dockets/dates (real API data
only; anything the API can't confirm is marked UNVERIFIABLE / estimated-window).
"""
from __future__ import annotations

import datetime
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "PTAB_ITC_DOCKET.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com", "Accept": "application/json"}

FR_API = "https://www.federalregister.gov/api/v1/documents.json"
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
ODP_PTAB = "https://api.uspto.gov/api/v1/patent/trials/proceedings/search"
ODP_KEY = os.environ.get("USPTO_ODP_KEY", "").strip()

# statutory clocks (days). PTAB: FWD due ~12mo from institution, 18mo hard cap.
PTAB_FWD_DAYS = 365
PTAB_FWD_MAX_DAYS = 548
# ITC §337: median time-to-final-determination historically ~16-18mo from institution; the ALJ sets the
# exact "target date" ~45d post-institution. We estimate a WINDOW and mark the exact date UNVERIFIABLE.
ITC_TARGET_DAYS_LO = 480   # ~16mo
ITC_TARGET_DAYS_HI = 550   # ~18mo

IMMINENT_DAYS = 45         # 0-45d = imminent bucket
UPCOMING_DAYS = 180        # 46-180d = upcoming bucket


# ------------------------------------------------------------------ http
def _get(url, headers=None, timeout=30):
    try:
        req = urllib.request.Request(url, headers=headers or HDRS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except Exception as e:
        return {"_error": repr(e)[:200]}


# ------------------------------------------------------------------ ticker map (fuzzy party -> listed ticker)
_STOP = {"inc", "incorporated", "corp", "corporation", "co", "company", "llc", "lp", "ltd",
         "limited", "plc", "holdings", "holding", "group", "technologies", "technology",
         "the", "of", "and", "systems", "labs", "laboratories", "sa", "ag", "nv", "gmbh",
         "international", "industries", "industry", "usa", "america", "solutions", "networks",
         "communications", "semiconductor", "pharmaceuticals", "pharma", "therapeutics", "bio"}


def _norm(name: str) -> str:
    n = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower())
    n = re.sub(r"\s+", " ", n).strip()
    return n


def _tokens(name: str) -> set:
    return {t for t in _norm(name).split() if t and t not in _STOP and len(t) > 1}


def _load_ticker_index():
    """Build {norm_title -> {ticker,title}} and a token index for fuzzy party matching."""
    d = _get(SEC_TICKERS)
    idx, tok_idx = {}, {}
    if not isinstance(d, dict) or d.get("_error"):
        return idx, tok_idx, (d.get("_error") if isinstance(d, dict) else "load failed")
    for row in d.values():
        try:
            tk, title = row["ticker"], row["title"]
        except Exception:
            continue
        idx[_norm(title)] = {"ticker": tk, "title": title}
        for t in _tokens(title):
            tok_idx.setdefault(t, []).append({"ticker": tk, "title": title})
    return idx, tok_idx, None


def _match_ticker(party: str, idx: dict, tok_idx: dict):
    """Fuzzy-resolve a party name to a LISTED ticker. CATALYST-IDENTITY DISCIPLINE: a false map (e.g. the
    private '337 complainant "Aardvark Medical" -> public "Aardvark Therapeutics") mis-binds the ruling to
    the wrong company, so we are deliberately conservative. A match must cover a strong fraction of BOTH the
    party name and the company name; a lone shared distinctive token is returned only as LOW-confidence
    (surfaced but flagged for verification, never treated as a clean bind). Returns dict|None."""
    if not party:
        return None
    ptoks = _tokens(party)
    if not ptoks:
        return None
    pn = _norm(party)
    # exact match on the full normalized title = the only "clean" bind
    if pn in idx:
        m = dict(idx[pn]); m["match"] = "exact"; m["confidence"] = "high"; return m
    # candidate companies sharing distinctive tokens
    cand = {}
    for t in ptoks:
        for c in tok_idx.get(t, []):
            cand.setdefault(c["ticker"], c)
    best, best_key = None, (-1.0, -1.0)
    for c in cand.values():
        ctoks = _tokens(c["title"])
        if not ctoks:
            continue
        inter = ptoks & ctoks
        if not inter:
            continue
        pcover = len(inter) / len(ptoks)   # how much of the PARTY name is explained
        ccover = len(inter) / len(ctoks)   # how much of the COMPANY name is explained
        key = (min(pcover, ccover), len(inter))
        if key > best_key:
            best, best_key = c, key
    if not best:
        return None
    inter = _tokens(party) & _tokens(best["title"])
    pcover = len(inter) / len(ptoks)
    ccover = len(inter) / max(1, len(_tokens(best["title"])))
    m = dict(best)
    # HIGH: multi-token overlap that covers most of both names. LOW: a single shared token (mis-bind risk).
    if len(inter) >= 2 and min(pcover, ccover) >= 0.6:
        m["match"] = f"fuzzy(p{pcover:.2f}/c{ccover:.2f})"; m["confidence"] = "high"
    elif len(inter) >= 2 or (pcover >= 0.99 and ccover >= 0.99):
        m["match"] = f"fuzzy(p{pcover:.2f}/c{ccover:.2f})"; m["confidence"] = "medium"
    else:
        m["match"] = f"single-token:{sorted(inter)[0] if inter else '?'}"; m["confidence"] = "low"
    return m


# ------------------------------------------------------------------ LEG 2: ITC §337 (Federal Register)
def _parse_complainants(abstract: str):
    """Extract complainant(s) from 'on behalf of X (and Y) of <place>'."""
    if not abstract:
        return []
    m = re.search(r"on behalf of (.+?)(?:\.\s|\.$|(?:\s(?:The|An|A|Supplements?|A supplement)\s))", abstract)
    if not m:
        m = re.search(r"on behalf of (.+?) of [A-Z]", abstract)
    if not m:
        return []
    seg = m.group(1)
    # cut at the first " of <Place>" that ends an entity, then split conjunctions
    seg = re.split(r"\balleges\b", seg)[0]
    parts = re.split(r",? and |; ", seg)
    out = []
    for p in parts:
        p = re.sub(r"\s+of\s+[A-Z][A-Za-z.\- ]+(?:,\s*[A-Za-z ]+)?$", "", p).strip(" .,")
        if p and len(p) > 2:
            out.append(p)
    return out[:5]


def _parse_respondents(abstract: str):
    """Best-effort respondent extraction. The FR abstract for a fresh institution notice usually does NOT
    enumerate respondents (they are in the notice body); amendment/ID notices sometimes do. Pull the
    quoted short-names when a respondent list is present, else return []."""
    if not abstract or "respondent" not in abstract.lower():
        return []
    names = []
    # entities followed by a quoted short-name: Foo Bar Co. LTD ("Foo")
    for m in re.finditer(r"([A-Z][A-Za-z0-9&.\-]+(?:\s+[A-Z][A-Za-z0-9&.\-]+){0,5})\s*\(\"([^\"]+)\"\)", abstract):
        full = m.group(1).strip()
        if len(full) > 3:
            names.append(full)
    # dedupe, keep order
    seen, out = set(), []
    for n in names:
        k = _norm(n)
        if k and k not in seen:
            seen.add(k); out.append(n)
    return out[:25]


def _itc_docket(docket_ids):
    for d in docket_ids or []:
        m = re.search(r"(337-TA-\d+)", d)
        if m:
            return m.group(1)
    return None


def scan_itc(idx, tok_idx):
    """Pull recent ITC §337 institution notices from the Federal Register; map parties to tickers."""
    params = {
        "conditions[agencies][]": "international-trade-commission",
        "conditions[term]": "section 337 notice of institution of investigation",
        "conditions[publication_date][gte]": (datetime.date.today() - datetime.timedelta(days=540)).isoformat(),
        "per_page": "80", "order": "newest",
        "fields[]": ["title", "publication_date", "abstract", "docket_ids", "html_url"],
    }
    # build query with repeated fields[] keys
    q = urllib.parse.urlencode([(k, v) for k, vs in params.items() for v in ([vs] if isinstance(vs, str) else vs)])
    d = _get(f"{FR_API}?{q}")
    rows, err = [], None
    if isinstance(d, dict) and d.get("_error"):
        return [], d["_error"]
    today = datetime.date.today()
    for x in (d.get("results", []) if isinstance(d, dict) else []):
        docket = _itc_docket(x.get("docket_ids"))
        title = x.get("title") or ""
        abstract = x.get("abstract") or ""
        # keep only genuine §337 INSTITUTION notices (not 701/731 AD/CVD, not later procedural notices)
        if not docket:
            continue
        if "institution of investigation" not in title.lower() and "institution of investigation" not in abstract.lower():
            continue
        try:
            inst = datetime.date.fromisoformat(x.get("publication_date"))
        except Exception:
            inst = None
        complainants = _parse_complainants(abstract)
        respondents = _parse_respondents(abstract)
        # map parties -> tickers
        hits = []
        for role, names in (("complainant", complainants), ("respondent", respondents)):
            for nm in names:
                mt = _match_ticker(nm, idx, tok_idx)
                if mt:
                    hits.append({"role": role, "party": nm, "ticker": mt["ticker"],
                                 "listed_as": mt["title"], "match": mt["match"],
                                 "confidence": mt.get("confidence", "medium")})
        # dedupe hits by (ticker, role) — a party can appear twice (e.g. "Nokia Technologies" + "Nokia Corp")
        _seen, _h = set(), []
        for h in hits:
            k = (h["ticker"], h["role"])
            if k not in _seen:
                _seen.add(k); _h.append(h)
        hits = _h
        if inst:
            tgt_lo = inst + datetime.timedelta(days=ITC_TARGET_DAYS_LO)
            tgt_hi = inst + datetime.timedelta(days=ITC_TARGET_DAYS_HI)
            days_lo = (tgt_lo - today).days
            days_hi = (tgt_hi - today).days
        else:
            tgt_lo = tgt_hi = None
            days_lo = days_hi = None
        rows.append({
            "inv_no": docket,
            "title": re.sub(r";.*$", "", title).strip(),
            "institution_date": inst.isoformat() if inst else "UNVERIFIABLE",
            "complainants": complainants,
            "respondents": respondents or "see notice body (not in FR abstract)",
            "ticker_hits": hits,
            "target_date_est_window": (f"{tgt_lo.isoformat()} .. {tgt_hi.isoformat()}" if tgt_lo else "UNVERIFIABLE"),
            "target_date_exact": "UNVERIFIABLE (ALJ sets ~45d post-institution)",
            "days_to_est": days_lo if days_lo is not None else None,   # to the near edge of the window
            "days_to_window": [days_lo, days_hi] if days_lo is not None else None,
            "url": x.get("html_url"),
        })
    return rows, err


# ------------------------------------------------------------------ LEG 1: PTAB (USPTO ODP, key-optional)
def scan_ptab(idx, tok_idx):
    """Pull recent instituted IPR/PGR proceedings and compute the FWD-due window. Requires USPTO_ODP_KEY;
    without it, returns [] with an honest reason (the keyless legacy PTAB API was decommissioned 2026-06)."""
    if not ODP_KEY:
        return [], ("PTAB leg DISABLED: USPTO Open Data Portal now requires an API key (as of 2026-06 the "
                    "legacy keyless developer.uspto.gov PTAB API was decommissioned). Set env USPTO_ODP_KEY "
                    "(free, self-serve at data.uspto.gov) to enable. No fabricated PTAB data is emitted.")
    today = datetime.date.today()
    since = (today - datetime.timedelta(days=395)).isoformat()   # institutions in the last ~13mo -> FWD ahead
    # ODP PTAB Trials search. Field names per data.uspto.gov/apis/ptab-trials/search-proceedings.
    params = {"q": f"proceedingTypeCategory:\"AIA Trial\" AND institutionDecisionDate:[{since} TO *]",
              "rows": "100", "sort": "institutionDecisionDate desc"}
    q = urllib.parse.urlencode(params)
    hdrs = dict(HDRS); hdrs["X-API-KEY"] = ODP_KEY
    d = _get(f"{ODP_PTAB}?{q}", headers=hdrs)
    if isinstance(d, dict) and d.get("_error"):
        return [], f"PTAB ODP error: {d['_error']}"
    recs = []
    if isinstance(d, dict):
        recs = d.get("results") or d.get("proceedings") or d.get("patentTrialProceedingDataBag") or []
    rows = []
    for r in recs:
        # be liberal about field spellings across ODP schema versions
        def g(*keys):
            for k in keys:
                if isinstance(r, dict) and r.get(k) not in (None, ""):
                    return r.get(k)
            return None
        num = g("proceedingNumber", "trialNumber", "proceedingIdentifier")
        inst_s = g("institutionDecisionDate", "institutionDecisionMailedDate")
        subtype = g("proceedingTypeCategory", "subproceedingTypeCategory", "proceedingType") or ""
        owner = g("patentOwnerName", "respondentPartyName", "patentOwner")
        petitioner = g("petitionerPartyName", "petitionerName", "firstNamedPetitioner")
        if not (num and inst_s):
            continue
        try:
            inst = datetime.date.fromisoformat(str(inst_s)[:10])
        except Exception:
            continue
        fwd_due = inst + datetime.timedelta(days=PTAB_FWD_DAYS)
        fwd_max = inst + datetime.timedelta(days=PTAB_FWD_MAX_DAYS)
        days_to = (fwd_due - today).days
        hits = []
        for role, nm in (("patent_owner", owner), ("petitioner", petitioner)):
            mt = _match_ticker(nm, idx, tok_idx) if nm else None
            if mt:
                hits.append({"role": role, "party": nm, "ticker": mt["ticker"],
                             "listed_as": mt["title"], "match": mt["match"],
                             "confidence": mt.get("confidence", "medium")})
        rows.append({
            "proceeding": num,
            "type": subtype,
            "patent_owner": owner or "UNVERIFIABLE",
            "petitioner": petitioner or "UNVERIFIABLE",
            "institution_date": inst.isoformat(),
            "fwd_due_est": fwd_due.isoformat(),
            "fwd_due_max": fwd_max.isoformat(),
            "days_to": days_to,
            "ticker_hits": hits,
        })
    return rows, None


# ------------------------------------------------------------------ bucketing
def _bucket(days):
    if days is None:
        return "unknown"
    if days < 0:
        return "past"
    if days <= IMMINENT_DAYS:
        return "imminent"
    if days <= UPCOMING_DAYS:
        return "upcoming"
    return "distant"


def scan() -> dict:
    today = datetime.date.today()
    idx, tok_idx, tk_err = _load_ticker_index()
    ptab, ptab_err = scan_ptab(idx, tok_idx)
    itc, itc_err = scan_itc(idx, tok_idx)

    for r in ptab:
        r["bucket"] = _bucket(r.get("days_to"))
    for r in itc:
        r["bucket"] = _bucket(r.get("days_to_est"))

    def _has_verified(r):
        return any(h.get("confidence") in ("high", "medium") for h in r["ticker_hits"])

    # sort: rows with a VERIFIED ticker hit first, then any hit, then soonest decision within
    ptab.sort(key=lambda r: (0 if _has_verified(r) else (1 if r["ticker_hits"] else 2),
                             r.get("days_to") if r.get("days_to") is not None else 9999))
    itc.sort(key=lambda r: (0 if _has_verified(r) else (1 if r["ticker_hits"] else 2),
                            r.get("days_to_est") if r.get("days_to_est") is not None else 9999))

    caveats = []
    if tk_err:
        caveats.append(f"SEC ticker map failed to load ({tk_err}) — party->ticker mapping unavailable this run.")
    if ptab_err:
        caveats.append(ptab_err)
    if itc_err:
        caveats.append(f"ITC/Federal-Register pull error: {itc_err}")
    caveats.append("ITC target-determination dates are ESTIMATED windows (statutory ~16-18mo from institution); "
                   "the ALJ's exact target date is set ~45d post-institution and is marked UNVERIFIABLE here.")
    caveats.append("Respondent lists are best-effort from the Federal Register abstract; fresh institution notices "
                   "usually list respondents only in the notice BODY, so respondent-side ticker hits under-count.")
    caveats.append("PTAB FWD-due is the §316(a)(11) statutory estimate (12mo, 18mo cap) from the institution date — "
                   "a real forward date, but the Board can settle/terminate early; treat as the OUTER catalyst window.")

    n_ptab_hits = sum(1 for r in ptab if _has_verified(r))
    n_itc_hits = sum(1 for r in itc if _has_verified(r))

    return {
        "asof": today.isoformat(),
        "ptab": ptab,
        "itc": itc,
        "counts": {"ptab_rows": len(ptab), "ptab_verified_ticker_hits": n_ptab_hits,
                   "itc_rows": len(itc), "itc_verified_ticker_hits": n_itc_hits,
                   "itc_any_ticker_hits": sum(1 for r in itc if r["ticker_hits"])},
        "note": ("INFO/LATENCY class. Patent-validity (PTAB IPR/PGR -> Final Written Decision ~12mo post-institution) "
                 "and tariff (ITC §337 -> exclusion-order determination ~16-18mo post-institution) rulings hit single "
                 "small caps on a PUBLISHED docket the market doesn't price until the press release — the edge is "
                 "reading the calendar nobody reads. Each row binds to the SPECIFIC docket (337-TA-#### / PTAB trial "
                 "number) and NAMES the tradeable party (complainant/patent-owner win = pop; respondent exclusion / "
                 "petitioner-win-kills-patent = drop). Outcomes are ~coin-flip: this TIMES the catalyst and names the "
                 "instrument — sizing is a downstream convexity/defined-risk decision, never a directional call here."),
        "caveats": caveats,
    }


def main():
    res = scan()
    c = res["counts"]
    print(f"=== PTAB / ITC §337 DOCKET NOWCAST  {res['asof']} ===")
    print(f"  PTAB: {c['ptab_rows']} instituted proceedings ({c['ptab_verified_ticker_hits']} w/ verified listed party)")
    print(f"  ITC : {c['itc_rows']} §337 investigations   ({c['itc_verified_ticker_hits']} verified, "
          f"{c['itc_any_ticker_hits']} incl. low-confidence single-token maps)")

    def _fmt_hits(hits):
        out = []
        for h in hits:
            mark = "" if h.get("confidence") in ("high", "medium") else "?"   # ? = low-conf, verify identity
            out.append(f"{h['ticker']}{mark}({h['role']})")
        return ", ".join(out) or "-"

    print("\n  -- ITC §337 (verified-ticker rows first; ? = low-confidence single-token map, verify) --")
    shown = [r for r in res["itc"] if r["ticker_hits"]] or res["itc"]
    for r in shown[:12]:
        comp = "; ".join(r["complainants"][:2]) or "?"
        dw = r.get("days_to_window")
        win = f"{dw[0]}..{dw[1]}d" if dw else "date?"
        print(f"    {r['inv_no']:14} [{r['bucket']:8}] tgt~{win:12} {_fmt_hits(r['ticker_hits']):22} <- {comp[:44]}")

    print("\n  -- PTAB IPR/PGR (FWD-due, ticker-mapped first) --")
    if res["ptab"]:
        pshown = [r for r in res["ptab"] if r["ticker_hits"]] or res["ptab"]
        for r in pshown[:12]:
            print(f"    {r['proceeding']:16} [{r['bucket']:8}] FWD~{r['fwd_due_est']} ({r['days_to']:+d}d) "
                  f"{_fmt_hits(r['ticker_hits']):22} owner={str(r['patent_owner'])[:26]}")
    else:
        print("    (none — PTAB leg unavailable; see caveats)")

    print("\n  CAVEATS:")
    for cv in res["caveats"]:
        print(f"    - {cv}")

    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n[-> {OUT.relative_to(HERE.parent)}]")


if __name__ == "__main__":
    main()
