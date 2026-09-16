"""lse_shelf — the LSE MAIN + AIM leg of the global small-value screen.

================================ README ================================
WHAT IT SCREENS
  UK-listed operating companies, roughly USD 50M - 2B of market cap, on the two venues the
  Euronext/Nordic leg does not reach: the LSE Main Market and AIM. Sibling of
  `verticals/generators/euronext_shelf.py` — same composite, same guards, same rule that
  this is a UNIVERSE + RANKING engine and never the source of record. Anything that reaches
  a court is re-derived from the primary filing.

WHY THE UK IS ITS OWN LEG (and not just another Euronext venue)
  Three things are structurally different here and each is scored, not assumed:
    1. WITHHOLDING TAX IS ZERO. The UK levies no dividend withholding on a US holder. Every
       other venue on the Euronext leg runs 15-35% with a treaty reclaim that costs paperwork
       and months of float. On an income-ish value name that is 15-35% of the dividend, kept.
       It is a REAL edge and `wht_edge_bps` prices it against a 15% treaty-reclaim baseline.
       CAVEAT: the 0% is a UK-INCORPORATION fact, not a UK-listing fact. Plenty of LSE lines
       are Irish, Jersey, Guernsey, South African or US issuers, and those carry their own
       home-country rate. Incorporation is read per name from the exchange's own instrument
       record (`country`), never inferred from the .L suffix.
    2. STAMP DUTY / SDRT IS A REAL 0.5% FRICTION ON PURCHASES — one-way, unavoidable, and
       equivalent to giving back roughly a year of a 50bp edge on entry. It is NOT uniform:
       AIM-quoted shares have been SDRT-exempt since April 2014, and non-UK-incorporated
       issuers are outside the charge. So the friction is a function of (market, country of
       incorporation) and is emitted per name as `stamp_pct`. An AIM name and a Main-Market
       name at the same multiple are NOT the same price.
    3. CLOSED-END INVESTMENT COMPANIES DOMINATE THE MAIN MARKET. 306 of the 1,013 Main-Market
       equity lines — 30% — are ICB 302040 Closed End Investments. They are a different lane
       (NAV-discount, not Graham cheapness) and are excluded by the exchange's own sector
       classification rather than by guessing at names.

UNIVERSE — PRIMARY, from the exchange itself
  The universe is NOT a Yahoo screener sweep. It is the London Stock Exchange's own
  price-explorer service (api.londonstockexchange.com), swept per (market x ICB sector):
      POST /api/v1/components/refresh
        path       = live-markets/market-data-dashboard/price-explorer
        parameters = markets={MAINMARKET|AIM}&categories=EQUITY&sectors={icb}&indexname=
  It returns, per line: TIDM, ISIN, issuer code, issuer name, share-line description, ICB
  sector, quote currency, last/mid price, 52-week high/low and market capitalisation. That
  is better than a screener in four ways that matter: (a) it is complete — no result cap, so
  no silently-truncated sector; (b) it carries the MARKET SEGMENT, which is what decides
  stamp duty; (c) it carries the ISIN, which is the join key to the Takeover Panel's live
  offer-period table; (d) it carries the exchange's own ICB sector, which is what excludes
  the investment trusts. Yahoo is used only for FUNDAMENTALS and price history, keyed off a
  TIDM -> Yahoo-symbol mapping (`_yahoo_sym`).

SCORING — identical to the Japan/Korea/ESEF/Euronext legs, NOT reimplemented
  `verticals/deep_value/score.py` is imported: composite = mean of rank-percentiles across
  {EV/EBIT, FCF-yield, P/B, net-cash/mktcap, NCAV/mktcap}, plus its guards (sub-cash,
  cash-burner, holdco/NCI, MLP-artifact, negative equity, WC-driven FCF, one-time-gain).

HOW TO RE-RUN
  python3 lse_shelf.py --refresh-universe      # monthly; ~90 LSE API calls, writes LSE_UNIVERSE.json
  python3 lse_shelf.py --top 30                # score (fundamentals cached; --refresh-fund to redo)
  python3 lse_shelf.py --min-mcap-usd 5e7 --max-mcap-usd 2e9 --min-adv-usd 75e3
  Outputs: data/LSE_SHELF.json ({meta, rows}) — the full scored shelf.

GUARDS — every one is a COLUMN; nothing is silently excluded except funds/financials
  (a) PENSION / IAS-19 — the guard this build was written around, and the one that is
      CRITICAL here rather than merely useful. Defined-benefit schemes are pervasive among
      UK industrials of exactly this vintage and size, and a book-reserve or deficit-funded
      scheme is DEBT-LIKE while being completely invisible to a net-cash view built from
      Yahoo's balance sheet. The SFPI.PA court (2026-08-03) is the precedent: EUR 50.6M of
      unfunded retirement obligations — a Key Audit Matter for both auditors — turned "39% of
      the cap in net cash" into 12-18% and EV/EBIT 4.5x into 6.0-6.5x.
      Implementation, in order of preference:
        explicit pension tag -> long-term-provisions proxy -> NOTHING FOUND.
      The obligation is ADDED to the debt slot before the composite sees it; the raw tag stays
      auditable in `debt_ex_pension`. Four UK-specific extensions over the Euronext version:
        * IT IS ADDED NET OF TAX, NOT GROSS. The Euronext leg adds the gross obligation, which
          over-captures — a deficit is deductible as it is funded, so the claim standing ahead
          of the equity is the after-tax number. SFPI's court did exactly this: EUR 51M gross
          became EUR 38.3M net of the 25% French rate and EV/EBIT went 4.58x -> 6.06x. The UK
          main rate is also 25%. `pension_gross` and `pension_net_of_tax` are both emitted.
        * A SURPLUS IS NOT AN ASSET YOU OWN. UK schemes are increasingly in accounting
          surplus after the 2022-23 rate move, and the IAS-19 asset lands on the balance
          sheet and inflates book equity — flattering P/B — while being unavailable to
          shareholders absent a buyout or a wind-up with a surplus-refund (and a 25% charge).
          `pension_surplus_in_equity` flags it; the surplus is NEVER netted into cash.
        * DEFICIT-REPAIR CONTRIBUTIONS ARE A CASH CLAIM AHEAD OF THE EQUITY and they run
          through operating cash flow, so FCF already carries them — but a scheme in deficit
          with a recovery plan can absorb years of FCF. `pension_deficit_r` sizes the
          obligation against market cap; > 25% is a hard read-the-note flag.
        * `pension_unverified` fires when NO pension or provisions tag is found on a name
          whose sector is one where DB schemes are the norm. For those, treat net cash as
          UNVERIFIED, not clean. Absence of a tag is absence of evidence.
      A provisions proxy is NOT a verification — provisions also carry warranty,
      restructuring, dilapidations and litigation, so it OVER-captures. Flagged as a proxy so
      the promoter reads the IAS-19 note before sizing.

  (b) FCF = CFO MINUS TOTAL CAPEX. Verified empirically on this universe (2026-08-04):
      yfinance's `Capital Expenditure` on UK filers ALREADY equals Purchase-of-PPE plus
      Purchase-of-Intangibles — TW.L 6.7 = 4.2 + 2.5, SGE.L 59 = 41 + 18, ITV.L 54 = 26 + 28.
      So the total-capex requirement is SATISFIED by that tag, and adding the intangibles
      line again would double-count. The split is emitted anyway (`capex_ppe`,
      `capex_intangibles`) and `capex_intang_heavy` fires when intangibles exceed 40% of
      capex — capitalised development cost is an earnings-quality tell, and the UK small-cap
      software cohort is where it lives. `capdev_r` sizes it against SALES, which is the form
      the Tecnotree catch took: EUR 9.7M of capitalised development, 13.4% of sales, was the
      entire wedge between a EUR 14.8M screen FCF and the company's own reported EUR 4.6M.
      Above 8% of revenue `capdev_heavy` fires and the FCF yield should not be trusted until
      the intangibles note is read. This check has fired on 3-4 of every 8 verified names
      across the US, Japan and Europe batches.
      What FCF does NOT capture, and is flagged instead of silently adjusted: IFRS-16 LEASE
      PRINCIPAL. Under IFRS-16 the principal repayment sits in FINANCING, so operating cash
      flow is structurally flattered for lease-heavy models (retail, hospitality, leisure)
      relative to the pre-2019 series. yfinance does not separate lease principal from debt
      repayment, so no reliable numeric adjustment exists; `lease_heavy` fires when
      capitalised lease obligations are the majority of total debt AND exceed 25% of market
      cap, and the reader is told the FCF yield is overstated for those names.

  (c) EARNINGS DURABILITY, WITH THE CASH-GENERATION CONDITION. The base guard (inherited from
      the Euronext leg's Cantargia catch) fires on three shapes: revenue appearing from ~zero
      or tripling year on year; EBIT flipping out of a prior-year loss; EBIT positive while
      FCF is negative. Those catch a licensing upfront or a lumpy project completion, which
      Yahoo's normalised operating income cannot see because the windfall arrives as REVENUE,
      not as an unusual item.
      THE CORRECTION APPLIED HERE: the raw test over-fires on genuine turnarounds. A company
      whose EBIT flipped out of a loss but which ALSO converted that EBIT into cash — positive
      FCF now and positive operating cash flow in the prior year — is not a one-year artifact;
      it is a business that was cash-generative through the loss and has now cleared the
      accounting line. Those are DEMOTED-TO-WATCH (`durability_watch`) rather than dropped
      from the printed table. The accrual-gap shape (EBIT up, FCF negative) is NEVER rescued
      by this condition, because the condition IS cash generation and that shape fails it by
      construction.
      PROVENANCE, stated plainly: this condition existed in the desk's notes only BY
      REFERENCE. The backtest behind it found that the raw guard BLOCKS HUBS — the desk's
      single best position — and `quality_drawdown.py` carries an explicit docstring
      prohibition on porting the unconditioned guard into it. The fix itself was never
      written. This is its first implementation, and the HUBS shape is exactly what it
      rescues: GAAP EBIT crossing out of a loss while free cash flow was strongly positive on
      both sides of the cross. It has NOT been backtested on this universe.

  (d) EBIT TREND, TROUGH-ANCHORED. `ebit_trend` on the Euronext leg is current EBIT over the
      OLDEST annual EBIT on file, which silently assumes the oldest year is representative.
      It usually is not: if the base year happens to be the cyclical trough, a flat business
      prints a flattering "3.2x uptrend" and the melting-ice-cube guard goes quiet exactly
      when it should not. Both anchors are computed here:
        `ebit_trend`      = current / oldest   (kept for comparability with the Euronext leg)
        `ebit_vs_peak`    = current / max(history)   — the decline that actually matters
        `trough_anchored` = the oldest year IS the minimum of the history
      `melting` now fires on ebit_vs_peak < 0.5 (a real halving from the peak) and
      `trend_flattered` fires when the base year is the trough AND ebit_trend looks strong
      while ebit_vs_peak does not. Informational, never a demotion: a trough multiple on a
      cyclical is the buy and on a structural decliner is the trap, and only a human reading
      the business can tell which.

  (e) LIQUIDITY — MEDIAN, NOT MEAN. Yahoo's `averageDailyVolume3Month` is an arithmetic mean,
      and on a 400k-shares-a-day AIM name a single 8M-share block trade lifts the 3-month mean
      by ~10% and can carry a name over an ADV floor it never actually clears. ADV here is the
      MEDIAN of daily turnover over the last 63 sessions, computed from the daily bar series.
      `adv_mean_usd` is kept alongside and `adv_block_inflated` fires when the mean exceeds the
      median by more than 2x — that name trades by appointment.
      Executability is separately evidenced from the exchange record: live `bid`/`offer` give
      `spread_bps`, and `nms_shares` (normal market size) is the size a market maker is
      obliged to quote. A tight-looking screen candidate with a 400bp touch is not acquirable.

  (f) PATH — `pct_off_52w_low` and `days_since_low`, from the daily series. A composite is a
      SNAPSHOT and cannot tell a name that has been dead cheap for a year from one that fell
      off a cliff last week; the second is a falling knife with a news event behind it and the
      first is neglect. `fresh_low` fires under 30 days since the low, and `entry_exhausted`
      reproduces `quality_drawdown.py`'s two late-entry modes on identical constants so the
      two screens grade a path the same way: a big bounce (>35%) off a FRESH low (<90 days),
      or a very big bounce (>50%) off any low.

  (g) SHARE-COUNT / DUAL-CLASS VERIFICATION. The failure mode is arithmetic and needs no
      filing to detect: a vendor's `sharesOutstanding` is frequently ONE SHARE CLASS while its
      `marketCap` is the whole company, so cap divided by count does not reconcile to the
      traded price and every per-share ratio is wrong by the size of the missing class. HOOD
      is the specimen — 790.6M Class A quoted, 109M Class B omitted, a 12% market-cap error
      that flowed straight into P/E and P/S; TUYA the same shape. Four counts are cross-
      checked here: the filing's Ordinary Shares Number, the vendor's share count, the count
      implied by the vendor's own market cap over the price, and the count implied by the
      EXCHANGE's market cap over the exchange's price. `share_count_divergence` is the worst
      pairwise gap and `share_count_unverified` fires above 5% — or when fewer than two
      independent counts exist at all, because one unconfirmed number is not a verification.
      Separately, the exchange's issuer code groups every LINE of one issuer, so a
      genuine dual-class or multi-line structure is visible directly: `n_lines` > 1 sets
      `multi_line_issuer`, and the dedup keeps the most liquid ordinary line rather than
      scoring the same fundamentals twice.

  (h) PFIC — the shared gate is ON here, against the Euronext leg's precedent, plus the
      fair-market-value overlay. `verticals/deep_value/pfic_screen.py` is imported, not
      reimplemented: the ASSET test proxies passive assets over total assets at 50%, and the
      INCOME test proxies conjunctively (revenue/assets < 10% AND passive >= 40%) — a real
      operating business with revenue against its asset base is active.
      WHY THE EURONEXT SKIP DOES NOT TRAVEL. That leg argues EU/EEA operating companies in
      this band are not a PFIC population. London breaks the argument twice over: the UK's
      closed-end investment companies are statutory PFICs almost to a name (they are excluded
      here by ICB sector, but the line between "investment company" and "cash-rich holdco" is
      porous and that sector tag is the only thing holding it); and §1297's asset test on a
      PUBLIC issuer runs on FAIR MARKET VALUE, so the denominator is roughly market cap plus
      liabilities, not book assets.
      THE MECHANISM (PDD court, 2026-08-04) is that A DE-RATE MANUFACTURES THE STATUS: passive
      assets sit fixed in the numerator while the denominator collapses with the multiple. So
      drawdown is not a coincidence with PFIC risk, it is a CAUSE of it — and a cheapness
      screen is precisely the instrument that concentrates the exposure. An earlier reading of
      the EDINET shelf recorded "the PFIC gate anti-selects on drawdown" as a gate DEFECT;
      that court reversed it — the anti-selection is the mechanism working correctly.
      `pfic_fmv_share` carries the FMV ratio, the flag fires at 0.50, and `pfic_watch` marks
      the 0.45-0.50 band, where the tell is the year-over-year diff of the risk-factor
      sentence itself ("we do not believe we were a PFIC" -> "it is possible that we were").
      Nothing is dropped. A genuine net-cash bargain is the name most likely to trip this, and
      the answer is a QEF or mark-to-market election, not avoidance.

  (i) LIVE OFFER PERIOD + SECTOR TAKEOUT HEAT. The Takeover Panel publishes its Disclosure
      Table daily — every company currently in an offer period under the Code, with its ISIN
      and its named offeror. Joined on ISIN (the LSE universe carries it), which is exact,
      not fuzzy. `in_offer_period` means the name is a merger-arb, not a value screen
      candidate, and it is DEMOTED from the printed table. Aggregated up, the same table is a
      free read on where private equity is actually hunting: `sector_takeout_heat` counts live
      offer periods in the name's ICB sector and `pe_bid_sector` fires when at least one of
      those offerors is a financial sponsor. Sector heat is not a reason to own a name — it is
      a reason to believe the pond's discount has a closing mechanism.
      AND THE COHORT WARNING THAT GOES WITH IT: the bank-consolidation screen measured its own
      cohort's realised takeout multiples at 0.77-1.06x tangible book against a cohort trading
      at a 1.41x median — a takeout there is a DOWN round. Nothing on this shelf has been
      measured that way, so `sector_takeout_heat` is a liquidity-of-exit observation and
      nothing more. An acquisition is a free option; it is never a thesis.

  (j) FINANCIALS + VEHICLES EXCLUDED FROM THE GRAHAM SCORE. ICB 3xxxx financials, both REIT
      sectors, real estate, and both investment-vehicle sectors. "Net cash" is meaningless for
      a deposit-taker and NAV-discount is a different lane. Counts reported; rows stay in the
      universe file. A second pass on Yahoo's industry tag catches strays.

  (k) TRUST / CLIENT-CASH (the OTB.L catch, inherited). Travel, betting, payments, ticketing,
      insurance-broking and estate agency hold ring-fenced CUSTOMER float on the face of the
      balance sheet; netting it manufactures phantom EV. Flagged names are scored on the
      TRUST-SAFE variant (EV with no cash netting). ICB 405010 Travel and Leisure is added to
      the industry/name regexes as a sector-level trigger.

  (l) NON-EQUITY / SHARE-LINE HYGIENE. The exchange lists preference shares, warrants,
      nil-paid rights, convertibles and B-share lines in the same EQUITY category. Filtered on
      the instrument description, which is the exchange's own text ("ORD 5P" vs "8% CUM PREF"
      vs "WTS TO SUB FOR ORD"). Note that "(DI)" — Depositary Interest — is NOT filtered: that
      is how a legitimately non-UK-incorporated operating company settles in CREST, and
      Somero, a real business, trades that way.

  (m) CURRENCY PLANE. Quote currency is GBX (pence) on essentially every line while the
      REPORTING currency is frequently GBP, USD or EUR — miners and oil names report in USD
      as a rule. Market cap is bridged into the reporting currency exactly once, in
      `_to_fin_ccy()` (which divides GBX by 100 first), and every ratio is then single-plane.
      A median-P/B plane check runs before anything prints and hard-fails on a 100x error.
      This is the priceMagnifier lesson: unit conventions never transfer across venues.

  (o) CASH QUALITY + NET-DEBT SIGN RECONCILIATION — added after primary verification of the
      first run REFUTED a top-five name outright, and it is the most consequential guard here
      because it protects the SIGN of the metric everything else leans on.
      Capital Ltd (CAPD) printed "+11% of the market cap in net cash" and ranked 4th. Its own
      2025 annual report states NET DEBT of USD 31.8M. The screen was not slightly wrong; it
      had the sign backwards. The mechanism: `Other Short Term Investments` carried USD 99.8M,
      which is not a cash equivalent at all — it is a portfolio of LISTED JUNIOR MINER EQUITIES
      held at fair value through P&L. Netting a marketable-securities book against debt
      manufactures net cash out of net debt.
      Two independent checks, either of which demotes the name to a STRICT (true-cash-only)
      view that then governs EV, EV/EBIT, net cash and the composite:
        1. `securities_as_cash` — short-term investments are more than 25% of what the screen
           called cash;
        2. `netcash_sign_conflict` — the vendor publishes its OWN `Net Debt` line, and our
           computed net cash agreeing in sign with a positive net debt is a contradiction
           between two readings of the same balance sheet. Free, independent of our
           arithmetic, and it should always have been read.
      `ncash_r_asis` / `am_asis` preserve what the naive computation said, so the correction is
      auditable rather than invisible. On the first run this moved CAPD from +0.11 to -0.22 net
      cash and EV/EBIT 5.6x to 7.6x — reconciling to the filer's stated net debt exactly once
      the IFRS-16 lease liabilities inside Total Debt are backed out — and dropped it out of
      the top fifteen. It also cut Oxford Metrics from +0.66 to +0.24 net cash.
      A large securities book distorts the INCOME statement too: Capital booked a USD 66.0M
      realised and unrealised fair-value gain on those stakes in FY2025, which is a
      mark-to-market and not services earnings, and the unusual-items path cannot see it
      because it is not tagged unusual. `securities_book_material` fires above 20% of market
      cap so the reader knows to re-read the P&L as well as the balance sheet.
      LIMITATION: the vendor's `Net Debt` tag is present on only 133 of 249 shelf names, so
      check 2 is silent on the rest and check 1 carries the load there.

  (n) COVERAGE HONESTY. Yahoo throttles at universe scale and does it SILENTLY — 200s with
      empty statement frames, no exception. An empty frame is a RETRYABLE failure, never "this
      company has no balance sheet"; a circuit breaker stops the pass after BREAKER_N
      consecutive empties and preserves the cache; and per-market pull coverage is printed
      every run. A partial shelf that knows it is partial beats a full-looking shelf that
      quietly lost AIM.

WHAT THE FIRST RUN FOUND OUT ABOUT THE POND (2026-08-04, 1,599 lines -> 249 scored)
  1. THE MAIN MARKET IS MOSTLY NOT OPERATING COMPANIES. 310 of 989 Main-Market equity lines
     are closed-end investment companies, and 415 of 1,599 across both venues are investment
     vehicles or property once REITs and real-estate services are added. A screen that reaches
     the UK through a generic "region=gb" vendor query is scoring a fund register.
  2. AIM'S STAMP EXEMPTION IS MORE THAN EATEN BY ITS SPREAD, and the two are usually discussed
     as though only the first existed. Median touch on the AIM half of this shelf is 234bp
     against 20bp on the Main Market — an order of magnitude. Entry friction is therefore
     ~117bp (half-spread) on AIM against ~60bp (50bp SDRT + 10bp half-spread) on Main: AIM is
     roughly twice as expensive to enter DESPITE paying no stamp duty. Median AIM ADV is $244k
     against $1.32M, so the same names are also the ones you cannot size. The 0% withholding
     edge — worth ~60bp a year on a 4%-yielding name against a 15% treaty baseline — does not
     pay for a 234bp round trip in under two years of holding.
  3. THE OLDEST-YEAR EBIT ANCHOR FLATTERS NEARLY HALF THIS SHELF. `trough_anchored` fires on
     111 of 249 names: the earliest annual EBIT on file IS the minimum of the series, so the
     Euronext leg's `ebit_trend` would report an uptrend on 45% of the pond by construction.
     Anchoring on the peak instead moves 54 names into `melting`, and only 9 of those were
     visible to the old anchor.
  4. THE PFIC FMV OVERLAY DOES REAL WORK IN BOTH DIRECTIONS, and the direction it works in is
     the one the PDD court predicted. It ADDED exactly two names the book test cleared —
     GENL and OMG, the two most de-rated names near the top of the shelf (P/B 0.54 and 0.71) —
     because their collapsed market caps shrank the FMV denominator under the fixed pile of
     cash. And it CLEARED six names the book income-proxy had flagged, whose market caps are
     large against book. That is the mechanism stated exactly: the de-rate causes the status.
  5. UK DUAL-CLASS BARELY EXISTS. One multi-line issuer survived the dedup out of 249. The
     share-count guard still fires on 50 names (20%), but the cause is vendor-vs-filing
     vintage drift, not a hidden share class — which is the opposite of the US finding that
     motivated the guard, and is worth knowing before anyone reads a 20% fire rate as alarm.
  6. THE PROVISIONS PROXY IS LOAD-BEARING AND IT IS OFTEN NOT A PENSION. It supplies the
     obligation on 119 of 249 names against 60 explicit pension tags. Its single largest hit,
     Vistry at GBP 269.8M (30% of market cap), is Building Safety Act cladding remediation.
     Meanwhile 70 names return NO tag at all, 37 of them in sectors where DB schemes are the
     norm — Costain among them, a contractor with a large well-known scheme. On those, "net
     cash" is UNVERIFIED, not clean.
  7. PRIMARY VERIFICATION OF SIX NAMES REFUTED THREE SCREEN NUMBERS — read this before
     trusting any row. (a) CAPD's "+11% net cash" was NET DEBT of USD 31.8M per its own annual
     report; guard (o) was written in response and now corrects it. (b) CHH and COST were both
     flagged "no pension tag found" and BOTH have defined-benefit schemes — each in SURPLUS and
     each RECOGNISED as a balance-sheet asset (Churchill GBP 7.65M, 12% of its equity; Costain
     GBP 60.0M). So the screen's P/B is flattered on both and the surplus is not distributable.
     `pension_unverified` fired on both, which is the guard doing its job as a ROUTING flag
     even though the surplus detector itself is dead against this data source. (c) THX's EBIT
     is USD 199.7M, not the ~112M the screen carries, and its net cash is 28% not 32% — but
     the material omission is that USD 254M of Douta (Senegal) initial capex is earmarked
     against a USD 137.8M cash balance, so the 41% FCF yield is pre-committed. None of (c) is
     machine-readable from a balance sheet; it is a notes-and-commitments read, which is a
     court step. The screen cannot be fixed to catch it and should not pretend otherwise.

  8. THE LIVE-OFFER JOIN WORKS AND IS NOT COSMETIC. Nine shelf names are in a Code offer
     period today — Senior, Gooch & Housego, Advanced Medical Solutions, Gama Aviation
     (Epiris) among them — every one of which would otherwise have printed as a cheap
     industrial. They are merger arb, not value, and they are demoted.

KNOWN LIMITATIONS
  * Yahoo is a SECONDARY source for fundamentals. Fine for ranking; not evidence. Every name
    that reaches a court is re-derived from the annual report.
  * The pension guard's provisions proxy over-captures and its "nothing found" case is the
    dangerous one. It reduces a court-grade question to a screen flag; it does not answer it.
  * IFRS-16 lease liabilities sit inside Total Debt, so EV is overstated for lease-heavy
    models. Bias is conservative (bigger EV -> worse multiple -> no false bargain), and the
    matching CFO flattery runs the other way — for a lease-heavy retailer BOTH distortions
    are live at once and only the primary statements resolve them.
  * ADV and the path fields come from Yahoo's daily bars, which are consolidated and include
    off-book/OTC prints on some UK lines; treat the ADV as an upper bound on lit liquidity.
  * The Takeover Panel table is TODAY's state. A name that was taken out last year is not in
    it. A trailing-24-month takeout history would need the RNS archive and is not built.
  * Free float is Yahoo's `floatShares`, an estimate, and is absent for a real slice of AIM.
  * The universe is a STATIC snapshot; a delisting or a new admission is invisible until
    `--refresh-universe`.
  * `pension_surplus_in_equity` HAS NEVER FIRED — 0 of 249 on the first run — because Yahoo
    carries no pension-ASSET tag on UK balance sheets at all. The guard is written and is
    correct in principle (a UK scheme in surplus books an asset that inflates equity and
    flatters P/B while being unavailable to shareholders), but it is currently DEAD CODE
    against this data source and cannot be relied on. CONFIRMED against primary sources:
    Churchill China carries a recognised GBP 7.65M retirement-benefit ASSET (12% of its equity,
    and a key audit matter) and Costain a GBP 60.0M one — this screen sees neither, and both
    fell through to `pension_unverified`, which is the only reason they are flagged at all.
    Reading a surplus needs the annual report; it is a court step, not a screen step.
  * COMMITTED CAPEX AGAINST A CASH PILE IS INVISIBLE HERE. Thor Explorations' USD 254M of
    Douta initial capex, earmarked against a USD 137.8M cash balance, lives in the notes and
    the MD&A and on the face of nothing. A screen that reads balance sheets will keep scoring
    pre-committed cash as free cash. Treat `ncash_r` on any miner, developer or project
    business as a question rather than an answer.
  * `sector_takeout_heat` fires on 38% of the shelf, which is too broad to discriminate — 39
    live offer periods spread across a small number of ICB sectors light up most of them. The
    ISIN-exact `in_offer_period` (9 names) is the column that carries information; treat the
    sector aggregate as colour only.
  * The durability guard's cash-generation condition has NOT been backtested here. It rescued
    9 names on this run; whether any of them deserved rescuing is unknown until they are read.
  * IBKR conids are resolved OUT OF BAND (the IBKR MCP `search_contracts` tool) and merged
    from data/lse_conids.json. Missing = "not yet verified", never "not executable".
========================================================================
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
# reuse the shared composite + guards (never reimplemented) — verticals/deep_value/score.py
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "deep_value"))
import score as S                                              # noqa: E402
import pfic_screen as P                                        # noqa: E402

DATA = os.path.join(HERE, "data")
UNIVERSE = os.path.join(DATA, "LSE_UNIVERSE.json")
FUND_CACHE = os.path.join(DATA, "lse_fund_cache.json")
CONIDS = os.path.join(DATA, "lse_conids.json")
OFFERS = os.path.join(DATA, "LSE_OFFER_PERIODS.json")
OUT = os.path.join(DATA, "LSE_SHELF.json")

LSE_API = "https://api.londonstockexchange.com/api/v1/components/refresh"
LSE_INSTRUMENT = "https://api.londonstockexchange.com/api/gw/lse/instruments/alldata/"
PRICE_EXPLORER_COMPONENT = "block_content%3A9524a5dd-7053-4f7a-ac75-71d12db796b4"
TAKEOVER_PANEL = "https://www.thetakeoverpanel.org.uk/disclosure/disclosure-table"
# gov/enterprise sites check the full Chrome fingerprint, not just the UA
UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-GB,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": "https://www.londonstockexchange.com",
    "Referer": "https://www.londonstockexchange.com/",
}

MARKETS = {"MAINMARKET": "LSE Main Market", "AIM": "AIM"}

# ICB sectors whose balance-sheet semantics break the Graham score, plus the vehicle sectors.
FIN_SECTORS = {
    "301010": "Banks", "302010": "Finance and Credit Services",
    "302020": "Investment Banking and Brokerage Services",
    "302030": "Mortgage Real Estate Investment Trusts",
    "302040": "Closed End Investments",
    "302050": "Open End and Miscellaneous Investment Vehicles",
    "303010": "Life Insurance", "303020": "Non-life Insurance",
    "351010": "Real Estate Investment and Services",
    "351020": "Real Estate Investment Trusts",
}
# (k) sector-level trigger for the client-cash guard
TRUST_SECTORS = {"405010"}          # Travel and Leisure
# (a) sectors where a legacy DB scheme is the NORM, so a missing tag is suspicious
DB_PENSION_SECTORS = {
    "502010", "502020", "502030", "502040", "502050", "502060",   # industrials
    "501010", "551010", "551020", "552010",                        # construction / materials / chemicals
    "402020", "403010", "404010", "451010", "451020", "452010",    # legacy consumer / media / retail
    "651010", "651020", "651030",                                  # utilities
}

FX_FALLBACK = {"USD": 1.0, "GBP": 1.34, "EUR": 1.16, "SEK": 0.105, "NOK": 0.099,
               "DKK": 0.156, "CHF": 1.25, "CAD": 0.73, "AUD": 0.65, "ZAR": 0.055,
               "JPY": 0.0066, "ILS": 0.30, "SGD": 0.78, "HKD": 0.128}
FX_PAIRS = {"GBP": "GBPUSD=X", "EUR": "EURUSD=X", "SEK": "SEKUSD=X", "NOK": "NOKUSD=X",
            "DKK": "DKKUSD=X", "CHF": "CHFUSD=X", "CAD": "CADUSD=X", "AUD": "AUDUSD=X",
            "ZAR": "ZARUSD=X", "JPY": "JPYUSD=X", "SGD": "SGDUSD=X", "HKD": "HKDUSD=X"}

# (1) WHT by country of INCORPORATION, not of listing. The 0% is the UK edge; everything else
#     on this shelf is a foreign issuer that happens to quote in London.
WHT = {"GB": ("0%", 0.0), "JE": ("0%", 0.0), "GG": ("0%", 0.0), "IM": ("0%", 0.0),
       "BM": ("0%", 0.0), "KY": ("0%", 0.0), "VG": ("0%", 0.0), "GI": ("0%", 0.0),
       "IE": ("25%r", 0.25), "US": ("30%", 0.30), "ZA": ("20%r", 0.20),
       "AU": ("30%r", 0.30), "CA": ("25%r", 0.25), "IL": ("25%r", 0.25),
       "FR": ("25%r", 0.25), "NL": ("15%", 0.15), "LU": ("15%", 0.15),
       "CY": ("0%", 0.0), "SG": ("0%", 0.0), "HK": ("0%", 0.0)}
TREATY_BASELINE = 0.15      # what a reclaimed European position realistically lands at

# (l) share lines that are not the ordinary equity. The exchange's own instrument description.
NON_ORD = re.compile(
    r"(\bPREF(ERENCE|ERRED)?\b|\bCUM\b|\bCNV\b|\bCONV\b|\bWT?S\b|\bWARRANT|NIL PAID|\bNPV RTS\b"
    r"|\bRIGHTS?\b|\bDEB\b|\bLN\b|\bLOAN NOTE|\bUNSEC\b|\bSUBORD|\bGDR\b|\bADR\b|\bADS\b"
    r"|DEPOSITARY RECEIPT|\bREG\s?S\b|\b144A\b|\bETF\b|\bETP\b|\bETC\b|\bETN\b"
    r"|\d+\s?%\s|\bTREASURY\b|\bB SHARE|\bC SHARE|\bDEFERRED\b|\bREDEEMABLE\b)", re.I)
# fund / vehicle names the ICB sector tag misses
FUNDISH = re.compile(
    r"(INVESTMENT TRUST|INVESTMENT COMPANY|\bVCT\b|VENTURE CAPITAL TRUST|\bOEIC\b|\bICVC\b"
    r"|\bSICAV\b|\bFUND\b|\bFUNDS\b|UNIT TRUST|\bREIT\b|\bSPAC\b|ACQUISITION CORP"
    r"|CAPITAL PARTNERS PLC|CLOSED[- ]END|\bPCC\b|PROTECTED CELL)", re.I)
TRUST_INDUSTRY = re.compile(
    r"(Travel|Tour|Lodging|Airlines|Gambling|Casino|Betting|Insurance Broker|Ticket"
    r"|Payment|Real Estate Services|Financial Conglomerates|Resorts)", re.I)
TRUST_NAME = re.compile(
    r"(TRAVEL|HOLIDAY|\bTOURS?\b|CRUISE|TICKET|\bBET\b|BETTING|GAMING|CASINO|LOTTER"
    r"|BOOKMAK|INSURANCE BROK|ESTATE AGEN|PAYMENTS?\b|PAYTECH|MONEY TRANSFER)", re.I)
LEGAL_SFX = re.compile(r"\b(PLC|LIMITED|LTD|GROUP|HOLDINGS?|INC|CORP(ORATION)?|SE|NV|AB)\b\.?", re.I)

BS_KEYS = ("Total Assets", "Current Assets", "Total Liabilities Net Minority Interest",
           "Stockholders Equity", "Cash And Cash Equivalents")
MAX_FAILS = 4
BREAKER_N = 25
ADV_SESSIONS = 63           # ~3 months of sessions, matching the vendor window we replace
UK_TAX_RATE = 0.25          # UK main corporation-tax rate — the pension deficit's tax shield
# (f) path constants, kept identical to quality_drawdown.py so the two screens grade the same
MAX_OFF_LOW, FRESH_LOW_DAYS, HARD_OFF_LOW = 0.35, 90, 0.50
ORDER_CAP_OF_ADV = 0.20     # never size an order above this share of a day's prints (SFPI rule)


# ----------------------------------------------------------------- LSE primary API
def _lse_post(params: str, page: int, size: int = 500, timeout: int = 60) -> dict:
    body = {"path": "live-markets/market-data-dashboard/price-explorer",
            "parameters": params,
            "components": [{"componentId": PRICE_EXPLORER_COMPONENT,
                            "parameters": f"page%3D{page}%26size%3D{size}"}]}
    req = urllib.request.Request(LSE_API, data=json.dumps(body).encode(), headers=UA)
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    blocks = {x["name"]: x["value"] for x in r[0]["content"]}
    return blocks


def lse_sectors() -> list[dict]:
    """The exchange's own ICB sector list — pulled live so a reclassification cannot rot."""
    b = _lse_post("markets%3DMAINMARKET%26categories%3DEQUITY%26indexname%3D", 0, size=1)
    return b["priceexplorerfields"]["sectors"]


