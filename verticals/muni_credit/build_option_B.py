"""Option B — disciplined higher-yield CA muni ETF, ON-THESIS.

Bumps yield over the AA Option A by going DOWN in rating/liquidity but NOT in true credit quality:
scan the INSULATED sectors (school/CC GO, water/wastewater, electric/utility revenue) for their
higher-yielding names, then EMMA-verify each is genuinely an insulated GO / essential-service
revenue credit — REJECTING any COP, lease, CFD/Mello-Roos, or tax-increment bond masquerading under
a school/water issuer name (the R/f/M "clean" gate). Yield pickup comes only from obscurity /
illiquidity / discount within verified-safe credits, never from buying risk.

Requires TWS running with the API enabled (port 7496). EMMA does the per-CUSIP verification.
Run:  python3 build_option_B.py
Output: muni_etf_option_B_highyield.json (+ a printed A-vs-B comparison).
"""
import json, datetime, time, re, logging
logging.getLogger('ib_insync').setLevel(logging.CRITICAL)
import emma_scraper as E, channel_scoring_v2 as C, liquidity_gate as LG
from ib_insync import IB, ScannerSubscription, TagValue

SETTLE = datetime.date(2026, 6, 10)


def ytmf(px, cp, mat):
    try: y, m, d = [int(x) for x in mat.split("-")]
    except Exception: return None
    T = (datetime.date(y, m, d) - SETTLE).days / 365.25
    if T <= 0 or not px or px <= 0: return None
    n = max(1, round(T * 2)); c = cp / 2.0; lo, hi = -0.05, 0.40
    for _ in range(70):
        rr = (lo + hi) / 2; per = rr / 2
        pv = sum(c / (1 + per) ** k for k in range(1, n + 1)) + 100 / (1 + per) ** n
        lo, hi = (rr, hi) if pv > px else (lo, rr)
    return round((lo + hi) / 2, 4)


DA = re.compile(r"\s(\d+\.?\d*)\s+(\d{1,2}/\d{1,2}/\d{2,4})")
def parse(s):
    m = DA.search(s or "")
    if not m: return None, None
    cp = float(m.group(1)); mm, dd, yy = m.group(2).split("/"); yy = int(yy)
    return cp, f"{(yy if yy > 1900 else 2000 + yy):04d}-{int(mm):02d}-{int(dd):02d}"


def sectype(up):
    if "JUDGMENT OBLIGATION" in up: return "JOB"            # GF judgment bond, NOT ad-valorem GO
    if "LIMITED OBLIGATION" in up: return "LTD-OBL"         # not the unlimited ad-valorem pledge
    if any(x in up for x in ("CERTIFICATES OF PARTICIPATION", "CTFS OF PARTN", "COPS ")): return "COP"
    if any(x in up for x in ("COMMUNITY FACILITIES DIST", "SPECIAL TAX", "MELLO-ROOS", "MELLO ROOS")): return "CFD"
    if any(x in up for x in ("TAX ALLOCATION", "TAX INCREMENT", "SUCCESSOR AGENCY", "REDEVELOPMENT")): return "TAB"
    if "LEASE REVENUE" in up: return "LEASE"
    if "LIMITED PROJECT" in up: return "LPRB"
    if "WASTEWATER" in up or "SEWER" in up or ("WATER" in up and "REVENUE" in up): return "WATER-REV"
    if ("ELECTRIC" in up or "POWER" in up) and \
       any(x in up for x in ("REVENUE", "REV ", "ELECTRIC SYSTEM", "ELEC SYS", "POWER PROJECT",
                             "PUBLIC POWER", "PUB PWR")): return "ELEC-REV"
    if any(x in up for x in ("SCH DIST", "SCHOOL DIST", "ELEM SCH", "HIGH SCH", "UNIF SCH",
                             "CMNTY COLLEGE", "COMMUNITY COLLEGE", "COLLEGE DIST")) and \
       any(x in up for x in ("GENERAL OBLIGATION", "UNLIMITED", "UNLTD", " GO ", "(GO)")): return "SCHOOL-GO"
    return "OTHER"


