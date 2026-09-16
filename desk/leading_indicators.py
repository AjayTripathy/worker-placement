"""leading_indicators — encode each MFT nowcast as a PROGRAM: read the leading data, compute
P(gate). Turns the hand-read probabilities from the 2026-07-10 batch into a pipeline.

Each indicator has (1) cached INPUTS (dated, sourced — the same external data the analysts read),
(2) a live fetch() that will pull fresh data on the monthly cron, and (3) an ENCODED nowcast model
mapping inputs -> P(gate). The models are specified A PRIORI (a normal-CDF nowcast for continuous-
metric gates; a momentum model for the streak gate) — NOT tuned to reproduce the hand P. Running
the comparison on the SAME cached inputs isolates MODEL-vs-JUDGMENT (not data drift): where pipeline
≈ hand, the reasoning was mechanical and faithfully encoded; where they diverge, the human added
(or mis-anchored) judgment the formula doesn't carry — which points at the next feature to encode.

    python3 -m desk.leading_indicators           # compute pipeline P + compare vs frozen hand P
    python3 -m desk.leading_indicators --live     # best-effort live refresh of the cached inputs
READ-ONLY.
"""
from __future__ import annotations

import json
import math
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALIB = ROOT / "desk" / "data" / "calibration_ledger.jsonl"


def _phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def _clip(x, a, b):
    return max(a, min(b, x))


def _mean(xs):
    return sum(xs) / len(xs)


# --- nowcast models (a-priori; sigma = the a-priori month-to-month vol of that metric) -----------
def _nc_tsm(x):
    cons = _mean(x["consensus_yoy"])
    mu = 0.5 * cons + 0.3 * x["tsmc_may_yoy"] + 0.2 * _mean(x["peer_yoy"])   # weight: consensus>own-run-rate>peers
    sigma = 10.0
    p = _phi((mu - x["gate_yoy"]) / sigma)
    return p, f"E[JunYoY]≈{mu:.0f}% (.5·cons{cons:.0f} +.3·May{x['tsmc_may_yoy']:.0f} +.2·peers{_mean(x['peer_yoy']):.0f}); σ{sigma:.0f} → P(≥{x['gate_yoy']}%)"


def _nc_cost(x):
    mu = 0.35 * x["june_comp"] + 0.35 * x["june_comp_adj"] + 0.30 * x["redbook_yoy"] - x["gas_haircut"]
    sigma = 2.5
    p = _phi((mu - x["gate_comp"]) / sigma)
    return p, f"E[JulComp]≈{mu:.1f}% (blend Jun {x['june_comp']}/{x['june_comp_adj']} + Redbook {x['redbook_yoy']} − gas {x['gas_haircut']}); σ{sigma} → P(≥{x['gate_comp']}%)"


def _nc_sia(x):
    mu, sigma = x["last_mom"], 12.0                                          # smoothed 3-mo-MA: last MoM is the drift
    p = _phi((mu - 0) / sigma)
    return p, f"3mo-MA MoM last {mu:+.1f}%; σ{sigma:.0f} (roll-off risk) → P(MoM>0)"


def _nc_tm(x):
    run = _mean(x["recent_dsr_yoy"])
    mu = run - x["comp_difficulty"] - x["gas_drag"]        # FEATURE: tough prior-year base + elevated gas
    sigma = 4.0
    p = _phi((mu - 0) / sigma)
    return p, f"E[JulDSR]≈{mu:+.1f}% (run {run:+.1f} − comp-diff {x['comp_difficulty']} − gas {x['gas_drag']}); σ{sigma:.0f} → P(≥0)"


def _wc_frac(x):
    """Fraction of the month inside the World-Cup window (a data feature: next month, WC over → 0)."""
    return min(x["wc_end_day"], x["month_days"]) / x["month_days"]


def _nc_macau_mom(x):
    wcf = _wc_frac(x)                                       # FEATURE: WC calendar drives the recovery
    recovery = -x["wc_yoy_impact"] * (x["june_wc_frac"] - wcf)   # July less WC-affected than June -> MoM up
    mu, sigma = recovery, 8.0
    p = _phi((mu - 0) / sigma)
    return p, f"WC frac Jul {wcf:.2f} vs Jun {x['june_wc_frac']:.2f} → MoM recovery {mu:+.1f}%; σ{sigma:.0f} → P(MoM≥0)"


def _nc_macau_yoy(x):
    wcf = _wc_frac(x)
    mu = x["wc_yoy_impact"] * (wcf / x["june_wc_frac"])     # July YoY drag scales with its WC fraction
    sigma = 6.0
    p = _phi((mu - 0) / sigma)
    return p, f"WC frac Jul {wcf:.2f} → Jul YoY drag {mu:+.1f}%; σ{sigma:.0f} → P(YoY≥0)"


