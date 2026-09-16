# Execution-path comparison — CA specialty muni sleeve (~$1mm)

*Fill in the bracketed cells as each desk answers. The decisive row is **odd-lot markup** — that's the hidden cost the headline fee hides. Scoring math at the bottom converts everything to one comparable number: all-in annual drag, and net after-tax TEY.*

## The grid

| | **MS (via MFO + wrap)** | **Fidelity / Schwab (self-directed)** | **Muni specialist B-D** (Stifel / RJ / Hilltop) |
|---|---|---|---|
| Can do **client-directed** deep-discount odd-lots? | [ask Q1] | Yes (you direct; they execute) | Yes (their core business) |
| **Advisory / wrap fee** (recurring) | **0.40%** (MFO) | ~0% (no advisory) | ~0% (brokerage) |
| **Custody / platform fee** | [ask Q3] | ~0 (free at both) | [ask] |
| **Odd-lot markup** per purchase (THE number) | [ask Q2/Q4] | [ask desk] — typ. ~0.25–0.75pt | [ask] — often tight, it's their inventory |
| Principal or **agent** execution? | [ask Q2] | principal (markup disclosed G-15) | principal (markup disclosed) |
| **RFQ multiple dealers / best-ex** demonstrated? | [ask Q4 — Turlock test] | you control the RFQ on the ticket | yes — they source bid-wanteds |
| **Turlock test fill** (vs ~79 tape / 82.4 offer) | [their answer] | [their answer] | [their answer] |
| **Fill-vs-limit reporting** | [ask Q5] | yes (on confirms) | [ask] |
| **Consolidated reporting** w/ rest of portfolio | yes (in the wrap) | no (separate account) | no (separate account) |
| **Setup required** | none (existing) | open 1 account | open 1 account + find the rep |
| **You keep control of the limit / RFQ?** | only if directed (Q1) | fully | mostly (rep executes your limit) |

## Scoring — convert to one comparable number

**Step 1 — amortize the markup.** A one-time markup of *M* points on a bond ~*Y* years to maturity ≈ **M ÷ Y × 100 bps/yr** of yield given up. For this ladder *Y* ≈ 15.
- 0.25pt → ~1.7 bps/yr · 0.50pt → ~3.3 bps/yr · 1.0pt → ~6.7 bps/yr · 2.0pt → ~13 bps/yr

**Step 2 — all-in annual drag** = advisory fee + custody + amortized markup (bps/yr):

| | advisory | custody | markup (amortized) | **all-in drag** |
|---|---|---|---|---|
| MS | 40 | [ ] | [ M/15×100 ] | **[ ]** |
| Fidelity/Schwab | 0 | 0 | [ M/15×100 ] | **[ ]** |
| Muni specialist | 0 | [ ] | [ M/15×100 ] | **[ ]** |

**Step 3 — net after-tax TEY** ≈ gross after-tax TEY (≈ **8.2%**) − all-in drag.
*Caveat: advisory fees are paid with after-tax dollars and aren't deductible, so each 1 bp of recurring fee costs ~2 bps of TEY-equivalent. The markup (in the bond price) reduces yield directly, ~1:1. So the fee row hurts about twice as much per bp as the markup row — weight accordingly.*

## How to read the result

- **If MS's markup is competitive AND the money's already in the wrap** (0.40% sunk): MS likely wins on net — existing relationship, consolidated reporting, no setup, and the only marginal cost is a reasonable markup.
- **If MS quotes a fat markup or won't demonstrate RFQ** (Turlock test fails): the 0.40% is buying you a markup pass-through. Self-direct the specialty sleeve at Fidelity/Schwab where you pay **one transparent markup you control**, and leave MS the conventional/managed money where the wrap earns its fee.
- **The muni specialist** is the wildcard: often the *tightest* markups on obscure CA paper (it's their inventory and they want to move it), but a separate relationship and rep-dependent. Worth a quote if MS disappoints and you want better sourcing than a discount desk.

**The single decision rule:** whichever path shows the **lowest all-in drag *while* answering "yes" to client-directed deep-discount + demonstrating the Turlock RFQ.** A low fee means nothing if they won't run the strategy; a willingness to run it means nothing if the markup quietly eats the edge. Both boxes must be checked.

---

## Post-call capture — note these 8 things, I'll score them in

*From tomorrow's desk call (run-sheet questions → grid cells). Capture the raw answer; I convert to the comparable number.*

| # | What to capture on the call | Source (run-sheet) | Fills grid cell(s) |
|---|---|---|---|
| 1 | **Which desk** — name + type (discount bond desk / muni specialist B-D) | opener | which column |
| 2 | **Calibration markup** — their offer on **91412G2F1** (last cust-buy **101.71**). *Offer − 101.71 = M, the number.* | Calibration RFQ | Odd-lot markup → amortized bps/yr |
| 3 | **Markup convention** — disclosed bps, or built into the price? | Q1 | Odd-lot markup; Principal/agent |
| 4 | **Inter-dealer level** — will they show it, or only their offer? | Q2 | RFQ/best-ex; transparency (green/red flag) |
| 5 | **Standing want-list / BWIC** — can they hold a GTC want-list and run bid-wanteds? | Q3 + Tier-B handoff | RFQ multiple dealers; sourcing (the capability test) |
| 6 | **A real Tier-B fill** — did any stale name (e.g. 900211CP6 @ 79.50, or 817409H32 @ 83.50) get worked/filled? | Tier B | Turlock-test fill row |
| 7 | **Fill-vs-limit reporting** + how fills are confirmed | Close | Fill-vs-limit reporting |
| 8 | **Custody/platform fee + account setup** needed | Close | Custody fee; setup |

**Pre-computed so #2 is instant** — amortized over the ladder's ~15y: markup 0.25pt → **1.7 bps/yr** · 0.50 → **3.3** · 0.75 → **5.0** · 1.0 → **6.7** · 1.5 → **10** · 2.0 → **13 bps/yr**. Then **net after-tax TEY ≈ 8.2% − all-in drag** (advisory 0 for a desk + custody + amortized markup).

**Two-box gate to report against:** does the desk (a) say **yes** to client-directed deep-discount odd-lots *and* (b) demonstrate sourcing (a real bid-wanted on a Tier-B name)? On pure cost the desk almost always wins the *specialty sleeve*: it carries **no recurring advisory fee**, so even a fat 1 pt markup is ~6.7 bps/yr amortized vs the MFO's **40 bps/yr** — and the advisory bites ~2× harder per bp (after-tax, non-deductible) than the in-price markup. So if both gate-boxes are **yes**, the desk wins on drag, and the MFO+wrap only earns back its fee on consolidated reporting + zero setup + the existing relationship. If either box is **no**, the desk is a retail order-taker regardless of markup — and that's the disqualifier, not the price. I'll fill the grid and state the verdict once you give me #1–#8.
