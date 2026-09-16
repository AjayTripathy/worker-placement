"""Per-name CA capital-gains beta for the honesty basket.

PURPOSE
-------
Replace Ch4's categorical income/property/enterprise split with a CONTINUOUS per-name
credit-sensitivity to a California capital-gains shock — the channel an AI-equity crash
transmits through (same pipe as dot-com: state GF cap-gains/stock-option income tax).

THIS IS A STRUCTURAL MODEL, NOT AN ECONOMETRIC REGRESSION. Per-obligor pledged-revenue
time series over 20+ years do not exist to regress on CA cap-gains receipts. Instead each
name's beta is built from revenue-channel elasticity x credit-structure shield x regional
tech-hub factor, anchored to two hard facts:
  (1) CA cap-gains+option PIT revenue ran $17B (2000-01) -> $5B (2002-03), -71% [LAO];
      cap-gains avg ~7.9% of GF revenue, ~3x the volatility of overall PIT.
  (2) The dot-com credit outcome (by 2003): CA STATE GO fell S&P AA -> BBB (~6 notches) /
      Moody's Aa2 -> Baa1 (5 notches), worst-rated state, while SB-222 school GO and water
      revenue were untouched. (The 2009 GFC Baa1/IOU low is a SEPARATE episode — not this anchor.)

NORMALIZATION: beta = 1.00 == the credit/spread sensitivity of an unshielded CA state-GF
income-tax claim to a dot-com-magnitude cap-gains shock (i.e. CA State GO ~ 1.0). Every
other name is scaled relative to that. beta is a CREDIT-SPREAD/RATING beta (mark-to-market
credit risk), not a default beta (GO default risk is ~0 via constitutional priority).

beta_name = channel_beta x struct_factor x region_factor
Uncertainty: +/-CHANNEL_BAND on channel_beta -> per-name low/base/high.
"""
import json

HOLD = "/Users/ajay/exalted/signalos/verticals/muni_credit/data/etf_v2_holdings.json"
OUT  = "/Users/ajay/exalted/signalos/verticals/muni_credit/data/etf_v2_capgains_beta.json"
CHANNEL_BAND = 0.40   # +/-40% uncertainty on the channel elasticity

# --- revenue-channel elasticity to a dot-com-magnitude CA cap-gains shock (0..1) ---
CHANNEL = {
    "state_gf_income_tax":    1.00,   # the $17B->$5B pipe itself (reference)
    "county_gf_appropriation":0.35,   # county GF: property+sales dominant, some income/econ; approp risk
    "tax_increment":          0.20,   # marginal AV growth above frozen base, property-cycle linked
    "muni_revenue_authority": 0.15,   # lease/revenue authority, general-economy linked
    "ccrc_entrance":          0.30,   # entrance fees gated on residents selling assets (wealth-sensitive)
    "hospital_revenue":       0.12,   # non-cyclical demand + investment-income/regional links
    "housing_finance":        0.10,   # mortgage/housing linked, not income-tax
    "school_go_av":           0.05,   # Prop-13 acquisition-value AV: near-immune to an equity/income shock
    "water_revenue":          0.03,   # most non-cyclical revenue stream there is
}
# --- credit-structure shield: how much a lien/insurance/priority caps the rating move ---
STRUCT = {
    "state_go":        1.00,  # rating fully exposed (dot-com: 4-5 notches), even if default-protected
    "school_go_sb222": 0.60,  # statutory ad-valorem lien further insulates an already-sticky base
    "tab":             0.90,  # limited structural shield
    "hospital_naked":  1.00,  # naked CHFFA conduit
    "ccrc_calmortgage":0.45,  # HCAI/Cal-Mortgage insurance caps downside but partly inherits state credit
    "water":           0.95,
    "calhfa":          0.90,
    "county_cop":      0.85,  # COP weaker than GO; appropriation
    "muni_rev":        0.95,
}
# --- regional tech-hub multiplier ---
REGION_SV = 1.40   # Silicon Valley / Bay Area (direct tech-economy footprint)
REGION_BAY = 1.10
REGION_BASE = 1.00

