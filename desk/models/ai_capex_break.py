"""ai_capex_break — a break-timing model for the AI-capex credit cycle.

Source thesis: groundbrkr.com "The Second Derivative" (2026-07-02): the AI buildout is a
credit-financed real-estate cycle (take-or-pay backlog = a loan book; OpenAI = the naked
borrower funded by its own appreciation) that breaks when capex growth DECELERATES, not
when demand falls — the 2008 mechanism (delinquencies turned while prices still rose).

THE MODEL (three pieces):

1. THE REFINANCE WALL (the binding constraint). OpenAI is a Minsky Ponzi-unit: obligations
   are serviced by new liability issuance. Sustainable iff
        Capacity(t) = d_max * V(t)  >=  Need(t)
   where d_max = max tolerable dilution per year (~15% private: the $122B raise on $852B
   was 14.3% — they ran at the ceiling; ~3-5% public via follow-ons), V(t) = mark that
   compresses with step-up m(t), and Need(t) = burn + take-or-pay coming due. The IPO is
   the terminal refinance because the PRIVATE supply of $100B+ rounds is exhausted, but a
   public listing at flat-to-down marks CUTS annual capacity ~3-4x. The wall is where the
   curves cross.

2. THE GATES (the 2008-sequence, formalized as observables — each is a leading indicator
   of the wall, none requires believing the thesis):
   A TERMINAL-REFINANCE: IPO prices < $852B last private mark, or slips past Q1-27, or any
     new round shows step-up < 1.3 / distress structure (ratchets, seniority, guarantees).
   B NASH-FLIP: first hyperscaler capex guide-DOWN that the tape REWARDS (same-day multiple
     expansion, controlling for the print) — the moment spending stops being a call option.
   C COLLATERAL-CASCADE: neocloud credit event (spread blowout, GPU-ABS downgrade, DDTL
     covenant waiver) or GPU spot-rental prices through levered-neocloud breakeven.

3. THE CLOCK (2008-mapped hazard). HPA decelerated mid-2005 -> delinquencies turned 2006
   (~4-6q) -> credit froze Aug-07 -> equity event Sep-08. Map: realized-capex deceleration
   T0 -> borrower stress T0+4-6q -> credit freeze +2-4q -> equity event +2-4q. Difference
   from 2008: this cycle has a DATED terminal refinance (the IPO), which can pull the
   revelation forward; and sovereign/strategic backstops that can push it back.

MEASUREMENT RULE (the model's one methodological claim): compute the second derivative on
REALIZED trailing capex + current-quarter guides only. Forward-consensus acceleration is
systematically negative in a boom (analysts under-extrapolate; guides keep getting RAISED),
so consensus-based a<0 is not a signal. Realized a<0 for 2 consecutive quarters starts the
clock. As of 2026-07-30 realized acceleration is NOT yet negative (guides still rising) —
the article's clock may be started on the wrong series.

Data notes (2026-07-30): V_last=852 (Mar-26, VERIFIED); S-1 target 730-850 + delay chatter
(VERIFIED); 2027 consensus capex growth 13-22% vs 2026 ~50-84% (VERIFIED, wide); article's
burn/backlog figures (57% of revenue, $115B cum by 2029, $1.05T lab share of $2.1T backlog,
MSFT-strips-support Apr-26, CRWV DDTL 5.0 securitized May-26) are UNVERIFIED — treated as
parameters, not facts.

    python3 -m desk.models.ai_capex_break
"""
from __future__ import annotations

import json
from pathlib import Path

# ── Parameters (each: value, source, verified?) ───────────────────────────────
P = {
    "V_last_private_bn": 852,          # Mar-26 round mark [VERIFIED]
    "last_raise_bn": 122,              # -> d_max private = 122/852 = 14.3% [VERIFIED]
    "ipo_target_range_bn": (730, 850), # S-1 target [VERIFIED]; below last mark = Gate A amber
    "d_max_private": 0.15,             # dilution ceiling/yr while private (revealed by the 122 raise)
    "d_max_public": 0.04,              # realistic annual follow-on capacity post-IPO w/o crushing px
    "debt_capacity_bn": 25,            # unsecured/convert capacity w/o a co-signer (article: none)
    # OpenAI cash need path, $B/yr (burn + take-or-pay due; article-parameterized, UNVERIFIED):
    "need": {2026: 20, 2027: 30, 2028: 45, 2029: 55},
    # step-up as a function of regime: observed sequence 1.91,1.67,1.70,1.23 [article]
    "m_boom": 1.6, "m_decel": 1.15, "m_bust": 0.75,
    # realized hyperscaler capex $B (5 platforms) — consensus levels [VERIFIED, wide error bars]:
    "capex": {2024: 230, 2025: 412, 2026: 700, 2027: 850},   # 2026-27 = consensus midpoints
}

GATES = {
    "A_terminal_refinance": {
        "state": "AMBER",
        "why": "S-1 range 730-850 sits BELOW the 852 last private mark; Reuters delay-to-2027 "
               "chatter. FIRES on: pricing <852, slip past Q1-27, or any round w/ step-up <1.3 "
               "or ratchets/seniority/guarantees in structure.",
    },
    "B_nash_flip": {
        "state": "GREEN (unfired — the strongest live counter-signal)",
        "why": "All five are still RAISING capex guides (GOOG 180-190, META 125-145). The flip "
               "fires the first time a guide-DOWN is rewarded same-day (multiple expansion, "
               "print-controlled). Until then the reflexive loop is still feeding.",
    },
    "C_collateral_cascade": {
        "state": "UNKNOWN (needs data feeds)",
        "why": "Neocloud credit spreads / GPU-ABS marks / DDTL covenant events / GPU spot-rental "
               "$/hr vs levered breakeven. No feed wired yet.",
    },
}


