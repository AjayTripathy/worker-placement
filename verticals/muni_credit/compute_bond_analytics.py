"""Pull coupon / maturity / dated-date / call schedule + latest trade price for each
CUSIP in the CA Muni Honesty Basket from EMMA, then compute per-bond YTM, yield-to-worst,
and modified duration (to worst), plus equal-weight portfolio aggregates.

Source: EMMA /Security/Details/<cusip> (post-disclaimer) — authoritative free MSRB data.
Bond math: street convention, semiannual coupons, 30/360, fractional first period.
Mark = most-recent reported trade price (prefer sale-to-customer); valued as-of SETTLE.
YTW = min(yield-to-maturity, yield-to-next-call@call-price). Duration computed to worst.
"""
import sys, re, json, time
from datetime import date
sys.path.insert(0, "/Users/ajay/exalted/signalos/verticals/muni_credit")
import emma_scraper as E

SETTLE = date(2026, 6, 5)            # common valuation/settlement date
HOLD = "/Users/ajay/exalted/signalos/verticals/muni_credit/data/etf_v2_holdings.json"


# ---------- EMMA fetch ----------
def fetch_security(cusip, s):
    url = E.BASE + "/Security/Details/" + cusip
    t = s.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text
    if "yesButton" in t:
        s.post(E.BASE + "/Disclaimer.aspx",
               data={"__VIEWSTATE": E._hidden("__VIEWSTATE", t),
                     "__VIEWSTATEGENERATOR": E._hidden("__VIEWSTATEGENERATOR", t),
                     "__EVENTVALIDATION": E._hidden("__EVENTVALIDATION", t),
                     "ctl00$mainContentArea$disclaimerContent$yesButton": "Accept"},
               headers={"Content-Type": "application/x-www-form-urlencoded",
                        "Origin": E.BASE, "Referer": url}, timeout=40)
        t = s.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text

    # labeled descriptive fields sit as plain text between markup -> match on a flattened copy
    flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))

    def grab(pat):
        m = re.search(pat, flat)
        return m.group(1).strip() if m else None

    coupon = grab(r"Coupon:\s*([\d.]+)\s*%")
    mat = grab(r"Maturity Date:\s*(\d{2}/\d{2}/\d{4})")
    dated = grab(r"Dated Date:\s*(\d{2}/\d{2}/\d{4})")
    callable_ind = grab(r"Callable\s*:\s*(\w+)")
    call_date = grab(r"Next Call Date\s*:\s*(\d{2}/\d{2}/\d{4})")
    call_price = grab(r"Next Call Price \(%\)\s*:\s*([\d.]+)")

    px = yx = tdate = ttype = None
    m = re.search(r"var tradeData = (\{.*?\});", t, re.S)
    if m:
        try:
            rows = json.loads(m.group(1)).get("data", [])
        except json.JSONDecodeError:
            rows = []
        # prefer most-recent sale-to-customer; fallback most-recent any
        cust = [r for r in rows if r.get("TT") == "S"]
        pick = (cust or rows)
        if pick:
            r0 = pick[0]              # px, yx and trade-date all from the SAME mark row
            px, yx = r0.get("PX"), r0.get("YX")
            tdate = (r0.get("TD") or "")[:10]
            ttype = r0.get("TT")
    return dict(coupon=float(coupon) if coupon else None,
                maturity=mat, dated=dated, callable=callable_ind,
                call_date=call_date, call_price=float(call_price) if call_price else None,
                price=float(px) if px is not None else None,
                trade_yield=float(yx) if yx is not None else None,
                trade_date=tdate, trade_type=ttype, n_trades=len(rows) if m else 0)


# ---------- bond math (semiannual, 30/360) ----------
def _d(s):
    mm, dd, yy = s.split("/")
    return date(int(yy), int(mm), int(dd))

def _days360(d1, d2):
    dd1 = min(d1.day, 30)
    dd2 = min(d2.day, 30) if dd1 == 30 else d2.day
    return (d2.year - d1.year) * 360 + (d2.month - d1.month) * 30 + (dd2 - dd1)

def _coupon_dates(settle, maturity):
    """Semiannual coupon dates on the maturity day/month, all dates > settle, in order."""
    dates = []
    y = maturity.year
    while date(y, maturity.month, maturity.day) > settle or y >= maturity.year - 60:
        for mo in (maturity.month, (maturity.month + 6 - 1) % 12 + 1):
            try:
                cd = date(y, mo, maturity.day)
            except ValueError:
                cd = date(y, mo, 28)
            dates.append(cd)
        if y <= maturity.year - 60:
            break
        y -= 1
    dates = sorted(set([d for d in dates if d > settle and d <= maturity]))
    return dates

