# Execution Autonomy Ladder (v1.0 — 2026-07-03, user-initiated: "at some point I do want you to be able to place directly")

Direct placement is EARNED by measured records, not granted by enthusiasm. Each rung has explicit
gates, hard rails that survive even a confused agent, and a one-word kill switch.

## Rung 0 — TODAY: I stage, user submits
Read-Only API at the Gateway. Every order is a staged instruction the user reviews and submits.

## Rung 1 — Parameterized auto-placement (the first direct-placement rung)
**What:** I place orders ONLY inside a pre-approved envelope: ticker + side + max qty + price cap +
time window, approved by the user via the dashboard approve button (audited). Example: "IBEX reserve
0.5%, cap $32.50, valid to Sept-10" — I choose timing/instrument within it.
**Hard rails (defense in depth):**
- IBKR-level precautionary settings: max order size, max daily orders, restricted-list — enforced by
  the BROKER, not by my code
- Per-order cap 1% of book, daily cap 2%, no options, no shorts, long-only common stock
- NEW names never — only tickers with an adjudicated OWNABLE/STARTER verdict + explainer + frozen call
- Instant notification on every placement; the audit log is append-only
- Kill switch: the user says "halt trading" anywhere → the API user gets disabled at IBKR
**Gates to unlock:**
1. Calibration ledger: Brier(ours) < Brier(market) on >= 20 resolved calls (the sizing gate applies to autonomy too)
2. TCA: >= 10 fills scored, median slippage vs VWAP <= +15bps
3. Missed-entry ledger: one full quarterly review cycle with the response taxonomy holding
4. Data integrity: 4 consecutive weeks with ZERO phantom-tick/stale-GO/poisoned-referee incidents
   reaching a decision surface (this week alone had three — the system caught them, but each was an
   order-placing hazard; the guards must prove themselves quiet first)
5. Dry-run month: Rung-1 logic runs in shadow mode (logs what it WOULD place); user reviews the log

## Rung 2 — Standing mandates
Resting-ladder management (replace expired GTCs per plan), harvest-window mechanics in December,
rebalancing within approved bands. Weekly review ritual. Gates: 3 clean months at Rung 1.

## Never (at any rung)
- Initiating a name the pipeline hasn't adjudicated
- Sizing beyond the envelope; averaging into a kill-triggered position
- Anything while a data-integrity flag is open on that ticker
- Trading through a RED_TEAM_PENDING stage

## Technical path
Gateway Read-Only (now) → second API user with trade permission, IP-locked to this machine,
IBKR precautionary limits set → shadow month → Rung 1. The Read-Only user REMAINS the data pipe;
the trading user is separate so data flow never carries order risk.
