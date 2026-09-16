"""Cheba / Project Evergreen 'B Wild' — store-level-EBITDA -> buyer-FCFE bridge + return model.

The CIM (Project_Evergreen_B_Wild.pdf) discloses store-level economics but NO transaction
structure (price, leverage, fees, MOIC). The prior DD (outputs/evergreen_dd.json) established
that the marketed "22.9% EBITDA" is STORE-LEVEL (4-wall + royalty), not buyer cash flow. This
script quantifies that gap and shows the implied return as a FUNCTION of the undisclosed price
and leverage, so we can underwrite the deal we can't yet see terms for.

ALL undisclosed inputs are labeled ASSUMPTION with a basis. Disclosed inputs are labeled DECK.
Nothing here is precision — it is a defensible counter-model and a sensitivity frame for PCM.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# DISCLOSED (from the CIM, via prior image reads — outputs/evergreen_dd.json)
# ---------------------------------------------------------------------------
SALES_CONSOL = 68.06          # DECK p65: consolidated 24-unit sales ($M)
SLEBITDA_PF_TTM = 14.515      # DECK p64: Pro-Forma TTM P5 2025 store-level EBITDA ($M)
SLEBITDA_2024A = 13.10        # DECK p64: 2024 actual store-level EBITDA ($M)
SLEBITDA_2025E = 16.91        # DECK p64: 2025E store-level EBITDA ($M)
ROYALTY_DECK = 0.047          # DECK p49: single "royalty" line = 4.7% of sales
ROYALTY_STD = 0.050           # FDD Item 6 + FA §13.2: royalty = 5% of Net Sales (NOT 6% — corrected)
BRAND_FUND_PCT = 0.020        # FDD Item 6: Brand Fund Contribution = 2% of Net Sales (can rise to 4.2%);
                              # separate mandatory franchisor fee. The deck's 4.7% line may omit it.
N_UNITS = 24
RUMORED_ENTRY_MULT = 4.7      # from teaser/email, NOT this CIM; struck on (unknown) EBITDA base

# ---------------------------------------------------------------------------
# ASSUMPTIONS for items the CIM omits (each with a basis; varied in sensitivity)
# ---------------------------------------------------------------------------
# Above-store corporate G&A: SLEBITDA includes store labor+opex but NOT regional mgmt,
# accounting, marketing, area supervisors. Multi-unit franchise platforms typically run
# 5-8% of sales above-store. Basis: franchisee-platform norms; 24 units needs real overhead.
GNA_PCT = 0.06                # ASSUMPTION midpoint (range 0.05-0.08 in sensitivity)
# Owner/exec replacement comp: Timmons (CEO) + Archer (CFO) are the operating team. If their
# comp is NOT already in store-level opex, a buyer must fund replacement management.
OWNER_COMP = 1.0              # ASSUMPTION $M (range 0.75-1.5)
# Maintenance capex: restaurant reinvestment (equipment, refresh). 2-4% of sales typical.
MAINT_CAPEX_PCT = 0.03        # ASSUMPTION midpoint (range 0.02-0.04)
# Franchise-fee true-up: FDD Item 6 recurring fees = 5% royalty + 2% Brand Fund = 7% of Net Sales;
# the deck shows one 4.7% "royalty" line. Conservative = deck omits the Brand Fund -> deduct
# (7% - 4.7%) = 2.3pt. If it's already in store opex the gap is ~0. UNVERIFIABLE -> deduct.
APPLY_FRANCHISE_TRUEUP = True


def bridge(slebitda: float, sales: float = SALES_CONSOL, *,
           gna_pct=GNA_PCT, owner_comp=OWNER_COMP, maint_pct=MAINT_CAPEX_PCT,
           franchise_trueup=APPLY_FRANCHISE_TRUEUP) -> dict:
    """SLEBITDA -> true EBITDA -> unlevered FCF. Returns the full waterfall."""
    gna = sales * gna_pct
    fdd_fees = ROYALTY_STD + BRAND_FUND_PCT                 # 7% per FDD Item 6 (5% royalty + 2% brand fund)
    fee_trueup = sales * max(fdd_fees - ROYALTY_DECK, 0.0) if franchise_trueup else 0.0
    true_ebitda = slebitda - gna - owner_comp - fee_trueup
    maint_capex = sales * maint_pct
    unlev_fcf = true_ebitda - maint_capex
    return {
        "slebitda": slebitda,
        "less_gna": -gna,
        "less_owner_comp": -owner_comp,
        "less_franchise_fee_trueup": -fee_trueup,
        "true_ebitda": true_ebitda,
        "less_maint_capex": -maint_capex,
        "unlevered_fcf": unlev_fcf,
        "true_ebitda_pct_of_sl": true_ebitda / slebitda,
        "unlev_fcf_pct_of_sl": unlev_fcf / slebitda,
    }


def entry_view(slebitda: float, mult: float = RUMORED_ENTRY_MULT) -> dict:
    """What '4.7x' means depending on the base it is struck on."""
    b = bridge(slebitda)
    ev = mult * slebitda                     # entry struck on STORE-LEVEL (the flattering base)
    return {
        "ev_on_slebitda": ev,
        "mult_on_true_ebitda": ev / b["true_ebitda"],
        "unlev_fcf_yield_at_ev": b["unlevered_fcf"] / ev,
        "true_ebitda": b["true_ebitda"],
        "unlev_fcf": b["unlevered_fcf"],
    }


# New-unit economics for growth-capex netting (the prior model double-counted: it credited
# interim FCF AND the EBITDA growth that same cash had to fund).
SL_PER_NEW_UNIT = 0.644       # DECK p49: ~$2.8M AUV x ~23% store-level margin = $0.64M SLEBITDA/unit
NET_BUILD_COST = 1.0          # ASSUMPTION $M/unit (DECK $775K understated; FDD range $631K-$2.086M)


def levered_return(slebitda_entry: float, *, entry_mult: float, ebitda_growth: float,
                   exit_mult: float, leverage: float, debt_rate: float, hold_yrs: float) -> dict:
    """Equity MOIC/IRR with growth-capex netting. EV struck on store-level EBITDA both ends
    (apples-to-apples with the marketing). EBITDA growth above flat is BOUGHT with new units,
    whose build cost is netted against cumulative FCF — so cash can't be counted twice."""
    ev_in = entry_mult * slebitda_entry
    debt = ev_in * leverage
    equity_in = ev_in - debt
    slebitda_exit = slebitda_entry * ebitda_growth
    ev_out = exit_mult * slebitda_exit
    equity_out = ev_out - debt               # debt interest-only, repaid from exit proceeds

    new_units = max(0.0, (slebitda_exit - slebitda_entry) / SL_PER_NEW_UNIT)
    growth_capex = new_units * NET_BUILD_COST
    # cumulative UNLEVERED true FCF over the hold (avg of entry/exit run-rates x years)
    fcf_in = bridge(slebitda_entry)["unlevered_fcf"]
    fcf_out = bridge(slebitda_exit, sales=SALES_CONSOL * ebitda_growth)["unlevered_fcf"]
    cum_unlev_fcf = (fcf_in + fcf_out) / 2 * hold_yrs
    cum_interest = debt * debt_rate * hold_yrs
    net_cash = cum_unlev_fcf - cum_interest - growth_capex
    if net_cash >= 0:                        # build self-funds; surplus distributed
        cum_fcfe, equity_in_eff = net_cash, equity_in
    else:                                    # build needs follow-on capital calls
        cum_fcfe, equity_in_eff = 0.0, equity_in + (-net_cash)
    total_to_equity = equity_out + cum_fcfe
    moic = total_to_equity / equity_in_eff if equity_in_eff > 0 else float("nan")
    irr = moic ** (1 / hold_yrs) - 1 if moic > 0 else float("nan")
    return {
        "ev_in": ev_in, "debt": debt, "equity_in": equity_in, "equity_in_eff": equity_in_eff,
        "new_units": new_units, "growth_capex": growth_capex, "net_cash": net_cash,
        "slebitda_exit": slebitda_exit, "ev_out": ev_out, "equity_out": equity_out,
        "cum_fcfe": cum_fcfe, "moic": moic, "irr": irr,
    }


