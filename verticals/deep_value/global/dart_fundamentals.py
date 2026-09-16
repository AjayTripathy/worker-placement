"""dart_fundamentals — Korea-leg fundamentals from DART (the FSS's EDGAR), mapped to the
us-gaap-flavored keys score.py already understands (mirrors edinet_fundamentals for Japan).

TWO transports fill the same store (data/dart_store.json); the screen is source-agnostic:

  1. BULK no-auth route (VALIDATED 2026-07-21 — what the first RUN used): OpenDART's
     재무정보 일괄다운로드 ("bulk financial-statement download") serves per-period ZIPs of
     EVERY periodic filer's XBRL facts as cp949 TSVs, NO API key required:
       POST /disclosureinfo/fnltt/dwld/list.do            -> the file list (names carry a
                                                             generation timestamp; re-scrape,
                                                             never hardcode)
       GET  /cmm/downloadFnlttZip.do?fl_nm=<file>.zip      -> the ZIP itself
     Each ZIP splits by statement (BS/PL/CF) x consolidation (연결=consolidated / 별도=separate)
     x sector: banks(은행)/insurers(보험)/securities(증권)/other-financial(금융기타) file in their
     OWN members — so "exclude financials" = simply don't parse those members. FY2025 annual
     (generated 2026-07-16) ≈ 2,100 consolidated + 2,600 separate filers. One ZIP set covers the
     whole market — strictly better than 2,500 keyed per-company calls.

  2. Keyed OpenDART API (needs the free key — signup state + steps in INVENTORY.md):
     corpCode.xml = the bulk company registry (corp_code -> stock_code), and
     fnlttSinglAcntAll.json = per-company full statements (reprt 11011 annual / 11012 half /
     11013 Q1 / 11014 Q3; fs_div CFS consolidated, OFS separate). 20k req/day limit — one
     annual pass over ~2,500 names is fine. Untested pending the key (account created
     2026-07-21, email verification blocked on the expired Gmail MCP token).

KRW values stay NATIVE (full won — Samsung prints Assets 566,942,110,000,000); every ratio is
currency-neutral and the FX bridge lives in the screen's display only.

CONSOLIDATED outranks everything (the Fujitsu lesson): a company's rec comes wholly from the
연결 members if its consolidated BS exists, else wholly from 별도 — the two planes are never
mixed inside one rec.

K-IFRS structural note (the one-time-gain guard): K-IFRS presentation (기업회계기준서 제1001호)
REQUIRES 영업이익 = 수익 - 매출원가 - 판관비, so one-time gains sit below operating income by
construction, same as JP-GAAP's 특별이익 — OneTimeGain_* is structurally 0 here.

Korean-name fallback matching gotcha: 비유동자산 CONTAINS the substring 유동자산 — every
current-bucket name match must guard against the 비유동 prefix.
"""
from __future__ import annotations
import io, json, os, re, time, urllib.parse, urllib.request, zipfile
import xml.etree.ElementTree as ET

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CACHE = os.path.join(DATA, "dart_cache")
STORE = os.path.join(DATA, "dart_store.json")
BASE = "https://opendart.fss.or.kr"
HDRS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Referer": "https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/main.do"}
SLEEP = 1.0                                   # polite on the bulk endpoint (files are ~5MB)

# docu_cd on the bulk page -> (quarter tag in file names, OpenDART reprt_code)
DOCU = {"FY": ("4Q", "11011"), "HY": ("2Q", "11012"), "FQ": ("1Q", "11013"), "TQ": ("3Q", "11014")}