def _yahoo_sym(tidm: str) -> str:
    """TIDM -> Yahoo symbol. Taylor Wimpey's TIDM is literally 'TW.' and Yahoo calls it
    'TW.L'; BT's second line is 'BT.A' / 'BT-A.L'. Trailing dot dropped, interior dot to
    hyphen, then the venue suffix."""
    t = (tidm or "").strip().rstrip(".")
    return t.replace(".", "-") + ".L"


def refresh_universe(pause: float = 0.35) -> dict:
    """Sweep the LSE price explorer per (market x ICB sector).

    Sector-sliced rather than market-sliced so the ICB sector arrives attached to each line —
    it is what excludes the investment trusts and what the takeout-heat overlay aggregates on.
    ~90 calls; run monthly (admissions and delistings move at that pace).
    """
    secs = lse_sectors()
    print(f"LSE ICB sectors: {len(secs)}")
    rows, dropped_pages = {}, 0
    for mk in MARKETS:
        got = 0
        for s in secs:
            code, name = s["key"], s["value"].strip()
            page = 0
            while True:
                params = (f"markets%3D{mk}%26categories%3DEQUITY%26sectors%3D{code}"
                          f"%26indexname%3D")
                try:
                    b = _lse_post(params, page)
                except Exception as e:
                    print(f"  {mk}/{code} page={page} FAILED: {e}")
                    dropped_pages += 1
                    break
                v = b.get("priceexplorersearch") or {}
                content = v.get("content") or []
                for x in content:
                    tidm = x.get("tidm")
                    if not tidm or tidm in rows:
                        continue
                    rows[tidm] = {
                        "tidm": tidm, "sym": _yahoo_sym(tidm), "isin": x.get("isin"),
                        "issuercode": x.get("issuercode"), "name": x.get("issuername"),
                        "line": x.get("name"), "description": x.get("description"),
                        "market": mk, "sector_code": code, "sector": name,
                        "px_ccy": x.get("currency"),
                        "px": x.get("lastprice") or x.get("midPrice"),
                        "mid": x.get("midPrice"),
                        "mcap_local": x.get("marketcapitalization"),
                        "w52_min": x.get("fiftyTwoWeeksMin"),
                        "w52_max": x.get("fiftyTwoWeeksMax"),
                        "islse": x.get("islse"),
                    }
                    got += 1
                page += 1
                time.sleep(pause)
                if page >= (v.get("totalPages") or 1) or not content:
                    break
        print(f"  {mk} ({MARKETS[mk]}): {got} equity lines")
    os.makedirs(DATA, exist_ok=True)
    payload = {"meta": {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "London Stock Exchange price-explorer API (PRIMARY) — "
                  "POST api.londonstockexchange.com/api/v1/components/refresh, "
                  "path=live-markets/market-data-dashboard/price-explorer, swept per "
                  "(market x ICB sector)",
        "markets": list(MARKETS), "sectors": len(secs), "failed_pages": dropped_pages,
        "refresh": "python3 lse_shelf.py --refresh-universe"},
        "rows": list(rows.values())}
    json.dump(payload, open(UNIVERSE, "w"), ensure_ascii=False, indent=1)
    print(f"universe written: {len(rows)} lines -> {UNIVERSE}")
    return payload


