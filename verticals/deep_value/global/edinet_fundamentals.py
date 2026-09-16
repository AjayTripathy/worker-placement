"""edinet_fundamentals — Japan-leg fundamentals from EDINET (the FSA's EDGAR), mapped to the
us-gaap-flavored keys score.py already understands (mirrors ifrs_fundamentals.IFRS_MAP).

EDINET has NO frames-style cross-section endpoint, so the shape is: crawl the annual-report
season (有価証券報告書, form 030000 — March FY-ends file mid/late June) date-by-date via
documents.json, download each filing's data ZIP into data/edinet_cache/, extract the needed
JPPFS (JP-GAAP) / IFRS concepts per filing, and MERGE into data/edinet_store.json. The screen
runs off the store; every number in it carries the docID it came from.

Two transports fill the same cache (extractor + store are source-agnostic):
  - API v2 (preferred): needs the free subscription key (env EDINET_API_KEY or
    data/edinet_key.txt; signup steps in INVENTORY.md). type=5 CSV zip = EDINET's own
    fact extraction — we prefer it; type=1 raw-XBRL zip is the fallback parse.
  - edinet_browser_crawl.py (no key): Playwright on the public viewer, same ZIPs.

JPY values stay NATIVE — every ratio is currency-neutral; the FX bridge lives in the screen
and only where a USD figure is displayed. JP-GAAP structural note: 特別利益 (extraordinary
gains) sit BELOW operating income by construction, so JPPFS OperatingIncome is already clean
of the one-time-gain pollution the US screen has to strip; IFRS filers keep the exposure and
are flagged by standard instead.
"""
from __future__ import annotations
import csv, io, json, os, re, time, urllib.request, urllib.error, zipfile
import xml.etree.ElementTree as ET

DATA = os.path.join(os.path.dirname(__file__), "data")
CACHE = os.path.join(DATA, "edinet_cache")
STORE = os.path.join(DATA, "edinet_store.json")
API = "https://api.edinet-fsa.go.jp/api/v2"
HDRS = {"User-Agent": "signalos-deepvalue research 4tripathy@gmail.com"}
SLEEP = 0.6                      # be polite — gov API, and EMMA taught us about 403 rate-limits

ANNUAL_FORM = "030000"           # 有価証券報告書 (securities report = the annual report)
ANNUAL_ORD = "010"               # ordinance 010 = 企業内容等の開示 (corporate disclosure)