# ---------------------------------------------------------------- concept mapping
# account_id (the XBRL standard codes — ifrs-full_* / dart_*) -> score.py contract keys.
# Ordered best-first. Frequencies from the FY2025 consolidated files are noted where they
# drove the ordering (dart_OperatingIncomeLoss 2,244 of ~2,245 filers, etc).
CONCEPT_MAP = {
    "Revenues": ["ifrs-full_Revenue"],                                  # 2,214/2,245
    "OperatingIncomeLoss": ["dart_OperatingIncomeLoss"],                # 2,244/2,245
    "Assets": ["ifrs-full_Assets"],
    "AssetsCurrent": ["ifrs-full_CurrentAssets"],
    "Liabilities": ["ifrs-full_Liabilities"],
    "LiabilitiesCurrent": ["ifrs-full_CurrentLiabilities"],
    "StockholdersEquity": ["ifrs-full_EquityAttributableToOwnersOfParent",  # 2,133
                           "ifrs-full_Equity"],                         # umbrella; NCI netted below
    "MinorityInterest": ["ifrs-full_NoncontrollingInterests"],
    "CashAndCashEquivalentsAtCarryingValue": ["ifrs-full_CashAndCashEquivalents"],
    # ST investments kept NARROW (over-stating cash manufactures fake cheapness):
    # 단기금융상품 + current FVTPL securities only — NOT OtherCurrentFinancialAssets
    # (that bucket mixes in receivable-like items).
    "_STInvDeposits": ["ifrs-full_ShorttermDepositsNotClassifiedAsCashEquivalents"],  # 1,005
    "_STInvFVTPL": ["ifrs-full_CurrentFinancialAssetsAtFairValueThroughProfitOrLoss",
                    "ifrs-full_CurrentFinancialAssetsAtFairValueThroughProfitOrLossMandatorilyMeasuredAtFairValue",
                    "ifrs-full_CurrentFinancialAssetsAtFairValueThroughProfitOrLossDesignatedUponInitialRecognition",
                    "dart_CurrentFinancialAssetDesignationAsAtFairValueThroughProfitOrLoss",
                    "ifrs-full_CurrentFinancialAssetsMeasuredAtFairValueThroughOtherComprehensiveIncome"],
    "_STInvAC": ["ifrs-full_CurrentFinancialAssetsAtAmortisedCost"],  # 단기투자증권/예치금 (97 filers)
    # LT passive (PFIC asset-test numerator): LT deposits + investment securities across ALL
    # K-IFRS measurement categories — FVOCI, FVTPL, amortised-cost, EquityInstrumentsHeld
    # (장기투자증권: the 079960 Dongyang E&P miss — ₩97bn sat here untagged by the original map,
    # printing pfic_fmv_share 0.46 on a true ~1.0). Bias = OVER-capture (conservative: more
    # PFIC flags on the shelf where the poison hides). Frequencies from the FY2025 연결 BS.
    # Equity-method stakes (InvestmentAccountedForUsingEquityMethod) stay EXCLUDED:
    # >=25% look-through stakes count as active for §1297 — the chaebol cross-holding plane
    # would otherwise false-flag half the shelf.
    "_LTInvDeposits": ["dart_LongTermDepositsNotClassifiedAsCashEquivalents"],         # 740
    "_LTInvFVOCI": ["ifrs-full_NoncurrentFinancialAssetsMeasuredAtFairValueThroughOtherComprehensiveIncome",  # 511
                    "ifrs-full_NoncurrentFinancialAssetsAtFairValueThroughOtherComprehensiveIncome",          # 117
                    "ifrs-full_FinancialAssetsAtFairValueThroughOtherComprehensiveIncome",       # 62 (unsplit -> LT)
                    "ifrs-full_NoncurrentInvestmentsInEquityInstrumentsDesignatedAtFairValueThroughOtherComprehensiveIncome"],
    "_LTInvFVTPL": ["ifrs-full_NoncurrentFinancialAssetsAtFairValueThroughProfitOrLoss",
                    "ifrs-full_NoncurrentFinancialAssetsAtFairValueThroughProfitOrLossMandatorilyMeasuredAtFairValue",
                    "ifrs-full_NoncurrentFinancialAssetsAtFairValueThroughProfitOrLossDesignatedUponInitialRecognition",
                    "ifrs-full_FinancialAssetsAtFairValueThroughProfitOrLoss",                   # 95 (unsplit -> LT)
                    "ifrs-full_FinancialAssetsAtFairValueThroughProfitOrLossDesignatedAsUponInitialRecognition"],
    "_LTInvAC": ["ifrs-full_NoncurrentFinancialAssetsAtAmortisedCost"],                # 92
    "_LTInvEquityInstr": ["ifrs-full_EquityInstrumentsHeld"],                           # 장기투자증권
    # over-capture umbrellas, PFIC-ONLY (kept OUT of netcash — they mix in guarantee deposits
    # and accrued items): routed to OtherLongTermInvestments, which pfic_screen.PASSIVE_CONCEPTS
    # and the screen's FMV overlay count but score.py's netcash never sees
    "_InvOtherFin": ["ifrs-full_OtherNoncurrentFinancialAssets",                        # 1,487
                     "ifrs-full_OtherCurrentFinancialAssets"],                          # 1,368
    # debt — two presentation styles per bucket; max(style A, style B) per bucket, then sum
    # buckets (the score.py overlap-safe idiom; bias = over-state, the COLL/HAIN lesson)
    "_DebtCurSpecificST": ["ifrs-full_ShorttermBorrowings"],            # 1,077
    "_DebtCurSpecificLTP": ["ifrs-full_CurrentPortionOfLongtermBorrowings"],
    "_DebtCurSpecificBond": ["dart_CurrentPortionOfBonds"],
    "_DebtCurSpecificCB": ["dart_CurrentPortionOfConvertibleBonds"],
    "_DebtCurCombined": ["ifrs-full_CurrentLoansReceivedAndCurrentPortionOfNoncurrentLoansReceived",
                         "ifrs-full_CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings"],
    "_DebtNoncurLoans": ["ifrs-full_LongtermBorrowings", "dart_LongTermBorrowingsGross",
                         "ifrs-full_NoncurrentPortionOfNoncurrentLoansReceived"],
    "_DebtNoncurBonds": ["ifrs-full_NoncurrentPortionOfNoncurrentBondsIssued", "dart_BondsIssued"],
    "_DebtCB": ["dart_ConvertibleBonds"],
    "_DebtLeaseCur": ["ifrs-full_CurrentLeaseLiabilities"],
    "_DebtLeaseNoncur": ["ifrs-full_NoncurrentLeaseLiabilities"],
    "_ContractAdvances": ["ifrs-full_ContractLiabilities", "ifrs-full_CurrentContractLiabilities",
                          "ifrs-full_NoncurrentContractLiabilities", "dart_Advances"],
    "NetCashProvidedByUsedInOperatingActivities":
        ["ifrs-full_CashFlowsFromUsedInOperatingActivities"],           # 2,174 across label styles
    "PaymentsToAcquirePropertyPlantAndEquipment":
        ["ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"],  # 1,918
}
_CODE2KEY = {}
for _k, _cands in CONCEPT_MAP.items():
    for _i, _c in enumerate(_cands):
        _CODE2KEY.setdefault(_c, (_k, _i))

