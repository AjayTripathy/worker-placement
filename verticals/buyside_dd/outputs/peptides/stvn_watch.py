"""stvn_watch — combined STVN entry watch (READ-ONLY, no orders). Two signals:
  (1) PRICING: STVN price vs the entry band (from the diligence + the $13-anchor correction),
      with LLY/NVO for the leadership-pair context. Daily.
  (2) FACTORY: Stevanato Fishers + Latina hiring-velocity ramp (margin-inflection leading proxy).
      Refreshed weekly (skipped if last snapshot < 6 days old, to be polite to LinkedIn).

Entry band (corrected off the stale $13 bear anchor):
  >  $17.0  ABOVE base FV — no action
  $15.5-17  APPROACHING — start watching the factory ramp closely
  $13.5-15.5 ENTRY ZONE — buy here IF the operator-hiring taper / margin inflection is confirming
  <  $13.5  DEEP / bear FV — strong unless thesis broke
Demand is already de-risked (whale-ID: Lilly-anchored 93%); the gate is price + the margin inflection.
"""
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))   # .../signalos repo root (peptides->outputs->buyside_dd->verticals->signalos)
from verticals.buyside_dd.connectors.hiring_velocity import fetch_postings, ramp_metrics, _classify
from verticals.buyside_dd.connectors.customer_id import census_trade_flow

WATCH_LOG = HERE / "stvn_watch_log.jsonl"
HIRE_LOG = HERE / "hiring_velocity_log.jsonl"
SITES = [("Stevanato Fishers IN", "Fishers, Indiana"), ("Stevanato Latina IT", "Latina, Italy")]

# Aesthetics fleet (the GLP-1-face/body book). entry=(buy_below, add_below); fv=(bear,base,bull).
# Only buy inside the entry band AND on the named catalyst confirming. Ranked ESTA>GALD>EOLS>LFMD>INMD.
BOOK = {
    "ESTA": {  # Establishment Labs — body/implant pure-play; refi wall pushed to 2031 (Oaktree $300M)
        "ccy": "$", "kind": "WAIT", "entry": (74, 70), "fv": (58, 92, 120), "regime": "DISCOVERING (SI 13% = squeeze-fuel, do-NOT-short)",
        "thesis": "highest-growth body/implant pure-play; refi RESOLVED to 2031; FCF+ H2-26. GLP-1-body = narrative (co. lists as RISK).",
        "catalyst": "2026-08-05 Q2 earnings (FCF inflection); buy low-$70s, add <$70."},
    "GALD": {  # Galderma — quality GLP-1-face (owns Sculptra biostim); EQT exit cleared; fully priced
        "ccy": "CHF", "yf": "GALD.SW", "kind": "WAIT", "entry": (145, 130), "fv": (120, 178, 225), "regime": "DISCOVERED_CROWDED",
        "thesis": "highest-quality GLP-1-face owner (Sculptra biostimulator); ~37x 26E EBITDA = fully priced; demand air-pocket.",
        "catalyst": "2026-08 H1-26 results; buy only on pullback to CHF 130-145."},
    "HUGEL": {  # Hugel 145020.KQ — Korean toxin/Letybo; great franchise, control-auction overhang = justified discount
        "ccy": "KRW", "yf": "145020.KQ", "kind": "EVENT-GATED", "entry": (220000, 200000), "fv": (180000, 300000, 430000),
        "regime": "DISCOVERED / discount-justified (foreign-crowding workaround: foreign-OWN 41%, marginal flow = foreign SELLING)",
        "thesis": "47%-margin net-cash toxin franchise (rivals GALD quality); weak stock = JUSTIFIED discount (CBC/Aphrodite ~43% control-auction overhang + Korea-discount), NOT undiscovered. China growing, US ITC tail de-risked.",
        "catalyst": "control-auction RESET OUT: fresh Jun-19-2026 refi (KRW765B, matures Jun-17-2029) = 'hold, not sell'. Base case sale H1-2028 (re-market 2027). NO near-term catalyst. Tells: 400k-ask price CUT / DART block-trade filing / new refi."},
    "INMD": {  # InMode — RF/body device; CEO-led $16.20 take-private (conflicted); 57% mktcap is cash
        "ccy": "$", "kind": "EVENT-GATED", "entry": (13, 12), "fv": (11, 16.2, 18.5), "regime": "MBO-arb (take-under)",
        "thesis": "CEO-led $16.20 take-private (Jun-15 vote); ~$8.4/sh cash; conflicted take-under + class action + ITC. GLP-1-body UNVERIFIABLE.",
        "catalyst": "2026-06-15 MBO vote; standalone-value add only <$13."},
}

