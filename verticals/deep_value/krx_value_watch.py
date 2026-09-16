"""krx_value_watch — band watch for the KRX-listed (Korea) book names. COSMECCA/COSMAX/SILICON2/HUGEL
were band-watched in the DD but had NO standing price watcher — so a crash-week print into the
accumulate band (the 2026-06 KOSPI circuit-breaker week) could pass unseen. This closes that gap.

EXECUTABILITY (corrected 2026-06-29): these ARE IBKR-resolvable on exchange KRX with LIVE two-sided
quotes (COSMECCA verified: bid/ask ~₩70.3k/70.5k intraday, is_close=false) — the earlier "close-only,
not IBKR-executable" tag was a wrong over-generalization of the muni-feed lesson. Caveats that DO hold:
(1) trading requires the IBKR account's Korea/KRX permission to be enabled (foreign-investor setup);
(2) liquidity is foreign-flow-dominated and thin (COSMECCA ADTV ~$4.6M) — size <10-15% of ADTV.
The cron prices via yfinance (headless); for an in-session live mark/quote, use the IBKR `cid` on KRX.
READ-ONLY: this watch never places orders.

Verdict types differ from the US basket — encode them so a band touch reads correctly:
  ACCUM   accumulate-on-weakness name (COSMECCA, COSMAX) — ENTRY/DEEP-ADD = a real buy signal
  NEUTRAL fair-to-mildly-cheap watch (SILICON2 — short dropped 2026-06-30, was a conservative-FV artifact);
          a band touch is a watch trigger, not an action
  EVENT   event-gated (HUGEL control-auction) — band is a reference, action is gated on the event

  python3 verticals/deep_value/krx_value_watch.py
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE / "data" / "krx_value_log.jsonl"
# the dashboard live-prices the KRX book off yfinance, whose Korean (.KQ/.KS) feed lags by DAYS — when TWS
# is up this watch refreshes an authoritative IBKR snapshot here, which the aggregator's _basket prefers.
OVERRIDE = HERE.parents[2] / "desk" / "ui" / "data" / "krx_px_override.json"

# yf=yfinance symbol; cid=IBKR contract_id (exchange KRX, live two-sided); entry=(start, deep);
# fv=(bear, base, bull); verdict ACCUM/AVOID/EVENT (all KRW).
BASKET = {
    "COSMECCA": {"yf": "241710.KQ", "cid": 783906358, "verdict": "ACCUM", "conv": "MED (the edge name)",
                 "entry": (70000, 62000), "fv": (40000, 76000, 108000), "sector": "K-beauty ODM",
                 "thesis": "virality-latency edge (Anua/BYOMA ODM confirmed via openFDA whale-ID); clean DD (unqualified "
                           "audit, top-5 cust <35%, 23% ROE, only profitable dual-region ODM). BASE FV RE-AUDITED 2026-06-30 "
                           "67k->₩76k: we were ~13% too conservative — the MULTIPLE was the bigger error (peer-minus 11x vs a "
                           "warranted 12-12.5x for a 2x-category-growth, higher-margin share-gainer), growth over-faded below "
                           "consensus (anchored to the flat Census aggregate, not COSMECCA's winning book). Earnings-quality "
                           "caution KEPT (receivables the auditor's sole KAM, neg FCF, governance) = FV 76k not back to 82k. "
                           "At ~77k = FAIR-to-slightly-rich (no longer the <62.9k bargain — our OLD FV made a band that never "
                           "triggered); accumulate on a pullback <70k / add <62k. Aug-5 Q2 = re-rate/de-rate trigger.",
                 "kill": "Q2 (Aug-15) confirms Korea export decel to ~12% + OPM <12% -> toward ₩40k bear / founder-undertaking "
                         "or governance (failed KOSPI uplisting) re-surfaces / FCF + RPT note (UNVERIFIABLE pre-size) come back bad"},
    "COSMAX": {"yf": "192820.KS", "cid": 206185926, "verdict": "WAIT", "conv": "MED-LOW (scale-leader)",
               "entry": (135000, 120000), "fv": (110000, 185000, 245000), "sector": "K-beauty ODM (scale leader)",
               "thesis": "scale-leader K-beauty ODM ~10x fwd / 0.68x sales; the margin-INFLECTION thesis is REFUTED by Cosmax's "
                         "OWN deck (OP leverage 'decreased' on mix/cost = STRUCTURAL, not fillable-capacity). China RECOVERING "
                         "(+19.6%, profitable) so that drag is dated; US +46% but only ~6% of group. BASE RE-AUDITED 2026-06-30 "
                         "165k->185k: we sat below ALL 25 analysts' 170k floor (conservative-multiple reflex) and under-credited "
                         "net-earnings +312% (below-OP-line: China equity-method + FX) — but we DON'T chase Street 240k because "
                         "the OP-inflection IS data-refuted (1Q26 OP +3% < rev +16%). WAIT — re-rate only when consolidated OP "
                         "growth >= rev growth (deck stops printing 'leverage decreased'); starter <=135k.",
               "kill": "OP leverage stays negative another quarter / China relapses / US stays <10% of group (no mix help)"},
    "SILICON2": {"yf": "257720.KQ", "cid": 720321359, "verdict": "NEUTRAL", "conv": "NEUTRAL / WAIT (short dropped)",
                 "entry": (30000, 24000), "fv": (24000, 44000, 58000), "sector": "K-beauty export aggregator",
                 "thesis": "export AGGREGATOR still growing +41% in 1Q26 (decel 132->85->64->46->60->76->41 but off a HUGE base). "
                           "SHORT-BIAS DROPPED in the 2026-06-30 re-audit — it was itself a conservative-FV artifact: we (1) "
                           "anchored a share-GAINER to the flat Census import-flow ('converging to the run-rate') when the winning "
                           "book compounds above the aggregate, and (2) put a distress 8.4x multiple on a +41% grower, landing base "
                           "32k = ~30% below the Street floor 46k. Corrected base ₩44k (KEEP the ~11x DISTRIBUTOR multiple, not a "
                           "brand multiple — disintermediation is real: Anua/medicube sell direct on Amazon US). At ~fair now: this "
                           "is fair-to-mildly-cheap, NOT a short. Watch, don't press.",
                 "kill": "2Q26 ~Aug-7 YoY decel <25% + OM breaks <15% + a named anchor brand pulls its US distribution = re-opens the bear"},
    "HUGEL": {"yf": "145020.KQ", "cid": 442443814, "verdict": "EVENT", "conv": "EVENT-GATED",
              "entry": (220000, 200000), "fv": (180000, 300000, 430000), "sector": "aesthetics (toxin/filler)",
              "thesis": "47%-margin net-cash toxin franchise (rivals GALD quality); weak stock = JUSTIFIED discount "
                        "(CBC/Aphrodite ~43% control-auction overhang + Korea-discount), NOT undiscovered. China growing, US "
                        "ITC tail de-risked. EVENT-GATED: fresh Jun-19-2026 refi (₩765B, matures Jun-2029) reset the auction "
                        "OUT = 'hold, not sell' — no near-term catalyst; band is a reference, action waits on the control event.",
              "kill": "control-auction resolves (sale = the catalyst; refi-only = dead money) / China toxin approval slips / ITC tail re-opens"},
}
_ACCUM = {"COSMECCA", "COSMAX"}   # names where ENTRY/DEEP-ADD = a genuine accumulate signal


def _price(yf_sym):
    try:
        import yfinance as yf
        c = yf.download(yf_sym, period="5d", progress=False, auto_adjust=True)["Close"].dropna()
        return round(float(c.iloc[-1].item() if hasattr(c.iloc[-1], "item") else c.iloc[-1])) if len(c) else None
    except Exception:
        return None


def _ibkr_prices(basket) -> dict:
    """Live KRX prices from TWS BY contract_id (READ-ONLY — never places orders). Returns {tkr: {px, prior_close}};
    empty if TWS is down (caller falls back to yfinance). On any success, MERGES the dashboard override file so
    the desk shows the authoritative IBKR feed instead of the stale yfinance Korean quote."""
    try:
        from ib_insync import IB, Contract
    except Exception:
        return {}
    ib = IB()
    port = None
    for p in (7496, 7497, 4001, 4002):
        try:
            ib.connect("127.0.0.1", p, clientId=37, timeout=8, readonly=True)
            port = p
            break
        except Exception:
            continue
    if not port:
        return {}
    out = {}
    try:
        ib.reqMarketDataType(1)               # live; degrades to delayed if no KRX live permission
        for tkr, cfg in basket.items():
            cid = cfg.get("cid")
            if not cid:
                continue
            try:
                c = Contract(conId=cid, exchange="KRX")
                ib.qualifyContracts(c)
                tk = ib.reqMktData(c, "", snapshot=True)
                ib.sleep(2.0)
                px = tk.last if (tk.last and tk.last > 0) else (tk.close if tk.close else None)
                pc = tk.close if (tk.close and tk.close > 0) else None
                if px:
                    out[tkr] = {"px": round(float(px)), "prior_close": (round(float(pc)) if pc else None)}
            except Exception:
                continue
    finally:
        ib.disconnect()
    if out:
        asof = datetime.now(timezone.utc).isoformat(timespec="minutes")
        prices = {}
        if OVERRIDE.exists():
            try:
                prices = json.loads(OVERRIDE.read_text()).get("prices", {})
            except Exception:
                prices = {}
        for tkr, v in out.items():
            prices[tkr] = {**v, "asof": asof, "src": "IBKR"}
        OVERRIDE.parent.mkdir(parents=True, exist_ok=True)
        OVERRIDE.write_text(json.dumps({"asof": asof, "src": "krx_value_watch live IBKR", "prices": prices}, indent=1))
    return out


def _zone(p, cfg):
    if p is None:
        return "UNKNOWN", "price unavailable"
    start, deep = cfg["entry"]
    bear, base, bull = cfg["fv"]
    if p <= deep:
        return "DEEP-ADD", f"<= {deep:,} truck zone (bear FV {bear:,})"
    if p <= start:
        return "ENTRY", f"in {deep:,}-{start:,} accumulate band"
    if p <= base:
        return "WATCH", f"above start, below base FV {base:,}"
    return "ABOVE", f"> base FV {base:,} — no action"


def main():
    asof = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"=== KRX-LISTED VALUE BASKET {asof}  (Korea book; IBKR-listed on KRX, live two-sided; READ-ONLY) ===")
    print("  rank: COSMECCA(accum) > COSMAX(wait) | SILICON2 = NEUTRAL/watch (short dropped) | HUGEL = event-gated")
    print("  NOTE: tradeable on IBKR/KRX IF account Korea-permission enabled; KRW, foreign-flow-dominated + thin — size <10-15% ADTV")
    ib_px = _ibkr_prices(BASKET)
    if ib_px:
        print(f"  PRICE SOURCE: live IBKR (TWS) — refreshed dashboard override {OVERRIDE.name} ({len(ib_px)}/{len(BASKET)} names)")
    else:
        print("  PRICE SOURCE: yfinance fallback (TWS down) — dashboard keeps the last good IBKR override; note Korean .KQ/.KS lags ~days")
    rows = []
    for tkr, cfg in BASKET.items():
        p = (ib_px.get(tkr) or {}).get("px") or _price(cfg["yf"])
        zone, note = _zone(p, cfg)
        rows.append({"tkr": tkr, "px": p, "zone": zone, "verdict": cfg["verdict"]})
        bear, base, bull = cfg["fv"]
        up = f"{base / p - 1:+.0%}" if p else "?"
        px_s = f"₩{p:,}" if p else "₩?"
        # signal-ready per-name line:  TKR  ₩price  [VERDICT] -> ZONE note
        print(f"\n  {tkr:9} {px_s:>10}  [{cfg['verdict']}] -> {zone}  {note}")
        print(f"        {cfg['sector']} | {cfg['conv']} | FV bear ₩{bear:,}/base ₩{base:,}/bull ₩{bull:,} "
              f"(base {up}) | entry ₩{cfg['entry'][0]:,}-{cfg['entry'][1]:,}")
        print(f"        thesis: {cfg['thesis']}")
        print(f"        KILL: {cfg['kill']}")
    # delta-alerts vs prior run — only ACCUM names emit a buy-band alert; all names emit a hard-move alert
    alerts = []
    if LOG.exists():
        try:
            prev = {p["tkr"]: p for p in json.loads(LOG.read_text().splitlines()[-1]).get("rows", [])}
            for r in rows:
                pr = prev.get(r["tkr"])
                if not pr:
                    continue
                if r["tkr"] in _ACCUM and r["zone"] in ("ENTRY", "DEEP-ADD") and pr.get("zone") not in ("ENTRY", "DEEP-ADD"):
                    alerts.append(f"{r['tkr']} ENTERED {r['zone']} band (₩{r['px']:,}) — accumulate (IBKR/KRX, <10-15% ADTV)")
                if r["px"] and pr.get("px") and r["px"] < pr["px"] * 0.92:
                    tag = "covers short tgt" if r["verdict"] in ("AVOID", "SHORT") else "CHECK KILL-TRIGGERS"
                    alerts.append(f"{r['tkr']} {(r['px']/pr['px']-1)*100:.0f}% vs last run (₩{r['px']:,}) — {tag}")
        except Exception:
            pass
    with open(LOG, "a") as f:
        f.write(json.dumps({"asof": asof, "rows": rows}, default=str) + "\n")
    if alerts:
        print("\n  >>> ALERTS: " + "  |  ".join(alerts))
    else:
        print("\n  basket: no action (no new accumulate-band entries, no >8% drops)")
    print(f"[-> {LOG.name}]  ACCUM names buy-in-band via IBKR/KRX (Korea-permission + <10-15% ADTV); SILICON2 neutral/watch; HUGEL event-gated. No orders.")


if __name__ == "__main__":
    main()
