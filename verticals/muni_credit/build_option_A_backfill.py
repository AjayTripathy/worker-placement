"""Option A backfill — top the execution-clean AA basket back to 24 with fresh LIQUID UC/essential
names. Scans the UC-Regents + essential-revenue universe (A's character), classifies by CUSIP via
channel_scoring_v2, EMMA-verifies the mark, applies the liquidity_gate, and adds the highest-YTW
survivors not already held. Re-sizes to $1M. Requires TWS (port 7496)."""
import json, datetime, time, re, logging
logging.getLogger('ib_insync').setLevel(logging.CRITICAL)
import emma_scraper as E, channel_scoring_v2 as C, liquidity_gate as LG
from ib_insync import IB, ScannerSubscription, TagValue

SETTLE = datetime.date(2026, 6, 9); TARGET, LOT = 1_000_000, 5000
INSULATED = {"uc_grb", "uc_lprb", "school_go_sb222", "water"}

def ytmf(px, cp, mat):
    y, m, d = [int(x) for x in mat.split("-")]
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

def yrs(m): y, mo, dd = [int(x) for x in m.split('-')]; return (datetime.date(y, mo, dd) - SETTLE).days / 365.25
def insul_of(k): p = C.PROFILES[k]; return round(100 * (1 - sum(C.CH_W[c] * p.get(c, 0) for c in C.CH_W)), 1)
def tey_at(px, cp, ytw, mat):
    thr = 100 - 0.25 * yrs(mat); curr = cp / px
    if px < thr: return round(curr * 2.01 + max(0.0, ytw - curr) * 1.0, 4), True
    return round(ytw * 2.01, 4), False

def tax_status_taxable(cusip, s):
    """EMMA tax-status gate: a federally TAXABLE bond gets no x2.01 gross-up and the after-tax
    ranking would actively select it on fictitious yield (caught 2026-06-10: 27/106 of the B scan,
    then 2 UC names — 91412GXY6, 91412GN43 — in A itself; odd 3-decimal coupons are the tell)."""
    url = E.BASE + "/Security/Details/" + cusip
    t = s.get(url, headers={"Referer": E.BASE + "/"}, timeout=40).text
    up = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).upper()
    return bool(re.search(r"TAX STATUS\s*:\s*TAXABLE", up) or "FEDERALLY TAXABLE" in up
                or re.search(r"\(TAXABLE\)", up) or " TAXABLE LIMITED" in up or " TAXABLE GENERAL" in up)


def tape(cusip, s):
    """one EMMA fetch -> (liquidity metrics, latest ytw, latest px, latest date)."""
    m = LG.tape_metrics(cusip, s)
    rows = LG._fetch_trades(cusip, s)
    rows = [r for r in rows if r.get('YX') is not None and r.get('PX')]
    rows.sort(key=lambda r: r['TD'], reverse=True)
    if not rows: return m, None, None, None
    return m, rows[0]['YX'] / 100.0, rows[0]['PX'], rows[0]['TD'][:10]