def refinance_wall():
    """Year-by-year funding capacity vs need under three regimes. The wall = first year
    capacity < need with no stabilizer."""
    rows = []
    for regime, m, d_pub in (("boom (IPO >=852, story intact)", P["m_boom"], 0.05),
                             ("decel (IPO flat-to-down, m~1.15)", P["m_decel"], P["d_max_public"]),
                             ("bust (mark -25%, m<1)", P["m_bust"], 0.02)):
        V = P["V_last_private_bn"]
        for yr in (2027, 2028, 2029):
            V = V * (m if yr == 2027 else max(1.0, m - 0.15) if regime.startswith("boom") else m)
            cap = d_pub * V + P["debt_capacity_bn"]
            need = P["need"][yr]
            rows.append({"regime": regime, "year": yr, "mark_bn": round(V), "capacity_bn": round(cap),
                         "need_bn": need, "binds": cap < need})
    return rows


def second_derivative():
    """Realized + consensus capex derivatives. The signal series is REALIZED-only."""
    c = P["capex"]
    yrs = sorted(c)
    g = {y: round(100 * (c[y] / c[y - 1] - 1)) for y in yrs[1:]}
    a = {y: g[y] - g[y - 1] for y in list(g)[1:]}
    return {"levels_bn": c, "growth_pct": g, "accel_pp": a,
            "note": "2026-27 are consensus, not realized — the 2027 acceleration (-49pp on these "
                    "midpoints) is a FORECAST artifact until guides actually stop rising. "
                    "Signal = realized trailing-4Q accel < 0 for 2 consecutive quarters."}


def clock():
    """Scenario tree with frozen probabilities (2026-07-30). Break = visible credit event in
    the AI complex (neocloud seizure / major impairment / RPO reprice), per the article's
    sequence — NOT merely an equity drawdown."""
    return {
        "scenarios": [
            {"p": 0.20, "path": "IPO prices >=852 on schedule (<=Q1-27)",
             "break_window": "clock resets 4-6q; earliest 2028H2"},
            {"p": 0.45, "path": "IPO delayed into 2027 + private/sovereign bridge",
             "break_window": "2027H2-2028H2 (median case)"},
            {"p": 0.25, "path": "IPO below mark or pulled, no mega-bridge",
             "break_window": "cascade within 2-3q of the event (2027)"},
            {"p": 0.10, "path": "structural rescue (federal stake / hyperscaler re-wrap of OpenAI)",
             "break_window": "no credit break; capex growth flatlines, semis derate anyway"},
        ],
        "aggregates": {"P(break by end-2027)": "~0.30", "P(break by end-2028)": "~0.60",
                       "median": "H1-2028, fat early tail keyed to the IPO event",
                       "condition": "ALL paths assume Gate B fires first or concurrently; while all "
                                    "five raise guides, break probability within 2q is LOW"},
    }


TRIPWIRES = [
    "1. Realized capex accel: 5 hyperscalers' trailing-4Q capex growth delta each 10-Q — RED at <0 twice consecutively (the clock-starter)",
    "2. Guide-direction count each earnings cycle: first capex guide-DOWN + same-day tape reward = Gate B (event-study on the day)",
    "3. OpenAI terminal refinance: IPO date/price vs 852; any round's step-up <1.3; STRUCTURE tells (ratchets/seniority/guarantees) outrank headline marks",
    "4. GPU spot rental $/hr (H100/B200 indices) vs levered-neocloud breakeven — the 'rent roll' of the real-estate frame",
    "5. Neocloud credit: CRWV bond spreads, GPU-ABS new-issue spreads/enhancement, any covenant waiver = Gate C RED",
    "6. Accounting tells: depreciation-life extensions at hyperscalers; RPO counterparty-concentration disclosures (ORCL % from one name)",
    "7. Anthropic contrast: its step-ups holding while OpenAI's compress = counterparty problem (thesis intact); BOTH compressing = demand problem (worse)",
]


def write_ensemble_json():
    import datetime
    out = {"member": "mechanism_refinance_wall", "asof": datetime.date.today().isoformat(),
           "state": "AMBER",
           "reading": {"gates": {k: v["state"] for k, v in GATES.items()},
                       "wall": "binds 2028 in bust regime only; boom/decel regimes clear",
                       "second_derivative": second_derivative(), "clock": clock()},
           "P_break_by_2027": 0.30, "P_break_by_2028": 0.60,
           "notes": ["gate A amber (IPO range below last mark + delay chatter), gate B green "
                     "(guides still rising = loop intact), gate C unwired",
                     "measurement rule: realized capex accel NOT yet negative - the article's "
                     "clock may be started on consensus, the wrong series"]}
    p = Path(__file__).resolve().parents[2] / "desk" / "data" / "ai_ensemble" / "mechanism.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))


def main():
    write_ensemble_json()
    print("=== AI-CAPEX BREAK MODEL (2026-07-30) ===\n")
    print("-- second derivative (measurement rule: trust realized only) --")
    print(json.dumps(second_derivative(), indent=1))
    print("\n-- the refinance wall (capacity vs need, $B) --")
    for r in refinance_wall():
        flag = "  <-- BINDS" if r["binds"] else ""
        print(f"  {r['regime']:38} {r['year']}  mark {r['mark_bn']:>5}  capacity {r['capacity_bn']:>4}  need {r['need_bn']:>3}{flag}")
    print("\n-- gates --")
    for k, v in GATES.items():
        print(f"  {k}: {v['state']}\n    {v['why']}")
    print("\n-- clock --")
    print(json.dumps(clock(), indent=1))
    print("\n-- tripwires --")
    for t in TRIPWIRES:
        print(f"  {t}")


if __name__ == "__main__":
    main()
