"""build_desk_rfq — generate the bond-desk RFQ / bid-wanted sheet for the CURRENT book, with the SPREADS
we want to test computed from the real EMMA trade tape (customer offer vs customer bid).

For each DD-confirmed BUY:
  - offer  = recent customer-BUY prints (sale_to_customer) = what retail pays  -> the level we'd lift
  - bid    = recent customer-SELL prints (purchase_from_customer) = the dealer bid
  - spread = offer - bid (the dealer round-trip); our TEST BID sits inside it.
The concession we test scales with liquidity (you can lift a self-directed name; you must be paid to
provide liquidity in a thin one):
  SELF-DIRECTED  -> test at the offer (or -3 bps): just hit it
  DESK           -> test offer -10 bps: work the order
  THIN           -> test offer -22 bps: you're the liquidity, demand the concession
Outputs: outputs/RFQ_BOOK.md (desk sheet) + outputs/RFQ_BOOK.json (structured, for the OMS/desk).

NEVER places an order — staging only.  python build_desk_rfq.py [--par 40000]
"""
import json, os, re, sys, datetime, statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
REPORTS = OUT / "diligence_reports"
TODAY = datetime.date(2026, 6, 21)
WINDOW_DAYS = 60          # "recent" tape window for a stable two-sided read
RETAIL_MIN, RETAIL_MAX = 5_000, 250_000   # exclude institutional blocks (they print through retail)
CONCESSION_BPS = {"SELF-DIRECTED": 3, "DESK": 10, "THIN": 22, "UNKNOWN": 15}


def _load(p, d):
    try: return json.load(open(p))
    except Exception: return d


def _tape(cu):
    for f in (REPORTS / cu / "raw" / "emma_trade_tape.json", REPORTS / cu / "raw" / "trade_tape.json"):
        if f.exists():
            d = _load(f, [])
            return d if isinstance(d, list) else d.get("data") or d.get("trades") or []
    return []


def _two_sided(cu, today):
    """Recent customer offer (we pay) / customer bid (dealer pays) medians + the spread, from the tape."""
    rows = _tape(cu)
    offers, bids = [], []
    for r in rows:
        try:
            d = datetime.date.fromisoformat((r.get("trade_date") or "")[:10])
        except Exception:
            continue
        if (today - d).days > WINDOW_DAYS:
            continue
        par = r.get("par_traded") or 0
        if not (RETAIL_MIN <= par <= RETAIL_MAX):
            continue
        px, yld, tt = r.get("price"), r.get("yield_pct"), r.get("trade_type")
        if px is None:
            continue
        if tt == "sale_to_customer":
            offers.append((px, yld))
        elif tt == "purchase_from_customer":
            bids.append((px, yld))
    def med(xs, i): return round(st.median([x[i] for x in xs if x[i] is not None]), 3) if xs else None
    return {"offer_px": med(offers, 0), "offer_yld": med(offers, 1),
            "bid_px": med(bids, 0), "bid_yld": med(bids, 1),
            "n_offer": len(offers), "n_bid": len(bids)}