# Korean 항목명 fallback (custom/non-standard account codes). Matched on the label with
# whitespace + list-numbering stripped. Guards: current-bucket names reject a 비유동 prefix;
# 영업손실-labelled custom rows can carry unsigned magnitudes — code-matched rows win first,
# so the residual exposure is tiny (44 filers use the 영업손실 label, nearly all code-tagged).
NAME_MAP = [
    ("Revenues", ("매출액", "수익(매출액)", "영업수익", "매출")),
    ("OperatingIncomeLoss", ("영업이익(손실)", "영업이익", "영업손실")),
    ("Assets", ("자산총계",)),
    ("AssetsCurrent", ("유동자산",)),
    ("Liabilities", ("부채총계",)),
    ("LiabilitiesCurrent", ("유동부채",)),
    ("StockholdersEquity", ("지배기업소유주지분", "지배기업의소유주에게귀속되는자본",
                            "지배기업소유주에게귀속되는자본", "지배기업의소유지분")),
    ("MinorityInterest", ("비지배지분",)),
    ("CashAndCashEquivalentsAtCarryingValue", ("현금및현금성자산",)),
    # convertible/BW paper by LABEL (Hyunwoo 092300 lesson, batch-2): the code tier missed a
    # custom-tagged 유동성전환사채 of ₩11.3B -> net-cash 61% printed vs 29% true. Exact-match
    # tier, so 유동성전환사채 cannot collide with 전환사채.
    ("_DebtCurSpecificCB", ("유동성전환사채", "유동전환사채", "전환사채(유동)",
                            "유동성신주인수권부사채")),
    ("_DebtCB", ("전환사채", "신주인수권부사채", "교환사채")),
    # contract advances (Hancom 372910 lesson: 선수금 EXCEEDED total cash — prepay-float mask)
    ("_ContractAdvances", ("계약부채", "선수금", "유동계약부채", "비유동계약부채", "선수수익")),
    ("_STInvDeposits", ("단기금융상품", "단기투자자산", "단기투자증권")),
    ("NetCashProvidedByUsedInOperatingActivities",
     ("영업활동현금흐름", "영업활동으로인한현금흐름", "영업활동으로인한순현금흐름", "영업활동순현금흐름")),
    ("PaymentsToAcquirePropertyPlantAndEquipment", ("유형자산의취득",)),
]
_NONCUR_GUARDED = {"AssetsCurrent", "LiabilitiesCurrent"}

