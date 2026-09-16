"""spinoff_orphans — Stage-0b FLOW generator: the SPIN-OFF ORPHAN coverage-vacuum trade.

THE CLASSIC SETUP. A parent registers a spinco on Form 10-12B weeks-to-months before the
distribution. At distribution, holders of the parent are handed shares in a company they did not
choose, that no sell-side analyst covers, that is absent from their benchmark, and that is often
below their mandate's size/liquidity floor. They sell mechanically, on a calendar, with no view on
price. A filings-reader who has already read the information statement is trading against a
price-INSENSITIVE seller. The window is typically the first 30-90 days after distribution.

WHAT THE JULY-2026 ONE-SHOT (THEME_SPINOFF_FLOW_2026_07_04.json) ESTABLISHED — the correction this
generator is built around, because the naive version of the trade is WRONG in the US today:

    THE INDEX-FLOW MECHANISM IS VENUE-CONDITIONAL AND, FOR S&P 500 PARENTS, INVERTED.
    S&P DJI now makes SAME-CYCLE index placement decisions for qualifying spincos of S&P 500
    parents — the spinco is ADDED to an S&P index at (or within days of) distribution. When the
    spinco lands back in the S&P 500 (SOLS, Q, FDXF), index funds are forced BUYERS, not sellers,
    and the "orphan washout" never happens. Backtesting the whole 10-12B cohort therefore
    manufactures false alpha off the index-INCLUDED winners.

    The washout fires only on the DOWNGRADE / NO-PLACEMENT sub-cohort:
      (a) S&P 500 parent -> spinco placed in MidCap 400 or SmallCap 600 (the sole genuine net
          forced-SELL: every S&P 500 fund must sell a line it can never hold — MBGL),
      (b) spinco given NO index placement at all (the purest orphan), and
      (c) non-US venues with no auto-placement rule (DAX -> MDAX void, ~3 months — the Aumovio
          channel; that leg is out of scope for an EDGAR-sourced scanner and stays a manual watch).

    Corollaries encoded below: RMT (Reverse Morris Trust) deals produce ZERO holder flow — the
    spinco merges into an acquirer and parent holders get acquirer stock — so they are excluded,
    not scored. And the INVERTED trade is real and is a DIFFERENT playbook (long the forced BUY
    ahead of an index-inclusion announcement); this scanner LABELS it rather than pretending it is
    the orphan trade.

HOW IT WORKS (all free, no keys):
  1. DISCOVERY: the EDGAR full-index (Archives/edgar/full-index/YYYY/QTRn/form.idx), form type
     10-12B and 10-12B/A, over the trailing BACKFILL_DAYS (12mo+) — the registration stream for
     exchange-listed spin vehicles. Deduped by CIK (issuers rename mid-registration: Middleby Food
     Processing -> Midera, Cyprium -> Versigent — same CIK throughout). 10-12G is DELIBERATELY
     excluded: verified over 12 months, that stream is ~95% BDCs / private credit and PE feeder
     funds / OTC shells, not spins.
     The full-index is used INSTEAD OF the EFTS full-text API on purpose: EFTS answers a request
     burst with a blanket 403 that lasts minutes and returns an empty result set indistinguishable
     from "no spins were registered" — a silent-zero this scanner must not have. form.idx is
     authoritative, complete, ~5 requests per year of history, current through the prior business
     day, and carries the accession number inline.
  2. PARSE the information statement (Exhibit 99.1 — reliably the largest .htm in the filing):
     parent name, parent ticker ("...will continue to trade ... under the symbol DD"), spinco
     ticker ("we intend to list ... under the symbol Q"), record date, expected distribution date,
     distribution ratio, when-issued language. Late amendments carry filled-in dates; early ones
     carry blanks — an unparsed date is emitted as null, never guessed. Parent name is the MODAL
     candidate across every pattern, not the first hit (first-hit captured 'Honeywell that will
     hold the assets'), and the parent ticker falls back to an exact normalized-name lookup in
     EDGAR's company_tickers.json when the filing never restates the symbol.
  3. TRAP FILTER (positive evidence only, mirroring the lock-up scanner's IPO-eligibility gate).
     A 10-12B is also the form for an OTC-to-exchange UPLISTING, a holdco REORG and a foreign
     REDOMICILIATION — none of which is a spin. Rejects, each with a reason:
       - the ticker's price history STARTS BEFORE the Form 10          -> 'holdco_reorg /
         already_trading' (Enviri II Corp resolving to NVRI with bars back to 2024; BioStem and
         Private Bancorp are OTC issuers uplisting, trading for years)
       - a UK/Irish scheme-of-arrangement move to a US holdco          -> 'redomiciliation_no_flow'
         (Ashtead -> Sunbelt Rentals Holdings: every holder simply exchanges into the new parent,
         so there is no orphan and no forced flow)
       - Reverse Morris Trust                                          -> 'rmt_no_flow'
       - too little distribution language to be a spin at all          -> 'not_a_spin'
     The spin test does NOT key on the word "spin-off" (Mobility Global uses it twice against 269
     uses of "the distribution") nor on the capitalized defined term (that rejected Honeywell
     Aerospace, 15 capitalized vs 504 case-insensitive). It keys on case-insensitive "the
     distribution" density plus "information statement": across a full 12-month cohort real spins
     run 45-588 and 64-166, every non-spin tops out at 8 and 0.
  4. FORCED-SELLING SETUP: parent and spinco checked against the live S&P 500 / 400 / 600
     constituent lists and classified on the TIER MOVE (500 > 400 > 600 > none) — signing the flow
     off the S&P 500 alone missed Middleby (400) -> Midera (600), which is just as much a forced
     sell for 400 funds:
       FORCED_SELL_DOWNGRADE    spinco placed a tier DOWN -> the genuine mechanical sell
       ORPHAN_NO_PLACEMENT      spinco in NO S&P index -> the purest orphan
       FORCED_BUY_INVERTED      500 parent + 500 spinco -> index funds BUY; a different playbook
       INDEX_PLACEMENT_MATCHED  same tier -> funds keep the line, no mechanical flow
       ORPHAN_UNINDEXED_PARENT  parent not in a US index (foreign/OTC) -> coverage vacuum may be
                                real but the mechanical leg needs a manual home-index check
       PENDING_DISTRIBUTION     not yet distributed -> placement unknowable, watch
     Membership is read AS OF TODAY. For a live cohort that is what matters; a BACKTEST must pin
     membership to the distribution date, because S&P migrates names at later rebalances.
  5. TRACKING (already-trading spins): yfinance, measured FROM THE DISTRIBUTION, not from the first
     bar. Two distortions are removed:
       - leading zero-volume bars (MFP's 2026-06-26 phantom: volume 0, high 200, low 21, close
         110.50 against a real regular-way open of 35.00 next session — a fabricated -57% dump);
       - WHEN-ISSUED sessions, which open up to ~2 weeks early on a separate thin line and which
         Yahoo staples onto the front of the series. Measuring from bar 1 charged HONA a -27.4%
         drawdown off a $269.95 when-issued print against its $200 regular-way open. Where the
         filing gives a distribution date we cut to it (HONA's true drawdown: -20.7%); where it
         does not, metrics_from says 'first traded bar' and regular_way_start_unverified is set.
     Pattern classified as DUMPING / DUMP_THEN_BASE / BASING / NO_DUMP / RIPPING, alongside
     days_since_distribution and the forced-selling-window status (0-30 ACTIVE / 31-90 LATE /
     >90 CLOSED).

DEGRADATION IS LOUD, NEVER SILENT. Both upstreams throttle: EDGAR answers a burst with a blanket
403, Yahoo with a rate-limit error, and in both cases the naive result is an empty/None value that
is indistinguishable from a real "nothing here". So: an empty EDGAR discovery aborts WITHOUT
writing; a per-ticker Yahoo failure leaves stage/setup/window as None so the MERGE keeps the last
good classification (rather than demoting a live orphan to 'not yet distributed'); and every
unresolved name is printed in its own report section.

Output: data/SPINOFF_ORPHANS.json, MERGE semantics — keyed by CIK, new names appended, existing
names updated field-by-field, and any hand-added keys (desk_note, disposition, prior_art) are
PRESERVED. The store is never rewritten from scratch.

    python3 verticals/generators/spinoff_orphans.py
    python3 verticals/generators/spinoff_orphans.py --no-parse    # discovery + tracking only
READ-ONLY. Times and sizes the trade; never places one.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "SPINOFF_ORPHANS.json"
IDX_CACHE = HERE / "data" / "_sp_constituents.json"
PRIOR_ART = HERE / "data" / "THEME_SPINOFF_FLOW_2026_07_04.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}

BACKFILL_DAYS = 400        # >12mo: seeds the current orphan cohort and one full index-cycle of history
MAX_PARSE = 32             # information statements are up to ~4MB — cap fetches, newest first
DOC_BYTES = 6_000_000      # hard read cap per document
IDX_CACHE_DAYS = 7         # S&P constituent lists refreshed weekly
WINDOW_ACTIVE = 30         # 0-30d post-distribution = forced selling ACTIVE
WINDOW_LATE = 90           # 31-90d = LATE window (discretionary orphan drift)
DUMP_PCT = 0.10            # >=10% drawdown off the first-week high = a dump worth naming
BASE_RECOVERY = 0.04       # >=4% up off the trough (and trough not today) = it has based
SLEEP = 0.12               # SEC fair-access pacing (limit is 10 req/s; we run ~8)

# S&P index float-cap floors, as published by S&P DJI in the 2026 methodology. HEURISTIC USE ONLY —
# they are used to explain a placement, never to assert one. Actual placement is read from the live
# constituent lists.
SP_FLOOR_NOTE = "S&P 500 >=~$22.7B, MidCap 400 ~$7.4-22.7B, SmallCap 600 ~$1.1-7.4B (2026 methodology)"


# ----------------------------------------------------------------------------- fetch helpers
BACKOFF = (5, 15, 45, 90)   # SEC answers a burst with a temporary 403 block; it clears in ~1-2 min
FETCH_ERRORS = []           # every give-up is recorded, so a degraded run reports DEGRADED not "clean"


def _get(url: str, timeout: int = 60) -> bytes:
    """GET with SEC-fair-access pacing and 403/429-aware backoff.

    EDGAR does not rate-limit with a 429 — it answers a burst with a blanket 403 for ~1-2 minutes.
    Swallowing that returns an EMPTY cohort that looks identical to 'no spins registered', which is
    the worst possible failure mode for a scanner. So: retry with backoff, and on final failure
    record the URL in FETCH_ERRORS so the run is labelled DEGRADED.
    """
    last = None
    for i, wait in enumerate((0,) + BACKOFF):
        if wait:
            time.sleep(wait)
        try:
            time.sleep(SLEEP)
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(DOC_BYTES)
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in (403, 429, 500, 502, 503, 504):
                break
        except Exception as e:
            last = e
    FETCH_ERRORS.append(f"{type(last).__name__}: {url[:120]}")
    raise last if last else RuntimeError(url)


def _gj(url: str, timeout: int = 40):
    """JSON GET; {} on any failure after backoff (the caller checks FETCH_ERRORS for degradation)."""
    try:
        return json.loads(_get(url, timeout))
    except Exception:
        return {}


def _gt(url: str, timeout: int = 90) -> str:
    """Fetch a filing document and strip tags/entities to flat text. '' on failure."""
    try:
        h = _get(url, timeout).decode("utf-8", "ignore")
    except Exception:
        return ""
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    t = re.sub(r"<[^>]+>", " ", h)
    # Decode the entities that carry MEANING before blanking the rest: '&amp;' blanked to a space
    # turned "S&P Global" into "S P Global" in every parsed parent name.
    for ent, ch in (("&amp;", "&"), ("&#38;", "&"), ("&apos;", "'"), ("&#39;", "'"),
                    ("&quot;", '"'), ("&nbsp;", " "), ("&#8217;", "'"), ("&rsquo;", "'")):
        t = t.replace(ent, ch)
    t = re.sub(r"&(?:#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);", " ", t)
    return re.sub(r"\s+", " ", t)


# ----------------------------------------------------------------------------- 1. discovery
def _quarters(days: int):
    """The EDGAR full-index quarters spanning [today-days, today], newest first."""
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    qs, y, q = [], start.year, (start.month - 1) // 3 + 1
    while (y, q) <= (end.year, (end.month - 1) // 3 + 1):
        qs.append(f"{y}/QTR{q}")
        q += 1
        if q > 4:
            y, q = y + 1, 1
    return list(reversed(qs))


def discover_form10(days: int = BACKFILL_DAYS):
    """Every 10-12B / 10-12B/A filing in the window, from the EDGAR full-index. Newest first.

    WHY full-index AND NOT the EFTS full-text API: EFTS answers a request burst with a blanket
    403 that lasts minutes and returns an EMPTY result set that is indistinguishable from "no
    spins were registered" — a silent-zero failure mode this scanner must not have. form.idx is a
    complete, authoritative, ~5-request-per-year enumeration on www.sec.gov, is current through
    the prior business day, and carries the accession number directly (no second lookup). EFTS
    remains useful for text search; it is not needed for a form-type enumeration.

    10-12G is DELIBERATELY excluded: verified over 12 months, that stream is ~95% BDCs, private
    credit/PE feeder funds and OTC shells, not exchange-listed spin vehicles.
    """
    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    rows = []
    for qtr in _quarters(days):
        try:
            txt = _get(f"https://www.sec.gov/Archives/edgar/full-index/{qtr}/form.idx", 90).decode("latin-1")
        except Exception:
            continue
        for line in txt.split("\n"):
            if not line.startswith("10-12B"):
                continue
            # fixed-width-ish: form | company | cik | date | edgar/data/<cik>/<accession>.txt
            m = re.match(r"^(10-12B(?:/A)?)\s+(.+?)\s{2,}(\d+)\s+(\d{4}-\d{2}-\d{2})\s+(\S+)", line)
            if not m:
                continue
            form, name, cik, fdate, path = m.groups()
            if fdate < cutoff:
                continue
            adsh = Path(path).stem
            rows.append({"form": form, "name": name.strip(), "cik": str(cik).zfill(10),
                         "file_date": fdate, "adsh": adsh})
    rows.sort(key=lambda r: r["file_date"], reverse=True)
    return rows


def group_by_cik(rows):
    """Collapse the filing stream into one registrant per CIK.

    Issuers RENAME mid-registration (Middleby Food Processing -> Midera; Cyprium -> Versigent;
    Solstice Advanced Materials LLC -> Inc.) — same CIK throughout, so CIK is the only stable key.
    The newest filing's name wins.
    """
    reg = {}
    for row in rows:
        cik = row["cik"]
        name = re.sub(r"\s*/\s*[A-Z]{2}\s*$", "", row["name"]).strip()   # 'Corp / IN' state suffix
        r = reg.setdefault(cik, {
            "cik": cik, "registrant": name, "filings": [], "_adsh": {},
        })
        key = f"{row['file_date']} {row['form']}"
        if key not in r["filings"]:
            r["filings"].append(key)
        r["_adsh"][row["file_date"]] = row["adsh"]
    for r in reg.values():
        r["filings"].sort(reverse=True)
        r["first_registered"] = r["filings"][-1].split()[0]
        r["latest_filing"] = r["filings"][0].split()[0]
        r["n_amendments"] = max(0, len(r["filings"]) - 1)
    return reg


def submissions(cik10: str):
    return _gj(f"https://data.sec.gov/submissions/CIK{cik10}.json")


# ----------------------------------------------------------------------------- 2/3. parse
def largest_doc(cik10: str, adsh: str):
    """Filename of the biggest .htm in the accession = the Exhibit 99.1 information statement.

    Verified across the cohort: the Form 10 cover itself is ~20-30KB while the information
    statement (which carries the parent, the dates, the tickers and the capitalization) is
    0.5-4MB, so 'largest .htm' resolves it without parsing the exhibit index.
    """
    if not adsh:
        return None
    u = f"https://www.sec.gov/Archives/edgar/data/{int(cik10)}/{adsh.replace('-', '')}/index.json"
    js = _gj(u)
    items = ((js.get("directory") or {}).get("item") or []) if isinstance(js, dict) else []
    htm = [(int(i.get("size") or 0), i["name"]) for i in items
           if str(i.get("name", "")).lower().endswith((".htm", ".html"))]
    if not htm:
        return None
    size, name = max(htm)
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik10)}/{adsh.replace('-', '')}/{name}"


_JUNK_PARENT = re.compile(r"^(future|fellow|our|valued|new)\b", re.I)


def _clean_co(name: str) -> str:
    name = re.sub(r"\s+", " ", (name or "")).strip(" ,.:;-")
    return re.sub(r"\s*\(.*?\)\s*", " ", name).strip()


def parse_info_statement(text: str, registrant: str) -> dict:
    """Pull the spin facts out of the information statement. Every field is None if unparsed.

    Nothing here is inferred: an early 10-12B/A literally leaves the distribution date blank
    ('expected to be completed on , 2025'), and a blank is reported as a blank.
    """
    out = {
        "is_spin": False, "spin_evidence": None, "rmt": False, "redomiciliation": False,
        "parent_name": None, "parent_ticker": None, "spinco_ticker_filed": None,
        "record_date": None, "distribution_date_expected": None,
        "distribution_ratio": None, "when_issued_language": False,
        "leverage_to_parent_flag": False,
    }
    if not text:
        return out

    # --- is this actually a spin?
    # DO NOT key on the word "spin-off": several real spins barely use it and run instead on the
    # defined terms "the Distribution" / "the Separation" (Mobility Global: 2 uses of 'spin-off'
    # against 269 of 'the distribution'; Versant: 2 against 279). Nor on the CASE-SENSITIVE defined
    # term — capitalization is inconsistent across filers and agents, and keying on it rejected
    # Honeywell Aerospace (15 capitalized vs 504 case-insensitive). Measured over a full 12-month
    # cohort the clean discriminator is case-INSENSITIVE density plus the information statement:
    # real spins run 45-588 'the distribution' with 64-166 'information statement', while every
    # non-spin (uplisting, shell, redomiciliation) tops out at 8 and 0.
    n_dist = len(re.findall(r"\bthe\s+distribution\b", text, re.I))
    n_is = len(re.findall(r"information\s+statement", text, re.I))
    n_spin = len(re.findall(r"spin-?off", text, re.I))
    n_sda = len(re.findall(r"separation\s+and\s+distribution\s+agreement", text, re.I))
    out["is_spin"] = (n_dist >= 30 and n_is >= 20) or n_sda >= 5
    out["spin_evidence"] = (f"'the distribution' x{n_dist}, 'information statement' x{n_is}, "
                            f"'spin-off' x{n_spin}, separation-and-distribution-agreement x{n_sda}")
    out["rmt"] = bool(re.search(r"Reverse\s+Morris\s+Trust", text, re.I))
    # A UK/Irish scheme-of-arrangement REDOMICILIATION also files a Form 10 and also creates a new
    # listed holdco — but every holder simply exchanges into the new parent, so there is no orphan
    # and no forced flow. Ashtead -> Sunbelt Rentals Holdings is the type specimen (92 uses).
    n_redom = len(re.findall(r"redomicil", text, re.I))
    out["redomiciliation"] = n_redom >= 5 and not out["is_spin"]
    if out["redomiciliation"]:
        out["spin_evidence"] += f"; REDOMICILIATION ('redomicil' x{n_redom}, scheme of arrangement)"

    # --- parent: the information statement is addressed to the PARENT's holders.
    # Candidates are pooled across every pattern and the MODAL one wins — taking the first match
    # captured a relative clause on Honeywell ('Honeywell that will hold the assets') where the
    # modal answer across 4 hits was plainly 'Honeywell'. 'Shareowner' is Honeywell's house term.
    cands = []
    for p, w in ((r"Dear\s+([A-Z][A-Za-z0-9&.,'\- ]{2,55}?)\s+(?:Stockholder|Shareholder|Shareowner)", 5),
                 (r"wholly[\s-]owned\s+subsidiary\s+of\s+([A-Z][A-Za-z0-9&.,'\- ]{2,55}?)(?:\s*[,(.]|\s+and\b|\s+that\b|\s+which\b)", 1),
                 (r"separation\s+from\s+([A-Z][A-Za-z0-9&.,'\- ]{2,55}?)(?:\s*[,(.]|\s+and\b|\s+that\b|\s+which\b)", 1),
                 (r"stockholders?\s+of\s+([A-Z][A-Za-z0-9&.,'\- ]{2,55}?)\s+(?:will\s+receive|of\s+record)", 1)):
        for m in re.finditer(p, text):
            cand = _clean_co(m.group(1))
            cand = re.split(r"\s+(?:that|which|will|and\s+its)\s+", cand)[0].strip(" ,.")
            if cand and not _JUNK_PARENT.match(cand) and 2 < len(cand) <= 45:
                cands.extend([cand] * w)
    if cands:
        out["parent_name"] = max(set(cands), key=cands.count)

    # --- parent ticker: only the PARENT "continues to trade" under its existing symbol
    m = re.search(r"(?:will\s+)?continues?\s+to\s+(?:be\s+)?trade[sd]?[^.]{0,240}?"
                  r"symbol\s+[\"“]?([A-Z]{1,5})\b", text)
    if m:
        out["parent_ticker"] = m.group(1)

    # --- spinco ticker: the SPINCO is being listed for the first time
    for p in (r"(?:intend\s+to\s+(?:have\s+)?(?:apply\s+to\s+)?list|expect\s+to\s+list|"
              r"has\s+been\s+approved\s+for\s+listing|will\s+be\s+listed|applied\s+to\s+list)"
              r"[^.]{0,260}?under\s+the\s+symbol\s+[\"“]?([A-Z]{1,5})\b",
              r"under\s+the\s+symbol\s+[\"“]?([A-Z]{1,5})[\"”]?[^.]{0,80}?(?:following|after)\s+the\s+"
              r"(?:distribution|spin-?off)"):
        for m in re.finditer(p, text):
            sym = m.group(1)
            if sym != out["parent_ticker"]:
                out["spinco_ticker_filed"] = sym
                break
        if out["spinco_ticker_filed"]:
            break

    # --- dates (a blank in the filing stays a blank here)
    D = r"([A-Z][a-z]{2,8}\s+\d{1,2},\s+\d{4})"
    m = re.search(r"on\s+" + D + r"\s*,?\s*(?:the\s+)?record\s+date", text) or \
        re.search(r"record\s+date[^.]{0,60}?\b(?:is|will\s+be)\s+" + D, text)
    if m:
        out["record_date"] = _isodate(m.group(1))
    for p in (r"distribution\s+date[^.]{0,80}?(?:is|will\s+be|is\s+expected\s+to\s+be)\s+" + D,
              r"on\s+" + D + r"\s*,?\s*(?:the\s+)?distribution\s+date",
              r"expected\s+to\s+be\s+completed\s+on\s+" + D,
              r"distribution\s+(?:is\s+)?expected\s+to\s+occur\s+on\s+" + D,
              # Honeywell's cover letter carries the only filled-in date in the whole document:
              # "we expect to distribute all of the outstanding shares ... on June 29, 2026"
              r"expect\s+to\s+distribute[^.]{0,200}?\bon\s+" + D,
              r"distribut(?:e|ion\s+of)[^.]{0,160}?\bon\s+" + D + r"[^.]{0,40}?(?:to\s+(?:our\s+)?(?:stockholders|shareholders|shareowners))"):
        m = re.search(p, text, re.I)
        if m:
            out["distribution_date_expected"] = _isodate(m.group(1))
            break

    m = re.search(r"[Ff]or\s+ever(?:y)\s+([\d,.]+)\s+shares?\s+of[^.]{0,120}?receive\s+([\d,.]+)\s+shares?", text)
    if m:
        out["distribution_ratio"] = f"{m.group(2)} spinco per {m.group(1)} parent"

    out["when_issued_language"] = bool(re.search(r"when-?issued", text, re.I))

    # --- the ADIG informed-seller tell: spinco levers up and pushes the cash to the parent
    out["leverage_to_parent_flag"] = bool(
        re.search(r"(?:pay|distribute|transfer)[^.]{0,120}?(?:cash\s+)?(?:dividend|distribution)"
                  r"[^.]{0,80}?to\s+(?:our\s+)?(?:parent|" + re.escape((out["parent_name"] or " ")[:24]) + r")",
                  text, re.I)
        and re.search(r"expect[^.]{0,120}?incur[^.]{0,120}?indebtedness", text, re.I))
    return out


def _isodate(s: str):
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.datetime.strptime(re.sub(r"\s+", " ", s).strip(), fmt).date().isoformat()
        except Exception:
            continue
    return None


# ----------------------------------------------------------------------------- 4. index membership
def sp_constituents(force: bool = False) -> dict:
    """{'500': [...], '400': [...], '600': [...]} — cached weekly on disk.

    Source is the Wikipedia constituent tables (the only free, no-key, machine-readable S&P
    membership list). Selection picks, among the wikitables on the page, the one whose distinct
    ticker count is CLOSEST to the index's nominal size — the pages also carry a 'recent changes'
    table whose tickers would otherwise pollute the set (the S&P 400 page's changes table yields
    589 symbols against the constituents table's 400).
    """
    if IDX_CACHE.exists() and not force:
        try:
            js = json.loads(IDX_CACHE.read_text())
            age = (datetime.date.today() - datetime.date.fromisoformat(js["asof"])).days
            if age <= IDX_CACHE_DAYS and all(js.get("indices", {}).get(k) for k in ("500", "400", "600")):
                return js["indices"]
        except Exception:
            pass
    pages = {"500": ("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", 500),
             "400": ("https://en.wikipedia.org/wiki/List_of_S%26P_400_companies", 400),
             "600": ("https://en.wikipedia.org/wiki/List_of_S%26P_600_companies", 600)}
    idx = {}
    for k, (u, expect) in pages.items():
        try:
            time.sleep(SLEEP)
            h = _get(u, 60).decode("utf-8", "ignore")
        except Exception:
            FETCH_ERRORS.append(f"sp_constituents:{k}")
            idx[k] = []
            continue
        cands = []
        for tbl in re.findall(r"<table[^>]*wikitable[^>]*>(.*?)</table>", h, re.S):
            got = []
            for row in re.findall(r"<tr[^>]*>(.*?)</tr>", tbl, re.S):
                cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)
                if len(cells) < 2:
                    continue
                for c in cells[:2]:
                    c0 = re.sub(r"<[^>]+>", "", c).strip()
                    if re.fullmatch(r"[A-Z][A-Z.\-]{0,5}", c0):
                        got.append(c0)
                        break
            if got:
                cands.append(sorted(set(got)))
        idx[k] = min(cands, key=lambda t: abs(len(t) - expect)) if cands else []
    # never overwrite a good cache with a degraded fetch
    if IDX_CACHE.exists():
        try:
            old = json.loads(IDX_CACHE.read_text()).get("indices", {})
            for k in ("500", "400", "600"):
                if len(idx.get(k) or []) < 0.5 * len(old.get(k) or []):
                    idx[k] = old[k]
        except Exception:
            pass
    IDX_CACHE.write_text(json.dumps(
        {"asof": datetime.date.today().isoformat(),
         "source": "en.wikipedia.org constituent tables (largest-table-nearest-nominal-size selection)",
         "indices": idx}, indent=1))
    return idx


_CT_CACHE = {}


def company_tickers():
    """{normalized company name: ticker} from EDGAR's company_tickers.json.

    Used only as a FALLBACK when the information statement never says "will continue to trade
    under the symbol X" — several filers name the parent in prose but never restate its ticker,
    which left the parent index unresolved and the setup UNCLASSIFIED.
    """
    if _CT_CACHE:
        return _CT_CACHE
    js = _gj("https://www.sec.gov/files/company_tickers.json")
    if isinstance(js, dict):
        for v in js.values():
            try:
                _CT_CACHE[_norm_co(v["title"])] = v["ticker"]
            except Exception:
                continue
    return _CT_CACHE


def _norm_co(n: str) -> str:
    n = re.sub(r"[^a-z0-9 ]", " ", (n or "").lower())
    n = re.sub(r"\b(inc|corp|corporation|ltd|limited|llc|lp|plc|co|holdings?|company|"
               r"group|the|de|nemours|nv|sa|ag|ab|se)\b", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def resolve_parent_ticker(parent_name: str):
    """Exact-normalized-name match only. An ambiguous or partial match returns None rather than a
    guess — a wrong parent ticker would silently mis-sign the whole forced-flow classification."""
    if not parent_name:
        return None
    key = _norm_co(parent_name)
    if not key or len(key) < 3:
        return None
    return company_tickers().get(key)


def index_of(ticker, idx) -> str:
    if not ticker:
        return "UNKNOWN"
    t = ticker.upper().replace(".", "-")
    for k in ("500", "400", "600"):
        pool = {x.upper().replace(".", "-") for x in (idx.get(k) or [])}
        if t in pool:
            return f"SP{k}"
    return "NONE"


_TIER = {"SP500": 3, "SP400": 2, "SP600": 1, "NONE": 0}
IDX_ASOF_CAVEAT = ("index membership is read AS OF TODAY, not as of the distribution — S&P DJI "
                   "migrates names between the 500/400/600 at later rebalances, so for a spin more "
                   "than ~90d old the class describes where it SITS, not necessarily where it was "
                   "PLACED. Fine for live cohort work; a backtest must pin membership to the "
                   "distribution date")


def classify_setup(parent_idx: str, spinco_idx: str, trading: bool) -> tuple:
    """(setup_class, is_our_trade, rationale) — the July-2026 doctrine, mechanized.

    The flow is signed by the TIER MOVE, not by the S&P 500 alone: an index fund that receives a
    spinco it cannot hold must sell it, and that is equally true of an S&P 400 parent whose spinco
    lands in the 600 (Middleby -> Midera). Ranking the tiers rather than special-casing the 500
    is what catches that; treating 400->600 as a 'same tier' placement understated it.
    """
    if not trading:
        return ("PENDING_DISTRIBUTION", None,
                "not yet distributed — S&P placement is decided at/near distribution, so the "
                "forced-flow SIGN is unknowable today; read the information statement now, size later")
    if parent_idx in ("UNKNOWN", "NONE"):
        return ("ORPHAN_UNINDEXED_PARENT", None,
                "the parent is not in an S&P US index (foreign primary listing, OTC, or the ticker "
                "did not resolve) — so there is no measurable US index flow to sign. The COVERAGE "
                "vacuum can still be real and is often deeper for a cross-border orphan (the "
                "DAX->MDAX / LSE-primary channel), but the mechanical leg must be checked by hand "
                "against the parent's actual home index. Not auto-sized")
    p, s = _TIER.get(parent_idx, 0), _TIER.get(spinco_idx, 0)
    if s == 0:
        return ("ORPHAN_NO_PLACEMENT", True,
                f"{parent_idx} parent, spinco in NO S&P index — the purest orphan: 100% of the "
                f"parent's index ownership is a forced seller with no offsetting index bid. "
                f"CAVEAT: {IDX_ASOF_CAVEAT}")
    if s < p:
        return ("FORCED_SELL_DOWNGRADE", True,
                f"{parent_idx} parent, spinco placed DOWN into {spinco_idx} — every {parent_idx} "
                f"fund must sell a line it can never hold. The genuine net forced-SELL sub-cohort "
                f"(MBGL is the type specimen). The flow is PARTLY OFFSET by {spinco_idx} funds "
                f"buying and is commonly front-run, so the edge is the discretionary orphan drift "
                f"AFTER the mechanical print, not the print itself. CAVEAT: {IDX_ASOF_CAVEAT}")
    if s == p == 3:
        return ("FORCED_BUY_INVERTED", False,
                "S&P DJI placed the spinco back in the S&P 500 same-cycle — index funds are forced "
                "BUYERS, not sellers. This is the INVERTED trade (a different playbook), NOT the "
                "orphan washout; including it in an orphan basket manufactures false alpha")
    if s == p:
        return ("INDEX_PLACEMENT_MATCHED", False,
                f"parent and spinco both in {spinco_idx} — the placement matches, so index funds "
                f"keep the line and there is no mechanical sell. No clean flow edge")
    return ("FORCED_BUY_UPGRADE", False,
            f"spinco placed UP ({parent_idx} parent -> {spinco_idx} spinco) — a forced BUY, the "
            f"inverted playbook, not the orphan washout")


# ----------------------------------------------------------------------------- 5. tracking
YF_BACKOFF = (15, 45, 120, 240)   # Yahoo throttles hard; a daily cron can afford to wait it out


def yf_batch(tickers):
    """{ticker: DataFrame|None} for every ticker, in ONE yfinance session, with rate-limit backoff.

    Returns None for a ticker with genuinely no data (not yet trading) and OMITS a ticker whose
    fetch FAILED. That distinction is load-bearing: Yahoo rate-limits aggressively, and a swallowed
    rate-limit makes every already-trading spinco look pre-distribution — which silently empties
    the orphan cohort while the scanner reports success. Failures go to FETCH_ERRORS instead.
    """
    tickers = sorted({t for t in tickers if t})
    if not tickers:
        return {}
    try:
        import yfinance as yf
    except Exception:
        FETCH_ERRORS.append("yfinance not importable — tracking leg unavailable")
        return {}
    out, pending, last = {}, list(tickers), None
    for wait in (0,) + YF_BACKOFF:
        if not pending:
            break
        if wait:
            time.sleep(wait)
        try:
            df = yf.download(pending, period="2y", auto_adjust=False, group_by="ticker",
                             progress=False, threads=False, actions=False)
        except Exception as e:
            last = e
            continue
        # yfinance reports PER-TICKER failures inside a partially-successful frame. A rate-limited
        # ticker and a genuinely-not-yet-trading ticker both come back as all-NaN columns, so the
        # only way to tell them apart is yfinance's own error map. Conflating them is what makes a
        # throttled run silently report every trading spinco as 'not yet distributed'.
        try:
            from yfinance import shared as _yfshared
            errs = dict(getattr(_yfshared, "_ERRORS", {}) or {})
        except Exception:
            errs = {}
        still = []
        for t in list(pending):
            transient = "ratelimit" in str(errs.get(t, "")).lower().replace(" ", "")
            if transient:
                still.append(t)
                last = errs.get(t)
                continue
            try:
                sub = df[t] if (df is not None and len(pending) > 1) else df
                sub = sub.dropna(how="all") if sub is not None else None
            except Exception:
                sub = None
            out[t] = sub if (sub is not None and not sub.empty) else None
        pending = still
    for t in pending:
        FETCH_ERRORS.append(f"yfinance rate-limited after {len(YF_BACKOFF)} retries: {t}")
    return out


def price_track(h, form10_date: str, dist_date: str = None, wi_language: bool = False):
    """Post-distribution price behaviour from a price frame, or None if the name is not trading.

    Two guards that matter:
      - LEADING ZERO-VOLUME BARS ARE DROPPED. Yahoo emits a phantom opening/when-issued bar for
        fresh spins (MFP 2026-06-26: volume 0, high 200, low 21, close 110.50 against a real
        regular-way open of 35.00 next session). Keeping it fabricates a -57% dump.
      - HISTORY PREDATING THE FORM 10 means the ticker is NOT a fresh distribution — it is the
        surviving parent of a holdco reorg or an already-listed issuer (Enviri II -> NVRI, bars to
        2024). Returned with reorg=True so the caller can reject rather than score it.
    """
    if h is None or getattr(h, "empty", True):
        return None
    try:
        vol = h["Volume"].fillna(0)
        keep = [i for i, v in enumerate(vol) if v > 0]
        if not keep:
            return None
        h = h.iloc[keep[0]:]
        first_dt = h.index[0].date()
        if form10_date and first_dt < datetime.date.fromisoformat(form10_date):
            return {"reorg": True, "first_bar": first_dt.isoformat(),
                    "note": f"price history starts {first_dt} — BEFORE the Form 10 ({form10_date}); "
                            f"not a fresh distribution"}
        # METRICS ARE MEASURED FROM THE DISTRIBUTION, NOT FROM THE FIRST BAR. When-issued trading
        # opens up to ~2 weeks early on a separate, thin line, and Yahoo staples those bars onto
        # the front of the series. Measuring from bar 1 charged HONA a -27.4% "dump" off a $269.95
        # when-issued print against a $200 regular-way open — an air-pocket that never happened to
        # anyone who received the distribution. When the filing gives us the date, we cut to it.
        rw_from = first_dt
        metrics_from = "first traded bar"
        if dist_date:
            try:
                d0 = datetime.date.fromisoformat(dist_date)
                if d0 > first_dt:
                    cut = h[h.index.map(lambda x: x.date() >= d0)]
                    if len(cut) >= 2:
                        h, rw_from, metrics_from = cut, d0, "filed distribution date"
            except Exception:
                pass
        close = h["Close"].astype(float)
        first_close = float(close.iloc[0])
        last_close = float(close.iloc[-1])
        early = close.iloc[:5]
        early_high = float(early.max())
        trough = float(close.min())
        trough_dt = close.idxmin().date()
        n = len(close)
        dd = (trough - early_high) / early_high if early_high else 0.0
        rec = (last_close - trough) / trough if trough else 0.0
        days_since_trough = (h.index[-1].date() - trough_dt).days
        tot = (last_close - first_close) / first_close if first_close else 0.0

        if dd <= -DUMP_PCT and rec >= BASE_RECOVERY and days_since_trough >= 5:
            pattern = "DUMP_THEN_BASE"
        elif dd <= -DUMP_PCT and days_since_trough <= 5:
            pattern = "DUMPING"
        elif dd <= -DUMP_PCT:
            pattern = "BASING"
        elif tot >= 0.15:
            pattern = "RIPPING"
        else:
            pattern = "NO_DUMP"
        return {
            "reorg": False,
            "first_bar_date": first_dt.isoformat(),
            "metrics_from": metrics_from,
            "metrics_start": rw_from.isoformat(),
            # Without a filed date we cannot tell a when-issued bar from a regular-way one, so the
            # drawdown may be overstated. Say so rather than let the number stand unqualified.
            "regular_way_start_unverified": (metrics_from == "first traded bar" and bool(wi_language)),
            "n_sessions": n,
            "first_close": round(first_close, 2),
            "early_high": round(early_high, 2),
            "trough": round(trough, 2), "trough_date": trough_dt.isoformat(),
            "last_close": round(last_close, 2),
            "drawdown_from_early_high_pct": round(dd * 100, 1),
            "recovery_off_trough_pct": round(rec * 100, 1),
            "total_since_distribution_pct": round(tot * 100, 1),
            "pattern": pattern,
        }
    except Exception:
        return None


def window_status(dist_date: str):
    if not dist_date:
        return None, None
    d = (datetime.date.today() - datetime.date.fromisoformat(dist_date)).days
    if d < 0:
        return d, "PRE_DISTRIBUTION"
    if d <= WINDOW_ACTIVE:
        return d, "FORCED_SELLING_ACTIVE"
    if d <= WINDOW_LATE:
        return d, "LATE_WINDOW"
    return d, "WINDOW_CLOSED"


# ----------------------------------------------------------------------------- merge + main
_DERIVED = {  # fields this scanner owns and may overwrite; anything else in the store is preserved
    "registrant", "sic", "sic_description", "biz_location", "filings", "n_amendments",
    "first_registered", "latest_filing", "parent_name", "parent_ticker", "parent_index",
    "spinco_ticker", "spinco_ticker_filed", "spinco_index", "when_issued_ticker", "exchange",
    "record_date", "distribution_date_expected", "distribution_date", "distribution_date_source",
    "distribution_ratio", "when_issued_language", "leverage_to_parent_flag", "is_spin",
    "spin_evidence", "rmt", "stage", "setup_class", "is_orphan_trade", "setup_rationale",
    "days_since_distribution", "window_status", "track", "reject_reason", "last_scanned",
    "price_status", "redomiciliation", "first_traded_bar", "when_issued_bars_suspected",
    "parent_ticker_source",
}


# Fields whose absence is itself the fact: once a name stops being rejected (or stops having
# when-issued bars), the old value must be CLEARED, not preserved by the stale-value guard.
_CLEARABLE = {"reject_reason", "when_issued_bars_suspected"}


def merge_write(records: dict, meta: dict) -> dict:
    """MERGE by CIK. Never clobbers: hand-added keys survive, and a degraded field (None) never
    overwrites a previously-good value."""
    store = {}
    if OUT.exists():
        try:
            store = json.loads(OUT.read_text())
        except Exception:
            store = {}
    spins = store.get("spins") or {}
    if isinstance(spins, list):  # tolerate an older list-shaped store
        spins = {r.get("cik"): r for r in spins if r.get("cik")}
    n_new = 0
    for cik, rec in records.items():
        cur = spins.get(cik)
        if cur is None:
            rec.setdefault("first_seen", datetime.date.today().isoformat())
            spins[cik] = rec
            n_new += 1
            continue
        for k, v in rec.items():
            if k in _DERIVED and k not in _CLEARABLE and v is None and cur.get(k) is not None:
                continue          # a failed fetch must not erase a good prior value
            cur[k] = v
    store["spins"] = spins
    store["asof"] = meta["asof"]
    store["n_tracked"] = len(spins)
    store["n_new_this_run"] = n_new
    for k in ("doctrine", "method", "note", "sp_index_asof", "backfill_days",
              "price_leg", "degraded", "fetch_errors"):
        if k in meta:
            store[k] = meta[k]
    OUT.write_text(json.dumps(store, indent=1))
    return store


DOCTRINE = (
    "SPIN-OFF ORPHAN = the coverage-vacuum trade: at distribution, parent holders are handed a "
    "stock no analyst covers, that is not in their benchmark, and that is often below their "
    "mandate floor — they sell on a calendar, price-insensitively, for ~30-90 days. BUT the US "
    "index leg is INVERTED for S&P 500 parents: S&P DJI now places qualifying spincos back into "
    "an S&P index SAME-CYCLE, so index funds are forced BUYERS (SOLS, Q, FDXF) and no washout "
    "occurs. The real forced-SELL cohort is (a) S&P 500 parent -> spinco DOWNGRADED into 400/600 "
    "(MBGL), (b) spinco given NO index placement, and (c) non-US no-auto-placement venues "
    "(DAX->MDAX, the Aumovio channel — out of scope for an EDGAR scanner, manual watch). RMT "
    "deals are EXCLUDED: parent holders receive acquirer stock, so there is zero orphan flow. Any "
    "backtest must isolate the downgrade/no-placement sub-cohort or the index-INCLUDED winners "
    "manufacture false alpha. Even inside the true cohort, the MECHANICAL print is front-run and "
    "partly offset — the durable edge is the DISCRETIONARY orphan drift over the following 4-8 "
    "weeks, into a name we have already read the information statement on."
)


def scan(parse: bool = True, track: bool = True, backfill_days: int = BACKFILL_DAYS) -> dict:
    today = datetime.date.today()
    rows = discover_form10(backfill_days)
    reg = group_by_cik(rows)
    idx = sp_constituents()
    prior = {}
    if PRIOR_ART.exists():
        try:
            prior = (json.loads(PRIOR_ART.read_text()).get("dispositions") or {})
        except Exception:
            prior = {}

    # PASS 1 — EDGAR facts (registration, ticker assignment, information statement).
    staged, parsed = [], 0
    for cik, r in sorted(reg.items(), key=lambda kv: kv[1]["latest_filing"], reverse=True):
        sub = submissions(cik)
        tickers = sub.get("tickers") or []
        exchanges = sub.get("exchanges") or []
        wi = next((t for t in tickers if t.endswith("-WI") or re.fullmatch(r"[A-Z]{4}V{1,2}", t)), None)
        live = [t for t in tickers if t != wi]
        ticker = live[0] if live else None
        exch = next((e for t, e in zip(tickers, exchanges) if t == ticker and e), None)

        addr = ((sub.get("addresses") or {}).get("business") or {})
        rec = {
            "cik": cik, "registrant": r["registrant"], "sic": sub.get("sic"),
            "sic_description": sub.get("sicDescription"),
            "biz_location": ", ".join(x for x in (addr.get("city"), addr.get("stateOrCountry")) if x) or None,
            "filings": r["filings"],
            "n_amendments": r["n_amendments"], "first_registered": r["first_registered"],
            "latest_filing": r["latest_filing"],
            "spinco_ticker": ticker, "when_issued_ticker": wi, "exchange": exch,
            "last_scanned": today.isoformat(),
        }

        # ---- parse the newest information statement
        p = {}
        if parse and parsed < MAX_PARSE:
            adsh = r["_adsh"].get(max(r["_adsh"])) if r["_adsh"] else None
            url = largest_doc(cik, adsh)
            if url:
                p = parse_info_statement(_gt(url), r["registrant"])
                parsed += 1
        rec.update({k: p.get(k) for k in (
            "is_spin", "spin_evidence", "rmt", "redomiciliation", "parent_name", "parent_ticker",
            "spinco_ticker_filed", "record_date", "distribution_date_expected",
            "distribution_ratio", "when_issued_language", "leverage_to_parent_flag")})
        if not rec["spinco_ticker"] and rec["spinco_ticker_filed"]:
            rec["spinco_ticker"] = rec["spinco_ticker_filed"]
        staged.append((cik, r, rec, p))

    # PASS 2 — one batched price fetch for the whole cohort (Yahoo rate-limits per-ticker loops,
    # and a swallowed rate-limit would report every trading spinco as 'not yet distributed').
    px = yf_batch([rec["spinco_ticker"] for _, _, rec, _ in staged]) if track else {}
    px_ok = bool(px) or not track

    records = {}
    for cik, r, rec, p in staged:
        tkr = rec["spinco_ticker"]
        tr = (price_track(px.get(tkr), r["first_registered"], p.get("distribution_date_expected"),
                          bool(p.get("when_issued_language")))
              if (track and tkr and tkr in px) else None)
        # a ticker the batch could not resolve at all is UNKNOWN, not 'not trading'
        price_status = ("OK" if (track and tkr and tkr in px) else
                        ("NO_TICKER" if not tkr else ("FETCH_FAILED" if track else "SKIPPED")))
        rec["price_status"] = price_status

        # ---- trap filter (positive evidence only)
        reject = None
        if tr and tr.get("reorg"):
            reject = f"holdco_reorg / already_trading ({tr['note']})"
        elif p and p.get("rmt"):
            reject = "rmt_no_flow (Reverse Morris Trust — parent holders receive ACQUIRER stock; zero orphan flow)"
        elif p and p.get("redomiciliation"):
            reject = (f"redomiciliation_no_flow (a UK/Irish scheme-of-arrangement move to a US holdco — "
                      f"every holder exchanges into the new parent, so there is no orphan and no forced "
                      f"flow; Ashtead -> Sunbelt Rentals is the type specimen. {p.get('spin_evidence')})")
        elif p and not p.get("is_spin"):
            reject = (f"not_a_spin (10-12B filed for an uplisting, shell or holdco registration, not a "
                      f"distribution; {p.get('spin_evidence')})")
        elif parse and not p:
            reject = None  # unparsed (budget/fetch) — do NOT reject on missing evidence

        if reject:
            rec.update({"stage": "REJECTED", "reject_reason": reject, "track": None,
                        "setup_class": None, "is_orphan_trade": False, "setup_rationale": None,
                        "days_since_distribution": None, "window_status": None,
                        "distribution_date": None, "distribution_date_source": None})
            records[cik] = rec
            continue

        # ---- stage + distribution date
        if tr:
            filed, first_bar = p.get("distribution_date_expected"), tr["first_bar_date"]
            # The FILED date wins when we have it: the first traded bar can be a WHEN-ISSUED
            # session, which runs up to ~2 weeks before the distribution (HONA printed bars from
            # Jun-15 against a filed distribution of Jun-29). Using the bar would age the
            # forced-selling window by that gap and close it early.
            if filed:
                rec["distribution_date"] = filed
                rec["distribution_date_source"] = "information statement (filed)"
            else:
                rec["distribution_date"] = first_bar
                rec["distribution_date_source"] = "first traded bar (zero-volume leading bars dropped)"
            rec["first_traded_bar"] = first_bar
            if filed and abs((datetime.date.fromisoformat(filed)
                              - datetime.date.fromisoformat(first_bar)).days) > 3:
                rec["when_issued_bars_suspected"] = (
                    f"first bar {first_bar} vs filed distribution {filed} — the earlier bars are "
                    f"when-issued; window dated off the FILED date")
            rec["stage"] = "TRADING"
        else:
            rec["distribution_date"] = p.get("distribution_date_expected")
            rec["distribution_date_source"] = "information statement (expected)" if rec["distribution_date"] else None
            if price_status == "FETCH_FAILED":
                # DO NOT claim 'not yet distributed' off a failed price fetch — that is exactly how
                # a rate-limited run would silently empty the orphan cohort. stage is left None so
                # the MERGE preserves whatever the last good run established.
                rec["stage"] = None
            elif rec["when_issued_ticker"]:
                rec["stage"] = "WHEN_ISSUED"
            else:
                rec["stage"] = "REGISTERED" if r["n_amendments"] < 2 else "LATE_STAGE_REGISTRATION"

        rec["reject_reason"] = None      # accepted this run — clear any stale rejection
        rec["track"] = tr
        if not rec.get("parent_ticker"):
            rec["parent_ticker"] = resolve_parent_ticker(rec.get("parent_name"))
            if rec["parent_ticker"]:
                rec["parent_ticker_source"] = "EDGAR company_tickers.json, exact normalized name match"
        rec["parent_index"] = index_of(rec.get("parent_ticker"), idx)

        if price_status == "FETCH_FAILED":
            # Everything downstream of the price leg is UNKNOWN this run, not FALSE. Emitting None
            # (rather than 'UNKNOWN'/'PENDING_DISTRIBUTION') lets the MERGE keep the last good
            # classification — otherwise one rate-limited run would silently demote MBGL from
            # FORCED_SELL_DOWNGRADE to 'not yet distributed'.
            for k in ("spinco_index", "setup_class", "is_orphan_trade", "setup_rationale",
                      "days_since_distribution", "window_status", "distribution_date",
                      "distribution_date_source"):
                rec[k] = None
        else:
            rec["spinco_index"] = index_of(rec.get("spinco_ticker"), idx) if tr else "UNKNOWN"
            cls, ours, why = classify_setup(rec["parent_index"], rec["spinco_index"], bool(tr))
            rec["setup_class"], rec["is_orphan_trade"], rec["setup_rationale"] = cls, ours, why
            d, ws = window_status(rec["distribution_date"])
            rec["days_since_distribution"], rec["window_status"] = d, ws

        if tkr and tkr in prior and "prior_art" not in rec:
            rec["prior_art"] = f"2026-07-04 one-shot: {prior[tkr]}"
        records[cik] = rec

    meta = {
        "asof": today.isoformat(), "backfill_days": backfill_days,
        "sp_index_asof": (json.loads(IDX_CACHE.read_text()).get("asof") if IDX_CACHE.exists() else None),
        "doctrine": DOCTRINE,
        "method": ("EDGAR full-index form.idx 10-12B/10-12B/A stream (12mo backfill) -> dedupe by CIK -> parse the "
                   "Exhibit-99.1 information statement (largest .htm) for parent / tickers / record + "
                   "distribution dates / ratio -> trap-filter uplistings, holdco reorgs and RMTs -> "
                   "S&P 500/400/600 membership for parent and spinco -> setup classification -> "
                   "yfinance post-distribution track measured from the FILED distribution date where available "
                   "(leading zero-volume and when-issued bars dropped). "
                   f"Index floors for context only: {SP_FLOOR_NOTE}."),
        "note": ("MERGE store, keyed by CIK. Unparsed fields are null, never guessed — early "
                 "10-12B/As literally leave the distribution date blank. Forced-selling window: "
                 f"0-{WINDOW_ACTIVE}d ACTIVE / {WINDOW_ACTIVE + 1}-{WINDOW_LATE}d LATE / >{WINDOW_LATE}d CLOSED. "
                 "READ-ONLY; never places an order."),
        "price_leg": "OK" if px_ok else "FAILED (yfinance rate-limited or unreachable — stages left UNRESOLVED, not downgraded)",
        "degraded": bool(FETCH_ERRORS),
        "fetch_errors": FETCH_ERRORS[:20] or None,
    }
    return {"records": records, "meta": meta, "n_registrants": len(reg), "n_parsed": parsed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-parse", action="store_true", help="skip information-statement fetches")
    ap.add_argument("--no-track", action="store_true", help="skip yfinance price tracking")
    ap.add_argument("--days", type=int, default=BACKFILL_DAYS)
    a = ap.parse_args()

    res = scan(parse=not a.no_parse, track=not a.no_track, backfill_days=a.days)
    if res["n_registrants"] == 0:
        # An empty EDGAR discovery is almost never real (the 10-12B stream runs ~50 filings/yr) —
        # it means EFTS threw a blanket 403 at us. Do NOT write: a silent empty run would advance
        # `asof` and make a throttled fetch read as "no spins registered".
        print("=== SPIN-OFF ORPHAN GENERATOR — DEGRADED, NOT WRITTEN ===")
        print("  EDGAR returned 0 10-12B registrants. That is a fetch failure, not an empty cohort.")
        for e in FETCH_ERRORS[:10]:
            print(f"    {e}")
        print(f"  store left untouched at {OUT}")
        sys.exit(2)
    store = merge_write(res["records"], res["meta"])
    if res["meta"]["degraded"]:
        print(f"!! DEGRADED RUN — {len(FETCH_ERRORS)} fetch failure(s); some fields may be stale/null:")
        for e in FETCH_ERRORS[:8]:
            print(f"     {e}")
    rows = list(store["spins"].values())

    print(f"=== SPIN-OFF ORPHAN GENERATOR  {res['meta']['asof']}  "
          f"({res['n_registrants']} 10-12B registrants over {a.days}d, {res['n_parsed']} information "
          f"statements parsed, {store['n_new_this_run']} new, {store['n_tracked']} tracked) ===")

    live = [r for r in rows if r.get("stage") == "TRADING" and r.get("window_status") != "WINDOW_CLOSED"]
    live.sort(key=lambda r: r.get("days_since_distribution") or 999)
    print(f"\n  ORPHAN COHORT — trading, forced-selling window still open (<= {WINDOW_LATE}d):")
    if not live:
        print("    (none)")
    for r in live:
        t = r.get("track") or {}
        flag = "**" if r.get("is_orphan_trade") else "  "
        print(f"  {flag}{(r.get('spinco_ticker') or '?'):6} {r['registrant'][:30]:30} "
              f"ex-{(r.get('parent_ticker') or r.get('parent_name') or '?')[:14]:14} "
              f"dist {r.get('distribution_date')} ({r.get('days_since_distribution')}d, {r.get('window_status')})")
        print(f"        {r.get('setup_class')}  parent={r.get('parent_index')} spinco={r.get('spinco_index')}  "
              f"| {t.get('pattern')}: first ${t.get('first_close')} -> trough ${t.get('trough')} "
              f"({t.get('drawdown_from_early_high_pct')}%) -> ${t.get('last_close')} "
              f"({t.get('recovery_off_trough_pct'):+}% off low)" if t else "")

    pend = [r for r in rows if r.get("stage") in ("WHEN_ISSUED", "LATE_STAGE_REGISTRATION", "REGISTERED")]
    pend.sort(key=lambda r: (r.get("stage") != "WHEN_ISSUED", r.get("latest_filing") or ""), reverse=False)
    print(f"\n  PIPELINE — registered, not yet distributed (read the information statement NOW):")
    for r in pend:
        wi = f" WI:{r['when_issued_ticker']}" if r.get("when_issued_ticker") else ""
        lev = "  ** LEVERAGE-TO-PARENT (informed-seller tell)" if r.get("leverage_to_parent_flag") else ""
        print(f"    {(r.get('spinco_ticker') or '?'):6} {r['registrant'][:34]:34} "
              f"ex-{(r.get('parent_name') or '?')[:22]:22} {r.get('stage'):26} "
              f"{r['n_amendments']}A last {r.get('latest_filing')}{wi}{lev}")

    closed = [r for r in rows if r.get("stage") == "TRADING" and r.get("window_status") == "WINDOW_CLOSED"]
    print(f"\n  WINDOW CLOSED ({len(closed)}) — history, for backtesting the sub-cohorts:")
    for r in sorted(closed, key=lambda r: r.get("days_since_distribution") or 0):
        t = r.get("track") or {}
        print(f"    {(r.get('spinco_ticker') or '?'):6} {r['registrant'][:26]:26} {r.get('setup_class'):22} "
              f"{r.get('days_since_distribution')}d  {t.get('pattern')}  "
              f"tot {t.get('total_since_distribution_pct')}%")

    rej = [r for r in rows if r.get("stage") == "REJECTED"]
    print(f"\n  REJECTED (not a spin-off orphan — {len(rej)}):")
    for r in rej:
        print(f"    {(r.get('spinco_ticker') or '?'):6} {r['registrant'][:34]:34} <- {(r.get('reject_reason') or '')[:96]}")

    # Anything the price leg could not resolve THIS run. It must be printed: without this section a
    # rate-limited name simply disappears from every bucket, and a shorter report reads like a
    # cleaner one.
    shown = {id(x) for x in live + pend + closed + rej}
    stale = [r for r in rows if id(r) not in shown]
    if stale:
        print(f"\n  UNRESOLVED THIS RUN ({len(stale)}) — price leg failed; values below are from the "
              f"last good run, NOT today:")
        for r in stale:
            print(f"    {(r.get('spinco_ticker') or '?'):6} {r['registrant'][:34]:34} "
                  f"stage={r.get('stage')} setup={r.get('setup_class')} "
                  f"(price_status={r.get('price_status')}, last_scanned={r.get('last_scanned')})")
    print(f"\n[-> {OUT.name}]")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------------------------
# REGISTRY SNIPPET — for the main session to paste into desk/registry.py (NOT edited from here).
#
#     {"name": "gen_spinoff_orphans", "cmd": ["python3", "verticals/generators/spinoff_orphans.py"],
#      "cadence": "daily", "log": "verticals/generators/data/spinoff_orphans_cron.out",
#      "asset_class": "equities", "extractor": "generic", "enabled": True,
#      "note": "Stage-0b FLOW generator: the SPIN-OFF ORPHAN coverage-vacuum trade. Polls the EDGAR "
#              "10-12B registration stream via the full-index form.idx (12mo backfill), parses each "
#              "Exhibit-99.1 information "
#              "statement for parent / tickers / record + distribution dates / ratio, trap-filters "
#              "uplistings + holdco reorgs + RMTs, then classifies the forced-flow SIGN off live S&P "
#              "500/400/600 membership. CRITICAL doctrine (from the 2026-07-04 one-shot): the US "
#              "index leg is INVERTED for S&P 500 parents — S&P DJI places qualifying spincos back "
#              "into an S&P index SAME-CYCLE, so funds are forced BUYERS (SOLS/Q/FDXF) and no "
#              "washout occurs. The true forced-SELL cohort is (a) S&P500 parent -> spinco "
#              "DOWNGRADED to 400/600 (MBGL) and (b) spinco with NO index placement; RMTs are "
#              "excluded (zero holder flow). Tracks post-distribution price with leading "
#              "zero-volume Yahoo bars dropped (the MFP phantom bar fabricates a -57% dump) and "
#              "buckets the window 0-30d ACTIVE / 31-90d LATE / >90d CLOSED. Daily because the "
#              "actionable state changes on single filings (an 8-A12B / a final amendment with the "
#              "distribution date filled in) and the window is short. MERGE store by CIK. EXPAND: "
#              "non-US no-auto-placement venues (DAX->MDAX, the Aumovio channel) + spin-debt / "
#              "dividend-to-parent quality screen + the INVERTED pre-inclusion long"},
#
# Daily is the right cadence: a single 10-12B/A can flip a name from 'date blank' to 'distributing
# in 9 days', and the whole edge is being read-up BEFORE the window opens.
# ---------------------------------------------------------------------------------------------
