# PRE-REGISTRATION — Polymarket whale-flow drift test (FROZEN 2026-07-05, before any outcome data)

The Form-4 lesson governs: our insider-cluster backtest was NULL; this signal earns trading use
ONLY by beating three nulls on pre-declared terms. Until then the scanner is attention-allocation
with NO seed priority, and whale flow must never be cited as evidence of likely drift.

SIGNAL: single proxyWallet position >= $X in one market within 24h, grid X in {50k, 100k, 250k},
crossed with track-record tiers {unconditioned; hit-rate>55% over >=20 prior resolved; realized
PnL > $250k on-chain} = 3x3 cells (data-api.polymarket.com/trades?filterAmount= + Dune/Polygon
resolved-history join).
OUTCOMES (both pre-declared): (1) in-market drift — implied p moves toward the whale side over
{1h, 1d, to-resolution} net of a no-whale matched-control basket; report p-move AND resolution
accuracy. (2) cross-asset drift — for whale events on markets with a pre-declared equity map,
the mapped equity's {1d, 5d} move in the whale-implied direction. Leg 2 is the desk product and
is expected weakest.
NULLS (all three must be beaten): placebo (equal-size random trades, no drift); reversion
(whale p-moves in thin markets revert per Kyle's-lambda painting — lambda decays ~0.5 -> ~0.02
as liquidity deepens, arXiv 2603.03136); already-priced (route every cross-asset candidate
through discovery_state(); CROWDED = excluded, per the RCAT overturn).
POWER: minimum N=30 whale events per cell for leg 1; leg 2 requires N>=15 mapped events — if the
lookback can't produce that, the verdict is UNDERPOWERED (not a pass). Stopping rule: one
lookback pass 2024-01 -> 2026-06; no peeking-and-extending.
EXCLUSIONS: markets <$100k total volume (painting cheap); wallets <30d old; self-resolving/UMA-
disputed markets.

## AMENDMENT 2026-07-05 (pre-outcome, permitted — no outcome data examined yet): THE INSIDER-SIGNATURE ARM

The original grid conditions on GRINDER SKILL (long track records). The user's objection inverts it:
in event classes with concentrated PRIVATE information (M&A, regulatory decisions, company
announcements, drug approvals), the informed actor is an INSIDER — who has NO track record by
construction (rare appearances, narrow class, aggressive size). Event contracts are not
securities; leakage-betting sits in a legal grey zone equities law doesn't reach — so the thin
venue can OUT-INFORM the deep one precisely when the information is private. The fish hierarchy
("deep venue leads") holds for public-info aggregation and INVERTS for leakage.

SECOND ARM — insider-signature events, tested SEPARATELY from the grinder arm:
- class filter: market belongs to a LEAK-PRONE class {M&A/acquired-by, regulatory approval/
  enforcement, company announcement, clinical readout};
- print signature: aggressive (taker side, moves the mid >=2pp) AND >= $25k (lower floor than
  the grinder arm — insiders size to conviction not bankroll) ;
- wallet signature: LOW-N (<10 lifetime markets) OR class-concentrated (>=70% of volume in one
  class); fresh wallets NOT excluded (the original exclusion is REVERSED for this arm — age<30d
  is part of the signature, not a disqualifier);
- absorption filter: the mid HOLDS or extends 24h post-print (reversion = painting, still).
OUTCOMES: same two legs (in-market resolution accuracy; mapped-equity drift) + a third specific
to this arm: does the EVENT resolve YES-early (before its natural calendar) — the leakage tell.
NULLS: same three, plus a class-matched placebo (equal-size prints in NON-leak-prone classes).
PREDICTION (frozen): the grinder arm shows weak/no drift (public-info efficiency); the
insider-signature arm is where any real signal lives, concentrated in M&A/approvals.