def _nc_il_vgt(x):                                          # Illinois VGT net-terminal-income (state metric)
    mu, sigma = x["recent_yoy"], x["sigma"]
    p = _phi((mu - x["gate"]) / sigma)
    return p, f"IL VGT NTI YoY {mu:+.1f}% (state at records); σ{sigma:.0f} → P(YoY≥{x['gate']}%)"


def _nc_acel(x):                                           # ACEL Q2 vs consensus, led by IL VGT (its core)
    mu = x["il_vgt_yoy"] + x["expansion"] - x["consensus_hurdle"]
    sigma = x["sigma"]
    p = _phi((mu - 0) / sigma)
    return p, f"IL VGT {x['il_vgt_yoy']:+.1f} + expansion {x['expansion']:+.1f} − hurdle {x['consensus_hurdle']:+.1f} → μ{mu:+.1f}; σ{sigma:.0f}"


def _nc_cannabis(x):                                       # operator rev vs consensus in a CONTRACTING market
    mu = x["state_blend_yoy"] + x["share_gain"] - x["consensus_priced_yoy"]
    sigma = x["sigma"]
    p = _phi((mu - 0) / sigma)
    return p, f"state {x['state_blend_yoy']:+.1f} + share {x['share_gain']:+.1f} − priced {x['consensus_priced_yoy']:+.1f} → μ{mu:+.1f}; σ{sigma:.0f}"


def _nc_cox_saar(x):
    mu, sigma = x["recent_saar"], x["sigma"]
    p = _phi((mu - x["gate"]) / sigma)
    return p, f"SAAR {mu:.1f}M recent; σ{sigma} → P(≥{x['gate']}M)"


# --- the registry: id -> {source, inputs (cached/dated), live URL(s), model, feeds:(ticker,cat_date)} ---
INDICATORS = {
    "tsm_taiwan_monthly": {
        "source": "Taiwan monthly revenue (peers UMC/ASE printed) + TSMC IR",
        "asof": "2026-07-10", "feeds": ("TSM", "2026-07-13"),
        "inputs": {"consensus_yoy": [52, 67], "tsmc_may_yoy": 30.1, "peer_yoy": [22.9, 32.9], "gate_yoy": 30},
        "live": "https://investor.tsmc.com/english/monthly-revenue/2026", "model": _nc_tsm},
    "cost_redbook": {
        "source": "Costco June IR release + Johnson Redbook weekly",
        "asof": "2026-07-10", "feeds": ("COST", "2026-08-05"),
        "inputs": {"june_comp": 8.8, "june_comp_adj": 7.0, "redbook_yoy": 9.5, "gas_haircut": 0.5, "gate_comp": 5},
        "live": "https://tradingeconomics.com/united-states/redbook-index", "model": _nc_cost},
    "sia_billings": {
        "source": "SIA/WSTS global billings (3-mo-MA)",
        "asof": "2026-07-10", "feeds": ("SIA-BILLINGS", "2026-08-05"),
        "inputs": {"last_mom": 9.2, "streak": 15}, "live": "https://www.semiconductors.org/", "model": _nc_sia},
    "toyota_us_sales": {
        "source": "Toyota pressroom monthly US sales + Cox SAAR (+ comp-difficulty & gas features)",
        "asof": "2026-07-10", "feeds": ("TM", "2026-08-03"),
        "inputs": {"recent_dsr_yoy": [4.0, 3.3, 5.0], "comp_difficulty": 1.5, "gas_drag": 0.6},
        "live": "https://pressroom.toyota.com/", "model": _nc_tm},
    "macau_ggr_mom": {
        "source": "Macau DICJ monthly GGR + FIFA WC calendar feature",
        "asof": "2026-07-10", "feeds": ("MLCO", "2026-08-01"),
        "inputs": {"wc_end_day": 19, "month_days": 31, "june_wc_frac": 1.0, "wc_yoy_impact": -12.1},
        "live": "https://www.dicj.gov.mo/web/en/information/DadosEstat_mensal/", "model": _nc_macau_mom},
    "macau_ggr_yoy": {
        "source": "Macau DICJ monthly GGR + FIFA WC calendar feature",
        "asof": "2026-07-10", "feeds": ("MACAU-GGR", "2026-08-01"),
        "inputs": {"wc_end_day": 19, "month_days": 31, "june_wc_frac": 1.0, "wc_yoy_impact": -12.1},
        "live": "https://www.dicj.gov.mo/web/en/information/DadosEstat_mensal/", "model": _nc_macau_yoy},
    "il_vgt": {
        "source": "Illinois Gaming Board monthly VGT net-terminal-income (state at records)",
        "asof": "2026-07-10", "feeds": ("IL-VGT", "2026-08-15"),
        "inputs": {"recent_yoy": 5.0, "gate": 0.0, "sigma": 6.0},
        "live": "https://www.igb.illinois.gov/VideoReports.aspx", "model": _nc_il_vgt},
    "acel_via_il_vgt": {
        "source": "ACEL Q2 revenue vs consensus, led by IL VGT (its core state)",
        "asof": "2026-07-10", "feeds": ("ACEL", "2026-08-07"),
        "inputs": {"il_vgt_yoy": 5.0, "expansion": 1.5, "consensus_hurdle": 5.0, "sigma": 4.0},
        "live": "https://www.igb.illinois.gov/VideoReports.aspx", "model": _nc_acel},
    "aawh_cannabis": {
        "source": "AAWH Q2 vs consensus — IL/NJ/MI state monthly sales (contracting)",
        "asof": "2026-07-10", "feeds": ("AAWH", "2026-08-12"),
        "inputs": {"state_blend_yoy": -10.0, "share_gain": 5.0, "consensus_priced_yoy": -3.0, "sigma": 5.0},
        "live": "https://www.idfpr.com/profs/adultusecan.asp", "model": _nc_cannabis},
    "tcnnf_cannabis": {
        "source": "TCNNF (Trulieve) Q2 vs consensus — FL OMMU weekly THC (its core, stable)",
        "asof": "2026-07-10", "feeds": ("TCNNF", "2026-08-07"),
        "inputs": {"state_blend_yoy": 2.0, "share_gain": 3.0, "consensus_priced_yoy": 3.0, "sigma": 5.0},
        "live": "https://knowthefactsmmj.com/", "model": _nc_cannabis},
    "cox_saar": {
        "source": "Cox Automotive US new-vehicle SAAR (self-forecast published pre-print)",
        "asof": "2026-07-10", "feeds": ("COX-SAAR", "2026-08-03"),
        "inputs": {"recent_saar": 16.3, "gate": 16.0, "sigma": 0.4},
        "live": "https://www.coxautoinc.com/insights/", "model": _nc_cox_saar},
}


