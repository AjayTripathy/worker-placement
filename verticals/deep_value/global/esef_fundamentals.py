"""esef_fundamentals — Europe leg of the global value screen: ESEF (EEA iXBRL mandate)
fundamentals via filings.xbrl.org, mapped to the us-gaap-flavored keys score.py already
understands (mirrors ifrs_fundamentals.IFRS_MAP / edinet_fundamentals.CONCEPT_MAP).

Source: https://filings.xbrl.org — FREE, no auth. JSON:API index at /api/filings
(filter[country]=CC, page[size]<=250, include=entity gives LEI + name), and per-filing
pre-extracted xBRL-JSON facts files (the "json_url" package) — we prefer those over
parsing iXBRL ourselves. One adapter covers GB + Nordics + Poland (INVENTORY.md #3).

Shape: crawl the per-country filing index into data/esef_cache/index_<CC>.json, pick the
latest annual filing per entity (LEI) within the vintage window, download each facts JSON
(gzip-cached in data/esef_cache/facts/), extract ifrs-full concepts per filing, MERGE into
data/esef_store.json. The screen (screen_europe.py) runs off the store; every number in it
carries the fxo_id + filing URL it came from.

KNOWN ESEF LIMITS (encoded, not papered over):
  - PRIMARY STATEMENTS ONLY are block-tagged with numbers — notes are text blocks. So no
    debt-maturity detail, no share counts in many filings.
  - ENTITY-SPECIFIC EXTENSIONS are rampant (esp. operating profit — there is no ifrs-full
    "OperatingProfit"; filers who don't use ProfitLossFromOperatingActivities extend).
    When a standard ifrs-full tag is absent we LOG THE MISS per company (extraction_misses
    in the store + per-country loss rates from coverage_report()) — we never guess into an
    extension namespace. Coverage honesty over coverage inflation.
  - ANNUAL ONLY: half-yearlies are not ESEF-mandated; all _prior/_q keys are None, same as
    the Japan/20-F adapters. score.py's quarterly gates are structurally skipped.
  - IE returns 0 filings on this index (Euronext Dublin OAM not aggregated) — logged, not
    silently absorbed. NO (Norway) IS present (files ESEF as EEA member).

Values stay NATIVE per filing currency (GBP/PLN/SEK/DKK/NOK/EUR) — ratios are
currency-neutral; the FX bridge lives in screen_europe.py and only where USD is displayed.
"""
from __future__ import annotations
import argparse, gzip, json, os, re, time, urllib.error, urllib.parse, urllib.request
from collections import Counter
from datetime import datetime, timedelta

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CACHE = os.path.join(DATA, "esef_cache")
FACTS_DIR = os.path.join(CACHE, "facts")
STORE = os.path.join(DATA, "esef_store.json")
BASE = "https://filings.xbrl.org"
HDRS = {"User-Agent": "signalos-deepvalue research 4tripathy@gmail.com",
        "Accept-Encoding": "gzip"}
SLEEP = 0.35                       # be polite — free public infra (EMMA 403 lesson)
COUNTRIES = ["GB", "PL", "SE", "FI", "DK", "NO", "IE"]   # IE known-empty; kept so the gap is REPORTED
SINCE_DEFAULT = None               # None = auto per country: latest AVAILABLE vintage (see below)
# FEED-LAG REALITY (measured 2026-07-21): filings.xbrl.org national feeds are unevenly
# stale — GB/DK/FI carry FY2025/26, but SE and NO stop at FY2024 (nothing date_added
# since ~2025) and PL stops at FY2023. A fixed "FY2025" window would silently report
# zero coverage for those countries. Instead each country's vintage window is derived
# from ITS OWN latest valid period_end (minus ~380d), and every row carries period_end
# so the screen can flag fiscal-year staleness rather than hide it.