# per-slot assignment {slot: (channel_key, struct_key, region, region_note)}
ASSIGN = {
    1:  ("school_go_av","school_go_sb222",REGION_BASE,"LA (Duarte USD)"),
    2:  ("school_go_av","school_go_sb222",REGION_BASE,"rural (Alpine USD)"),
    3:  ("school_go_av","school_go_sb222",REGION_BASE,"Fresno (Clovis USD)"),
    4:  ("school_go_av","school_go_sb222",REGION_BASE,"LA (Downey USD)"),
    5:  ("school_go_av","school_go_sb222",REGION_BASE,"Fresno (Sanger USD)"),
    6:  ("school_go_av","school_go_sb222",REGION_BASE,"LA (Pomona USD)"),
    7:  ("hospital_revenue","hospital_naked",REGION_SV,"Silicon Valley (El Camino)"),
    8:  ("hospital_revenue","hospital_naked",REGION_SV,"Silicon Valley (Stanford)"),
    9:  ("ccrc_entrance","ccrc_calmortgage",REGION_BAY,"Bay (Aldersly, San Rafael)"),
    10: ("ccrc_entrance","ccrc_calmortgage",REGION_BASE,"Central Valley (Bethany)"),
    11: ("housing_finance","calhfa",REGION_BASE,"statewide (CalHFA)"),
    12: ("tax_increment","tab",REGION_BASE,"Orange Co (Anaheim TAB)"),
    13: ("muni_revenue_authority","muni_rev",REGION_BASE,"Orange Co (Anaheim rev)"),
    14: ("tax_increment","tab",REGION_SV,"Silicon Valley (San Jose RDA succ TAB)"),
    15: ("tax_increment","tab",REGION_BASE,"Inland Empire (Fontana TAB)"),
    16: ("tax_increment","tab",REGION_BASE,"Sonoma (Cloverdale TAB)"),
    17: ("water_revenue","water",REGION_BASE,"SoCal (Met Water)"),
    18: ("water_revenue","water",REGION_BASE,"Monterey (Marina Coast Water)"),
    19: ("state_gf_income_tax","state_go",REGION_BASE,"statewide (CA State GO)"),
    20: ("county_gf_appropriation","county_cop",REGION_BASE,"San Diego (County pension COP)"),
}


def beta(ch_key, st_key, region, band=0.0):
    return CHANNEL[ch_key]*(1+band) * STRUCT[st_key] * region


def main():
    H = {h["slot"]: h for h in json.load(open(HOLD))["holdings"]}
    rows = []
    for slot, (ch, st, reg, note) in ASSIGN.items():
        b   = beta(ch, st, reg)
        lo  = beta(ch, st, reg, -CHANNEL_BAND)
        hi  = beta(ch, st, reg, +CHANNEL_BAND)
        rows.append({"slot":slot,"obligor":(H[slot].get("obligor_name") or "")[:38],
                     "channel":ch,"region_note":note,
                     "beta":round(b,3),"beta_lo":round(lo,3),"beta_hi":round(hi,3)})
    rows.sort(key=lambda r:-r["beta"])
    n = len(rows)
    tot   = sum(r["beta"] for r in rows)
    tot_lo= sum(r["beta_lo"] for r in rows)
    tot_hi= sum(r["beta_hi"] for r in rows)
    basket = tot/n
    # contribution share
    for r in rows:
        r["contrib_pct"] = round(100*r["beta"]/tot,1)
    ex19 = sum(r["beta"] for r in rows if r["slot"]!=19)/(n-1)
    agg = {"n":n,
           "basket_beta_equalwt":round(basket,3),
           "basket_beta_band":[round(tot_lo/n,3),round(tot_hi/n,3)],
           "interpretation":"basket carries ~%.0f%% of the cap-gains credit-sensitivity of an all-state-GO portfolio (=1.0)"%(100*basket),
           "state_go_contrib_pct":round(100*1.0/tot,1),
           "basket_beta_ex_state_go":round(ex19,3),
           "inert_tail_share_pct":round(100*sum(r["beta"] for r in rows if r["channel"] in("school_go_av","water_revenue"))/tot,1),
           "anchor":"CA cap-gains+option PIT revenue $17B(2000-01)->$5B(2002-03) = -71% [LAO]; State GO=1.0 calibrated to dot-com AA->BBB"}
    json.dump({"rows":rows,"aggregate":agg},open(OUT,"w"),indent=1)

    print(f"{'slot':>4} {'beta':>6} {'[lo,hi]':>14} {'cum%':>6}  obligor / channel")
    cum=0
    for r in rows:
        cum+=r["contrib_pct"]
        print(f"{r['slot']:>4} {r['beta']:>6.3f} [{r['beta_lo']:.3f},{r['beta_hi']:.3f}] {cum:>5.0f}%  "
              f"{r['obligor']:<38} {r['channel']}")
    print(f"\nEQUAL-WEIGHT BASKET BETA = {basket:.3f}  (band {agg['basket_beta_band']})")
    print(f"  vs all-State-GO portfolio = 1.000  ->  {agg['interpretation']}")
    print(f"  State GO (1 name) drives {agg['state_go_contrib_pct']}% of total basket beta")
    print(f"  basket beta EX the State GO = {ex19:.3f}")
    print(f"  inert tail (6 school GO + 2 water) = {agg['inert_tail_share_pct']}% of total beta")
    print("saved ->",OUT)


if __name__ == "__main__":
    main()
