"""Bond-STRUCTURE screen for the CA muni book — call risk, capital-appreciation
bonds (CABs), and insurance / underlying-rating surfacing.

WHY THIS EXISTS
---------------
Structural features change a bond's economics *independently of issuer credit*.
We got burned: CUSIP 926055KH6 (Victor Valley Union HSD GO Refunding 2016B) sat in
the book modeled as an ~11-year hold at ~8% after-tax yield — but its EMMA security
details show it is CALLABLE AT PAR (100.0) on 2026-08-01. As of the 2026-06-19 cutoff
that is a ~6-week par call, not a long hold: priced above par, it is economically a
short instrument that gets yanked at 100. A ladder anchor it is not. This module
catches that automatically so it never recurs.

WHAT IT CHECKS  (screen_structure(cusip) -> dict)
-------------------------------------------------
1. CALL RISK
   - next_call_date / call_price / years_to_call from EMMA /Security/Details/<cusip>
     (the same authoritative, post-disclaimer MSRB page compute_bond_analytics uses).
   - HARD flag "near-par-call: not a long hold" when years_to_call < 2 AND the bond is
     marked at/above (call_price - PAR_TOLERANCE). At/above a par call with a near call
     date => the call is in-the-money for the issuer and will very likely be exercised;
     the instrument's real horizon is the call, not the maturity.
   - SOFT flag "near call (<2y) but priced below call" when the call is near but the bond
     trades at a discount (call less likely to be economically exercised) — surface, don't
     hard-stop.

2. CAPITAL APPRECIATION BONDS (CABs)
   - zero-coupon / compound-interest CA school structures: toxic deferred-debt-service
     ratios; several CA districts were legislatively barred from issuing them (AB 182).
   - detected via coupon == 0 OR "capital appreciation" / "compound interest" / "CAB" /
     "accreted" in the security description. is_cab True -> HARD flag.

3. INSURANCE + UNDERLYING
   - insured (EMMA "Insured: Yes/No", authoritative boolean) + best-effort insurer name
     from the security description (AGM/BAM/AG/Assured/National/Ambac/...). EMMA's free
     security page carries the boolean but NOT the insurer name, so insurer is often None
     -> reported UNVERIFIABLE, never guessed.
   - underlying (uninsured) vs insured agency ratings from /Security/RatingsPartialView.
     EMMA's free tier is frequently rating-gated ("No ratings information provided") ->
     UNVERIFIABLE. An insured wrap on a (UNVERIFIABLE or weak) underlying is SURFACED, not
     failed — the framework already prices wrap compression conditional on the underlying.

HARD RULE: never fabricate a call date / call price / rating / insurer. If EMMA does not
render a call schedule the bond is call_status UNVERIFIABLE — a MISSING schedule is NOT
"non-callable". Missing ratings are UNVERIFIABLE, not "unrated".

Source: EMMA https://emma.msrb.org/Security/Details/<cusip> (post-disclaimer) +
/Security/RatingsPartialView. Reuses emma_scraper for the session/disclaimer machinery.
Cache: data/structure_cache.json keyed by CUSIP.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import date
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
import emma_scraper as E  # session, disclaimer accept, _hidden, BASE

# --- cutoff / valuation ---
TODAY = date(2026, 6, 19)               # cutoff = today, controls "years_to_call"
CACHE = Path(__file__).parent / "data" / "structure_cache.json"
BOOK = Path(__file__).parent / "data" / "etf_v2_holdings.json"

# A bond marked at >= (call_price - PAR_TOLERANCE) with a near call is effectively
# trading to the call. 1.0 point of slack absorbs bid/ask + small premia.
PAR_TOLERANCE = 1.0
NEAR_CALL_YEARS = 2.0

# Recognized monoline / muni bond insurers (current + legacy). Matched in the
# security description; legacy names (Ambac/MBIA/FGIC/...) still appear on seasoned wraps.
_INSURERS = [
    ("AGM", r"\bAGM\b|Assured Guaranty Municipal"),
    ("BAM", r"\bBAM\b|Build America Mutual"),
    ("AGC", r"Assured Guaranty Corp|\bAGC\b"),
    ("Assured Guaranty", r"Assured Guaranty"),
    ("National", r"National Public Finance|\bNational\b"),
    ("Berkshire Hathaway", r"Berkshire Hathaway Assurance|\bBHAC\b"),
    ("Ambac", r"\bAmbac\b"),
    ("MBIA", r"\bMBIA\b"),
    ("FGIC", r"\bFGIC\b"),
    ("Syncora", r"Syncora|\bXLCA\b"),
    ("Radian", r"\bRadian\b"),
    ("CIFG", r"\bCIFG\b"),
]

_CAB_PAT = re.compile(
    r"capital appreciation|compound interest|\bCAB\b|\bCABs\b|accreted|"
    r"accretion bond|convertible capital appreciation|\bCCAB\b",
    re.I,
)

_AGENCY_LABELS = {
    "Fitch": "Fitch",
    "KBRA": "Kroll",
    "Moody's": "Moody's",
    "Moody&#39;s": "Moody's",
    "S&#38;P": "S&P",
    "S&amp;P": "S&P",
    "S&P": "S&P",
}
_NO_RATING = "No ratings information provided"


# ----------------------------------------------------------------------------
def _d(s: str) -> Optional[date]:
    try:
        mm, dd, yy = s.split("/")
        return date(int(yy), int(mm), int(dd))
    except Exception:
        return None


def _flat(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def _accept(session, cusip: str, html_txt: str, url: str) -> str:
    """Accept the CUSIP-license disclaimer if the page is gated, return fresh HTML."""
    if "yesButton" not in html_txt:
        return html_txt
    session.post(
        E.BASE + "/Disclaimer.aspx",
        data={
            "__VIEWSTATE": E._hidden("__VIEWSTATE", html_txt),
            "__VIEWSTATEGENERATOR": E._hidden("__VIEWSTATEGENERATOR", html_txt),
            "__EVENTVALIDATION": E._hidden("__EVENTVALIDATION", html_txt),
            "ctl00$mainContentArea$disclaimerContent$yesButton": "Accept",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "Origin": E.BASE, "Referer": url},
        timeout=40,
    )
    return session.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text


def _security_description(html_txt: str) -> Optional[str]:
    """The issuer/issue/security description headline (EMMA renders it in an <h3>)."""
    best = None
    for m in re.finditer(r"<h3[^>]*>(.*?)</h3>", html_txt, re.S):
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
        # the security headline is the long all-caps issue title, not nav labels
        if len(txt) > 25 and any(k in txt.upper() for k in
                                 ("BOND", "NOTE", "DISTRICT", "AUTHORITY",
                                  "CITY", "COUNTY", "STATE", "OBLIGATION", "GO")):
            if best is None or len(txt) > len(best):
                best = txt
    return best


def _detect_insurer(desc: Optional[str], html_txt: str) -> Optional[str]:
    """Best-effort insurer name. EMMA's free security page does not carry the insurer
    name (only the Insured boolean), so this usually returns None -> UNVERIFIABLE.
    Never guess an insurer from the Insured=Yes flag alone."""
    hay = " ".join(x for x in (desc, _flat(html_txt)) if x)
    for name, pat in _INSURERS:
        if re.search(pat, hay):
            return name
    return None


def _fetch_ratings(session, cusip: str, ref_url: str) -> dict:
    """Per-agency long-term ratings from /Security/RatingsPartialView. EMMA's free tier
    is frequently rating-gated ('No ratings information provided') -> that agency is left
    out (UNVERIFIABLE). Returns {agency: rating_text} only for agencies that publish."""
    try:
        r = session.get(
            E.BASE + "/Security/RatingsPartialView",
            params={"cusip": cusip},
            headers={"X-Requested-With": "XMLHttpRequest",
                     "Accept": "text/html, */*; q=0.01", "Referer": ref_url},
            timeout=40,
        )
    except Exception:
        return {}
    flat = _flat(r.text)
    out = {}
    # Each agency renders as: "<Agency> <rating-or-'No ratings information provided ...'>"
    labels = ["Fitch", "KBRA", "Moody's", "S&#38;P", "S&P"]
    positions = []
    for lab in labels:
        i = flat.find(lab)
        if i >= 0:
            positions.append((i, lab))
    positions.sort()
    for idx, (pos, lab) in enumerate(positions):
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(flat)
        seg = flat[pos + len(lab):end].strip()
        if _NO_RATING in seg or not seg:
            continue
        # capture a rating token (Aaa/Aa1/AA+/BBB-/A1/etc.) near the agency label
        m = re.search(r"\b(Aaa|Aa[123]|A[123]|Baa[123]|Ba[123]|B[123]|"
                      r"Caa[123]|Ca|C|AAA|AA[+-]?|A[+-]?|BBB[+-]?|BB[+-]?|"
                      r"B[+-]?|CCC[+-]?|CC|D|NR)\b", seg)
        if m:
            out[_AGENCY_LABELS.get(lab, lab)] = m.group(1)
    return out


# ----------------------------------------------------------------------------
def _fetch_security(session, cusip: str) -> dict:
    """Pull the structural fields + latest mark from EMMA /Security/Details/<cusip>."""
    url = E.BASE + "/Security/Details/" + cusip
    t = session.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text
    t = _accept(session, cusip, t, url)
    flat = _flat(t)

    def g(pat):
        m = re.search(pat, flat)
        return m.group(1).strip() if m else None

    coupon = g(r"Coupon:\s*([\d.]+)\s*%")
    desc = _security_description(t)

    # latest trade mark (prefer most-recent sale-to-customer)
    px = tdate = None
    m = re.search(r"var tradeData = (\{.*?\});", t, re.S)
    n_trades = 0
    if m:
        try:
            rows = json.loads(m.group(1)).get("data", [])
        except json.JSONDecodeError:
            rows = []
        n_trades = len(rows)
        cust = [r for r in rows if r.get("TT") == "S"]
        pick = cust or rows
        if pick:
            px = pick[0].get("PX")
            tdate = (pick[0].get("TD") or "")[:10]

    ratings = _fetch_ratings(session, cusip, url)

    return {
        "cusip": cusip,
        "security_description": desc,
        "coupon": float(coupon) if coupon else None,
        "maturity_date": g(r"Maturity Date:\s*(\d{2}/\d{2}/\d{4})"),
        "dated_date": g(r"Dated Date:\s*(\d{2}/\d{2}/\d{4})"),
        "callable": g(r"Callable\s*:\s*(\w+)"),
        "next_call_date": g(r"Next Call Date\s*:\s*(\d{2}/\d{2}/\d{4})"),
        "call_price": (lambda v: float(v) if v else None)(g(r"Next Call Price \(%\)\s*:\s*([\d.]+)")),
        "insured_flag": g(r"Insured\s*:\s*(\w+)"),
        "insurer": _detect_insurer(desc, t),
        "ratings": ratings,
        "price": float(px) if px is not None else None,
        "trade_date": tdate,
        "n_trades": n_trades,
        "page_ok": "Security Details" in t or "Maturity Date" in flat,
    }


# ----------------------------------------------------------------------------
def _assess(rec: dict) -> dict:
    """Apply structure logic to a raw EMMA pull. Pure (no I/O) for testability."""
    cusip = rec["cusip"]
    flags_hard, flags_soft, notes = [], [], []

    # ---- (1) CALL RISK ----
    callable_ind = rec.get("callable")
    call_date_s = rec.get("next_call_date")
    call_price = rec.get("call_price")
    cd = _d(call_date_s) if call_date_s else None

    if not rec.get("page_ok"):
        call_status = "UNVERIFIABLE"          # page didn't render -> cannot assert anything
    elif callable_ind == "No":
        call_status = "NON_CALLABLE"
    elif callable_ind == "Yes" and cd is None:
        # callable but EMMA didn't render the schedule -> UNVERIFIABLE, NOT non-callable
        call_status = "UNVERIFIABLE"
        notes.append("callable=Yes but EMMA rendered no call date -> call schedule UNVERIFIABLE")
    elif cd is not None:
        call_status = "CALLABLE"
    else:
        call_status = "UNVERIFIABLE"

    years_to_call = None
    if cd is not None:
        years_to_call = round((cd - TODAY).days / 365.25, 2)

    price = rec.get("price")
    # A premium/at-par determination resting on a >12-month-old print is not trustworthy
    # (the bond may have amortized; mark is decade-stale on some seasoned names).
    # The call DATE is still authoritative, so we keep a near-call SOFT flag, but we do
    # not assert "in-the-money par call" off a stale mark — downgrade HARD->SOFT.
    tdate = rec.get("trade_date") or ""
    stale_mark = bool(tdate) and tdate < "2025-06-19"

    call_risk = "NONE"
    if call_status == "CALLABLE" and years_to_call is not None and cd > TODAY:
        cp = call_price if call_price is not None else 100.0
        near = years_to_call < NEAR_CALL_YEARS
        at_or_above = price is not None and price >= (cp - PAR_TOLERANCE)
        if near and at_or_above and not stale_mark:
            call_risk = "HARD"
            flags_hard.append(
                f"near-par-call: not a long hold (call {call_date_s} @ {cp:g}, "
                f"{years_to_call}y out; marked {price} >= call-{PAR_TOLERANCE:g})")
        elif near and at_or_above and stale_mark:
            call_risk = "SOFT"
            flags_soft.append(
                f"near call (<{NEAR_CALL_YEARS:g}y) at/above par but mark {price} is stale "
                f"(last trade {tdate}) — call date real, in-the-money-ness UNVERIFIABLE; "
                f"refresh mark before treating as long hold")
        elif near and price is None:
            # near call, no mark to judge in-the-money-ness -> surface, can't hard-stop
            call_risk = "SOFT"
            flags_soft.append(
                f"near call (<{NEAR_CALL_YEARS:g}y) but no recent mark to assess "
                f"call-economics (call {call_date_s} @ {cp:g})")
        elif near:
            call_risk = "SOFT"
            flags_soft.append(
                f"near call (<{NEAR_CALL_YEARS:g}y) but priced below call "
                f"({price} < {cp:g}); call less likely exercised — verify horizon")
    elif call_status == "UNVERIFIABLE":
        call_risk = "UNVERIFIABLE"

    # ---- (2) CABs ----
    desc = rec.get("security_description") or ""
    coupon = rec.get("coupon")
    is_cab = bool(_CAB_PAT.search(desc)) or (coupon is not None and coupon == 0.0)
    if is_cab:
        flags_hard.append("capital-appreciation/zero-coupon (CAB) structure — toxic "
                          "deferred debt-service; surface for exclusion")

    # ---- (3) INSURANCE + UNDERLYING ----
    insured = None
    if rec.get("insured_flag") == "Yes":
        insured = True
    elif rec.get("insured_flag") == "No":
        insured = False
    insurer = rec.get("insurer")  # often None on EMMA free page -> UNVERIFIABLE

    ratings = rec.get("ratings") or {}
    # EMMA's RatingsPartialView publishes the security's *enhanced* (insured) rating when
    # carried; the underlying/unenhanced rating is separately gated and usually absent.
    insured_rating = None
    underlying_rating = "UNVERIFIABLE"
    if ratings:
        # take the strongest available agency rating as the insured/enhanced rating proxy
        insured_rating = "; ".join(f"{a}:{v}" for a, v in sorted(ratings.items()))
    else:
        insured_rating = "UNVERIFIABLE"

    if insured:
        notes.append(
            "insured wrap present; underlying (uninsured) rating "
            f"{'UNVERIFIABLE on EMMA free tier' if underlying_rating == 'UNVERIFIABLE' else underlying_rating}"
            " — wrap compresses spread conditional on underlying; surface, do not exclude")
        flags_soft.append("insured wrap — confirm underlying credit (wrap masks issuer risk)")

    verdict = "FLAG" if flags_hard else ("REVIEW" if flags_soft else "CLEAN")

    return {
        "cusip": cusip,
        "security_description": rec.get("security_description"),
        "coupon": coupon,
        "maturity_date": rec.get("maturity_date"),
        # call risk
        "callable": callable_ind,
        "call_status": call_status,
        "next_call_date": call_date_s,
        "call_price": call_price,
        "years_to_call": years_to_call,
        "price": price,
        "trade_date": rec.get("trade_date"),
        "call_risk": call_risk,
        # CAB
        "is_cab": is_cab,
        # insurance / underlying
        "insured": insured,
        "insurer": insurer,                       # None -> UNVERIFIABLE insurer name
        "insured_rating": insured_rating,
        "underlying_rating": underlying_rating,
        # roll-up
        "hard_flags": flags_hard,
        "soft_flags": flags_soft,
        "notes": notes,
        "verdict": verdict,
        "as_of": TODAY.isoformat(),
    }


# ----------------------------------------------------------------------------
def _load_cache() -> dict:
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text())
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=2, default=str))


def screen_structure(cusip: str, session=None, use_cache: bool = True,
                     refresh: bool = False) -> dict:
    """Run the bond-structure screen on one CUSIP.

    Returns a dict with (selected) fields:
      cusip, security_description, coupon, maturity_date,
      callable, call_status (CALLABLE / NON_CALLABLE / UNVERIFIABLE),
      next_call_date, call_price, years_to_call, price, trade_date,
      call_risk (NONE / SOFT / HARD / UNVERIFIABLE),
      is_cab,
      insured (bool/None), insurer, insured_rating, underlying_rating,
      hard_flags[], soft_flags[], notes[], verdict (CLEAN/REVIEW/FLAG), as_of.

    Call-risk flag logic:
      HARD  "near-par-call: not a long hold"  <- years_to_call < 2 AND
                                                 price >= call_price - 1.0 point.
            (a callable bond at/above its par call with a near call date is economically
             a short instrument; it must never be modeled as a ladder anchor.)
      SOFT  near call (<2y) but priced below the call OR no recent mark to judge.
      UNVERIFIABLE  EMMA rendered no call schedule (missing != non-callable).
    """
    cusip = cusip.strip().upper()
    cache = _load_cache() if use_cache else {}
    if use_cache and not refresh and cusip in cache:
        return cache[cusip]

    own_session = session is None
    s = session or E._session()
    try:
        rec = _fetch_security(s, cusip)
        result = _assess(rec)
    except Exception as e:  # network/parse failure -> honest UNVERIFIABLE, not a clean pass
        result = {
            "cusip": cusip, "call_status": "UNVERIFIABLE", "call_risk": "UNVERIFIABLE",
            "is_cab": None, "insured": None, "insurer": None,
            "insured_rating": "UNVERIFIABLE", "underlying_rating": "UNVERIFIABLE",
            "hard_flags": [], "soft_flags": [], "notes": [f"fetch error: {e}"],
            "verdict": "UNVERIFIABLE", "as_of": TODAY.isoformat(),
        }
    finally:
        if own_session:
            time.sleep(0.4)

    if use_cache:
        cache[cusip] = result
        _save_cache(cache)
    return result


def screen_book(cusips, refresh: bool = True) -> list[dict]:
    s = E._session()
    out = []
    for c in cusips:
        try:
            out.append(screen_structure(c, session=s, refresh=refresh))
        except Exception as e:
            out.append({"cusip": c, "verdict": "UNVERIFIABLE",
                        "notes": [f"error: {e}"], "call_risk": "UNVERIFIABLE"})
        time.sleep(0.4)
    return out


# ----------------------------------------------------------------------------
def _fmt(v, w, dash="—"):
    s = dash if v is None else str(v)
    return s[:w].ljust(w)


def _print_table(rows: list[dict]) -> None:
    cols = (("cusip", 10), ("next_call", 11), ("yrs_to_call", 11),
            ("call_px", 8), ("is_cab", 7), ("insurer", 14), ("call_risk", 13))
    header = " ".join(name.ljust(w) for name, w in cols)
    print(header)
    print("-" * len(header))
    for r in rows:
        line = " ".join([
            _fmt(r.get("cusip"), 10),
            _fmt(r.get("next_call_date"), 11),
            _fmt(r.get("years_to_call"), 11),
            _fmt(r.get("call_price"), 8),
            _fmt(r.get("is_cab"), 7),
            _fmt(r.get("insurer") or ("INSURED?" if r.get("insured") else "no") , 14),
            _fmt(r.get("call_risk"), 13),
        ])
        print(line)


if __name__ == "__main__":
    BURNED = "926055KH6"            # MUST fire near-par-call (call ~2026-08-01)
    DD_NAMES = ["168520PA6", "861419ZJ1", "925836KH0", "697479CB7"]

    # book CUSIPs (if available)
    book_cusips = []
    if BOOK.exists():
        try:
            book_cusips = [h["cusip"] for h in json.loads(BOOK.read_text())["holdings"]]
        except Exception:
            book_cusips = []

    # union: burned name + 4 DD names + book, de-duped, burned first for visibility
    seen, order = set(), []
    for c in [BURNED] + DD_NAMES + book_cusips:
        cu = c.strip().upper()
        if cu not in seen:
            seen.add(cu); order.append(cu)

    print(f"=== structure_screen  (cutoff/today = {TODAY.isoformat()}) ===")
    print(f"screening {len(order)} CUSIPs: burned={BURNED}, "
          f"{len(DD_NAMES)} DD names, {len(book_cusips)} book names\n")

    results = screen_book(order, refresh=True)
    by = {r["cusip"]: r for r in results}

    _print_table(results)

    # ---- explicit validation on the burned CUSIP ----
    b = by.get(BURNED, {})
    print(f"\n=== VALIDATION: {BURNED} (must FLAG near-par-call) ===")
    print(f"  security : {b.get('security_description')}")
    print(f"  callable : {b.get('callable')}   call_status: {b.get('call_status')}")
    print(f"  next_call: {b.get('next_call_date')}  call_price: {b.get('call_price')}  "
          f"years_to_call: {b.get('years_to_call')}")
    print(f"  price    : {b.get('price')} (trade {b.get('trade_date')})")
    print(f"  call_risk: {b.get('call_risk')}   verdict: {b.get('verdict')}")
    print(f"  insured  : {b.get('insured')}  insurer: {b.get('insurer')}  "
          f"underlying: {b.get('underlying_rating')}")
    for f in b.get("hard_flags", []):
        print(f"  HARD FLAG -> {f}")
    fired = (b.get("call_risk") == "HARD"
             and b.get("next_call_date") == "08/01/2026"
             and any("near-par-call" in f for f in b.get("hard_flags", [])))
    print(f"\n  >>> 926055KH6 near-par-call HARD FLAG: "
          f"{'FIRED ✓' if fired else 'DID NOT FIRE ✗'}")

    # ---- the other 4 DD names: call dates + insurance ----
    print(f"\n=== DD NAMES: call dates + insurance ===")
    for c in DD_NAMES:
        r = by.get(c, {})
        print(f"  {c}: call {r.get('next_call_date')} @ {r.get('call_price')} "
              f"({r.get('years_to_call')}y, risk={r.get('call_risk')}); "
              f"insured={r.get('insured')} insurer={r.get('insurer')}; "
              f"cab={r.get('is_cab')}")

    # ---- book roll-up ----
    flagged = [r for r in results if r.get("verdict") == "FLAG"]
    print(f"\n=== ROLL-UP ===")
    print(f"  total screened : {len(results)}")
    print(f"  HARD FLAG       : {len(flagged)} -> "
          f"{[r['cusip'] for r in flagged]}")
    print(f"  CABs            : {[r['cusip'] for r in results if r.get('is_cab')]}")
    print(f"  insured wraps   : {[r['cusip'] for r in results if r.get('insured')]}")
    print(f"  call UNVERIFIABLE: {[r['cusip'] for r in results if r.get('call_status') == 'UNVERIFIABLE']}")
    print(f"\ncache -> {CACHE}")