# ifrs-full concept -> score.py contract keys (candidates best-first; matched on the
# LOCAL name with the "ifrs-full:" prefix required — extension namespaces never match,
# BY DESIGN: an extension hit would be a guess about a filer-defined meaning).
CONCEPT_MAP = {
    "Revenues": ["Revenue", "RevenueFromContractsWithCustomers", "RevenueFromSaleOfGoods",
                 "RevenueFromRenderingOfServices", "RevenueFromInterest"],
    "OperatingIncomeLoss": ["ProfitLossFromOperatingActivities"],   # the extension-loss hotspot
    # EBIT-derivation fallback inputs (standard tags, so deriving is arithmetic not guessing):
    # EBIT ~= PBT + FinanceCosts - FinanceIncome. Differs from operating profit by
    # associates/other-gains placement -> carried as a FLAG (_ebit_derived), never silent.
    "_PBT": ["ProfitLossBeforeTax"],
    "_FinCosts": ["FinanceCosts"],
    "_FinIncome": ["FinanceIncome"],
    "Assets": ["Assets"],
    "AssetsCurrent": ["CurrentAssets"],
    "Liabilities": ["Liabilities"],
    "LiabilitiesCurrent": ["CurrentLiabilities"],
    "StockholdersEquity": ["EquityAttributableToOwnersOfParent", "Equity"],  # Equity netted of NCI in _derive
    "CashAndCashEquivalentsAtCarryingValue": ["CashAndCashEquivalents", "Cash",
                                              "CashAndBankBalancesAtCentralBanks"],
    "ShortTermInvestments": ["OtherCurrentFinancialAssets", "CurrentFinancialAssets"],
    "LongTermInvestments": ["OtherNoncurrentFinancialAssets",
                            "InvestmentsInSubsidiariesJointVenturesAndAssociates",
                            "InvestmentAccountedForUsingEquityMethod"],
    # debt — ifrs-full borrowings family. Split parts are summed; the all-in "Borrowings"
    # floors the sum (never added on top): the COLL/HAIN bias = over-state debt.
    "_DebtCurrentBorrowings": ["CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings",
                               "ShorttermBorrowings", "CurrentPortionOfLongtermBorrowings"],
    "_DebtNoncurrentBorrowings": ["NoncurrentPortionOfNoncurrentBorrowings", "LongtermBorrowings"],
    "_DebtLeaseCurrent": ["CurrentLeaseLiabilities"],
    "_DebtLeaseNoncurrent": ["NoncurrentLeaseLiabilities"],
    "_DebtCombined": ["Borrowings"],
    "_DebtLeaseCombined": ["LeaseLiabilities"],
    # lease principal repaid (financing section) — the IFRS16 FCF defect (screen_defects.jsonl
    # 2026-07-21): FCF = CFO − capex omits it, overstating FCFy up to 2.4x on leased retailers
    "_LeasePayments": ["PaymentsOfLeaseLiabilitiesClassifiedAsFinancingActivities",
                       "RepaymentsOfLeaseLiabilities"],
    "NetCashProvidedByUsedInOperatingActivities":
        ["CashFlowsFromUsedInOperatingActivities",
         "CashFlowsFromUsedInOperatingActivitiesContinuingOperations"],
    "PaymentsToAcquirePropertyPlantAndEquipment":
        ["PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
         "PurchaseOfPropertyPlantAndEquipmentIntangibleAssetsOtherThanGoodwillInvestmentPropertyAndOtherNoncurrentAssets"],
    "MinorityInterest": ["NoncontrollingInterests"],
    # share count — ESEF primary-statement tagging often omits it; screen falls back to
    # yfinance shares/mcap when absent (basis logged either way)
    "_SharesIssued": ["NumberOfSharesIssued", "NumberOfSharesOutstanding"],
}
_KEYS_REQUIRED = ["Revenues", "OperatingIncomeLoss", "Assets", "Liabilities",
                  "StockholdersEquity", "CashAndCashEquivalentsAtCarryingValue",
                  "NetCashProvidedByUsedInOperatingActivities",
                  "PaymentsToAcquirePropertyPlantAndEquipment"]  # tracked for extension-loss reporting
_LOCAL2KEY = {}
for _k, _cands in CONCEPT_MAP.items():
    for _i, _c in enumerate(_cands):
        _LOCAL2KEY.setdefault(_c, (_k, _i))

_CORE_DIMS = {"concept", "entity", "period", "unit", "language", "noValue"}


def _get(url: str, timeout=90) -> bytes:
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return raw


# ---------------------------------------------------------------- index crawl

