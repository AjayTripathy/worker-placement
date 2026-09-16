"""subthreshold_arb_scanner — Stage 0b CARRY generator: SUB-THRESHOLD all-cash merger arb.

THE CAPACITY CEILING IS THE EDGE. Merger-arb funds run billions and can't be bothered with a
$200M all-cash take-out — the absolute $-edge per name is too small to move their book and the
target's float can't absorb their size. So SMALL cash deals (<~$500M target equity value) carry a
WIDER spread for the SAME regulatory / financing / MAC break risk as a large deal that arb desks
crowd to a few bps. A small investor + AI reading EVERY recent merger 8-K captures that neglected
carry — the office capacity-ceiling edge (fee-replication CARRY, ours by design).

v1 finds RECENT all-cash merger agreements from PRIMARY SEC data — nothing fabricated:
  1. DISCOVER   EDGAR EFTS full-text search over 8-K / DEFM14A for merger-agreement language in the
                last ~120 days -> target issuer CIK + the announcing exhibit URL.
  2. PARSE      the CASH per-share consideration ("$X.XX per share in cash") from the exhibit text;
                stock/mixed deals with no clean cash number are SET ASIDE (skipped_non_cash), never guessed.
  3. RESOLVE    CIK -> ticker (SEC company_tickers.json); pull LIVE price + shares out (yfinance).
  4. SIZE       deal_value_est = offer x shares_out; KEEP only sub-threshold (< ~$500M).
  5. SPREAD     spread = (offer - price) / price; annualized if a target/expected close is stated.

Break risk is REAL and larger for small deals (financing contingencies, MAC outs, thin sponsors) —
every candidate carries a break-risk caveat and, where cheap, the announced financing/regulatory
conditions. A wide spread is NOT free money: the DD/court step is why the market pays that spread.
Unresolvable tickers self-drop (reported, never silent). NO offer prices are fabricated — real filings only.

    python3 verticals/generators/subthreshold_arb_scanner.py [--days 120] [--max-value 500]
Writes data/SUBTHRESHOLD_ARB.json. READ-ONLY. (A CARRY generator — never an order.)
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "SUBTHRESHOLD_ARB.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}

TICKERS_MAP = "https://www.sec.gov/files/company_tickers.json"
EFTS = "https://efts.sec.gov/LATEST/search-index"
ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{doc}"

# full-text queries that surface a cash merger agreement / announcement. Each is an EFTS phrase.
QUERIES = [
    '"per share in cash"',
    '"Agreement and Plan of Merger"',
]
FORMS = "8-K,DEFM14A,DEFA14A,SC 14D9"

# sub-threshold ceiling ($ target equity value) — where the arb desks stop bothering.
DEFAULT_MAX_VALUE_M = 500.0
# a computed offer must be a sane equity take-out price; outside this = a mis-parse (e.g. a bond
# redemption price, a per-unit distribution) -> discard rather than emit a fabricated offer.
OFFER_LO, OFFER_HI = 0.50, 2000.0

# "$X.XX per share in cash" and close cousins. Ordered most-specific first; first sane hit wins.
CASH_PATS = [
    r"\$\s*([0-9]{1,4}(?:,[0-9]{3})*(?:\.[0-9]{1,4})?)\s+(?:in\s+cash\s+)?per\s+share(?:\s+in\s+cash)?",
    r"\$\s*([0-9]{1,4}(?:,[0-9]{3})*(?:\.[0-9]{1,4})?)\s+per\s+(?:share\s+of\s+common\s+stock\s+)?in\s+cash",
    r"cash\s+(?:payment|consideration)\s+of\s+\$\s*([0-9]{1,4}(?:,[0-9]{3})*(?:\.[0-9]{1,4})?)\s+per\s+share",
    r"\$\s*([0-9]{1,4}(?:,[0-9]{3})*(?:\.[0-9]{1,4})?)\s+per\s+share\s+of\s+(?:common\s+stock|the\s+Company)",
]
# NON-DEAL / non-binding tells: a "$X per share" that is NOT a signed all-shares cash take-out.
# These are the dominant full-text false positives — a going-private PROPOSAL (indication of interest,
# not a signed agreement), or a PIPE/investment where someone buys NEW shares FROM the company at $X.
NONDEAL_TELLS = [
    r"non-?binding", r"indication\s+of\s+interest", r"preliminary\s+(?:non-?binding\s+)?proposal",
    r"proposes\s+a\s+going-private", r"has\s+(?:agreed|proposes)\s+to\s+acquire\s+[\d,]+\s+shares",
    r"purchase\s+(?:of\s+)?[\d,]+\s+shares", r"private\s+placement", r"subscription\s+agreement",
    r"at\s+a\s+price\s+of\s+at\s+least", r"letter\s+of\s+intent",
]
# POSITIVE tells that this IS a definitive all-shares cash acquisition (require at least one).
DEAL_TELLS = [
    r"definitive\s+(?:merger\s+)?agreement", r"Agreement\s+and\s+Plan\s+of\s+Merger",
    r"each\s+(?:issued\s+and\s+outstanding\s+)?share.{0,40}(?:converted|cancelled|right\s+to\s+receive)",
    r"outstanding\s+shares?.{0,60}(?:acqui|merger|will\s+be\s+(?:converted|cancelled))",
    r"tender\s+offer", r"take[\s-]private", r"will\s+be\s+acquired", r"to\s+be\s+acquired\s+by",
    r"merger\s+consideration",
]

# SPAC / de-SPAC tells: a "$X per share" here is trust/redemption or a business-combination value,
# NOT a cash take-out of an operating target. These belong to spac_trust_arb_scanner, not this one.
SPAC_TELLS = [
    r"blank\s+check", r"business\s+combination", r"trust\s+account", r"Surviving\s+Pubco",
    r"redeem\w*\s+(?:their\s+)?(?:public\s+)?shares", r"Class\s+A\s+ordinary\s+shares",
    r"initial\s+public\s+offering.{0,40}trust", r"de-?SPAC",
]

# tells that the deal is stock / mixed (no clean cash number) — set aside, don't guess.
STOCK_TELLS = [
    r"exchange\s+ratio", r"shares?\s+of\s+(?:the\s+)?(?:acquir|parent|buyer)", r"stock-for-stock",
    r"fixed\s+exchange", r"per\s+share\s+in\s+(?:the\s+form\s+of\s+)?(?:stock|shares|equity)",
    r"elect(?:ion)?\s+to\s+receive\s+(?:either\s+)?(?:cash\s+or|stock)",
]
# expected-close phrasing -> a rough close date/quarter for annualization.
CLOSE_PATS = [
    r"expected\s+to\s+close\s+(?:in|by|during|no\s+later\s+than)\s+(?:the\s+)?([A-Za-z0-9,\s]{4,40}?)(?:\.|,|\s+subject|\s+and)",
    r"clos(?:e|ing)\s+is\s+expected\s+(?:in|by|during)\s+(?:the\s+)?([A-Za-z0-9,\s]{4,40}?)(?:\.|,|\s+subject)",
    r"anticipated\s+to\s+(?:be\s+)?clos(?:e|ing)?\s+(?:in|by|during)\s+(?:the\s+)?([A-Za-z0-9,\s]{4,40}?)(?:\.|,|\s+subject)",
]
# ---------------------------------------------------------------------------
# DEAL-QUALITY GATES (added after e2e DD: the "wider spread, same risk" thesis only holds for CLEAN
# small deals). Two independent traps the raw scanner used to surface as clean carry:
#   * BOARD-REJECTED / HOSTILE — DXLG: an unsolicited, board-REJECTED tender by Camac/Zodiac. The
#     target board unanimously recommends stockholders REJECT; the ~30% spread correctly prices a
#     near-zero close probability. NOT a clean arb -> EXCLUDE.
#   * UNCOMMITTED FINANCING — LSTA: a SIGNED, board-recommended deal, but the bidder's own words are
#     "do not have committed financing"; only a non-binding LOI backs it. The ~7% spread prices real
#     break risk. NOT clean carry -> EXCLUDE (or strongly flag).
#
# board_stance (from the TARGET's recommendation in its SC 14D9 / merger proxy):
#   'rejected'    — board recommends REJECT / vote AGAINST, or the offer is unsolicited / hostile /
#                   not approved by the Board  -> EXCLUDE.
#   'recommended' — board recommends FOR / accept / adopt (a friendly, board-approved deal).
#   'unknown'     — not determinable from the text -> keep as candidate WITH a review flag.
BOARD_REJECT_TELLS = [
    r"recommends?\s+that\s+(?:the\s+)?(?:stockholders|shareholders|holders).{0,30}\breject\b",
    r"recommends?\s+that\s+(?:the\s+)?(?:stockholders|shareholders|holders).{0,40}\bnot\s+tender\b",
    r"recommends?\s+(?:that\s+)?(?:stockholders|shareholders).{0,30}vote\s+against",
    r"\bunsolicited\s+(?:tender\s+)?offer\b", r"\bhostile\s+(?:tender\s+)?offer\b",
    r"not\s+approved\s+by\s+the\s+Board", r"reject\s+the\s+offer",
]
BOARD_RECOMMEND_TELLS = [
    r"(?:Board|board\s+of\s+directors).{0,60}recommends?\s+that\s+(?:the\s+)?(?:stockholders|shareholders|holders).{0,40}(?:accept|tender|adopt|approve|vote\s+(?:for|in\s+favor))",
    r"unanimously\s+(?:recommends?|approved|adopted)",
    r"recommends?\s+that\s+(?:its\s+)?(?:stockholders|shareholders)\s+vote\s+(?:for|in\s+favor)",
    r"Board.{0,40}(?:approved|adopted)\s+the\s+(?:Merger\s+)?Agreement",
]

# financing (from the offer / merger docs — SC TO-T, merger 8-K exhibit, DEFM14A, SC 14D9):
#   'uncommitted' — the bidder lacks firm money: "do not have committed financing", a non-binding /
#                   LOI backing, a financing condition/out  -> EXCLUDE or strongly flag.
#   'committed'   — firm money: committed-financing / equity- or debt-commitment letter, fully
#                   financed, no financing condition.
#   'unknown'     — not determinable -> keep as candidate WITH a review flag.
# Two tiers so a truthful positive phrase can't be misread. A deal can say "not subject to a financing
# condition" (a POSITIVE — no financing OUT) while the bidder STILL has no committed money (LSTA says
# BOTH). The decisive UNCOMMITTED tell is the bidder plainly stating it lacks committed money / has only
# an LOI — that STRONG tell governs unconditionally. The WEAK tells (a bare "financing condition",
# "subject to ... financing") only decide when no explicit committed statement is present, and are
# written to NOT fire on the negated positive form ("no/not ... financing condition").
FIN_UNCOMMITTED_STRONG = [
    r"(?:do|does)\s+not\s+have\s+committed\s+financing", r"no\s+committed\s+financing",
    r"lack\w*\s+committed\s+financing", r"non-?binding", r"letter\s+of\s+intent",
    r"no\s+assurance.{0,40}financing",
]
# the weak "financing condition" tell must NOT fire on the common POSITIVE phrasing where the deal says
# it is NOT subject to a/any financing condition — those are stripped before the weak match runs.
FIN_NOT_COND_PATS = [
    r"not\s+subject\s+to\s+(?:a|an|any|the)?\s*financing\s+condition",
    r"no\s+financing\s+condition", r"without\s+(?:a|any)\s+financing\s+condition",
    r"free\s+of\s+(?:a|any)\s+financing\s+condition",
]
FIN_UNCOMMITTED_WEAK = [
    r"subject\s+to\s+(?:the\s+availability\s+of\s+|obtaining\s+|receipt\s+of\s+)?financing",
    r"financing\s+condition",
]
# committed tells: an explicit commitment letter / fully-financed / no-out statement. (The bare phrase
# "committed financing" is deliberately NOT here — it is ambiguous, appearing in BOTH "has committed
# financing" and "do not have committed financing"; the STRONG uncommitted list already catches the
# negative form first, so we require an unambiguous positive commitment phrase here.)
FIN_COMMITTED_TELLS = [
    r"equity\s+commitment\s+letter", r"debt\s+commitment\s+letter", r"fully\s+financed",
    r"not\s+subject\s+to\s+(?:a|an|any|the)?\s*financing\s+condition", r"no\s+financing\s+condition",
    r"financing\s+commitment", r"(?:has|have)\s+(?:obtained|secured)\s+(?:the\s+)?(?:committed\s+)?financing",
]

# financing / regulatory condition tells to capture cheaply for the break-risk note.
COND_TELLS = {
    "financing_contingent": r"financing\s+condition|committed\s+financing|debt\s+financing|subject\s+to.{0,40}financing",
    "HSR/antitrust": r"Hart-Scott-Rodino|HSR|antitrust|regulatory\s+approval",
    "CFIUS": r"CFIUS|foreign\s+investment",
    "shareholder_vote": r"stockholder\s+approval|shareholder\s+vote|special\s+meeting",
    "go_shop": r"go-shop|solicitation\s+period",
    "tender_offer": r"tender\s+offer|exchange\s+offer",
}


def _get_json(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=30) as r:
            return json.load(r)
    except Exception:
        return None


def _get_text(url, limit=400_000):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=30) as r:
            raw = r.read(limit)
        txt = raw.decode("utf-8", "ignore")
        # strip tags -> plain text for regex
        txt = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", txt)
        txt = re.sub(r"(?s)<[^>]+>", " ", txt)
        txt = txt.replace("&nbsp;", " ").replace("&#160;", " ").replace("&amp;", "&")
        txt = re.sub(r"&#\d+;", " ", txt)
        return re.sub(r"\s+", " ", txt)
    except Exception:
        return None


def _cik_ticker_map():
    """{cik_int: TICKER} from the SEC master file (first/primary ticker per CIK)."""
    d = _get_json(TICKERS_MAP)
    out = {}
    if isinstance(d, dict):
        for row in d.values():
            try:
                cik = int(row["cik_str"])
                if cik not in out:                      # keep the primary listing
                    out[cik] = str(row["ticker"]).upper()
            except Exception:
                continue
    return out


def _efts(query, startdt, enddt):
    """EFTS full-text hits: list of {cik, name, date, doc_url, acc}."""
    hits = []
    params = urllib.parse.urlencode({"q": query, "forms": FORMS, "startdt": startdt, "enddt": enddt})
    d = _get_json(f"{EFTS}?{params}")
    if not isinstance(d, dict):
        return hits
    for h in (d.get("hits", {}).get("hits") or []):
        try:
            _id = h["_id"]                                # "<accession>:<doc>"
            acc, doc = _id.split(":", 1)
            src = h.get("_source", {})
            ciks = src.get("ciks") or []
            if not ciks:
                continue
            cik = int(ciks[0])
            acc_nodash = acc.replace("-", "")
            url = ARCHIVE.format(cik=cik, acc_nodash=acc_nodash, doc=doc)
            hits.append({"cik": cik, "name": (src.get("display_names") or ["?"])[0],
                         "date": src.get("file_date"), "acc": acc, "doc_url": url})
        except Exception:
            continue
    return hits


def _parse_cash(txt):
    """First SANE $/share cash offer in the text, or None. Returns float."""
    for pat in CASH_PATS:
        for m in re.finditer(pat, txt, re.I):
            try:
                v = float(m.group(1).replace(",", ""))
            except Exception:
                continue
            if OFFER_LO <= v <= OFFER_HI:
                return v
    return None


def _looks_stock(txt):
    return any(re.search(p, txt, re.I) for p in STOCK_TELLS)


def _is_nondeal(txt):
    """True if the '$X/share' is a non-binding proposal or a share-purchase/PIPE, not an all-shares take-out."""
    return any(re.search(p, txt, re.I) for p in NONDEAL_TELLS)


def _is_definitive_deal(txt):
    """True if the text carries definitive all-shares cash-acquisition language."""
    return any(re.search(p, txt, re.I) for p in DEAL_TELLS)


def _is_spac(txt, name):
    """True if this is a SPAC / de-SPAC business combination (belongs to the trust-arb scanner)."""
    # SPAC naming convention: "... Acquisition Corp" / "... Merger Corp" / blank-check.
    if re.search(r"Acquisition\s+Corp|\bMerger\s+(?:Corp|Sub|II|III|IV|V)\b|Blank\s+Check", name or "", re.I):
        return True
    # a single decisive de-SPAC phrase suffices; otherwise require two weaker tells.
    if re.search(r"Surviving\s+Pubco|blank\s+check|de-?SPAC", txt, re.I):
        return True
    return sum(bool(re.search(p, txt, re.I)) for p in SPAC_TELLS) >= 2


def _board_stance(txt):
    """Target board's recommendation: 'rejected' | 'recommended' | 'unknown'.
    REJECT wins ties — a hostile/unsolicited offer is disqualifying even if some 'recommend' boilerplate
    is present elsewhere (a target's REJECT 14D9 still quotes the bidder's 'recommends you tender')."""
    if any(re.search(p, txt, re.I) for p in BOARD_REJECT_TELLS):
        return "rejected"
    if any(re.search(p, txt, re.I) for p in BOARD_RECOMMEND_TELLS):
        return "recommended"
    return "unknown"


def _financing(txt):
    """Deal financing quality: 'uncommitted' | 'committed' | 'unknown'.
    A STRONG uncommitted tell ('do not have committed financing' / LOI / non-binding) governs
    unconditionally — LSTA states both this AND 'No Financing Condition', and the lack of committed money
    is the break risk. An explicit committed statement otherwise wins over a merely WEAK uncommitted tell
    (a bare 'financing condition' / 'subject to financing') so a truthful 'not subject to a financing
    condition, fully financed' deal is not mislabeled."""
    if any(re.search(p, txt, re.I) for p in FIN_UNCOMMITTED_STRONG):
        return "uncommitted"
    if any(re.search(p, txt, re.I) for p in FIN_COMMITTED_TELLS):
        return "committed"
    # strip the POSITIVE "not subject to a/any financing condition" phrasings so the weak tell below
    # (a bare "financing condition") doesn't misread a deal that explicitly has NO financing out.
    weak_txt = txt
    for p in FIN_NOT_COND_PATS:
        weak_txt = re.sub(p, " ", weak_txt, flags=re.I)
    if any(re.search(p, weak_txt, re.I) for p in FIN_UNCOMMITTED_WEAK):
        return "uncommitted"
    return "unknown"