def _price_from_yield(settle, maturity, coupon, y, redeem=100.0, redeem_date=None):
    """Dirty price per 100 given annual yield y (decimal). Returns (dirty, accrued, periods)."""
    end = redeem_date or maturity
    cdates = [d for d in _coupon_dates(settle, maturity) if d <= end]
    if not cdates:
        cdates = [end]
    c = coupon / 2.0
    nxt = cdates[0]
    prev = _prev_coupon(nxt, maturity)
    dip = _days360(prev, nxt) or 180
    dsc = _days360(settle, nxt)
    w = dsc / dip                       # fraction of current period remaining
    accrued = c * (1 - w)
    yp = y / 2.0
    dirty = 0.0
    periods = []
    for k, cd in enumerate(cdates):
        exp = w + k
        cf = c
        if cd == end:                   # redemption period: add principal/call price
            cf = c + redeem
        dirty += cf / (1 + yp) ** exp
        periods.append((exp / 2.0, cf / (1 + yp) ** exp))
    return dirty, accrued, periods

def _prev_coupon(nxt, maturity):
    mo = nxt.month - 6
    y = nxt.year
    if mo <= 0:
        mo += 12; y -= 1
    try:
        return date(y, mo, maturity.day)
    except ValueError:
        return date(y, mo, 28)

def solve_yield(clean, settle, maturity, coupon, redeem=100.0, redeem_date=None):
    """Bisection for annual yield matching clean price."""
    lo, hi = -0.05, 0.40
    for _ in range(200):
        mid = (lo + hi) / 2
        dirty, accrued, _ = _price_from_yield(settle, maturity, coupon, mid, redeem, redeem_date)
        if (dirty - accrued) > clean:   # price too high -> raise yield
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def mod_duration(clean, ytw, settle, maturity, coupon, redeem=100.0, redeem_date=None):
    dirty, accrued, periods = _price_from_yield(settle, maturity, coupon, ytw, redeem, redeem_date)
    mac = sum(t * pv for t, pv in periods) / dirty
    return mac / (1 + ytw / 2.0)


def analyze(rec):
    if rec["price"] is None or rec["coupon"] is None or not rec["maturity"]:
        return None
    settle, mat = SETTLE, _d(rec["maturity"])
    clean, cpn = rec["price"], rec["coupon"]
    yrs_mat = _days360(settle, mat) / 360.0

    # --- to-maturity (unambiguous; my engine, validated vs EMMA on discounts) ---
    ytm = solve_yield(clean, settle, mat, cpn)
    dur_mat = mod_duration(clean, ytm, settle, mat, cpn)

    # --- authoritative yield-to-worst = EMMA's reported trade yield (MSRB convention,
    #     captures full call + sinking schedule). My single-next-call YTW is a cross-check. ---
    emma_ytw = rec["trade_yield"] / 100.0 if rec.get("trade_yield") is not None else None

    my_ytw, worst, yrs_worst, dur_worst = ytm, "MATURITY", yrs_mat, dur_mat
    if rec["callable"] == "Yes" and rec["call_date"]:
        cd = _d(rec["call_date"])
        if cd > settle:
            cprice = rec["call_price"] or 100.0
            ytc = solve_yield(clean, settle, mat, cpn, redeem=cprice, redeem_date=cd)
            if ytc < ytm:
                my_ytw, worst = ytc, "CALL " + rec["call_date"]
                yrs_worst = _days360(settle, cd) / 360.0
                dur_worst = mod_duration(clean, ytc, settle, mat, cpn, cprice, cd)

    # guard: a near-term call (<0.5y) priced off a STALE mark gives a meaningless YTW/dur
    stale = rec.get("trade_date", "") < "2025-06-01"
    artifact = worst.startswith("CALL") and yrs_worst < 0.5 and stale
    if artifact:
        my_ytw, worst, yrs_worst, dur_worst = ytm, "MATURITY(stale-call-supressed)", yrs_mat, dur_mat

    # divergence flag between my next-call YTW and EMMA's full-schedule YTW
    div = (emma_ytw is not None and abs(my_ytw - emma_ytw) > 0.005)
    return dict(
        ytm=ytm, dur_to_maturity=dur_mat, years_to_maturity=yrs_mat,
        emma_ytw=emma_ytw, my_ytw=my_ytw, worst=worst,
        years_to_worst=yrs_worst, dur_to_worst=dur_worst,
        ytw_divergence=div, stale_mark=stale)