INCLUDE = {"SCHOOL-GO", "WATER-REV", "ELEC-REV"}
MAP = {"SCHOOL-GO": ("school_go_av", "school_go_sb222", "CA school/CC district GO"),
       "WATER-REV": ("water_revenue", "water", "essential-service water/wastewater revenue"),
       "ELEC-REV": ("water_revenue", "water", "essential-service electric/utility revenue")}


def verify(cu, s):
    url = E.BASE + "/Security/Details/" + cu
    t = s.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text
    if "yesButton" in t:
        s.post(E.BASE + "/Disclaimer.aspx",
               data={"__VIEWSTATE": E._hidden("__VIEWSTATE", t),
                     "__VIEWSTATEGENERATOR": E._hidden("__VIEWSTATEGENERATOR", t),
                     "__EVENTVALIDATION": E._hidden("__EVENTVALIDATION", t),
                     "ctl00$mainContentArea$disclaimerContent$yesButton": "Accept"},
               headers={"Content-Type": "application/x-www-form-urlencoded", "Origin": E.BASE, "Referer": url},
               timeout=40)
        t = s.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text
    # block/rate-limit detection: a blocked fetch returns a short 403/"Request Rejected" page; do NOT
    # let it fall through to sectype()=OTHER (a silent false reject). Raise so callers can back off.
    if "403 Forbidden" in t or "Request Rejected" in t or "Access Denied" in t or len(t) < 1200:
        raise RuntimeError("emma_blocked")
    up = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).upper()
    # tax-status gate: a federally TAXABLE muni gets NO x2.01 gross-up — the after-tax ranking
    # would otherwise select taxable high-coupon bonds on a fictitious tax benefit (caught
    # 2026-06-10: judgment-obligation + taxable-limited-obligation bonds masquerading as
    # school GOs at "10%+ TEY"). EMMA states it both as a field and in the issue title.
    taxable = bool(re.search(r"TAX STATUS\s*:\s*TAXABLE", up) or "FEDERALLY TAXABLE" in up
                   or re.search(r"\(TAXABLE\)", up) or " TAXABLE LIMITED" in up
                   or " TAXABLE GENERAL" in up)
    ytw = tdate = pxv = None
    m = re.search(r"var tradeData = (\{.*?\});", t, re.S)
    if m:
        try: rows = json.loads(m.group(1)).get("data", [])
        except Exception: rows = []
        pick = [r for r in rows if r.get("TT") == "S"] or rows
        if pick:
            r0 = pick[0]; ytw = r0.get("YX"); pxv = r0.get("PX"); tdate = (r0.get("TD") or "")[:10]
    return sectype(up), (ytw / 100.0 if ytw is not None else None), tdate, pxv, taxable


def insul(pk): p = C.PROFILES[pk]; return round(100 * (1 - sum(C.CH_W[c] * p.get(c, 0) for c in C.CH_W)), 1)


def yrs_to_mat(mat):
    y, m, d = [int(x) for x in mat.split("-")]
    return (datetime.date(y, m, d) - SETTLE).days / 365.25


def tey_aftertax(px, cp, ytw, mat):
    """De-minimis-aware after-tax TEY (CA top combined bracket x2.01). Below the de-minimis
    threshold (100 - 0.25*yrs) the discount accretion is taxed as ORDINARY income, so only the
    coupon-yield component gets the muni gross-up. THIS, not gross YTW, is the selection metric —
    ranking on YTW mechanically prefers deep discounts whose tax drag eats the apparent pickup."""
    thr = 100 - 0.25 * yrs_to_mat(mat)
    curr = cp / px
    if px < thr:
        return round(curr * 2.01 + max(0.0, ytw - curr) * 1.0, 4), True
    return round(ytw * 2.01, 4), False