def _parse_close(txt):
    for pat in CLOSE_PATS:
        m = re.search(pat, txt, re.I)
        if m:
            phrase = re.sub(r"\s+", " ", m.group(1)).strip(" ,.")
            if 3 <= len(phrase) <= 40:
                return phrase
    return None


def _conditions(txt):
    return [label for label, pat in COND_TELLS.items() if re.search(pat, txt, re.I)]


def _acquirer(txt, target_name):
    """Best-effort acquirer name from the announcement lede."""
    m = re.search(r"(?:acqui\w+\s+by|be\s+acquired\s+by|merger\s+with|agreement\s+with)\s+([A-Z][A-Za-z0-9&.,\- ]{2,50}?)(?:,| in| for| under| pursuant| a )", txt)
    if m:
        return m.group(1).strip(" ,.")
    return None


def _close_to_days(phrase, today):
    """Rough days-to-close from a quarter/month phrase like 'the fourth quarter of 2026'."""
    if not phrase:
        return None, None
    p = phrase.lower()
    yr = None
    ym = re.search(r"(20[2-3][0-9])", p)
    if ym:
        yr = int(ym.group(1))
    q = None
    for qn, keys in {4: ["fourth", "q4"], 3: ["third", "q3"], 2: ["second", "q2"], 1: ["first", "q1"]}.items():
        if any(k in p for k in keys):
            q = qn
            break
    months = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
              "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}
    mo = next((mn for name, mn in months.items() if name in p), None)
    target = None
    if yr and q:
        target = datetime.date(yr, q * 3, 28)                    # end of the quarter
    elif yr and mo:
        target = datetime.date(yr, mo, 15)
    elif yr:
        target = datetime.date(yr, 12, 31)
    if not target:
        return None, phrase
    return (target - today).days, phrase