# Wellness sleeve (general healthspan trends, beyond aesthetics). All 4 deep-dived 2026-06-26;
# each CAUGHT stale screen framing (mcaps off 2-3x, catalyst misID). Rank INSP > PGNY > PRCT > VERU.
WELLNESS = {
    "INSP": {  # Inspire — sleep-apnea neurostim; 2025 collapse was a CPT-coding gap NOT GLP-1; net-cash floor
        "ccy": "$", "kind": "WAIT", "entry": (42, 38), "fv": (30, 60, 95),
        "regime": "dislocation, event-gated (-53% YTD; ~$400M net-cash floor; short FADING 12.7% not building)",
        "thesis": "sleep-apnea hypoglossal neurostim; 2025 collapse = lost Medicare CPT code (NOT GLP-1); GLP-1 net-EXPANDS dx funnel; Inspire V margin-accretive (86.5% GM). Bear time-boxed ~18mo.",
        "catalyst": "Sept-2026 AMA CPT panel = THE binary (Cat-I code -> Jan-2028 re-rate); Q2 ~Aug = guided max-pain trough."},
    "WST": {  # West Pharma — elastomer/Daikyo components in every GLP-1 pen; verified tailwind but at recovery TOP
        "ccy": "$", "kind": "WAIT", "entry": (290, 255), "fv": (249, 320, 432),
        "regime": "quality-compounder at RECOVERY TOP (40x fwd, ~1.6% under 52wk high; round-tripped the 2025 destocking crash)",
        "thesis": "most VERIFIABLE GLP-1 tailwind — HVP ~60% of sales, destocking OVER (Q1 +15% organic, RAISED FY26), regulatory re-filing moat. Real tail = ORAL-GLP-1 (orforglipron) compresses the multiple YEARS before volumes fall. Undisclosed whale 15.8% (Novo/Lilly).",
        "catalyst": "Q2 ~Jul-23 beat-and-raise (P0.97, re-rate-confirm) | THREAT: Lilly orforglipron/oral-GLP-1 milestones thru 2026 (multiple-compression). Dislocation buy = $190-230 destocking-crash zone."},
    "PGNY": {  # Progyny — fertility benefits; the feared client cliff already absorbed; quality buyback compounder
        "ccy": "$", "kind": "WAIT", "entry": (23, 20), "fv": (18, 28, 40),
        "regime": "quality-compounder, CLEAN, debt-free; macro-beta = tech employment; NOT undiscovered (~21x GAAP/13x adj, fair)",
        "thesis": "category-leader fertility benefits; feared Alphabet client-loss ALREADY happened & absorbed (+10% FY25 through it); ~$310M cash no debt, ~9% shares retired/6mo; low-teens EPS compounder. Utilization = the open risk.",
        "catalyst": "2026 selling-season client adds (Sep-Nov) = re-rate event; Q2 print ~Aug = utilization tell."},
    "PRCT": {  # PROCEPT — men's-health BPH Aquablation robotics; utilization-per-system declining = the crux
        "ccy": "$", "kind": "WAIT", "entry": (19, 17), "fv": (12, 24, 42),
        "regime": "de-rated unprofitable MedTech (-65% from high, ~2.5x EV/sales); high-beta, capex-cyclical",
        "thesis": "men's-health BPH Aquablation robot; cheap after 6 analyst cuts BUT utilization-per-system DECLINING + flat US BPH market = cyclical(self-inflicted realignment) vs structural(saturation) coin-flip. EAU/AUA guideline upgrades already fired, didn't stop the de-rate.",
        "catalyst": "Q2-2026 print ~late-Jul/Aug (procedures-per-system re-accel = re-rate) + Q4-2026 EBITDA inflection (~55% odds, removes 2027 dilution)."},
    "BRBR": {  # BellRing — Premier Protein RTD; GLP-1 helps VOLUME but margin broke (commoditization)
        "ccy": "$", "kind": "SHOW-ME", "entry": (9.0, 7.5), "fv": (6, 12.5, 21),
        "regime": "broken compounder (-81%/12mo; $1.3B stub NOT $8B; IV ~99%); show-me turnaround, leveraged ~3.5x",
        "thesis": "GLP-1 IS demand-helpful (RTD volume +11.7%) but can't convert to margin: Adj-GM 34.5%->22.7%, price-mix -9% (buying volume w/ promos), FY26 EBITDA guide CUT ~28%. Real bear = protein-RTD commoditization + 74% customer concty (Walmart/Costco/Amazon) + leverage. Short right for the wrong reason.",
        "catalyst": "Q3 FY26 ~Aug-4-6 (P0.97 down-skew): price/mix narrowing toward -5% + Adj-GM inflecting = repair -> $7.50-9 pays; another cut/<=-8% = short confirmed -> $5-8. FY27 guide Q4 ~Nov = re-rate fulcrum."},
    "HIMS": {  # Hims & Hers — best telehealth franchise but NOT ownable; compounding cliff + Novo blow-up + governance
        "ccy": "$", "kind": "SHOW-ME", "entry": (22, 18), "fv": (15, 26, 42),
        "regime": "DISCOVERED_CROWDED (-55% from high; crowded-long); NOT ownable on price alone",
        "thesis": "best franchise but the bear is already in the Q1 10-Q: growth +111%->+3.8%, US rev DECLINED -8.4% (all 'growth' = ZAVA M&A), GM 73->65%. GLP-1 compounding cliff HERE (FDA named Hims; $33.5M WL restructuring); Novo terminated+sued (dismissed w/o prejudice = refile risk)+securities suits; founder 175-vote/sh control. Premium vs LFMD NOT justified — do NOT pair.",
        "catalyst": "Q2 ~early-Aug (first full qtr under WL restructuring, decisive). OWNABLE only <=$22 AND 2 quarters US (not-M&A) re-accel w/ GM>=68% AND no live Novo injunction. Bull lever = new branded/oral-GLP-1 supply deal (watch 8-Ks)."},
    "VERU": {  # Veru — enobosarm GLP-1 muscle-preservation; science-OK but $3 warrant-wall structure-trap
        "ccy": "$", "kind": "BINARY", "entry": (2.40, 1.80), "fv": (0.60, 2.80, 7.0),
        "regime": "SCIENCE-OK / STRUCTURE-TRAP; single-asset binary; twice-burned (COVID/sabizabulin), NOT undiscovered",
        "thesis": "enobosarm preserves lean mass on GLP-1 (best SARM muscle data in 15yr, honestly disclosed) BUT Oct-2025 raise layered $3.00 warrant wall (as-conv ~41.8M ~2.6x) capping upside; cash $27.6M ~3.7q runway. FDA endpoint = incremental weight loss, NOT 'muscle preservation'.",
        "catalyst": "PLATEAU 34-wk interim ~Q1-2027 (NCT07446998); P(pos)~0.65; dilutive raise likely around it. Accumulate ONLY $1.80-2.40 (below warrant wall) as a sized binary."},
}