# contains-tier for custom-coded INVESTMENT labels (fires only when both the standard-code
# lookup and the exact-name tier miss, and ONLY on 재무상태표 rows — the CF statement carries
# same-named FLOW rows like 당기손익-공정가치측정금융자산의 취득/처분 that must never sum into a
# balance). Guards: 부채 (the FVTPL *liability* twin) and 누계액 (기타포괄손익누계액 is an equity
# line) never match. Current-labelled hits go to the PFIC-only bucket (netcash stays narrow);
# everything else is LT.
_INV_NAME_PAT = ("투자유가증권", "투자증권", "장기투자자산", "장기금융상품", "만기보유",
                 "공정가치측정금융자산", "공정가치금융자산", "상각후원가측정금융자산")
_INV_NAME_BLOCK = ("부채", "누계액", "매출채권", "미수", "취득", "처분", "평가", "감소", "증가")


def _inv_name_key(lab: str) -> str | None:
    if any(b in lab for b in _INV_NAME_BLOCK):
        return None
    if not any(p in lab for p in _INV_NAME_PAT):
        return None
    cur = ("유동" in lab and "비유동" not in lab) or lab.startswith("단기") or "유동성" in lab
    return "_InvOtherFin" if cur else "_LTInvNamed"


def api_key() -> str | None:
    k = os.environ.get("DART_API_KEY")
    if k:
        return k.strip()
    p = os.path.join(DATA, "dart_key.txt")
    if os.path.exists(p):
        return open(p).read().strip() or None
    return None


def _get(url, timeout=120, data=None, hdrs=None):
    req = urllib.request.Request(url, data=data, headers={**HDRS, **(hdrs or {})})
    return urllib.request.urlopen(req, timeout=timeout).read()


# ---------------------------------------------------------------- bulk (no-auth) transport

def bulk_file_index() -> dict:
    """{(year, docu_cd, role): fl_nm} from the bulk-download list page (no auth). File names
    carry a generation timestamp, so this is scraped fresh (cached 1 day)."""
    cf = os.path.join(CACHE, "bulk_index.json")
    if os.path.exists(cf) and time.time() - os.path.getmtime(cf) < 86400:
        raw = json.load(open(cf))
        return {tuple(k.split("|")): v for k, v in raw.items()}
    html = _get(f"{BASE}/disclosureinfo/fnltt/dwld/list.do", data=b"",
                hdrs={"X-Requested-With": "XMLHttpRequest"}).decode("utf-8", "replace")
    idx = {}
    for yr, docu, role, fl in re.findall(
            r"download_ext002\('(\d{4})','(\w{2})',\s*'(\w{2})',\s*'([^']+\.zip)'\)", html):
        idx[(yr, docu, role)] = fl
    os.makedirs(CACHE, exist_ok=True)
    json.dump({"|".join(k): v for k, v in idx.items()}, open(cf, "w"))
    if not idx:
        raise RuntimeError("bulk list page yielded no files — layout change or block")
    return idx


def bulk_fetch(year: str, docu: str, roles=("BS", "PL", "CF")) -> dict:
    """Download the bulk ZIPs for one (year, report) into the cache. Resumable by construction
    (cache hit skips the network). Returns {role: local_path}."""
    idx = bulk_file_index()
    out = {}
    q = DOCU[docu][0]
    os.makedirs(CACHE, exist_ok=True)
    for role in roles:
        path = os.path.join(CACHE, f"{year}_{q}_{role}.zip")
        if os.path.exists(path) and os.path.getsize(path) > 0:
            out[role] = path
            continue
        fl = idx.get((year, docu, role))
        if not fl:
            print(f"  bulk file missing on DART: {year} {docu} {role}")
            continue
        raw = _get(f"{BASE}/cmm/downloadFnlttZip.do?fl_nm={urllib.parse.quote(fl)}")
        time.sleep(SLEEP)
        if raw[:2] != b"PK":
            print(f"  {fl}: not a zip ({raw[:60]!r})")
            continue
        open(path, "wb").write(raw)
        out[role] = path
    return out


