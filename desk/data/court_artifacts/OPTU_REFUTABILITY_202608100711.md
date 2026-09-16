## Context

OPTU is the former Altice USA (ATUS), renamed Optimum Communications on 2025-11-07. The screen filed it under a "Cable & Other Pay Television" secular-decline cohort — but the −72.4% drawdown is **not** a secular-decline print. It is a solvency event: the 10-Q filed 2026-08-06 carries an explicit going-concern qualification. The cohort narrative and the actual price driver are on different axes.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| OPTU | **STRUCTURAL** (capital structure, not business model) | Committed financing against the **$4,122.5M April-2027 maturity** — *not* broadband PSUs | **NONE committed.** 10-Q (period 6/30/26, filed 8/6/26): "substantial doubt exists about our ability to continue as a going concern"; cash $1,296.3M vs $6,347.5M of 2027 maturities ($4,122.5M Apr + $2,225.0M Jul); Q2 FCF **−$91.9M** vs +$28.4M yr-ago; net debt $25,333M @ **8.0x** L2QA; equity **−$5.2B**. [10-Q](https://www.sec.gov/Archives/edgar/data/0001702780/000170278026000048/optu-20260630.htm) · [Q2 release](https://investors.optimum.com/news-events/press-releases/detail/239/optimum-reports-second-quarter-2026-results) | 2026-11-05 (yfinance-derived, UNCONFIRMED) — **but Q2 already landed 2026-08-06** | The cohort narrative is *separately* half-refuted: broadband PSU −40k improved from −64.2k in Q1, Adj EBITDA margin 38.8% **+140bps**, mobile +49.9k (record Q2). Operations are decaying slowly; the equity is not pricing operations. |

**Two-axis read (the reason this row is not DAMAGE-ABSENT):**

- *Cohort axis (secular decline)* — **partially refuted.** Broadband rev $840.9M (−5.1%), total rev $2,023.7M (−5.8%), Adj EBITDA $785.7M (−2.2%) with margin **expanding**. A −72% drawdown is not what this operating trend prices.
- *Actual axis (solvency)* — **confirmed, and the discount is correct.** LTM Adj EBITDA ≈ $3.14B. Equity requires EV > $25.3B net debt = **>8.0x**; cable comps clear 5.5–7x. The common is struck roughly **$5B out of the money** with ~8 months to the April-2027 wall.

**The dispositive disclosure is insider positioning, not the numbers.** Per the company's own June 1 2026 announcement ([IR](https://investors.optimum.com/news-events/press-releases/detail/233/optimum-launches-effort-to-drive-a-consensual-repositioning) · [as filed](https://www.sec.gov/Archives/edgar/data/1702780/000121390026063161/ea029287101ex99-1.htm)): CSC II issued **$300M Series A Preferred at 13% cash / 15% PIK**; board members and executives **exchanged their common for $212.5M of those preferred units**; the company then tendered for **120M unaffiliated shares at $2.50** (completed July 2026). The stock is now $0.7689. Insiders moved *up* the capital structure into the asset-recipient entity and cashed the public out at 3.3× the current price; the remaining common is the stub they vacated. Share count fell to **272,565,547** (7/31/26) with 206M in treasury.

The stated rationale is that the June-2024 **Co-Op Agreement** (~99% of CSC Holdings debt) blocks facility-specific deals, and a conventional debt-for-equity swap could trigger a **>$4B tax liability**. Optimum has filed an antitrust challenge to that agreement — a genuine wildcard, but it is litigation against an organized 99% creditor bloc, not a valuation argument.

## COURT-WORTHY (damage-absent, ranked)

**None.** No member qualifies as damage-absent. OPTU's operating damage is milder than the cohort prices, but the equity's discount is governed by a going-concern solvency event that a court cannot re-rate. Escalating this to a red/blue court would burn a bench on a name where the sizing answer is already determined.

**COURT-WORTHINESS OPTU: 3/10** — going-concern equity stub ~$5B out of the money with insiders already exchanged into 13% preferred; a court changes nothing about a no-position book.

**PRINT PROXIMITY: NONE within 5 trading days — Q2 print already landed 2026-08-06** (10-Q accession 0001702780-26-000048 + 8-K 0001702780-26-000042, both in the evidence pack's filing list and confirmed against the filed 10-Q covering the period ended 6/30/26). Next print 2026-11-05 is yfinance-derived and UNCONFIRMED. The live catalyst is not a print — it is the CSC Holdings restructuring negotiation, which can produce headlines on any day.

**PRE-PRINT POSITION: FLAT.** Not a valuation call and not a price-gate candidate — response-taxonomy class is *data/solvency*, which kills rather than tranches. There is no price at which this equity is a diligence-supported long ahead of the April-2027 wall; the instrument where work would actually pay is the CSC Holdings paper, not the common.

## Three corrections to the evidence pack

1. **Market cap is stale.** Pack says $366,356,745; post-tender it is 272,565,547 × $0.7689 = **~$209.6M**. The pack is running the pre-tender share count.
2. **XBRL block is stale/mis-framed.** Latest revenue shown is 2025-06-30 = $2,147.2M; actual Q2 2026 = $2,023.7M. `dil_sh` 467,744k predates the 120M-share tender. Do not use this block for per-share math on OPTU.
3. **Entity label.** Pack carries "Optimum Communications, Inc." but sector routing still treated it as a going-concern operating comp; it should carry a distressed/restructuring flag that suppresses cohort-dislocation routing.

## Provenance and two blockers

- **SEC.gov returned 403 to every WebFetch call** (no custom User-Agent available in this session, and no Bash to curl with one). The Q2 press release was fetched directly from the company IR site (primary). The 10-Q figures — going-concern language, maturities, cash, share count — were read through a filing mirror, not from EDGAR directly. They are internally consistent with the IR release, but **a court citing the going-concern wording verbatim should re-pull `optu-20260630.htm` from EDGAR with a proper UA first.**
- **IBKR `get_price_snapshot` permission was not granted** (non-interactive session), so the $0.7689 price is the pack's Yahoo mark, not a live IBKR quote. This violates the standing live-price rule; it is not load-bearing here (the conclusion holds anywhere in the $0.58–$2.79 52-week range), but flagging it rather than letting it pass silently.

**Dashboard close-out could not be executed** — no Bash tool and no read access outside the working directory in this session, so I could not upsert the ledger, re-run the scanner, or verify via `/api/everything`. The payload to apply: `OPTU → class STRUCTURAL, edge_classification REJECT (solvency), entry_plan NONE, court_worthiness 3/10, no escalation`, plus the three pack corrections above.