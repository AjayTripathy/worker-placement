"""effects — desk binding for the officekit effects registry.

The registry itself (2026-09-02 Phase-0 productization) lives in officekit/effects.py:
each portfolio insight is a small, named, testable PROGRAM dispatched per scenario by
the Disaster Planner — a new insight is a new registered effect + a test, never an
engine edit. This module re-exports the registry for desk callers and keeps the
desk's self-test (which exercises the effects against the LIVE household model).

Run as `python3 -m desk.effects` for the selftest.
"""
from __future__ import annotations

from officekit.effects import (  # noqa: F401
    EFFECTS, _BY_ID, effect, run, index, by_channel,
    tax_harvest_hedge, fixed_debt_rate_short, illiquid_mark_lag,
    short_book_rotation, correlation_compression,
)


def _selftest():
    """Self-tests: each effect's core contract, against the live household model."""
    from desk.household import load_model
    m = load_model()

    def ctx_for(shocks):
        # a minimal scenario + a move() that applies factor shocks like the planner
        sc = {"shocks": shocks}
        NOMINAL = {"cash", "cash_pending", "tax_reserve", "real_estate_debt"}

        def move(s):
            if s["category"] in NOMINAL:
                return 0.0
            return max(sum((s["beta"].get(f) or 0.0) * v for f, v in shocks.items()), -0.95)
        return {"m": m, "sc": sc, "move": move, "X": {}}

    # 1) tax hedge: $0 on a tiny move (below buffer), positive & larger on a big crash
    small = tax_harvest_hedge(ctx_for({"S&P 500": -0.05}))
    big = tax_harvest_hedge(ctx_for({"S&P 500": -0.30, "Venture Capital": -0.10}))
    assert small is None, "tax hedge should not fire below the embedded-gain buffer"
    assert big and big["delta"] > 0, "tax hedge should fire in a crash"
    bigger = tax_harvest_hedge(ctx_for({"S&P 500": -0.45, "Venture Capital": -0.15}))
    assert bigger["delta"] > big["delta"], "tax hedge must be convex (bigger crash → bigger cushion)"
    # 2) fixed-debt rate short: fires only when rates rise
    assert fixed_debt_rate_short(ctx_for({"Rates": 0.12})), "rate short should fire on +rates"
    assert fixed_debt_rate_short(ctx_for({"Rates": -0.05})) is None, "rate short should not fire on -rates"
    # 3) mark-lag fires on an equity selloff
    assert illiquid_mark_lag(ctx_for({"S&P 500": -0.30, "Venture Capital": -0.10}))["shadow"] > 0
    # 4) short-book rotation only in real risk-off
    assert short_book_rotation(ctx_for({"S&P 500": -0.05})) is None
    assert short_book_rotation(ctx_for({"S&P 500": -0.30}))["shadow"] > 0
    # 5) dispatch + index
    fired = run(ctx_for({"S&P 500": -0.30, "Venture Capital": -0.10, "Rates": -0.05}))
    assert any(e["id"] == "tax_harvest_hedge" for e in fired)
    assert len(index()) == len(EFFECTS) == 5
    print(f"[effects] selftest OK — {len(EFFECTS)} effects registered:")
    for e in index():
        print(f"  · {e['id']:24s} {e['kind']:8s} channel={e['channel']}")


if __name__ == "__main__":
    _selftest()