def _zip_members(path):
    z = zipfile.ZipFile(path)
    for i in z.infolist():
        try:
            nm = i.filename.encode("cp437").decode("cp949")   # zip names are cp949-mangled
        except (UnicodeDecodeError, UnicodeEncodeError):
            nm = i.filename
        yield z, nm, i


_FIN_SECTOR = ("금융기타", "보험", "은행", "증권")               # sector-format filers = the financials


def _clean_label(s: str) -> str:
    s = re.sub(r"^[IVXⅠⅡⅢⅣⅤ]+\s*\.\s*", "", s.strip())        # "Ⅰ.영업활동현금흐름" style
    return s.replace(" ", "").replace("　", "")


def _num(s: str):
    s = s.strip().replace(",", "")
    if not s or s in ("-", "0.0"):
        return None if s != "0.0" else 0.0
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def parse_bulk_zip(path: str, consolidated: bool) -> dict:
    """One bulk ZIP -> {stock_code: {facts + identity}} from the requested consolidation plane.
    Financial-sector members (은행/보험/증권/금융기타) are SKIPPED — that's the financials carve-out.
    Facts land as (our_key, rank) candidates; _resolve() picks winners per company."""
    want_suffix = "_연결"                                  # consolidated members end 연결
    out: dict[str, dict] = {}
    for z, nm, info in _zip_members(path):
        if not nm.endswith(".txt"):
            continue
        base = nm.rsplit("_", 1)[0]                        # strip the generation date
        if any(f"_{s}" in base for s in _FIN_SECTOR):
            continue
        is_consol = base.endswith(want_suffix.rstrip("_")) and "_연결" in base
        if is_consol != consolidated:
            continue
        is_bs = "재무상태표" in base                        # inv name-tier fires on BS rows only
        txt = z.read(info).decode("cp949", "replace")
        lines = txt.splitlines()
        hdr = lines[0].split("\t")
        try:
            i_code = hdr.index("종목코드"); i_nm = hdr.index("회사명")
            i_mkt = hdr.index("시장구분"); i_ind = hdr.index("업종")
            i_indnm = hdr.index("업종명"); i_pe = hdr.index("결산기준일")
            i_acc = hdr.index("항목코드"); i_lab = hdr.index("항목명")
        except ValueError:
            continue
        # current-period column: annual files say 당기; interim files say 당기 1분기말 /
        # 당기 1분기 3개월 / 당기 1분기 누적 — prefer the cumulative (누적) flow column
        cur_cands = [j for j, h in enumerate(hdr) if h.strip().startswith("당기")]
        if not cur_cands:
            continue
        i_cur = next((j for j in cur_cands if "누적" in hdr[j]), cur_cands[0])
        for ln in lines[1:]:
            p = ln.split("\t")
            if len(p) <= i_cur:
                continue
            code = p[i_code].strip("[] ")
            if not code:
                continue
            c = out.setdefault(code, {
                "stock_code": code, "name": p[i_nm].strip(), "market": p[i_mkt].strip(),
                "ksic": p[i_ind].strip(), "ksic_nm": p[i_indnm].strip(),
                "period_end": p[i_pe].strip(), "_facts": {}})
            val = _num(p[i_cur])
            if val is None:
                continue
            acc = p[i_acc].strip()
            hit = _CODE2KEY.get(acc)
            if hit:
                key, rank = hit
                c["_facts"].setdefault(key, {})
                c["_facts"][key].setdefault(("code", rank), val)
                continue
            lab = _clean_label(p[i_lab])
            for key, names in NAME_MAP:
                if lab in names:
                    if key in _NONCUR_GUARDED and "비유동" in lab:
                        break
                    c["_facts"][key] = c["_facts"].get(key, {})
                    c["_facts"][key].setdefault(("name", 99), val)
                    break
            else:
                ik = _inv_name_key(lab) if is_bs else None
                if ik:                                     # sum-key: every row kept (unique seq)
                    d = c["_facts"].setdefault(ik, {})
                    d[("name", 99, len(d))] = val
    return out


