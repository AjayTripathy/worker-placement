"""refresh_universe.py — re-pull the CA insulated-muni universe from IBKR TWS into bonds_priced.json.

This is the FUEL for bond_scanner.py. The prior cached universe was a one-off 4-5%-coupon scan that
MISSED the 3% discount vintage (the highest-after-tax-TEY school GOs). This re-pull widens coupon to
3-6 and partitions the BOND.MUNI CA scanner across insulated-issuer keywords (to beat the 50-row cap),
so it captures the discount school GOs + water/UC names bond_scanner wants — and skips the COP/CFD/RDA
noise by keyword-targeting, which also saves downstream EMMA work.

Requires TWS running (port 7496, readonly). Run on demand, or wire into a WEEKLY cron (a fresh universe
is what lets the daily bond_scanner surface genuinely new issuance). Writes bonds_priced.json in the
exact shape bond_scanner reads: {source, screen, n, bonds:[{conid,cusip,coupon,maturity,isin,px,ytm}]}.

Usage:  python3 refresh_universe.py [--out bonds_priced.json] [--keywords KW,KW,...] [--quick]
"""
import json, os, re, time, datetime, argparse, logging
logging.getLogger("ib_insync").setLevel(logging.CRITICAL)
from ib_insync import IB, ScannerSubscription, TagValue

HERE = os.path.dirname(os.path.abspath(__file__))
SETTLE = datetime.date.today()
DA = re.compile(r"\s(\d+\.?\d*)\s+(\d{1,2}/\d{1,2}/\d{2,4})")

# Insulated-issuer keyword partitions — each returns up to 50 rows from the BOND.MUNI CA scanner;
# union across keywords gives broad coverage of the pledge types bond_scanner accepts.
KEYWORDS = ["UNIF", "UNIFIED", "ELEM", "ELEMENTARY", "HIGH SCH", "SCH DIST", "SCHOOL", "UNION",
            "CMNTY COLL", "COMMUNITY COLL", "COLLEGE", "REGENTS", "UNIV OF CALIF", "STATE UNIV",
            "WATER", "WTR", "SEWER", "SANITAT", "IRRIGATION", "UTILITY", "UTIL", "MUNICIPAL UTIL",
            "PUBLIC UTIL", "RECLAMATION", "POWER", "ELECTRIC"]

def parse(s):
    m = DA.search(s or "")
    if not m: return None, None
    cp = float(m.group(1)); mm, dd, yy = m.group(2).split("/"); yy = int(yy)
    return cp, f"{(yy if yy > 1900 else 2000 + yy):04d}-{int(mm):02d}-{int(dd):02d}"

def ytmf(px, cp, mat):
    try: y, m, d = [int(x) for x in mat.split("-")]
    except Exception: return None
    T = (datetime.date(y, m, d) - SETTLE).days / 365.25
    if T <= 0 or not px or px <= 0: return None
    n = max(1, round(T * 2)); c = cp / 2.0; lo, hi = -0.05, 0.40
    for _ in range(60):
        rr = (lo + hi) / 2; per = rr / 2
        pv = sum(c / (1 + per) ** k for k in range(1, n + 1)) + 100 / (1 + per) ** n
        lo, hi = (rr, hi) if pv > px else (lo, rr)
    return round((lo + hi) / 2, 4)

# coupon bands — the scanner returns only the top-50-by-yield per query, so a single 3-6% band gets
# crowded with premium 5-6s and the 3% DISCOUNTS never surface. Partition by coupon so each tier
# (esp. the 3% de-minimis discounts, the highest-after-tax-TEY names) gets its own top-50.
COUPON_BANDS = [("2.0", "3.6"), ("3.6", "4.6"), ("4.6", "6.1")]

def scan(ib, kw, clo, chi):
    sub = ScannerSubscription(instrument="BOND.MUNI", locationCode="BOND.MUNI.US",
                              scanCode="HIGH_BOND_ASK_YIELD_ALL", numberOfRows=50)
    f = [TagValue("couponRateAbove", clo), TagValue("couponRateBelow", chi),
         TagValue("maturityDateAbove", "20340101"), TagValue("maturityDateBelow", "20461231"),
         TagValue("bondUSStateLike", "CA"), TagValue("bondIssuerLike", kw)]
    try:
        return [sd.contractDetails.contract for sd in ib.reqScannerData(sub, [], f) if sd.contractDetails]
    except Exception as e:
        print(f"   scan '{kw}'/{clo}-{chi} err {str(e)[:40]}"); return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "bonds_priced.json"))
    ap.add_argument("--keywords", default=None, help="comma-separated override")
    ap.add_argument("--quick", action="store_true", help="3 keywords only (smoke test)")
    ap.add_argument("--port", type=int, default=7496)
    a = ap.parse_args()
    kws = (a.keywords.split(",") if a.keywords else (KEYWORDS[:3] if a.quick else KEYWORDS))

    ib = IB(); ib.connect("127.0.0.1", a.port, clientId=143, timeout=20, readonly=True)
    cand = {}
    for kw in kws:
        kn = 0
        for clo, chi in COUPON_BANDS:
            cs = scan(ib, kw, clo, chi)
            for c in cs:
                r = ib.reqContractDetails(c)
                if not r: continue
                d = r[0]; cu = getattr(d, "cusip", None)
                cp, mat = parse(getattr(d, "descAppend", "") or "")
                if cu and cp and mat and cu not in cand:
                    cand[cu] = {"conid": c.conId, "cusip": cu, "coupon": cp, "maturity": mat,
                                "isin": None, "_c": c}; kn += 1
        print(f"   [{kw}] +{kn} → universe {len(cand)}", flush=True)
    print(f"[refresh] {len(cand)} unique insulated-candidate CUSIPs; pricing...", flush=True)

    # price in batches via snapshot tickers (IBKR muni feed = close-only)
    contracts = [cand[cu].pop("_c") for cu in list(cand)]
    cus = list(cand)
    for i in range(0, len(contracts), 40):
        chunk = contracts[i:i+40]; cu_chunk = cus[i:i+40]
        try:
            ticks = ib.reqTickers(*chunk)
        except Exception:
            ticks = []
        for cu, t in zip(cu_chunk, ticks):
            px = None
            for v in (getattr(t, "close", None), getattr(t, "last", None), getattr(t, "marketPrice", lambda: None)()):
                if v and v == v and v > 0: px = float(v); break   # v==v filters NaN
            cand[cu]["px"] = round(px, 3) if px else None
            cand[cu]["ytm"] = ytmf(px, cand[cu]["coupon"], cand[cu]["maturity"]) if px else None
        print(f"   priced {min(i+40,len(contracts))}/{len(contracts)}", flush=True)
    ib.disconnect()

    bonds = [b for b in cand.values()]
    out = {"source": "refresh_universe", "screen": "CA BOND.MUNI 3-6% / 2034-2046 / insulated-kw",
           "asof": SETTLE.isoformat(), "n": len(bonds), "bonds": bonds}
    json.dump(out, open(a.out, "w"), indent=1, default=str)
    priced = sum(1 for b in bonds if b.get("px"))
    print(f"[refresh] wrote {a.out}: {len(bonds)} bonds ({priced} priced)", flush=True)

if __name__ == "__main__":
    main()