def main():
    par = 40_000
    if "--par" in sys.argv:
        par = int(sys.argv[sys.argv.index("--par") + 1])
    dd = _load(OUT / "dd_verdicts.json", {})
    m = {r["cusip"]: r for r in _load(OUT / "DILIGENCE_MASTER.json", [])}
    lt = _load(OUT / "LIQUIDITY_TAPE.json", {})
    calls = _load(OUT / "CALL_SCHEDULES.json", {})
    book = [cu for cu, v in dd.items() if v == "BUY" and cu in m]
    book.sort(key=lambda cu: str(m[cu].get("maturity")))   # ladder order

    rows = []
    for cu in book:
        r = m[cu]; liq = lt.get(cu, {}); ts = _two_sided(cu, TODAY)
        tier = liq.get("execution_tier") or "UNKNOWN"
        offer = ts["offer_px"] if ts["offer_px"] is not None else r.get("px")
        # offer yield: prefer the recent tape; fall back to the screen YTW (tape rows are often null-yield)
        offer_yld = ts["offer_yld"] if ts["offer_yld"] is not None else (
            round((r.get("ytw") or 0) * 100, 3) if r.get("ytw") else None)
        spread_px = (round(offer - ts["bid_px"], 3) if (offer is not None and ts["bid_px"] is not None) else None)
        spread_bps = (round(ts["bid_yld"] - ts["offer_yld"], 1)
                      if (ts["bid_yld"] is not None and ts["offer_yld"] is not None) else None)
        conc = CONCESSION_BPS[tier]
        # price sensitivity from a DURATION proxy (NOT the noisy tape spread, which blows up when the
        # measured bid/offer yields nearly coincide): mod duration ~ 0.75 x years-to-maturity, capped 14.
        try:
            yrs = max(1, int(str(r.get("maturity"))[:4]) - TODAY.year)
        except Exception:
            yrs = 12
        mod_dur = min(yrs * 0.75, 14.0)
        px_per_bp = mod_dur * (offer or 100) / 10000.0     # px points per 1 bp of yield
        test_bid_yld = round(offer_yld + conc / 100.0, 3) if offer_yld is not None else None
        test_bid_px = round(offer - conc * px_per_bp, 3) if offer is not None else None

        # --- CALL DISCIPLINE: every CA muni here is callable at par. Paying ABOVE the call price on a
        # callable bond means your yield-to-WORST is to the call, not to maturity, and you forfeit the
        # premium when it's redeemed. HARD RULE: never bid above the call price. ---
        ci = calls.get(cu, {})
        call_px = ci.get("call_price"); call_dt = ci.get("next_call_date")
        cd = None
        if call_dt and re.match(r"\d\d/\d\d/\d{4}", str(call_dt)):
            mm, day, yy = call_dt.split("/"); cd = datetime.date(int(yy), int(mm), int(day))
        yrs_to_call = round((cd - TODAY).days / 365.0, 1) if cd else None
        capped = False
        if call_px and test_bid_px is not None and test_bid_px > call_px:
            test_bid_px = float(call_px); capped = True
            test_bid_yld = r.get("coupon")          # at par, YTM == coupon (clean, no premium amortization)
        offer_premium = bool(call_px and offer and offer > call_px + 0.10)   # market is above the call price
        near_call = bool(yrs_to_call is not None and yrs_to_call <= 2.0)

        rows.append({
            "cusip": cu, "issuer": str(r.get("issuer")), "coupon": r.get("coupon"),
            "maturity": str(r.get("maturity"))[:10], "pledge": r.get("pledge") or "school",
            "par": par, "tier": tier, "n_yr": liq.get("n365"), "max_block": liq.get("max_block"),
            "offer_px": offer, "offer_yld": offer_yld, "bid_px": ts["bid_px"], "bid_yld": ts["bid_yld"],
            "tape_spread_px": spread_px, "tape_spread_bps": spread_bps,
            "test_concession_bps": conc, "test_bid_px": test_bid_px, "test_bid_yld": test_bid_yld,
            "n_offer_60d": ts["n_offer"], "n_bid_60d": ts["n_bid"],
            "call_date": call_dt, "call_price": call_px, "yrs_to_call": yrs_to_call,
            "bid_capped_at_par": capped, "offer_above_par": offer_premium, "near_call": near_call,
        })

    json.dump({"asof": TODAY.isoformat(), "par_per_name": par, "n": len(rows),
               "book_par": par * len(rows), "names": rows},
              open(OUT / "RFQ_BOOK.json", "w"), indent=1, default=str)

    premium = [x for x in rows if x["offer_above_par"]]
    L = [f"# RFQ / Bid-Wanted Sheet — CA Muni HTM Book ({len(rows)} names)", "",
         f"_As of {TODAY}. Every name DD-confirmed BUY (combined binder on file). HTM ladder. Offer = recent "
         f"EMMA customer-buy tape (retail clips, {WINDOW_DAYS}d); some are stale stored marks — the desk's "
         f"live market governs. Size ~${par:,}/name (~${par*len(rows):,} book)._", "",
         "> **⚠ CALL DISCIPLINE — read first. Every name is callable at PAR (100); "
         f"{sum(1 for x in rows if x['near_call'])} within ~2 years. We do **NOT bid above the call price** "
         "on any name — paying a premium on a near-par-callable makes your yield-to-WORST the call (well "
         "below the coupon) and forfeits the premium when it's redeemed. All test bids below are **capped "
         "at par.** Where the market is above par, we pass or wait — we do not chase.**", "",
         "| # | CUSIP | Issuer | Cpn | Mat | Tier | Offer | **Call (par)** | **Test bid (≤par)** | n/yr |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for i, x in enumerate(rows, 1):
        offer = f"{x['offer_px']}" + ("  ⚠>par" if x["offer_above_par"] else "")
        call = f"{str(x['call_date'])[:10]} @{x['call_price']}" + ("  **NEAR**" if x["near_call"] else "")
        tb = (f"**{x['test_bid_px']} / {x['test_bid_yld']}%**" + (" *(capped @par)*" if x["bid_capped_at_par"] else f" (+{x['test_concession_bps']}bp)")) if x["test_bid_px"] is not None else "—"
        L.append(f"| {i} | {x['cusip']} | {x['issuer'][:24]} | {x['coupon']} | {x['maturity'][:7]} | "
                 f"{x['tier']} | {offer} | {call} | {tb} | {x['n_yr']} |")

    thin = [x['cusip'] for x in rows if x['tier'] == 'THIN']
    nobid = [x['cusip'] for x in rows if not x['bid_px']]
    L += ["", "## The test — what we want priced", "",
          f"1. **Live two-sided market** on each, and can you **source the offer at size** (${par:,} clip) — "
          "or is it bid-only?",
          "2. **Can you fill at our Test bid?** It's at or below par (capped — see call discipline). Where you "
          "can't, show your best offer and the **yield-to-WORST** (to the call, not to maturity) at that offer.",
          f"3. **Do NOT show us premium offers as a buy.** Names where the market is already above par "
          f"({', '.join(x['cusip'] for x in premium) or 'none'}) — at a premium the YTW is to the par call; "
          "we will not pay up. Quote yield-to-call if you quote a premium.",
          f"4. **Thin names** (test wider): {', '.join(thin) or 'none'} — the execution risk; tell us which "
          "you simply **cannot show**.",
          f"5. Names with **no recent customer bid** on the tape ({', '.join(nobid) or 'none'}) — confirm a "
          "market exists at all before we rest a bid.",
          "6. **Relative value:** any better swap in the same maturity/zone/credit at a tighter spread (at or "
          "below par)?",
          "7. Odd-lot (~$40k) handling + settlement — flag any name where odd-lot pricing is punitive.", "",
          "_Staging only — no order is placed until per-name fills are confirmed and approved. We never bid "
          "above the call price._"]
    open(OUT / "RFQ_BOOK.md", "w").write("\n".join(L))
    _render_pdf("\n".join(L), OUT / "RFQ_BOOK.pdf")
    print(f"RFQ_BOOK: {len(rows)} names | book ${par*len(rows):,} | thin={len(thin)} no-bid={len(nobid)}")
    print(f"  -> {OUT/'RFQ_BOOK.md'}  +  RFQ_BOOK.json  +  RFQ_BOOK.pdf")


def _render_pdf(md_text, dest):
    """Render the desk sheet to a landscape PDF (wide table) via Playwright/chromium. Best-effort."""
    try:
        import markdown as _md
        from playwright.sync_api import sync_playwright
    except Exception:
        return
    css = ("<style>@page{size:Letter landscape;margin:0.5in} body{font:9pt/1.4 -apple-system,Arial,sans-serif}"
           "h1{font-size:15pt;border-bottom:2px solid #234} table{border-collapse:collapse;width:100%;font-size:8pt}"
           "th,td{border:1px solid #ccd;padding:3px 5px;text-align:left} th{background:#eef2f7}</style>")
    html = css + _md.markdown(md_text, extensions=["tables", "sane_lists"])
    try:
        with sync_playwright() as p:
            br = p.chromium.launch(); pg = br.new_page()
            pg.set_content(html, wait_until="load")
            pg.pdf(path=str(dest), format="Letter", landscape=True, print_background=True,
                   margin={"top": "0.4in", "bottom": "0.4in", "left": "0.3in", "right": "0.3in"})
            br.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
