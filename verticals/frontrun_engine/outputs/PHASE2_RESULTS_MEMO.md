# Frontrun Engine — Phase 2 (EVENT-DRIVEN, amendment A-4) Results Memo

As-of 2026-06-24. Arm A = DXYZ + RVI. Control = ADX/USA. Locked params unchanged (5% materiality,
>65% hit-rate, edge(A)−edge(B) primary). Primary sources: EDGAR NPORT-P / N-CSR / 424B3 (holdings +
official NAV), IBKR daily prices, company releases + Reuters/CNBC/Bloomberg/PitchBook (round/IPO dates).

## Verdict: §7 criterion FAILED (and re-framed). The negative result IS the finding.

The frontrun-the-up-mark hypothesis is **REFUTED on the only hard event** (SpaceX IPO) and
indeterminate on the soft ones. The aggregation-cost **MOAT is confirmed** (Arm A has discrete,
unobservable private marks; Arm B has none), but the **trade direction the spec assumed does not hold**:
in these retail-driven single-name pre-IPO CEFs the premium is set by venture-beta sentiment and
**overshoots derived NAV on both sides of the event**, so price is NOT anchored on the stale official
NAV — which is the premise the whole frontrun rests on.

## Mark-event table (post-3/31 = the only frontrun candidates; pre-3/31 already in official NAV)

| Fund | Holding | Wt @3/31 | Event | Date | Valuation | vs 3/31 | Conf |
|---|---|---|---|---|---|---|---|
| DXYZ | SpaceX ×3 | 14.34% | **IPO** | **2026-06-12** | ~$1.75–1.8T ($135/sh, ~$75B raised) vs ~$800B basis (~2.19×) | POST · KEYSTONE | VERIFIED |
| DXYZ | Anthropic | 17.92% | Series G $380B | 2026-02-12 | (in 3/31 NAV) | PRE | VERIFIED |
| DXYZ | OpenAI ×2 | 5.71% | $500B tender | 2025-10-02 | (in 3/31 NAV) | PRE | VERIFIED |
| DXYZ | Databricks | 1.04% | $165–175B (in talks) | 2026-06-09 | too small to move DXYZ | POST | SOFT |
| DXYZ | Revolut | 1.57% | $115B (weighing) | 2026-06-05 | too small to move DXYZ | POST | SOFT |
| RVI | Revolut | 7.67% | $115B (weighing) | 2026-06-05 | $75B→$115B (1.53×) | POST | SOFT |
| RVI | Databricks (L+K) | 12.46% | $165–175B (in talks) | 2026-06-09 | $134B→$170B (1.27×) | POST | SOFT |
| RVI | Mercor | 7.63% | $10B Series C | 2025-10-27 | (in 3/31 NAV) | PRE | VERIFIED |

## Per-event derived-NAV surprise (clears 5% gate?)

- **DXYZ-SpaceX-IPO (keystone):** SpaceX $107.3M → ~$235M (no-DLOM) implies derived OFFICIAL NAV/sh
  **$28.75 (+17.1%)**; under a lockup DLOM of 20%/35% it's **$27.91 (+13.6%) / $27.28 (+11.1%)**.
  **Clears 5% with wide margin. Direction UP. VERIFIED.**
- **RVI-Jun-marks:** Revolut $115B + Databricks $170B → derived **$25.84 (+7.4%)** vs $24.05.
  **Clears 5% gate — but SOFT** (both rounds in-talks/weighing, not closed priced rounds).
- **DXYZ-Jun-soft:** Databricks+Revolut move DXYZ only +0.9% — **sub-gate** (weights too small).

## Frontrun measurement — the DXYZ/SpaceX keystone (analyzed in depth)

Premium/discount vs last official NAV ($24.56):

```
 3/31  +9%      ...    5/11  +190% ($71.24 peak)   6/11  +58%   6/12 IPO +18%   6/24 +3.2% ($25.34)
```

- **Predicted (naive frontrun):** price converges UP toward the higher derived NAV (~$28–29) ahead of
  the official print. **REFUTED.**