# JPPFS / EDINET-IFRS local element names -> our us-gaap-flavored keys (score.py contract).
# Candidates are ordered best-first; matched on LOCAL name (prefix jppfs_cor:/jpigp_cor:
# stripped) so one table serves both taxonomies. IFRS names carry the literal "IFRS" suffix
# in EDINET's jpigp taxonomy — that suffix is the standard tell, not a typo.
CONCEPT_MAP = {
    "Revenues": ["NetSales", "RevenueIFRS", "OperatingRevenue1", "OperatingRevenue2",
                 "NetSalesOfCompletedConstructionContracts", "OperatingRevenue",
                 "SalesIFRS", "NetSalesIFRS", "RevenuesIFRS"],
    "OperatingIncomeLoss": ["OperatingIncome", "OperatingProfitLossIFRS", "OperatingIncomeIFRS"],
    "Assets": ["Assets", "AssetsIFRS", "TotalAssetsIFRSSummaryOfBusinessResults"],
    "AssetsCurrent": ["CurrentAssets", "CurrentAssetsIFRS"],
    "Liabilities": ["Liabilities", "LiabilitiesIFRS"],
    "LiabilitiesCurrent": ["CurrentLiabilities", "CurrentLiabilitiesIFRS"],
    # parent equity: prefer the explicit parent-attributable tag; NetAssets is the JP-GAAP
    # umbrella (includes NCI + stock-acquisition rights) — netted down in _derive() below
    "StockholdersEquity": ["EquityAttributableToOwnersOfParentIFRS", "NetAssets", "EquityIFRS"],
    "_ShareholdersEquityJP": ["ShareholdersEquity"],           # 株主資本 (ex-OCI component)
    "_SubscriptionRights": ["SubscriptionRightsToShares", "ShareAcquisitionRights"],
    "CashAndCashEquivalentsAtCarryingValue":
        ["CashAndDeposits", "CashAndCashEquivalentsIFRS", "CashAndCashEquivalents"],
    "ShortTermInvestments": ["ShortTermInvestmentSecurities", "OtherFinancialAssetsCAIFRS"],
    "LongTermInvestments": ["InvestmentSecurities", "OtherFinancialAssetsNCAIFRS"],
    # debt, JP-GAAP splits it finely — summed (not max'd) in _derive(); the COLL/HAIN lesson
    # says bias to OVER-state debt, and these JPPFS tags don't overlap each other
    "_DebtShortTermLoans": ["ShortTermLoansPayable", "ShortTermBorrowings",
                            "BorrowingsCurrentIFRS", "BondsAndBorrowingsCurrentIFRS"],
    "_DebtCurrentPortionLTL": ["CurrentPortionOfLongTermLoansPayable",
                               "CurrentPortionOfLongTermBorrowings"],
    "_DebtCurrentPortionBonds": ["CurrentPortionOfBonds", "CurrentPortionOfBondsPayable"],
    "_DebtCommercialPaper": ["CommercialPapersLiabilities", "ShortTermBondsPayable"],
    "_DebtBonds": ["BondsPayable", "ConvertibleBonds", "ConvertibleBondTypeBondsWithShareAcquisitionRights"],
    "_DebtLongTermLoans": ["LongTermLoansPayable", "LongTermBorrowings",
                           "BorrowingsNoncurrentIFRS", "BondsAndBorrowingsNoncurrentIFRS"],
    "_DebtLeaseCurrent": ["LeaseObligationsCurrent", "LeaseLiabilitiesCurrentIFRS"],
    "_DebtLeaseNoncurrent": ["LeaseObligationsNoncurrent", "LeaseLiabilitiesNoncurrentIFRS"],
    # IFRS filers sometimes tag only an all-in borrowings total — floor the sum with it
    # (the score.py DebtLongtermAndShorttermCombinedAmount idiom, never added on top)
    "_DebtCombinedIFRS": ["BondsAndBorrowingsIFRS", "BorrowingsIFRS"],
    "NetCashProvidedByUsedInOperatingActivities":
        ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesIFRS"],
    # contract liabilities / customer advances — the Kinki-Sharyo 7122 lesson (batch-2): a
    # build-to-order manufacturer's "net cash" is customer prepayment; populated on next crawl
    "_ContractLiabilities": ["ContractLiabilities", "ContractLiabilitiesCurrent",
                             "AdvancesReceivedOnUncompletedConstructionContractsCLA",
                             "AdvancesReceived"],
    "PaymentsToAcquirePropertyPlantAndEquipment":
        ["PurchaseOfPropertyPlantAndEquipmentInvCF",
         "PurchaseOfPropertyPlantAndEquipmentAndIntangibleAssetsInvCF",
         "PurchaseOfPropertyPlantAndEquipmentInvCFIFRS",
         "PurchaseOfPropertyPlantAndEquipmentAndIntangibleAssetsInvCFIFRS"],
    "MinorityInterest": ["NonControllingInterests", "NonControllingInterestsIFRS"],
    # issued shares — lets the screen price mcap = shares x bulk close instead of per-name
    # yfinance fast_info (which rate-limits at ~40 names/4min). AS-OF-FILING-DATE count
    # FIRST: it reflects post-fiscal-year-end splits (NIHON SEIKO split 1:4 on 2026-04-01;
    # the FYE count made a 41% FCF yield print as 164%). Includes treasury stock -> mcap
    # slightly OVERstated -> conservative for a cheapness screen.
    "_SharesIssued": ["NumberOfIssuedSharesAsOfFilingDateIssuedSharesTotalNumberOfSharesEtc",
                      "TotalNumberOfIssuedSharesSummaryOfBusinessResults",
                      "TotalNumberOfIssuedShares", "TotalNumberOfSharesIssuedSummaryOfBusinessResults"],
}
_LOCAL2KEY = {}                    # local element name -> (our_key, candidate_rank)
for _k, _cands in CONCEPT_MAP.items():
    for _i, _c in enumerate(_cands):
        _LOCAL2KEY.setdefault(_c, (_k, _i))