_SUM_KEYS = {"_InvOtherFin", "_LTInvNamed"}                # buckets whose candidates ADD, not compete


def _resolve(facts: dict) -> dict:
    """Candidate facts -> flat concept row: standard-code matches outrank name matches,
    lower candidate rank wins within a tier. SUM-keys (the over-capture investment buckets)
    sum every candidate instead — OtherCurrent + OtherNoncurrent are different assets."""
    rec = {}
    for key, cands in facts.items():
        if key in _SUM_KEYS:
            rec[key] = sum(cands.values())
            continue
        best = sorted(cands.items(), key=lambda kv: (kv[0][0] != "code", kv[0][1]))[0]
        rec[key] = best[1]
    return rec


def _derive(rec: dict) -> dict:
    """Fold the K-IFRS components into the score.py contract keys."""
    g = rec.get
    # debt: per-bucket max of presentation styles, buckets summed (overlap-safe)
    cur_specific = sum((g(k) or 0) for k in ("_DebtCurSpecificST", "_DebtCurSpecificLTP",
                                             "_DebtCurSpecificBond", "_DebtCurSpecificCB"))
    cur = max(cur_specific, g("_DebtCurCombined") or 0)
    noncur = (g("_DebtNoncurLoans") or 0) + (g("_DebtNoncurBonds") or 0) + (g("_DebtCB") or 0)
    lease = (g("_DebtLeaseCur") or 0) + (g("_DebtLeaseNoncur") or 0)
    total = cur + noncur + lease
    if any(g(k) is not None for k in ("_DebtCurSpecificST", "_DebtCurSpecificLTP",
                                     "_DebtCurSpecificBond", "_DebtCurSpecificCB",
                                     "_DebtCurCombined", "_DebtNoncurLoans", "_DebtNoncurBonds",
                                     "_DebtCB", "_DebtLeaseCur", "_DebtLeaseNoncur")):
        rec["LongTermDebt"] = total
        rec["DebtLongtermAndShorttermCombinedAmount"] = total
    # investments -> the pfic_screen / netcash contract keys.
    # ShortTermInvestments (feeds netcash): deposits + FVTPL/FVOCI securities + amortised-cost
    # 단기투자증권 — genuine near-cash only.
    st_keys = ("_STInvDeposits", "_STInvFVTPL", "_STInvAC")
    if any(g(k) is not None for k in st_keys):
        rec["ShortTermInvestments"] = sum((g(k) or 0) for k in st_keys)
    # LongTermInvestments (PFIC + pfic_screen book test): every LT securities category.
    lt_keys = ("_LTInvDeposits", "_LTInvFVOCI", "_LTInvFVTPL", "_LTInvAC",
               "_LTInvEquityInstr", "_LTInvNamed")
    if any(g(k) is not None for k in lt_keys):
        rec["LongTermInvestments"] = sum((g(k) or 0) for k in lt_keys)
    # OtherLongTermInvestments (PFIC-ONLY over-capture): the other-financial-asset umbrellas.
    # pfic_screen.PASSIVE_CONCEPTS counts this key; score.py netcash never reads it.
    if g("_InvOtherFin") is not None:
        rec["OtherLongTermInvestments"] = g("_InvOtherFin")
    # capex: score.py subtracts a positive magnitude (us-gaap Payments* convention);
    # the bulk CF prints 취득 rows as negative outflows for some filers — normalize
    k = "PaymentsToAcquirePropertyPlantAndEquipment"
    if rec.get(k) is not None and rec[k] < 0:
        rec[k] = -rec[k]
    return rec