# Cosmeceutical sleeve (clinical/active skincare — de-anchored from GLP-1). 4 deep-dived 2026-06-26;
# again every screen input had a material error (BEISY ticker/mcap, ODD float-artifact, CRDA label,
# ELF net-cash->net-debt). Rank BEISY > ELF > CRDA > ODD; anchors LRLCY/EL, deep-value SKIN.
COSMECEUTICAL = {
    "BEI.DE": {  # Beiersdorf — Eucerin/Aquaphor Derma moat (PATENTED Thiamidol) at a DECADE LOW. NOTE: 'BEISY' is NOT a real ticker (carried from the screen); trade BEI.DE/XETRA (IBKR sym BEI@IBIS); US ADR BDRFY=dead
        "ccy": "EUR", "yf": "BEI.DE", "kind": "WAIT", "entry": (72, 66), "fv": (60, 79, 100),
        "regime": "de-rated quality dislocation (-45% from peak, decade low; net-cash ~EUR4B; maxingvest 52% controlled; FOREIGN positioning-blind — trade XETRA EUR, the 'BEISY' ADR is DEAD/use BDRFY=untradeable)",
        "thesis": "NOT the durable compounder LRLCY is — it's a TURNAROUND: the GROUP is SHRINKING (organic -4.6% Q1-26), NIVEA 56% losing W-Europe share, La Prairie -15%. Derma (Eucerin/Aquaphor +11.7% on PATENTED Thiamidol) is a real moat but only 15% & can't offset. Own-now case = CHEAP + FLOORED (decade low, ~EUR4B net cash floor at bear EUR60), NOT 'fair value of a compounder'. Re-rate gated on the UNPROVEN NIVEA inflection.",
        "catalyst": "H1-2026 ~Aug-6; re-rate trigger = NIVEA W-Europe monthly market-share INFLECTION (Derma already believed). BUY-SMALL the floored dislocation <=72, scale lower; durability unproven so size it small."},
    "ELF": {  # e.l.f. — cleanest QUANTIFIED skinification (skincare 9->23%); Rhode/Naturium; US-liquid
        "ccy": "$", "kind": "WAIT", "entry": (55, 48), "fv": (40, 68, 105),
        "regime": "real thesis, fair-not-cheap (~2.8x sales, ~20x adj-P/E; net DEBT ~$552M; runs near GAAP breakeven mid-Rhode-integration); US-liquid = most actionable of the sleeve",
        "thesis": "cleanest QUANTIFIED skinification (skincare 9->23% of mix); Rhode acq $390M +80% at cheap 2.3x, Naturium 2x. Tariff bear WEAKER than consensus (SCOTUS voided IEEPA-reciprocal Feb-26; only 25% Sec-301 structural; price raises -> Q4 GM +140bps). BUT decel confirmed (FY27 +12-14% vs FY26 +25%, core color +4%).",
        "catalyst": "Q1 FY27 ~Aug (first clean organic-vs-acq split, swing); Rhode->Sephora Europe 19-mkt Sept = re-rate trigger. Accumulate $48-55."},
    "CRDA": {  # Croda — beauty-ACTIVES picks-and-shovels BUT only ~1/6 of group; quality cyclical; trade LSE
        "ccy": "GBp", "yf": "CRDA.L", "kind": "WAIT", "entry": (2900, 2700), "fv": (2400, 3375, 4200),
        "regime": "quality-cyclical chemical (NOT a structural-skincare pure-play); positioning-blind — trade LSE GBP (COIHY ADR unusable)",
        "thesis": "'purest cosmetic-actives shovel' label REFUTED — Beauty Actives is ~15-20% of group (~1/6); rest cyclical (Industrial -4.6%, Life Sciences destock + COVID-lipid unwind, GBP44.6M impair). De-rate from the 2021 lipid-bubble is earnings-driven & CORRECT. Fairly priced — not a trap, not a bargain.",
        "catalyst": "H1-2026 28-Jul; real re-rate = >20% group-margin target by FY2028 (~6% EPS/100bp). Accumulate on weakness 2700-2900p."},
    "ODD": {  # Oddity — owned-R&D (Oddity Labs REAL) but paid-social platform-dependency wound; spec turnaround
        "ccy": "$", "kind": "SHOW-ME", "entry": (11, 9), "fv": (7, 14.5, 28),
        "regime": "speculative turnaround (-82% from high; econ mcap ~$813M, EV ~$696M ~0.86x sales, $550M convert); platform-dependency repriced",
        "thesis": "Oddity Labs IS real (Revela acq, Boston lab ~45 staff, 8 owned-molecule products to mkt 2026) but $0 of FY25 rev depended on it = option not yet moat. Bear PRINTED Feb-26: Meta algo change spiked CPA 1.5->2.8, withdrew guidance, Q1-26 rev -26%, first net loss. First-party data doesn't insulate top-of-funnel CAC.",
        "catalyst": "Q2-2026 ~early-Aug = THE trigger (CPA rollback toward ~2.0 = re-rate; stays ~2.8/another cut = de-rate). Asymmetry attractive only <$10 near cash."},
    "LRLCY": {  # L'Oreal OR.PA — highest-QUALITY cosmeceutical, but WAIT: fair-not-cheap (28x for ~5% growth)
        "ccy": "EUR", "yf": "OR.PA", "kind": "WAIT", "entry": (375, 350), "fv": (310, 400, 455),
        "regime": "highest-QUALITY but FAIR-NOT-CHEAP (own-now WALKED BACK 2026-06-26): ~28x fwd for only MID-SINGLE-DIGIT organic (~5-6% LFL) = ~5x PEG, reported rev ~FLAT (FX drag); '5% below its own 30-40x history' is a relative crutch (that band was a low-rate artifact). Best-in-class (20% op margin/18% ROE/near-unlevered/EUR7.2B FCF) but thin MoS; thesis leans on the multiple HOLDING. Trade Paris EUR (LRLCY ADR unsponsored)",
        "thesis": "OWNS the derm moat (CeraVe/La Roche-Posay/SkinCeuticals/Vichy: +5.5% LFL, 26.1% margin, 3 brands >EUR1B); GALD derm air-pocket didn't reach it (dermo-cosmetics, not injectables); raised Galderma stake to 20% = aesthetics call-option. BUT it's a low-mid-single-digit grower at a premium multiple — quality-compounder/TINA case justifies a FAIR multiple, NOT paying up for slowing growth. Same bucket as GALD/PGNY: quality at full price, wait for the dip.",
        "catalyst": "WAIT for a pullback — start EUR350-375, real own-now only on a EUR320 dislocation; do NOT pay 28x at spot ~388. Downside trigger = rate-regime multiple compression (the thin-MoS risk), not the franchise."},
}