def _try_live(url, timeout=8):
    """Best-effort live pull (runs from the Mac's residential IP on the monthly cron, so not
    cloud-IP-blocked like the agent run). Returns raw text or None; per-source parsing is TODO —
    for now the connector degrades gracefully to the dated cached inputs."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
    except Exception:
        return None


def nowcast(iid, live=False):
    ind = INDICATORS[iid]
    src = "CACHED"
    if live and _try_live(ind["live"]) is not None:
        src = "LIVE-REACHED (parse TODO → still using cached values)"
    p, explain = ind["model"](ind["inputs"])
    return {"id": iid, "feeds": ind["feeds"], "p": round(p, 3), "explain": explain, "data": src, "asof": ind["asof"]}


def _hand_p():
    hp = {}
    if CALIB.exists():
        for line in CALIB.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if isinstance(r.get("our_p"), (int, float)):
                hp[(r.get("ticker"), r.get("cat_date"))] = r["our_p"]
    return hp


def compare(live=False):
    hp = _hand_p()
    rows = []
    for iid in INDICATORS:
        nc = nowcast(iid, live=live)
        hand = hp.get(nc["feeds"])
        delta = round(nc["p"] - hand, 3) if hand is not None else None
        rows.append({**nc, "hand_p": hand, "delta": delta})
    return rows


def main(live=False):
    rows = compare(live=live)
    print(f"{'indicator':22} {'feeds':16} {'pipe':>5} {'hand':>5} {'Δ':>6}  basis")
    print("-" * 118)
    deltas = []
    for r in rows:
        tk = f"{r['feeds'][0]}@{r['feeds'][1][5:]}"
        d = f"{r['delta']:+.2f}" if r["delta"] is not None else "  —"
        flag = "  ⟵ DIVERGE" if r["delta"] is not None and abs(r["delta"]) >= 0.10 else ""
        if r["delta"] is not None:
            deltas.append(abs(r["delta"]))
        print(f"{r['id']:22} {tk:16} {r['p']:>5.2f} {(r['hand_p'] or 0):>5.2f} {d:>6}  {r['explain'][:56]}{flag}")
    if deltas:
        print("-" * 118)
        print(f"mean|Δ|={sum(deltas)/len(deltas):.3f}   median|Δ|={sorted(deltas)[len(deltas)//2]:.3f}   "
              f"within 0.05: {sum(1 for d in deltas if d<=0.05)}/{len(deltas)}   diverge(≥0.10): {sum(1 for d in deltas if d>=0.10)}/{len(deltas)}")


if __name__ == "__main__":
    import sys
    main(live="--live" in sys.argv)
