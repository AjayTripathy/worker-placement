# ADJUDICATION — GEF survivor court (outright Class A) — 2026-08-31

**Ruling: REFUTABILITY-PARK RATIFIED WITH CUTS — STARTER 0.5% Class A PROPOSED, price-gated
≤$83.00; ladder ≤$76 / ≤$73 ratified. Full red/blue remand DENIED (court-worthiness 5/10,
below the ≥6 line; the pair court already benched this issuer's disclosure surface today, and
a full court would move price, not verdict — the bench said so and its work supports it).**

## Procedural findings first (parent must see these)

1. **Duplicate queue rows.** The survivor enqueue was appended raw (bypassing Store.upsert's
   ticker key), so the queue holds TWO GEF rows; the survivor row also inherited the killed
   pair court's history and its `source` reads `dual_class_screen/extremes`, not
   `gef_adjudication_survivor/2026-08-31`. The pair-kill row is intact. Parent close-out
   should collapse the duplicate.
2. **Stage path.** The survivor row moved KILLED→ADJUDICATE off a single refutability bench.
   That is the refutability-park pattern (court-worthiness < 6), not a stage-skip — but the
   transition label makes it look like one. Runner ticket: park transitions should read
   REFUTABILITY→ADJUDICATE on the fresh row.

## Tier re-verification (live, adjudicator)

- **Tape (IBKR, both classes):** A **$82.94 −1.4%** (52w 54.85–90.39 → 8.2% off high, +51%
  off low); B $105.56. No dislocation — verified, the bench's premise holds. IBKR live
  dividend yield 2.74% corroborates the corrected ~3.0% (not the pitch's 5.3%).
- **Yield reconciliation (the bench's decisive catch) — ARITHMETIC VERIFIED:** equity
  25.1M×$82.94 + 21.4M×$105.56 ≈ $4.34B + net debt $741.9M → EV ≈ $5.08B ÷ $625M guide-mid =
  **8.1x EV/EBITDA**; FCF $315M ÷ $4.34B = **7.3% FCF yield** (pitch said 10.1%); blended
  dividend ~3.2%. The routed thesis overstated its two headline yields by ~300bp and ~200bp —
  the same combined-share-count artifact the pair court logged as vendor-artifact member 6,
  inherited into the thesis itself.
- **EDGAR outage:** SEC browse/fetch 503 "undergoing maintenance" live this session (verified
  directly) — the bench's Q3 figures (adj EBITDA $183.4M +24.7%, FY guide raised $615–635M,
  net debt $741.9M, leverage 1.1x) were read from the company's own GlobeNewswire release and
  call transcript, cross-consistent. EDGAR re-pull is a DRAIN gating tranche-2 adds, not the
  starter.
- **Insider cluster (the bench's unread item) — READ:** 9 Form 4s + 3 Form 144s, Aug 3–25,
  via data.sec.gov (up during the web outage). Sampled filings: Bergwall (SVP, Chief
  Commercial Officer) disposed ~2,000 sh at ~$87 ≈ $175k; multi-officer single-day batch
  Aug 5. Pattern = small officer sales in the open window after the 7/28 print, near 52w
  highs. NOT principal-family distribution, NOT AGX-scale. Recorded as caveat; full-cluster
  tally with 10b5-1 status = drain before tranche 2.

## Ruling logic

Clean court, no named kill → FLAT unavailable (minimum-starter default). But the corrected
numbers put Class A at FAIR (7.3% FCF yield, 8.1x EV/EBITDA, flat organic volume, ~$30M of
cost-out left), not dislocated — §TINA-CLASS: fair-quality entry sizes at 0.5%, calendar/price
tranches for the rest. Cuts applied to the bench's proposal:

1. **Price gate ≤$83.00** on the starter (at/below adjudication tape — no chase).
2. **The A-over-B leg is discretionary, not structural** — the 5:1 buyback skew is management
   practice under a ~2%/yr pace cap, not a charter right. The FY26 10-K per-class repurchase
   split is therefore a named kill-variable: if the A-skew does not repeat, the reason to own
   A over B is gone (B carries 1.5x the cash claim).
3. SFS is the one damaged segment (23% of EBITDA, adj EBITDA −$6.3M) with a dated, checkable
   catalyst: RISI recognition of the June $60/ton containerboard increase.

## Instrumentation (pre-registered)

**Pack GEF-SURV|2026-11-05** (Q4/FY26 print; date UNCONFIRMED — analog was Nov-5-2025; the
pack's 2026-10-28 was a yfinance artifact of the old FYE, per the bench):
- Q4 adjusted FCF ≥$109M (guide-low arithmetic requires it) → thesis intact; miss → exit review.
- SFS adj EBITDA stabilizes sequentially OR RISI recognizes the $60/ton → add eligibility at
  the ≤$76 band strengthens.
- Any guide-down of the $615–635M base → exit.
**Pack GEF-ABSKEW|2027-01-15** (FY26 10-K): Class A:B repurchase split — <3:1 kills the
A-preference; re-evaluate holding B or exiting.

**Calibration freezes:**
- GEF-Q4FCF|2026-11-05: P(Q4 adj FCF ≥ $109M) = **0.60**
- GEF-RISI|2026-11-05: P(RISI recognizes $60/ton by the Q4 report) = **0.55**
- GEF-ABSKEW|2027-01-15: P(FY26 10-K shows A:B repurchase ≥ 3:1) = **0.65**

## KG

- `pitch_yield_reconciliation_gate` — PROPOSED: any routed/survivor thesis's headline yields
  must be rebuilt from primary per-class share counts before benches spend on them (this
  pitch overstated FCF yield ~300bp and dividend ~200bp off the inherited share-count
  artifact).

## Drains owed

1. EDGAR re-pull of Q3 8-K/10-Q figures once SEC maintenance ends (gates tranche 2).
2. Full Form 4/144 cluster tally + 10b5-1 adoption dates (gates tranche 2).
3. Q4 print-date PR watch (pack date UNCONFIRMED).

Sources: IBKR live tape (A 4812174, B 4812176); data.sec.gov submissions CIK 43920 + Form 4
XMLs (accessions 0000043920-26-000128, -000113); bench artifact GEF_REFUTABILITY_202608311531
(GlobeNewswire Q3 release, call transcript, 6/2/26 dividend PR); pair-court artifact
GEF_ADJUDICATION_202608311515 (charter, buyback history).
