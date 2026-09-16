"""lockup_expiry_scanner — Stage 0b FLOW: the IPO/SPAC lock-up expiration forced-supply calendar.

A lock-up expiry is a DATED, price-INSENSITIVE forced-SUPPLY event. When a newly-public
company IPOs, insiders / pre-IPO holders / VCs sign an underwriter lock-up (standard 180 days,
sometimes 90/365) barring them from selling. On the expiry date that restriction lifts and a
large locked share count can hit a thin public float for the first time — the mechanics are a
pre-unlock drift-DOWN (holders front-run their own supply) and an unlock-DAY air-pocket. The
trade is to buy the forced-seller washout, exactly the ADIG orphan-spin pattern in reverse-time:
a mechanical, calendar-scheduled seller with no view on price.

How it works (all free, no keys):
  1. EDGAR EFTS full-text search for recent 424B4 (final IPO prospectus) filings over the last
     ~200 days — each hit gives issuer, CIK, filing date (~= the IPO/pricing date).
  2. Lock-up TERM: fetch the prospectus and parse the "<N> days after the date of this prospectus"
     lock-up language (standard 180; 90/365 seen). If unparseable -> DEFAULT 180, record flagged
     lockup_days_estimated=True. unlock_date = ipo_date + lockup_days.
  3. BUCKET on days-to-unlock: 'imminent' = 0..21d (the actionable air-pocket window),
     'upcoming' = 22..90d. Passed or >90d are dropped.
  4. Ticker resolved from EDGAR company_tickers.json (CIK->ticker); live price via yfinance for
     CONTEXT only (optional, tolerates failure).

Magnitude proxy (locked shares vs public float) is NOT cheaply available from the 424B4 cover in
a machine-parseable way across issuers, so est_locked_pct_float is left None with a note — the DD
step pulls the cover's share counts / a later 10-Q shares-outstanding vs the IPO float. We do NOT
fabricate the magnitude. Seed = EDGAR's 424B4 stream; EXPAND (S-1/424B3 SPAC de-SPAC lockups,
secondary-lockup tranches) in v2.

    python3 verticals/generators/lockup_expiry_scanner.py
Writes data/LOCKUP_EXPIRY.json. READ-ONLY — never places an order.
"""
from __future__ import annotations

import datetime
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "LOCKUP_EXPIRY.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}

LOOKBACK_DAYS = 200          # 424B4 filings this far back can still have a live/near lock-up
DEFAULT_LOCKUP_DAYS = 180    # the standard underwriter lock-up; flagged when we fall back to it
IMMINENT_MAX = 21            # 0..21 days to unlock = the actionable air-pocket window
UPCOMING_MAX = 90            # 22..90 days = watch/pre-drift window
MAX_PARSE = 60               # cap prospectus fetches (politeness / rate-limit) — newest first
PRIOR_PERIODIC_YEARS = 1.0   # a 10-K/10-Q/20-F predating the 424B4 by > this = NOT a fresh IPO
BROKEN_IPO_PCT = 0.60        # current px < this * IPO px = a badly broken IPO -> value_trap flag


def _get_json(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=30) as r:
            return json.load(r)
    except Exception:
        return {}


def _submissions(cik10: str):
    """EDGAR submissions JSON for a 10-digit CIK. {} on any network/parse error."""
    return _get_json(f"https://data.sec.gov/submissions/CIK{cik10}.json")


