"""smallcap_value_watch — tracked watch for the cheap-AND-quality small-cap-value basket (rotation
thesis #1). READ-ONLY, no orders. Names that survived the deep-value finder -> quality overlay (now with
one-time-gain normalization) -> R/f(M) trap-filter -> full DD (GCT/CRCT) or trap-filter (the rest).
16 consumer-side candidates trap-filtered -> 7 real; symmetric-DD on the non-consumer survivors (2026-06-27)
added REPX (energy) and benched SD, killed WLKP/INVA -> 8 names here. Per-name files in data/*_trap.md.

Each carries: live price + zone vs entry band, FV bear/base/bull, conviction, and the per-name KILL
TRIGGERS the diligence surfaced. The thesis: in a small-cap rotation the edge is EXCLUSION — own the
cheap-and-VERIFIED, the screen-cheapest were all traps (GIII/UPBD/SIGA/YELP/PSIX/COLL). Per-name DDs in
verticals/deep_value/data/*_trap.md and *_FULL_DD.md.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE / "data" / "smallcap_value_log.jsonl"

# entry=(start, deep/truck); fv=(bear, base, bull). conviction HIGH/MED/LOW. thin=use-limits.
BASKET = {
    "GCT": {"conv": "HIGH", "entry": (32, 25), "fv": (24, 40, 60), "sector": "B2B furniture/3PL",
            "thesis": "net-cash(31% of mcap, zero bank debt) distributor+3PL mis-priced as China-fraud; 8.9x P/E / "
                      "~5.9x EV/EBIT, ~15% FCFy ($182.8M FCF), NI +9% to $137.4M, KPMG-audited/no-VIE; the honest "
                      "catch = it's a 1P-distributor (29.8%-GM engine) not the 'asset-light marketplace' bulls sell; "
                      "deserved discount = controlled-co (Wu 70.7% vote), NOT fraud. THE high-conviction find. "
                      "TARIFF BEAR NOW SIZED (2026-06-28, origin_mix triangulation): China-origin ~62/73/82% of "
                      "~$2.06B GMV (3P 85% / 1P 73% / Noble-House 55%; customs BOL 80/20 China/VN corroborates). "
                      "Bear bounded: the biggest China bucket (3P, $851M) is OFF GCT's P&L (tariff incidence on the "
                      "3P seller/US buyer); GCT's own-inventory China landed cost ~$558M (1P + Noble House) -> ~$67M "
                      "worst-case un-recovered EBIT (~42% of $161.2M pretax) at 60% pass-through, ~$0 at the FULL "
                      "pass-through demonstrated Q3'25 (product "
                      "margin EXPANDED to 29.9%). NOT a margin value-trap; residual = demand-elasticity (spend/buyer "
                      "$144k->$130k) + 70.7% control. Re-struck FV: bear $25 (cash-backstopped) / base $42 (+31%) / bull $60.",
            "kill": "GM <22% for 2 quarters / auditor change off KPMG / organic (ex-acq) rev negative / Sec-232 "
                    "furniture step-up effective Jan-2027 / Founder-Undertaking lapse ~Aug-2027 + privatization chatter"},
    "DFIN": {"conv": "HIGH", "entry": (42, 36), "fv": (45, 56, 60), "sector": "compliance software",
             "thesis": "software-transition compounder mis-priced as dying-print: SW now 47% rev/45% profit, +21% "
                       "EBITDA; EBIT GROWS on declining rev (real mix-shift); the scary GAAP net-income drop was a "
                       "1-time non-cash pension settlement; 8.6x EV/EBIT, 10.5% FCFy, 1.4x lev, ~5%/yr buyback.",
             "kill": "prolonged IPO/M&A deal-freeze (EBIT toward ~$115M) / software mix stalls below 50% of profit / "
                     "leverage rises on a debt-funded deal"},
    "EVER": {"conv": "MED (HALF-SIZE)", "entry": (23, 18), "fv": (25, 38, 41), "sector": "insurance marketplace",
             "thesis": "online insurance lead-gen marketplace; cyclical-peak trap REFUTED — Q1 printed RECORD op-income "
                       "+ record 12.3% margin, still new-highs (the +132% was a trough base-effect, not a peak); net "
                       "cash $178M, zero debt. HALF-SIZE: ONE carrier = 40% of revenue + ~90% auto = concentration risk.",
             "kill": "the 40%-customer concentration footnote worsens / TRUE YoY revenue decline (distinct from the "
                     "seasonal Q1 dip) = re-opens the cyclical-peak hypothesis"},
    "EPAM": {"conv": "MED (STARTER <=$80)", "entry": (80, 70), "fv": (65, 115, 131), "sector": "IT/digital-engineering",
             "thesis": "premium digital-product engineering at 6.2x EV/EBIT, net cash ~$17/sh, 14.6% FCFy, de-rated "
                       "-60% on AI-disruption + Ukraine-delivery fears. Geography DE-RISKED (India now #1 delivery); "
                       "AI net-POSITIVE so far ($125M AI rev, +Anthropic partnership). BUT organic growth low-single-"
                       "digit + guide LOWERED; the AI-disruption SECULAR question is the open UNVERIFIABLE = starter "
                       "only, not a conviction core.",
             "kill": "organic cc revenue turns negative / delivery headcount must keep FALLING to defend margin (= AI "
                     "compressing billable hours, the bear winning) / a >10% client emerges then churns"},
    "SBH": {"conv": "MED-LOW", "entry": (15, 12), "fv": (16, 20, 22), "sector": "beauty retail/distrib",
            "thesis": "Sally Beauty Supply + CosmoProf pro-distribution; 'dying retail' REFUTED — consolidated comps "
                      "+1.3%, Sally comps positive w/ traffic AND unit-retail up; net debt 1.7x & FALLING; +17% was "
                      "stale, latest qtr ~+4% gross-margin-led (Fuel-for-Growth). Return = re-rate + ~6%/yr buyback + "
                      "de-lever, NOT organic growth. Ties the beauty theme.",
            "kill": "Sally (consumer) comps turn NEGATIVE / net-debt/EBITDA rises (de-lever reverses) / GM gains fade"},
    "BKE": {"conv": "LOW (income-value)", "entry": (43, 38), "fv": (40, 49, 52), "sector": "apparel retail",
            "thesis": "net-cash ($5.73/sh) 33%-ROIC mall apparel retailer; the MELT thesis REFUTED — comps +5.1%, "
                      "transactions +2.6% (rising TRAFFIC), store count flat. BUT the +37% EBIT that surfaced it was a "
                      "1-time $19.1M litigation settlement -> underlying EBIT DECLINED YoY (the growth signal is a "
                      "trap). Income-value 'paid-to-wait': 3.2% covered regular div + variable special. Buy the "
                      "cash-return, NOT the growth. 6.8-7.3x EV/EBIT ex-settlement.",
            "kill": "comps turn NEGATIVE / transactions roll over (the anti-melt tell breaks) / regular dividend cut"},
    "CRCT": {"conv": "LOW (income-value, thin)", "entry": (4.40, 4.10), "fv": (3.22, 5.50, 7.72), "sector": "crafting subscription",
             "thesis": "89%-GM Cricut Access subscription annuity inside a declining-hardware shell; annuity GROWING but "
                       "MATURING (penetration ~92%, net-adds halving, first sequential sub-decline); FCFy FLATTERED "
                       "(14% headline -> ~7-9% normalized); income-value 'paid-to-wait' (4.4% div + buyback); Class-B = "
                       "5 votes -> 93% controlled = LOWBALL-take-under risk (not a premium). Accumulate-on-weakness, LIMITS.",
             "kill": "paid-subscribers roll over QoQ / Platform (subscription) rev turns negative YoY / controller "
                     "take-under proposal / recurring capital-return cut while cash is retained (pre-take-private tell)"},
    "REPX": {"conv": "MED-LOW (HALF-SIZE energy; WATCH-not-add, already +31% YTD)", "entry": (30, 26), "fv": (22, 40, 55), "sector": "energy E&P (Permian)",
             "thesis": "Riley Permian small-cap E&P; symmetric-DD survivor (2026-06-27) = the first NON-consumer leg. The "
                       "scary screen inputs are mischaracterizations: the '-17% EBIT' is -13% and 100% PRICE (WTI deck -14%) "
                       "while production GREW +8% (Q1'26 oil +46% YoY); the $70M GAAP 'loss' is a $115M non-cash hedge MTM on "
                       "+$44M op-income; Silverback was an in-basin bolt-on (NOT a leverage-up Eagle Ford entry). Low-decline "
                       "Yeso conventional (8yr PDP life); maint-capex-adj FCF ~12% of equity, div covered 3.5x; borrowing base "
                       "RAISED $400->425M. CAVEAT (IBKR live $34.07, +31% YTD): ALREADY RE-RATED — base FV $40 is only ~+17%, "
                       "NOT the +75% the trap-filter's mis-stated $22 spot implied. Modest upside, WATCH for a pullback to "
                       "the high-$20s. Half-size = commodity-cyclical + 1.7x net-debt.",
             "kill": "WTI <$58 AND a borrowing-base CUT at the Oct-2026 redetermination / net-debt/EBITDAX >2.5x / oil volumes "
                     "roll below ~19,000 Bbls/d absent a divestiture / Permian gas+NGL negative realizations deepen and swamp "
                     "the oil netback (Q1'26 gas -$1.68/Mcf, NGL -$6.22/Bbl = ~21% of volume value-destructive)"},
}
_THIN = {"CRCT", "SBH", "EVER", "REPX"}


def _price(tkr):
    try:
        import yfinance as yf
        c = yf.download(tkr, period="5d", progress=False, auto_adjust=True)["Close"].dropna()
        return round(float(c.iloc[-1].item() if hasattr(c.iloc[-1], "item") else c.iloc[-1]), 2) if len(c) else None
    except Exception:
        return None


def _zone(p, cfg):
    if p is None:
        return "UNKNOWN", "price unavailable"
    start, deep = cfg["entry"]
    bear, base, bull = cfg["fv"]
    if p <= deep:
        return "DEEP-ADD", f"<= {deep} truck zone (bear FV {bear})"
    if p <= start:
        return "ENTRY", f"in {deep}-{start} accumulate band"
    if p <= base:
        return "WATCH", f"above start, below base FV {base} — accumulate on weakness to {start}"
    return "ABOVE", f"> base FV {base} — no action"


def main():
    asof = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"=== SMALL-CAP VALUE BASKET {asof}  (rotation thesis #1; READ-ONLY, no orders) ===")
    print("  rank by conviction: GCT > DFIN > EVER(half) > EPAM(starter) > REPX(half,energy) > SBH > BKE > CRCT  |  cheap-AND-VERIFIED + symmetric-DD diversifier (REPX)")
    rows = []
    for tkr, cfg in BASKET.items():
        p = _price(tkr)
        zone, note = _zone(p, cfg)
        rows.append({"tkr": tkr, "px": p, "zone": zone, "conv": cfg["conv"]})
        bear, base, bull = cfg["fv"]
        up = f"{base / p - 1:+.0%}" if p else "?"
        lim = " [thin — use LIMITS]" if tkr in _THIN else ""
        print(f"\n  {tkr:5} ${p}  -> [{zone}] {note}{lim}")
        print(f"        {cfg['sector']} | conviction {cfg['conv']} | FV bear ${bear}/base ${base}/bull ${bull} "
              f"(base {up}) | entry ${cfg['entry'][0]}-{cfg['entry'][1]}")
        print(f"        thesis: {cfg['thesis']}")
        print(f"        KILL: {cfg['kill']}")
    # delta-alert vs the prior run — so the durable OS-cron output is self-surfacing (no agent needed)
    alerts = []
    if LOG.exists():
        try:
            prev = {p["tkr"]: p for p in json.loads(LOG.read_text().splitlines()[-1]).get("rows", [])}
            for r in rows:
                pr = prev.get(r["tkr"])
                if not pr:
                    continue
                if r["zone"] in ("ENTRY", "DEEP-ADD") and pr.get("zone") not in ("ENTRY", "DEEP-ADD"):
                    alerts.append(f"{r['tkr']} ENTERED {r['zone']} band (${r['px']})")
                if r["px"] and pr.get("px") and r["px"] < pr["px"] * 0.92:
                    alerts.append(f"{r['tkr']} {(r['px']/pr['px']-1)*100:.0f}% vs last run (${r['px']}) — CHECK KILL-TRIGGERS")
        except Exception:
            pass
    with open(LOG, "a") as f:
        f.write(json.dumps({"asof": asof, "rows": rows}, default=str) + "\n")
    if alerts:
        print("\n  >>> ALERTS: " + "  |  ".join(alerts))
    else:
        print("\n  basket: no action (no new entry-band entries, no >8% drops)")
    print(f"[-> {LOG.name}]  accumulate ENTRY/DEEP-ADD within band; half-size EVER; limits on thin names. No orders.")


if __name__ == "__main__":
    main()
