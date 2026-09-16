"""tariff_refund_cohort — Stage-0b MECHANISM-FIRST generator: the IEEPA / Section-122 tariff-refund cohort.

THE MECHANISM (house IP, courts 2026-08-03/04 — FND / ISRG / ARHS / DSGX):
  The Supreme Court struck the IEEPA tariffs on 2026-02-20 (Learning Resources v. Trump). The
  administration's replacement ran under Section 122, which carries a hard statutory sunset —
  effective 2026-02-24 + 150 days = 2026-07-24 — absent congressional action. Importers who paid
  IEEPA duties therefore hold REFUND CLAIMS, and importers guiding on a tariff cost hold a cost
  line with a statutory expiry date printed in their own filings.

  That single legal event splits the tape TWO WAYS, and the split is an accounting choice, not a
  business one — which is exactly why the sell side misreads it:

  (A) EPS-MIRAGE FADES — the FND pattern. A company RECOGNIZES the refund in the period. GAAP EPS
      jumps, gross margin "expands", the print beats, and consensus is marked UP. The improvement
      is a one-time customs-duty recovery, not operations. FND Q2-2026: GAAP EPS +53.4% while
      ADJUSTED EPS was FLAT, comps -2.1%, and the $0.31 GAAP-vs-adjusted spread WAS the refund;
      consensus still moved FY26 $1.903 -> $1.971 with 4 up-revisions in 7 days. Any screen that
      reads estimate DIRECTION without reading estimate COMPOSITION buys tariff refunds. These are
      FADE-THE-ESTIMATE candidates for the court — NOT auto-shorts (gate-6).

  (B) POSITIVE-SKEW CONSERVATIVES — the ISRG / ARHS pattern. A company does NOT recognize the
      refund (a gain contingency it cannot book) and/or guides as though the tariff cost PERSISTS.
      ISRG's July-16 release assumed tariffs "remain in place through the end of the year" (~$122M
      of embedded cost) while its own 10-Q, filed five days later, printed the Section-122 150-day
      sunset. ARHS states outright that its outlook "does not include any benefit from potential
      IEEPA tariff refunds." If the sunset held, those guides raise near-mechanically.

  MASKING CHANNEL: the non-GAAP reconciliation (A) / the unrecognized gain contingency (B).
  SIGNAL CHANNEL: EDGAR full text — the verbatim sentence in the 8-K/10-Q/10-K.
  SIGNAL-TO-PRICE LATENCY: A resolves at the NEXT print (the refund does not repeat, the compare
  breaks); B resolves at the next guide (weeks-to-a-quarter).

THE B-SIDE CONFOUNDERS ARE MANDATORY, NOT OPTIONAL (the ISRG red-team lesson, which cut that call
from 0.60 to 0.55 and struck its "verified EDGE" label):
  1. The Federal Circuit EXTENDED its stay on 2026-06-11, keeping the 10% tariffs in place pending
     proceedings — the sunset may not have bitten.
  2. Section 232 / 301 SUBSTITUTION is the administration's stated intent — the cost can be
     re-imposed under a different authority the same week it lapses.
  3. Therefore a management guiding "tariffs persist" is NOT necessarily being conservative. The
     parsimonious explanation is INFORMED CAUTION: counsel did not forget the statute in its own
     10-Q. B is POSITIVE SKEW ON A PUBLIC FACT, not free money, and a statutory date printed in a
     10-Q covered by fifteen analysts is not an informational moat.
  Every B row in the output carries these confounders verbatim. There is no un-confounded B name.

GUARDS (each one is a specific past failure):
  * MAGNITUDE FROM FILINGS ONLY. A dollar or per-share figure is recorded only when it appears in
    the verbatim filing sentence (or the sentence adjacent to it). We NEVER estimate a refund
    silently. Unquantified is reported as unquantified — the ARHS refund is real and its amount is
    genuinely unknown, and that is the honest output.
  * NO SHORTING ATTENTION NAMES (gate-6). A-fades are labeled FADE_THE_ESTIMATE and carry live
    short interest / days-to-cover; any name with squeeze fuel is flagged NO_SHORT explicitly.
    FND itself failed this test in court: 15.7M shares short, 6.05 days-to-cover.
  * CONSENSUS MOVEMENT IS EVIDENCE, NOT THE CLAIM. Estimate revisions come from a market data
    feed, not a filing; they are labeled as such and never used to infer a refund's existence.
  * CLASSIFICATION IS EARNED, NOT ASSUMED. A/B requires marker language in the extracted sentence;
    otherwise the row is 'unclear' and stays out of both ranked tables.

Usage:
  python3 verticals/generators/tariff_refund_cohort.py [--since 2026-02-20] [--max-docs 600]
                                                       [--pages 8] [--no-market]
Writes verticals/generators/data/TARIFF_REFUND_COHORT.json + desk/data/TARIFF_REFUND_INTAKE_<date>.md
READ-ONLY. Never places orders. No fabricated tickers — CIK->ticker via the SEC canonical map only.
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OUT_JSON = HERE / "data" / "TARIFF_REFUND_COHORT.json"
INTAKE_DIR = REPO / "desk" / "data"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}

EFTS = "https://efts.sec.gov/LATEST/search-index"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

SCOTUS_DATE = "2026-02-20"      # Learning Resources v. Trump — IEEPA tariffs struck
S122_EFFECTIVE = "2026-02-24"   # Section 122 replacement effective
S122_SUNSET = "2026-07-24"      # +150 days, the statutory maximum without congressional action

CONFOUNDERS = [
    "Federal Circuit EXTENDED its stay on 2026-06-11 — the 10% tariffs may remain in place pending "
    "proceedings, so the Section-122 sunset may not have bitten.",
    "Section 232 / 301 SUBSTITUTION is the administration's stated intent — the same cost can be "
    "re-imposed under a different authority within days of the lapse.",
    "INFORMED CAUTION, not conservatism: a management that guides 'tariffs persist' while its own "
    "10-Q prints the sunset date has counsel who read the statute. Positive skew on a public fact "
    "is not an informational moat.",
]

# ---------------------------------------------------------------------------
# EFTS query set. Conjunctions ("IEEPA" refund) are used where the bare term is too broad —
# bare "IEEPA" returns 1025 filings, most of them risk-factor boilerplate with no refund claim.
# 'spec' = specificity weight, used ONLY to prioritise doc fetches under --max-docs.
# ---------------------------------------------------------------------------
QUERIES = [
    {"q": '"tariff refund"', "spec": 5},
    {"q": '"tariff refunds"', "spec": 5},
    {"q": '"refund of tariffs"', "spec": 5},
    {"q": '"duty refund"', "spec": 5},
    {"q": '"refund of duties"', "spec": 5},
    {"q": '"customs duty" refund', "spec": 4},
    {"q": '"IEEPA" refund', "spec": 4},
    {"q": '"gain contingency" tariff', "spec": 4},
    {"q": '"Section 122" tariff', "spec": 3},
    # B-SIDE RECALL LEG. The persist-assumption often sits in a guidance release that never uses the
    # word IEEPA or the word refund — ISRG's "assumes such tariffs remain in place through the end of
    # the year" is in the July-16 8-K, and no refund-keyed query reaches it. These queries exist
    # purely so the B side is not silently under-collected relative to the A side.
    {"q": '"tariffs remain in place"', "spec": 4},
    {"q": '"tariffs remain in effect"', "spec": 4},
    {"q": '"remain in effect for 150 days"', "spec": 5},
    {"q": '"outlook assumes" tariff', "spec": 3},
    {"q": '"guidance assumes" tariff', "spec": 3},
    {"q": '"assumes tariffs"', "spec": 4},
    {"q": '"tariff rates continued"', "spec": 4},
]
FORMS = "8-K,10-Q,10-K"

# --- sentence-level trigger: the sentence must be about tariffs/duties AND about recovery ------
TARIFF_TOK = re.compile(r"\b(IEEPA|Section\s*122|tariff|customs\s+dut|duties|duty)\b", re.I)
# The B side lives in sentences that never say "refund": ISRG's decisive 10-Q line is "will remain in
# effect for 150 days, the maximum period that Section 122 permits without congressional action", and
# its guidance line is "assumes such tariffs remain in place through the end of the year". v1 required
# 'remain in place' exactly and lost both — the ground-truth name was absent from its own cohort.
RECOVER_TOK = re.compile(r"(refund|recover|reimburse|gain\s+conting|"
                         r"remain\s+in\s+(?:place|effect)|remains?\s+in\s+(?:place|effect)|"
                         r"150\s+days|sunset|expire|lapse|congressional\s+action|"
                         r"assum\w+[^.]{0,40}tariff|tariff[^.]{0,40}assum\w+|"
                         r"continu\w+[^.]{0,30}(?:for the (?:balance|remainder)|through the end))", re.I)

# --- classification markers ---------------------------------------------------------------
# A = the refund is IN the reported numbers or IN the guide (the mirage the consensus extrapolates)
A_MARKERS = [
    (re.compile(r"(recogni[sz]ed|recorded|received|collected)\s+(?:a\s+|an\s+|the\s+)?"
                r"(?:\$[\d.,]+\s*(?:million|billion)?\s*)?(?:of\s+)?(?:tariff|customs|duty|duties|IEEPA)?"
                r"[^.]{0,60}refund", re.I), 3, "refund RECOGNIZED/RECEIVED in the period"),
    (re.compile(r"refund[^.]{0,80}\b(was|were|has been|have been)\s+(recogni[sz]ed|recorded|received)", re.I),
     3, "refund recorded in results"),
    (re.compile(r"\bone[- ]?time\b[^.]{0,60}(refund|duty|tariff|benefit)", re.I), 2,
     "described as one-time"),
    (re.compile(r"(reduc\w+|decreas\w+|benefit\w*)\s+(?:to\s+)?cost of (?:sales|goods|revenue)[^.]{0,80}"
                r"(tariff|duty|duties|refund)", re.I), 2, "flowed through cost of sales"),
    (re.compile(r"(favorab\w+|positive\w*)\s+(?:ly\s+)?(impact\w*|affect\w*)[^.]{0,60}(refund|tariff|duty)", re.I),
     1, "described as favorably impacting the period"),
    (re.compile(r"(guidance|outlook|guide)[^.]{0,80}\b(includes?|reflects?|incorporat\w+)\b[^.]{0,60}refund", re.I),
     3, "refund INCLUDED in guidance"),
    (re.compile(r"refund[^.]{0,60}(receivable|asset)\b[^.]{0,40}(recorded|recogni[sz]ed|established)", re.I),
     3, "refund receivable booked"),
]
# B = the refund is NOT in the numbers, and/or the guide assumes the tariff cost persists
B_MARKERS = [
    (re.compile(r"gain\s+conting\w+", re.I), 3, "unrecognized GAIN CONTINGENCY"),
    (re.compile(r"(ha(?:ve|s)\s+not|did\s+not|does\s+not|no)\s+[^.]{0,40}"
                r"(recogni[sz]ed?|record\w*)\s*[^.]{0,40}(refund|gain|receivable)", re.I), 3,
     "refund explicitly NOT recognized"),
    (re.compile(r"(does not include|excludes?|excluded|not included in|no benefit from)[^.]{0,80}"
                r"(refund|tariff refund)", re.I), 3, "refund EXCLUDED from guidance/outlook"),
    (re.compile(r"may be eligible[^.]{0,60}refund", re.I), 2, "'may be eligible for a refund' — unbooked claim"),
    (re.compile(r"(assum\w+|assumption)[^.]{0,90}tariffs?[^.]{0,90}"
                r"(remain in place|remain|continue|persist|through the end of the year|for the (?:remainder|balance))",
                re.I), 3, "guide ASSUMES tariffs PERSIST"),
    (re.compile(r"tariffs?[^.]{0,60}(remain in effect|remain in place)[^.]{0,60}"
                r"(through|for the remainder|for the balance|end of)", re.I), 2,
     "tariff cost assumed in effect through the guide period"),
    (re.compile(r"(uncertain|cannot|unable to)[^.]{0,60}(estimate|determine|quantif\w+)[^.]{0,60}refund", re.I),
     1, "refund amount not estimable"),
]
# NEGATION GUARD on the A side. "the Company's current outlook does not include any benefit from
# potential IEEPA tariff refunds" is the single cleanest B sentence in the whole cohort, and it fired
# the A marker (outlook … include … refund) because the marker never looked left for the negator.
# ARHS tied 3-3 and fell into 'unclear' — the ground-truth B name buried by its own decisive sentence.
NEGATOR = re.compile(r"\b(not|no|never|without|exclud\w*|excluding|nor|neither|"
                     r"unable to|cannot|has yet to|have yet to)\b", re.I)


def _negated(sent: str, span: tuple[int, int]) -> bool:
    """True when a negator sits immediately before the matched A-marker span."""
    lo = max(0, span[0] - 60)
    return bool(NEGATOR.search(sent[lo:span[0] + 40]))


# the Section-122 sunset itself, printed in the filing — the ISRG tell
SUNSET_MARKER = re.compile(r"(150\s+days|Section\s*122)[^.]{0,160}"
                           r"(maximum period|without congressional action|expire|sunset|terminat)", re.I)

# --- magnitude extraction: FILING TEXT ONLY -----------------------------------------------
MONEY = re.compile(r"\$\s?([\d,]+(?:\.\d+)?)\s*(billion|million|thousand|bn|mm|m\b|k\b)?", re.I)
PER_SHARE = re.compile(r"\$\s?(\d+\.\d{2,3})\s*(?:per\s+(?:basic\s+and\s+)?(?:diluted\s+)?share|/\s*share)", re.I)
MULT = {"billion": 1e9, "bn": 1e9, "million": 1e6, "mm": 1e6, "m": 1e6,
        "thousand": 1e3, "k": 1e3, None: 1.0, "": 1.0}
# a dollar figure is a REFUND magnitude only if a refund/tariff token sits this close to it
PROX = 130
MAG_ANCHOR = re.compile(r"\b(refund\w*|tariff\w*|IEEPA|dut(?:y|ies)|recover\w+|reimburse\w+)\b", re.I)
# flattened financial TABLES: their numbers have no grammar binding them to a subject, so we refuse
# to read a magnitude out of one (the GIII 'RECONCILIATION OF GAAP GROSS PROFIT' false $139.5M).
TABLE_TELLS = re.compile(r"(reconciliation of|in thousands|unaudited\)|three months ended|"
                         r"six months ended|nine months ended|\(in millions)", re.I)


def _is_table(sent: str) -> bool:
    """True when the 'sentence' is really a flattened table row/header rather than prose."""
    dollars = sent.count("$")
    if dollars >= 5:
        return True
    if dollars >= 2 and TABLE_TELLS.search(sent):
        return True
    if sent.count("​") >= 3:      # zero-width separators — an EDGAR table tell
        return True
    return False


def _get(url: str, retries: int = 3, timeout: int = 45) -> bytes | None:
    """Polite GET with backoff — EDGAR 429s aggressively on EFTS and the archives."""
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            time.sleep(1.0 + 0.9 * i)
    return None


def _get_json(url: str) -> dict:
    raw = _get(url)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _ticker_map() -> dict:
    """CIK -> ticker. Multi-class issuers list several symbols per CIK; prefer the plain common
    (shortest, no class suffix) so Moog resolves MOG-A not MOG-B and Bruker resolves BRKR not BRKRP."""
    d = _get_json(TICKERS_URL)
    out = {}
    for _, row in (d or {}).items():
        try:
            cik, tk = int(row["cik_str"]), row["ticker"].upper()
        except Exception:
            continue
        cur = out.get(cik)
        if cur is None or (len(tk), tk) < (len(cur["ticker"]), cur["ticker"]):
            out[cik] = {"ticker": tk, "title": row["title"]}
    return out


def _clean_name(display: str) -> str:
    return re.sub(r"\s*\(.*", "", display or "").strip()[:70]


def _efts(query: str, since: str, until: str, pages: int) -> list[dict]:
    """Paginate EFTS (100/page) -> normalized hit rows keyed on the exact matched document."""
    rows, seen = [], set()
    for page in range(pages):
        p = {"q": query, "forms": FORMS, "startdt": since, "enddt": until}
        if page:
            p["from"] = page * 100
        d = _get_json(EFTS + "?" + urllib.parse.urlencode(p))
        hits = (((d or {}).get("hits") or {}).get("hits")) or []
        if not hits:
            break
        for h in hits:
            _id = h.get("_id", "")
            if _id in seen:
                continue
            seen.add(_id)
            s = h.get("_source") or {}
            ciks = s.get("ciks") or []
            if not ciks:
                continue
            names = s.get("display_names") or []
            adsh, _, fname = _id.partition(":")
            rows.append({
                "cik": int(ciks[0]),
                "name": _clean_name(names[0] if names else ""),
                "date": s.get("file_date", ""),
                "form": (s.get("root_forms") or [s.get("form", "")])[0],
                "adsh": s.get("adsh", "") or adsh,
                "fname": fname,
                "file_type": s.get("file_type", ""),
                "sic": (s.get("sics") or [""])[0],
            })
        if len(hits) < 100:
            break
        time.sleep(0.35)
    return rows


def _doc_url(cik: int, adsh: str, fname: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh.replace('-', '')}/{fname}"


def _text(raw: bytes) -> str:
    """HTML -> flat text. Filings are XHTML with inline XBRL; strip tags and normalise whitespace."""
    t = raw.decode("utf-8", "ignore")
    t = re.sub(r"(?is)<(script|style|ix:header)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = html.unescape(t)
    t = t.replace(" ", " ").replace("’", "'").replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", t)


def _sentences(txt: str) -> list[str]:
    """Cheap sentence split that survives '$1.2 million.' and 'U.S.' — good enough for evidence quoting."""
    # Bullet glyphs MUST be split points. Press releases glue unrelated bullets into one blob, and a
    # proximity-anchored magnitude then reads across the join: LNN's "$12 billion in one-time payments
    # to farmers" landed within 130 chars of a tariff-refund clause and became a $12bn refund.
    txt = re.sub(r"[•●▪·]", ". ", txt)
    parts = re.split(r"(?<=[.;])\s+(?=[A-Z(\"'$])", txt)
    return [p.strip() for p in parts if 30 <= len(p) <= 1200]


def _magnitudes(sent: str) -> dict:
    """Dollar / per-share figures FROM THIS SENTENCE, and ONLY those ATTACHED TO A REFUND TOKEN.

    v1 took the largest dollar figure anywhere in the sentence and produced garbage: BBW's
    "$550M" was a revenue line in a flattened press-release paragraph, GIII's "$139.5M" came out
    of a GAAP-to-non-GAAP reconciliation table, and both blew the refund-vs-quarter-EPS ratio out
    to four digits. A dollar figure now counts as a refund magnitude only if a refund/tariff token
    sits within PROX characters of it, and flattened TABLES are refused outright — their numbers
    have no sentence grammar binding them to anything.
    """
    if _is_table(sent):
        return {"usd": None, "per_share": None, "refused": "table-like text — magnitude not attributable"}
    usd, per_sh = [], []
    for m in MONEY.finditer(sent):
        try:
            v = float(m.group(1).replace(",", "")) * MULT.get((m.group(2) or "").lower(), 1.0)
        except Exception:
            continue
        if v < 1e4:             # sub-$10k figures are page refs / share prices, not refunds
            continue
        lo, hi = max(0, m.start() - PROX), min(len(sent), m.end() + PROX)
        if MAG_ANCHOR.search(sent[lo:hi]):
            usd.append(v)
    for m in PER_SHARE.finditer(sent):
        lo, hi = max(0, m.start() - PROX), min(len(sent), m.end() + PROX)
        if not MAG_ANCHOR.search(sent[lo:hi]):
            continue
        try:
            per_sh.append(float(m.group(1)))
        except Exception:
            continue
    return {"usd": max(usd) if usd else None, "per_share": max(per_sh) if per_sh else None}


def _classify(sents: list[str]) -> dict:
    """Score A vs B from marker language in the tariff-recovery sentences. Earned, never assumed."""
    a_score = b_score = 0
    a_reasons, b_reasons, evidence = [], [], []
    # magnitudes are attributed to the SIDE of the sentence that carried them. A recognized $128M of
    # recoveries with a $2M residual gain contingency is an A name, not a B name — a marker COUNT
    # would call it B (two B markers beat one A marker) and the money says otherwise. (CRI, v1 bug.)
    rec_usd = unrec_usd = best_ps = None
    sunset_cited = False
    for s in sents:
        # A markers are asserted claims ("we recognized"), so a negator in front of one flips its
        # meaning entirely. B markers are already negation-shaped and are matched as written.
        hit_a = []
        for rx, w, lab in A_MARKERS:
            mm = rx.search(s)
            if mm and not _negated(s, mm.span()):
                hit_a.append((w, lab))
        hit_b = [(w, lab) for rx, w, lab in B_MARKERS if rx.search(s)]
        if SUNSET_MARKER.search(s):
            sunset_cited = True
        if not (hit_a or hit_b):
            continue
        a_score += sum(w for w, _ in hit_a)
        b_score += sum(w for w, _ in hit_b)
        a_reasons += [lab for _, lab in hit_a]
        b_reasons += [lab for _, lab in hit_b]
        mag = _magnitudes(s)
        if mag["usd"]:
            if hit_b and not hit_a:
                unrec_usd = max(unrec_usd or 0.0, mag["usd"])
            elif hit_a and not hit_b:
                rec_usd = max(rec_usd or 0.0, mag["usd"])
            else:   # mixed sentence — attribute to the heavier side, never to both
                side = "a" if sum(w for w, _ in hit_a) >= sum(w for w, _ in hit_b) else "b"
                if side == "a":
                    rec_usd = max(rec_usd or 0.0, mag["usd"])
                else:
                    unrec_usd = max(unrec_usd or 0.0, mag["usd"])
        if mag["per_share"] and (best_ps is None or mag["per_share"] > best_ps):
            best_ps = mag["per_share"]
        evidence.append({"sentence": s[:600],
                         "usd": mag["usd"], "per_share": mag["per_share"],
                         "side": "A" if hit_a and not hit_b else ("B" if hit_b and not hit_a else "mixed"),
                         "markers": [lab for _, lab in hit_a + hit_b]})
    both = a_score > 0 and b_score > 0
    if a_score == 0 and b_score == 0:
        cls = "unclear"
    # MONEY BREAKS THE TIE when both sides fire: whichever pot is ~3x the other decides the name.
    elif both and rec_usd and unrec_usd and rec_usd >= 3 * unrec_usd:
        cls = "A"
    elif both and rec_usd and unrec_usd and unrec_usd >= 3 * rec_usd:
        cls = "B"
    elif a_score > b_score:
        cls = "A"
    elif b_score > a_score:
        cls = "B"
    else:
        cls = "unclear"     # a genuine tie is not a call — the court can read the sentences
    return {"classification": cls, "a_score": a_score, "b_score": b_score,
            "a_reasons": sorted(set(a_reasons)), "b_reasons": sorted(set(b_reasons)),
            "both_sides": both,
            "refund_recognized_usd": rec_usd, "refund_unrecognized_usd": unrec_usd,
            "refund_usd": rec_usd if cls == "A" else (unrec_usd if cls == "B" else (rec_usd or unrec_usd)),
            "refund_per_share": best_ps,
            "sunset_cited_in_filing": sunset_cited,
            "evidence": evidence[:6]}


# ---------------------------------------------------------------------------
# Market overlay — labeled as MARKET DATA, never used to infer a filing fact.
# ---------------------------------------------------------------------------
def _market(ticker: str) -> dict:
    out = {"source": "yfinance (market data, NOT a filing fact)"}
    try:
        import warnings
        warnings.filterwarnings("ignore")
        import yfinance as yf
        t = yf.Ticker(ticker)
        try:
            tr = t.eps_trend
            if tr is not None and not tr.empty:
                for per in ("0y", "0q"):
                    if per in tr.index:
                        cur = float(tr.loc[per, "current"])
                        d90 = float(tr.loc[per, "90daysAgo"])
                        out[f"eps_{per}_current"] = round(cur, 4)
                        out[f"eps_{per}_90d_ago"] = round(d90, 4)
                        # a percentage revision is meaningless across a sign flip or off a
                        # near-zero base (BYRN printed -563% because the estimate crossed zero)
                        if d90 and abs(d90) >= 0.05 and (cur > 0) == (d90 > 0):
                            out[f"eps_{per}_rev_pct_90d"] = round(100.0 * (cur - d90) / abs(d90), 2)
                        else:
                            out[f"eps_{per}_rev_pct_90d"] = None
                            out[f"eps_{per}_rev_note"] = "not meaningful — sign flip or near-zero base"
        except Exception:
            pass
        try:
            rv = t.eps_revisions
            if rv is not None and not rv.empty and "0y" in rv.index:
                out["up_revisions_30d_0y"] = int(rv.loc["0y", "upLast30days"])
                out["down_revisions_30d_0y"] = int(rv.loc["0y", "downLast30days"])
            if rv is not None and not rv.empty and "0q" in rv.index:
                out["up_revisions_7d_0q"] = int(rv.loc["0q", "upLast7days"])
        except Exception:
            pass
        info = {}
        try:
            info = t.info or {}
        except Exception:
            pass
        out["market_cap"] = info.get("marketCap")
        out["shares_outstanding"] = info.get("sharesOutstanding")
        out["short_pct_float"] = info.get("shortPercentOfFloat")
        out["days_to_cover"] = info.get("shortRatio")
        try:
            out["price"] = round(float(t.fast_info.get("lastPrice")), 2)
        except Exception:
            pass
    except Exception as e:
        out["error"] = str(e)[:120]
    return out


def _squeeze_gate(mkt: dict) -> tuple[bool, str]:
    """gate-6: no shorting attention names. A-fades are estimate fades, not short recommendations."""
    spf = mkt.get("short_pct_float")
    dtc = mkt.get("days_to_cover")
    hot = (spf is not None and spf >= 0.08) or (dtc is not None and dtc >= 4.0)
    if hot:
        return True, (f"NO_SHORT — squeeze fuel present (short {100 * spf:.1f}% of float, "
                      f"{dtc} days-to-cover). Express as FADE-THE-ESTIMATE in court, never a short."
                      if spf is not None and dtc is not None else
                      "NO_SHORT — squeeze fuel present. FADE-THE-ESTIMATE only.")
    return False, "FADE-THE-ESTIMATE candidate for court. Not an auto-short (gate-6 applies regardless)."


def scan(since: str, until: str, pages: int, max_docs: int, do_market: bool) -> dict:
    tmap = _ticker_map()

    # ---- 1. harvest EFTS ------------------------------------------------------------
    by_doc: dict[str, dict] = {}
    per_query = {}
    for spec in QUERIES:
        rows = _efts(spec["q"], since, until, pages)
        per_query[spec["q"]] = len(rows)
        for r in rows:
            key = f"{r['adsh']}:{r['fname']}"
            if key in by_doc:
                by_doc[key]["spec"] = max(by_doc[key]["spec"], spec["spec"])
                by_doc[key]["queries"].append(spec["q"])
            else:
                r["spec"] = spec["spec"]
                r["queries"] = [spec["q"]]
                by_doc[key] = r
        time.sleep(0.3)

    # one document per accession: the highest-specificity matched file (press release beats the wrapper)
    by_adsh: dict[str, dict] = {}
    for r in by_doc.values():
        cur = by_adsh.get(r["adsh"])
        if not cur or r["spec"] > cur["spec"]:
            by_adsh[r["adsh"]] = r
    docs = sorted(by_adsh.values(), key=lambda r: (-r["spec"], r["date"]), reverse=False)
    docs = sorted(docs, key=lambda r: (-r["spec"], r["date"] or ""), reverse=True)
    docs = sorted(docs, key=lambda r: -r["spec"])
    n_total_docs = len(docs)
    fetch = docs[:max_docs]

    # ---- 2. read the filings, extract verbatim sentences ------------------------------
    parsed = []
    for i, r in enumerate(fetch):
        raw = _get(_doc_url(r["cik"], r["adsh"], r["fname"]))
        if not raw:
            continue
        txt = _text(raw)
        sents = [s for s in _sentences(txt) if TARIFF_TOK.search(s) and RECOVER_TOK.search(s)]
        if not sents:
            continue
        cl = _classify(sents)
        if cl["classification"] == "unclear" and not cl["evidence"]:
            continue
        info = tmap.get(r["cik"]) or {}
        parsed.append({**r, **cl, "ticker": info.get("ticker", ""),
                       "sec_name": info.get("title", r["name"]),
                       "filing_url": _doc_url(r["cik"], r["adsh"], r["fname"]),
                       "n_trigger_sentences": len(sents)})
        if i % 25 == 0:
            print(f"  ...{i}/{len(fetch)} docs read, {len(parsed)} with tariff-recovery language",
                  file=sys.stderr)
        time.sleep(0.12)

    # ---- 3. roll up to the issuer -----------------------------------------------------
    by_cik: dict[int, dict] = {}
    for p in parsed:
        cur = by_cik.get(p["cik"])
        if not cur:
            by_cik[p["cik"]] = {**p, "filings": [{"form": p["form"], "date": p["date"],
                                                  "adsh": p["adsh"], "url": p["filing_url"],
                                                  "classification": p["classification"]}]}
            continue
        cur["filings"].append({"form": p["form"], "date": p["date"], "adsh": p["adsh"],
                               "url": p["filing_url"], "classification": p["classification"]})
        # Keep the strongest-signal filing as the issuer's representative row. EVERY derived field
        # moves together — v1 omitted the magnitude keys from this list, so an issuer could show a
        # dollar figure read from one filing beside a verbatim sentence quoted from another
        # (GIII's $139.5M and COLM's $78M sat next to sentences that contained no such number).
        # A quoted sentence and the magnitude printed beside it must come from the SAME document.
        new_rank = (p["a_score"] + p["b_score"], p["date"] or "")
        cur_rank = (cur["a_score"] + cur["b_score"], cur["date"] or "")
        if new_rank > cur_rank:
            for k in ("classification", "a_score", "b_score", "a_reasons", "b_reasons",
                      "both_sides", "refund_usd", "refund_per_share",
                      "refund_recognized_usd", "refund_unrecognized_usd",
                      "evidence", "date", "form", "adsh", "filing_url",
                      "sunset_cited_in_filing", "n_trigger_sentences"):
                cur[k] = p[k]

    names = list(by_cik.values())

    # ---- 4. market overlay (A and B only; unclear rows do not earn a data pull) --------
    if do_market:
        for n in names:
            if n["classification"] == "unclear" or not n["ticker"]:
                continue
            n["market"] = _market(n["ticker"])
            time.sleep(0.25)

    # ---- 5. rank ----------------------------------------------------------------------
    for n in names:
        mkt = n.get("market") or {}
        n["quantified"] = bool(n.get("refund_usd") or n.get("refund_per_share"))
        rev = mkt.get("eps_0y_rev_pct_90d")

        # THE BRIEF'S A-BAR: refund > 15% of the quarter's EPS. The per-share refund comes from the
        # filing when the filing states one (the FND shape); otherwise it is DERIVED as
        # filing-dollars / reported shares outstanding. Both inputs are real figures — the division
        # is ours and is labeled as such. Denominator = the consensus current-quarter EPS.
        ps, deriv = n.get("refund_per_share"), "filing states a per-share figure"
        if ps is None and n.get("refund_usd") and mkt.get("shares_outstanding"):
            try:
                ps = float(n["refund_usd"]) / float(mkt["shares_outstanding"])
                deriv = "DERIVED: filing dollars / reported shares outstanding (pre-tax basis unless the filing says otherwise)"
            except Exception:
                ps = None
        q_eps = mkt.get("eps_0q_current")
        if ps and q_eps:
            n["refund_per_share_used"] = round(ps, 4)
            n["refund_per_share_basis"] = deriv
            n["refund_pct_of_quarter_eps"] = round(100.0 * ps / abs(q_eps), 1)
            n["over_15pct_of_quarter_eps"] = n["refund_pct_of_quarter_eps"] > 15.0
            if n["refund_pct_of_quarter_eps"] > 300:
                # legitimate for a micro-cap whose refund dwarfs a thin quarter (AOUT), but it is
                # also the shape a mis-parsed magnitude takes — never let it pass unchallenged
                n["magnitude_verify"] = ("refund exceeds 3x the quarter's consensus EPS — plausible for a "
                                         "thin-earnings small cap, but READ THE VERBATIM SENTENCE before "
                                         "acting; do not take the ratio on trust")
        else:
            n["refund_pct_of_quarter_eps"] = None
            n["over_15pct_of_quarter_eps"] = None
            n["refund_per_share_basis"] = "NOT COMPUTABLE — no per-share figure in the filing and no share count"
        n["consensus_marked_up"] = bool(rev is not None and rev > 0.5)
        # A rank: quantified refund x consensus being marked UP (the mirage is being extrapolated)
        if n["classification"] == "A":
            hot, note = _squeeze_gate(mkt)
            n["squeeze_fuel"] = hot
            n["expression"] = note
            # THE BRIEF'S A BAR, both legs required: the one-timer is material to the quarter's EPS
            # AND the consensus is being marked UP on it (the mirage is actually being extrapolated).
            # A big refund at a name whose estimates are being CUT is not a mirage — the market has
            # already seen through it (BYRN: -563% revision on a widening loss; refund is real,
            # the fade is not).
            n["A_bar_met"] = bool(n.get("over_15pct_of_quarter_eps") and n["consensus_marked_up"])
            if mkt.get("eps_0y_current") is not None and mkt["eps_0y_current"] < 0:
                n["revision_caveat"] = ("consensus FY EPS is a LOSS — the % revision is unstable and "
                                        "the estimate-fade framing does not apply cleanly")
            score = n["a_score"]
            if n["quantified"]:
                score += 3
            if n["refund_per_share"]:
                score += 2      # a per-share figure is the FND-shaped, directly-comparable tell
            if n.get("over_15pct_of_quarter_eps"):
                score += 4      # the brief's bar: the one-timer is material to the quarter's EPS
            if rev is not None:
                score += max(0.0, min(6.0, rev))          # bigger mark-up = bigger mirage
            if (mkt.get("up_revisions_30d_0y") or 0) > (mkt.get("down_revisions_30d_0y") or 0):
                score += 2
            n["rank_score"] = round(score, 2)
        elif n["classification"] == "B":
            score = n["b_score"]
            if n["quantified"]:
                score += 3      # the brief's B bar: QUANTIFIED embedded cost, not just persist language
            if any("PERSIST" in r or "persist" in r for r in n["b_reasons"]):
                score += 3      # explicit persist-assumption language
            if n["sunset_cited_in_filing"]:
                score += 2      # the ISRG shape: the company printed the sunset in its own filing
            n["rank_score"] = round(score, 2)
            n["confounders"] = CONFOUNDERS
            n["expression"] = ("POSITIVE SKEW on a public fact — RP_FAIR with a skew overlay, not an "
                               "edge. Own at a fair price; do not pay an edge premium.")
        else:
            n["rank_score"] = 0.0

    # names meeting BOTH legs of the A bar lead the table regardless of raw marker score
    A = sorted([n for n in names if n["classification"] == "A"],
               key=lambda x: (not x.get("A_bar_met"), -x["rank_score"]))
    B = sorted([n for n in names if n["classification"] == "B"], key=lambda x: -x["rank_score"])
    U = [n for n in names if n["classification"] == "unclear"]

    return {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "mechanism": {
            "scotus_struck_ieepa": SCOTUS_DATE,
            "section_122_effective": S122_EFFECTIVE,
            "section_122_sunset": S122_SUNSET,
            "A_pattern": "EPS MIRAGE — refund recognized in results/guide; consensus extrapolates a "
                         "one-timer (the FND pattern). FADE-THE-ESTIMATE for court, never auto-short.",
            "B_pattern": "POSITIVE SKEW — refund unrecognized (gain contingency) and/or guide assumes "
                         "the tariff cost persists (the ISRG/ARHS pattern). Guide raises mechanically "
                         "if the sunset held.",
            "confounders": CONFOUNDERS,
        },
        "window": {"since": since, "until": until},
        "counts": {
            "efts_docs_matched": n_total_docs, "docs_fetched": len(fetch),
            "docs_with_tariff_recovery_language": len(parsed),
            "issuers": len(names), "A": len(A), "B": len(B), "unclear": len(U),
            "quantified": sum(1 for n in names if n.get("quantified")),
            "per_query_hits": per_query,
        },
        "A_fades": A, "B_skews": B, "unclear": U,
    }


def _fmt_usd(v) -> str:
    if not v:
        return "—"
    if v >= 1e9:
        return f"${v / 1e9:.2f}bn"
    if v >= 1e6:
        return f"${v / 1e6:.1f}M"
    return f"${v / 1e3:.0f}k"


def write_intake(res: dict) -> Path:
    d = datetime.date.today().strftime("%Y%m%d")
    path = INTAKE_DIR / f"TARIFF_REFUND_INTAKE_{d}.md"
    c = res["counts"]
    L = [f"# TARIFF-REFUND COHORT — intake {datetime.date.today()}",
         "",
         f"**Mechanism.** SCOTUS struck the IEEPA tariffs {SCOTUS_DATE}; the Section-122 replacement took "
         f"effect {S122_EFFECTIVE} and carried a 150-day statutory sunset at {S122_SUNSET}. Importers hold "
         "refund claims. The accounting choice splits the tape two ways.",
         "",
         f"**Coverage.** {c['efts_docs_matched']} EDGAR filings matched the query set; {c['docs_fetched']} read; "
         f"{c['docs_with_tariff_recovery_language']} carried tariff-recovery sentences; **{c['issuers']} issuers** "
         f"→ **{c['A']} A-fades / {c['B']} B-skews / {c['unclear']} unclear**; "
         f"**{c['quantified']} quantified from filings**.",
         "",
         "---", "",
         "## A — EPS-MIRAGE FADES (the FND pattern)",
         "*The refund is IN the reported number or the guide. Consensus marks up a one-timer. "
         "These are FADE-THE-ESTIMATE candidates for the court — not auto-shorts (gate-6).*", "",
         "| # | ticker | issuer | filing | refund recognized (filing) | % of qtr EPS | cons. FY rev 90d | up/dn 30d | **A bar** | squeeze | verbatim fragment |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, n in enumerate(res["A_fades"][:15], 1):
        m = n.get("market") or {}
        mag = _fmt_usd(n.get("refund_usd"))
        if n.get("refund_per_share"):
            mag += f" / ${n['refund_per_share']:.2f}ps"
        rev = m.get("eps_0y_rev_pct_90d")
        pct = n.get("refund_pct_of_quarter_eps")
        pcts = "—" if pct is None else (f"**{pct:.0f}%**" if n.get("over_15pct_of_quarter_eps") else f"{pct:.0f}%")
        if pct is not None and "DERIVED" in (n.get("refund_per_share_basis") or ""):
            pcts += "†"
        frag = (n["evidence"][0]["sentence"][:170] + "…") if n.get("evidence") else "—"
        L.append(f"| {i} | **{n['ticker'] or '—'}** | {n['sec_name'][:28]} | {n['form']} {n['date']} | {mag} | {pcts} | "
                 f"{f'{rev:+.1f}%' if rev is not None else '—'} | "
                 f"{m.get('up_revisions_30d_0y', '—')}/{m.get('down_revisions_30d_0y', '—')} | "
                 f"{'**MET**' if n.get('A_bar_met') else 'no'} | "
                 f"{'**NO_SHORT**' if n.get('squeeze_fuel') else 'ok'} | {frag.replace('|', '/')} |")
    L += ["", "**A bar** = BOTH legs: refund >15% of the quarter's consensus EPS AND consensus marked UP "
          "over 90d. A big refund at a name whose estimates are being CUT is not a mirage — the market "
          "already saw through it. Bar-MET rows sort first.",
          "", "† per-share refund DERIVED as filing dollars / reported shares outstanding (pre-tax basis "
          "unless the filing says otherwise); unmarked = the filing states the per-share figure itself. "
          "Denominator = consensus current-quarter EPS."]
    L += ["", "## B — POSITIVE-SKEW CONSERVATIVES (the ISRG / ARHS pattern)",
          "*Refund unrecognized and/or the guide assumes the tariff cost persists. The guide raises "
          "mechanically if the sunset held.*", "",
          "**CONFOUNDERS — apply to EVERY B name, no exceptions:**"]
    L += [f"{i}. {c_}" for i, c_ in enumerate(CONFOUNDERS, 1)]
    L += ["", "| # | ticker | issuer | filing | unrecognized / embedded (filing) | sunset in own filing | also recognized | markers | verbatim fragment |",
          "|---|---|---|---|---|---|---|---|---|"]
    for i, n in enumerate(res["B_skews"][:15], 1):
        ev = [e for e in n.get("evidence", []) if e.get("side") in ("B", "mixed")] or n.get("evidence") or []
        frag = (ev[0]["sentence"][:170] + "…") if ev else "—"
        L.append(f"| {i} | **{n['ticker'] or '—'}** | {n['sec_name'][:28]} | {n['form']} {n['date']} | "
                 f"{_fmt_usd(n.get('refund_unrecognized_usd'))} | {'YES' if n.get('sunset_cited_in_filing') else 'no'} | "
                 f"{_fmt_usd(n.get('refund_recognized_usd')) if n.get('both_sides') else '—'} | "
                 f"{'; '.join(n['b_reasons'])[:70]} | {frag.replace('|', '/')} |")
    L += ["", "---", "",
          "## Guards in force",
          "- **Magnitude from filings only.** Every dollar/per-share figure above is read from the verbatim "
          "sentence quoted beside it. Unquantified is printed as unquantified — never estimated.",
          "- **Consensus revisions are MARKET DATA** (yfinance), used as evidence that the mirage is being "
          "extrapolated — never to infer that a refund exists.",
          "- **gate-6:** no shorting attention names. A-rows carry short interest / days-to-cover; squeeze-fuel "
          "names are marked NO_SHORT. A-fades go to court as estimate fades.",
          "- **B is skew, not edge.** A statutory date printed in a widely-covered 10-Q is not an "
          "informational moat; classify RP_FAIR with a skew overlay.",
          "", f"Machine-readable: `{OUT_JSON}`"]
    path.write_text("\n".join(L))
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=SCOTUS_DATE)
    ap.add_argument("--until", default=datetime.date.today().isoformat())
    ap.add_argument("--pages", type=int, default=8)
    ap.add_argument("--max-docs", type=int, default=600)
    ap.add_argument("--no-market", action="store_true")
    a = ap.parse_args()

    res = scan(a.since, a.until, a.pages, a.max_docs, not a.no_market)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(res, indent=1, default=str))
    p = write_intake(res)
    c = res["counts"]
    print(f"tariff_refund_cohort: {c['efts_docs_matched']} filings matched / {c['docs_fetched']} read / "
          f"{c['issuers']} issuers -> A={c['A']} B={c['B']} unclear={c['unclear']} "
          f"quantified={c['quantified']}")
    print(f"  {OUT_JSON}\n  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