def _yf_price_shares(ticker):
    """(price, shares_out) live via yfinance; either may be None."""
    import yfinance as yf
    try:
        tk = yf.Ticker(ticker)
        fi = getattr(tk, "fast_info", {}) or {}
        px = fi.get("last_price") or fi.get("lastPrice")
        sh = fi.get("shares") or fi.get("shares_outstanding")
        if px is None or sh is None:
            info = {}
            try:
                info = tk.info or {}
            except Exception:
                info = {}
            px = px or info.get("regularMarketPrice") or info.get("previousClose")
            sh = sh or info.get("sharesOutstanding")
        if px is None:
            hist = tk.history(period="5d")
            if len(hist):
                px = float(hist["Close"].dropna().iloc[-1])
        return (float(px) if px else None), (float(sh) if sh else None)
    except Exception:
        return None, None


def scan(days=120, max_value_m=DEFAULT_MAX_VALUE_M) -> dict:
    today = datetime.date.today()
    startdt = (today - datetime.timedelta(days=days)).isoformat()
    enddt = today.isoformat()
    cikmap = _cik_ticker_map()

    # 1) discover unique (cik, doc) announcements across the queries
    seen_docs = set()
    docs = []
    for q in QUERIES:
        for h in _efts(q, startdt, enddt):
            key = (h["cik"], h["doc_url"])
            if key in seen_docs:
                continue
            seen_docs.add(key)
            docs.append(h)
        time.sleep(0.3)

    n_scanned = 0
    candidates, all_cash, skipped_non_cash, dropped, excluded = [], [], [], [], []
    seen_cik = set()

    for h in docs:
        cik = h["cik"]
        if cik in seen_cik:                              # one deal per target
            continue
        txt = _get_text(h["doc_url"])
        time.sleep(0.25)
        if not txt:
            continue
        n_scanned += 1
        ticker = cikmap.get(cik)
        name = re.sub(r"\s*\(CIK.*$", "", h["name"]).strip()

        offer = _parse_cash(txt)
        if offer is None:
            if _looks_stock(txt):
                skipped_non_cash.append({"cik": cik, "ticker": ticker, "name": name,
                                         "date": h["date"], "why": "stock/mixed — no clean cash/share number"})
            continue

        # GATE: a "$X per share in cash" is only a tradeable arb if it's a DEFINITIVE all-shares take-out.
        # A NONDEAL tell (non-binding, proposal, share-purchase, subscription, "at least") VETOES — a signed
        # take-out never calls itself non-binding, and a generic "definitive agreement" in a safe-harbor
        # disclaimer must NOT rescue it (GDC going-private PROPOSAL, GBR investor buying 2M shares both did that).
        if _is_spac(txt, name):
            skipped_non_cash.append({"cik": cik, "ticker": ticker, "name": name, "date": h["date"],
                                     "why": "SPAC / de-SPAC business combination — trust/redemption value, not an operating-target take-out (see spac_trust_arb)",
                                     "parsed_number": round(offer, 4)})
            continue
        if _is_nondeal(txt):
            skipped_non_cash.append({"cik": cik, "ticker": ticker, "name": name, "date": h["date"],
                                     "why": "non-binding proposal / PIPE / share-purchase / LOI — not a signed all-shares cash deal",
                                     "parsed_number": round(offer, 4)})
            continue
        if not _is_definitive_deal(txt):
            skipped_non_cash.append({"cik": cik, "ticker": ticker, "name": name, "date": h["date"],
                                     "why": "no definitive-agreement / all-shares language (ambiguous)",
                                     "parsed_number": round(offer, 4)})
            continue
        seen_cik.add(cik)

        # DEAL-QUALITY GATES: the "wider spread, same risk" thesis only holds for CLEAN small deals.
        # 1) BOARD STANCE — a board-REJECTED / hostile / unsolicited offer prices a near-zero close prob;
        #    the spread is NOT carry, it's a broken-deal discount. EXCLUDE (DXLG lands here).
        # 2) FINANCING — an UN-committed bidder (only a non-binding LOI, "do not have committed financing",
        #    or a financing out) carries real break risk that a clean deal doesn't. EXCLUDE (LSTA here).
        # 'unknown' on either passes through as a candidate but is REVIEW-flagged (free-text is best-effort).
        board_stance = _board_stance(txt)
        financing = _financing(txt)
        if board_stance == "rejected":
            excluded.append({"ticker": ticker, "name": name, "cik": cik, "date": h["date"],
                             "reason": "board_rejected", "board_stance": board_stance,
                             "financing": financing, "parsed_offer": round(offer, 4),
                             "why": "target board recommends REJECT / offer is unsolicited-hostile — "
                                    "spread prices a near-zero close probability, not clean carry",
                             "source_doc": h["doc_url"]})
            continue
        if financing == "uncommitted":
            excluded.append({"ticker": ticker, "name": name, "cik": cik, "date": h["date"],
                             "reason": "uncommitted_financing", "board_stance": board_stance,
                             "financing": financing, "parsed_offer": round(offer, 4),
                             "why": "bidder lacks committed financing (non-binding LOI / 'do not have "
                                    "committed financing' / financing out) — spread prices real break risk",
                             "source_doc": h["doc_url"]})
            continue

        if not ticker:
            dropped.append({"cik": cik, "name": name, "offer_cash_per_share": offer,
                            "why": "no SEC ticker (private/foreign/OTC target) — can't price"})
            continue

        price, shares = _yf_price_shares(ticker)
        if not price:
            dropped.append({"cik": cik, "ticker": ticker, "name": name, "offer_cash_per_share": offer,
                            "why": "no live price (yfinance unresolved — likely already closed/delisted)"})
            continue

        deal_value = offer * shares if shares else None
        close_phrase = _parse_close(txt)
        days_to_close, expected_close = _close_to_days(close_phrase, today)
        conds = _conditions(txt)
        acquirer = _acquirer(txt, name)
        spread = (offer - price) / price if price else None
        annualized = None
        if spread is not None and days_to_close and days_to_close > 0:
            annualized = spread * (365.0 / days_to_close)

        wide = spread is not None and spread > 0.40      # >40% "live-deal" spread = hostile/broken OR stale/mis-parse
        review_flags = []
        if board_stance == "unknown":
            review_flags.append("board_stance UNKNOWN — confirm the target board recommends FOR (not a hostile offer) in the SC 14D9 / proxy")
        if financing == "unknown":
            review_flags.append("financing UNKNOWN — confirm the bidder has committed financing (commitment letters), not just an LOI")
        cond_note = ("; ".join(conds) if conds else "no explicit conditions parsed") + \
                    " | BREAK RISK: small all-cash deals break MORE than large ones (financing/MAC/thin sponsor) " \
                    "— a wide spread PRICES that risk. Verify the financing commitment + regulatory path in DD."
        if review_flags:
            cond_note = "REVIEW: " + " ; ".join(review_flags) + " | " + cond_note
        if wide:
            cond_note = "WIDE-SPREAD FLAG (>40%): market implies a LOW close-probability (hostile/unsolicited/likely-fail) " \
                        "OR the parsed offer is stale/superseded — verify the deal is LIVE and firm before trusting the spread. " + cond_note

        row = {
            "ticker": ticker, "name": name, "cik": cik, "announce_date": h["date"],
            "offer_cash_per_share": round(offer, 4),
            "price": round(price, 4),
            "spread_pct": round(spread * 100, 2) if spread is not None else None,
            "deal_value_est": round(deal_value) if deal_value else None,
            "deal_value_est_m": round(deal_value / 1e6, 1) if deal_value else None,
            "sub_threshold": (deal_value is not None and deal_value < max_value_m * 1e6),
            "expected_close": expected_close,
            "days_to_close": days_to_close,
            "annualized_spread": round(annualized * 100, 1) if annualized is not None else None,
            "wide_spread_flag": wide,
            "board_stance": board_stance,
            "financing": financing,
            "review_flags": review_flags,
            "acquirer": acquirer,
            "conditions_note": cond_note,
            "source_doc": h["doc_url"],
        }
        all_cash.append(row)
        # a candidate = sub-threshold (or unknown-size, flagged) AND a POSITIVE spread (price below offer)
        if spread is not None and spread > 0 and (row["sub_threshold"] or deal_value is None):
            candidates.append(row)

    candidates.sort(key=lambda r: -(r["spread_pct"] or -99))
    all_cash.sort(key=lambda r: -(r["spread_pct"] if r["spread_pct"] is not None else -99))

    sub = [r for r in candidates if r["sub_threshold"]]
    unknown_size = [r for r in candidates if r["deal_value_est"] is None]

    return {
        "asof": today.isoformat(),
        "window_days": days,
        "max_value_m": max_value_m,
        "n_scanned": n_scanned,
        "n_all_cash": len(all_cash),
        "candidates": candidates,
        "all_cash_deals": all_cash,
        "excluded": excluded,
        "skipped_non_cash": skipped_non_cash,
        "dropped": dropped,
        "distribution": {
            "n_candidates": len(candidates),
            "n_sub_threshold_known": len(sub),
            "n_unknown_size": len(unknown_size),
            "n_excluded": len(excluded),
            "median_spread_pct": round(sorted(r["spread_pct"] for r in candidates)[len(candidates) // 2], 2) if candidates else None,
        },
        "caveats": [
            "DEAL-QUALITY GATE: the wider-spread-same-risk thesis holds only for CLEAN small deals. Deals "
            "whose TARGET board recommends REJECT (unsolicited/hostile) or whose bidder lacks committed "
            "financing (non-binding LOI / 'do not have committed financing' / a financing out) are moved to "
            "`excluded` with a reason — the spread there prices a broken/under-financed deal, not neglected "
            "carry. board_stance / financing == 'unknown' pass through but carry a REVIEW flag (free-text "
            "parsing is best-effort; confirm the SC 14D9 recommendation + the commitment letters in DD).",
            "THE SPREAD IS THE BREAK-RISK PREMIUM: a wide spread on a small deal is NOT free money — small "
            "all-cash deals break MORE often (financing contingencies, MAC outs, thin/PE sponsors, regulatory "
            "surprises). The DD/court step is verifying the financing commitment letter + antitrust path + "
            "the definitive agreement's outs before sizing.",
            "OFFER PRICE is regex-parsed from the announcing 8-K/press exhibit ('$X.XX per share in cash') — "
            "verify against the DEFINITIVE merger agreement (a lede number can be a headline value that a "
            "later amendment/CVR adjusts). Numbers outside ${:.2f}-${:.0f} are discarded as mis-parses.".format(OFFER_LO, OFFER_HI),
            "DEAL VALUE = offer x yfinance shares-outstanding (may be stale / exclude options/RSUs/net-debt) — "
            "it's a SIZE SCREEN for the sub-threshold gate, not a precise enterprise value.",
            "DAYS-TO-CLOSE is parsed from soft language ('expected to close in Q4 2026') and mapped to the "
            "quarter-end — annualized_spread is therefore approximate; a stated drop-dead date (DD pull) is firmer.",
            "STOCK / MIXED / COLLAR deals with no clean cash number are SET ASIDE in skipped_non_cash (never "
            "guessed) — v2 parses exchange ratios + collars.",
            "A NEGATIVE spread (price above offer) usually means the market expects a BUMP, a competing bid, or "
            "the parsed offer is stale/superseded — shown in all_cash_deals, excluded from candidates.",
            "Targets with no SEC ticker (private/foreign/OTC) or no live price (already-closed/delisted) "
            "self-drop into `dropped` — reported, never silently omitted.",
        ],
        "note": "CARRY class — SUB-THRESHOLD merger arb. Arb funds skip small all-cash deals (<${:.0f}M) because "
                "the absolute $-edge can't move a big book and the float can't absorb their size, so small deals "
                "carry a WIDER spread for the SAME regulatory/financing/MAC break risk — a capacity-ceiling edge "
                "that's ours by design (fee-replication CARRY). Discovers recent cash merger agreements via EDGAR "
                "EFTS full-text (8-K/DEFM14A), parses the cash/share from PRIMARY exhibits, prices live via "
                "yfinance, gates on deal value < ${:.0f}M, sorts by spread. Break risk is REAL and larger for "
                "small deals — every candidate carries the announced financing/regulatory conditions + a "
                "break-risk caveat (the DD/court step). NO offer prices fabricated — real filings only. "
                "EXPAND (v2: parse stock/collar deals, regulatory/financing-condition SCORING, "
                "break-rate-adjusted spread).".format(max_value_m, max_value_m),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=120, help="EFTS lookback window (days)")
    ap.add_argument("--max-value", type=float, default=DEFAULT_MAX_VALUE_M, help="sub-threshold ceiling ($M target equity value)")
    args = ap.parse_args()

    res = scan(days=args.days, max_value_m=args.max_value)
    OUT.write_text(json.dumps(res, indent=1))
    d = res["distribution"]
    print(f"=== SUB-THRESHOLD MERGER-ARB SCANNER  {res['asof']}  "
          f"({res['n_scanned']} filings scanned, {res['n_all_cash']} all-cash, {d['n_candidates']} candidates) ===")
    print(f"  window {res['window_days']}d | ceiling ${res['max_value_m']:.0f}M | "
          f"{d['n_sub_threshold_known']} sub-threshold(known-size) + {d['n_unknown_size']} unknown-size | "
          f"median spread {d['median_spread_pct']}%")
    if res["candidates"]:
        print("  SUB-THRESHOLD CASH-ARB CANDIDATES (positive spread; verify financing + break risk in DD):")
        for r in res["candidates"][:15]:
            dv = f"${r['deal_value_est_m']:.0f}M" if r["deal_value_est_m"] else "size?"
            ann = f"  ann {r['annualized_spread']:.0f}%" if r["annualized_spread"] is not None else ""
            cl = f"  ~{r['expected_close']}" if r["expected_close"] else ""
            wf = "  [WIDE-verify-live]" if r.get("wide_spread_flag") else ""
            print(f"    {r['ticker']:6} {r['name'][:26]:26} px ${r['price']:7.2f}  offer ${r['offer_cash_per_share']:7.2f}  "
                  f"{r['spread_pct']:+6.2f}%  {dv:>7}{cl}{ann}{wf}")
    else:
        print("  no positive-spread sub-threshold cash deals this run (honest: small cash M&A is episodic).")
        if res["all_cash_deals"]:
            print("  all-cash deals seen (any size / sign):")
            for r in res["all_cash_deals"][:8]:
                dv = f"${r['deal_value_est_m']:.0f}M" if r["deal_value_est_m"] else "size?"
                sp = f"{r['spread_pct']:+.2f}%" if r["spread_pct"] is not None else "n/a"
                print(f"    {r['ticker']:6} {r['name'][:26]:26} px ${r['price']:7.2f}  offer ${r['offer_cash_per_share']:7.2f}  {sp:>8}  {dv:>7}")
    if res["excluded"]:
        print(f"  EXCLUDED on deal-quality gate ({len(res['excluded'])}):")
        for x in res["excluded"][:10]:
            print(f"    {(x.get('ticker') or x['name'][:16]):16} {x['reason']:22} "
                  f"board={x['board_stance']:11} fin={x['financing']}")
    if res["skipped_non_cash"]:
        print(f"  set aside (stock/mixed, no clean cash #): {[x.get('ticker') or x['name'][:16] for x in res['skipped_non_cash'][:10]]}")
    if res["dropped"]:
        print(f"  dropped (no ticker / no price, {len(res['dropped'])}): {[x.get('ticker') or x['name'][:14] for x in res['dropped'][:10]]}")
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
