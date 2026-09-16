import re, json, time, datetime, os
import _dd_agent1 as D
import emma_scraper as E

SETTLE = datetime.date(2026, 6, 10)
OUT = "outputs/buylist_dd/agent1.json"
os.makedirs("outputs/buylist_dd", exist_ok=True)

BL = {o['cusip']: o for o in json.load(open("outputs/BUY_LIST_20260610.json"))['orders']}
CUSIPS = ["91412G2F1", "926055KH6", "91412HJC8", "050002AW4", "58661PDN9", "817409H32"]

# AB-1200 flagged LEAs (negative/qualified, FY24-25 First+Second interim)
FLAGGED = set()
for f in ['cde_first2425.html', 'cde_second2425.html']:
    t = open('data/issuer_credit/' + f).read()
    for r in re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S):
        cells = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', c)).strip()
                 for c in re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)]
        if len(cells) >= 2:
            FLAGGED.add(cells[1].lower())

def yrs(mat):
    y, m, d = [int(x) for x in mat.split("-")]
    return (datetime.date(y, m, d) - SETTLE).days / 365.25

def recompute_tey(px, cp, ytw, mat):
    thr = 100 - 0.25 * yrs(mat)
    curr = cp / px
    if px < thr:
        return round(curr * 2.01 + max(0.0, ytw - curr) * 1.0, 4), True, thr
    return round(ytw * 2.01, 4), False, thr

def latest_trades(rows):
    # rows have TD, TT (S=cust buy, P=cust sell, D=dealer), PX, YX
    def dt(r):
        return (r.get('TD') or '')[:10]
    srt = sorted(rows, key=dt, reverse=True)
    return srt

s = E._session()
results = []