def load_universe() -> dict:
    if not os.path.exists(UNIVERSE):
        raise SystemExit("no universe file — run: python3 lse_shelf.py --refresh-universe")
    return json.load(open(UNIVERSE))


def lse_instrument(tidm: str) -> dict:
    """Per-instrument record: country of INCORPORATION (the WHT key), live bid/offer, NMS.

    Tried with and without the trailing dot because the exchange's TIDM for a two-letter
    issuer carries one ('TW.') and the price explorer sometimes hands back the stripped form.
    """
    for t in (tidm, tidm.rstrip("."), tidm + "."):
        try:
            req = urllib.request.Request(LSE_INSTRUMENT + t,
                                         headers={k: v for k, v in UA.items()
                                                  if k != "Content-Type"})
            d = json.load(urllib.request.urlopen(req, timeout=25))
            if isinstance(d, dict) and d.get("tidm"):
                return d
        except Exception:
            continue
    return {}


# ----------------------------------------------------------------- (i) takeover overlay
def fetch_offer_periods(refresh: bool = True) -> dict:
    """The Takeover Panel Disclosure Table — every UK company currently in an offer period.

    Primary, published daily, and it carries the ISIN, so the join to the universe is EXACT
    rather than a fuzzy name match. Also carries the named offeror, which is what separates a
    trade-buyer bid from a private-equity bid.
    """
    if not refresh and os.path.exists(OFFERS):
        return json.load(open(OFFERS))
    try:
        req = urllib.request.Request(TAKEOVER_PANEL,
                                     headers={k: v for k, v in UA.items()
                                              if k not in ("Content-Type", "Origin")})
        html = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
    except Exception as e:
        print(f"  takeover-panel fetch failed: {e} (overlay disabled this run)")
        return {"meta": {"error": str(e)}, "by_isin": {}}
    out = {}
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        blob = " | ".join(cells)
        m = re.search(r"ISIN:\s*([A-Z]{2}[A-Z0-9]{9}\d)", blob)
        if not m:
            continue
        off = re.search(r"OFFEROR:\s*([^|]+)", blob)
        offeror = (off.group(1).strip() if off else
                   ("no named offeror" if re.search(r"No named offeror", blob, re.I) else None))
        out[m.group(1)] = {"offeror": offeror,
                           "pe_bidder": bool(offeror and re.search(
                               r"(LLP|\bLP\b|Partners|Capital|Equity|Investors|BidCo|Bidco"
                               r"|newly formed company)", offeror))}
    payload = {"meta": {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "source": TAKEOVER_PANEL, "n": len(out)}, "by_isin": out}
    os.makedirs(DATA, exist_ok=True)
    json.dump(payload, open(OFFERS, "w"), ensure_ascii=False, indent=1)
    print(f"takeover panel: {len(out)} live offer periods")
    return payload