def _ipo_eligibility(cik10: str, ipo_date: datetime.date):
    """Classify the issuer as fresh-IPO vs renamed-shell / established-follow-on.

    The load-bearing discriminator is PRIOR PUBLIC-REPORTING HISTORY, not the name alone:
      - a periodic report (10-K/10-Q/20-F) filed > PRIOR_PERIODIC_YEARS before the 424B4 => the
        issuer was ALREADY a reporting public company. If it ALSO carries a different former name
        it's a reverse-merger shell (Gemphire->NeuroBo->MetaVia: periodics back to 2016);
        otherwise it's an established-issuer follow-on / secondary (ProPetro, DAXOR). Both are
        rejected — neither is a first-IPO lock-up.

    A DIFFERENT former name WITHOUT prior periodic history is NOT a shell — it's a legal-entity
    re-org of a genuinely-fresh IPO (York Space Systems, ex-'Yellowstone Midco Holdings II, LLC',
    with no periodic filings predating its 424B4). Those PASS. Rejecting on formerNames alone
    over-fired and killed real IPOs (York/YSS, EquipmentShare/EQPT).

    Returns (is_ipo: bool, reject_reason: str|None). Network failure => (True, None): we do NOT
    reject on missing data, only on positive evidence of a shell / follow-on.
    """
    js = _submissions(cik10)
    if not isinstance(js, dict) or not js:
        return True, None                              # no evidence -> don't reject

    def _norm(n: str):
        n = re.sub(r"[^a-z0-9 ]", " ", (n or "").lower())
        n = re.sub(r"\b(inc|corp|corporation|ltd|llc|lp|plc|co|holdings?|company|group|the)\b", " ", n)
        return re.sub(r"\s+", " ", n).strip()
    cur = _norm(js.get("name", ""))
    former = js.get("formerNames") or []
    diff_former = [str(f.get("name", "")) for f in former
                   if isinstance(f, dict) and _norm(f.get("name", "")) and _norm(f.get("name", "")) != cur]

    cutoff = ipo_date - datetime.timedelta(days=int(365.25 * PRIOR_PERIODIC_YEARS))
    recent = (js.get("filings") or {}).get("recent") or {}
    forms = recent.get("form") or []
    dates = recent.get("filingDate") or []
    prior_periodic = None
    for form, fd in zip(forms, dates):
        if form in ("10-K", "10-Q", "20-F", "40-F", "10-KSB", "10-QSB"):
            try:
                if datetime.date.fromisoformat(fd) < cutoff:
                    prior_periodic = (form, fd)
                    break
            except Exception:
                continue

    if prior_periodic:
        form, fd = prior_periodic
        if diff_former:
            return False, (f"renamed_shell (formerNames: {', '.join(diff_former)}; "
                           f"prior {form} {fd} predates IPO — a reverse-merger shell, not a first IPO)")
        return False, f"followon (prior {form} {fd} predates IPO — established reporting issuer)"
    return True, None


def _efts_424b4(days=LOOKBACK_DAYS):
    """Recent final-IPO-prospectus (424B4) filings mentioning 'lock-up', newest first, paged."""
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    hits, seen = [], set()
    for frm in (0, 100, 200):     # EFTS returns 100/page; 3 pages covers the 424B4 stream over ~200d
        q = urllib.parse.urlencode({
            "forms": "424B4", "q": '"lock-up"',
            "startdt": start.isoformat(), "enddt": end.isoformat(), "from": frm,
        })
        js = _get_json(f"https://efts.sec.gov/LATEST/search-index?{q}")
        page = js.get("hits", {}).get("hits", []) if isinstance(js, dict) else []
        if not page:
            break
        for h in page:
            _id = h.get("_id", "")
            if _id and _id not in seen:
                seen.add(_id)
                hits.append(h)
    return hits


def _cik_ticker_map():
    """CIK(10-digit str) -> ticker from EDGAR's company_tickers.json (tolerate failure)."""
    js = _get_json("https://www.sec.gov/files/company_tickers.json")
    out = {}
    if isinstance(js, dict):
        for v in js.values():
            try:
                out[str(v["cik_str"]).zfill(10)] = v["ticker"]
            except Exception:
                continue
    return out


def _prospectus_text(cik: str, _id: str):
    """Fetch + de-tag the 424B4 document body from an EFTS _id ('accession:filename')."""
    try:
        acc, fn = _id.split(":")
        accn = acc.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accn}/{fn}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=45) as r:
            html = r.read().decode("utf-8", "ignore")
        t = re.sub(r"<[^>]+>", " ", html)
        return re.sub(r"\s+", " ", t)
    except Exception:
        return ""