def main():
    A = json.load(open('muni_etf_option_A_execclean.json')); held = A['barbell']
    have = {b['cusip'] for b in held}
    ib = IB(); ib.connect("127.0.0.1", 7496, clientId=87, timeout=20, readonly=True)
    def scan(kw):
        sub = ScannerSubscription(instrument="BOND.MUNI", locationCode="BOND.MUNI.US",
                                  scanCode="HIGH_BOND_ASK_YIELD_ALL", numberOfRows=50)
        f = [TagValue("couponRateAbove", "3"), TagValue("couponRateBelow", "6"),
             TagValue("maturityDateAbove", "20350101"), TagValue("maturityDateBelow", "20451231"),
             TagValue("bondUSStateLike", "CA"), TagValue("bondIssuerLike", kw)]
        return [sd.contractDetails.contract for sd in ib.reqScannerData(sub, [], f) if sd.contractDetails]
    cand = {}
    for kw in ["REGENTS", "UNIV OF CALIF", "CALIFORNIA UNIV", "UNIVERSITY CALIF", "WATER", "SCH DIST"]:
        for c in scan(kw):
            r = ib.reqContractDetails(c)
            if not r: continue
            cu = getattr(r[0], 'cusip', None); cp, mat = parse(getattr(r[0], 'descAppend', ''))
            if cu and cp and mat and cu not in have and cu not in cand:
                kls = C.classify_cusip(cu)
                if kls and kls[1] in INSULATED:
                    cand[cu] = {"cusip": cu, "coupon": cp, "maturity": mat, "klass": kls}
    ib.disconnect()
    print(f"insulated UC/essential candidates not already held: {len(cand)}", flush=True)

    s = E._session(); adds = []
    for cu, b in cand.items():
        try:
            m, ytw, px, td = tape(cu, s)
        except Exception as e:
            print(f"  skip {cu}: {str(e)[:40]}"); continue
        ok, why = LG.passes(m)
        if not (ok and ytw and px and 72 < px and ytw < 0.065 and (td or '0') > '2025-06'):
            print(f"  drop {cu} {b['klass'][2][:30]}: {'illiq:'+';'.join(why) if not ok else 'mark'}"); continue
        if tax_status_taxable(cu, s):
            print(f"  drop {cu} {b['klass'][2][:30]}: FEDERALLY TAXABLE"); continue
        ai_k, cr_k, lbl = b['klass']
        at, brk = tey_at(px, b['coupon'], ytw, b['maturity'])
        b.update(emma_px=px, ytw=ytw, trade_date=td, ytm=ytmf(px, b['coupon'], b['maturity']),
                 security=lbl, insul=insul_of(ai_k), credit=C.CREDIT[cr_k][0],
                 tey_ytw=round(ytw * 2.01, 4), tey_ytw_aftertax=at, demin_breach=brk,
                 security_credit_key=cr_k,
                 liq={k: m.get(k) for k in ('n365', 'days_since_trade', 'two_sided_days', 'px_spread', 'y_spread_bps', 'med_block', 'max_block')})
        del b['klass']; adds.append(b); time.sleep(0.3)
    adds.sort(key=lambda x: -x['ytw'])
    need = 24 - len(held)
    chosen = adds[:need]
    print(f"qualified liquid adds: {len(adds)}; taking {len(chosen)} to reach 24", flush=True)

    basket = held + chosen
    n = len(basket); base = (TARGET // n // LOT) * LOT
    for b in basket: b['par'] = base
    for b in sorted(basket, key=lambda x: -(x.get('ytw') or 0))[:(TARGET - base * n) // LOT]: b['par'] += LOT
    tot = sum(b['par'] for b in basket)
    def pw(k):
        num = sum(b['par'] * b[k] for b in basket if b.get(k) is not None); den = sum(b['par'] for b in basket if b.get(k) is not None)
        return num / den if den else None
    import statistics as st
    sp = [b['liq']['px_spread'] for b in basket if b.get('liq', {}).get('px_spread') is not None]
    summ = {"n": n, "added": len(chosen), "total_par": tot,
            "par_weighted_ytw_pct": round(pw('ytw') * 100, 2),
            "par_weighted_tey_gross_pct": round(pw('tey_ytw') * 100, 2),
            "par_weighted_tey_aftertax_pct": round(pw('tey_ytw_aftertax') * 100, 2),
            "par_weighted_insulation": round(pw('insul')), "par_weighted_credit": round(pw('credit')),
            "demin_breaches": sum(1 for b in basket if b.get('demin_breach')),
            "median_same_day_spread_pt": round(st.median(sp), 3) if sp else None,
            "median_trades_per_yr": int(st.median([b['liq']['n365'] for b in basket if b.get('liq')])),
            "all_last_trade_within_90d": all(b['liq']['days_since_trade'] <= 90 for b in basket if b.get('liq')),
            "ladder": f"{min(b['maturity'] for b in basket)}..{max(b['maturity'] for b in basket)}",
            "liquidity_floor": LG.FLOOR,
            "note": "execution-clean + backfilled to 24 vs live TWS 2026-06-09; every name two-sided & traded <=90d"}
    json.dump({"basket_summary": summ, "barbell": basket}, open('muni_etf_option_A_execclean.json', 'w'), indent=1, default=str)
    print(f"\nOPTION A (backfilled) — {n} bonds, ${tot:,}")
    print(f"  YTW {summ['par_weighted_ytw_pct']}% | TEY gross {summ['par_weighted_tey_gross_pct']}% | "
          f"TEY after-tax {summ['par_weighted_tey_aftertax_pct']}% | insul {summ['par_weighted_insulation']} | credit {summ['par_weighted_credit']}")
    print(f"  median spread {summ['median_same_day_spread_pt']}pt | median {summ['median_trades_per_yr']} trades/yr | all<=90d {summ['all_last_trade_within_90d']}")
    for b in chosen:
        print(f"  + {b['cusip']} {b['coupon']}% {b['maturity'][:7]} px {b['emma_px']:.1f} YTW {b['ytw']*100:.2f}% "
              f"insul {b['insul']} cr {b['credit']} n365 {b['liq']['n365']} -- {b['security'][:34]}")

if __name__ == "__main__":
    main()