for cu in CUSIPS:
    bl = BL[cu]
    print(f"\n=== {cu} ({bl.get('security')}) ===", flush=True)
    rec = {"cusip": cu}
    try:
        html = D.fetch(cu, s)
        p = D.parse(html)
    except Exception as e:
        rec.update(verdict="REJECT", basis=f"EMMA unreachable: {e}",
                   tax_status="UNKNOWN", pledge_confirmed=False, callable=None, next_call=None,
                   live_last_trade_px=None, live_last_trade_date=None, tape_moved_pt=None,
                   recomputed_tey_at=None, tey_divergence_pp=None, issuer_resolved=None,
                   ab1200="UNVERIFIED", notes="fetch failed after retries")
        results.append(rec)
        json.dump(results, open(OUT, "w"), indent=1)
        time.sleep(1); continue

    fg = D.figi(cu)
    fg_name = None
    try:
        fg_name = fg[0]['data'][0]['name']
        fg_ticker = fg[0]['data'][0]['ticker']
    except Exception:
        fg_ticker = None

    title = p['security_desc']
    up = p['up_snippet']

    # tax
    taxable = p['taxable']
    amt = p['amt']
    tax_status = "TAXABLE" if taxable else ("AMT" if amt else "TAX-EXEMPT")

    # trades
    rows = latest_trades(p['trades'])
    lt = rows[0] if rows else {}
    live_px = lt.get('PX')
    live_date = (lt.get('TD') or '')[:10] if lt else None
    live_yx = lt.get('YX')
    has_S = any(r.get('TT') == 'S' for r in rows[:30])
    has_P = any(r.get('TT') == 'P' for r in rows[:30])

    mark = bl.get('last_print_px')
    tape_moved = round(float(live_px) - float(mark), 3) if (live_px and mark) else None

    # recompute tey using LIVE ytw if present else mark ytw
    ytw_use = (live_yx / 100.0) if live_yx is not None else bl.get('ytw_at_mark')
    px_use = float(live_px) if live_px else float(mark)
    tey, demin, thr = recompute_tey(px_use, bl['coupon'], ytw_use, bl['maturity'])
    list_tey = bl.get('tey_aftertax_at_mark')
    tey_div = round((tey - list_tey) * 100, 3) if list_tey is not None else None  # pp

    rec.update(
        tax_status=tax_status,
        callable=p['callable'],
        next_call=p['next_call'],
        live_last_trade_px=live_px,
        live_last_trade_date=live_date,
        tape_moved_pt=tape_moved,
        recomputed_tey_at=round(tey * 100, 3),  # in pct
        tey_divergence_pp=tey_div,
        issuer_resolved=fg_name,
    )

    # ---- pledge confirmation (per buy-list claim) ----
    claim = bl.get('security', '').lower()
    pledge_ok = True; pledge_note = ""
    badmask = any(k in up for k in [" CERTIFICATE OF PARTICIPATION", " CERTIFICATES OF PARTICIPATION",
                                    " LEASE REVENUE", "JUDGMENT OBLIGATION", "MELLO-ROOS", "MELLO ROOS",
                                    "TAX ALLOCATION", "COMMUNITY FACILITIES DISTRICT", "SPECIAL TAX",
                                    "LIMITED OBLIGATION"])
    if "uc regents limited project" in claim or "limited project" in claim:
        pledge_ok = "LIMITED PROJECT REVENUE" in up
        pledge_note = "UC Limited Project Revenue" if pledge_ok else "NOT UC LtdProj"
    elif "grb" in claim or "general revenue" in claim:
        pledge_ok = "GENERAL REVENUE" in up and "UNIVERSITY" in up
        pledge_note = "UC General Revenue" if pledge_ok else "NOT UC GRB"
    elif "water" in claim or "wastewater" in claim:
        pledge_ok = any(k in up for k in ["WATER", "WASTEWATER", "SEWER", "REVENUE"])
        pledge_note = "essential-service revenue" if pledge_ok else "NOT water/sewer rev"
    elif "go" in claim or "general obligation" in claim or "school" in claim:
        pledge_ok = "GENERAL OBLIGATION" in up
        pledge_note = "GO confirmed" if pledge_ok else "NOT GO"
    if badmask:
        pledge_ok = False; pledge_note += " | MASQUERADE TOKEN PRESENT"
    rec['pledge_confirmed'] = bool(pledge_ok)

    # ---- AB-1200 ----
    is_k12 = ("school" in claim or "go" in claim or "hsd" in claim or "unified" in claim
              or "elementary" in claim or "high" in claim) and "community college" not in claim and "cmnty clg" not in claim.replace("community","cmnty")
    ab = "N/A"
    issuer_name_for_ab = (bl.get('issuer') or "")
    if cu == "91412G2F1" or cu == "91412HJC8" or "uc regents" in claim or "university" in claim:
        ab = "N/A (UC system revenue bond)"
        is_k12 = False
    elif "water" in claim or "wastewater" in claim:
        ab = "N/A (water revenue)"
        is_k12 = False
    if is_k12:
        # determine the district name
        nm = None
        for k in ["victor valley", "mendocino unified", "sequoia union high"]:
            if cu == "926055KH6": nm = "victor valley"
            if cu == "58661PDN9": nm = "mendocino unified"
            if cu == "817409H32": nm = "sequoia union high"
        flagged_hit = [f for f in FLAGGED if nm and nm in f]
        ab = "CLEAN (absent from neg/qual tables)" if not flagged_hit else f"FLAGGED: {flagged_hit}"
    rec['ab1200'] = ab

    # ---- verdict ----
    notes = []
    notes.append(f"FIGI={fg_name}/{fg_ticker}")
    notes.append(f"title={title}")
    notes.append(f"thr={round(thr,2)} demin={demin}")
    notes.append(f"cust-buy_prints={has_S} cust-sell_prints={has_P}")
    notes.append(f"list_tey={list_tey} list_mark={mark}")

    verdict = "CLEAR"; basis = []
    if tax_status == "TAXABLE":
        verdict = "REJECT"; basis.append("FEDERALLY TAXABLE")
    elif tax_status == "AMT":
        verdict = "REJECT"; basis.append("AMT bond")
    if not pledge_ok:
        verdict = "REJECT"; basis.append("pledge mismatch/masquerade: " + pledge_note)
    # tape staleness / move
    daysold = None
    if live_date:
        try:
            ld = datetime.date(*[int(x) for x in live_date.split("-")])
            daysold = (SETTLE - ld).days
        except Exception:
            pass
    flagcav = []
    if tape_moved is not None and abs(tape_moved) > 0.5:
        flagcav.append(f"tape moved {tape_moved}pt vs mark")
    if daysold is not None and daysold > 30:
        flagcav.append(f"mark stale {daysold}d")
    if tey_div is not None and abs(tey_div) > 0.05:
        flagcav.append(f"TEY div {tey_div}pp")
    if verdict != "REJECT" and flagcav:
        verdict = "FLAG"; basis += flagcav
    if not basis:
        basis = [f"{tax_status}, {pledge_note}, callable {p['next_call']}, tape fresh ({daysold}d)"]

    rec['verdict'] = verdict
    rec['basis'] = "; ".join(basis)
    rec['notes'] = " | ".join(notes)
    rec['_daysold'] = daysold

    print(f"  tax={tax_status} pledge={pledge_ok}({pledge_note}) call={p['next_call']} "
          f"livepx={live_px}@{live_date}({daysold}d) moved={tape_moved} tey={round(tey*100,3)} div={tey_div}pp "
          f"AB={ab} FIGI={fg_name} => {verdict}", flush=True)

    results.append(rec)
    json.dump(results, open(OUT, "w"), indent=1)
    time.sleep(1.2)

print("\nDONE. wrote", OUT)