# ----------------------------------------------------------------- FX
def live_fx() -> tuple[dict, str]:
    fx, basis = dict(FX_FALLBACK), "static fallback"
    try:
        import yfinance as yf
        got = 0
        for ccy, pair in FX_PAIRS.items():
            try:
                p = yf.Ticker(pair).fast_info["last_price"]
                if p and p > 0:
                    fx[ccy], got = float(p), got + 1
            except Exception:
                pass
        if got:
            basis = f"live yfinance FX ({got}/{len(FX_PAIRS)} pairs)"
    except ImportError:
        pass
    return fx, basis


def _to_fin_ccy(amount, quote_ccy, fin_ccy, fx):
    """(m) the ONE place a currency plane is crossed. GBX/GBp are pence — divided by 100 here
    and nowhere else."""
    if amount is None or not quote_ccy or not fin_ccy:
        return None
    if quote_ccy.upper() in ("GBP", "GBX") and quote_ccy != "GBP":
        amount, quote_ccy = amount / 100.0, "GBP"
    elif quote_ccy in ("GBp",):
        amount, quote_ccy = amount / 100.0, "GBP"
    if quote_ccy in ("ZAc", "ILA", "EUX", "USX"):
        amount = amount / 100.0
        quote_ccy = {"ZAc": "ZAR", "ILA": "ILS", "EUX": "EUR", "USX": "USD"}[quote_ccy]
    fq, ff = fx.get(quote_ccy), fx.get(fin_ccy)
    if not fq or not ff:
        return None
    return amount * fq / ff


# ----------------------------------------------------------------- price history
def fetch_history(syms: list[str], chunk: int = 60) -> dict:
    """Daily bars -> (e) MEDIAN turnover and (f) the path fields.

    Yahoo's averageDailyVolume3Month is a MEAN and a single block print on an AIM line lifts
    it enough to carry a name over an ADV floor it does not clear on a normal day. The median
    of the last ADV_SESSIONS daily turnovers is the honest number; the mean is kept beside it
    so the block-inflation ratio is visible.
    """
    import numpy as np, yfinance as yf
    out = {}
    for i in range(0, len(syms), chunk):
        part = syms[i:i + chunk]
        try:
            d = yf.download(part, period="1y", interval="1d", group_by="ticker",
                            auto_adjust=False, progress=False, threads=True)
        except Exception as e:
            print(f"  history chunk {i} failed: {e}")
            continue
        for s in part:
            try:
                df = d[s].dropna(subset=["Close"]) if len(part) > 1 else d.dropna(subset=["Close"])
            except Exception:
                continue
            if df is None or df.empty or len(df) < 20:
                continue
            tv = (df["Close"] * df["Volume"]).dropna()
            if tv.empty:
                continue
            win = tv[-ADV_SESSIONS:]
            last, lo = float(df["Close"].iloc[-1]), float(df["Close"].min())
            loi = df["Close"].idxmin()
            out[s] = {
                "adv_med_q": float(np.median(win)),          # quote-plane (pence x shares)
                "adv_mean_q": float(win.mean()),
                "sessions": int(len(df)),
                "last_px_q": last,
                "low_1y_q": lo,
                "high_1y_q": float(df["Close"].max()),
                "pct_off_52w_low": round(last / lo - 1, 4) if lo > 0 else None,
                "days_since_low": int((df.index[-1] - loi).days),
                "px_asof": str(df.index[-1].date()),
            }
        time.sleep(0.3)
    return out


# ----------------------------------------------------------------- fundamentals
def _row(df, *labels):
    if df is None or getattr(df, "empty", True):
        return None
    for lb in labels:
        if lb in df.index:
            try:
                v = df.loc[lb].iloc[0]
            except Exception:
                continue
            if v is not None and v == v:
                return float(v)
    return None


def _colstamp(df):
    try:
        return str(df.columns[0].date())
    except Exception:
        return None


def _hist(df, *labels, n=5):
    if df is None or getattr(df, "empty", True):
        return []
    for lb in labels:
        if lb in df.index:
            return [float(v) if (v is not None and v == v) else None
                    for v in list(df.loc[lb].values)[:n]]
    return []


def _map_facts(bs, inc, cf, info, inc_annual=None, cf_annual=None) -> dict:
    """yfinance frames -> the us-gaap key convention score.py consumes."""
    g = {}
    g["Assets"] = _row(bs, "Total Assets")
    g["AssetsCurrent"] = _row(bs, "Current Assets")
    g["LiabilitiesCurrent"] = _row(bs, "Current Liabilities")
    g["Liabilities"] = _row(bs, "Total Liabilities Net Minority Interest")
    g["StockholdersEquity"] = _row(bs, "Stockholders Equity", "Common Stock Equity")
    g["MinorityInterest"] = _row(bs, "Minority Interest") or 0.0
    g["CashAndCashEquivalentsAtCarryingValue"] = _row(
        bs, "Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments")
    # ---- (o) CASH QUALITY — the CAPD sign inversion --------------------------------
    # `Other Short Term Investments` is NOT reliably a cash equivalent on this universe. On
    # Capital Ltd it is a USD 99.8M portfolio of LISTED JUNIOR MINER EQUITIES carried at fair
    # value through P&L. Netting it against debt turned the company's own stated NET DEBT of
    # USD 31.8M into a printed "+11% of the cap in net cash" — the sign of the single most
    # load-bearing metric on the shelf, inverted. The raw tag is kept for the as-is view and
    # a STRICT cash figure (true cash only) is carried beside it.
    g["ShortTermInvestments"] = _row(bs, "Other Short Term Investments")
    g["_cash_strict"] = _row(bs, "Cash And Cash Equivalents")
    g["LongTermInvestments"] = _row(bs, "Investments And Advances", "Long Term Equity Investment")
    # the vendor publishes its OWN net-debt line. It is free, independent of our arithmetic,
    # and disagreeing with it in SIGN means one of the two is wrong — always worth knowing.
    g["_net_debt_tag"] = _row(bs, "Net Debt")
    g["DebtLongtermAndShorttermCombinedAmount"] = _row(bs, "Total Debt")
    g["LongTermDebtNoncurrent"] = _row(bs, "Long Term Debt And Capital Lease Obligation",
                                       "Long Term Debt")
    g["DebtCurrent"] = _row(bs, "Current Debt And Capital Lease Obligation", "Current Debt")
    g["_SharesIssued"] = _row(bs, "Ordinary Shares Number", "Share Issued")
    g["_lease_debt"] = _row(bs, "Capital Lease Obligations") or 0.0

    # ---- (a) PENSION / IAS-19 -------------------------------------------------------
    # Debt-like, pervasive on UK industrials of this vintage, and invisible to a net-cash
    # view built off Yahoo. SFPI.PA (court 2026-08-03) is the precedent: EUR50.6M unfunded,
    # a Key Audit Matter for both auditors, which turned "39% of the cap in net cash" into
    # 12-18% and EV/EBIT 4.5x into 6.0-6.5x.
    _pens = _row(bs, "Pension And Other Post Retirement Benefit Plans",
                     "Non Current Pension And Other Postretirement Benefit Plans",
                     "Pensionand Other Post Retirement Benefit Plans Non Current")
    _pens_cur = _row(bs, "Pensionand Other Post Retirement Benefit Plans Current",
                         "Pension And Other Post Retirement Benefit Plans Current") or 0.0
    _prov_lt = _row(bs, "Long Term Provisions") or 0.0
    obligation = (_pens or 0.0) + _pens_cur
    if not obligation and _prov_lt:
        obligation = _prov_lt
    g["_pension_obligation"] = obligation or 0.0
    g["_pension_source"] = ("pension_tag" if (_pens or _pens_cur) else
                            "long_term_provisions_proxy" if _prov_lt else "NONE_FOUND")
    g["_pension_is_proxy"] = bool(not (_pens or _pens_cur) and _prov_lt)
    # a UK scheme in SURPLUS books an ASSET that inflates equity and flatters P/B while being
    # unavailable to shareholders absent a buyout / surplus refund. Never netted into cash.
    g["_pension_asset"] = _row(bs, "Pension And Other Post Retirement Benefit Plans Asset",
                               "Prepaid Pension Costs") or 0.0
    # TAX-EFFECT BEFORE ADDING TO EV. The Euronext leg adds the obligation GROSS, which
    # over-captures: a deficit is deductible as it is funded, so the claim on the equity is
    # the after-tax amount. SFPI's court did this explicitly — EUR 51M gross became EUR 38.3M
    # net of the 25% French rate, and the honest EV/EBIT was 6.06x rather than the 4.58x the
    # gross-cash screen printed. The UK main rate is also 25%.
    g["_pension_gross"] = g["_pension_obligation"]
    g["_pension_net"] = round(g["_pension_obligation"] * (1 - UK_TAX_RATE), 2)
    if g["_pension_net"]:
        base = g.get("DebtLongtermAndShorttermCombinedAmount") or 0.0
        g["_debt_ex_pension"] = base
        g["DebtLongtermAndShorttermCombinedAmount"] = base + g["_pension_net"]

    g["Revenues"] = _row(inc, "Total Revenue", "Operating Revenue")
    g["OperatingIncomeLoss"] = _row(inc, "Operating Income")
    g["_ebit_reported"] = _row(inc, "Total Operating Income As Reported")
    g["_unusual"] = _row(inc, "Total Unusual Items", "Special Income Charges")
    g["_ebit_derived"] = False
    if g["OperatingIncomeLoss"] is None:
        pre, ie, ii = (_row(inc, "Pretax Income"), _row(inc, "Interest Expense"),
                       _row(inc, "Interest Income"))
        if pre is not None and (ie is not None or ii is not None):
            g["OperatingIncomeLoss"] = pre + (ie or 0.0) - (ii or 0.0)
            g["_ebit_derived"] = True
        else:
            g["OperatingIncomeLoss"] = _row(inc, "EBIT")
            g["_ebit_derived"] = g["OperatingIncomeLoss"] is not None
    # Yahoo's Operating Income is NORMALIZED (unusual items already excluded), so feeding a
    # non-zero OneTimeGain would double-count the add-back. This is exactly WHY the durability
    # guard (c) exists: normalization strips unusual items but NOT one-time REVENUE.
    g["OneTimeGain_ttm"] = 0.0

    # ---- (b) FCF = CFO - TOTAL CAPEX ------------------------------------------------
    # Verified on this universe 2026-08-04: yfinance's `Capital Expenditure` on UK filers
    # ALREADY equals PPE + intangibles (TW.L 6.7 = 4.2 + 2.5; SGE.L 59 = 41 + 18; ITV.L
    # 54 = 26 + 28). Adding the intangibles line again would DOUBLE-COUNT. The split is
    # carried through so capitalised development cost is visible.
    g["NetCashProvidedByUsedInOperatingActivities"] = _row(cf, "Operating Cash Flow")
    capx = _row(cf, "Capital Expenditure", "Capital Expenditure Reported")
    ppe = _row(cf, "Purchase Of PPE")
    intang = _row(cf, "Purchase Of Intangibles")
    total = abs(capx) if capx is not None else None
    if total is None and (ppe is not None or intang is not None):
        total = abs(ppe or 0.0) + abs(intang or 0.0)
    elif total is not None and (ppe is not None or intang is not None):
        # floor at the sum of the components — if the umbrella tag were ever PPE-only the
        # components win. Bias is conservative (bigger capex -> lower FCF).
        total = max(total, abs(ppe or 0.0) + abs(intang or 0.0))
    g["PaymentsToAcquirePropertyPlantAndEquipment"] = total
    g["_capex_ppe"], g["_capex_intangibles"] = (abs(ppe) if ppe is not None else None,
                                                abs(intang) if intang is not None else None)

    # ---- (c)/(d) history for the durability + trend guards ---------------------------
    g["_rev_hist"] = _hist(inc_annual, "Total Revenue", "Operating Revenue")
    g["_ebit_hist"] = _hist(inc_annual, "Operating Income")
    g["_cfo_hist"] = _hist(cf_annual, "Operating Cash Flow")
    g["_consol_verified"] = ("Minority Interest" in getattr(bs, "index", [])
                             or "Total Equity Gross Minority Interest" in getattr(bs, "index", []))
    i = info or {}
    g["_float"] = i.get("floatShares")
    g["_shares_yahoo"] = i.get("sharesOutstanding")
    g["_mcap_yahoo"] = i.get("marketCap")
    g["_n_analysts"] = i.get("numberOfAnalystOpinions")
    g["_industry"] = i.get("industry")
    g["_sector_info"] = i.get("sector")
    g["_fin_ccy_info"] = i.get("financialCurrency")
    g["_bs_date"], g["_flow_date"] = _colstamp(bs), _colstamp(inc)
    return g