# DEI (document-entity info) — identity + standard, from the jpdei taxonomy
DEI = {"EDINETCodeDEI": "edinet_code", "SecurityCodeDEI": "sec_code",
       "FilerNameInEnglishDEI": "name_en", "FilerNameInJapaneseDEI": "name_ja",
       "CurrentPeriodEndDateDEI": "period_end", "AccountingStandardsDEI": "std",
       "WhetherConsolidatedFinancialStatementsArePreparedDEI": "has_consol"}


def api_key() -> str | None:
    k = os.environ.get("EDINET_API_KEY")
    if k:
        return k.strip()
    p = os.path.join(DATA, "edinet_key.txt")
    if os.path.exists(p):
        return open(p).read().strip() or None
    return None


def _get(url, timeout=60):
    req = urllib.request.Request(url, headers=HDRS)
    return urllib.request.urlopen(req, timeout=timeout).read()


def list_documents(date: str, key: str) -> list[dict]:
    """All filings submitted on `date` (YYYY-MM-DD), cached to edinet_cache/list_<date>.json."""
    os.makedirs(CACHE, exist_ok=True)
    cf = os.path.join(CACHE, f"list_{date}.json")
    if os.path.exists(cf):
        return json.load(open(cf))["results"]
    d = json.loads(_get(f"{API}/documents.json?date={date}&type=2&Subscription-Key={key}"))
    time.sleep(SLEEP)
    if d.get("metadata", {}).get("status") not in ("200", 200):
        raise RuntimeError(f"documents.json {date}: {d.get('metadata')}")
    json.dump(d, open(cf, "w"), ensure_ascii=False)
    return d.get("results", [])


def annual_reports(results: list[dict]) -> list[dict]:
    """Filter a day's filings to original annual reports of corporate filers (form 030000,
    ordinance 010, not an amendment, has an EDINET code)."""
    return [r for r in results
            if r.get("formCode") == ANNUAL_FORM and r.get("ordinanceCode") == ANNUAL_ORD
            and r.get("edinetCode") and not (r.get("parentDocID"))
            and r.get("docTypeCode") == "120" and r.get("xbrlFlag") == "1"]