def build_from_bulk(year: str, docu: str) -> dict:
    """One bulk (year, report) pass -> {stock_code: score.py-ready rec}. Consolidated (연결)
    outranks separate (별도): a company with a consolidated BS takes its WHOLE rec from the
    consolidated plane; the two planes are never mixed (the Fujitsu lesson)."""
    paths = bulk_fetch(year, docu)
    if "BS" not in paths:
        raise RuntimeError(f"no BS bulk file for {year} {docu}")
    planes = {}
    for consolidated in (True, False):
        merged: dict[str, dict] = {}
        for role in ("BS", "PL", "CF"):
            if role not in paths:
                continue
            part = parse_bulk_zip(paths[role], consolidated)
            for code, c in part.items():
                m = merged.setdefault(code, {k: v for k, v in c.items() if k != "_facts"})
                m.setdefault("_facts", {})
                for key, cands in c["_facts"].items():
                    m["_facts"].setdefault(key, {}).update(
                        {k2: v2 for k2, v2 in cands.items() if k2 not in m["_facts"].get(key, {})})
        planes[consolidated] = merged
    out = {}
    reprt = DOCU[docu][1]
    for code in set(planes[True]) | set(planes[False]):
        use_consol = code in planes[True] and planes[True][code]["_facts"].get("Assets")
        src = planes[True][code] if use_consol else planes[False].get(code) or planes[True][code]
        rec = {k: v for k, v in src.items() if k != "_facts"}
        rec.update(_resolve(src["_facts"]))
        # umbrella-equity fallback: net NCI out of 자본총계 when no parent-attributable tag
        if rec.get("StockholdersEquity") is not None and use_consol:
            f = src["_facts"].get("StockholdersEquity", {})
            won = sorted(f.items(), key=lambda kv: (kv[0][0] != "code", kv[0][1]))[0][0]
            if won == ("code", 1):                          # ifrs-full_Equity (the umbrella)
                rec["StockholdersEquity"] -= (rec.get("MinorityInterest") or 0)
        rec = _derive(rec)
        rec["_consol"] = bool(use_consol)
        rec["reprt_code"] = reprt
        rec["src"] = f"dart_bulk_{year}_{docu}"
        # score.py housekeeping: annual/period cadence, no rolling TTM, K-IFRS 영업이익 is
        # structurally ex-one-timers (기준서 1001 presentation rule)
        rec["_ttm_rolling"] = False
        rec["_ifrs_annual"] = True
        for k in ("OperatingIncomeLoss_prior", "OperatingIncomeLoss_q",
                  "OperatingIncomeLoss_q_prior", "Revenues_prior"):
            rec[k] = None
        rec["OneTimeGain_q"] = rec["OneTimeGain_q_prior"] = rec["OneTimeGain_ttm"] = 0
        out[code] = rec
    return out


# ---------------------------------------------------------------- keyed API transport
# (UNTESTED pending the key — the account exists, email verification pending; INVENTORY.md)

def fetch_corp_codes(key: str | None = None) -> dict:
    """corpCode.xml (keyed) -> {stock_code: corp_code} for listed names, cached."""
    key = key or api_key()
    if not key:
        raise SystemExit("no DART_API_KEY (env or data/dart_key.txt) — see INVENTORY.md; "
                         "the bulk route (build_from_bulk) needs no key")
    cf = os.path.join(CACHE, "corp_codes.json")
    if os.path.exists(cf):
        return json.load(open(cf))
    raw = _get(f"{BASE}/api/corpCode.xml?crtfc_key={key}")
    z = zipfile.ZipFile(io.BytesIO(raw))
    root = ET.fromstring(z.read(z.namelist()[0]))
    out = {}
    for el in root.iter("list"):
        stock = (el.findtext("stock_code") or "").strip()
        if stock and stock != " ":
            out[stock] = {"corp_code": el.findtext("corp_code"),
                          "name": el.findtext("corp_name")}
    os.makedirs(CACHE, exist_ok=True)
    json.dump(out, open(cf, "w"), ensure_ascii=False)
    return out