def crawl_index(country: str, refresh=False) -> list:
    """Full filing index for one country -> [{lei, name, period_end, json_url, ...}],
    cached to esef_cache/index_<CC>.json. ~6-12 pages of 250; resumable = re-run."""
    os.makedirs(CACHE, exist_ok=True)
    cf = os.path.join(CACHE, f"index_{country}.json")
    if os.path.exists(cf) and not refresh:
        return json.load(open(cf))
    rows, page = [], 1
    while True:
        q = urllib.parse.urlencode({"filter[country]": country, "page[size]": 250,
                                    "page[number]": page, "include": "entity"})
        d = json.loads(_get(f"{BASE}/api/filings?{q}"))
        time.sleep(SLEEP)
        ents = {e["id"]: e["attributes"] for e in d.get("included", []) if e["type"] == "entity"}
        for f in d.get("data", []):
            a = f["attributes"]
            eid = (((f.get("relationships") or {}).get("entity") or {}).get("data") or {}).get("id")
            ent = ents.get(eid, {})
            rows.append({"filing_id": f["id"], "fxo_id": a.get("fxo_id"),
                         "lei": ent.get("identifier"), "name": ent.get("name"),
                         "country": a.get("country"), "period_end": a.get("period_end"),
                         "date_added": a.get("date_added"), "json_url": a.get("json_url"),
                         "report_url": a.get("report_url"), "error_count": a.get("error_count")})
        total = d.get("meta", {}).get("count", 0)
        print(f"  {country} page {page}: {len(rows)}/{total}")
        if len(rows) >= total or not d.get("data"):
            break
        page += 1
    json.dump(rows, open(cf, "w"), ensure_ascii=False, indent=0)
    return rows