def _pull_one(sym):
    import yfinance as yf
    t = yf.Ticker(sym)
    bs = None
    try:
        qbs, abs_ = t.quarterly_balance_sheet, t.balance_sheet
        ok_q = qbs is not None and not qbs.empty and all(k in qbs.index for k in BS_KEYS)
        bs = qbs if (ok_q and (abs_ is None or abs_.empty or qbs.columns[0] > abs_.columns[0])) else abs_
    except Exception:
        pass
    inc, cf, info, ttm_i = None, None, None, False
    try:
        inc_annual = t.income_stmt
    except Exception:
        inc_annual = None
    try:
        cf_annual = t.cashflow
    except Exception:
        cf_annual = None
    try:
        inc = t.ttm_income_stmt
        ttm_i = inc is not None and not inc.empty
    except Exception:
        pass
    if not ttm_i:
        inc = inc_annual
    try:
        cf = t.ttm_cashflow
        if cf is None or cf.empty:
            cf = cf_annual
    except Exception:
        cf = cf_annual
    try:
        info = t.info
    except Exception:
        info = {}
    f = _map_facts(bs, inc, cf, info, inc_annual=inc_annual, cf_annual=cf_annual)
    f["_ttm"] = bool(ttm_i)
    f["_fetched"] = time.time()
    return f


def yahoo_throttled() -> bool:
    """Probe the crumb endpoint — the thing that actually rate-limits. yfinance answers a
    throttle with EMPTY frames and no exception, and reading that as "no balance sheet" is
    how a throttle silently deletes a whole venue from a shelf."""
    try:
        import yfinance.data as D
        return not bool(D.YfData()._get_cookie_and_crumb()[1])
    except Exception:
        return False


def _safe(sym, tries=2, pace=0.25):
    import random
    last = None
    for k in range(tries):
        try:
            f = _pull_one(sym)
            if f.get("Assets"):
                time.sleep(pace)
                return f
            last = f
        except Exception as e:
            last = {"_error": f"{type(e).__name__}: {e}"}
        time.sleep(pace + (2 ** k) + random.random())
    out = last or {}
    out["_fetched"] = time.time()
    return out


def fetch_fundamentals(syms, refresh=False, workers=2, pace=0.25, batch_pause=5.0) -> dict:
    """(n) threaded pull, cached hard, with the silent-throttle circuit breaker."""
    cache = json.load(open(FUND_CACHE)) if os.path.exists(FUND_CACHE) else {}
    todo = [s for s in syms if refresh or s not in cache
            or (not cache[s].get("Assets") and cache[s].get("_fails", 0) < MAX_FAILS)]
    if not todo:
        return cache
    retries = sum(1 for s in todo if s in cache)
    print(f"pulling fundamentals for {len(todo)} names "
          f"({len(syms)-len(todo)} cached, {retries} retrying), {workers} workers")
    if yahoo_throttled():
        print("  !! Yahoo crumb endpoint is rate-limited RIGHT NOW — skipping the pull rather "
              "than burning the names as failures. Re-run in ~15-30 min; cache resumes.")
        return cache
    done, streak, tripped = 0, 0, False
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for sym, f in zip(chunk, ex.map(lambda s: _safe(s, pace=pace), chunk)):
                if not f.get("Assets"):
                    streak += 1
                    old = cache.get(sym)
                    # NEVER let a throttled empty overwrite a good cached row — a refresh
                    # would otherwise destroy exactly the data it was run to improve
                    if old and old.get("Assets"):
                        old["_fails"] = old.get("_fails", 0) + 1
                        old["_stale_refresh"] = True
                    else:
                        f["_fails"] = (old or {}).get("_fails", 0) + 1
                        cache[sym] = f
                else:
                    streak = 0
                    cache[sym] = f
                done += 1
        ok = sum(1 for s in todo[:done] if cache.get(s, {}).get("Assets"))
        print(f"  ...{done}/{len(todo)}  ({ok} with a balance sheet)")
        json.dump(cache, open(FUND_CACHE, "w"))
        if streak >= BREAKER_N:
            tripped = True
            break
        if done < len(todo):
            time.sleep(batch_pause)
    json.dump(cache, open(FUND_CACHE, "w"))
    if tripped:
        print(f"  !! CIRCUIT BREAKER: {streak} consecutive empty pulls = Yahoo is throttling. "
              f"{len(todo)-done} names unpulled. Shelf is PARTIAL — see meta.pull_complete.")
    return cache


def _norm_name(n):
    s = re.sub(r"[^A-Z0-9 ]", " ", (n or "").upper())
    return re.sub(r"\s+", " ", LEGAL_SFX.sub(" ", s)).strip()