# Korean (K-beauty) cosmeceutical sub-sleeve. 3 deep-dived 2026-06-26 w/ FOREIGN-CROWDING WORKAROUND +
# the Census HS3304 KR->US import tell (1.13x, no surge = real but NOT parabolic — load-bearing in all 3).
# Rank COSMECCA > COSMAX > SILICON2. Anchors: Amorepacific (turnaround), VT (spec), APR/Medicube (watch/FADE).
KBEAUTY = {
    "COSMECCA": {  # 241710.KQ — clean diversified K-beauty ODM; FULL DD = fairly valued, accumulate LOWER
        "ccy": "KRW", "yf": "241710.KQ", "kind": "ACCUM<62.9k", "entry": (62900, 54000), "fv": (40000, 67000, 110000),
        "regime": "DISCOVERED (foreign-own 6%->22.7%) but flow read OK (foreigners still NET BUYING, marginal seller=domestic NPS, short book 0.21%=no bear); -38% = Feb parabola-break + SECTOR ODM de-rate + LIVE macro crash, NOT company-specific; net DEBT ~120B (not net cash); KRX-direct",
        "thesis": "FULL DD (6 work-streams): CLEAN business (unqualified audit, RPT clean, top-5 cust<35% verified via openFDA whale-ID: Anua/BYOMA/Bass Pro/L'Oreal) at ROUGHLY FAIR VALUE — base FV revised 82k->67k (screen pulled the bull-yr EPS forward + applied a peer-PREMIUM multiple). Census HS3304 boom DECELERATING (2024 +54% -> 2025 +5.7% -> 2026 ~flat); the +56% is base-effect share-gain = fade it, underwrite 15-20%. Englewood/onshoring REAL but small/slow/low-margin (US-Totowa +12% 6%OM; the engine is its KOREA sub) = ~3-5% of FV option, not a pillar. Net debt + FY25 FCF NEGATIVE + governance (failed KOSPI uplisting on spousal co-CEO) cap it.",
        "catalyst": "NOT a buy at 66.5k (prob-wtd EV ~+5%, -40% bear tail). Accumulate: starter <=62,900 / core 58-60k / add 52-54k; invalidate <52k. Mid-Aug Q2 = re-rate(OPM 13-14%+Englewood>=15%+Korea>30%) vs unwind(Korea->12%+OPM<12%). Pre-size pulls: RPT note + clean FCF (both UNVERIFIABLE)."},
    "COSMAX": {  # 192820.KS — cheap scale-leader ODM BUT margin-inflection REFUTED by own deck; leverage
        "ccy": "KRW", "yf": "192820.KS", "kind": "WAIT", "entry": (135000, 120000), "fv": (110000, 165000, 230000),
        "regime": "DISCOVERED crowded large-cap (foreign-own 38.3%, ROSE through the -47% year); cheap-for-EARNED-reasons (~2.9x liab/equity, neg working capital); 52w low",
        "thesis": "scale-leader K-beauty ODM ~10x fwd / 0.68x sales BUT the margin-inflection thesis is REFUTED by Cosmax's OWN deck (OP leverage 'decreased' on mix/cost = STRUCTURAL, not fillable-capacity). China RECOVERING (+19.6%, turned profitable) so the drag is dated; US +46% but only ~6% of group. Consensus TP 248k ABOVE the bull case = Street priced for the leg the data refutes.",
        "catalyst": "Q2 ~mid-Aug; re-rate ONLY when consolidated OP growth >= rev growth (deck stops 'leverage decreased'); P~0.30 at Q2, ~0.45 in 2 quarters. Starter only <=135k as a capitulation option."},
    "SILICON2": {  # 257720.KQ — K-beauty export aggregator; momentum vehicle, parabola rolling over = AVOID
        "ccy": "KRW", "yf": "257720.KQ", "kind": "AVOID", "entry": (22000, 18000), "fv": (20000, 32000, 54000),
        "regime": "momentum vehicle ALREADY rolling over (-53% from high; retail-driven ~8.6% foreign; 7 analysts BUY w/ TP +92% not yet cut = late-cycle estimates-follow-decel)",
        "thesis": "K-beauty export AGGREGATOR but PARABOLA ROLLING OVER: growth 132->85->64->46->60->76->+41.1% (1Q26, lowest in 8q), converging to the import-flow run-rate the Census 1.13x predicted; margins compressing (OM 22.8->18.6%). 'Purest US beta' MIS-anchored (Europe #1 34%, NA #2 24%); thin-margin redistribution wholesaler (93%), disintermediation risk (Anua/BoJ/medicube sell direct on Amazon US).",
        "catalyst": "2Q26 ~Aug-7 DECISIVE: de-rate if YoY<30% / OM<17% -> 2nd leg to 20-24k; re-rate only if YoY re-accel >45% + Europe inflection. Fade-the-bounce; NO entry at spot."},
}