def latest_annual_per_entity(rows: list, since=None) -> list:
    """One filing per LEI: the freshest VALID period_end in the vintage window.
    since=None -> auto window = [country's own max valid period_end - 380d, today]
    (the feed-lag fix — see SINCE_DEFAULT note). period_end in the future = metadata
    error (an annual report's period has ended by construction) -> dropped. Amended /
    duplicate filings: freshest date_added wins."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    valid = [r for r in rows
             if r.get("lei") and r.get("period_end") and r["period_end"] <= today]
    if not valid:
        return []
    if since is None:
        max_pe = max(r["period_end"] for r in valid)
        since = (datetime.fromisoformat(max_pe) - timedelta(days=380)).strftime("%Y-%m-%d")
        print(f"  vintage window auto: period_end in [{since}, {today}] (feed max {max_pe})")
    best = {}
    for r in valid:
        if r["period_end"] < since:
            continue
        b = best.get(r["lei"])
        if b is None or (r["period_end"], r.get("date_added") or "") > (b["period_end"], b.get("date_added") or ""):
            best[r["lei"]] = r
    return list(best.values())


# ---------------------------------------------------------------- facts fetch

def fetch_facts(filing: dict, refresh=False):
    """One filing's xBRL-JSON facts dict, gzip-cached by fxo_id. None on any failure
    (404s happen; the caller logs them as coverage misses)."""
    if not filing.get("json_url"):
        return None
    os.makedirs(FACTS_DIR, exist_ok=True)
    fid = re.sub(r"[^A-Za-z0-9_.-]", "_", filing["fxo_id"] or filing["filing_id"])
    path = os.path.join(FACTS_DIR, fid + ".json.gz")
    if os.path.exists(path) and not refresh:
        try:
            return json.loads(gzip.open(path).read())
        except Exception:
            os.remove(path)
    url = filing["json_url"]
    if not url.startswith("http"):
        url = BASE + urllib.parse.quote(url)
    try:
        raw = _get(url, timeout=180)
        time.sleep(SLEEP)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        time.sleep(SLEEP)
        return None
    try:
        d = json.loads(raw)
    except ValueError:
        return None
    with gzip.open(path, "wb") as fh:
        fh.write(raw if isinstance(raw, bytes) else raw.encode())
    return d


# ---------------------------------------------------------------- extraction

def _parse_period(p: str):
    """xBRL-JSON period -> ('duration', start, end) | ('instant', end, end)."""
    if "/" in p:
        s, e = p.split("/", 1)
        return "duration", s, e
    return "instant", p, p


def _days(s: str, e: str) -> float:
    try:
        return (datetime.fromisoformat(e.replace("Z", "")) -
                datetime.fromisoformat(s.replace("Z", ""))).days
    except ValueError:
        return -1


def extract_filing(filing: dict, facts_doc: dict):
    """xBRL-JSON facts -> mapped concept row (score.py contract), native currency.

    Rules: ifrs-full namespace only (extensions never matched — see module docstring);
    NON-dimensional facts only (any extra dimension = a segment/member slice, not the
    consolidated total); current fiscal year = the ~annual duration with the latest end,
    instants at that same end-datetime. Duplicate facts (statement + re-tagged) collapse
    by most-common value; a real conflict is logged, majority wins."""
    facts = facts_doc.get("facts", {})
    # Danish (a.o.) filers put the WHOLE report on ConsolidatedAndSeparateFinancial-
    # StatementsAxis (52 DK filings extracted ZERO before this): that lone axis is a
    # consolidation MARKER, not a segment slice — accept it. Bucket precedence:
    # plain > ConsolidatedMember > SeparateMember; separate-only accounts are kept but
    # flagged _consol=False (the Japan 'solo' column — a flag, never a silent pick).
    CONSOL_AXIS = "ifrs-full:ConsolidatedAndSeparateFinancialStatementsAxis"
    buckets = {"plain": [], "consol": [], "separate": []}  # (local, kind, start, end, val, unit)
    n_ext = n_ifrs = 0
    for f in facts.values():
        dims = f.get("dimensions", {})
        c = dims.get("concept", "")
        if ":" in c:
            (n_ifrs, n_ext) = (n_ifrs + 1, n_ext) if c.startswith("ifrs-full:") else (n_ifrs, n_ext + 1)
        if not c.startswith("ifrs-full:"):
            continue
        extra = set(dims) - _CORE_DIMS
        if extra == {CONSOL_AXIS}:
            bucket = "consol" if "Consolidated" in str(dims[CONSOL_AXIS]) else "separate"
        elif extra:
            continue                                   # dimensional slice, not the total
        else:
            bucket = "plain"
        local = c.split(":", 1)[1]
        hit = _LOCAL2KEY.get(local)
        if hit is None or "period" not in dims:
            continue
        try:
            val = float(f.get("value"))
        except (TypeError, ValueError):
            continue
        kind, s, e = _parse_period(dims["period"])
        buckets[bucket].append((local, kind, s, e, val, dims.get("unit") or ""))
    # the bucket carrying the most distinct mapped concepts wins; ties follow precedence
    order = ("plain", "consol", "separate")
    mode = max(order, key=lambda b: (len({x[0] for x in buckets[b]}), -order.index(b)))
    usable = buckets[mode]
    if not usable:
        return None, {"n_ifrs": n_ifrs, "n_ext": n_ext}

    # current fiscal year = latest end among ~annual durations (330-400d handles 52/53-wk)
    ann_ends = [e for (_, k, s, e, _, _) in usable if k == "duration" and 330 <= _days(s, e) <= 400]
    fy_end = max(ann_ends) if ann_ends else max(e for (_, k, s, e, _, _) in usable)

    by_key = {}
    for local, kind, s, e, val, unit in usable:
        if e != fy_end:
            continue
        if kind == "duration" and not (330 <= _days(s, e) <= 400):
            continue
        key, rank = _LOCAL2KEY[local]
        by_key.setdefault(key, {}).setdefault(rank, []).append((val, unit))

    rec, currencies, conflicts = {}, Counter(), 0
    for key, ranked in by_key.items():
        rank = min(ranked)
        vals = [v for v, _ in ranked[rank]]
        cnt = Counter(vals)
        if len(cnt) > 1:
            conflicts += 1
        rec[key] = cnt.most_common(1)[0][0]
        rec["_src_" + key] = CONCEPT_MAP[key][rank]
        for _, u in ranked[rank]:
            m = re.match(r"iso4217:([A-Z]{3})", u)
            if m and key != "_SharesIssued":
                currencies[m.group(1)] += 1
    if not rec:
        return None, {"n_ifrs": n_ifrs, "n_ext": n_ext}

    rec = _derive(rec)
    rec["_consol"] = mode != "separate"                # separate-only accounts -> 'solo' flag
    rec["currency"] = currencies.most_common(1)[0][0] if currencies else None
    rec["_mixed_currency"] = len(currencies) > 1
    rec["_tag_conflicts"] = conflicts
    rec["_n_ifrs_facts"], rec["_n_ext_facts"] = n_ifrs, n_ext
    rec["fy_end"] = fy_end[:10]
    # traceability contract: every row names its filing
    rec["fxo_id"] = filing.get("fxo_id")
    rec["filing_url"] = BASE + (filing.get("report_url") or "")
    rec["facts_url"] = BASE + (filing.get("json_url") or "")
    rec["lei"] = filing.get("lei")
    rec["name"] = filing.get("name")
    rec["country"] = filing.get("country")
    rec["period_end"] = filing.get("period_end")
    # extension-loss honesty: which contract keys this filing failed to yield
    rec["_missing"] = [k for k in _KEYS_REQUIRED if rec.get(k) is None]
    # score.py housekeeping — annual-only cadence, same as the Japan/20-F adapters
    rec["_ttm_rolling"] = False
    rec["_ifrs_annual"] = True
    for k in ("OperatingIncomeLoss_prior", "OperatingIncomeLoss_q", "OperatingIncomeLoss_q_prior",
              "Revenues_prior"):
        rec[k] = None
    # no reliable discrete one-time-gain tag in ESEF primary statements; IFRS operating
    # profit keeps the exposure (screen carries the uniform-IFRS caveat, not a fake 0-risk)
    rec["OneTimeGain_q"] = rec["OneTimeGain_q_prior"] = rec["OneTimeGain_ttm"] = 0
    return rec, {"n_ifrs": n_ifrs, "n_ext": n_ext}


def _derive(rec: dict) -> dict:
    g = rec.get
    # EBIT fallback: extension-tagged operating profit is invisible to us BY POLICY, but
    # PBT + net finance costs is derivable from standard tags. Flagged, counted in coverage.
    rec["_ebit_derived"] = False
    if g("OperatingIncomeLoss") is None and g("_PBT") is not None:
        rec["OperatingIncomeLoss"] = g("_PBT") + (g("_FinCosts") or 0) - (g("_FinIncome") or 0)
        rec["_src_OperatingIncomeLoss"] = "derived:ProfitLossBeforeTax+FinanceCosts-FinanceIncome"
        rec["_ebit_derived"] = True
    # total debt: sum the borrowings splits + leases, floor with the all-in tags
    parts = [g("_DebtCurrentBorrowings"), g("_DebtNoncurrentBorrowings"),
             g("_DebtLeaseCurrent"), g("_DebtLeaseNoncurrent")]
    combined = (g("_DebtCombined") or 0) + (g("_DebtLeaseCombined") or 0)
    if any(p is not None for p in parts) or combined:
        total = max(sum(p for p in parts if p), combined)
        rec["LongTermDebt"] = total
        rec["DebtLongtermAndShorttermCombinedAmount"] = total
    # Equity (umbrella) includes NCI — net down to parent when the parent tag was absent
    if g("_src_StockholdersEquity") == "Equity" and g("StockholdersEquity") is not None:
        rec["StockholdersEquity"] = g("StockholdersEquity") - (g("MinorityInterest") or 0)
    # capex as positive magnitude (score.py subtracts it); ESEF Purchase* is normally
    # tagged positive (debit balance) but sign-flipped filings exist
    k = "PaymentsToAcquirePropertyPlantAndEquipment"
    if rec.get(k) is not None and rec[k] < 0:
        rec[k] = -rec[k]
    return rec


# ---------------------------------------------------------------- store + crawl

def load_store() -> dict:
    return json.load(open(STORE)) if os.path.exists(STORE) else {}


def merge_store(new_rows: dict) -> dict:
    """MERGE by LEI, freshest period_end wins — never overwrite-clobber a shared store
    (the recurring DILIGENCE_MASTER bug)."""
    store = load_store()
    for lei, rec in new_rows.items():
        old = store.get(lei)
        if old is None or (rec.get("period_end") or "") >= (old.get("period_end") or ""):
            store[lei] = rec
    os.makedirs(DATA, exist_ok=True)
    json.dump(store, open(STORE, "w"), ensure_ascii=False, indent=0)
    return store


def crawl(countries=None, since=SINCE_DEFAULT, max_docs=None, refresh_index=False) -> dict:
    """Country-by-country: index -> latest annual per LEI -> facts -> extract -> merge.
    Resumable by construction (index + facts + store all cached/merged incrementally).
    Prints per-country coverage + extension-loss honestly; misses land in the store's
    companion file esef_cache/coverage_<CC>.json."""
    out, n = {}, 0
    for cc in (countries or COUNTRIES):
        print(f"[{cc}] index...")
        try:
            rows = crawl_index(cc, refresh=refresh_index)
        except urllib.error.HTTPError as ex:
            print(f"  index FAILED: {ex}")
            continue
        picks = latest_annual_per_entity(rows, since)
        print(f"  filings {len(rows)} -> latest-annual entities: {len(picks)}")
        vintage_max = max((p["period_end"] for p in picks), default=None)
        cov = {"country": cc, "filings_total": len(rows), "entities_vintage": len(picks),
               "vintage_max_period_end": vintage_max,
               "no_json": 0, "fetch_fail": 0, "no_facts": 0, "extracted": 0,
               "missing_key_counts": Counter(), "fully_covered": 0,
               "ebit_std_tag": 0, "ebit_derived": 0, "ebit_absent": 0}
        for i, filing in enumerate(sorted(picks, key=lambda r: r["period_end"], reverse=True)):
            if max_docs is not None and n >= max_docs:
                break
            n += 1
            if not filing.get("json_url"):
                cov["no_json"] += 1
                continue
            d = fetch_facts(filing)
            if d is None:
                cov["fetch_fail"] += 1
                continue
            rec, _stats = extract_filing(filing, d)
            if rec is None:
                cov["no_facts"] += 1
                continue
            cov["extracted"] += 1
            if rec.get("OperatingIncomeLoss") is None:
                cov["ebit_absent"] += 1
            elif rec.get("_ebit_derived"):
                cov["ebit_derived"] += 1
            else:
                cov["ebit_std_tag"] += 1
            if not rec["_missing"]:
                cov["fully_covered"] += 1
            for k in rec["_missing"]:
                cov["missing_key_counts"][k] += 1
            out[filing["lei"]] = rec
            if (i + 1) % 50 == 0:
                print(f"  ...{i+1}/{len(picks)} (extracted {cov['extracted']})")
                merge_store({k: v for k, v in out.items()})   # checkpoint the store
        cov["missing_key_counts"] = dict(cov["missing_key_counts"])
        ex_n = cov["extracted"] or 1
        # extension-loss = share of extracted filings where the STANDARD operating-profit
        # tag was absent (derived-EBIT recoveries still count as tag loss — honesty)
        cov["ext_loss_ebit_pct"] = round(100 * (cov["ebit_derived"] + cov["ebit_absent"]) / ex_n, 1)
        cov["ext_loss_rev_pct"] = round(100 * cov["missing_key_counts"].get("Revenues", 0) / ex_n, 1)
        json.dump(cov, open(os.path.join(CACHE, f"coverage_{cc}.json"), "w"), indent=1)
        print(f"  [{cc}] extracted {cov['extracted']}/{len(picks)} "
              f"(no-json {cov['no_json']}, fetch-fail {cov['fetch_fail']}, empty {cov['no_facts']}) "
              f"| EBIT-tag loss {cov['ext_loss_ebit_pct']}% rev-loss {cov['ext_loss_rev_pct']}%")
    merge_store(out)
    return out


def coverage_report() -> list:
    reps = []
    for cc in COUNTRIES:
        p = os.path.join(CACHE, f"coverage_{cc}.json")
        if os.path.exists(p):
            reps.append(json.load(open(p)))
    return reps


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--countries", nargs="+", default=None)
    ap.add_argument("--since", default=SINCE_DEFAULT)
    ap.add_argument("--max-docs", type=int, default=None)
    ap.add_argument("--refresh-index", action="store_true")
    a = ap.parse_args()
    rows = crawl(a.countries, a.since, a.max_docs, a.refresh_index)
    store = merge_store(rows)
    print(f"\ncrawled {len(rows)} filings -> store now {len(store)} issuers")
    for cov in coverage_report():
        print(f"  {cov['country']}: vintage {cov['entities_vintage']} extracted {cov['extracted']} "
              f"| EBIT-loss {cov.get('ext_loss_ebit_pct')}% | missing {cov['missing_key_counts']}")
