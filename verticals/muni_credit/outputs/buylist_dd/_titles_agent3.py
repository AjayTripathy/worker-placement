import re
OUT = "/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/buylist_dd"
CUSIPS = ["95330PHH1","032591TU3","17132CDL9","358233ED2","777387AH4","607735CA3"]
for cu in CUSIPS:
    t = open(f"{OUT}/raw_{cu}.html").read()
    up = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).upper()
    print("="*90); print(cu)
    # the security title typically ends "...* COUPON: X %" — grab the 200 chars before " COUPON:"
    for m in re.finditer(r"([A-Z0-9 ,&.'/\(\)\-]{20,180}?)\*?\s*COUPON\s*:", up):
        seg = m.group(1).strip()
        if len(seg) > 15:
            print("  TITLE:", seg[-160:])
            break
    # also show any GO / pledge wording
    for kw in ["GENERAL OBLIGATION", "UNLIMITED", "UNLTD", "AD VALOREM", " GO ", "GO BDS", "GO BONDS", "CERTIFICATES OF PARTICIPATION", "MELLO", "SPECIAL TAX", "LEASE"]:
        if kw in up:
            idx = up.find(kw)
            print(f"    PLEDGE[{kw.strip()}]: ...{up[max(0,idx-40):idx+50]}")
    # coupon/maturity confirm
    cm = re.search(r"COUPON\s*:\s*([\d.]+)\s*% MATURITY DATE:\s*([\d/]+)", up)
    if cm: print("  COUPON/MAT:", cm.group(1), cm.group(2))