def _book_zone(p, cfg):
    if p is None:
        return "UNKNOWN — price unavailable"
    add, deep = cfg["entry"]
    bear, base, bull = cfg["fv"]
    if p <= deep:
        return f"ADD ZONE (<= {cfg['ccy']}{deep}) — high-conviction add unless thesis broke"
    if p <= add:
        return f"ENTRY ZONE ({cfg['ccy']}{deep}-{add}) — start the position on catalyst confirm"
    if p <= base:
        return f"WATCH ({cfg['ccy']}{add}-{base}) — fair-to-base; wait for the pullback band"
    return f"ABOVE base FV (> {cfg['ccy']}{base}) — no action"


def _eols_inventory():
    """EOLS quarterly inventory via SEC XBRL — the tariff-stockpile tell. Returns
    {latest_period, latest_$M, prior_peak_$M, filed, stockpile_flag, series}."""
    import requests
    H = {"User-Agent": "SignalOS Research admin@signalos.io"}
    try:
        tk = requests.get("https://www.sec.gov/files/company_tickers.json", headers=H, timeout=20).json()
        cik = next((str(v["cik_str"]).zfill(10) for v in tk.values() if v["ticker"] == "EOLS"), None)
        u = requests.get(f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/InventoryNet.json",
                         headers=H, timeout=20).json().get("units", {}).get("USD", [])
        seen = {}
        for x in u:
            if x.get("form") in ("10-Q", "10-K"):
                seen[x["end"]] = (x["val"], x.get("filed"))
        ends = sorted(seen)
        if not ends:
            return None
        latest = ends[-1]; lv, filed = seen[latest]
        peak = max(v[0] for v in seen.values())
        # stockpile = latest materially above the prior (pre-latest) peak
        prior_peak = max([v[0] for e, v in seen.items() if e != latest] or [0])
        flag = "STOCKPILE_BUILD" if lv > prior_peak * 1.15 else ("ELEVATED" if lv > prior_peak * 0.95 else "normal")
        return {"period": latest, "inv_M": round(lv / 1e6, 1), "prior_peak_M": round(prior_peak / 1e6, 1),
                "filed": filed, "flag": flag,
                "series": {e: round(seen[e][0] / 1e6, 1) for e in ends[-6:]}}
    except Exception as e:
        return {"error": str(e)[:80]}


