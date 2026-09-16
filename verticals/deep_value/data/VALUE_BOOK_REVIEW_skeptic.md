# Value-Detector Book — Independent Skeptic Review (disconfirmation pass)

*2026-06-27. SignalOS quant-analyst run as a HARD SKEPTIC on VALUE_BOOK.md (GCT/DFIN/EVER/EPAM/SBH/BKE/CRCT). Brief: find why it's wrong/overfit/a rationalization — not verify it's right. All factual numbers tested HELD; the FRAMING is what failed.*

## Verdict on the book: KEEP THE DILIGENCE, KILL THE "BOOK" FRAMING
The factual spine is honest (load-bearing numbers verified vs primary XBRL — see below) and the trap-files are genuinely adversarial. As replicated diligence it's good. But as a *"value basket"* it is **largely consumer-discretionary small-cap beta with a quality screen bolted on**, and the selection has a structural asymmetry the prose hides: **the algorithmic gate that killed the 16 rejects would have waved at least one survivor through on the same error — the survivors were saved by uneven human DD time, not by the method.**

## 1. "Value" factor, or consumer-disc beta in disguise? — Mostly disguise
Real SIC by CIK: GCT (5961 catalog), SBH (5990 retail), BKE (5651 apparel), CRCT (3559, consumer crafting) = 4 consumer-disc. EVER = ~90% auto-insurance cycle. DFIN = catalyst IS IPO/M&A volume = the risk-on factor itself. EPAM = the only true sector diversifier, and it's a "starter" with an admittedly unverifiable core. **No value FACTOR — a basket of cheap cyclicals that move together in a rotation.** De-beauty-ing was cosmetic (SBH relabeled "beauty"→"beauty retail/distrib"; same GICS, same driver).

## 2. DEADLIEST finding — the gate is blind to the failure mode it was built to catch
- **GIII was KILLED** for a multiple struck on a stale-peak EBIT.
- **BKE was KEPT** even though its +37% EBIT is a one-time $19.1M litigation settlement masking a YoY *decline* — the *identical* failure mode. It passed `passes_quality()` because the latest-quarter inflection guard (`quality.py:50-53`) reads reported `OperatingIncomeLoss_q` (`fundamentals.py:95`), which *includes* the settlement → reads +37% (passes) instead of true −7%.
- Same blindness had COLL passing as "net-cash 4.9x" until a human re-pulled debt tags.
**The screen reliably manufactures bullish errors; only the per-name DDs catch them — and only GCT/CRCT got full DDs.** So "16→7 trap-filtered survivors" is a selection artifact (conviction-by-effort), not a clean screen output. Fix: normalize one-time/non-operating items before the EBIT inflection + earn-yield gates, and give every survivor symmetric DD.

## 3. TTM construction
`CY2025 − CY2025Q1 + CY2026Q1` is point-in-time clean for a LIVE run today, but **not survivorship-safe for any backtest** (frames drops off-fiscal + slow-filers). Fine for the watch; invalid as evidence of edge.

## 4. Basket-alpha / exclusion-recall claim — unfalsifiable here
For a 7-name long, "we avoid traps" can't be observed (no counterfactual) and has no statistical power (the N≥20 rule applies a fortiori). The prior small-cap work established recall durability for an **exclusion screen over a large universe**, NOT a 7-name concentrated long. This is **diligence-replication value (~bps of avoided fees), not alpha** — stop implying otherwise.

## 5. Per-name verdict
| Name | Verdict | Disconfirming reason | KILL-switch hole |
|---|---|---|---|
| **GCT** | **KEEP** (top conviction defensible) | it's a China-tariff-cycle bet, not "value"; real net-cash floor | PRC cash-repatriability (31% of case) impairs with no GM/auditor signal |
| **DFIN** | **DEMOTE** from co-anchor | catalyst = risk-on macro factor = beta, not idiosyncratic | multiple de-rates faster than EBIT in a risk-off; all KILLs read "fine" |
| **EVER** | **DEMOTE to quarter-size** | 40% customer + 90% auto = binary the multiple can't pay for | carrier cuts CPC (not leaves); margin erodes, revenue stays +YoY |
| **EPAM** | **CUT / pure starter** | core thesis self-admittedly unverifiable; falling-knife AI option | cc-rev-negative is coincident not leading; KILL fires after the loss |
| **SBH** | **DEMOTE** | levered equity stub; return = financial engineering | modest GM give-back compresses levered equity; comps stay flat-positive |
| **BKE** | **DEMOTE / near-CUT** | algo surfaced it on a FAKE number; ~fair value; 107% payout | *special*-div cut (not regular, which KILL watches) breaks paid-to-wait |
| **CRCT** | **CUT from basket; tiny limit-only** | thin, 93%-controlled take-under no floor, sub-decline printing, FCF half headline | "Year-4 rollover" may already be Year-1 |

## 6. Factual claims checked vs primary — ALL HELD
1. BKE Q1 EBIT $59.45M vs $43.55M (+36.6%) — VERIFIED XBRL; one-time-settlement framing corroborated.
2. EVER 40% single customer / Q1-26 op-income $23.4M record / cash $178.5M — VERIFIED (10-Q + XBRL).
3. GCT cash+STI $363.2M / Q1-26 EBIT $42.5M record / ~31% net-cash / live $32.03 (−18.5% YTD) — VERIFIED.

## 7. Loose end
Stale docstring: `smallcap_value_watch.py:2` says "5 names / 12 trap-filtered"; dict + main() say 7/16 — a tell the basket grew by accretion.

## Bottom line
Numbers clean; **framing as a "diversified value book with durable exclusion-recall" does not hold.** It's 7 cheap cyclicals (5 consumer-disc) a human diligenced unevenly, of which the method would have mis-promoted ≥1 (BKE) and mis-rejected ≥1 (GIII) on identical evidence. Real value = diligence-replication, not basket-alpha. Honest core after the cuts: **GCT (kept), DFIN (demoted to beta), everything else demote/cut.**