# lock-up-day patterns in priority order. The standard underwriter clause is
# "...will not ... sell ... for a period of 180 days after the date of this prospectus".
# We anchor the strongest patterns to lock-up / prospectus / closing language so a bare
# "N days" (a quiet period, a notice window, a settlement cycle) can't masquerade as the term.
_LOCKUP_PATS = [
    r"lock-?up\s+(?:agreement|period)[^.]{0,160}?(\d{2,3})[\s-]*days",
    r"(?:for\s+a\s+period\s+of\s+)?(\d{2,3})[\s-]*days\s+after\s+the\s+date\s+of\s+this\s+prospectus",
    r"(\d{2,3})[\s-]*days\s+after\s+(?:the\s+)?(?:date\s+of\s+)?(?:the\s+)?closing",
    r"period\s+of\s+(\d{2,3})[\s-]*days",
    r"(\d{2,3})[\s-]*day\s+lock-?up",
]


def _parse_lockup_days(text: str):
    """Return (days, estimated) — parsed lock-up term or (DEFAULT, True) if unfound.

    Only accepts plausible terms {60,75,90,120,180,270,360,365}; the loose 'N days after
    prospectus' clause can also catch quiet-period / notice windows, so we constrain to real
    lock-up lengths. 75d matters — small-cap / shelf-takedown lock-ups run shorter than the
    180d standard and a hard-coded 180 mis-dates the unlock (the MetaVia trap: 75d, not 180d).
    """
    plausible = {60, 75, 90, 120, 180, 270, 360, 365}
    for p in _LOCKUP_PATS:
        for m in re.finditer(p, text, re.I):
            try:
                d = int(m.group(1))
            except Exception:
                continue
            if d in plausible:
                return d, False
    return DEFAULT_LOCKUP_DAYS, True


def _parse_ipo_price(text: str):
    """Best-effort IPO price/share from the 424B4 cover ('initial public offering price ... $X.XX').
    Returns float or None."""
    for p in (
        r"initial\s+public\s+offering\s+price\s+(?:of|is|was|per\s+share\s+(?:of|is|was)?)?\s*\$?\s*([0-9]{1,4}\.[0-9]{2})",
        r"public\s+offering\s+price\s+of\s+\$?\s*([0-9]{1,4}\.[0-9]{2})\s+per\s+share",
        r"\$?\s*([0-9]{1,4}\.[0-9]{2})\s+per\s+share",
    ):
        m = re.search(p, text, re.I)
        if m:
            try:
                v = float(m.group(1))
                if 0.10 <= v <= 1000:
                    return round(v, 2)
            except Exception:
                continue
    return None


def _litigation_probe(issuer: str):
    """Securities-litigation flag — DELIBERATELY a no-op from EDGAR alone.

    HONESTY NOTE (verified, do not re-add a naive EFTS query): confirming an ACTIVE securities-
    fraud class action needs docket data that lives at the COURTS (CourtListener/RECAP), not
    EDGAR. Every EFTS full-text attempt from here is a false-positive machine: 'class action' is
    risk-factor boilerplate in essentially every prospectus, and EFTS treats multiple quoted
    phrases as OR (not AND) — so '"BitGo" "securities class action"' returns hundreds of hits
    that merely mention BitGo, while a single combined phrase 500-errors. Emitting a warning off
    that would flag EVERY name and mean nothing.

    So this returns no hit by design. The RELIABLE value-trap tell we DO fire on is the broken-IPO
    price ratio (below). Confirming litigation is the DD step's job — the litigation-screen
    connector (CourtListener) runs a real docket search per principal. Returns (False, None)."""
    return False, None