def fmt(x, d=2):
    return f"{x:,.{d}f}"


def main():
    L = []
    p = L.append
    p("# Cheba / Project Evergreen 'B Wild' — EBITDA Bridge & Return Model")
    p("_2026-06-25 · store-level→buyer-FCFE bridge built from the CIM's own disclosed numbers."
      " Undisclosed transaction terms (price/leverage/fees) are modeled as sensitivities — the"
      " deck contains none. DECK = disclosed; ASSUMPTION = our input with basis._\n")

    # ---- 1. The bridge ----
    p("## 1. Store-level EBITDA → buyer cash flow (the marketed-vs-real gap)\n")
    p("The deck markets **22.9% 'EBITDA'** (p49) and a consolidated **$14.515M PF TTM-P5 SLEBITDA**"
      " (p64). That is a 4-wall + royalty number — *before* above-store G&A, owner/exec comp,"
      " maintenance capex, D&A, and any debt service. The bridge to what equity actually earns:\n")
    for label, sl in [("PF TTM-P5 2025 (deck headline base)", SLEBITDA_PF_TTM),
                      ("2024 actual (un-pro-forma)", SLEBITDA_2024A)]:
        b = bridge(sl)
        p(f"**{label}** — SLEBITDA ${fmt(sl)}M:")
        p(f"| line | $M |")
        p(f"|---|---:|")
        p(f"| Store-level EBITDA (DECK) | {fmt(b['slebitda'])} |")
        p(f"| − Above-store G&A @ {GNA_PCT:.0%} sales (ASSUMPTION) | {fmt(b['less_gna'])} |")
        p(f"| − Owner/exec replacement comp (ASSUMPTION) | {fmt(b['less_owner_comp'])} |")
        p(f"| − Franchise-fee true-up: FDD 7% (5% roy + 2% brand fund) vs deck 4.7%, if not in opex | {fmt(b['less_franchise_fee_trueup'])} |")
        p(f"| **= True EBITDA** | **{fmt(b['true_ebitda'])}** |")
        p(f"| − Maintenance capex @ {MAINT_CAPEX_PCT:.0%} sales (ASSUMPTION) | {fmt(b['less_maint_capex'])} |")
        p(f"| **= Unlevered free cash flow** | **{fmt(b['unlevered_fcf'])}** |")
        p(f"\n  True EBITDA = **{b['true_ebitda_pct_of_sl']:.0%} of store-level**;"
          f" unlevered FCF = **{b['unlev_fcf_pct_of_sl']:.0%} of store-level**.\n")

    # ---- 2. What "4.7x" really is ----
    p("## 2. What the rumored 4.7x entry actually is\n")
    p("'4.7x' (from the teaser, not this CIM) struck on the **store-level** base is a much richer"
      " multiple on **true** EBITDA:\n")
    p("| entry base | EV @ 4.7x | = multiple on TRUE EBITDA | unlevered FCF yield @ that EV |")
    p("|---|---:|---:|---:|")
    for label, sl in [("PF TTM-P5 SLEBITDA $14.5M", SLEBITDA_PF_TTM),
                      ("2024A SLEBITDA $13.1M", SLEBITDA_2024A)]:
        e = entry_view(sl)
        p(f"| {label} | ${fmt(e['ev_on_slebitda'])}M | "
          f"**{fmt(e['mult_on_true_ebitda'],1)}x** | {e['unlev_fcf_yield_at_ev']:.1%} |")
    p("\n→ A headline '4.7x' on the marketed base is **~8x on true EBITDA** — the entry looks"
      " cheap only because it is struck on a pre-overhead number. The honest unlevered FCF yield"
      " is **~9-10%**, not the ~21% (=1/4.7) the headline implies.\n")

    # ---- 3. Return sensitivity ----
    p("## 3. Equity return — sensitivity to the two undisclosed levers (growth × exit)\n")
    p("Entry @ 4.7x PF-SLEBITDA (EV ≈ ${:.0f}M), 6-yr hold, 50% leverage @ 9.0% all-in"
      " (ASSUMPTIONS — the CIM discloses neither price nor debt). EV struck on store-level both"
      " ends (apples-to-apples with the marketing). 'EBITDA growth' is the consolidated"
      " store-level multiple — the 'double' = 2.0x requires ~23 new units (near-tripling the"
      " footprint) and the model nets each scenario's build capex against interim FCF.\n"
      .format(RUMORED_ENTRY_MULT * SLEBITDA_PF_TTM))
    # unit counts derived from SL_PER_NEW_UNIT so labels are honest (the 'double' nearly triples footprint)
    growths = [("flat (no new units)", 1.00), ("2025E +29% (~7 units)", 1.29),
               ("+60% (~14 units)", 1.60), ("DOUBLE (~23 units, deck thesis)", 2.00)]
    exits = [("flat 4.7x", 4.7), ("5.0x ('conservative')", 5.0), ("5.5x", 5.5)]
    p("**MOIC** (equity multiple):\n")
    p("| growth ↓ / exit → | " + " | ".join(e[0] for e in exits) + " |")
    p("|---|" + "|".join(["---:"] * len(exits)) + "|")
    for gl, g in growths:
        row = [gl]
        for el, ex in exits:
            r = levered_return(SLEBITDA_PF_TTM, entry_mult=4.7, ebitda_growth=g,
                               exit_mult=ex, leverage=0.50, debt_rate=0.09, hold_yrs=6)
            row.append(f"{fmt(r['moic'],2)}x")
        p("| " + " | ".join(row) + " |")
    p("\n**IRR** (6-yr):\n")
    p("| growth ↓ / exit → | " + " | ".join(e[0] for e in exits) + " |")
    p("|---|" + "|".join(["---:"] * len(exits)) + "|")
    for gl, g in growths:
        row = [gl]
        for el, ex in exits:
            r = levered_return(SLEBITDA_PF_TTM, entry_mult=4.7, ebitda_growth=g,
                               exit_mult=ex, leverage=0.50, debt_rate=0.09, hold_yrs=6)
            row.append(f"{r['irr']:.0%}")
        p("| " + " | ".join(row) + " |")

    # ---- 4. Takeaways ----
    # pull the specific cells the bullets cite so text and table can never diverge
    flat = levered_return(SLEBITDA_PF_TTM, entry_mult=4.7, ebitda_growth=1.00, exit_mult=4.7,
                          leverage=0.50, debt_rate=0.09, hold_yrs=6)
    base = levered_return(SLEBITDA_PF_TTM, entry_mult=4.7, ebitda_growth=1.29, exit_mult=4.7,
                          leverage=0.50, debt_rate=0.09, hold_yrs=6)
    dbl = levered_return(SLEBITDA_PF_TTM, entry_mult=4.7, ebitda_growth=2.00, exit_mult=5.0,
                         leverage=0.50, debt_rate=0.09, hold_yrs=6)
    p("\n## 4. Read\n")
    p(f"- **The 'double EBITDA' = a near-tripling of the footprint.** Doubling consolidated"
      f" store-level EBITDA needs **~{dbl['new_units']:.0f} new units** (24→~47) at Elevated AUVs"
      f" in unproven KS/KC-MO markets — and it consumes essentially all interim cash"
      f" (${dbl['growth_capex']:.0f}M build program). It is a capital obligation, not organic"
      f" growth; SSS has collapsed to 1.5% (p44).")
    p(f"- **Floor case** (no new units, flat 4.7x exit): **{fmt(flat['moic'],2)}x MOIC /"
      f" {flat['irr']:.0%} IRR** levered — a poor risk-adjusted return for an illiquid single-"
      f"operator niche-chain LP. **Honest base** (the deck's own 2025E +29%, flat exit):"
      f" **{fmt(base['moic'],2)}x / {base['irr']:.0%}**. The marketed 4-6x only appears in the"
      f" double × multiple-expansion corner ({fmt(dbl['moic'],2)}x / {dbl['irr']:.0%}) — the"
      f" *thesis*, not the base.")
    p("- **The single biggest swing is the EBITDA base, not the exit multiple**: the bridge cuts"
      " store-level $14.5M to ~$8.5M true EBITDA (~59%). If the 4.7x is actually struck on store-"
      " level (as marketed), the buyer is paying **~8x true EBITDA** — confirm the base before"
      " anything else.")
    p("- **Returns are levered & self-funding-dependent.** 50% debt @ 9% does meaningful lifting;"
      " unlevered the floor case is ~1.3-1.4x. The growth cases assume the build self-funds from"
      " retained FCF (model nets growth capex) — if it needs follow-on capital calls, IRR drops"
      " further on the later timing.")
    p("- **Most sensitive assumptions** (ask PCM to replace with actuals): the EBITDA base the 4.7x"
      " is struck on, above-store G&A %, owner-comp normalization, royalty reset, per-unit build"
      " cost, and leverage/rate. Every one is swappable for a disclosed number.\n")

    out = "outputs/cheba_bridge_model.md"
    open(out, "w").write("\n".join(L))
    print("\n".join(L))
    print(f"\n[wrote {out}]")


if __name__ == "__main__":
    main()
