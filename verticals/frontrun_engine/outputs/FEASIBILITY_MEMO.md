# Frontrun Engine v0 — Phase 1 Data-Feasibility Memo

As-of 2026-06-24. Primary sources only (SEC EDGAR NPORT-P / XBRL / N-CSR / 424B3; IBKR live price).
This memo answers the spec's critical Phase-1 question: **what is runnable now vs blocked.**

## The decisive feasibility finding (changes the pilot's runnable scope)

**BDCs do not file NPORT-P.** ARCC, OBDC, FSK, MAIN, PSEC, GBDC are business development
companies that file 10-Q/10-K + N-2, NOT the NPORT-P that the moat classifier and the re-mark
engine consume. Their Schedule of Investments (with the Level-1/2/3 split) lives inside the 10-Q
as an HTML/table exhibit, refreshed quarterly with the same ~45-day lag, and is not exposed as a
clean machine-readable holdings feed. Verified: `submissions/CIK*.json` returns **0 NPORT-P** for
all six BDCs; their L3 share is only partially recoverable from XBRL companyfacts (3 of 6 cleanly).

Consequence: **the engine-tractable Arm A is the venture/pre-IPO CEFs that file NPORT-P, of which
DXYZ is the one clean, liquid, traded example.** The BDCs are confirmed high-moat (Level-3 ~100%)
but are **engine-blocked in Phase 1** for the point-in-time daily re-mark.

## What is gettable FREE (verified working)

| Data need | Source | Status |
|---|---|---|
| CEF Level-3 % of NAV + full holdings | EDGAR NPORT-P `primary_doc.xml` | WORKS — parsed for all 6 CEFs |
| BDC Level-3 % (3 of 6) | EDGAR XBRL companyfacts (L3 reconciliation / total investments) | PARTIAL — ARCC/FSK/GBDC clean; OBDC/MAIN/PSEC tagged dimensionally |
| Portfolio turnover (the gate) | N-CSR financial-highlights | WORKS — DXYZ 5.71%, CET 4.64%, GAB 11%, RVT 14%, ADX 55.6% |
| DXYZ official NAV/share | DXYZ 424B3 prospectus supplements | WORKS — $24.56 as-of 2026-03-31 (424B3 2026-05-12) |
| Arm-B holding prices (L1 equities) | any equity feed / IBKR | WORKS — trivial, daily |
| Live market price (premium/discount) | IBKR snapshot | WORKS — DXYZ last $25.38, bid/ask 25.27/25.44 |
| Dead-fund / survivorship membership | EDGAR ticker map + submissions last-filing | WORKS — BKCC death documented (last filing 2024-03-28) |

## What is BLOCKED or hard (the honest gaps)

1. **DXYZ daily official-NAV history.** DXYZ has NO XBRL companyfacts feed. Its official NAV is
   published quarterly via 424B3 supplements (point estimates: $24.56 @ 3/31) and on Destiny's own
   site, not as a clean daily series. A 2–3yr **daily** NAV backtest series for DXYZ does not exist
   from free primary sources at daily granularity — it is quarterly/episodic. **This caps the DXYZ
   backtest to event-spaced observations, not a daily panel.**

2. **The L3 re-mark itself, for private holdings.** DXYZ's L3 names (Anthropic, SpaceX, OpenAI,
   Databricks, Stripe, Shield AI…) have NO continuous markable price. The official mark moves only
   on discrete events (a new round, a secondary, an IPO, or a comp/credit pass-through the fund
   elects). So the derived-NAV signal for Arm A fires **episodically, on detected private-round /
   comp events**, not daily. This is consistent with the moat thesis (the predictability is in
   anticipating the next discrete mark), but it means Arm A's event count is **low-N by nature** —
   a real statistical-power constraint for the §7 hit-rate test.

3. **BDC holdings as a daily-markable feed.** Blocked as above (no NPORT). A BDC re-mark would
   require parsing each 10-Q Schedule-of-Investments table and mapping loans to a credit-spread
   comp — feasible but a much larger build, and still only quarterly holdings.

4. **NPORT history depth.** `submissions.recent` covers ~1yr of NPORT; older filings need the
   paginated shards (added on demand). Not a blocker, just an extra fetch for the 2–3yr window.

## The tractable subset (what Phase 2 can actually run)

- **Arm A engine-tractable: DXYZ only** (clean, traded, NPORT-filing, L3 67.9%, turnover 5.71%).
  Backtest is **event-spaced** (quarterly NPORT + episodic private-round marks + 424B3 NAV prints),
  not a daily panel. Free out-of-sample (spec §8) is the cleanest near-term signal: hold a derived
  NAV and score the next official print cold.
- **Arm B control: ADX / USA / RVT / GAB** — fully tractable (daily L1 prices, NPORT holdings,
  N-CSR turnover). RVT/GAB are low-turnover (14% / 11%); ADX is high (55.6%) and should be gated
  out or caveated; USA turnover pending.
- **Excluded (correct, per locked rule):** CET (L3 24.2%, middle band).
- **Survivorship:** BKCC documented as the in-window BDC death; teeth are limited because the whole
  BDC arm is engine-blocked anyway.

## Honest verdict

The **classifier and the engine work and tie out to primary-source official NAV** (DXYZ to the
penny; ADX exactly). The **moat split is real and verifiable** (DXYZ 67.9% L3 of genuinely
private names vs ADX/USA/RVT/GAB 0% L3). But the clean A/B test is **asymmetric in tractability**:
Arm B is a rich daily panel; Arm A reduces to **one fund, event-spaced, low-N**. The pilot can run
a *directional* preliminary A−B and the DXYZ forward out-of-sample now, but a statistically powered
§7 test needs either (a) more NPORT-filing venture/pre-IPO CEFs in Arm A, or (b) building the BDC
10-Q Schedule-of-Investments parser to unlock the six high-moat BDCs. Both are Phase-2 scope items.