def fetch_zip(doc_id: str, key: str, kind: int = 5) -> str | None:
    """Download one filing's data ZIP (kind 5 = CSV facts, 1 = raw XBRL) into the cache.
    Returns the local path (cache hit skips the network). Resumable by construction."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{doc_id}_t{kind}.zip")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    try:
        raw = _get(f"{API}/documents/{doc_id}?type={kind}&Subscription-Key={key}", timeout=120)
        time.sleep(SLEEP)
    except (urllib.error.HTTPError, urllib.error.URLError):
        time.sleep(SLEEP)
        return None
    if raw[:2] != b"PK":                       # JSON error body, not a zip
        return None
    open(path, "wb").write(raw)
    return path


# ---------------------------------------------------------------- extraction

def _extract_from_facts(facts: list[tuple[str, str, float]]) -> dict | None:
    """facts = [(local_elem, contextID, value)] -> mapped concept row (+ _consol flag)."""
    by_key: dict[str, dict[int, list]] = {}
    for local, ctx, val in facts:
        hit = _LOCAL2KEY.get(local)
        if not hit:
            continue
        by_key.setdefault(hit[0], {}).setdefault(hit[1], []).append((ctx, val))
    rec, consol_votes = {}, []
    for key, ranked in by_key.items():
        # CONSOLIDATION OUTRANKS TAG PREFERENCE: an IFRS filer's 有報 carries parent-only
        # JP-GAAP statements alongside the consolidated IFRS ones — ranking tags first let
        # jppfs CashAndDeposits (parent standalone, ¥1.5B) beat CashAndCashEquivalentsIFRS
        # (consolidated, ¥450B) on Fujitsu. Sweep all candidates consolidated-first instead.
        done = False
        for want_consol in (True, False):
            for rank in sorted(ranked):
                for c, v in ranked[rank]:
                    # FilingDateInstant covers the share-count summary rows; everything
                    # else keys off the CurrentYear duration/instant contexts
                    if not (c.startswith("CurrentYear") or c.startswith("FilingDate")):
                        continue
                    is_nc = "NonConsolidated" in c
                    if "Member" in c.replace("NonConsolidatedMember", "") or is_nc == want_consol:
                        continue
                    rec[key] = v
                    rec["_src_" + key] = CONCEPT_MAP[key][rank]   # which tag won (traceability)
                    consol_votes.append(want_consol)
                    done = True
                    break
                if done:
                    break
            if done:
                break
    if not rec:
        return None
    rec["_consol"] = (sum(consol_votes) >= len(consol_votes) / 2) if consol_votes else False
    return rec


def _derive(rec: dict) -> dict:
    """Fold JP-specific components into the score.py contract keys."""
    g = rec.get
    # total debt = sum of the JPPFS splits (non-overlapping; bias over-state — COLL/HAIN lesson)
    debt_parts = [g(k) for k in ("_DebtShortTermLoans", "_DebtCurrentPortionLTL",
                                 "_DebtCurrentPortionBonds", "_DebtCommercialPaper",
                                 "_DebtBonds", "_DebtLongTermLoans",
                                 "_DebtLeaseCurrent", "_DebtLeaseNoncurrent")]
    if any(p is not None for p in debt_parts) or g("_DebtCombinedIFRS") is not None:
        total = max(sum(p for p in debt_parts if p), g("_DebtCombinedIFRS") or 0)
        rec["LongTermDebt"] = total                        # score.py reads this as the LT umbrella
        rec["DebtLongtermAndShorttermCombinedAmount"] = total
    # JP-GAAP NetAssets includes NCI + stock-acquisition rights — net down to parent equity
    if g("_src_StockholdersEquity") in ("NetAssets", "EquityIFRS"):
        eq = g("StockholdersEquity")
        if eq is not None:
            rec["StockholdersEquity"] = eq - (g("MinorityInterest") or 0) - (g("_SubscriptionRights") or 0)
    # capex arrives as a NEGATIVE outflow in EDINET CF statements; score.py subtracts capex,
    # so hand it over as a positive magnitude (same convention as us-gaap Payments* tags)
    for k in ("PaymentsToAcquirePropertyPlantAndEquipment",):
        if rec.get(k) is not None and rec[k] < 0:
            rec[k] = -rec[k]
    return rec


def _decode_edinet_csv(raw: bytes) -> str:
    for enc in ("utf-16", "utf-8-sig", "cp932"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def extract_from_zip(path: str) -> dict | None:
    """One filing ZIP (CSV-facts flavor or raw-XBRL flavor) -> mapped concept row + DEI.
    Every row carries doc_id (from the filename) — the traceability contract."""
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return None
    names = z.namelist()
    facts, dei = [], {}

    csvs = [n for n in names if n.lower().endswith((".csv", ".tsv")) and "jpaud" not in n.lower()]
    if csvs:                                              # EDINET's own fact extraction (type=5)
        for n in csvs:
            txt = _decode_edinet_csv(z.read(n))
            rdr = csv.reader(io.StringIO(txt), delimiter="\t")
            hdr = next(rdr, None)
            if not hdr or len(hdr) < 3:
                continue
            try:
                i_el, i_ctx, i_val = hdr.index("要素ID"), hdr.index("コンテキストID"), hdr.index("値")
            except ValueError:
                continue
            for row in rdr:
                if len(row) <= max(i_el, i_ctx, i_val):
                    continue
                el = row[i_el].split(":")[-1]
                if el in DEI:
                    dei[DEI[el]] = row[i_val].strip()
                    continue
                if el in _LOCAL2KEY:
                    try:
                        facts.append((el, row[i_ctx], float(row[i_val].replace(",", ""))))
                    except ValueError:
                        pass
    else:                                                 # raw XBRL instance (type=1)
        inst = [n for n in names if n.endswith(".xbrl") and "PublicDoc" in n]
        for n in inst:
            try:
                root = ET.fromstring(z.read(n))
            except ET.ParseError:
                continue
            for el in root.iter():
                tag = el.tag.split("}")[-1]
                if tag in DEI and el.text:
                    dei[DEI[tag]] = el.text.strip()
                elif tag in _LOCAL2KEY and el.text:
                    ctx = el.get("contextRef", "")
                    try:
                        facts.append((tag, ctx, float(el.text.replace(",", ""))))
                    except ValueError:
                        pass
    rec = _extract_from_facts(facts)
    if not rec:
        return None
    rec = _derive(rec)
    rec.update(dei)
    # doc identity: API zips carry the docID in the filename; viewer zips are generically
    # named, so fall back to the instance filename inside (jpcrp030000-asr-001_E#####-000_
    # <period>_<ord>_<submitted>) — unique per filing either way
    m = re.match(r"(S[0-9A-Z]{7})", os.path.basename(path))
    inner = next((os.path.basename(n) for n in names
                  if "jpcrp" in n and os.path.basename(n).split(".")[0]), "")
    rec["doc_id"] = m.group(1) if m else (inner.rsplit(".", 1)[0] or os.path.basename(path))
    # score.py housekeeping: annual-only cadence (no quarterly frame in a 有報 crawl)
    rec["_ttm_rolling"] = False
    rec["_ifrs_annual"] = True
    for k in ("OperatingIncomeLoss_prior", "OperatingIncomeLoss_q", "OperatingIncomeLoss_q_prior",
              "Revenues_prior"):
        rec[k] = None
    # JP-GAAP: 特別利益 is below operating income by construction -> EBIT already ex-one-timers;
    # IFRS filers keep the exposure (no reliable discrete tag here) -> flagged via std in screen
    rec["OneTimeGain_q"] = rec["OneTimeGain_q_prior"] = rec["OneTimeGain_ttm"] = 0
    return rec


# ---------------------------------------------------------------- store

def load_store() -> dict:
    return json.load(open(STORE)) if os.path.exists(STORE) else {}


def merge_store(new_rows: dict) -> dict:
    """MERGE by edinet_code, freshest period_end wins — never overwrite-clobber the shared
    store (the recurring DILIGENCE_MASTER bug)."""
    store = load_store()
    for code, rec in new_rows.items():
        old = store.get(code)
        if old is None or (rec.get("period_end") or "") >= (old.get("period_end") or ""):
            store[code] = rec
    os.makedirs(DATA, exist_ok=True)
    json.dump(store, open(STORE, "w"), ensure_ascii=False, indent=1)
    return store


def crawl(dates: list[str], key: str | None = None, max_docs: int | None = None) -> dict:
    """Date-by-date season crawl via the API. Needs the key; browser fallback lives in
    edinet_browser_crawl.py. Returns {edinet_code: concept-row}."""
    key = key or api_key()
    if not key:
        raise SystemExit("no EDINET_API_KEY (env or data/edinet_key.txt) — see INVENTORY.md; "
                         "or use edinet_browser_crawl.py (no-key browser route)")
    out, n = {}, 0
    for date in dates:
        docs = annual_reports(list_documents(date, key))
        print(f"{date}: {len(docs)} annual reports")
        for d in docs:
            if max_docs and n >= max_docs:
                return out
            p = fetch_zip(d["docID"], key, kind=5) or fetch_zip(d["docID"], key, kind=1)
            rec = extract_from_zip(p) if p else None
            if rec and rec.get("edinet_code"):
                rec.setdefault("name_en", d.get("filerName"))
                rec["submitted"] = d.get("submitDateTime")
                out[rec["edinet_code"]] = rec
            n += 1
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dates", nargs="+", required=True, help="YYYY-MM-DD ...")
    ap.add_argument("--max-docs", type=int, default=None)
    a = ap.parse_args()
    rows = crawl(a.dates, max_docs=a.max_docs)
    store = merge_store(rows)
    print(f"crawled {len(rows)} filings -> store now {len(store)} issuers")
