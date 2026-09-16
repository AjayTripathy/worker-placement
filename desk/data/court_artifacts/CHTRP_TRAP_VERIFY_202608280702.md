### CHTRP (Charter Communications Series A Cumulative Redeemable Preferred — a fixed-rate, mandatorily-redeemable holdco preferred, NOT an equity claim) — screen mcap $2.72B / EY 181% / P/B 0.17 / ROE 30% — **SCREEN-MISCLASSIFIED**

**KILL FACTS**
- **Every screen metric is a cross-instrument join.** `ni_ttm` $4.933B, `equity` $16.385B, `ey` 1.8116, `pb` 0.166, `roe` 0.3011, `carry_spread` 1.7203 are Charter **common/consolidated** figures mapped onto a **preferred** ticker. CHTRP has no claim on Charter's earnings or book equity — it is a fixed $1.75/sh/yr claim capped at $25. Defect class: **instrument-class artifact** (the family the prompt names) compounded by **family (1) share-count join**.
- **Corrected mcap: ~$171M**, not $2,722,934,097 — 7,183,812 shares outstanding (Liberty Broadband 10-K FY2025, converted 1:1 into Charter preferred at the 2026-08 merger close) × $23.765. Screen figure overstated **15.9×** and does not reconcile to either the preferred count or CHTR's ~141.7M diluted common (pack XBRL `dil_sh`).
- **Correct economics (primary, LBRD 8-A12B/10-K + Charter merger terms):** 7.00%/yr accruing daily on a $25 liquidation price ($1.75/sh), cumulative, paid Jan/Apr/Jul/Oct 15; **no optional redemption ever**; mandatory redemption on the first business day after **2039-03-08**. Charter preferred has substantially identical terms.
- **Structural subordination is the unpaid risk.** This sits at Charter Communications, Inc. — junior to the entire CCO Holdings / Charter Operating stack (~$95B+, plus Cox-deal debt). At $23.765 it yields **7.36% current / ~7.7% YTM (12.5y)** — plausibly *inside* senior CCOH unsecured. Risk not fairly paid ⇒ this is a DECLINE on structure, not on "fair price, no edge," so the FAIR-CARRY rule does not rescue it.
- **No dislocation:** pack tape shows px = 52-week high (dd52 = 0.0), +15.2% off low.

**LIVE FACTS**
- Honest filer; issuer books it as an ASC 480 **liability** with dividends as interest expense — which is why several vendors falsely report "does not currently pay a dividend." **Vendor artifact, not a suspension.**
- Tails bounded ($25 + arrears), cumulative, no call risk, no conversion, no actor: nothing pulls it to par before 2039.
- **UNVERIFIED:** CCOH unsecured yield (the spread comparator); any change-of-control put; ADV; qualified-dividend treatment post-merger.

**RESOLVES ON:**
- **2026-10-15** — first Charter-obligor dividend payment lands at $0.4375/sh (confirms assumption clean).
- **Late-Oct 2026** Q3 print (date UNCONFIRMED) — post-Cox pro-forma net leverage; >4.5x = credit re-rate.
- **Any date:** CHTRP YTM ≥ CCOH unsecured YTW **+150bp** (needs a bond quote to test).

**Disposition:** **AVOID/DECLINE** for the deep-value court — no deep-value thesis exists once the join is unwound. **Reopen-condition:** route to a credit/carry sleeve (never deep value) if price < ~$20 (YTM >9%) **and** a verified positive spread to CCOH unsecured.

**Prompt correction (first-class output):** the evidence pack fed common-equity slots (NEXT PRINT, SBC, OCF, dil_sh) for a preferred ticker. For instrument-class tickers the pack must carry the **certificate of designations + the senior debt stack**; and the screener should hard-reject rows where `mcap / px` ≠ the ticker's own share count.

Sources: [LBRD 8-A12B (preferred terms)](https://www.sec.gov/Archives/edgar/data/1611983/000110465920137156/tm2038415d1_8a12b.htm) · [LBRD 10-K FY2025 (7,183,812 shares; mandatory redemption 2039-03-08)](https://www.libertybroadband.com/investors/financial-information/sec-filings-liberty-broadband/content/0001104659-26-010397/0001104659-26-010397.pdf) · [Charter/Liberty S-4 424B3 (1:1 conversion, identical terms)](https://www.sec.gov/Archives/edgar/data/1091667/000114036125001605/ny20038391x12_424b3.htm) · [Charter 8-A12B for CHTRP](https://www.sec.gov/Archives/edgar/data/1091667/000114036126033679/ef20080486_8a12b.htm) · [Charter–Cox completion](https://corporate.charter.com/newsroom/charter-and-cox-communications-complete-transaction)

*Note: sec.gov returned 403 to the fetch tool in this session (no Bash available to send a full browser fingerprint); the SEC-hosted documents above were read via search-index extraction, and the LBRD 10-K via the issuer-hosted mirror. Terms are corroborated across three independent documents but the Charter 8-A text itself is **secondary-sourced** — re-pull it directly before any credit-sleeve action.*