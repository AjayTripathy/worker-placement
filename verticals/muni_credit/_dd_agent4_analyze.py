import json, datetime, re
SETTLE = datetime.date(2026,6,10)
raw = json.load(open("outputs/buylist_dd/_agent4_raw.json"))
LIST = {o["cusip"]: o for o in json.load(open("outputs/BUY_LIST_20260610.json"))["orders"]}

# re-load full trade arrays from the saved page text
import sys
def load_trades(cu):
    t = open(f"outputs/buylist_dd/_raw_{cu}.txt").read()
    return None  # tape already in raw json head; need full -> re-parse below
# Actually re-parse full tape from the original HTML we didn't save; reuse trades_head won't be enough.
# We saved flattened text (tags stripped) so tradeData JSON is gone. Re-fetch full arrays quickly cached:
print("note: using full tape from re-fetch cache if present")

def yrs(mat):
    y,m,d=[int(x) for x in mat.split("-")]; return (datetime.date(y,m,d)-SETTLE).days/365.25
def tey_aftertax(px,cp,ytw,mat):
    thr=100-0.25*yrs(mat); curr=cp/px
    if px<thr: return round(curr*2.01+max(0.0,ytw-curr)*1.0,4), True, round(thr,3)
    return round(ytw*2.01,4), False, round(thr,3)

CALLS={"870462TJ7":"2028-08-01@100","13049WAX3":"2026-07-10@100","547541LJ9":"2027-08-01@100",
       "168520PA6":"2027-08-01@100","223093TK1":"2026-08-01@100","079113DY9":"2026-08-01@100"}
for cu in raw:
    o=LIST[cu]; cp=o["coupon"]; mat=o["maturity"]
    ytw_list=o["ytw_at_mark"]; px_list=o["last_print_px"]; tey_list=o["tey_aftertax_at_mark"]
    tey, demin, thr = tey_aftertax(px_list, cp, ytw_list, mat)
    print(f"\n=== {cu}  {o.get('issuer') or o.get('security')} ===")
    print(f"  coupon={cp} mat={mat} call={CALLS[cu]}  ytm_yrs={yrs(mat):.2f} deminthr={thr}")
    print(f"  list px={px_list} ytw={ytw_list:.4f} tey_list={tey_list} demin_list={o['demin_breach']}")
    print(f"  recomputed tey={tey} demin={demin}  DIV={round((tey-tey_list)*100,3)}pp")
