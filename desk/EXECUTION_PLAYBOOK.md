# Execution Playbook (v1.0 — 2026-07-03)
Born from three human-beats-machine moments in one day: a limit staged under the live tape off a
stale close; Midprice suggested by the user, not the desk; thin-float handling living in scar tissue.

## The staging checklist (MANDATORY before any create_order_instruction)
1. `python3 -m desk.preorder_card TICKER --usd N [--cap X]` — the card decides the instrument.
2. **The user's live screen outranks every feed we have.** If our quote basis is `close` or stale,
   ASK for the live level or trust the user's number over ours — never stage a limit against a photo.
3. Caps come from the PLAN (entry-band ceiling / pull-forward cap), not from spread math.
4. If the card says MIDPRICE: the MCP can't stage it — hand the user reviewed params
   (side/qty/cap/TIF) for direct placement, then DELETE any staged duplicate immediately.

## Instrument selection (the card's rules, human-readable)
| Situation | Instrument | Why |
|---|---|---|
| Thin float (<15M) / order >2% ADV / spread >50bps | **IBKR Midprice**, price-capped at the plan ceiling | pegs NBBO mid: half-spread capture, floats WITH the tape |
| Liquid name, tight spread | Marketable LIMIT (ask+1 tick) | pay the spread, own the position — size carries risk, not price |
| <0.1% of ADV, liquid US | MARKET acceptable | spread cost < monitoring cost |
| Quote suspect/quarantined | DO NOT STAGE | never trade against the phantom-tick guard |
| Foreign close-only line (KRX etc.) | LIMIT near close ±band, GTC, verify basis | executability ≠ our feed's visibility |

## Venue quirks (scar-tissue registry)
- **LSE**: pence vs pounds vs USD-GDR on the same suffix — registry ccy is authoritative
- **KRX**: intraday close-only through our channels; account permission gates execution
- **TSE**: 100-share lots, lunch halt; **XETRA/BIT**: auction liquidity in small names
- **Thin ADRs**: trade the local line's hours mentally even when routing the ADR

## The feedback loop
Every fill → `desk/execution_tca.py ingest` (from get_account_trades on positions polls) → scored
vs open/VWAP/close. Median slippage vs VWAP is the desk's execution skill metric — reviewed monthly
like the calibration ledger. Unmeasured advice doesn't improve.

## Standing doctrine
- I stage, the user submits. Read-Only API on the Gateway makes live-data physically trade-proof.
- A fill-optimization tweak that misses is re-staged marketable next session — never inched downward
  into a de-facto price gate (the taxonomy applies at order granularity too).
