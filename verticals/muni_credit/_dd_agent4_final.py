import json, datetime
SETTLE=datetime.date(2026,6,10)
tapes=json.load(open("outputs/buylist_dd/_agent4_tapes.json"))
LIST={o["cusip"]:o for o in json.load(open("outputs/BUY_LIST_20260610.json"))["orders"]}
def yrs(mat):
    y,m,d=[int(x) for x in mat.split("-")]; return (datetime.date(y,m,d)-SETTLE).days/365.25
def tey_aftertax(px,cp,ytw,mat):
    thr=100-0.25*yrs(mat); curr=cp/px
    if px<thr: return round(curr*2.01+max(0.0,ytw-curr)*1.0,4),True,round(thr,3)
    return round(ytw*2.01,4),False,round(thr,3)
def dparse(s): return datetime.date.fromisoformat(s[:10])
CALLS={"870462TJ7":"2028-08-01@100","13049WAX3":"2026-07-10@100","547541LJ9":"2027-08-01@100",
       "168520PA6":"2027-08-01@100","223093TK1":"2026-08-01@100","079113DY9":"2026-08-01@100"}
TTNAME={"P":"customer-buy(dealer-sold-to-cust)","S":"customer-sell(dealer-bought)","D":"inter-dealer"}
for cu in ["870462TJ7","13049WAX3","547541LJ9","168520PA6","223093TK1","079113DY9"]:
    o=LIST[cu]; rows=tapes[cu]; cp=o["coupon"]; mat=o["maturity"]
    # rows are most-recent-first; latest trade
    latest=rows[0]
    ldate=dparse(latest["TD"]); lpx=latest["PX"]; lyx=latest["YX"]
    days_since=(SETTLE-ldate).days
    # two-sided recency: most recent customer-buy (P) and customer-sell (S) dates
    pdt=next((dparse(r["TD"]) for r in rows if r.get("TT")=="P"),None)
    sdt=next((dparse(r["TD"]) for r in rows if r.get("TT")=="S"),None)
    # 30-day window stats
    win=[r for r in rows if (SETTLE-dparse(r["TD"])).days<=30]
    sizes=[r.get("TA") for r in win if r.get("TA")]
    pxs=[r["PX"] for r in win if r.get("PX")]
    tey,demin,thr=tey_aftertax(o["last_print_px"],cp,o["ytw_at_mark"],mat)
    div=round((tey-o["tey_aftertax_at_mark"])*100,3)
    moved=round(lpx-o["last_print_px"],3)
    print(f"\n=== {cu}  {o.get('issuer') or o.get('security')} ({o['security']}) ===")
    print(f"  call={CALLS[cu]} coupon={cp} mat={mat}")
    print(f"  LATEST tape: {ldate} px={lpx} ytw%={lyx} type={TTNAME.get(latest['TT'])} size={latest.get('TA')}")
    print(f"  list last_print_px={o['last_print_px']} list last_trade={o.get('last_trade')}  -> tape_moved={moved}pt days_since={days_since}")
    print(f"  two-sided: last cust-BUY(P)={pdt}  last cust-SELL(S)={sdt}")
    print(f"  30d window: n={len(win)} px[{min(pxs) if pxs else '-'},{max(pxs) if pxs else '-'}] sizes[min={min(sizes) if sizes else '-'},max={max(sizes) if sizes else '-'}]")
    print(f"  TEY recompute: list_tey={o['tey_aftertax_at_mark']} recomputed={tey} DIV={div}pp  demin_list={o['demin_breach']} demin_recomp={demin} thr={thr}")
    print(f"  limit_px={o['limit_px']} vs latest tape px={lpx}  (limit {'ABOVE' if o['limit_px']>lpx else 'below'} last print)")