def _price(tkr):
    try:
        import yfinance as yf
        d = yf.download(tkr, period="5d", progress=False, auto_adjust=True)
        c = d["Close"].dropna()
        return round(float(c.iloc[-1].item() if hasattr(c.iloc[-1], "item") else c.iloc[-1]), 2) if len(c) else None
    except Exception:
        return None


def _zone(p):
    if p is None:
        return "UNKNOWN", "price unavailable"
    if p > 17.0:
        return "ABOVE", "above base FV — no action"
    if p > 15.5:
        return "APPROACHING", "watch the factory ramp closely"
    if p > 13.5:
        return "ENTRY_ZONE", "BUY if operator-hiring taper / margin inflection confirms"
    return "DEEP", "bear FV — strong entry unless thesis broke"


def _hiring_is_stale(days=6):
    if not HIRE_LOG.exists():
        return True
    try:
        rows = [json.loads(l) for l in HIRE_LOG.read_text().splitlines() if l.strip()]
        last = max(date.fromisoformat(r["asof"]) for r in rows)
        today = max(last, last)  # no Date.now reliance; use newest log date as anchor if needed
        return (date.fromisoformat(datetime.now(timezone.utc).strftime("%Y-%m-%d")) - last).days >= days
    except Exception:
        return True


def main():
    asof = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    stvn, lly, nvo = _price("STVN"), _price("LLY"), _price("NVO")
    zone, note = _zone(stvn)

    print(f"=== STVN WATCH {asof} ===")
    print(f"STVN ${stvn}  -> {zone}: {note}")
    print(f"  context: LLY ${lly} / NVO ${nvo}  (leadership: long-LLY / underweight-NVO)")
    print(f"  entry band: >17 above | 15.5-17 approaching | 13.5-15.5 ENTRY | <13.5 deep")

    hiring_summary = {}
    if _hiring_is_stale():
        print("\n-- factory ramp (weekly refresh) --")
        for label, loc in SITES:
            rows = fetch_postings("Stevanato OR Ompi", loc, company_filter=("stevanato", "ompi"))
            m = ramp_metrics(rows)
            hiring_summary[label] = {"n_open": m["n_open"], "production_share": m["production_share"],
                                     "posted_last_30d": m["posted_last_30d"]}
            with open(HIRE_LOG, "a") as f:
                f.write(json.dumps({"asof": asof, "site": label, "source": "linkedin_guest", **m,
                        "titles": [{"t": r["title"], "cls": _classify(r["title"]), "posted": r.get("posted")}
                                   for r in rows]}, default=str) + "\n")
            print(f"  {label}: {m['n_open']} reqs, {m['production_share']:.0%} production, "
                  f"{m['posted_last_30d']} fresh(30d)")
    else:
        print("\n-- factory ramp: snapshot < 6d old, skipping (weekly cadence) --")

    # --- EOLS (medspa/aesthetics turnaround) — price + the tariff-stockpile inventory tell ---
    eols = _price("EOLS")
    inv = _eols_inventory()
    print(f"\n=== EOLS WATCH {asof} ===")
    print(f"EOLS ${eols}  (buy-rated small/spec; pullback entry ~$5-6; Oct $7.5 put -> ~$6 net basis)")
    if inv and "error" not in inv:
        print(f"  inventory tell: {inv['period']} = ${inv['inv_M']}M (prior peak ${inv['prior_peak_M']}M) "
              f"[{inv['flag']}] filed {inv['filed']}")
        print(f"    series($M): {inv['series']}")
        print(f"    WATCH: Q2 (Jun-30) 10-Q ~Aug 5 -> inventory breaking >~$33M/4mo = tariff pre-buy REAL "
              f"(mitigation executing); flat ~$25M = exposed, year-end 'update' hollow.")
    # LEADING tell: Census air-imports (Korea->US botulinum HS3002.49) — the only channel that sees the
    # air-freighted Jeuveau; surges ~5wk-lagged, AHEAD of the Aug filings. Decisive months = May-Sep.
    tf = census_trade_flow("300249", "south korea", mode="air")
    air = None
    if tf.get("status") == "OK":
        air = {"latest": tf["latest_month"], "velocity": tf["velocity_vs_baseline"], "surge": tf["surge"]}
        print(f"  air-import tell (Census, LEADING): {tf['latest_month']} velocity {tf['velocity_vs_baseline']}x "
              f"vs baseline -> {'SURGE = stockpiling' if tf['surge'] else 'no surge yet'} "
              f"(recent ${tf['recent_3mo_avg_M']}M vs base ${tf['baseline_avg_M']}M; 100% air)")
        print(f"    watch May-Sep months (post ~5wk lag) for velocity breaking >1.25x = pre-tariff pre-buy.")
    else:
        print(f"  air-import tell (Census): {tf.get('status')} — {tf.get('note','')}")
    # --- EOLS catalyst calendar: the dated tariff-durability tells (when does the under-priced re-rate fire) ---
    from datetime import date as _d
    today_d = _d.fromisoformat(asof)
    EOLS_CATALYSTS = [
        ("2026-08-05", "Q2 10-Q — June-30 inventory (stockpile/deferral tell)"),
        ("2026-09-29", "Section 232 tariff EFFECTIVE (15% Korea/Jeuveau)"),
        ("2026-11-05", "Q3 10-Q — Sept-30 inventory (at/after tariff)"),
        ("2026-12-15", "year-end tariff 'update' (does 'longer-term solution' get a noun?)"),
        ("2027-02-25", "Q4/FY26 earnings + 2027 GUIDANCE = the durability RE-RATE catalyst"),
    ]
    upcoming = sorted([(c, (_d.fromisoformat(c[0]) - today_d).days) for c in EOLS_CATALYSTS],
                      key=lambda z: z[1])
    upcoming = [(c, d) for c, d in upcoming if d >= -3]
    print("  catalyst calendar:")
    for (dt, label), dleft in upcoming[:4]:
        mark = "  <<< IMMINENT" if 0 <= dleft <= 21 else ""
        print(f"    {dt}  T{'+' if dleft>=0 else ''}{dleft:>4}d  {label}{mark}")

    # --- LFMD (telehealth, contrarian-value satellite behind EOLS) — price band + Q2 swing catalyst ---
    lfmd = _price("LFMD")
    lz = ("ENTRY $3.0-3.5 (margin of safety)" if lfmd and 3.0 <= lfmd <= 3.5 else
          "DEEP <$3 (bear floor — strong unless thesis broke)" if lfmd and lfmd < 3.0 else
          "WAIT >$3.5 (fair-to-rich; don't pay base FV for an unproven turn)" if lfmd else "?")
    print(f"\n=== LFMD WATCH {asof} ===")
    print(f"LFMD ${lfmd} -> {lz}")
    print(f"  bear $2.5-3 / base $4-4.5 / bull $7-9 | ~0.8x rev vs HIMS 2.8x | NOT a HIMS margin-trap (GM 84->88%)")
    print(f"  SWING: Q2-2026 earnings ~Aug 5 -> adj EBITDA inflecting + ARPU stabilizing = CONFIRM (buy up to ~$5); "
          f"miss/ARPU sliding = bear. Small satellite, behind EOLS.")
    # LEADING tell (highest-information): RexMD(high-ARPU men's) vs LifeMD(low-ARPU weight) web-traffic split.
    # RexMD stabilizing -> P(confirm) up, go long; RexMD falling -20%+/mo -> down lean. SimilarWeb is gated
    # from this egress, so last-known + REFRESH-via-agent (the cron can re-pull rexmd.com/lifemd.com MoM).
    # CORRECTED 2026-07-10 (male-DTC run): the prior -0.37/+0.24 was INVERTED (transposed brands).
    # SimilarWeb June-2026 re-pull: rexmd.com +10.2% MoM (men's brand GROWING), lifemd.com -24.6% MoM.
    # This is CONSISTENT with filings ("RexMD returned to growth" Q3-25; ED personalized +40% QoQ Q1-26):
    # the high-ARPU men's core is NOT collapsing — blended ARPU (-21% YoY) falls from low-ARPU weight/women's
    # cohort MIX, not RexMD attrition. Sign flip => the leading tell now leans LONG, not down. (single-source, MoM-noisy)
    tr = {"asof": "2026-06", "rexmd_mom": 0.102, "lifemd_mom": -0.246, "source": "SimilarWeb 2026-07-10 re-pull"}
    rx, lf = tr["rexmd_mom"], tr["lifemd_mom"]
    read = ("RexMD GROWING (men's core intact) -> ARPU dilution is MIX not attrition, lean LONG" if rx > -0.10 else
            "RexMD FALLING hard -> ARPU dilution ongoing, lean DOWN/wait")
    print(f"  web-traffic tell ({tr['asof']}, {tr['source']} — REFRESH SimilarWeb rexmd.com/lifemd.com): "
          f"RexMD {rx:+.0%}/mo, LifeMD {lf:+.0%}/mo -> {read}")

    # --- BOOKS OF WATCHES: aesthetics fleet + wellness sleeve. Each name is a WATCH (entry band + FV
    # bracket + dated catalyst); none is a market-order trigger. Conviction-order ≠ actionability — the
    # [TIER]+gap shows what's actually doable now (WAIT / BINARY / EVENT-GATED / accumulate). ---
    def _emit_book(title, rank, d):
        print(f"\n=== {title} {asof}  ({rank}) ===")
        rows = []
        for tkr, cfg in d.items():
            p = _price(cfg.get("yf", tkr))
            band = _book_zone(p, cfg)
            rows.append({"tkr": tkr, "px": p, "zone": band, "kind": cfg.get("kind", "WAIT")})
            cur = (f"{cfg['ccy']}{int(p):,}" if p is not None and p == int(p) else
                   f"{cfg['ccy']}{p}") if p is not None else "n/a"
            gap = f"{cfg['entry'][0] / p - 1:+.0%} to entry" if p else "gap n/a"
            print(f"  {tkr:5} {cur:>9} -> [{cfg.get('kind','WAIT')}] ({gap})  {band}")
            print(f"        {cfg['thesis']}")
            print(f"        FV bear {cfg['ccy']}{cfg['fv'][0]} / base {cfg['ccy']}{cfg['fv'][1]} / bull {cfg['ccy']}{cfg['fv'][2]}"
                  f"  | entry {cfg['ccy']}{cfg['entry'][0]}-{cfg['entry'][1]}  | regime {cfg['regime']}")
            print(f"        catalyst: {cfg['catalyst']}")
        return rows

    book = _emit_book("AESTHETICS BOOK", "rank: ESTA > GALD > EOLS > HUGEL > LFMD > INMD", BOOK)
    wellness = _emit_book("WELLNESS SLEEVE", "rank: INSP > WST > PGNY > PRCT > BRBR > HIMS > VERU", WELLNESS)
    print("  watch-lite (crowded-quality, no deep-DD yet): DXCM RMD SMPL — buy the consensus story, not an edge.")
    cosmo = _emit_book("COSMECEUTICAL SLEEVE", "rank: LRLCY > BEI.DE > ELF > CRDA > ODD (de-anchored from GLP-1)", COSMECEUTICAL)
    print("  cosmeceutical anchors/watch-lite: EL (prestige 'active-longevity' turnaround, not cheap) | "
          "SKIN (HydraFacial pro-channel, broken micro-cap option). [LRLCY promoted to full entry above.]")
    kbeauty = _emit_book("K-BEAUTY SUB-SLEEVE", "rank: COSMECCA > COSMAX > SILICON2 (KRX-direct; Census HS3304 1.13x=real-not-parabolic)", KBEAUTY)
    print("  k-beauty anchors/watch-lite: Amorepacific 090430 (Cosrx/Aestura/Laneige turnaround, discovered) | "
          "VT 018290 (Reedle Shot viral, spec, Cube overhang) | APR 278470 (Medicube — maximally DISCOVERED +154%/yr P/E~34 = WATCH/FADE, not a buy).")

    # --- VIRALITY RADAR: viral cosmeceutical SKU -> PUBLIC beneficiary (latency ~1-2 quarters before the print) ---
    print(f"\n=== VIRALITY RADAR {asof}  (cosmeceutical; WebSearch scan, refresh ~monthly) ===")
    print("  viral SKU -> public beneficiary (the trade: virality LEADS the manufacturer/brand earnings print):")
    print("    Anua + BYOMA  (ACCEL, openFDA-CONFIRMED mfr) -> COSMECCA 241710 [ODM] — cleanest fresh pair; "
          "corroborates the Cosmecca DEMAND thesis from the viral side (~12.7x vs 20x sector = latency unpriced)")
    print("    Naturium (ACCEL) -> ELF [brand-owner] | Rhode (PEAK, latency spent) -> ELF | "
          "Medicube (PEAK) -> APR (DISCOVERED, harvested)")
    print("    Beauty of Joseon (ACCEL) -> Kolmar 161890 [ODM, UNVERIFIED-confirm] | "
          "Drunk Elephant (FADE) -> Shiseido 4911.T = short-side tell (fading virality -> soft print ahead)")
    print("    PRIVATE / IPO-or-M&A watch (no public vehicle = the gap): Gudai Global (Beauty of Joseon/Tirtir/"
          "Skin1004), Biodance, Rejuran (PDRN originator)")
    print("  [full: run_virality_scan.py + VIRALITY_RADAR.md | connectors/beauty_virality.py (brand->vehicle map "
          "+ openFDA ODM resolver) | TikTok/Reddit/Sephora APIs GATED -> detection=WebSearch]")

    with open(WATCH_LOG, "a") as f:
        f.write(json.dumps({"asof": asof, "stvn": stvn, "lly": lly, "nvo": nvo, "zone": zone,
                            "hiring": hiring_summary, "eols": eols,
                            "eols_inv": (inv if inv and "error" not in inv else None),
                            "eols_air": air, "lfmd": lfmd, "lfmd_zone": lz,
                            "book": book, "wellness": wellness, "cosmo": cosmo, "kbeauty": kbeauty}, default=str) + "\n")
    # trend
    hist = [json.loads(l) for l in WATCH_LOG.read_text().splitlines() if l.strip()]
    if len(hist) > 1:
        print("\nPRICE TREND:", " -> ".join(f"{h['asof'][5:]}:${h['stvn']}({h['zone'][:4]})" for h in hist[-8:]))
    print(f"\n[-> {WATCH_LOG.name}]  ACTION: only if zone in ENTRY_ZONE/DEEP and factory ramp confirms. No orders.")


if __name__ == "__main__":
    main()
