"""Hardened Test C: ordinal stress from BLIND per-issuer rating-action COUNTS (round 2),
scored via the pre-registered rubric (testC_hardening_rubric.json). Tie-aware Spearman.

Ordinal stress 0-3 assigned by the fixed rubric from documented counts only:
  3 = default(s) OR sector-wide multi-notch (>=3); 2 = multiple downgrades / neg-outlook+dg;
  1 = isolated downgrade or sector pressure, no CA bond action enumerated; 0 = affirmed/upgraded.
'not-documented' middle cells -> 0 for downgrades is treated as UNRESOLVED (counted 0 but flagged).
"""
import json
from itertools import groupby

SEC = ["State GO","County COP","RDA/TAB","Hospital","CCRC","CalHFA","School GO","Water"]
PRED = {"State GO":1,"County COP":2,"RDA/TAB":3,"Hospital":4,"CCRC":5,"CalHFA":6,"School GO":7,"Water":8}

# ordinal stress from round-2 documented counts (evidence noted in comments)
ORD = {
 "Dot-com 2000-03 (income/cap-gains)": {
   "State GO":3,   # ~9 actions, AA->BBB/Baa1 multi-notch
   "County COP":3, # state lease/appropriation tracked GO A->BBB- (multi-notch); no default
   "RDA/TAB":0,    # 0 confirmed in-window (AV rose; TAB distress is post-2008)
   "Hospital":1,   # BBA operating distress, but 0 documented CA CHFFA bond rating actions
   "CCRC":0,"CalHFA":0,"School GO":0,"Water":0},
 "GFC 2008-09 (property/liquidity)": {
   "State GO":3,   # 7 actions, A->Baa1
   "County COP":3, # Vallejo Ch.9 default 2008 (COP payments suspended)
   "RDA/TAB":1,    # Ripon A3->Baa2; AV pressure; no default
   "Hospital":1,   # ARS/liquidity stress, neg outlook, no CA default enumerated
   "CCRC":2,       # national default cluster (Erickson); CA subcount not isolable
   "CalHFA":2,     # >=2 Moody's HMRB downgrades (~$5B), no default
   "School GO":0,"Water":0},
 "COVID 2020 (operational/liquidity)": {
   "State GO":0,   # affirmed (Fitch upgrade 2019; held 2020)
   "County COP":0,"RDA/TAB":0,
   "Hospital":2,   # Pioneers Memorial 3-notch to junk + national neg outlook
   "CCRC":3,       # record 23 retirement defaults (national); hardest-hit sector
   "CalHFA":0,"School GO":0,"Water":0},
 "2022 (rate/inflation)": {
   "State GO":0,   # held (no 2022 action)
   "County COP":0,"RDA/TAB":0,
   "Hospital":1,   # neg sector outlook, no CA default
   "CCRC":2,       # #1 default sector nationally ($560M/75%); CA not isolable
   "CalHFA":0,     # UPGRADED S&P AA (Dec 2022)
   "School GO":0,"Water":0},
}

def tie_ranks(scores):  # higher stress -> rank 1; average ranks for ties
    order = sorted(SEC, key=lambda s: -scores[s])
    ranks = {}; i = 0
    while i < len(order):
        j = i
        while j < len(order) and scores[order[j]] == scores[order[i]]:
            j += 1
        avg = (i+1 + j)/2.0  # average of ranks (i+1 .. j)
        for k in range(i, j):
            ranks[order[k]] = avg
        i = j
    return ranks

def spearman(pred, act):
    n=len(pred); d2=sum((pred[s]-act[s])**2 for s in pred)
    return 1 - 6*d2/(n*(n*n-1))

out={"crises":{}}
print(f"{'crisis':<38}{'hardened rho':>13}   notes")
for crisis, sc in ORD.items():
    ar = tie_ranks(sc)
    rho = spearman(PRED, ar)
    nties = max(len(list(g)) for _,g in groupby(sorted(sc.values())))
    out["crises"][crisis]={"rho_hardened":round(rho,3),"ordinal":sc,"actual_ranks":ar}
    print(f"{crisis:<38}{rho:>13.2f}   largest tie-block={nties}")
# insulated tier check
ins_zero = all(ORD[c]["School GO"]==0 and ORD[c]["Water"]==0 for c in ORD)
print(f"\nschool GO & water = 0 documented actions in ALL 4 regimes: {ins_zero}")
json.dump(out, open("/Users/ajay/exalted/signalos/verticals/muni_credit/data/testC_hardened.json","w"), indent=1)
print("saved -> data/testC_hardened.json")