def fetch_company(corp_code: str, year: str, reprt: str = "11011",
                  key: str | None = None) -> dict | None:
    """fnlttSinglAcntAll.json for one company (keyed) -> score.py-ready rec. CFS preferred,
    OFS fallback. Cached per (corp, year, reprt) — resumable; ~0.1s pacing is far inside the
    20k/day limit."""
    key = key or api_key()
    if not key:
        raise SystemExit("DART_API_KEY required for the per-company API — see INVENTORY.md")
    os.makedirs(CACHE, exist_ok=True)
    for fs_div in ("CFS", "OFS"):
        cf = os.path.join(CACHE, f"api_{corp_code}_{year}_{reprt}_{fs_div}.json")
        if os.path.exists(cf):
            d = json.load(open(cf))
        else:
            url = (f"{BASE}/api/fnlttSinglAcntAll.json?crtfc_key={key}&corp_code={corp_code}"
                   f"&bsns_year={year}&reprt_code={reprt}&fs_div={fs_div}")
            d = json.loads(_get(url))
            time.sleep(0.1)
            if d.get("status") in ("000", "013"):          # 013 = no data (cache the miss too)
                json.dump(d, open(cf, "w"), ensure_ascii=False)
            else:
                raise RuntimeError(f"fnlttSinglAcntAll {corp_code}: {d.get('status')} {d.get('message')}")
        rows = d.get("list") or []
        if not rows:
            continue
        facts = {}
        for r in rows:
            val = _num(str(r.get("thstrm_amount") or ""))
            if val is None:
                continue
            acc = (r.get("account_id") or "").replace(":", "_").strip()
            hit = _CODE2KEY.get(acc)
            if hit:
                facts.setdefault(hit[0], {}).setdefault(("code", hit[1]), val)
                continue
            lab = _clean_label(r.get("account_nm") or "")
            for kk, names in NAME_MAP:
                if lab in names:
                    if kk in _NONCUR_GUARDED and "비유동" in lab:
                        break
                    facts.setdefault(kk, {}).setdefault(("name", 99), val)
                    break
            else:
                ik = _inv_name_key(lab) if (r.get("sj_div") == "BS") else None
                if ik:
                    d = facts.setdefault(ik, {})
                    d[("name", 99, len(d))] = val
        if not facts.get("Assets"):
            continue
        rec = _resolve(facts)
        rec = _derive(rec)
        rec.update({"_consol": fs_div == "CFS", "reprt_code": reprt,
                    "src": f"dart_api_{year}_{reprt}_{fs_div}",
                    "_ttm_rolling": False, "_ifrs_annual": True,
                    "OneTimeGain_q": 0, "OneTimeGain_q_prior": 0, "OneTimeGain_ttm": 0})
        for k in ("OperatingIncomeLoss_prior", "OperatingIncomeLoss_q",
                  "OperatingIncomeLoss_q_prior", "Revenues_prior"):
            rec[k] = None
        return rec
    return None


# ---------------------------------------------------------------- store

def load_store() -> dict:
    return json.load(open(STORE)) if os.path.exists(STORE) else {}


def merge_store(new_rows: dict, interim: dict | None = None) -> dict:
    """MERGE by stock_code, freshest period_end wins — never overwrite-clobber the shared
    store (the recurring DILIGENCE_MASTER bug). Interim recs attach under rec['interim']
    (kept SEPARATE from the annual keys: the screen's flows always come from one coherent
    statement set, never an annual/interim mix)."""
    store = load_store()
    for code, rec in new_rows.items():
        old = store.get(code)
        if old is None or (rec.get("period_end") or "") >= (old.get("period_end") or ""):
            keep_interim = (old or {}).get("interim")
            store[code] = rec
            if keep_interim:
                store[code]["interim"] = keep_interim
    for code, rec in (interim or {}).items():
        if code in store:
            old_i = store[code].get("interim") or {}
            if (rec.get("period_end") or "") >= (old_i.get("period_end") or ""):
                store[code]["interim"] = {k: v for k, v in rec.items()
                                          if not k.startswith("OneTimeGain")}
    os.makedirs(DATA, exist_ok=True)
    json.dump(store, open(STORE, "w"), ensure_ascii=False, indent=1)
    return store


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", default="2025")
    ap.add_argument("--docu", default="FY", choices=list(DOCU))
    ap.add_argument("--interim-year", default="2026")
    ap.add_argument("--interim-docu", default="FQ", choices=list(DOCU),
                    help="latest interim (2026 H1 lands late-Aug; 1Q is the latest until then)")
    a = ap.parse_args()
    annual = build_from_bulk(a.year, a.docu)
    print(f"annual {a.year} {a.docu}: {len(annual)} filers "
          f"({sum(1 for r in annual.values() if r['_consol'])} consolidated)")
    interim = build_from_bulk(a.interim_year, a.interim_docu)
    print(f"interim {a.interim_year} {a.interim_docu}: {len(interim)} filers")
    store = merge_store(annual, interim)
    print(f"store: {len(store)} issuers -> {STORE}")