def main():
    holds = json.load(open(HOLD))["holdings"]
    s = E._session()
    rows = []
    for h in holds:
        cusip = h["cusip"]
        try:
            rec = fetch_security(cusip, s)
        except Exception as e:
            rec = {"error": str(e), "price": None, "coupon": None, "maturity": None}
        rec["slot"] = h["slot"]; rec["cusip"] = cusip
        rec["obligor"] = h.get("obligor_name")
        an = analyze(rec) if "error" not in rec else None
        if an:
            rec.update(an)
        rows.append(rec)
        m = rec.get("maturity") or "?"
        if an:
            flag = " *DIV" if an["ytw_divergence"] else ""
            print(f"{h['slot']:>2} {cusip} cpn={rec.get('coupon'):>5} mat={m} "
                  f"call={rec.get('call_date')}@{rec.get('call_price')} px={rec.get('price')} "
                  f"| YTM={an['ytm']*100:.3f} EMMA-YTW={(an['emma_ytw'] or 0)*100:.3f} "
                  f"durMat={an['dur_to_maturity']:.2f} durWorst={an['dur_to_worst']:.2f} "
                  f"worst={an['worst']}{flag}")
        else:
            print(f"{h['slot']:>2} {cusip} cpn={rec.get('coupon')} mat={m} px={rec.get('price')} | NO ANALYTICS")
        time.sleep(0.4)

    priced = [r for r in rows if r.get("ytm") is not None]
    withmat = [r for r in rows if r.get("coupon") and r.get("maturity")]
    ytw_set = [r for r in priced if r.get("emma_ytw") is not None]
    def avg(xs): return sum(xs) / len(xs) if xs else None
    agg = {
        "n_total": len(rows), "n_priced": len(priced), "n_with_terms": len(withmat),
        "n_ytw_emma": len(ytw_set),
        "avg_coupon_pct": round(avg([r["coupon"] for r in withmat]), 3),
        "wac_note": "equal-weight average coupon",
        # yields
        "avg_ytm_pct": round(avg([r["ytm"] for r in priced]) * 100, 3),
        "ytm_min_pct": round(min(r["ytm"] for r in priced) * 100, 3),
        "ytm_max_pct": round(max(r["ytm"] for r in priced) * 100, 3),
        "avg_ytw_pct": round(avg([r["emma_ytw"] for r in ytw_set]) * 100, 3),
        "ytw_min_pct": round(min(r["emma_ytw"] for r in ytw_set) * 100, 3),
        "ytw_max_pct": round(max(r["emma_ytw"] for r in ytw_set) * 100, 3),
        "ytw_source": "EMMA reported trade yield (MSRB yield-to-worst convention)",
        # call give-up
        "avg_ytm_minus_ytw_bps": round((avg([r["ytm"] for r in ytw_set]) - avg([r["emma_ytw"] for r in ytw_set])) * 10000, 1),
        # duration / maturity
        "avg_mod_duration_to_maturity_yrs": round(avg([r["dur_to_maturity"] for r in priced]), 2),
        "avg_mod_duration_to_worst_yrs": round(avg([r["dur_to_worst"] for r in priced]), 2),
        "dur_mat_min_yrs": round(min(r["dur_to_maturity"] for r in priced), 2),
        "dur_mat_max_yrs": round(max(r["dur_to_maturity"] for r in priced), 2),
        "wam_yrs_to_maturity": round(avg([r["years_to_maturity"] for r in withmat]), 2),
        "wam_min_yrs": round(min(r["years_to_maturity"] for r in priced), 2),
        "wam_max_yrs": round(max(r["years_to_maturity"] for r in priced), 2),
        # structure / data quality
        "n_callable": sum(1 for r in withmat if r.get("callable") == "Yes"),
        "n_stale_mark": sum(1 for r in priced if r.get("stale_mark")),
        "n_ytw_divergence": sum(1 for r in priced if r.get("ytw_divergence")),
        "settle_date": SETTLE.isoformat(),
        "tey_factor": 2.01,
        "avg_ytw_tey_pct": round(avg([r["emma_ytw"] for r in ytw_set]) * 100 * 2.01, 2),
        "avg_ytm_tey_pct": round(avg([r["ytm"] for r in priced]) * 100 * 2.01, 2),
    }
    out = {"settle": SETTLE.isoformat(), "rows": rows, "aggregates": agg}
    p = "/Users/ajay/exalted/signalos/verticals/muni_credit/data/etf_v2_bond_analytics.json"
    json.dump(out, open(p, "w"), indent=1, default=str)
    print("\n=== AGGREGATES ===")
    for k, v in agg.items():
        print(f"  {k}: {v}")
    print("\nsaved ->", p)


if __name__ == "__main__":
    main()