def _yf_price(ticker: str):
    """Live-ish last price for context only. Optional; tolerate any failure."""
    try:
        import yfinance as yf
        fi = yf.Ticker(ticker).fast_info
        px = fi.get("last_price") or fi.get("lastPrice")
        return round(float(px), 2) if px else None
    except Exception:
        return None


def scan(with_prices: bool = True) -> dict:
    today = datetime.date.today()
    hits = _efts_424b4()
    tick = _cik_ticker_map()

    # Dedup by CIK (keep the newest 424B4 per issuer) and pre-filter to plausible candidates:
    # an IPO can be in-window only if SOME lock-up term in {90..365} lands its unlock in
    # [today .. today+UPCOMING]. Concretely ipo_date must be within [today-365 .. today-69].
    def _fdate(h):
        return (h.get("_source", {}) or {}).get("file_date", "")
    hits.sort(key=_fdate, reverse=True)

    cands, seen_cik = [], set()
    for h in hits:
        s = h.get("_source", {}) or {}
        ciks = s.get("ciks") or ([s.get("cik")] if s.get("cik") else [])
        cik10 = str(ciks[0]).zfill(10) if ciks else None
        fdate = s.get("file_date")
        if not cik10 or not fdate or cik10 in seen_cik:
            continue
        seen_cik.add(cik10)
        try:
            ipo_date = datetime.date.fromisoformat(fdate)
        except Exception:
            continue
        age = (today - ipo_date).days
        # shortest plausible term = 90d (unlock still ahead needs age<=90+UPCOMING);
        # longest = 365d (unlock already ahead needs age<=365). age>=69 so a 90d lock isn't stale.
        if age < 90 - UPCOMING_MAX or age > 365:
            continue
        cands.append((ipo_date, cik10, h, s))

    # Parse-priority: the closer an IPO's DEFAULT-180 unlock is to the actionable window, the more
    # a real term matters — parse those first so the budget lands on likely IN-WINDOW names.
    def _prio(c):
        ipo_date = c[0]
        return abs(((ipo_date + datetime.timedelta(days=DEFAULT_LOCKUP_DAYS)) - today).days)
    cands.sort(key=_prio)

    imminent, upcoming, rejected, parsed = [], [], [], 0
    for ipo_date, cik10, h, s in cands:
        name = (s.get("display_names") or [""])[0]
        mt = re.search(r"\(([A-Z][A-Z.\-]{0,5})\)", name)
        ticker = tick.get(cik10) or (mt.group(1) if mt else None)
        issuer = re.sub(r"\s*\([^)]*\)\s*", " ", name).strip()

        # FIX 1 & 3: reject renamed shells (formerNames) and established-issuer follow-ons
        # (a periodic report predating the 424B4). Positive evidence only — missing data passes.
        is_ipo, reject_reason = _ipo_eligibility(cik10, ipo_date)
        if not is_ipo:
            rejected.append({
                "issuer": issuer[:60], "ticker": ticker, "cik": cik10,
                "ipo_date": ipo_date.isoformat(), "is_ipo": False,
                "reject_reason": reject_reason,
            })
            continue

        lockup_days, estimated = DEFAULT_LOCKUP_DAYS, True
        ipo_px = None
        if parsed < MAX_PARSE:
            txt = _prospectus_text(cik10, h.get("_id", ""))
            if txt:
                lockup_days, estimated = _parse_lockup_days(txt)
                ipo_px = _parse_ipo_price(txt)
                parsed += 1

        unlock = ipo_date + datetime.timedelta(days=lockup_days)
        dte = (unlock - today).days
        if dte < 0:
            # a PARSED term whose unlock already passed (the MetaVia 75d trap: expired in April) —
            # bucket it as rejected/term_expired so it's visible, not silently dropped.
            rejected.append({
                "issuer": issuer[:60], "ticker": ticker, "cik": cik10,
                "ipo_date": ipo_date.isoformat(), "is_ipo": True,
                "lockup_days": lockup_days, "lockup_days_estimated": estimated,
                "unlock_date": unlock.isoformat(), "days_to_unlock": dte,
                "reject_reason": f"term_expired (unlock {unlock.isoformat()} already passed)",
            })
            continue
        if dte > UPCOMING_MAX:
            continue

        # SPAC IPO units/warrants: the OPERATING-company insider air-pocket applies at DE-SPAC,
        # not at the SPAC's own IPO lock-up — flag so the reader down-weights these (they dominate
        # the 424B4 stream by count but aren't the classic forced-seller washout).
        is_spac = bool(re.search(r"acquisition\s+corp|acquisition\s+ltd", issuer, re.I))
        is_unit = bool(ticker and re.search(r"(?:U|W|-WT|-UN|R)$", ticker))

        price = _yf_price(ticker) if (with_prices and ticker) else None

        # FIX 4: QUALITY / VALUE-TRAP FLAG (a warning, not a drop). A badly broken IPO
        # (px < BROKEN_IPO_PCT of the IPO price) or a litigation hit surfaces WITH a warning so a
        # BitGo-style air-pocket isn't mistaken for a clean buy. Row is kept — this informs the DD.
        broken_pct = None
        value_trap_risk = False
        trap_reasons = []
        if price and ipo_px:
            ratio = price / ipo_px
            # sanity-guard the parsed IPO price: a ratio >3x almost always means the cover parser
            # grabbed a wrong '$X.XX per share' figure (par value, option strike) rather than the
            # real IPO price (York/YSS parsed $0.35 -> a bogus 55x). Don't emit a garbage ratio.
            if 0 < ratio <= 3:
                broken_pct = round(ratio, 3)
                if broken_pct < BROKEN_IPO_PCT:
                    value_trap_risk = True
                    trap_reasons.append(f"broken IPO: ${price} vs ${ipo_px} IPO ({int(broken_pct*100)}% of issue)")
        lit_hit, lit_note = _litigation_probe(issuer)
        if lit_hit:
            value_trap_risk = True
            trap_reasons.append(lit_note)

        rec = {
            "issuer": issuer[:60], "ticker": ticker, "cik": cik10,
            "ipo_date": ipo_date.isoformat(), "is_ipo": True,
            "lockup_days": lockup_days, "lockup_days_parsed": (not estimated),
            "lockup_days_estimated": estimated,
            "unlock_date": unlock.isoformat(), "days_to_unlock": dte,
            "spac_or_unit": is_spac or is_unit,
            "est_locked_pct_float": None,          # NOT fabricated — DD pulls cover shares vs float
            "ipo_price": ipo_px, "price": price, "broken_ipo_pct": broken_pct,
            "value_trap_risk": value_trap_risk,
            "value_trap_reason": ("; ".join(trap_reasons) if trap_reasons else None),
            "note": ("DEFAULT 180d lock-up (prospectus term not parsed) — verify"
                     if estimated else f"lock-up term ({lockup_days}d) parsed from the 424B4")
                    + ("; SPAC/unit — air-pocket applies at DE-SPAC not this IPO, down-weight" if (is_spac or is_unit) else "")
                    + ("; VALUE-TRAP RISK — surfaced by magnitude but flagged: " + "; ".join(trap_reasons) if value_trap_risk else ""),
        }
        (imminent if dte <= IMMINENT_MAX else upcoming).append(rec)

    # operating companies first (the real air-pocket), then by nearest unlock
    imminent.sort(key=lambda r: (r["spac_or_unit"], r["days_to_unlock"]))
    upcoming.sort(key=lambda r: (r["spac_or_unit"], r["days_to_unlock"]))
    return {
        "asof": today.isoformat(), "n_scanned": len(seen_cik),
        "n_prospectus_parsed": parsed,
        "imminent": imminent, "upcoming": upcoming, "rejected": rejected,
        "note": "FLOW class — IPO lock-up expiry = a DATED, price-INSENSITIVE forced-SUPPLY event. "
                "Standard 180d (90/365 seen). Mechanics: pre-unlock drift-down (holders front-run "
                "their own supply) + an unlock-DAY air-pocket; the trade is BUYING the forced-seller "
                "washout, not shorting into it (that's crowded). 'imminent' = 0-21d to unlock (the "
                "actionable window), 'upcoming' = 22-90d (pre-drift watch). Source = EDGAR 424B4 "
                "full-text stream; lockup_days parsed from the prospectus where possible, else "
                "DEFAULT 180 with lockup_days_estimated=True. est_locked_pct_float is None — the "
                "magnitude (locked shares vs public float) is a DD pull from the cover / a later "
                "10-Q, NOT fabricated. IPO-eligibility is enforced from the EDGAR submissions JSON: "
                "renamed shells (formerNames non-empty, e.g. Gemphire->NeuroBo->MetaVia) and "
                "established-issuer follow-ons (a 10-K/10-Q/20-F predating the 424B4 by >1yr, e.g. "
                "ProPetro) are moved to 'rejected' with a reason, not surfaced as IPOs. A parsed "
                "term whose unlock already passed goes to 'rejected'/term_expired. Surviving names "
                "carry value_trap_risk: a badly broken IPO (px < 60% of issue) or a securities-"
                "litigation EFTS hit is flagged (a WARNING, the row is kept — it informs the DD, it "
                "is not deleted). EXPAND: SPAC de-SPAC 424B3 lockups + secondary-lockup tranches. "
                "READ-ONLY; times the trade, never places it.",
    }


