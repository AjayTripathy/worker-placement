### DAL (Delta Air Lines — US network carrier + SkyMiles/Amex loyalty + Monroe refinery) — screen "tsa weekly-sum z4v13 = −3.2, yoy = null" — **SCREEN-ARTIFACT**

**KILL FACTS (the flag, not the company)**
- The flag's only seasonality-neutral leg is missing (`yoy_pct: null`). A 4-week-vs-13-week z on *unadjusted weekly levels* over late Aug/early Sep mechanically prints deep-negative as the summer peak rolls off (Labor Day is the last peak; TSA's own daily/weekly files are the authority: https://www.tsa.gov/travel/passenger-volumes, weekly primaries e.g. https://www.tsa.gov/sites/default/files/foia-readingroom/tsa-throughput-data-to-august-9-2026-to-august-15-2026.pdf). **Corrected value: indeterminate / UNVERIFIED** — not −3.2σ of demand. Defect class: family (3)-adjacent — mis-specified window on a seasonal series, no YoY control. FILE IT.
- Series-integrity hit: TSA restated throughput for 1 Mar–13 Jun 2026 after **understating** ATL/MCO/MIA/LAX/LGA/BOS — i.e. Delta's own hub (vendor report, non-primary, authority = FlightBI reading TSA restatement: https://flightbi.com/tsa-update/). Any z computed across a restated/unrestated boundary is void. Recompute or drop.
- Cohort mapping error confirmed: WYNN's Macau leg is DICJ GGR, not TSA — cohort defect (SCREEN-MISCLASSIFIED for WYNN, not DAL).
- Evidence-pack corrections (do not use for math): pack `rev` series ends **2018-03-31** (8 yrs stale); `sbc` is **empty** → SBC-vs-dilution untestable from pack; `ocf` entries are all March-quarter point prints → no TTM. Primary only: https://www.sec.gov/Archives/edgar/data/0000027904/000002790426000031/dal-20260630.htm
- Net-cash claims are inadmissible: Air Traffic Liability $10.0B is customers' money (family 2); Delta reports adjusted *net debt*, exact figure not retrieved → UNVERIFIED (https://ir.delta.com/news/news-details/2026/Delta-Air-Lines-Announces-June-Quarter-2026-Financial-Results/default.aspx).

**LIVE FACTS (company contradicts the flag)**
- June-2026 quarter: record revenue $17.7B, +14% on ~1% capacity; adj TRASM +12.4%; main-cabin unit revenue positive 2nd straight quarter; op margin 8.8%; EPS $1.56; FY26 guide affirmed adj EPS $6.50–7.50, FCF $3–4B; dividend +15%; debt paydown (same PR + https://www.sec.gov/Archives/edgar/data/27904/000002790426000029/deltaairlinesannouncesjune.htm).
- Real cycle stress is **cost**, not demand: highest quarterly fuel expense in company history, CASM +21%, CASM-Ex +6.8%, variable-rate debt 22% (10-Q above). Q2 FCF was only $209M on $1.4B capex.
- PRICED BY WHOM: ~25 analysts polled, consensus target $104.77 (authority: stockanalysis.com/S&P Global poll, https://stockanalysis.com/stocks/dal/forecast/) — not an orphan, so FAIR-CARRY's uncovered-paper edge does not apply. Tape $78.75, −17.7% off 52w high. Book: no position.
- PRINT PROXIMITY: 2026-10-08 is yfinance-derived, **UNCONFIRMED**; Delta's pattern is a webcast PR ~3 weeks prior (https://ir.delta.com/news/news-details/2026/Delta-Air-Lines-Announces-Webcast-of-June-Quarter-2026-Financial-Results/default.aspx).

**RESOLVES ON:**
- ~2026-09-15/22: Delta webcast-date 8-K/PR confirms the Q3 date (kills the yfinance guess).
- Q3 print (est. 2026-10-08/12): Sept-quarter EPS vs guided $2.00–2.50; FY FCF $3–4B intact?
- Weekly: rebuilt YoY-of-weekly-sum on restated TSA + Delta domestic RASM commentary.

**Disposition:** WATCH + tripwire — reopen only if (a) rebuilt YoY TSA prints ≤−3% for 3 consecutive weeks, or (b) Delta cuts FY26 EPS/FCF guidance. No advance to court: flag unreproducible, name fully covered.