def main():
    ib = IB(); ib.connect("127.0.0.1", 7496, clientId=91, timeout=20, readonly=True)
    def scan(kw):
        sub = ScannerSubscription(instrument="BOND.MUNI", locationCode="BOND.MUNI.US",
                                  scanCode="HIGH_BOND_ASK_YIELD_ALL", numberOfRows=50)
        f = [TagValue("couponRateAbove", "3"), TagValue("couponRateBelow", "6"),
             TagValue("maturityDateAbove", "20350101"), TagValue("maturityDateBelow", "20451231"),
             TagValue("bondUSStateLike", "CA"), TagValue("bondIssuerLike", kw)]
        return [sd.contractDetails.contract for sd in ib.reqScannerData(sub, [], f) if sd.contractDetails]
    seen = {}
    for kw in ["SCH DIST", "ELEM", "HIGH SCH", "CMNTY", "WATER", "ELECTRIC"]:
        dets = []
        for c in scan(kw):
            r = ib.reqContractDetails(c)
            if r: dets.append(r[0])
        cs = [d.contract for d in dets]; px = {}
        for i in range(0, len(cs), 90):
            for tk in ib.reqTickers(*cs[i:i + 90]):
                v = tk.close; px[tk.contract.conId] = float(v) if v is not None and v == v else None
            ib.sleep(0.3)
        for d in dets:
            cu = getattr(d, 'cusip', None); cp, mat = parse(getattr(d, 'descAppend', ''))
            if cu and cp and mat and cu not in seen:
                seen[cu] = {"cusip": cu, "coupon": cp, "maturity": mat, "close": px.get(d.contract.conId)}
    ib.disconnect()

    cands = [v for v in seen.values() if v.get("close")]
    byyr = {}
    for b in cands: byyr.setdefault(b["maturity"][:4], []).append(b)
    shortlist = []
    for y, l in byyr.items():
        # de-skewed candidate pool: lowest-price (discount/high-YTW) AND high-coupon-near-par
        # (premium, de-minimis-safe) — lowest-price-only pre-selects the tax-drag bonds
        picks = sorted(l, key=lambda r: r["close"])[:6]
        for b in sorted(l, key=lambda r: (-r["coupon"], abs(r["close"] - 102))):
            if b not in picks: picks.append(b)
            if len(picks) >= 12: break
        shortlist += picks
    print(f"scanned {len(cands)} insulated candidates; EMMA-verifying {len(shortlist)}…", flush=True)

    s = E._session(); kept = []
    for b in shortlist:
        try: st, ytw, td, pxv, taxable = verify(b["cusip"], s)
        except Exception: st, ytw, td, pxv, taxable = "ERR", None, None, None, False
        b.update(sectype=st, ytw=ytw, trade_date=td, emma_px=pxv or b["close"])
        if taxable:
            print(f"  drop {b['cusip']} FEDERALLY TAXABLE (no gross-up; not a tax-exempt sleeve name)", flush=True)
            time.sleep(0.4); continue
        if st in INCLUDE and ytw and (td or "0") > "2025-01" and (pxv or b["close"]) > 72 and ytw < 0.065:
            # execution gate: only keep names that actually trade two-sided & recently (no paper blocks)
            lm = None
            for attempt in range(2):
                try:
                    lm = LG.tape_metrics(b["cusip"], s); break
                except Exception:
                    time.sleep(8)                 # EMMA throttling — back off once, then skip
            if lm is None:
                print(f"  drop {b['cusip']} EMMA-unreachable (gate could not run; not kept unverified)", flush=True)
                time.sleep(0.4); continue
            ok, why = LG.passes(lm)
            if not ok:
                print(f"  drop {b['cusip']} illiquid: {';'.join(why)}", flush=True); time.sleep(0.4); continue
            b["liq"] = {k: lm.get(k) for k in ('n365','days_since_trade','two_sided_days','px_spread','y_spread_bps','med_block','max_block')}
            b["ytm"] = ytmf(b["emma_px"], b["coupon"], b["maturity"]); kept.append(b)
        time.sleep(0.4)
    print(f"verified-insulated-clean & tradeable: {len(kept)} of {len(shortlist)}", flush=True)

    for b in kept:
        pk, ck, lbl = MAP[b["sectype"]]; b["security"] = lbl
        b["insul"] = insul(pk); b["credit"] = C.CREDIT[ck][0]; b["tey_ytw"] = round(b["ytw"] * 2.01, 4)
        b["tey_ytw_aftertax"], b["demin_breach"] = tey_aftertax(b["emma_px"], b["coupon"], b["ytw"], b["maturity"])
    AT = lambda r: -(r["tey_ytw_aftertax"])      # selection metric: AFTER-TAX TEY, not gross YTW
    byyr = {}
    for b in kept: byyr.setdefault(b["maturity"][:4], []).append(b)
    basket = []
    for y in sorted(byyr):
        for b in sorted(byyr[y], key=AT):
            if b["cusip"][:6] in {x["cusip"][:6] for x in basket}: continue
            basket.append(b); break
    extra = sorted([b for b in kept if b not in basket and b["cusip"][:6] not in {x["cusip"][:6] for x in basket}],
                   key=AT)
    basket += extra[:24 - len(basket)]

    TARGET, LOT = 1_000_000, 5_000
    base = (TARGET // max(1, len(basket)) // LOT) * LOT
    for b in basket: b["par"] = base
    for b in sorted(basket, key=AT)[:(TARGET - base * len(basket)) // LOT]: b["par"] += LOT
    def pw(k): n = sum(b["par"] * b[k] for b in basket if b.get(k) is not None); return n / sum(b["par"] for b in basket)
    from collections import Counter
    summ = {"n": len(basket), "total_par": sum(b["par"] for b in basket),
            "par_weighted_ytw_pct": round(pw("ytw") * 100, 2), "par_weighted_tey_gross_pct": round(pw("tey_ytw") * 100, 2),
            "par_weighted_tey_aftertax_pct": round(pw("tey_ytw_aftertax") * 100, 2),
            "demin_breaches": sum(1 for b in basket if b.get("demin_breach")),
            "par_weighted_insulation": round(pw("insul")), "par_weighted_credit": round(pw("credit")),
            "sector_mix": dict(Counter(b["sectype"] for b in basket)),
            "ladder": f"{min(b['maturity'] for b in basket)}..{max(b['maturity'] for b in basket)}",
            "selection_metric": "after-tax TEY (de-minimis aware)",
            "screen": "CA insulated GO/essential-rev, EMMA-verified clean, higher-yield"}
    json.dump({"basket_summary": summ, "barbell": basket}, open("muni_etf_option_B_highyield.json", "w"), indent=1, default=str)
    print(f"\nOPTION B — {summ['n']} bonds, ${summ['total_par']:,}  [selected on AFTER-TAX TEY]")
    print(f"  YTW {summ['par_weighted_ytw_pct']}% | TEY gross {summ['par_weighted_tey_gross_pct']}% | "
          f"TEY after-tax {summ['par_weighted_tey_aftertax_pct']}% | demin breaches {summ['demin_breaches']}/{summ['n']} | "
          f"insul {summ['par_weighted_insulation']} | credit {summ['par_weighted_credit']}")
    print(f"  sectors {summ['sector_mix']} | ladder {summ['ladder']}")
    for b in sorted(basket, key=lambda x: x['maturity']):
        print(f"    {b['sectype']:9} {b['cusip']} {b['coupon']}% {b['maturity'][:7]} px {b['emma_px']:.1f} "
              f"YTW {b['ytw']*100:.2f}% TEYat {b['tey_ytw_aftertax']*100:.2f}%{' DM' if b['demin_breach'] else '   '} last {b['trade_date']}")


if __name__ == "__main__":
    main()
