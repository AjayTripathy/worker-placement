# LSE COURT ADDENDUM (read WITH _CONTRACT.md — all of it applies; this adds the UK layer)

Your name's screen row: verticals/generators/data/LSE_SHELF.json (match TIDM). Intake context:
desk/data/LSE_INTAKE_20260804.md. Offer-period table: verticals/generators/data/LSE_OFFER_PERIODS.json.

1. PRICE UNITS: LSE quotes in PENCE (GBp). Every yfinance/IBKR/report join must state the unit; the
   priceMagnifier lesson applies — a 100x error is the default failure, not the exception. Tape-verify
   in both units before any ratio.
2. PENSION BY HAND: the shelf's pension guard is DEAD CODE vs this vendor (CHH/COST both carry DB
   SURPLUSES inflating equity that "no pension" tags missed). Pull the DB note from the annual report
   (Companies House or investor site — free): deficit → SFPI-style EV adjustment; SURPLUS → strip it
   from book equity before any P/B claim (recoverable surplus is usually restricted).
3. COMMITTED CAPEX / NOTES: the THX lesson — capital commitments live in the notes, not the balance
   sheet. Any FCF-yield claim requires the commitments note read.
4. OFFER-PERIOD / TENDER CHECK: cross your name vs LSE_OFFER_PERIODS.json + any IBKR .TEN line
   (ACSO has one). A name in an offer period is a different court (special-sit, not value).
5. ENTRY FRICTION IS THE UK EDGE-EATER: quote (stamp duty 0.5% Main Market / 0% AIM) + the median
   touch from the shelf row. AIM's median touch 234bp EATS its stamp exemption. The 0% dividend WHT
   is a HOLDING-period edge — never justify a wide-touch entry with it.
6. PFIC where cash-heavy (GENL/OMG pre-flagged): corrected doctrine — conjunctive test + the
   de-rate-manufactures-status mechanism; FMV basis.
7. EXECUTABILITY: only 4 of 249 conids are IBKR-verified. Verify YOUR line: search_contracts/quote or
   state DATA-GATED. Account LSE permission is proven (BRBY/TW. held) — the line, not the venue, is
   the question. Median (not mean) daily turnover governs sizing; assume 3-8 sessions to exit thin names.
8. SOURCES: RNS via WebFetch (investegate.co.uk or londonstockexchange.com news), annual reports via
   the company site/Companies House. WebSearch is exhausted session-wide. UK reporting is semi-annual —
   state the staleness of your fundamentals honestly; interims may be 6+ months old.
9. Output identical to _CONTRACT.md (per-name MD + EC json court:"lse_shelf_20260804", ≤12-line
   return). Sizes vs $3.3M; UK names cap at 0.75% until an exit-liquidity record exists.