- **What actually happened:** price was already **far ABOVE** derived NAV before the event — peaking at
  a **+190% premium**, ~2.4× even the post-IPO derived NAV. The market was not anchored on the stale
  official $24.56 and was not converging up to ~$28; it was in a SpaceX-IPO-anticipation blow-off.
- **On the event (6/12):** the premium **collapsed** from +57.6% (6/11) to +18.0% (6/12) — price fell
  TOWARD derived NAV from above, the opposite of the long-the-discount thesis.
- **After:** by 6/24 price $25.34 = +3.2% premium = **below** the post-IPO derived NAV (~$27–29). A
  discount-to-derived-NAV has actually opened.
- **Hit/miss:** directional **MISS**. The realized dislocation that *did* exist (a +190% premium vs a
  ~$28 derived NAV) was a **short-the-premium** trade, not the spec's long-the-discount frontrun — and
  DXYZ is hard-to-borrow / squeeze-prone, so it was not capturable at scale net of borrow.

RVI mirrors this: ran to +206% premium (5/13), still +45% above its $25.84 derived NAV on 6/24. Premium
is venture-beta sentiment, not NAV-anchoring.

## edge(A) vs edge(control)

- **edge(Arm A) = NEGATIVE / INVERTED** on the keystone, INDETERMINATE on RVI. The exploitable mispricing
  was on the short side and borrow-constrained; the hypothesized long-the-discount frontrun did not fire.
- **edge(control ADX/USA) = ZERO BY CONSTRUCTION.** 100% Level-1 → daily NAV embeds any top-holding
  earnings move the same evening → derived(T−1)==official(T−1) always → **no 5% pre-print surprise can
  ever fire.** ADX trades a stable ~12–14% discount, weekly vol <4%, no event gap. Intended Arm-B null.
- **edge(A) − edge(B):** not estimable as positive. Arm A = 1 VERIFIED event (a MISS) + 1 SOFT; Arm B = 0
  events. The moat is real; the trade is not.

## §6 controls honored

- **Point-in-time:** holdings/weights from the 3/31 NPORT; derived NAVs use only marks public on/after
  the event date; official NAVs are the printed 424B3/N-CSR numbers ($24.56 DXYZ, $24.05 RVI), not fair
  value. **No look-ahead.**
- **Net of borrow / bid-ask:** the only profitable direction (short the +190% premium) is gated by DXYZ's
  documented hard-to-borrow/squeeze risk → flagged uncapturable. Bid/ask noted (DXYZ 25.33/25.60).
- **No fishing:** test definition, 5% gate, arms, and >65% bar are the A-4 locked params; not tuned.
- **Survivorship:** N/A to this event cut (both funds live); Phase-1 BKCC death documented separately.

## N / power — stated honestly

**N = 1 hard event** (SpaceX IPO) + 1 soft (RVI June marks). Arm B = 0. **No statistical significance is
claimed or possible.** The keystone is a single idiosyncratic once-ever event; its direction is reported
as a microstructure observation, not a backtested edge.

## Forward out-of-sample (cold scoring, per §8 spirit)

Recorded now, to be graded when the next official NAVs print (Q2, ~Aug 2026):
- **DXYZ derived OFFICIAL NAV/sh ≈ $27–29** (post-SpaceX-IPO, lockup-DLOM dependent).
- **RVI derived OFFICIAL NAV/sh ≈ $25.84** (if the soft Revolut/Databricks marks firm up).

## Microstructure encoded (the actual product)

- **Masking channel:** episodic private marks (NAV moves only on discrete round/IPO/tender events).
- **Signal channel:** a datable mark-event re-mark of the L3 book.
- **Signal-to-price latency:** in retail single-name pre-IPO CEFs, price *leads* and *overshoots* the mark
  on anticipation, then de-rates through the event — so the official-NAV print is a **lagging, non-anchoring**
  reference. The frontrun premise (price anchored on stale NAV, converging at the print) **fails** here; the
  tradeable dislocation is premium-overshoot mean-reversion (a short), not NAV-convergence (a long), and is
  borrow-gated. This is the opposite latency sign from the spec's hypothesis — and the reusable finding.
