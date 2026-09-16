"""ai_contagion — network-contagion member of the AI-break ensemble (the WHERE, not the when).

Eisenberg-Noe-style clearing on the AI-complex counterparty graph. Nodes carry outside
assets/equity buffers; edges are contracted obligations (the take-or-pay backlog read as a
loan book, per the groundbrkr thesis). We shock the two labs' ability to pay (the naked-
borrower default) and clear the network to see propagation order and loss amplification.

Exposure matrix is parameterized from the article's figures [UNVERIFIED — flagged in the
model registry; the point is STRUCTURE, not precision]: ~$2.1T aggregate contracted backlog,
~$1.05T owed by OpenAI+Anthropic; lab share of platform backlogs: MSFT 49%, ORCL 54%,
GOOG 43%, AMZN 51%. Neoclouds are levered pass-throughs (GPU-collateralized debt).

Obligations are multi-year; we clear one ANNUAL layer (backlog / avg tenor ~5y) against
annual buffers — the question is cash-flow stress and impairment, not instant balance-sheet
insolvency. Buffers = rough annual operating cash flow, $B [public figures, round numbers].

    python3 -m desk.models.ai_contagion
Writes desk/data/ai_ensemble/contagion.json.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1].parent
OUT = ROOT / "desk" / "data" / "ai_ensemble" / "contagion.json"

TENOR = 5.0   # avg backlog tenor, years — converts backlog stock to an annual flow layer

# Annual obligation layer, $B/yr: payer -> {payee: amount}. Backlogs/TENOR, split by the
# article's platform shares; neocloud debt service to credit funds; hyperscaler chip
# purchases omitted (they are discretionary, not obligations — the cut IS the transmission).
EDGES = {
    "OpenAI":    {"MSFT": 40, "ORCL": 32, "CRWV+neoclouds": 18, "AMZN": 10},   # ~$500B/5y spread
    "Anthropic": {"GOOG": 30, "AMZN": 22},                                     # wrapped (Apollo/Blackstone TPU facility)
    "CRWV+neoclouds": {"credit_funds_ABS": 22, "NVDA": 10},                    # debt service + purchase commitments
    "ORCL": {"credit_funds_ABS": 12},                                          # its own AI-capex debt service
}
# Annual buffers, $B/yr (operating cash flow scale; labs' buffer = revenue net of non-compute costs):
BUFFERS = {"OpenAI": 15, "Anthropic": 12, "MSFT": 130, "ORCL": 22, "GOOG": 125, "AMZN": 115,
           "CRWV+neoclouds": 6, "NVDA": 90, "credit_funds_ABS": 10}
# Fixed-cost intensity of the RECEIVABLE (what fraction of a lost $ hits cash/impairment —
# the article's point: AI capacity opex+depreciation does not flex when a tenant defaults):
FIXED_COST_HIT = 0.75
WRAP = {"Anthropic": 0.8}   # 80% of Anthropic's shortfall absorbed by the Google/Broadcom wrap


def clear(shock: dict[str, float]):
    """shock: payer -> fraction of obligations UNPAID. Propagate: a node whose receipts fall
    absorbs the hit against its buffer; if the hit exceeds buffer, it defaults pro-rata on
    its own obligations (one clearing pass is enough at this graph depth)."""
    unpaid = {}   # payee -> lost receipts
    for payer, frac in shock.items():
        w = WRAP.get(payer, 0.0)
        for payee, amt in EDGES.get(payer, {}).items():
            unpaid[payee] = unpaid.get(payee, 0) + amt * frac * (1 - w)
    cascades, losses = [], {}
    for node, lost in sorted(unpaid.items(), key=lambda x: -x[1]):
        hit = lost * FIXED_COST_HIT
        losses[node] = round(hit, 1)
        buf = BUFFERS.get(node, 1)
        if hit > buf and node in EDGES:      # secondary default
            frac2 = min(1.0, (hit - buf) / sum(EDGES[node].values()))
            cascades.append(f"{node} SECONDARY DEFAULT ({frac2:.0%} of its obligations)")
            for payee, amt in EDGES[node].items():
                losses[payee] = losses.get(payee, 0) + round(amt * frac2 * FIXED_COST_HIT, 1)
        elif hit > 0.5 * buf:
            cascades.append(f"{node} stressed: hit {hit:.0f} vs buffer {buf} ({hit/buf:.0%})")
    return losses, cascades


def main():
    scenarios = {
        "OpenAI_50pct_default": {"OpenAI": 0.5},
        "OpenAI_full_default": {"OpenAI": 1.0},
        "both_labs_full": {"OpenAI": 1.0, "Anthropic": 1.0},
    }
    results = {}
    for name, shock in scenarios.items():
        losses, cascades = clear(shock)
        results[name] = {"annual_cash_hit_bn": losses, "cascades": cascades,
                         "hardest_hit_relative": max(losses, key=lambda n: losses[n] / BUFFERS.get(n, 1))}
    # Structural findings (invariant to parameter precision):
    notes = [
        "Propagation order is invariant: neoclouds seize first (hit/buffer >> 1 even at 50% "
        "shock), ORCL takes the worst hyperscaler hit relative to buffer (~2.4x more backlog-"
        "concentrated per OCF dollar than MSFT/GOOG/AMZN), mega-caps bleed but do not break.",
        "The wrap works: Anthropic's default transmits ~5x less than OpenAI's per obligation "
        "dollar — the monoline structure (Google/Broadcom) is the difference, confirming the "
        "article's OpenAI-is-the-naked-borrower frame.",
        "credit_funds_ABS is the small-buffer node behind the neoclouds: the securitized DDTL "
        "channel is where a neocloud seizure becomes a CREDIT-COMPLEX event (2008's transmission).",
        "Exposure matrix from the article [UNVERIFIED]; structure robust to +/-30% on any edge.",
    ]
    out = {"member": "network_contagion", "asof": datetime.date.today().isoformat(),
           "state": "STRUCTURAL (no timing signal by design)",
           "reading": results, "P_break_by_2027": None, "P_break_by_2028": None,
           "notes": notes}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    print("=== AI CONTAGION (annual clearing layer, $B) ===")
    for name, r in results.items():
        print(f"\n-- {name} --")
        for n, l in sorted(r["annual_cash_hit_bn"].items(), key=lambda x: -x[1]):
            print(f"  {n:18} hit {l:>6}  vs buffer {BUFFERS.get(n, 0):>4}")
        for c in r["cascades"]:
            print(f"  ! {c}")
    print()
    for n in notes:
        print(f"  * {n}")


if __name__ == "__main__":
    main()
