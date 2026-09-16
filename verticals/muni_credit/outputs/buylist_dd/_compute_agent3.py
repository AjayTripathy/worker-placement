import json, re, datetime
OUT = "/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/buylist_dd"
SETTLE = datetime.date(2026, 6, 10)

# from buy list
LIST = {
 "95330PHH1": dict(coupon=4.0, mat="2041-08-01", last_print_px=98.932, ytw=0.04095, tey=0.0823),
 "032591TU3": dict(coupon=3.0, mat="2041-08-01", last_print_px=83.565, ytw=0.04505, tey=0.0813),
 "17132CDL9": dict(coupon=4.0, mat="2041-08-01", last_print_px=99.619, ytw=0.04033, tey=0.0811),
 "358233ED2": dict(coupon=3.0, mat="2041-08-01", last_print_px=83.954, ytw=0.0447,  tey=0.0808),
 "777387AH4": dict(coupon=4.0, mat="2042-08-01", last_print_px=97.814, ytw=0.04186, tey=0.0841),
 "607735CA3": dict(coupon=3.0, mat="2043-08-01", last_print_px=81.404, ytw=0.04574, tey=0.083),
}

def yrs(mat):
    y,m,d=[int(x) for x in mat.split("-")]
    return (datetime.date(y,m,d)-SETTLE).days/365.25

def tey_aftertax(px, cp, ytw, mat):
    thr = 100 - 0.25*yrs(mat)
    curr = cp/px
    if px < thr:
        return round(curr*2.01 + max(0.0, ytw-curr)*1.0, 4), True, round(thr,3)
    return round(ytw*2.01,4), False, round(thr,3)

for cu,L in LIST.items():
    t=open(f"{OUT}/raw_{cu}.html").read()
    m=re.search(r"var tradeData = (\{.*?\});", t, re.S)
    rows=json.loads(m.group(1)).get("data",[]) if m else []
    # latest by date overall
    rows_sorted=sorted(rows, key=lambda r:(r.get("TD") or ""), reverse=True)
    latest=rows_sorted[0]
    # latest customer SALE (S) print = what we'd lift; also overall latest
    sales=[r for r in rows if r.get("TT")=="S"]
    sales_sorted=sorted(sales, key=lambda r:(r.get("TD") or ""), reverse=True)
    s0=sales_sorted[0] if sales_sorted else None
    print("="*70); print(cu)
    print(f"  list last_print_px={L['last_print_px']}  ytw={L['ytw']}  tey={L['tey']}")
    print(f"  EMMA latest ANY:  TD={latest.get('TD','')[:10]} TT={latest.get('TT')} PX={latest.get('PX')} YX={latest.get('YX')}")
    if s0: print(f"  EMMA latest SALE: TD={s0.get('TD','')[:10]} PX={s0.get('PX')} YX={s0.get('YX')}")
    # tape moved vs list last_print
    lpx=latest.get("PX")
    moved=round(float(lpx)-L['last_print_px'],3) if lpx else None
    days_stale=(SETTLE-datetime.date.fromisoformat(latest.get("TD","")[:10])).days
    print(f"  tape_moved_pt(latest_any - list)= {moved}   days_since_latest_trade={days_stale}")
    # recompute TEY using EMMA latest sale px+ytw (best executable mark)
    use = s0 or latest
    px=float(use.get("PX")); yx=use.get("YX")/100.0
    tey,breach,thr=tey_aftertax(px, L['coupon'], yx, L['mat'])
    div=round(tey-L['tey'],4)
    print(f"  demin_thr={thr}  px<thr={px<thr}  recomputed_tey={tey} (at px={px}, ytw={yx:.4f})  div_vs_list={div:+.4f}pp")