# ----------------------------------------------------------------- the screen
def run(top=30, min_mcap_usd=5e7, max_mcap_usd=2e9, min_adv_usd=75e3, min_float=0.15,
        refresh_fund=False, workers=2, limit=None, skip_instruments=False):
    uni = load_universe()
    rows = uni["rows"]
    fx, fx_basis = live_fx()
    print(f"universe: {len(rows)} lines (generated {uni['meta']['generated_utc']}) | FX: {fx_basis}")
    offers = fetch_offer_periods()
    by_isin = offers.get("by_isin") or {}

    drop = Counter()
    # ---- (l) non-ordinary share lines -------------------------------------------------
    cand = []
    for r in rows:
        desc = f"{r.get('description') or ''} {r.get('line') or ''}"
        if NON_ORD.search(desc):
            drop["non_ordinary_line"] += 1
            continue
        if FUNDISH.search(r.get("name") or ""):
            drop["fund_vehicle_name"] += 1
            continue
        cand.append(r)

    # ---- (g) one issuer, many lines: dedup on the exchange's own issuer code ----------
    lines_by_issuer = defaultdict(list)
    for r in cand:
        lines_by_issuer[r.get("issuercode") or _norm_name(r.get("name"))].append(r)
    deduped = []
    for key, lines in lines_by_issuer.items():
        keep = max(lines, key=lambda r: (r.get("mcap_local") or 0))
        keep["_n_lines"] = len(lines)
        keep["_other_lines"] = [x["tidm"] for x in lines if x["tidm"] != keep["tidm"]] or None
        deduped.append(keep)
    drop["dup_issuer_line"] = len(cand) - len(deduped)
    cand = deduped

    # ---- (j) financials / vehicles out of the Graham score ---------------------------
    fin_rows = [r for r in cand if r["sector_code"] in FIN_SECTORS]
    cand = [r for r in cand if r["sector_code"] not in FIN_SECTORS]
    drop["financials_vehicles"] = len(fin_rows)
    trusts = sum(1 for r in fin_rows if r["sector_code"] in ("302040", "302050"))

    # ---- cheap pre-filters before spending a fundamentals call ------------------------
    pre = []
    for r in cand:
        px, qccy = r.get("px"), r.get("px_ccy")
        mcap_local = r.get("mcap_local")
        if not px or not qccy:
            drop["no_price"] += 1
            continue
        # the exchange reports market capitalisation in the MAJOR unit (GBP), not pence
        mcap_usd = (mcap_local or 0) * fx.get("GBP" if qccy.upper() in ("GBX", "GBP") else qccy,
                                              fx["GBP"])
        if not mcap_usd or mcap_usd <= 0:
            drop["no_mcap"] += 1
            continue
        r["_mcap_usd_pre"] = mcap_usd
        if not (min_mcap_usd <= mcap_usd <= max_mcap_usd):
            drop["mcap_band"] += 1
            continue
        pre.append(r)
    print("pre-filter drops: " + ", ".join(f"{k}={v}" for k, v in drop.most_common()))
    print(f"in the mcap band: {len(pre)}")

    # ---- (e)+(f) median ADV and the path fields, from daily bars ----------------------
    print(f"pulling 1y daily bars for {len(pre)} names (median ADV + path)...")
    hist = fetch_history([r["sym"] for r in pre])
    print(f"  bars for {len(hist)}/{len(pre)}")
    liq = []
    for r in pre:
        h = hist.get(r["sym"])
        if not h:
            drop["no_history"] += 1
            continue
        gbp = fx["GBP"] if (r["px_ccy"] or "").upper() in ("GBX", "GBP") else fx.get(r["px_ccy"], 0)
        scale = 0.01 if (r["px_ccy"] or "").upper() in ("GBX",) else 1.0
        r["_adv_usd"] = h["adv_med_q"] * scale * gbp
        r["_adv_mean_usd"] = h["adv_mean_q"] * scale * gbp
        r["_hist"] = h
        if r["_adv_usd"] < min_adv_usd:
            drop["adv_floor_median"] += 1
            continue
        liq.append(r)
    print(f"candidates for fundamentals: {len(liq)}")
    if limit:
        liq = sorted(liq, key=lambda r: -r["_adv_usd"])[:limit]

    funds = fetch_fundamentals([r["sym"] for r in liq], refresh=refresh_fund, workers=workers)

    now = time.time()
    recs, post = [], Counter()
    for r in liq:
        f = funds.get(r["sym"]) or {}
        if f.get("_error") or not f.get("Assets"):
            post["no_fundamentals"] += 1
            continue
        if f.get("OperatingIncomeLoss") is None and \
           f.get("NetCashProvidedByUsedInOperatingActivities") is None:
            post["no_income_anchor"] += 1
            continue
        ind = f.get("_industry") or ""
        if re.search(r"(Bank|Insurance|Asset Management|Capital Markets|REIT|Credit Services"
                     r"|Mortgage|Closed-End Fund|Shell Compan)", ind, re.I):
            post["financial_industry"] += 1
            continue
        invsum = sum((f.get(k) or 0) for k in ("CashAndCashEquivalentsAtCarryingValue",
                                               "ShortTermInvestments", "LongTermInvestments"))
        if f["Assets"] and invsum / f["Assets"] > 0.85 and (f.get("Revenues") or 0) < 0.05 * f["Assets"]:
            post["balance_shape_vehicle"] += 1
            continue

        # ---- (m) the currency plane, crossed exactly once ----------------------------
        fccy = f.get("_fin_ccy_info") or "GBP"
        qccy = r.get("px_ccy") or "GBX"
        if fccy not in fx:
            post["unknown_currency"] += 1
            continue
        px_f = _to_fin_ccy(r["px"], qccy, fccy, fx)
        shares_filing = f.get("_SharesIssued")
        shares = shares_filing or f.get("_shares_yahoo")
        if px_f and shares:
            mcap, basis = px_f * shares, ("px*shares(filing)" if shares_filing
                                          else "px*shares(yahoo)")
        else:
            mcap = _to_fin_ccy((r.get("mcap_local") or 0) * 100.0, qccy, fccy, fx)
            basis = "lse mcap"
        if not mcap or mcap <= 0:
            post["no_mcap_post"] += 1
            continue
        mcap_usd = mcap * fx[fccy]

        urow = {"sym": r["sym"], "mktcap": mcap, "px": r["px"], "sec": r["sector"],
                "ind": (r.get("name") or "")[:44], "country": "GB"}
        m = S.compute_metrics(urow, f)
        m["foreign"], m["adr"] = True, False
        m["tidm"], m["isin"], m["name"] = r["tidm"], r.get("isin"), r.get("name")
        m["market"], m["sector_code"] = r["market"], r["sector_code"]
        m["mcap_usd"], m["mcap_basis"] = mcap_usd, basis
        m["ccy"], m["px_ccy"] = fccy, qccy
        m["ccy_mismatch"] = fccy != "GBP"
        m["industry"] = ind

        # ---- (k) trust / client-cash -------------------------------------------------
        m["trust_cash_suspect"] = bool(TRUST_INDUSTRY.search(ind)
                                       or TRUST_NAME.search(r.get("name") or "")
                                       or r["sector_code"] in TRUST_SECTORS)
        # the UNCORRECTED figures are captured FIRST, before either the cash-quality or the
        # trust-cash guard rewrites them, so the JSON always shows what the naive computation
        # said next to what governs
        m["am_asis"], m["ncash_r_asis"] = m["am"], m["ncash_r"]

        # ---- (o) CASH QUALITY + SIGN RECONCILIATION ---------------------------------
        # Applied BEFORE the trust-cash guard so both corrections compose. Two independent
        # checks, either of which demotes the name to the STRICT (true-cash-only) view:
        #   1. marketable securities are a material part of what the screen called "cash";
        #   2. our net cash disagrees in SIGN with the vendor's own Net Debt line.
        sti = f.get("ShortTermInvestments") or 0.0
        cash_strict = f.get("_cash_strict")
        if cash_strict is None:
            cash_strict = max((m["cash"] or 0.0) - sti, 0.0)
        m["cash_strict"] = cash_strict
        m["st_investments"] = sti or None
        m["st_inv_share_of_cash"] = (round(sti / m["cash"], 3)
                                     if (sti and m["cash"] and m["cash"] > 0) else None)
        m["netcash_strict"] = cash_strict - m["debt"]
        m["ncash_r_strict"] = round(m["netcash_strict"] / mcap, 3) if mcap else None
        m["securities_as_cash"] = bool(m["st_inv_share_of_cash"]
                                       and m["st_inv_share_of_cash"] > 0.25)
        nd = f.get("_net_debt_tag")
        m["net_debt_vendor"] = nd
        # the vendor's Net Debt is POSITIVE when the company owes money; ours is positive when
        # it holds money. They should have opposite signs. Agreement of sign = a contradiction.
        m["netcash_sign_conflict"] = bool(nd is not None and m["netcash"] is not None
                                          and nd > 0 and m["netcash"] > 0)
        m["cash_quality_note"] = None
        if m["netcash_sign_conflict"] or m["securities_as_cash"]:
            m["cash_quality_note"] = (
                f"screen cash {m['cash']/1e6:.1f}M includes {sti/1e6:.1f}M of short-term "
                f"INVESTMENTS (marketable securities, not cash equivalents); true cash "
                f"{cash_strict/1e6:.1f}M. "
                + (f"The filer's own Net Debt line reads {nd/1e6:.1f}M — i.e. NET DEBT, "
                   f"against a screen that computed net CASH. The screen figure is REFUTED "
                   f"by the same balance sheet it came from; the strict view governs."
                   if m["netcash_sign_conflict"] else
                   "Score falls back to the strict view."))
            # the strict figure GOVERNS: conservative, and it is the one the filer would
            # recognise. `ncash_r_asis` preserves what the naive computation said.
            m["ncash_r"] = m["ncash_r_strict"]
            m["netcash"] = m["netcash_strict"]
            m["ev"] = mcap + m["debt"] + m["mi"] - cash_strict
            m["am"] = (m["ev"] / m["ebit"]) if (m["ebit"] and m["ebit"] > 0 and m["ev"] > 0) else None
            m["subcash"] = m["ev"] < 0
        # a large securities book also distorts the P&L: Capital Ltd booked a USD 66.0M
        # realised+unrealised fair-value gain on its junior-miner stakes in FY2025, which is a
        # mark-to-market and not services earnings — invisible to the unusual-items path
        # because it is not tagged unusual.
        m["securities_book_material"] = bool(sti and mcap and sti > 0.20 * mcap)

        m["am_trustsafe"] = None
        if m["trust_cash_suspect"]:
            ev_ts = mcap + m["debt"] + m["mi"]
            m["ev_trustsafe"] = ev_ts
            m["am_trustsafe"] = (ev_ts / m["ebit"]) if (m["ebit"] and m["ebit"] > 0 and ev_ts > 0) else None
            m["am"], m["subcash"] = m["am_trustsafe"], False
            m["ncash_r"] = min(0.0, m["ncash_r"]) if m["ncash_r"] is not None else None

        # ---- (a) pension columns -----------------------------------------------------
        po = f.get("_pension_gross") or 0.0
        m["pension_gross"] = po or None
        m["pension_net_of_tax"] = f.get("_pension_net") or None
        m["pension_tax_rate"] = UK_TAX_RATE
        m["pension_source"] = f.get("_pension_source")
        m["pension_is_proxy"] = bool(f.get("_pension_is_proxy"))
        m["debt_ex_pension"] = f.get("_debt_ex_pension")
        m["pension_deficit_r"] = round(po / mcap, 3) if (po and mcap) else None
        m["pension_material"] = bool(m["pension_deficit_r"] and m["pension_deficit_r"] > 0.25)
        m["pension_surplus"] = f.get("_pension_asset") or None
        m["pension_surplus_in_equity"] = bool(
            m["pension_surplus"] and m["eq"] and m["pension_surplus"] > 0.10 * m["eq"])
        m["pension_unverified"] = bool(f.get("_pension_source") == "NONE_FOUND"
                                       and r["sector_code"] in DB_PENSION_SECTORS)
        # WHAT THE PROVISION ACTUALLY IS depends on the sector, and on this universe the
        # single largest proxy hit is NOT a pension at all: for UK housebuilders and
        # contractors, Long Term Provisions is dominated by BUILDING SAFETY ACT cladding
        # remediation. Vistry's GBP 269.8M — 30% of its market cap — is that, not a scheme
        # deficit. The debt-like TREATMENT is still right (it is a statutory, non-negotiable
        # cash obligation running on a 30-year lookback, arguably harder than a pension
        # deficit, which can at least be renegotiated with trustees), but calling it a pension
        # would send the reader to the wrong note.
        m["provision_kind_hint"] = (
            "Building Safety Act cladding remediation is the usual content for a UK "
            "housebuilder/contractor — read the provisions note, not the IAS-19 note"
            if (m["pension_is_proxy"] and r["sector_code"] in ("501010", "402020")) else
            "IAS-19 retirement + long-service" if not m["pension_is_proxy"] and po else None)
        m["pension_note"] = (
            "PROVISIONS PROXY, not a verified pension — the tag also carries warranty, "
            "restructuring, dilapidations, litigation and (on UK builders) Building Safety Act "
            "remediation, so it OVER-captures as a pension figure while still being debt-like. "
            "Read the provisions note AND the auditors' Key Audit Matter, which is where "
            "SFPI's real number was. UK schemes also bury long-service awards here."
            if m["pension_is_proxy"] else
            "explicit pension tag" if f.get("_pension_source") == "pension_tag" else
            "NO pension or provisions tag on a sector where DB schemes are the norm — treat net "
            "cash as UNVERIFIED, not clean" if m["pension_unverified"] else
            "no pension tag found (sector where DB schemes are not the norm)")

        # ---- (b) capex composition + IFRS-16 flattery --------------------------------
        m["capex_ppe"], m["capex_intangibles"] = f.get("_capex_ppe"), f.get("_capex_intangibles")
        capex_t = f.get("PaymentsToAcquirePropertyPlantAndEquipment")
        m["capex_total"] = capex_t
        m["capex_intang_heavy"] = bool(m["capex_intangibles"] and capex_t
                                       and m["capex_intangibles"] > 0.40 * capex_t)
        # capitalised development as a share of SALES — the Tecnotree tell (EUR 9.7M, 13.4%
        # of sales, was the entire wedge between a EUR 14.8M screen FCF and the company's own
        # reported EUR 4.6M). Above ~8% of revenue, read the intangibles note before trusting
        # the FCF yield at all.
        m["capdev_r"] = (round(m["capex_intangibles"] / m["rev"], 3)
                         if (m["capex_intangibles"] and m.get("rev")) else None)
        m["capdev_heavy"] = bool(m["capdev_r"] and m["capdev_r"] > 0.08)
        m["lease_debt"] = f.get("_lease_debt")
        m["lease_heavy"] = bool(m["lease_debt"] and m["debt"]
                                and m["lease_debt"] > 0.5 * m["debt"]
                                and m["lease_debt"] > 0.25 * mcap)

        # ---- (c) durability, WITH the cash-generation condition -----------------------
        rh, eh = (f.get("_rev_hist") or []), (f.get("_ebit_hist") or [])
        ch = (f.get("_cfo_hist") or [])
        rev_prior = rh[1] if len(rh) > 1 else None
        ebit_prior = eh[1] if len(eh) > 1 else None
        cfo_prior = ch[1] if len(ch) > 1 else None
        cur_rev, cur_ebit, cur_fcf = m.get("rev"), m.get("ebit"), m.get("fcf")
        why, accrual_gap = [], False
        if cur_rev and cur_rev > 0 and rev_prior is not None:
            if rev_prior <= 0.02 * abs(cur_rev):
                why.append(f"revenue from ~0 to {cur_rev/1e6:.0f}M in one year")
            elif cur_rev >= 3 * rev_prior > 0:
                why.append(f"revenue {cur_rev/max(rev_prior,1):.1f}x prior year")
        if cur_ebit and cur_ebit > 0 and ebit_prior is not None and ebit_prior < 0:
            why.append(f"EBIT flipped {ebit_prior/1e6:.0f}M -> {cur_ebit/1e6:.0f}M")
        if cur_ebit and cur_ebit > 0 and cur_fcf is not None and cur_fcf < 0:
            why.append(f"EBIT +{cur_ebit/1e6:.0f}M but FCF {cur_fcf/1e6:.0f}M")
            accrual_gap = True
        # THE CASH-GENERATION CONDITION: a turnaround that converted to cash NOW and was
        # already cash-generative in the prior year is not a one-year accounting artifact.
        # It never rescues the accrual-gap shape — that shape fails the condition by
        # construction, which is the point.
        cash_generative = bool(cur_fcf is not None and cur_fcf > 0
                               and cfo_prior is not None and cfo_prior > 0)
        m["cash_generative_2y"] = cash_generative
        m["durability_why"] = "; ".join(why) or None
        m["durability_suspect"] = bool(why) and not (cash_generative and not accrual_gap)
        m["durability_watch"] = bool(why) and cash_generative and not accrual_gap

        # ---- (d) EBIT trend, both anchors ---------------------------------------------
        eh_v = [v for v in eh if v is not None]
        m["ebit_hist"] = eh_v or None
        m["ebit_oldest"] = eh_v[-1] if len(eh_v) >= 2 else None
        m["ebit_peak"] = max(eh_v) if eh_v else None
        m["ebit_trend"] = (round(cur_ebit / eh_v[-1], 2)
                           if (cur_ebit and len(eh_v) >= 2 and eh_v[-1] and eh_v[-1] > 0) else None)
        m["ebit_vs_peak"] = (round(cur_ebit / m["ebit_peak"], 2)
                             if (cur_ebit and m["ebit_peak"] and m["ebit_peak"] > 0) else None)
        m["trough_anchored"] = bool(len(eh_v) >= 3 and eh_v[-1] == min(eh_v))
        m["melting"] = bool(m["ebit_vs_peak"] is not None and m["ebit_vs_peak"] < 0.5)
        # the base year was the trough, so the "uptrend" is a recovery artifact and the
        # decline from peak is the number that matters
        m["trend_flattered"] = bool(m["trough_anchored"] and m["ebit_trend"]
                                    and m["ebit_trend"] > 1.2
                                    and m["ebit_vs_peak"] is not None and m["ebit_vs_peak"] < 0.8)

        # ---- (e) liquidity + (f) path -------------------------------------------------
        h = r["_hist"]
        m["adv_usd"], m["adv_mean_usd"] = round(r["_adv_usd"]), round(r["_adv_mean_usd"])
        m["adv_basis"] = f"median of {ADV_SESSIONS} sessions"
        m["adv_block_inflated"] = bool(r["_adv_usd"] > 0
                                       and r["_adv_mean_usd"] / r["_adv_usd"] > 2.0)
        m["thin"] = r["_adv_usd"] < 3e5
        # a scanner ask is not an acquirable position — carry the size the median day
        # actually supports (the Seiryo lesson: an order at 82% of a day's volume is not a
        # fill, it is a market impact event)
        m["max_order_usd"] = round(ORDER_CAP_OF_ADV * r["_adv_usd"])
        m["pct_off_52w_low"] = h["pct_off_52w_low"]
        m["days_since_low"] = h["days_since_low"]
        m["days_since_52w_low"] = h["days_since_low"]      # quality_drawdown's field name
        m["fresh_low"] = bool(h["days_since_low"] is not None and h["days_since_low"] < 30)
        # same two exhaustion modes quality_drawdown grades on, so the screens agree: a big
        # bounce off a FRESH low, or a very big bounce off any low — either way you are late
        m["entry_exhausted"] = bool(
            h["pct_off_52w_low"] is not None
            and ((h["pct_off_52w_low"] > MAX_OFF_LOW and h["days_since_low"] < FRESH_LOW_DAYS)
                 or h["pct_off_52w_low"] > HARD_OFF_LOW))
        m["px_asof"] = h["px_asof"]
        m["px_stale"] = bool(h["sessions"] < 200)

        flt = f.get("_float")
        m["float_shares"] = flt
        m["float_pct"] = round(flt / shares, 3) if (flt and shares) else None
        m["float_unknown"] = m["float_pct"] is None
        m["float_usd"] = round(m["float_pct"] * mcap_usd) if m["float_pct"] else None
        if m["float_pct"] is not None and m["float_pct"] < min_float:
            post["float_floor"] += 1
            continue

        # ---- (g) share-count / dual-class verification --------------------------------
        # The HOOD/TUYA mechanism: a vendor's `sharesOutstanding` is often ONE CLASS while its
        # `marketCap` is the whole company, so cap/shares does not reconcile to the price and
        # every per-share ratio is wrong by the missing class (HOOD: 790.6M Class A quoted,
        # 109M Class B omitted, a 12% cap error). The test is arithmetic and needs no filing:
        # divide each source's market cap by its own share count and see whether it equals the
        # traded price. Three independent counts are compared here — the filing's ordinary
        # share number, the vendor's, and the one implied by the EXCHANGE's own market cap.
        implied = None
        if r.get("mcap_local") and r.get("px"):
            px_gbp = r["px"] / 100.0 if (qccy or "").upper() == "GBX" else r["px"]
            implied = r["mcap_local"] / px_gbp if px_gbp else None
        # the vendor cap is quoted in the QUOTE currency's major unit (GBP), so it is divided
        # by the price in the same plane — never by the reporting-currency price
        px_major = (r["px"] / 100.0) if (qccy or "").upper() == "GBX" else r["px"]
        yh_implied = (f["_mcap_yahoo"] / px_major
                      if (f.get("_mcap_yahoo") and px_major) else None)
        counts = {"filing": shares_filing, "yahoo": f.get("_shares_yahoo"),
                  "lse_implied": implied, "yahoo_mcap_implied": yh_implied}
        vals = [v for v in counts.values() if v and v > 0]
        m["share_counts"] = {k: (round(v) if v else None) for k, v in counts.items()}
        m["share_count_divergence"] = (round(max(vals) / min(vals) - 1, 3)
                                       if len(vals) >= 2 else None)
        m["share_count_unverified"] = bool(m["share_count_divergence"] is None
                                           or m["share_count_divergence"] > 0.05)
        m["n_lines"] = r.get("_n_lines", 1)
        m["other_lines"] = r.get("_other_lines")
        m["multi_line_issuer"] = m["n_lines"] > 1

        # ---- (h) PFIC — the shared gate, plus the FMV overlay -------------------------
        # The Euronext leg SKIPS PFIC on the theory that EU/EEA operating companies are not a
        # PFIC population. That reasoning does not survive the crossing to London, for two
        # separate reasons, so the gate is ON here:
        #   * the UK IS a PFIC population — its closed-end investment companies are statutory
        #     PFICs almost to a name. They are excluded from this shelf by ICB sector, but
        #     the boundary between "investment company" and "cash-rich holdco" is porous and
        #     the sector tag is the only thing keeping them apart;
        #   * §1297's asset test on a PUBLIC issuer runs on FAIR MARKET VALUE, so the
        #     denominator is roughly market cap + liabilities, not book assets. That is the
        #     mechanism (PDD court, 2026-08-04): passive assets sit fixed in the numerator
        #     while the denominator collapses with the multiple, so THE DE-RATE CAUSES THE TAX
        #     STATUS. Drawdown is not a coincidence with PFIC risk, it is a cause of it —
        #     which means a cheapness screen is exactly the instrument that concentrates it.
        # `pfic_screen.pfic_risk` is imported rather than reimplemented; the FMV overlay is
        # applied on top the same way screen_europe/japan/korea do it. Nothing is EXCLUDED —
        # a genuine net-cash bargain is the name most likely to trip it, and the answer is a
        # QEF/mark-to-market election, not avoidance.
        pf = P.pfic_risk(m, f)
        m["pfic"], m["pfic_why"] = pf["pfic"], pf["reason"]
        m["pfic_severity"] = pf.get("severity")
        assets = f.get("Assets") or 0
        liab = f.get("Liabilities") or 0
        fmv_den = mcap + liab
        share = (invsum / fmv_den) if fmv_den > 0 else None
        m["pfic_fmv_share"] = round(share, 3) if share is not None else None
        if share is not None and share >= 0.50 and not m["pfic"]:
            m["pfic"] = True
            m["pfic_why"] = (f"FMV-basis passive {share*100:.0f}% >= 50% "
                             f"(book test passed: {pf['reason']})")
        # the watch band from the PDD court: above 0.45 the risk-factor language is the thing
        # that moves ("we do not believe we were a PFIC" -> "it is possible that we were")
        m["pfic_watch"] = bool(share is not None and 0.45 <= share < 0.50 and not m["pfic"])
        m["passive_asset_r"] = round(invsum / assets, 3) if assets else None
        ebit_margin = (m["ebit"] / m["rev"]) if (m.get("ebit") is not None and m.get("rev")) else None
        m["ebit_margin"] = round(ebit_margin, 3) if ebit_margin is not None else None

        # ---- (i) live offer period ----------------------------------------------------
        off = by_isin.get(r.get("isin") or "")
        m["in_offer_period"] = bool(off)
        m["offeror"] = (off or {}).get("offeror")
        m["pe_bidder"] = bool((off or {}).get("pe_bidder"))

        # ---- vintage / consolidation --------------------------------------------------
        m["consol_unverified"] = not f.get("_consol_verified")
        m["ttm"] = bool(f.get("_ttm"))
        m["bs_date"], m["flow_date"] = f.get("_bs_date"), f.get("_flow_date")
        try:
            m["flow_months"] = round((now - time.mktime(time.strptime(
                m["flow_date"], "%Y-%m-%d"))) / (30.44 * 86400))
        except (TypeError, ValueError):
            m["flow_months"] = None
        m["fy_stale"] = bool(m["flow_months"] and m["flow_months"] > 15)
        m["ebit_derived"] = bool(f.get("_ebit_derived"))
        m["ebit_reported"] = f.get("_ebit_reported")
        m["unusual_r"] = (round(f["_unusual"] / m["ebit"], 3)
                          if (f.get("_unusual") and m.get("ebit")) else None)
        m["n_analysts"] = f.get("_n_analysts")
        m["orphan"] = (m["n_analysts"] or 0) <= 1
        recs.append(m)

    print("post-filter drops: " + ", ".join(f"{k}={v}" for k, v in post.most_common()))
    print(f"scored population: {len(recs)}")

    # ---- coverage honesty by market ---------------------------------------------------
    cand_by_mk = Counter(r["market"] for r in liq)
    got_by_mk = Counter(r["market"] for r in liq if (funds.get(r["sym"]) or {}).get("Assets"))
    coverage = {k: {"candidates": cand_by_mk[k], "with_fundamentals": got_by_mk[k],
                    "pct": round(100 * got_by_mk[k] / cand_by_mk[k]) if cand_by_mk[k] else None}
                for k in sorted(cand_by_mk)}
    missing = sum(cand_by_mk.values()) - sum(got_by_mk.values())
    print("fundamentals coverage: " +
          ", ".join(f"{k} {v['with_fundamentals']}/{v['candidates']}" for k, v in coverage.items()))
    worst = min((c["pct"] for c in coverage.values() if c["pct"] is not None), default=100)
    if missing and (missing > 0.02 * sum(cand_by_mk.values()) or worst < 90):
        print(f"  !! PARTIAL PULL — {missing} candidates without fundamentals, worst market "
              f"{worst}%. Re-run to resume (cache preserved).")

    # ---- (m) plane check ---------------------------------------------------------------
    plane_fail = []
    for mk in sorted({r["market"] for r in recs}):
        pbs = sorted(x["pb"] for x in recs if x["market"] == mk and x.get("pb"))
        if len(pbs) < 5:
            continue
        med = pbs[len(pbs) // 2]
        ok = 0.05 < med < 50
        print(f"  plane check {mk}: median P/B {med:.2f} on n={len(pbs)} {'OK' if ok else '*** FAIL ***'}")
        if not ok:
            plane_fail.append(mk)
    if plane_fail:
        raise SystemExit(f"CURRENCY-PLANE FAILURE on {plane_fail} — refusing to emit a shelf")

    scored = S.composite(recs)
    shelf = S.clean_shortlist(scored, exclude_adr=False)

    # ---- (1)(2) per-name incorporation, WHT, stamp duty, live spread -------------------
    # Only the shelf gets the per-instrument call — country of incorporation is what decides
    # whether the "0% UK withholding" edge is real for this name, and it is NOT implied by
    # the .L suffix.
    if not skip_instruments:
        print(f"resolving incorporation + touch for {len(shelf)} shelf names (LSE instrument API)...")
        for i, rr in enumerate(shelf):
            d = lse_instrument(rr["tidm"])
            ctry = (d.get("country") or "").upper() or None
            rr["country_incorp"] = ctry
            wht_s, wht_r = WHT.get(ctry or "", ("unknown", None))
            rr["wht"], rr["wht_rate"] = wht_s, wht_r
            rr["wht_edge_bps"] = (round((TREATY_BASELINE - wht_r) * 1e4)
                                  if wht_r is not None else None)
            # SDRT: 0.5% on purchases of UK-incorporated shares; AIM quoted shares exempt
            # since Apr-2014; non-UK incorporation is outside the charge.
            uk_inc = ctry == "GB"
            rr["stamp_pct"] = 0.0 if (rr["market"] == "AIM" or not uk_inc) else 0.5
            rr["stamp_why"] = ("AIM-quoted — SDRT exempt since Apr-2014" if rr["market"] == "AIM"
                               else "non-UK incorporation — outside the UK stamp charge"
                               if not uk_inc else "UK-incorporated Main-Market line — 0.5% SDRT on buys")
            bid, off_ = d.get("bid"), d.get("offer")
            rr["bid"], rr["offer"] = bid, off_
            rr["spread_bps"] = (round(1e4 * (off_ - bid) / ((off_ + bid) / 2))
                                if (bid and off_ and off_ > bid) else None)
            rr["nms_shares"] = d.get("marketsize")
            rr["lse_segment"] = d.get("segment")
            rr["wide_touch"] = bool(rr["spread_bps"] and rr["spread_bps"] > 200)
            if (i + 1) % 25 == 0:
                print(f"  ...{i+1}/{len(shelf)}")
            time.sleep(0.2)
    else:
        for rr in shelf:
            rr["country_incorp"] = None
            rr["wht"], rr["wht_rate"], rr["wht_edge_bps"] = "unresolved", None, None
            rr["stamp_pct"] = 0.0 if rr["market"] == "AIM" else 0.5
            rr["stamp_why"] = "incorporation not resolved (--skip-instruments)"

    # ---- (i) sector takeout heat -------------------------------------------------------
    isin2sec = {r.get("isin"): r.get("sector_code") for r in rows if r.get("isin")}
    heat, pe_heat = Counter(), Counter()
    for isin, o in by_isin.items():
        sc = isin2sec.get(isin)
        if sc:
            heat[sc] += 1
            if o.get("pe_bidder"):
                pe_heat[sc] += 1
    for rr in shelf:
        rr["sector_takeout_heat"] = heat.get(rr["sector_code"], 0)
        rr["pe_bid_sector"] = pe_heat.get(rr["sector_code"], 0) > 0

    # ---- IBKR conids, merged out of band ------------------------------------------------
    conids = json.load(open(CONIDS)) if os.path.exists(CONIDS) else {}
    for rr in shelf:
        c = conids.get(rr["sym"]) or conids.get(rr["tidm"]) or {}
        rr["conid"] = c.get("conid")
        rr["ibkr_symbol"] = c.get("ibkr_symbol")
        rr["ibkr_exchange"] = c.get("exchange") or "LSE"
        rr["ibkr_verified_utc"] = c.get("verified_utc")

    n_dur = sum(1 for r in shelf if r.get("durability_suspect"))
    n_off = sum(1 for r in shelf if r.get("in_offer_period"))
    printable = [r for r in shelf
                 if not r.get("durability_suspect") and not r.get("in_offer_period")]

    keep = ("tidm", "sym", "isin", "name", "ind", "industry", "sec", "sector_code", "market",
            "country_incorp", "ccy", "px_ccy", "ccy_mismatch", "mktcap", "mcap_usd",
            "mcap_basis", "px", "px_asof", "score", "nmetrics",
            "am", "am_asis", "am_trustsafe", "trust_cash_suspect", "fcfy", "pb", "ncash_r",
            "ncash_r_asis", "ncav_r", "ev", "ebit", "ebit_reported", "ebit_derived",
            "unusual_r", "fcf", "rev", "cash", "debt", "mi", "eq", "netcash", "subcash",
            "cash_strict", "st_investments", "st_inv_share_of_cash", "netcash_strict",
            "ncash_r_strict", "securities_as_cash", "net_debt_vendor",
            "netcash_sign_conflict", "cash_quality_note", "securities_book_material",
            "capex_total", "capex_ppe", "capex_intangibles", "capex_intang_heavy",
            "capdev_r", "capdev_heavy", "lease_debt", "lease_heavy",
            "pension_gross", "pension_net_of_tax", "pension_tax_rate", "pension_source",
            "pension_is_proxy", "debt_ex_pension",
            "pension_deficit_r", "pension_material", "pension_surplus",
            "pension_surplus_in_equity", "pension_unverified", "pension_note",
            "provision_kind_hint",
            "durability_suspect", "durability_watch", "durability_why", "cash_generative_2y",
            "ebit_trend", "ebit_vs_peak", "ebit_peak", "ebit_oldest", "ebit_hist",
            "trough_anchored", "trend_flattered", "melting",
            "adv_usd", "adv_mean_usd", "adv_basis", "adv_block_inflated", "thin",
            "max_order_usd", "spread_bps", "wide_touch", "bid", "offer", "nms_shares",
            "lse_segment",
            "pct_off_52w_low", "days_since_low", "days_since_52w_low", "fresh_low",
            "entry_exhausted",
            "float_pct", "float_usd", "float_unknown",
            "share_counts", "share_count_divergence", "share_count_unverified",
            "n_lines", "other_lines", "multi_line_issuer",
            "passive_asset_r", "ebit_margin", "pfic", "pfic_why", "pfic_severity",
            "pfic_fmv_share", "pfic_watch",
            "in_offer_period", "offeror", "pe_bidder", "sector_takeout_heat", "pe_bid_sector",
            "wht", "wht_rate", "wht_edge_bps", "stamp_pct", "stamp_why",
            "holdco", "neg_equity", "wc_fcf", "mlp_artifact", "consol_unverified",
            "n_analysts", "orphan",
            "ibkr_exchange", "ibkr_symbol", "conid", "ibkr_verified_utc",
            "ttm", "bs_date", "flow_date", "flow_months", "fy_stale", "px_stale")

    os.makedirs(DATA, exist_ok=True)
    meta = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "module": "verticals/generators/lse_shelf.py",
        "thesis": "UK small-value — LSE Main + AIM; 0% dividend withholding is a genuine "
                  "structural edge, 0.5% SDRT is a genuine friction, and 30% of the Main "
                  "Market is closed-end vehicles that belong in a different lane",
        "universe_source": uni["meta"].get("source"),
        "fundamentals_source": "Yahoo (SECONDARY) — re-derive from the annual report before "
                               "any court",
        "universe_generated_utc": uni["meta"]["generated_utc"],
        "universe_lines": len(rows),
        "closed_end_and_vehicles_excluded": trusts,
        "fx_basis": fx_basis, "fx": {k: round(v, 5) for k, v in fx.items()},
        "filters": {"min_mcap_usd": min_mcap_usd, "max_mcap_usd": max_mcap_usd,
                    "min_adv_usd": min_adv_usd, "min_float": min_float,
                    "adv_basis": f"MEDIAN of {ADV_SESSIONS} sessions (not the vendor mean)"},
        "prefilter_drops": dict(drop), "postfilter_drops": dict(post),
        "scored": len(recs), "shelf": len(shelf),
        "pull_complete": missing == 0,
        "fundamentals_coverage_by_market": coverage,
        "candidates_without_fundamentals": missing,
        "scored_by_market": dict(Counter(r["market"] for r in recs)),
        "shelf_by_market": dict(Counter(r["market"] for r in shelf)),
        "orphans_on_shelf": sum(1 for r in shelf if r["orphan"]),
        "durability_suspect_demoted": n_dur,
        "durability_watch_rescued": sum(1 for r in shelf if r.get("durability_watch")),
        "in_offer_period_demoted": n_off,
        "melting_on_shelf": sum(1 for r in shelf if r.get("melting")),
        "trend_flattered_on_shelf": sum(1 for r in shelf if r.get("trend_flattered")),
        "pension_material_on_shelf": sum(1 for r in shelf if r.get("pension_material")),
        "pension_unverified_on_shelf": sum(1 for r in shelf if r.get("pension_unverified")),
        "netcash_sign_conflict_on_shelf": sum(1 for r in shelf if r.get("netcash_sign_conflict")),
        "securities_as_cash_on_shelf": sum(1 for r in shelf if r.get("securities_as_cash")),
        "pfic_flagged_on_shelf": sum(1 for r in shelf if r.get("pfic")),
        "pfic_watch_on_shelf": sum(1 for r in shelf if r.get("pfic_watch")),
        "entry_exhausted_on_shelf": sum(1 for r in shelf if r.get("entry_exhausted")),
        "share_count_unverified_on_shelf": sum(1 for r in shelf if r.get("share_count_unverified")),
        "aim_on_shelf": sum(1 for r in shelf if r["market"] == "AIM"),
        "zero_wht_on_shelf": sum(1 for r in shelf if r.get("wht_rate") == 0.0),
        "live_offer_periods_uk": len(by_isin),
        "conids_merged": sum(1 for r in shelf if r.get("conid")),
        "rerun": "python3 lse_shelf.py --top 30  (--refresh-universe monthly; "
                 "--refresh-fund to re-pull financials)",
        "known_limitations": "see module docstring README",
    }
    json.dump({"meta": meta, "rows": [{k: r.get(k) for k in keep} for r in shelf]},
              open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"\nwrote {OUT}  ({len(shelf)} scored rows)")

    def fmt(r):
        am = f"{r['am']:.1f}" if r["am"] else ("subC" if r["subcash"] else " -")
        fy = f"{r['fcfy']*100:.0f}%" if r["fcfy"] is not None else " -"
        pb = f"{r['pb']:.2f}" if r["pb"] else " -"
        nc = f"{r['ncash_r']:.2f}" if r["ncash_r"] is not None else " -"
        na = str(r["n_analysts"]) if r["n_analysts"] is not None else "-"
        off = f"{r['pct_off_52w_low']*100:.0f}%" if r.get("pct_off_52w_low") is not None else " -"
        fl = " ".join(t for t, on in [
            ("orphan", r["orphan"]), ("thin", r["thin"]), ("blocky", r.get("adv_block_inflated")),
            (f"touch{r['spread_bps']}bp" if r.get("spread_bps") else "", r.get("wide_touch")),
            ("NETDEBT-CONFLICT!", r.get("netcash_sign_conflict")),
            ("secs-as-cash", r.get("securities_as_cash") and not r.get("netcash_sign_conflict")),
            ("secs-book", r.get("securities_book_material")),
            ("PENSION!", r.get("pension_material") and not r.get("pension_is_proxy")),
            ("PROV!", r.get("pension_material") and r.get("pension_is_proxy")),
            ("pens?", r.get("pension_unverified")),
            ("prov-proxy", r.get("pension_is_proxy")),
            ("pens-surplus", r.get("pension_surplus_in_equity")),
            (f"melt{r['ebit_vs_peak']:.1f}x" if r.get("ebit_vs_peak") is not None else "melt",
             r.get("melting")),
            ("trough-anchor", r.get("trend_flattered")),
            ("dur-watch", r.get("durability_watch")), ("lease", r.get("lease_heavy")),
            ("cap-intang", r.get("capex_intang_heavy")),
            ("PFIC?", r.get("pfic")), ("pfic-watch", r.get("pfic_watch")),
            ("capdev", r.get("capdev_heavy")), ("late-entry", r.get("entry_exhausted")),
            ("shares?", r.get("share_count_unverified")),
            ("dual-line", r.get("multi_line_issuer")), ("cust-cash?", r["trust_cash_suspect"]),
            ("fx!", r["ccy_mismatch"]), ("ebit~", r["ebit_derived"]), ("WC-FCF", r["wc_fcf"]),
            ("holdco", r["holdco"]), ("neg-eq", r["neg_equity"]), ("no-NCI", r["consol_unverified"]),
            ("stale-FY", r["fy_stale"]), ("PE-sector", r.get("pe_bid_sector")),
            ("conid", bool(r.get("conid")))] if on and t)
        stamp = f"{r.get('stamp_pct', 0):.1f}" if r.get("stamp_pct") is not None else " -"
        return (f"  {r['tidm']:7s}{r['market'][:4]:5s}{r['mcap_usd']/1e6:7.0f}"
                f"{r['adv_usd']/1e3:7.0f}{am:>7s}{fy:>6s}{pb:>6s}{nc:>7s}{off:>7s}"
                f"{na:>3s} {str(r.get('wht') or '?'):>5s}{stamp:>5s} "
                f"{(r.get('name') or '')[:24]:24s} {fl}")

    print(f"\nLSE MAIN + AIM SMALL-VALUE SHELF  n={len(shelf)}  "
          f"orphans={meta['orphans_on_shelf']}  AIM={meta['aim_on_shelf']}  "
          f"durability-demoted={n_dur}  in-offer-demoted={n_off}")
    print(f"  {'tidm':7s}{'mkt':5s}{'mc$M':>7s}{'ADV$k':>7s}{'EV/EBT':>7s}{'FCFy':>6s}"
          f"{'P/B':>6s}{'ncash/m':>7s}{'off-lo':>7s}{'an':>3s} {'WHT':>5s}{'stmp':>5s} "
          f"{'name':24s} flags")
    for r in printable[:top]:
        print(fmt(r))
    print("\n  (mc/ADV in USD, ADV = MEDIAN daily turnover over 63 sessions; every RATIO computed "
          "in the reporting ccy — 'fx!' = reports in something other than GBP; 'stmp' = stamp "
          "duty % on a PURCHASE; EV carries IFRS-16 lease debt AND the pension obligation)")
    return shelf


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("====")[0])
    ap.add_argument("--refresh-universe", action="store_true",
                    help="re-sweep the LSE price explorer and rewrite the universe file")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--min-mcap-usd", type=float, default=5e7)
    ap.add_argument("--max-mcap-usd", type=float, default=2e9)
    ap.add_argument("--min-adv-usd", type=float, default=75e3)
    ap.add_argument("--min-float", type=float, default=0.15)
    ap.add_argument("--refresh-fund", action="store_true")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--limit", type=int, default=None,
                    help="cap the fundamentals pull to the N most liquid candidates (dev)")
    ap.add_argument("--skip-instruments", action="store_true",
                    help="skip the per-name LSE instrument call (no incorporation/touch data)")
    a = ap.parse_args()
    if a.refresh_universe:
        refresh_universe()
    run(a.top, a.min_mcap_usd, a.max_mcap_usd, a.min_adv_usd, a.min_float,
        a.refresh_fund, a.workers, a.limit, a.skip_instruments)
