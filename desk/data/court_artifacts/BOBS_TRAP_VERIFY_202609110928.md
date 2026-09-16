### BOBS (Bob's Discount Furniture — 214-store value furniture retailer, NYSE, Bain-controlled Feb-2026 IPO) — screen "band-touch: low 15.16 ≤ band 15.50, last 15.20" — **SCREEN-ARTIFACT**

**KILL FACTS**
- **The trigger is not live — defect family 1 (quote/date join).** Screen row asserts last 15.20 with a 15.16 touch; pack tape [ibkr_gw] prints **px 18.58**, i.e. **+22% above the 15.50 band**. Corrected value: no touch. Gate condition (the thing the ledger courts) is absent; nothing to stage. File as stale-quote join.
- **Tape's own lo52 9.74 is internally suspect.** BOBS IPO'd 2026-02-05 at $17.00 (19,450,000 shares, net proceeds $304.2M) — https://www.sec.gov/Archives/edgar/data/0002085187/000162828026054345/bobs-20260628.htm and https://www.sec.gov/Archives/edgar/data/2085187/000162828026005868/bobsdiscountfurnitureinc42.htm. A $9.74 low post-IPO is possible but UNVERIFIED; pct_off_low 0.908 is arithmetically consistent with px/lo52 and therefore inherits the defect if lo52 is a pre-IPO/vendor artifact. Do not quote "91% off the low."
- **Windfall-year screen (family 5/4).** Q2-26 GAAP was inflated by **$45.1M IEEPA tariff refunds ($37.9M into gross margin, $1.5M interest)**; gross profit "+20.7%" is a one-off. Ex-refund the business *shrank*: adj. EBITDA **$60.8M (9.8%) vs $62.8M (11.0%)**, adj. NI **$27.8M vs $32.2M**, on comps of only +2.3% — https://www.sec.gov/Archives/edgar/data/0002085187/000162828026053807/ex991-earningsreleasexq220.htm. Q1 same shape: adj. NI **$11.1M vs $14.1M (−21.5%)** — https://www.sec.gov/Archives/edgar/data/0002085187/000162828026032149/bobs-20260329.htm.
- **No net cash (family 2).** Cash **$32.0M**; the $176.6M "total liquidity" is mostly undrawn revolver — someone else's money. Plus 214 stores of operating-lease debt. IPO proceeds went to retire the $350M term loan, not to the balance sheet.

**LIVE FACTS**
- Primary 8-K 2026-08-07 corrects FY26 GAAP NI to **$142–150M** (tax on the refund was omitted from the Aug-6 reiteration) — https://www.sec.gov/Archives/edgar/data/2085187/000162828026054531/bobs-20260806.htm. Ex-refund (~$34M after tax) underlying NI ≈ $108–116M; on ~129M shares (DERIVED from IPO-day $2.2B mcap ÷ $17.02, **not primary**) at $18.58 that is **~21× clean earnings**. Not a deep-value hit.
- **No-actor law fails the other way:** Bain owns ~three-quarters post-IPO, controlled-company status, lock-up already lapsed. The actor is a seller, not a value-forcer.
- **PRICED BY WHOM:** syndicate-covered 2026 IPO — not an orphan, so the FAIR-CARRY exemption does not apply.
- **Pack gaps:** XBRL rev/sbc/dil_sh/ocf slots delivered **EMPTY** — SBC-vs-dilution and OCF/FCF quality are **UNVERIFIED**; I refuse to import them from any secondary. Next print 2026-11-11 is yfinance-derived, **UNCONFIRMED** — PRINT PROXIMITY: none established.

**RESOLVES ON:**
- 2026-11-11 (unconfirmed) Q3 print: comps and *ex-tariff* EBITDA margin vs 9.8%.
- Next 10-Q filing: pull SBC, diluted shares, OCF, lease liabilities to close the empty XBRL block.
- Any Bain secondary / 424B / Form 4 cluster — the real price gate.

**Disposition:** WATCH + tripwire — re-verify only on a **primary-quote** print ≤15.50 (not the stale row) *and* a post-refund quarter holding ≥10% adj-EBITDA margin. Prompt correction filed: the screen row's price context is wrong; the tape, not the row, governs.