def main():
    res = scan()
    OUT.write_text(json.dumps(res, indent=1))
    print(f"=== IPO LOCK-UP EXPIRY SCANNER  {res['asof']}  "
          f"({res['n_scanned']} recent IPOs scanned, {res['n_prospectus_parsed']} prospectuses parsed) ===")
    print(f"  IMMINENT (unlock in 0-{IMMINENT_MAX}d — the air-pocket window; buy the forced-seller washout):")
    if not res["imminent"]:
        print("    (none in window)")
    for r in res["imminent"]:
        px = f"${r['price']}" if r["price"] else "px?"
        est = " ~est180" if r["lockup_days_estimated"] else ""
        sp = " [SPAC/unit]" if r["spac_or_unit"] else ""
        vt = "  ** VALUE-TRAP: " + (r.get("value_trap_reason") or "") if r.get("value_trap_risk") else ""
        tk = r["ticker"] or "?"
        print(f"    {tk:6} {r['issuer'][:34]:34} unlock {r['unlock_date']} ({r['days_to_unlock']:+d}d, "
              f"{r['lockup_days']}d{est})  IPO {r['ipo_date']}  {px}{sp}{vt}")
    ops = [r for r in res["upcoming"] if not r["spac_or_unit"]]
    print(f"  UPCOMING (22-{UPCOMING_MAX}d — pre-drift watch; operating cos shown, SPAC/units hidden):")
    for r in ops[:15]:
        est = " ~est180" if r["lockup_days_estimated"] else ""
        tk = r["ticker"] or "?"
        print(f"    {tk:6} {r['issuer'][:34]:34} unlock {r['unlock_date']} ({r['days_to_unlock']:+d}d, "
              f"{r['lockup_days']}d{est})")
    if len(ops) > 15:
        print(f"    ... +{len(ops) - 15} more operating-co upcoming")
    n_spac_up = len(res["upcoming"]) - len(ops)
    if n_spac_up:
        print(f"    (+{n_spac_up} SPAC/unit upcoming suppressed — in JSON, down-weighted)")
    rej = res.get("rejected", [])
    print(f"  REJECTED (not a fresh-IPO first lock-up — {len(rej)}):")
    for r in rej[:20]:
        tk = r.get("ticker") or "?"
        print(f"    {tk:6} {r['issuer'][:34]:34} IPO {r['ipo_date']}  <- {r.get('reject_reason')}")
    if len(rej) > 20:
        print(f"    ... +{len(rej) - 20} more rejected")
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
