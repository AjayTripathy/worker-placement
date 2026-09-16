"""registry — the single manifest of every watch the Desk owns. ONE place that answers "what do we
monitor, how often, and how do we read its output." The Desk runner consolidates all scheduling here,
replacing the scattered OS crontab entries.

Each WatchSpec:
  name        unique id
  cmd         argv list (run from repo root)
  cadence     'weekday' | 'daily' | 'weekly' | 'hourly' | int minutes — how often it's DUE
  log         relative path the runner tees stdout to (append)
  asset_class equities/munis/beauty/cross
  extractor   key into extractors.EXTRACTORS (how to turn stdout into Signals)
  enabled     bool
  note        human description
"""
from __future__ import annotations
import os, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = Path(__file__).resolve().parent / "data" / "last_run.json"

WATCHES = [
    {"name": "ai_capex_watch", "cmd": ["python3", "-m", "desk.ai_capex_watch"],
     "cadence": "weekday", "log": "desk/data/ai_capex_watch.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "tripwires 1+2 of desk/models/ai_capex_break.py: realized hyperscaler capex acceleration (clock-starter; accumulates quarters, consensus excluded by design) + earnings-day guide-check reminders w/ Nash-flip event study on logged guide-downs (Gate B). Built 2026-07-30 from the groundbrkr second-derivative thesis."},
    {"name": "consistency_check", "cmd": ["python3", "-m", "desk.consistency_check"],
     "cadence": "hourly", "log": "desk/data/consistency_check.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "guard against research-to-UI drift: diffs edge_classifications vs entry_plan vs research_ledger vs scanner freshness; FLAGs any name whose verdict/sizing disagree (the failure the user caught 6x). Built 2026-07-01."},
    {"name": "positions_sync", "cmd": ["python3", "-m", "desk.positions_sync"],
     "cadence": "hourly", "log": "desk/data/positions_sync.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "auto-refresh positions_cache.json from the LOCAL TWS socket (ib_insync :7496 readonly) — fixes the hand-maintained-cache drift; no-clobber + STALE flag if TWS is down (>6h). The claude.ai MCP feed is session-bound so it can't be cron'd; this local-socket path can."},
    {"name": "pipeline_metrics", "cmd": ["python3", "-m", "desk.pipeline_metrics"],
     "cadence": "hourly", "log": "desk/data/pipeline_metrics.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "PRD success-metric snapshots (one row/day, merge-by-date): P1 pack-wiring %, batch advance rates, defect count; P3 stale packs, adjudication p90, unclassified held cost; tripwire backlog. History-keeping store desk/data/pipeline_metrics.json; /api/pipeline_metrics; consumed by pipeline_monitor's digest. Built 2026-08-06 (pipeline hardening)."},
    {"name": "orphan_screen", "cmd": ["python3", "-m", "verticals.deep_value.orphan_screen"],
     "cadence": "weekly", "log": "verticals/deep_value/data/orphan_screen.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "UNIVERSAL orphan/carry sweep (2026-08-06 user directive: screen every public equity): full US-listed tape incl ADRs, ALL sectors. Coverage-first (uncovered proxy + shortlist analyst-count), carry_spread = NI_ttm/mcap - (rf + Damodaran country ERP, Jan-2026 vintage, desk/data/damodaran_crp.json). Data stack per gateway-first doctrine: gw_quotes delayed snapshots (local, no IP limits) + Nasdaq-screener mcap + SEC XBRL TTM; yahoo shortlist-coverage ONLY. FAIR-CARRY rows -> conveyor (R1.9). fundamentals_missing (foreign ADR no-frames) COUNTED never hidden; fail-LOUD partial-tape guard."},
    {"name": "class_dislocation", "cmd": ["python3", "-m", "desk.class_dislocation"],
     "cadence": "daily",  # BACKSTOP ONLY — primary run = dedicated crontab pin 05:30 PT premarket (user-directed 2026-08-06) "log": "desk/data/class_dislocation.out",
     "asset_class": "equities", "extractor": "detector_scan", "enabled": True,
     "note": "pipeline-2 CLASS-dislocation detector (2026-08-06): fires when a cohort (sector x band auto + knowledge_graph/cohorts.json narrative cohorts) shows median 52w-drawdown <=-25% with LOW dispersion (iqr<=18pp) and residual vs SPY <=-15pp (beta-bleed guard; refuses to scan without SPY). One gw_quotes.bulk_stats sweep (tick 165), no history pulls. Events -> class_dislocation_events.json (S1 store) with narrative_anchor=UNEXPLAINED until triage attaches a DATED anchor (R2.2 no-hindsight rule) + grade_due +90d cohort=class_dislocation (MAUDE kill rule). Complements broken_print_radar (single-name tape) and dislocation_sweep (known names)."},
    {"name": "court_runner", "cmd": ["python3", "-m", "desk.court_runner"],
     "cadence": "hourly", "log": "desk/data/court_runner.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "the auto-court conveyor (2026-08-06 user directive: screen-surfaced names are automatically courted). Drains desk/data/court_queue.json <=4 dispatches/run via headless `claude -p` (grader transport, Keychain-auth, fail-LOUD): TRAP_VERIFY (opus) -> survivors -> COURT_RED -> COURT_BLUE (both fable — evenly-matched benches, COURT_DOCTRINE). Output-side validators (verdict enums, citation floor) refuse to persist junk. ADJUDICATE stays a session job (generator-never-grades-itself; pitch doc + ledger/edge/pack wiring) — the queue + consistency_check surface awaiting items. Screens enqueue idempotently on every run; ledger names refused at the door. Spend is queue-gated, not cadence-gated: empty queue = zero dispatches."},
    {"name": "pipeline_monitor", "cmd": ["python3", "-m", "desk.pipeline_monitor"],
     "cadence": "hourly", "log": "desk/data/pipeline_monitor.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "email monitoring for the hardened pipelines (RX.4 fail-LOUD): NEW CRITICAL invariant breaches -> immediate mail via desk.mailer, rate-limited one-per-breach-key-per-24h (grader-alarm lesson); Monday digest of metric trends + backlog burn-down. Metrics-file staleness >36h is itself a breach (a dead metrics cron must never read as health). Built 2026-08-06."},
    {"name": "smallcap_value", "cmd": ["python3", "verticals/deep_value/smallcap_value_watch.py"],
     "cadence": "weekday", "log": "verticals/deep_value/data/smallcap_value_cron.out",
     "asset_class": "equities", "extractor": "smallcap_value", "enabled": True,
     "note": "cheap-and-quality small-cap value basket — entry-band zones + delta alerts"},
    {"name": "dislocation_sweep", "cmd": ["python3", "verticals/generators/dislocation_sweep.py"],
     "cadence": "weekday", "log": "verticals/generators/data/dislocation_sweep_cron.out",
     "asset_class": "equities", "extractor": "detector_scan", "enabled": True,
     "note": "year-round value-dislocation watch over the KNOWN universe (ledger non-dead verdicts + deep_value/financials shortlists + held book, ~320 names): fires on IDIOSYNCRATIC drops (excess vs SPY -8%/5d or -15%/21d; held names 2pp earlier; moonshot-pullback + TRAP verdicts excluded; wash-sale names tagged DO-NOT-BUY-31D). PROPOSES ONLY — every fire routes cause-check -> discovery_state -> v1.4 court before any staging (beta-bleed ≠ dislocation). New-entry/deepening fires only (~10-session quiet). Built 2026-07-28; enabled per the silently-dead-watch lesson."},
    {"name": "us_broad_dislocation_sweep",
     "cmd": ["python3", "verticals/generators/us_broad_dislocation_sweep.py"],
     "cadence": "weekday", "log": "verticals/generators/data/us_broad_dislocation_cron.out",
     "asset_class": "equities", "extractor": "detector_scan", "enabled": True,
     # RATE BUDGET / STAGGER. Listed immediately after dislocation_sweep because desk.runner walks
     # WATCHES in order within one heartbeat: the known-universe sweep (~490 names, 3mo) runs, then
     # this (~800 names, 1y, ~14 batched calls ≈ 20-40s), and intl (8,133 names) is WEEKLY so the
     # three only collide once a week. broken_print_radar is hourly but window-gated and uses the
     # server-side screener rather than history pulls, so it competes for a different quota. The
     # cap-ladder universe is cached 7 days (UNI_CACHE_DAYS) precisely so the 8 screener calls that
     # build it do NOT recur daily on top of the radar's.
     "note": "the BROAD-US leg of the dislocation watch (2026-08-13), built off the VERIFIED SPGI miss: SPGI ground 457.38 (7/16) -> 405.24 (8/6), -11.4% in 17 sessions with SPY flat and no session worse than -3.5%, and NOTHING saw it — broken_print_radar only fires on single-session breaks, dislocation_sweep only sweeps the ~490 researched names (SPGI was never researched), the value screens never look at a premium-multiple compounder, and intl_dislocation_sweep was giving 8,133 FOREIGN names the multi-session treatment unresearched US large-caps lacked. TWO gaps, not one: closing the universe gap alone would STILL have missed SPGI, because its 21d POINT-TO-POINT excess vs SPY was only -9.0pp and its deepest 5d excess -7.9pp — both inside the -15/-8 gates — since the t-21 anchor (7/8) was itself a local low and the 7/16 peak was invisible to the measure. Point-to-point return is anchor-lucky; peak-anchored, the same tape reads -11.0pp. UNIVERSE = S&P 500 constituents (weekly Wikipedia cache spinoff_orphans maintains) UNION broken_print_radar's own cap-ladder US universe (~800 names, its builder reused, cached 7d here for the rate budget) MINUS everything dislocation_sweep already covers (incl. dead-verdict names) — so every fire is by construction UNRESEARCHED = an intake proposal, never a double-fire. FIVE LEGS on the shared date-aligned machinery in intl_dislocation_sweep (this module owns no benchmark arithmetic): 5d excess vs SPY <=-8pp (HIGH -12); 21d <=-15pp (HIGH -20); grind21 = excess DRAWDOWN from the 21-session high <=-11pp (HIGH -18) — the SPGI shape, guarded so a 2-day break or a window containing a single session worse than -8% is left to broken_print_radar; 63d point-to-point <=-20pp (HIGH -28) with a raw <=-10% floor; bleed52 = (drawdown-from-52w-high minus SPY's own) <=-25pp AND still WIDENING >=5pp over 21 sessions, labelled SLOW_BLEED. Bands CALIBRATED on the S&P 500 across five as-of dates spanning +18.5%/-5.2% SPY 63d regimes to the house 2-15% fire band: the coordinator's first-cut 63d MED of -14pp fired 30% of the index on 2026-06-30 purely because SPY was +18.5%/63d, which is the beta-bleed error in long-window form — hence the raw floor. Every leg keeps the raw-move-must-be-negative guard. SECTOR CONTEXT: the SPDR sector ETF is resolved lazily FOR FIRES ONLY (one cached .info call per new name) and printed as context — a name -12pp vs SPY but -1pp vs XLF is the sector wearing a single name's clothes. DEGRADED-LOUD: priced/requested named split into no-data/thin-history/not-swept, plus a LEG COVERAGE line naming how many priced names had too little tape for the 63d and bleed52 legs (a partial screen reported as a full one is the failure this doctrine exists for); a universe under 400 names or a missing SPY series ABORTS rather than printing a quiet tape. PROPOSES ONLY — cause-check -> discovery_state -> court (v1.4) before any staging."},
    {"name": "intl_dislocation_sweep", "cmd": ["python3", "verticals/generators/intl_dislocation_sweep.py"],
     "cadence": "weekly", "log": "verticals/generators/data/intl_dislocation_sweep_cron.out",
     "asset_class": "equities", "extractor": "detector_scan", "enabled": True,
     "note": "the INTERNATIONAL leg of the dislocation watch (2026-08-11): closes the blind spot between dislocation_sweep (US ledger names only) and broken_print_radar (US tape only) — the desk's stored foreign shelves (LSE price-explorer universe ~1,599 + LSE value shelf, Euronext/Nordic shelf ~502 + Euronext universe, EDINET Japan crawl ~1.2k, KRX value universe ~2.8k, ESEF Europe) were never tape-watched, so a 25% two-week break on a shelf name was invisible. TAPE SCREEN ONLY — no fundamental re-screen (the shelves already carry that work). Excess is measured vs the LOCAL index, never SPY (a Tokyo small-cap vs SPY measures the yen and the Nikkei): ^N225/.T, ^FTSE/.L, ^KS11+^KQ11/.KS+.KQ, ^STOXX for European suffixes with Nordic local overrides (^OMX/^OMXH25/^OMXC25/^OSEAX); no benchmark series = RAW moves, labelled UNAVAILABLE(raw) in the fire, never passed off as excess. Gates mirror the US sweep: excess -8%/5d or -15%/21d (HIGH at -12%/-20%), moonshot-pullback excluded, DEAD ledger verdicts dropped, new-entry/deepening fires only (~10-session quiet, intl_dislocation_state.json). DEGRADED-LOUD per the facilities_resolver doctrine: Yahoo drops international lines in waves, so every run prints 'X of Y priced; Z DEGRADED' and NAMES the casualties split into no-data / thin-history / not-swept-time-budget; unpriced names first go through a fallback ladder (alternate suffix forms incl. the KOSPI/KOSDAQ mislabel, then a local IBKR-gateway liveness probe) and a name the gateway quotes but Yahoo has no history for is reported as an INFRA failure, never as 'no dislocation'. Fires tag UNRESEARCHED (not in the research ledger) -> ENQUEUE-CANDIDATE intake language vs researched -> re-underwrite; PROPOSES ONLY — cause-check -> discovery_state -> court (v1.4) before any staging. Weekly because the registry cadence vocabulary has no cron-style day-of-week (Mon+Thu would need a crontab pin); wall-clock budget 480s keeps it inside the runner's 600s kill."},
    {"name": "cohort_dislocation", "cmd": ["python3", "verticals/generators/cohort_dislocation.py"],
     "cadence": "daily", "log": "verticals/generators/data/cohort_dislocation_cron.out",
     "asset_class": "equities", "extractor": "detector_scan", "enabled": True,
     # RATE BUDGET / STAGGER. Listed AFTER the three sweeps on purpose: within one runner heartbeat
     # they price the tape first, and this layer is built to REUSE rather than refetch. Price series
     # live in a day-keyed cache (data/cohort_px_cache.json), so a same-day re-run costs zero network
     # and only cohort members not already cached are pulled (a few batched yf.download calls, not a
     # universe sweep). The one genuinely NEW cost is the industry mapper's yfinance .info calls,
     # hard-capped at --map-budget per run (default 120, ~0.35s apart) so the map fills over days
     # instead of in one rate-limiting burst; the Nasdaq screener call it also makes is the same free
     # bulk endpoint class_dislocation already uses. DAILY not weekday because a cohort de-rate is a
     # multi-week episode — missing a session costs nothing and the episode dedup cannot double-fire.
     "note": "the COHORT-AGGREGATE leg of the dislocation watch (2026-08-13), built off the same verified SPGI miss as us_broad_dislocation_sweep but closing the ORTHOGONAL half of it. Every other dislocation layer screens ONE NAME AT A TIME; in early August 2026 the market re-rated the financial-data vendors as a CLASS on the AI-disintermediation narrative and nothing aggregates, so SPGI/MCO/MSCI each grinding 6-12pp below SPY read as three unrelated shrugs instead of one theme. Where us_broad fixes the MEASURE on a single name (peak-anchored grind), this fixes the UNIT OF OBSERVATION: the cohort. SIGNAL = the cohort's MEDIAN idiosyncratic excess vs SPY plus BREADTH — median because one blown-up member is not a class de-rate, breadth because a median can be carried by a minority. FIRE: median 21d excess <=-6pp AND >=60% of members negative (n>=4), or the 63d GRIND leg at <=-10pp; HIGH at -12pp/-18pp. Gates measured, not asserted: on the recorded Apr-Aug 2026 vendor tape (tests/golden) the raw gate clears 18 of 70 sessions and the EPISODE DEDUP turns that into 5 events (~1.4/cohort/month) — a fresh fire needs the cohort to ENTER a de-rate or deepen >=3pp, and a cohort must sit BELOW the gate 10 days to re-arm (an instant re-arm fragmented one May selloff into five 'new' fires). SINGLE-NAME SKEW GUARD: every cohort reports its EX-WORST-MEMBER median, and when dropping the deepest member takes it back above the bar the fire still stands but is capped at MED and labelled CONCENTRATED — on the anchor date the vendor median is -6.7pp while its ex-worst median is only -2.1pp (SPGI/MCO/MSCI sold off, FDS/MORN rallied), which is the honest shape of that finding. REGIME GUARD: excess-vs-SPY already nets out a market drop, so >25% of cohorts clearing at once is a broad ROTATION and every fire that day says so rather than handing the court twenty independent-looking theme questions. MEMBERSHIP two ways — curated narrative cohorts in knowledge_graph/cohorts.json (shared with class_dislocation) and auto industry:<label> cohorts from a cached yfinance-industry mapper over the liquid (>=$1B) tape. The auto leg's coarseness is a MEASURED limit, not an assumption: yfinance files SPGI/MCO/FDS/MSCI/MORN together with ICE/NDAQ/TRU under 'Financial Data & Stock Exchanges', and because the exchanges were rallying that bucket's median is POSITIVE and the de-rate vanishes — so the auto leg is recall, the curated leg precision, and a diluted bucket is reported as a dilution_diagnostic rather than trusted (both pinned by regression tests). TWO GUARDS THE FIRST LIVE RUNS FORCED: (a) AUTO-LEG COVERAGE GATE — the mapper fills ~120 names/run so an early auto cohort is not its industry but whichever few names the budget reached first (run 3 produced an 'industry:Biotechnology' of FOUR names and fired on it); auto cohorts are built, counted and reported but CANNOT fire until the map covers 50% of the liquid tape, and the withheld set plus a runs-to-close countdown is printed every run. Curated cohorts are unaffected because their membership is explicit, not sampled. (b) DUPLICATE SUPPRESSION — when an auto bucket and a curated cohort hold essentially the same names (Jaccard >=0.8) only the CURATED one fires; run 1 handed the court the identical five-vendor question twice under two cohort names, and the suppressed twin keeps its state entry so it cannot re-fire tomorrow. SPY-benchmarked therefore US-only: intl sweep names are read for context and counted, never aggregated (a Tokyo line vs SPY measures the yen). Reads DISLOCATION_SWEEP.json / US_BROAD_DISLOCATION_SWEEP.json / INTL_DISLOCATION_SWEEP.json defensively for universe seeds and cross-check — every one optional, absence tolerated and named. DEGRADED-LOUD: unpriced members, unmapped liquid names (invisible to the auto leg, with a runs-to-close estimate) and cohorts under the member floor are all COUNTED and NAMED. Emits DETFIRE|cohort_dislocation|<COHORT>|<SEV>| for the theme plus a companion line for the BEST-IN-CLASS DRAGGED member (largest cap + least levered among the members actually falling; missing balance-sheet data scores NEUTRAL and is named, never treated as clean), each carrying the explicit court question 'cohort de-rate: is <name> dislocated with its cohort or correctly repriced?'. PROPOSES ONLY — a cohort that fell together may be correctly repriced; cause-check -> discovery_state -> court (v1.4) before any staging."},
    {"name": "broken_print_radar", "cmd": ["python3", "-m", "desk.broken_print_radar"],
     "cadence": "daily", "log": "desk/data/broken_print_radar.out",
     "asset_class": "equities", "extractor": "detector_scan", "enabled": True,
     "note": "the desk's BEST manual habit, systematized: re-underwriting a quality name after a violent single-day break (VRLA, KALMAR, DGE.L, BOBS all entered through this door). Daily scan of the WHOLE US tape for single-session losers <=-15% at >=$250M cap — the gap dislocation_sweep can't cover (it only sees the ~320 names we already have a verdict on, so a break at an un-researched name is invisible) and band_watch can't (ledger bands only). Per hit it computes TRIAGE METRICS ONLY, no verdicts: drop, volume vs 3mo ADV, market cap, net-debt/EBITDA + balance-sheet-intact flag (financials NA, near-zero EBITDA flagged RATIO_NOT_MEANINGFUL, missing = UNKNOWN never clean), earnings-day vs news-day (yfinance earnings dates, window = session + prior trading day), 12-month drawdown context, short interest, and whether we already hold it / have a ledger verdict. Source = Yahoo equity screener via yfinance.screen(EquityQuery) — server-side percentchange/mktcap/region filters; OTC/pink lines excluded by default (stale 100-share prints fake -17% moves), excluded counts always reported. STORE IS THE HISTORY: the screener has no history parameter, so desk/data/BROKEN_PRINTS.json (MERGE-ONLY by date+ticker, atomic replace, corrupt-file backup) is the only record of a past session — a missed day is gone. OPERATIONAL: Yahoo rate-limits by IP and enrichment costs 2 calls/name, so runs are paced and a YFRateLimitError fails LOUD with no store write (never a silent '0 hits'); repeated manual re-runs in one hour WILL trip it for ~30+ min. Emails via desk.mailer only when the session has hits NEW since the last scan (a re-run on the same tape is silent). SEVERITY = routing priority (size of break x size of company), explicitly NOT a view: a -20% day is usually correctly priced. PROPOSES ONLY — cause-check -> discovery_state -> court (v1.4) before any staging. Built 2026-08-02; first tape 2026-07-31 = 20 hits (10 balance-sheet-intact) on peak Q2-print Friday. v2: international venues (the desk's EU/KRX watchlist), an intraday leg, and a graded base rate on what a -15% day is worth."},
    {"name": "gen_japan_tob_lane", "cmd": ["python3", "verticals/generators/japan_tob_lane.py",
                                           "--days", "8", "--top", "60", "--intake"],
     "cadence": "daily", "log": "verticals/generators/data/japan_tob_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b DATED-CATALYST generator: the Japan TOB / take-private lane. TSE's "
             "cost-of-capital directive plus the parent-subsidiary listing cleanup made Japan "
             "the densest take-private pond in the developed world, and a tender pays on a "
             "contractual event rather than on the tape level. TWO BOOKS THAT NEVER MIX: "
             "(A) ANNOUNCED = live tender offers, a real spread book; (B) ANTICIPATORY = "
             "structural fingerprints with NO offer, an equity position with an undated "
             "catalyst — never annualized, never summed with A. "
             "CHANNEL: TDnet (release.tdnet.info/inbs/I_list_NNN_YYYYMMDD.html) — plain HTTP, "
             "NO key and NO browser, ~850 disclosures/day, formulaic titles, public PDF per "
             "row; terms come out of the standardised 買付け等の概要 table. EDINET API v2 is "
             "the better authority (docTypeCode 240 公開買付届出書) but returns 401 unkeyed — "
             "getting a free subscription key is the top upgrade. TDnet retains only ~31 DAYS, "
             "so THE STORE IS THE HISTORY (broken_print_radar lesson): a day never crawled is "
             "gone, which is why this is daily and not weekly. Anticipatory side is fully "
             "OFFLINE off 1,525 cached EDINET annual-report XBRL fact sets — the FIEA Art.24-7 "
             "parent declaration, 関係会社 owned-by %, 大株主 table, director birthdates. "
             "DOMINANT FAILURE MODE, now gated: a target bid at a real premium goes LIMIT-UP "
             "(ストップ高) with an O=H=L bar and an unfilled buy queue for 1-3 sessions; reading "
             "that print books a spread that never existed (first run: a phantom +23.5% on 3276 "
             "and +11.1% on 9110, both actually ~+1.2%). The lane carries the TSE 値幅制限 table, "
             "detects the lock, and refuses to rank a locked name — the ADIG thin-print rule in "
             "its Japanese form. Also gated: offer price is read ANCHORED to its label (7523's "
             "notice recites a FAILED 2025 offer at 1,670 before stating the live 1,900); "
             "pre-conditional offers get NO computed annualization, only a labelled scenario off "
             "the bidder's own guided window; 大株主 percentages are reconciled against issued "
             "shares before use (an unreconciled row is left BLANK, never guessed — the first "
             "version read Mizuho as owning 86.88% of TOSO vs the true 6.88%). Anticipatory "
             "scoring is GATED not summed: a control channel (>=33.4% holder, or an aged "
             "owner-operator with no successor) must fire before cheapness scores at all, "
             "because summing cash + low P/B + old directors just reproduces the deep-value "
             "shelf. Financials/utilities/real-estate excluded (regulated cash is not buyout "
             "funding). Every deal carries the minimum-tender floor (miss it and the spread goes "
             "to zero AND the stock re-rates — two-sided, not capped), the two-step squeeze-out "
             "timeline (株式売渡請求 ~1-2mo at >=90% vs 株式併合 needing an EGM, ~3-5mo), the JPY "
             "add on an already-unhedged Japan book, and the taxable-account note that tender "
             "proceeds are a disposition and not a rollover. Held-book overlap checked every "
             "run: 7222 Nissan Shatai (Nissan 50.0%, cash 57% of mcap, P/B 0.71) sits in our own "
             "anticipatory book, so the lane must not double-add that exposure. PROPOSES ONLY — "
             "every fire routes through the court before staging. Built 2026-08-04; first run "
             "38 deals / 9 live / 320 of 1,316 issuers clearing a control gate."},
    {"name": "gen_spinoff_orphans", "cmd": ["python3", "verticals/generators/spinoff_orphans.py"],
     "cadence": "daily", "log": "verticals/generators/data/spinoff_orphans_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b FLOW generator: the SPIN-OFF ORPHAN coverage-vacuum trade. Polls the EDGAR "
             "10-12B registration stream via the full-index form.idx (12mo backfill), parses each "
             "Exhibit-99.1 information "
             "statement for parent / tickers / record + distribution dates / ratio, trap-filters "
             "uplistings + holdco reorgs + RMTs, then classifies the forced-flow SIGN off live S&P "
             "500/400/600 membership. CRITICAL doctrine (from the 2026-07-04 one-shot): the US "
             "index leg is INVERTED for S&P 500 parents — S&P DJI places qualifying spincos back "
             "into an S&P index SAME-CYCLE, so funds are forced BUYERS (SOLS/Q/FDXF) and no "
             "washout occurs. The true forced-SELL cohort is (a) S&P500 parent -> spinco "
             "DOWNGRADED to 400/600 (MBGL) and (b) spinco with NO index placement; RMTs are "
             "excluded (zero holder flow). Tracks post-distribution price with leading "
             "zero-volume Yahoo bars dropped (the MFP phantom bar fabricates a -57% dump) and "
             "buckets the window 0-30d ACTIVE / 31-90d LATE / >90d CLOSED. Daily because the "
             "actionable state changes on single filings (an 8-A12B / a final amendment with the "
             "distribution date filled in) and the window is short. MERGE store by CIK. EXPAND: "
             "non-US no-auto-placement venues (DAX->MDAX, the Aumovio channel) + spin-debt / "
             "dividend-to-parent quality screen + the INVERTED pre-inclusion long"},
    {"name": "gen_tariff_refund_cohort", "cmd": ["python3", "verticals/generators/tariff_refund_cohort.py", "--pages", "8", "--max-docs", "900"],
     "cadence": "weekly", "log": "verticals/generators/data/tariff_refund_cohort_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "MECHANISM-FIRST Stage-0b cohort off the 2026-08-03/04 courts (FND/ISRG/ARHS/DSGX). SCOTUS struck the IEEPA tariffs 2026-02-20; the Section-122 replacement took effect 02-24 with a 150-day statutory sunset at 2026-07-24. One legal event splits the tape TWO WAYS by ACCOUNTING CHOICE, which is why the sell side misreads it. (A) EPS-MIRAGE FADES: the company RECOGNIZES the refund, GAAP EPS jumps, margin 'expands', consensus marks UP a one-timer - FND Q2-26 printed GAAP EPS +53.4% vs ADJUSTED FLAT with comps -2.1%, the $0.31 GAAP/adj spread WAS the refund, and consensus still went $1.903->$1.971 on 4 up-revisions in 7 days. Any screen reading estimate DIRECTION without estimate COMPOSITION buys tariff refunds. (B) POSITIVE-SKEW CONSERVATIVES: refund unrecognized (gain contingency) and/or the guide assumes the cost PERSISTS - ISRG's release assumed tariffs 'through the end of the year' (~$122M embedded) while its own 10-Q five days later printed the 150-day sunset; ARHS states its outlook 'does not include any benefit from potential IEEPA tariff refunds'. Masking channel = the non-GAAP reconciliation (A) / the unrecognized gain contingency (B); signal channel = EDGAR full text; latency = A resolves at the NEXT print (the compare breaks), B at the next guide. EDGAR EFTS 9-query set over 8-K/10-Q/10-K since 02-20, verbatim sentence extraction, marker-scored A/B with MONEY breaking the tie when both sides fire (a name that recognized $128M and holds a $2M residual is an A, not a B - the v1 CRI bug). GUARDS: magnitude FROM FILINGS ONLY, never estimated (unquantified prints as unquantified - the ARHS refund is real and its amount is genuinely unknown); consensus revisions labeled MARKET DATA, evidence only, never used to infer a filing fact; gate-6 no shorting attention names - A-rows carry short interest/days-to-cover and squeeze-fuel names are marked NO_SHORT, A-fades go to court as FADE-THE-ESTIMATE candidates; every B row carries the three MANDATORY confounders (Fed-Circuit stay extended 2026-06-11, Section 232/301 substitution, and INFORMED CAUTION - counsel did not forget the statute printed in its own 10-Q), which is the ISRG red-team lesson that cut that call 0.60->0.55 and struck its 'verified EDGE' label. B is RP_FAIR with a skew overlay, never an edge premium. Weekly because the cohort grows one earnings season at a time. v2: XBRL tie-out of the recognized refund to the non-GAAP reconciliation line, next-print compare-break calendar, and a decay gate once the sunset/substitution question resolves."},
    {"name": "gen_quality_drawdown", "cmd": ["python3", "verticals/generators/quality_drawdown.py", "--enqueue", "5"],
     "cadence": "weekly", "log": "verticals/generators/data/quality_drawdown_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "THE GENERATOR POINTED AT WHERE THE MONEY CAME FROM. Built 2026-08-03 after a P&L attribution showed 94% of the book's gains came from software/services/insurance/brands (HUBS, GCT, DFIN, CTSH, SAP, BRBY, MNDY, KNSL, G, HRTG) while EVERY generator we owned screened cheap-on-assets industrials, distributors and banks - we had industrialised the search for a kind of name that produced none of our returns. Calibrating the nine winners at their ENTRY prices gave one shared signature: bought 37-77% below the name's OWN 3-year high (median -46%), while still being a good business. This screens that: drawdown 35-78% from own 3y high, gross margin >=35%, revenue CAGR >= -2% (the melting-ice-cube guard), net debt/EBITDA <= 3.5x, cap >= $400M, plus a BASING flag (a name still making new lows is a falling knife). Deliberately NOT a value screen - book value is consulted NOWHERE, a name can trade at 6x sales and pass. That is the point, and it is why deep_value/EDINET/Euronext structurally cannot find these. Universe = Yahoo server-side screener over 8 cap bands (same rail as broken_print_radar); FAILS LOUD if the universe comes back thin rather than reporting a false 'no candidates'. Store MERGES by ticker - a name's drawdown history across runs is itself signal. PROPOSES ONLY: cause-check -> discovery_state -> court before any staging. Weekly because drawdown depth moves slowly; the daily edge is already covered by broken_print_radar."},
    {"name": "financials_screen", "cmd": ["python3", "-m", "verticals.deep_value.financials_screen", "--top", "20", "--enrich", "45"],
     "cadence": "weekly", "log": "verticals/deep_value/data/financials_screen_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "FINANCIALS-specific value screen (the ex-financials deep-value scan can't reach insurers/banks): P/B(-TBV) x ROE-consistency x quality gates on $300M-$10B US insurers/banks/asset-light fin-svcs. Court-open items (combined ratio / PYD / CET1 / NIM) surfaced not fabricated. Writes financials_shortlist.json. Built 2026-07-25; enabled per the silently-dead-watch lesson. Anti-stacking: ADJUDICATED set excludes held P&C (EG/HRTG/KNSL/WRB) + P&C-court verdicts + EM banks."},
    {"name": "deal_cycle", "cmd": ["python3", "-m", "verticals.frontrun_engine.deal_cycle.monitor", "--no-bdc"],
     "cadence": "weekday", "log": "verticals/frontrun_engine/deal_cycle/data/deal_cycle_cron.out",
     "asset_class": "equities", "extractor": "deal_cycle", "enabled": True,
     "note": "IPO/M&A deal-cycle regime gauge (DFIN context) — regime changes only"},
    {"name": "aumovio_peer", "cmd": ["python3", "verticals/deep_value/aumovio_peer_watch.py"],
     "cadence": "weekday", "log": "verticals/deep_value/data/aumovio_peer_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Aumovio (AMV0.DE) Aug-6 order-print previewer via European tier-1 peer read-across; FIRE-ADD at edge>=+20pp in-band, KILL-WATCH if read-across flips structural (trap), front-run on 2/3 front-half peer confirm; tells Valeo Jul-22/Aptiv Jul-30/Forvia Jul-31; auto-retire after Aug-6-2026"},
    {"name": "luxury_heat", "cmd": ["python3", "verticals/deep_value/luxury_heat.py"],
     "cadence": "weekly", "log": "verticals/deep_value/data/luxury_heat_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "luxury brand-heat index (Wikipedia + Google Trends quarterly, winner/loser cohort-z, backtested vs printed comps) — reads BRBY/KER book names; trends file needs a Chrome refresh periodically (429s headless)"},
    {"name": "hubs_breeze_tripwires", "cmd": ["python3", "verticals/deep_value/hubs_breeze_tripwires.py"],
     "cadence": "daily", "log": "verticals/deep_value/data/hubs_tripwires_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "HUBS Aug-5 pre-print tripwires (Breeze evidence sweep 2026-07-01): A community credit-chatter velocity (Cloudflare — often DEGRADED, check manually weekly), B credits-KB + product-catalog hash diff (pricing iteration = bullish tuning), C careers monetization-mention delta. FLAGs deltas; AUTO-RETIRES after 2026-08-05."},
    {"name": "gen_plume_clusters", "cmd": ["python3", "verticals/generators/plume_cluster_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/plume_cluster_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b: methane super-emitter clusters (Carbon Mapper) -> operator attribution via SignalOS -> enforcement/liability seeds. Free tier non-commercial."},
    {"name": "gen_attention_divergence", "cmd": ["python3", "verticals/generators/attention_divergence_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/attention_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b: Wikipedia attention acceleration across the research ledger (backtested instrument: ~0.4-0.5 corr, NULL print edge -> pointers only); demand-vs-drama Trends check = manual step."},
    {"name": "gen_hiring_waves", "cmd": ["python3", "verticals/generators/hiring_wave_scanner.py"],
     "cadence": "weekday", "log": "verticals/generators/data/hiring_wave_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b: hiring wave/freeze sweep over the ledger universe (LinkedIn guest, 25 names/run rotating, coarse page-1 counts) — capacity ramps lead revenue 1-2q."},
    {"name": "gen_warn_layoffs", "cmd": ["python3", "verticals/generators/warn_layoff_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/warn_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b: WARN layoff waves (CA EDD xlsx; TX/NY queued) — 60d leading; wave at a strong name = margin action, at a weak one = distress."},
    {"name": "gen_fda_velocity", "cmd": ["python3", "verticals/generators/fda_velocity_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/fda_velocity_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b: 510(k) clearance velocity by applicant (openFDA) — product cycles lead device revenue 2-4q; first run caught ISRG stall 5->0."},
    {"name": "gen_nih_grants", "cmd": ["python3", "verticals/generators/nih_grant_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/nih_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b: NIH SBIR/STTR grant flow to companies (RePORTER) — non-dilutive runway/validation; public orgs = seeds, private clusters = IPO watchlist."},
    {"name": "gen_country_risk_arb", "cmd": ["python3", "verticals/generators/country_risk_arb_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/country_risk_arb_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b: Damodaran CRP vs market-implied country premium (bank COE track + 5 hard guards: structural-CRP exclusion, hyperinflation gate, 2x bond floor, state flag, sector-cheapness). Internally quarterly (no-ops <75d). Proposes only."},
    {"name": "gen_award_flow", "cmd": ["python3", "verticals/generators/award_flow_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/award_flow_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b generator: whole-universe federal award-flow acceleration (USASpending, 6mo windows); DoD lags ~98d; SignalOS maps recipients->tickers. Improvement queued: filter state-agency grant noise."},
    {"name": "gen_insider_clusters", "cmd": ["python3", "verticals/generators/insider_cluster_scanner.py", "--days", "2"],
     "cadence": "weekday", "log": "verticals/generators/data/insider_cluster_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b generator: clustered code-P insider buys (EDGAR Form 4 XMLs, throttled). DOCTRINE: no informational edge claimed — attention allocation ONLY — drift backtest 2026-07-02 = NULL (small-cap median 63d excess NEGATIVE despite survivorship inflation); no seed priority. Proposes, never sizes."},
    {"name": "gen_litigation_flow", "cmd": ["python3", "verticals/generators/litigation_flow_scanner.py", "--days", "7"],
     "cadence": "weekly", "log": "verticals/generators/data/litigation_flow_cron.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "Stage-0b generator: NEW material federal suits (securities/RICO/qui-tam via CourtListener anonymous search) w/ corporate defendants -> avoid/short seeds."},
    {"name": "gen_distress_8k", "cmd": ["python3", "verticals/generators/distress_8k_scanner.py", "--days", "7"],
     "cadence": "weekly", "log": "verticals/generators/data/distress_8k_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b generator: distress tells (Item 4.01 auditor changes, NT 10-K/Q, covenant waivers, going-concern 8-Ks via EDGAR full-text) -> avoid/short seeds + dislocation-buy candidates."},
    {"name": "gen_preferred_oddlot", "cmd": ["python3", "verticals/generators/preferred_oddlot_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/preferred_oddlot_cron.out",
     "asset_class": "preferreds", "extractor": "generic", "enabled": True,
     "note": "Stage-0b CARRY generator: mispriced $25-par preferreds & baby bonds — the purest office edge (institutions can't trade odd lots economically). Screens discount-to-par x illiquidity (the neglect signature); live dividend from yfinance (no hardcoded coupons). Seed universe (we hold OXLCZ) -> EXPAND; credit-money-good is the DD/court step (deep discount on impaired credit = trap). v1 candidates: SLG-PI/CIM-PA/GNL-PB office+mREIT preferreds"},
    {"name": "gen_kalshi_divergence", "cmd": ["python3", "verticals/generators/kalshi_divergence_scanner.py"],
     "cadence": "weekday", "log": "verticals/generators/data/kalshi_divergence_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b INFO generator: prediction-market (Kalshi) vs equity-implied divergence. PRICE markets (index/stock level) -> kalshi P(S>K) vs a realized-vol lognormal = a lead/lag or IV-vs-HV gap. KPI markets (company print) -> the crowd-implied median per operational metric (CMG comps ~+1.8% / URBN 810 stores / SCHW 39.7M accounts) = a prediction-market NOWCAST of the print, comparable to consensus/our MFT nowcast + the EXACT market_p for any OPEN earnings call we froze (Brier-vs-market, not RELATED). Seed 11 equity-linked series -> EXPAND"},
    {"name": "gen_russell_recon", "cmd": ["python3", "verticals/generators/russell_recon_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/russell_recon_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b FLOW generator: the annual Russell reconstitution — the year's biggest price-INSENSITIVE forced flow (index funds MUST trade the adds/deletes/migrations at the late-June effective close). Calendar-driven countdown; fires when the ~4-week prelim-list window opens (~late May) to surface the air-pocket (deletes) / pop (adds) / R2000<->R1000 migration-squeeze trades. Currently DORMANT -> 2027 effective ~Jun-25. The MFP FLOW class made recurring + calendar-certain"},
    {"name": "gen_lockup_expiry", "cmd": ["python3", "verticals/generators/lockup_expiry_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/lockup_expiry_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b FLOW generator: IPO lock-up expiry = a DATED, price-INSENSITIVE forced-SUPPLY event. Insiders/pre-IPO holders sign a 180d (90/365 seen) underwriter lock-up; at expiry a large locked count can hit a thin float -> pre-unlock drift-down + unlock-day air-pocket. BUY the forced-seller washout (the ADIG orphan-spin pattern), not short into it. Scans EDGAR 424B4 full-text (last 200d), parses the lock-up term (else DEFAULT 180 flagged estimated), buckets imminent 0-21d / upcoming 22-90d, flags SPAC/units (air-pocket applies at DE-SPAC). Magnitude (locked vs float) is a DD pull, NOT fabricated. Caveat: 424B4 stream includes follow-ons (DD confirms first-lockup). EXPAND: de-SPAC 424B3 + secondary-lockup tranches + IPO-vs-follow-on classifier"},
    {"name": "gen_spac_trust_arb", "cmd": ["python3", "verticals/generators/spac_trust_arb_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/spac_trust_arb_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b CARRY generator: pre-deal SPACs trading BELOW trust value = a near-guaranteed cash floor (every public holder can REDEEM for pro-rata trust+accrued-interest at the vote/extension/liquidation) plus free deal/warrant optionality. Institutions skip them (odd-lot / sub-threshold) = the office capacity edge. Trust-per-share from PRIMARY SEC XBRL (AssetsHeldInTrust / TemporaryEquitySharesOutstanding); price live from yfinance; $9-13 plausibility + period-consistency guard so a stale share count can't fabricate a discount. Seed ~23 active SPACs -> EXPAND (v2: SIC-6770 auto-discover, parse deadlines from 8-Ks). v1: LEGO +1.39% below trust; per-share NULL-flagged where no redeemable-share XBRL"},
    {"name": "gen_insider_10b51", "cmd": ["python3", "verticals/generators/insider_10b51_scanner.py", "--days", "10", "--pages", "4"],
     "cadence": "weekday", "log": "verticals/generators/data/insider_10b51_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b INFO generator: (a) open-market BUY CLUSTERS (>=2 distinct insiders, code-P >=$50k each, <=10d) tagged with the Rule 10b5-1 indicator — DISCRETIONARY clusters are the stronger tell; (b) 10b5-1 PLAN TERMINATIONS (v1: EFTS full-text 'Rule 10b5-1'+'terminated' on 10-Q/10-K/8-K -> DD review queue, since Item 408 is free-text). Complements gen_insider_clusters with the 10b5-1 dimension. Narrow/high-precision (recall-floor). Proposes, never sizes. v2: proper Item 408 parse + borrow-fee overlay + mktcap gating"},
    {"name": "gen_subthreshold_arb", "cmd": ["python3", "verticals/generators/subthreshold_arb_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/subthreshold_arb_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b CARRY generator: SUB-THRESHOLD all-cash merger arb. Arb funds skip small all-cash deals (<~$500M target equity value) — small deals carry a WIDER spread for the SAME regulatory/financing/MAC break risk arb desks crowd to a few bps on large deals (capacity-ceiling / fee-replication CARRY). Discovers cash merger agreements via EDGAR EFTS (8-K/DEFM14A/SC 14D9), parses '$X.XX per share in cash' from PRIMARY exhibits, prices live via yfinance, gates deal value < $500M, sorts by spread. Gates: non-binding-proposal/PIPE veto, definitive-agreement requirement, SPAC exclusion (-> spac_trust_arb). Break risk is REAL/larger for small deals — every candidate carries conditions + a break-risk caveat (the DD/court step: a wide spread PRICES low close-probability, not free money). v1: LSTA $4.00 (+5.8%, ~28% ann) / LPRO $3.15 / DXLG hostile $0.82 (+32%). v2: stock/collar deals, condition scoring, break-rate-adjusted spread"},
    {"name": "gen_auditor_late_filing", "cmd": ["python3", "verticals/generators/auditor_late_filing_scanner.py", "--days", "120", "--window", "90", "--pages", "6"],
     "cadence": "weekday", "log": "verticals/generators/data/auditor_late_filing_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b EXCLUSION generator (ANTI-PORTFOLIO, do-NOT-own): 8-K Item 4.01 auditor change INTERSECTED with an NT 10-K/NT 10-Q late-filing within ~90d = a high-precision distress/fraud precursor. The CONJUNCTION is the precision gate — either signal ALONE over-fires (recall-floor), so ONLY names with BOTH are surfaced. resigned_bool: an auditor RESIGNING ranks worse than dismissed. Reports n_auditor_only + n_late_only to show the gate's selectivity. Complements the small-cap-honesty catastrophe-exclusion overlay. READ-ONLY. First run: 208 auditor / 607 late -> 54 excluded (9 resigned): CFOO/GLAI/GWTI + VERI/FRPH/KRMN. v2: parse the 8-K disagreement/reportable-events language, going-concern overlay, mktcap gating"},
    {"name": "gen_ptab_itc_docket", "cmd": ["python3", "verticals/generators/ptab_itc_docket_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/ptab_itc_docket_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b INFO/LATENCY generator: patent-validity (PTAB IPR/PGR -> Final Written Decision ~12mo post-institution) + tariff (ITC Section 337 -> exclusion-order determination ~16-18mo) rulings move single small caps on a PUBLISHED docket the market doesn't price until the press release. Edge = reading the calendar nobody reads. Each row binds to the SPECIFIC docket (337-TA-#### / PTAB trial no.) and names the tradeable party with catalyst-identity discipline (low-confidence single-token maps flagged, not bound). ITC leg keyless via Federal Register (working: 66 investigations, 15 ticker-mapped incl CRDO 337-TA-1446 ~29-99d); PTAB leg needs USPTO_ODP_KEY (keyless API decommissioned 06-2026) -> degrades gracefully to UNAVAILABLE. Outcomes ~50/50 -> INFO nowcast that TIMES the catalyst; convexity/defined-risk sizing downstream (no premium selling). v2: PTAB institution leg, outcome base-rates, patent-assignee->ticker resolve"},
    {"name": "gen_thematic_etf_rebalance", "cmd": ["python3", "verticals/generators/thematic_etf_rebalance_scanner.py"],
     "cadence": "weekday", "log": "verticals/generators/data/thematic_etf_rebalance_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "FLOW class — thematic-ETF (ARK) rebalance forced-flow, the CAPACITY edge: ARK adds/drops $1-3B names whose public float is too small for anyone big to arbitrage, so an add = a pop and a trim/drop = an air-pocket that ISN'T crowded (opposite of S&P/Russell recon where the street front-runs a large-cap add). Signal-1 = ownership concentration (ARK days-of-ADV + est % of float). Signal-2 = day-over-day share deltas that ACCUMULATE across cron runs (ARK's CSV is same-day-only; the persisted state file IS the history). READ-ONLY; the tradeable trigger is a real ARK add/trim. v1: SLMT 26% float / CERS / NTLA / CRSP (small-cap genomics). v2: iShares/Global X holdings; scheduled index-rebalance dates; add=pop/drop=air-pocket entry side"},
    {"name": "gen_cef_term_liquidation", "cmd": ["python3", "verticals/generators/cef_term_liquidation_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/cef_term_liquidation_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "CARRY: TERM / TARGET-TERM CEFs converge discount-to-NAV to ~0 on a DATED prospectus termination event (buy the discount, collect the mechanical pull-to-NAV; nearer date + wider discount = higher annualized convergence). Odd-lot names institutions ignore = the office capacity edge. Price from yfinance, NAV from the X<ticker>X pseudo-quote (honest NULL where it won't resolve, ~56% coverage). DISTINCT from the REFUTED frontrun_engine pre-IPO CEF NAV-remark leg (there price LEADS the mark); the term-EVENT leg is a hard contractual forcing date, UNTESTED. CAVEAT: term can be extended via an 'eligible tender offer' (soft date, esp. RiverNorth/NMCO/BGB/BSL). v1: BGB 4.27% disc ~3.64%/yr (2027), BSL nearest 2027, BTT 7.74% (2030). v2: N-2/N-CEN auto-discover, robust NAV feed, activist-tender leg"},
    {"name": "gen_january_reversal", "cmd": ["python3", "verticals/generators/january_reversal_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/january_reversal_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "FLOW-class January-effect REVERSAL generator — the buy-the-bounce leg that PAIRS with gen_december_dislocation. Small-caps dumped for December tax losses snap back in January as the price-insensitive forced selling lifts; survives only in small caps too small for the factor funds that arbitraged it out of large caps (capacity edge). DORMANT off-season (empty candidates is correct) with a dated countdown; activates ~mid-Dec, re-framing december_dislocation's screened loss basket as reversal re-entries. FLOW re-rating not a fundamental call — quality-at-a-loss DD+court MANDATORY (that cohort is where value traps hide). Next reversal window ~2026-12-20"},
    {"name": "gen_borrow_fee", "cmd": ["python3", "verticals/generators/borrow_fee_scanner.py"],
     "cadence": "weekday", "log": "verticals/generators/data/borrow_fee_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b INFO generator: broad short-PRESSURE scan — FINRA daily short-volume ratio spiking >=~10-15pp above a 20d baseline for >=2 consecutive days (the squeeze_watch fingerprint, generalized beyond the SpaceX ASTS/BKSY/LUNR basket). CLASSIFIES each spike via the conditioning layer (discovery_state, top MAX_CLASSIFY=25) into distress (short is right -> AVOID) vs squeeze-setup (crowded short on an un-broken name) vs noise. DOCTRINE: a short-pressure spike measures SUPPLY/positioning NOT conviction (the MAUDE-velocity LR~1 lesson) -> PROPOSES only, never sizes on the spike alone; a signal on a DISCOVERED_CROWDED name is not a fresh trade (RCAT). Heavy FINRA 20d download = slow, runs unattended on the weekday cron. v2: a real borrow-fee/utilization feed, demand-vs-supply decomposition, days-to-cover overlay"},
    {"name": "gen_export_anomaly", "cmd": ["python3", "verticals/deep_value/import_anomaly_scanner.py", "--exports"],
     "cadence": "weekly", "log": "verticals/deep_value/data/export_anomaly_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b generator: whole-universe HS4 EXPORT acceleration/rollover (Census) — who is selling abroad faster."},
    {"name": "gen_lse_shelf", "cmd": ["python3", "verticals/generators/lse_shelf.py", "--top", "30"],
     "cadence": "weekly", "log": "verticals/generators/data/lse_shelf_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "Stage-0b VALUE generator: the LSE Main + AIM small-value shelf (~$50M-2B), sibling of gen-less euronext_shelf. UNIVERSE IS PRIMARY — the exchange's own price-explorer API swept per (market x ICB sector), not a Yahoo screener: complete (no result cap), and it carries the market segment (which decides stamp duty), the ISIN (the exact join to the Takeover Panel's daily offer-period table) and the ICB sector (which excludes the 306 closed-end investment companies that are 30% of the Main Market). Composite + guards imported from deep_value/score.py, never reimplemented. UK-specific economics scored per name, not assumed: 0% dividend WHT is a real edge but it is an INCORPORATION fact (9 Jersey / 5 Irish lines on the shelf carry their own rate), and 0.5% SDRT is a real friction that AIM lines and non-UK issuers do not pay. Guards this build adds over the Euronext leg: pension/IAS-19 added to debt NET OF TAX (the SFPI correction — gross over-captures), FCF on total capex with a capitalised-development ratio (the Tecnotree wedge), durability guard conditioned on 2-year cash generation (the HUBS fix — first implementation; it existed only by reference), ebit_trend anchored on the PEAK as well as the oldest year (45% of this shelf is trough-anchored, so the oldest-year anchor flatters nearly half of it), MEDIAN not mean ADV (first equity implementation in the repo) plus a live bid/offer touch, path fields on quality_drawdown's constants, a four-way share-count cross-check (the HOOD dual-class error), and the PFIC gate ON with the FMV overlay against euronext's skip (UK closed-ends are statutory PFICs and a de-rate MANUFACTURES the status). Yahoo is SECONDARY and only supplies fundamentals + bars; anything reaching a court re-derives from the annual report / RNS. --refresh-universe monthly (~90 API calls, 9 min). First run 2026-08-04: 1,599 lines -> 249 scored, 210 printable, 118 AIM."},
    {"name": "lab_scheduler_panel", "cmd": ["python3", "-m", "desk.lab_scheduler_panel"],
     "cadence": "weekly", "log": "desk/data/lab_panel_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "DGX/LH leading-utilization proxy: weekly next-available routine-draw appointment sample over a FIXED 12-metro x 2-company panel (desk/data/lab_panel/panel.json) -> per-company median days-to-next-slot / %same-day / %within-48h + Quest walk-in wait, appended to lab_panel/history.jsonl. Slot scarcity leads requisition volume by up to a quarter. PAPER until graded vs the October volume prints (beat consensus = the gate). Confounder: capacity adds shorten waits while volume RISES — cross-check hiring_velocity before reading a delta as demand. Anonymous public surfaces only (Quest find-location CSRF-sniff + Labcorp patient-app JWT-sniff, in-page replay); a blocked scheduler = DATA MISSING never zero; --manual CSV fallback. Built 2026-07-23."},
    {"name": "disclosure_watch", "cmd": ["python3", "-m", "desk.disclosure_watch"],
     "cadence": "hourly", "log": "desk/data/disclosure_watch_cron.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "GENERALIZED entity-disclosure rail (2026-07-29, user: 'not just Japan/Nintendo'; supersedes tdnet_watch same-day - state migrated, do NOT re-register the old module). Principle: risk drivers are ENTITIES on NATIVE planes; the watchmap covers the entity on its plane. Day-1: 13 entities x 3 adapters - tdnet (Nintendo 7974 = Hosiden's 78% tail; Hosiden 6804), edgar by hardcoded CIK w/ LOUD form classes 8-K/6-K/S-3/13D-G/144/424B (WAL/FSBW/OMF/NPB/QCOM/JMKE - NPB's S-3 tripwire lives here now), rss_or_page (Kalmar GNW, Verallia PDFs, LAGARDERE regulated-info ALWAYS-LOUD = the MMB re-open signal, Jungheinrich newsroom = the missed-ad-hoc scar's remediation, Kering GNW). Clear email + push within the hour, why/positions + doctrine line in every body ('a risk-driver disclosure re-opens the name's pack/court BEFORE acting on price'). STAGING RULE: every new position adds one dict per risk-driver entity named in its kill triggers."},
    {"name": "calendar_guard", "cmd": ["python3", "-m", "desk.catalyst_calendar_guard"],
     "cadence": "weekly", "log": "desk/data/calendar_guard_cron.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "KER-postmortem RC3 remediation: every OPEN forward-dated calibration call checked against the ticker's ACTUAL next earnings date (yfinance, threaded w/ per-ticker timeout, 7d cache); a print landing >3d before its trigger emits NEEDS-PACK (the earlier print can pre-determine the binary). One flag per ticker+date, re-arms when the date passes; DATA MISSING never silence. FIRST RUN 07-29: 25 flags incl THREE next-day prints (RBLX/PEO.WA/DFIN) - the failure class was endemic, not a KER one-off. yfinance dates are ESTIMATES: re-date frozen calls only on announcement PRs, but ARM PACKS on the estimate."},
    {"name": "cds_activity_watch", "cmd": ["python3", "-m", "desk.cds_activity_watch"],
     "cadence": "weekly", "log": "desk/data/cds_activity/cron.out",
     "asset_class": "credit", "extractor": "generic", "enabled": True,
     "note": "CDS leg of the AI-break tripwires (2026-09-12, principal ask). DTCC Trade Information Warehouse QUARTERLY single-name CDS ACTIVITY (dealers, avg daily notional, trades/day) for the AI-capex issuers (ORCL/AMZN/META/GOOGL/MSFT/DELL/AVGO/INTC/MU/SOFTBANK/NVDA/SMCI/ANET/EQIX/DLR/VRT) and the neocloud CANARIES (CoreWeave/Core Scientific/Nebius/IREN/Applied Digital/Lambda/Crusoe/xAI/OpenAI). Fires: NEW-FILE (always emailed), AI-ACTIVITY-UP (notional/day +50pct QoQ or dealers +3), CANARY-LISTED (a neocloud's FIRST cleared single-name appearance - CoreWeave was ABSENT in Q3-2025). Positioning/market-existence, NOT spreads: single-name CDS spreads have no free feed (ticket: TWS bond-yield leg). Fast broad leg = weekly_dashboard OAS z-fires (ig/bbb/hy/ccc_oas, cohort AI-BREAK)."},
    {"name": "agent_herd_pilot", "cmd": ["python3", "-m", "desk.agent_herd_pilot", "--summary"],
     "cadence": "weekday", "log": "desk/data/agent_herd/summary_cron.out",
     "asset_class": "cross", "extractor": "generic", "enabled": False,
     "note": "AGENT-HERD PILOT (pre-registered 2026-09-12, principal question 'can we front-run retail agentic traders?'). ZERO CAPITAL. Timing-critical legs run under launchd, NOT this heartbeat: com.signalos.agentherd.run 06:05 PT weekdays (pre-open panel: 3 model sizes x generic retail-agent prompt over CNBC/MarketWatch RSS + Stocktwits trending + Yahoo most-actives) and com.signalos.agentherd.grade 13:40 PT (flow-hit at T+1, excess vs SPY AND vs an attention control of unpicked most-actives at T+1/5/20, reversal). Kills frozen in the module docstring and packs PILOT-AGENTHERD|2026-10-26 (K1 flow, K2 no price effect) / |2026-12-08 (K3). Base rate: 5 front-run pilots killed. This registry row is documentation only (disabled) so the consolidated registry lists it."},
    {"name": "band_watch", "cmd": ["python3", "-m", "desk.band_watch"],
     "cadence": "hourly", "log": "desk/data/band_watch_cron.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "ENTRY/EXIT band rail on the hourly heartbeat (2026-07-29, post-KER-postmortem: the 6:15/7:45 sentinel runs alone missed intraday touches). Every ledger alert_below/alert_above priced via yf; fire -> macOS+ntfy push + the CLEAR email (subject ENTRY BAND HIT: <tickers>, body = verdict snippet + entry note + dossier link + the fired-gates-fill-or-grade doctrine line). One alert per crossing, re-arms on a 5% clear. ORDER_COVERED names excluded on the below side (a resting GTC IS the trigger) - keep that set synced to the BLOTTER not to instructions (unapproved IBKR instructions are not orders). Idempotent alongside the sentinel runs (shared state file).",},
    {"name": "kalmar_order_nowcast", "cmd": ["python3", "-m", "desk.kalmar_order_nowcast"],
     "cadence": "weekday", "log": "desk/data/kalmar_nowcast_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "FORWARD INSTRUMENTATION for the KALMAR.HE starter (owned-name doctrine, first instance 2026-07-29): nowcasts EQUIPMENT ORDER INTAKE — the position's load-bearing variable — ahead of the Q3 print (Oct-29). Channels: TED EU cargo-handling tenders CPV 42414* (pre-award leads bookings by months; publication-date censored), Kalmar order-PR QTD count (GNW; FLOOR detector — zero past day 45 = visibly weak; 0 items parsed = DATA MISSING never zero), RWI/ISL throughput index (macro anchor vs Drewry +3.0% glide), EPA Clean Ports change-detect (ZE cargo-handling awards feed the eco-share tripwire). Wired to the EC kill list: B2B<0.95 x2 (Q2=0.94 strike ONE) + eco<35% (last 40%). TRIPWIRE NOWCAST not alpha (frontrun ledger 4-for-4 negative on pipeline-leads-stock); grades vs frozen KALMAR.HE|2026-10-29 earnings_operating call. PAPER until graded."},
    {"name": "bank_callreport_watch", "cmd": ["python3", "-m", "desk.bank_callreport_watch"],
     "cadence": "weekly", "log": "desk/data/bank_callreport_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "v1.5 forward instrumentation for the WAL + FSBW starters: FDIC BankFind financials poll (api.fdic.gov — old host 301s) grading the red-team kill triggers MECHANICALLY on each new call report (fires on fresh REPDTE only). WAL cert 57512: uninsured % (>40% bar; 36.48% at 2026Q1, rising), uninsured-up-while-insured-down, NCO ann >0.60% (Q1 flagged 1.33% = the KNOWN fraud quarter — correct catch). FSBW cert 57633 (resolved via institutions API, cached; guessed cert was a defunct 2012 bank — resolve-first validated): C&D/RBC >115% bar (102.9% at Q1), retail-deposit proxy -5% seq, ACL<1.10% w/ NCO>0.5%. UNSERVED fields named every run: CDARS/ICS reciprocal (DEPINS proxy), holdco nonaccrual/TCE (bank-level only; NCLNLSR GNMA-inflated = TREND_ONLY never graded). Q2-26 call reports land ~late Aug. Grades vs WAL|2026-10-31 + FSBW|2026-10-31 window calls (print dates unannounced; re-date on the announcement PRs). PAPER until graded."},
    {"name": "vrla_volume_watch", "cmd": ["python3", "-m", "desk.vrla_volume_watch"],
     "cadence": "weekly", "log": "desk/data/vrla_volume_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "v1.5 forward instrumentation for the VRLA.PA starter: Eurostat monthly production index NACE C23.13 hollow glass (sts_inpr_m, CA, 2021=100) FR/IT/ES/DE/EU27 + rough Verallia-footprint weighted read -> leading proxy for the Q3 volume kill-bar (graded Oct-27). FLAG: weighted YoY <-2% two consecutive months. First run 07-29: weighted +2.2% (INFO) but FRANCE — the largest weight — negative 3 straight (-0.6/-9.0/-6.1%); Iberia strong partly base-effect. BASIS RISK named: market index incl competitors + tableware, ~2mo lag; direction/persistence is the signal never the level. Grades vs VRLA.PA|2026-10-27 frozen call. PAPER until graded."},
    {"name": "official_series_refresh", "cmd": ["python3", "-m", "desk.official_series", "refresh"],
     "cadence": "weekly", "log": "desk/data/official_series_cron.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "the MARKET LAYER refresh: polls every series in the desk/official_series.py REGISTRY "
             "and FLAGs each NEW month that prints (series name + value + YoY) plus any REVISION of "
             "an already-recorded period. Built 2026-08-10 on the principal's directive that the "
             "answer to 'we need Macau GGR' is a series registry any issuer can dispatch against, "
             "NOT a seventh bespoke macau_ggr_watch alongside vrla_volume_watch / "
             "bank_callreport_watch / the KALMAR TED+Census nowcast — those are registered as "
             "commented migration candidates and converge here. v1 rows: macau_ggr (DICJ, MOP "
             "million, T+1 BUSINESS DAY — the fastest official print the desk owns), "
             "macau_visitor_arrivals (DSEC, persons, ~T+4wk) and macau_hotel_occupancy (DSEC, "
             "percent, ~T+4wk), which together separate 'demand fell' from 'we lost share' from "
             "'spend-per-visit compressed' for LVS/WYNN/MGM/MLCO and the HK-listed operators. "
             "ADAPTERS ARE PER AGENCY not per series (dicj() reads report_en.xml behind the JS/XSLT "
             "monthly page; dsec() posts to the TimeSeriesApi the /ts SPA uses — no key, no "
             "browser), so a new series from a known agency is a registry row. FAILURE SEMANTICS "
             "mirror facilities_resolver exactly (fc34665d): an outage / wrong-shaped payload / "
             "UNIT DRIFT is degraded, surfaced LOUD and NEVER cached, while a genuine empty read is "
             "a real observation and IS cached; history MERGES by period and a changed value is "
             "recorded as a revision rather than clobbered. Rate series (occupancy) take "
             "percentage-POINT YoY and REFUSE quarter summing; levels take percent change. Weekly "
             "because the cadence is monthly and a once-per-day refetch floor keeps the bench "
             "prompts from re-polling an agency on every court. Wired into the brain: APPLIES_TO "
             "(kind m_source) + the KG shim at verticals/buyside_dd/m_sources/official_series.py, "
             "and render_series() injects the matched table into detector_preflight's planner "
             "prompt under MARKET LAYER."},
    {"name": "positions_board", "cmd": ["python3", "-m", "desk.positions_board"],
     "cadence": "hourly", "log": "desk/data/positions_board.out",
     "asset_class": "meta", "extractor": "generic", "enabled": True,
     "note": "Open-trades board JSON for /static/positions.html - joins positions + court verdicts + resting exit/entry rungs + next dated events + rule-6/stacking flags. Live prices reach the page via the symlinked /static/live_quotes.json (quote daemon, 60s client refresh); this cron only rebuilds structure."},
    {"name": "orders_calendar", "cmd": ["python3", "-m", "desk.orders_calendar"],
     "cadence": "hourly", "log": "desk/data/orders_calendar.out",
     "asset_class": "meta", "extractor": "generic", "enabled": True,
     "note": "Resting-orders + expiry calendar JSON for /static/orders_calendar.html (bands-rest-by-default doctrine 08-05: every order catalyst-dated; UNDATED bucket = violations surfaced, never hidden). Merges live orders_cache + *-REVIEW/*-CXL packs + grading packs + staged instructions from EC files. Cheap, local-only."},
    {"name": "conservatism_audit", "cmd": ["python3", "-m", "desk.conservatism_audit"],
     "cadence": "monthly", "log": "desk/data/conservatism_audit/cron.out",
     "asset_class": "meta", "extractor": "generic", "enabled": True,
     "note": "IS-CONSERVATISM-PAYING audit per desk/AUDIT_SPEC_CONSERVATISM.md v1.0 (frozen 2026-08-05). Run-1 verdict: NET -$204k/35d - selection NEUTRAL (C1 precision 0.49, $~0 net), cost = bands-never-met ($115k) + idle drag ($89k). Levers: RP_FAIR meet-the-price CONDITIONAL; deployment cadence = binding fix; bar unchanged pending N>=100. Run-2: add fill-cause subgrade + daily-NAV drag + recover 229 no-date records."},
    {"name": "pz2_hype_watch", "cmd": ["python3", "-m", "desk.pz2_hype_watch"],
     "cadence": "daily", "log": "desk/data/pz2_hype/cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "FDEV two-signal gate instrumentation (principal 08-04: pre-binary commitment OK WITH measured hype edge). PRE-LAUNCH: daily Steam wishlist rank (top-60 = T1 hype leg TRUE -> stage once ~09-10 accounts also clean; >200 or >100-at-T-7 = warning). POST-LAUNCH (10-13+): daily review positive-rate -> the LADDER (>=85 bull/78-85 base/70-78 warn/<=67 bear) = the T2 gate, verdict emailed 10-15. Volume secondary BY DESIGN (the pace bar passed the reference flop). Followers/Reddit legs blocked-manual. Grades vs FDEV|2026-09-30 frozen 0.80 + pack."},
    {"name": "hood_9cir_docket", "cmd": ["python3", "-m", "desk.hood_9cir_watch"],
     "cadence": "hourly", "log": "desk/data/hood_9cir_watch.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "DETECTION link for the HOOD event-contract catalyst: CourtListener poll on consolidated 9th Cir. 25-7187/25-7516/25-7831 (argued+submitted 2026-04-16, Nelson/Bade/Lee). On a disposition-shaped entry: emails via mailer + stamps hood_9cir_state.json -> an agent reads the opinion and runs the PRE-COMMITTED branches in resolution pack HOOD-9CIR|2026-12-31 (thesis: desk/reports/courts_20260804/HOOD_CATALYST_PACK.md). Frozen timing call 0.52; conditional direction 0.34/0.44/0.22. Sub-sigma event — no pre-position by design; agents STAGE, principal clicks (Rung-1 unearned). API trap: dateArgued NULL on member dockets, read docket text."},
    {"name": "bke_monthly_comps", "cmd": ["python3", "verticals/deep_value/bke_monthly_comps.py"],
     "cadence": "weekly", "log": "verticals/deep_value/data/bke_monthly_comps_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "PRIMARY-data melt tripwire for BKE: monthly net-sales/comps PR watch (Buckle still reports monthly). Fires on negative month; 2 consecutive = MELT WARNING (the DD falsifier). Built after the attention layer came back NULL/unmeasurable for apparel."},
    {"name": "sterv_demerger_watch", "cmd": ["python3", "verticals/deep_value/sterv_demerger_watch.py"],
     "cadence": "weekly", "log": "verticals/deep_value/data/sterv_demerger_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "STERV (Stora Enso) highest-value thesis-integrity tripwire: reads the forest-demerger commitment language off storaenso.com IR + newsroom (curl_cffi chrome124 — plain urllib/curl 403). Baseline anchor = 'complete it in the first half of 2027' (verbatim, Nov-2025 inside-info). FLAGs (a) softening/hedging vocab, (b) timeline move off H1-2027, (c) DISAPPEARANCE of the commitment across ALL live pages (absence = loudest, but requires >=1 successful fetch + all-page agreement — the SPCX false-absence guard: a DEGRADED fetch is DATA MISSING, never 'gone'). The SOTP trade IS the demerger completing on schedule, so this monitors the one load-bearing catalyst. Baseline seeded 2026-07-23; 'enabled':True per the 2026-07-22 dead-watch lesson."},
    {"name": "snapshot", "cmd": ["python3", "-m", "desk.snapshot"],
     "cadence": "weekday", "log": "desk/data/snapshot_cron.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "daily dated copies of the irreplaceable stores (calibration ledger = the skill record) + log trim; 30d retention; idempotent"},
    {"name": "venue_class", "cmd": ["python3", "verticals/generators/venue_class_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/venue_class.out",
     "asset_class": "equity", "extractor": "generic", "enabled": True,
     "note": "retailer venue-class mix vs valuation (A-mall lift screen); census-driven (aggregation-cost moat); NARROW claim per docstring — seeds carry no priority pre-validation"},
    {"name": "registry_audit", "cmd": ["python3", "-m", "desk.registry_audit"],
     "cadence": "weekly", "log": "desk/data/registry_audit.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "price-registry symbol+currency verification vs the live feed (CBKD GBP-mislabel / 028260 KRW-as-USD lessons); every mismatch here is a future phantom-tick incident"},
    {"name": "crossborder_twins", "cmd": ["python3", "verticals/generators/crossborder_twin_scanner.py"],
     "cadence": "weekday", "log": "verticals/generators/data/crossborder_twins.out",
     "asset_class": "equity", "extractor": "generic", "enabled": True,
     "note": "EM/DM twin-pair EY gaps vs lambda-adjusted CRP (growth + structure guards); the DISLOCATION use is gap-vs-baseline drift, not levels — baseline saved 2026-07-03"},
    {"name": "missed_entry", "cmd": ["python3", "-m", "desk.missed_entry_score"],
     "cadence": "weekly", "log": "desk/data/missed_entry.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "the anti-book for ENTRIES: grades every price gate JUSTIFIED/PREMATURE/WRONG vs realized paths (blue-team ruling 2026-07-03); the metric = realized dip-frequency vs required dip-probability"},
    {"name": "seasonality_calendar", "cmd": ["python3", "-m", "desk.seasonality", "--calendar"],
     "cadence": "weekly", "log": "desk/data/seasonality_calendar.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "annotates every upcoming earnings_print prediction with its seasonal shape + hard/easy-comp flags (IBEX lesson: a 'scary decel' was normal June-quarter shape + one anomalous comp)"},
    {"name": "december_dislocation", "cmd": ["python3", "verticals/generators/december_dislocation_scanner.py"],
     "cadence": "weekly", "log": "verticals/generators/data/december_dislocation.out",
     "asset_class": "equity", "extractor": "generic", "enabled": True,
     "note": "the buy-side of other people's tax-loss harvests: quality losers <=-30% YTD passing the deep-value gauntlet; SELF-GATES to Oct-Dec (off-season = fast exit); shortlist -> DD+court early Nov -> ladders pre-Thanksgiving -> the $0.5-0.75M December reserve"},
    {"name": "polymarket_whales", "cmd": ["python3", "verticals/generators/polymarket_whale_scanner.py"],
     "cadence": "weekday", "log": "verticals/generators/data/polymarket_whales.out",
     "asset_class": "event", "extractor": "generic", "enabled": True,
     "note": "attention-allocation ONLY until the pre-registered drift test passes (Form-4 NULL lesson); also accumulates the observation log the backtest needs"},
    {"name": "market_p_refresh", "cmd": ["python3", "-m", "desk.prediction_markets"],
     "cadence": "weekday", "log": "desk/data/market_p_refresh.out",
     "asset_class": "event", "extractor": "generic", "enabled": True,
     "note": "annotates OPEN frozen calls w/ live crowd odds (EXACT maps feed Brier-vs-market; RELATED = context only; threshold-mismatch trap guarded)"},
    {"name": "biotech_clearing", "cmd": ["python3", "verticals/generators/biotech_clearing_scanner.py"],
     "cadence": "weekday", "log": "verticals/generators/data/biotech_clearing.out",
     "asset_class": "equity", "extractor": "generic", "enabled": True,
     "note": "fresh Tang/Concentra/BML/Sarissa 13Ds = the cash-box clearing machine engaging; 3 forensic gates then same-week pipeline (latency edge; wide standing discounts are adversely selected)"},
    {"name": "tax_fit", "cmd": ["python3", "-m", "desk.tax_fit"],
     "cadence": "weekday", "log": "desk/data/tax_fit_cron.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "this-year deployment fit: 90d vol -> tax-option value (Dec-15 harvest window) + dated-catalyst notch; ranks the GO list. ALLOCATOR among DD-cleared names, never an entry justification."},
    {"name": "import_anomaly", "cmd": ["python3", "verticals/deep_value/import_anomaly_scanner.py"],
     "cadence": "weekly", "log": "verticals/deep_value/data/import_anomaly_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "INVERTED thesis generation (Stage 0b): whole-universe HS4 import acceleration/rollover anomalies (Census, ~5wk lag, monthly cache) -> thesis seeds for the SignalOS vehicle-mapping pass -> Stage 1 trap-screen. Built 2026-07-02."},
    {"name": "krx_value", "cmd": ["python3", "verticals/deep_value/krx_value_watch.py"],
     "cadence": "daily", "log": "verticals/deep_value/data/krx_value_cron.out",
     "asset_class": "equities", "extractor": "krx_value", "enabled": True,
     "note": "KRX-listed Korea book (COSMECCA/COSMAX/SILICON2/HUGEL) — band watch; alerts on accumulate-band touch; IBKR-tradeable on KRX if Korea-permission enabled, size <10-15% ADTV"},
    {"name": "stvn_book", "cmd": ["python3", "verticals/buyside_dd/outputs/peptides/stvn_watch.py"],
     "cadence": "weekday", "log": "desk/data/stvn_watch.out",
     "asset_class": "beauty", "extractor": "stvn_book", "enabled": True,
     "note": "aesthetics/wellness/cosmeceutical/K-beauty book — entry-band touches"},
    {"name": "beauty_virality", "cmd": ["python3", "verticals/buyside_dd/connectors/beauty_velocity_poll.py"],
     "cadence": "daily", "log": "verticals/buyside_dd/outputs/medspa/beauty_velocity_cron.out",
     "asset_class": "beauty", "extractor": "beauty_virality", "enabled": True,
     "note": "TikTok consumer-virality poll — NEW public-ticker brand vs yesterday"},
    {"name": "bond_scanner", "cmd": ["python3", "verticals/muni_credit/bond_scanner.py", "--max-new", "80"],
     "cadence": "weekly", "log": "desk/data/bond_scanner.out",
     "asset_class": "munis", "extractor": "generic", "enabled": False,
     "note": "incremental insulated-CA-muni finder (EMMA 403 rate-limit — weekly, disabled by default)", "dormant": "NO-MUNIS-2026 doctrine — intentionally paused; revisit 2027"},
    # ---- info-asymmetry detector scans over the book subset each APPLIES_TO (dispatch-index discipline) ----
    {"name": "det_litigation", "cmd": ["python3", "-m", "desk.detector_scan", "litigation"],
     "cadence": "weekly", "log": "desk/data/det_litigation.out",
     "asset_class": "cross", "extractor": "detector_scan", "enabled": True,
     "note": "federal-docket material-litigation screen over all public book names (CourtListener)"},
    {"name": "det_usaspending", "cmd": ["python3", "-m", "desk.detector_scan", "usaspending"],
     "cadence": "weekly", "log": "desk/data/det_usaspending.out",
     "asset_class": "equities", "extractor": "detector_scan", "enabled": True,
     "note": "federal award-flow drop over gov-revenue names (BAH/J/EPAM) — the contract-cut tell"},
    {"name": "det_hiring", "cmd": ["python3", "-m", "desk.detector_scan", "hiring_velocity"],
     "cadence": "weekly", "log": "desk/data/det_hiring.out",
     "asset_class": "equities", "extractor": "detector_scan", "enabled": True,
     "note": "job-posting capacity-ramp wave over capacity_ramp names (GCT/COSMECCA)"},
    {"name": "det_customer", "cmd": ["python3", "-m", "desk.detector_scan", "customer_id"],
     "cadence": "weekly", "log": "desk/data/det_customer.out",
     "asset_class": "equities", "extractor": "detector_scan", "enabled": True,
     "note": "customs-BOL undisclosed-customer tell over undisclosed_cust names (ELF/COSMECCA/COSMAX)"},
    {"name": "det_satellite", "cmd": ["python3", "-m", "desk.detector_scan", "satellite"],
     "cadence": "weekly", "log": "desk/data/det_satellite.out",
     "asset_class": "equities", "extractor": "detector_scan", "enabled": True,
     "note": "physical-asset (methane/oil/buildout) over physical_asset names (REPX/SD/COSMECCA) — AOI-gated"},
    {"name": "parametric_xclusion", "cmd": ["python3", "-m", "desk.parametric_xclusion"],
     "cadence": "weekly", "log": "desk/data/parametric_xclusion.out",
     "asset_class": "cross", "extractor": "detector_scan", "enabled": True,
     "note": "wash-sale drift guard: flags any IBKR book name that has crept into the Parametric SMA's ~314-name subset"},
    {"name": "harvest_goal", "cmd": ["python3", "-m", "desk.harvest_ledger"],
     "cadence": "weekday", "log": "desk/data/harvest_goal.out",
     "asset_class": "cross", "extractor": "detector_scan", "enabled": True,
     "note": "$2.4M harvest goal-tracker: realized vs projected vs goal; HIGH if behind pace (no silent cap)"},
    {"name": "catalyst_watch", "cmd": ["python3", "-m", "desk.catalyst_watch"],
     "cadence": "weekday", "log": "desk/data/catalyst_watch.out",
     "asset_class": "cross", "extractor": "detector_scan", "enabled": True,
     "note": "dated catalyst watchlist (KER Demna launch, INSP CPT panel, EOLS tariff, BAH/COSMECCA prints, harvest deadline) — surfaces as they approach"},
    {"name": "social_thesis", "cmd": ["python3", "verticals/social_thesis_engine/daily.py", "10"],
     "cadence": "daily", "log": "desk/data/social_thesis.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "social-feed vol/directional engine — SELL_VOL / DIRECTIONAL candidates + squeeze-fuel VETOes (needs TWS for the IV-richness step)"},
    {"name": "muni_universe", "cmd": ["python3", "verticals/muni_credit/refresh_universe.py", "--out", "bonds_priced_refreshed.json"],
     "cadence": "weekly", "log": "desk/data/muni_refresh.out",
     "asset_class": "munis", "extractor": "generic", "enabled": False,
     "note": "weekly insulated-CA-muni universe refresh (TWS-gated on 127.0.0.1:7496 — manual; daily scanner runs on the existing universe if TWS is down)", "dormant": "NO-MUNIS-2026 doctrine — intentionally paused; revisit 2027"},
    {"name": "convexity_watch", "cmd": ["python3", "-m", "desk.convexity_watch"],
     "cadence": "weekly", "log": "desk/data/convexity_watch.out",
     "note": "monitors the personal convexity bucket + watchlist for SEPTEMBER prep (PREPARE mode, not deploy — the incoming cash is the current convexity); tracks 52w position for accumulation + thesis-integrity"},
    {"name": "mft_page", "cmd": ["python3", "-m", "desk.mft_page"],
     "cadence": "hourly", "log": "desk/data/mft_page.out",
     "note": "renders the MFT sleeve dashboard (the MFT tab): calibration gauges + live frozen predictions + cohort + signal classes + the gate slaughterhouse"},
    {"name": "mft_forward", "cmd": ["python3", "-m", "desk.mft_forward"],
     "cadence": "weekly", "log": "desk/data/mft_forward.out",
     "note": "MFT prospective-calibration harness: reminds to FREEZE before cohort events (Layer-1 monthly nowcast + Layer-2 quarterly print/price), tracks the two Brier curves; PAPER until edge clears net of ST tax"},
    {"name": "gaming_monthlies", "cmd": ["python3", "-m", "desk.gaming_monthlies"],
     "cadence": "weekly", "log": "desk/data/gaming_monthlies.out",
     "note": "state gaming-commission monthly casino revenue BY PROPERTY -> regional casino smallcaps (FLL/MCRI/CNTY/GDEN); IL+IN parse per-property, CO/NV/MS detect+link; American Place = the FLL growth-asset nowcast"},
    {"name": "import_nowcast", "cmd": ["python3", "-m", "desk.import_nowcast"],
     "cadence": "weekly", "log": "desk/data/import_nowcast.out",
     "note": "Census monthly imports (HS x country, ~5wk lag) nowcasting import-driven smallcaps' prints; v1 = GCT furniture ex-China/Vietnam; extend per the exposure atlas"},
    {"name": "index_events", "cmd": ["python3", "-m", "desk.index_events"],
     "cadence": "daily", "log": "desk/data/index_events.out",
     "note": "the MFP class made recurring: S&P DJI add/delete announcements (~2-5d before effective) on small/mid caps -> triage -> event windows; slow-clock signal, fast-clock execution"},
    {"name": "spinoff_watch", "cmd": ["python3", "-m", "desk.spinoff_watch"],
     "cadence": "daily", "log": "desk/data/spinoff_watch.out",
     "note": "Form 10-12B spinco pipeline: new registrations notify; 3+ filings = LATE-STAGE (study before the orphan window — index forced selling in distribution weeks 1-6)"},
    {"name": "antiportfolio", "cmd": ["python3", "-m", "desk.antiportfolio"],
     "cadence": "weekly", "log": "desk/data/antiportfolio.out",
     "note": "the anti-portfolio: every DECLINE graded vs SPY from its verdict-day price (git-recovered baselines); the live out-of-sample test of the landmine-detector claim; regret listed first"},
    # DISABLED 2026-08-05 — launchd owns this schedule now (~/Library/LaunchAgents/
    # com.signalos.headless-grader.plist, StartInterval 7200). The grader shells out to `claude -p`,
    # whose credential lives in the macOS login Keychain; a crontab job runs outside the Aqua session
    # and cannot unlock it, so this entry returned "Not logged in" with exit 0 for 153 straight runs
    # and never graded anything. A LaunchAgent runs IN the GUI session and authenticates (verified).
    # Do NOT re-enable here without first moving the desk heartbeat itself off crontab.
    {"name": "headless_grader", "cmd": ["python3", "-m", "desk.headless_grader"],
     "cadence": "hourly", "log": "desk/data/headless_grader.out", "enabled": False,
     "note": "headless intelligent-read grader: for each DUE-open calibration call, runs `claude -p` (read-only WebFetch/WebSearch, neutral cwd) to read the PRIMARY print vs the exact gate and PROPOSE a grade -> pending_grades.json. NEVER resolves (confirmation stays a step; a mis-grade corrupts the scoreboard). Event-gated + deduped: claude fires ~once per landed print. Validated on BKE (+2.4% -> FAVORABLE)"},
    {"name": "print_radar", "cmd": ["python3", "-m", "desk.print_radar"],
     "cadence": "hourly", "log": "desk/data/print_radar.out", "enabled": True,
     "note": "event-aware sampling: hourly near a print (kicks the name's source watcher on print day, e.g. BKE->bke_monthly_comps) + the loop-not-closed alarm — any calibration call whose cat_date passed while still OPEN = a landed print that wasn't graded (the BKE gap). For an MFT 30-min action SLA, this should sample ~every 15m during a known print window (TODO)"},
    # print_radar --fast runs as a DIRECT */15 crontab line (like intraday_sentinel) — the registry
    # heartbeat only polls hourly, so a cadence:15 watch here would still only fire hourly. See crontab
    # `# signalos print-radar fast`. It self-gates to the ET comp print window (cheap no-op otherwise).
    {"name": "leading_indicators", "cmd": ["python3", "-m", "desk.leading_indicators", "--live"],
     "cadence": "weekly", "log": "desk/data/leading_indicators.out",
     "note": "MFT nowcast PIPELINE: encoded leading-indicator models (TSM/COST/SIA/TM/Macau) that GENERATE the calibration P from data instead of hand-reading it, and log pipeline-P vs the frozen hand-P. First batch (2026-07-10): mean|Δ|=0.078 vs hand; mechanical calls (TSM/COST/SIA) reproduced ±0.03, judgment calls diverged (TM +0.13 = missing comp-difficulty feature; MACAU-YoY -0.21 = human tail-anchoring, model better). --live best-effort refreshes cached inputs from the Mac IP (not cloud-blocked)"},
    {"name": "catalyst_action", "cmd": ["python3", "-m", "desk.catalyst_action", "--check"],
     "cadence": "hourly", "log": "desk/data/catalyst_action.out",
     "note": "CLOSES THE ACTION LOOP: a graded catalyst FIRES its pre-registered action (catalyst_action_registry.json) instead of just updating a Brier — the BKE gap (June comp graded FAVORABLE but the add-trigger sat in prose; we acted next-morning after a 2% pop). arm() is called instantly by calibration.resolve(); this --check nags any ARMED-but-unexecuted action past its SLA (MFT/INFO = 30m, latency-critical). anchor=pre_catalyst_close => a late action stands down rather than chasing the pop"},
    {"name": "lca_pyramid", "cmd": ["python3", "-m", "verticals.public_co.lca_pyramid", "auto"],
     "cadence": "weekly", "log": "verticals/public_co/data/lca_pyramid/lca_pyramid.out",
     "note": "DOL H-1B/LCA MARGIN/PYRAMID nowcast for large-cap IT-services (CTSH/ACN/TCS/INFY/IBM). USE: a MARGIN/utilization read (wage-level mix + median wage QoQ = pyramid flattening vs staying junior-heavy), routed to earnings review. DO NOT use LCA VOLUME as a demand/growth long-short discriminator — volume conflates cap-season timing + onshore/offshore mix + visa policy (screen 2026-07-09 DROPped the divergence thesis: INFY +79% vol was a cheap-petition cap-season flood w/ the LOWEST growth guide). Small books (EPAM/G/CNXC n<70) are NOISE. Playwright auto-fetch weekly"},
    {"name": "briefs_index", "cmd": ["python3", "-m", "desk.briefs_index"],
     "cadence": "weekly", "log": "desk/data/briefs_index.out",
     "note": "renders the in-app Briefs tab from briefs_manifest.json (DD / case studies / pitches served from the desk, off claude.ai)"},
    {"name": "household", "cmd": ["python3", "-m", "desk.household"],
     "cadence": "hourly", "log": "desk/data/household.out", "enabled": True,
     "note": "family-office command center: balance sheet as sleeve cards (target-vs-current + multi-factor beta), net-worth-weighted AGGREGATE beta, the beta matrix, + 3 agent lanes (SignalOS/Red-Blue/Disaster Planner). Data household.json; engine = officekit package (Phase-0 productization 2026-09-02). main() CHAINS the scenarios.html re-render (Scenario Planner, renamed 2026-09-02), so this one watch keeps BOTH the office and scenarios tabs fresh. Was registered without enabled:True from birth (2026-07-10) — the tabs sat frozen for 2 months; fixed 2026-09-02."},
    {"name": "strategy_book", "cmd": ["python3", "-m", "desk.strategy_book"],
     "cadence": "hourly", "log": "desk/data/strategy_book.out",
     "note": "renders strategy_book.html: the book by edge source — executed vs tracked-not-executed (the IVN catalyst record) + per-class calibration, all dated"},
    {"name": "thesis_index", "cmd": ["python3", "-m", "desk.thesis_index"],
     "cadence": "hourly", "log": "desk/data/thesis_index.out",
     "note": "renders thesis_index.html (the 'theses' tab): the WHOLE corpus — every ledger sleeve (GLP-1/K-beauty/EM-banks/deep-value/muni/…) + edge-class buckets for un-sleeved names, each name's verdict + one-line thesis, every ticker -> its dossier. Also regenerated by ledger_add.upsert() on any thesis change"},
    {"name": "consumer_heat", "cmd": ["python3", "-m", "desk.consumer_heat", "--refresh"],
     "cadence": "daily", "log": "desk/data/consumer_heat.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "CONSUMER PRODUCTS LANE (built 2026-08-15 on the principal's 'trending heatmap + reviews' "
             "directive): runs consumer_product_heat (Google Trends 28d-vs-90d acceleration + Reddit "
             "velocity + Amazon best-seller rank proxy) then consumer_product_reviews (Walmart review "
             "velocity + recent-cohort-vs-lifetime rating delta), then renders consumer_heat.html. "
             "DEGRADED-LOUD by design — Amazon/Target/Trustpilot are bot-walled from this egress and "
             "say so in the output rather than scoring zero; the rating delta needs 2 snapshots >=3d "
             "apart, so early rows read BASELINE_ONLY. RATE BUDGET: Google Trends ~6 req/min and hard-"
             "429s if hammered, r.jina.ai ~5-8s/page — one bounded daily pass over ~13 tracked brands "
             "(~8-10 min). Do NOT raise the cadence; add brands to connectors' TRACKED instead."},
    {"name": "adjudication_mailer", "cmd": ["python3", "-m", "desk.adjudication_mailer"],
     "cadence": "hourly", "log": "desk/data/adjudication_mailer.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "EVERY VERDICT REACHES THE INBOX, EXACTLY ONCE (built 2026-08-18 on the principal's "
             "'these courts not emailing their results?'). They were not: the conveyor wrote "
             "edge_classifications, upserted the ledger and re-rendered the dashboard, then "
             "STOPPED — notification happened only if a human called build_deck. Audit that "
             "prompted it: 25 adjudications on 08-17/18, 8 decks emailed, ZERO emails on 08-18. "
             "That is 'did we actually' in pure form — the pipeline completed and nothing acted, "
             "which is worse than an unreached verdict because the desk believes the work is done. "
             "Digest groups by disposition, leads with any verdict on a name WE HOLD, and gives "
             "verdict + one reason + armed gate per name. Sent-log is keyed ticker|date so re-runs "
             "never duplicate and a RE-ADJUDICATION correctly sends again (MFIC was vacated and "
             "re-courted the same day — both are notifiable)."},
    {"name": "resort_snowpack", "cmd": ["python3", "-m",
     "verticals.buyside_dd.connectors.resort_snowpack"],
     "cadence": "weekly", "log": "desk/data/resort_snowpack.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "THE LAG IS THE POINT (built 2026-08-18 for the MTN court): ski operators sell season "
             "passes in SPRING for the FOLLOWING winter, so the pass-sales number reported in "
             "autumn is conditioned by the snow customers JUST experienced — making last season's "
             "peak snow-water-equivalent a LEADING read on next season's pre-sold revenue. Free "
             "daily USDA NRCS SNOTEL data (no key) at stations sited ON the resorts. Baseline "
             "WY2026: ~55% of median across Vail/Copper/Fremont/Tahoe — severely below normal. "
             "Uses WTEQ not snow DEPTH (water equivalent is the conserved quantity). Honest limit "
             "encoded: snowpack conditions DEMAND and the NEXT pass cycle, not the sold year's "
             "pass revenue, which Vail's model deliberately insulates from weather."},
    {"name": "connector_smoke", "cmd": ["python3", "-m", "desk.connector_smoke"],
     "cadence": "daily", "log": "desk/data/connector_smoke.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "CONTRACT TEST for every KG-dispatched connector (built 2026-08-18). Calls query() "
             "on each and asserts it does not EXCEPT; success=False is a PASS because the contract "
             "held. Exists because two connectors built in one day ran fine from their CLI, were "
             "declared tested, were KG-registered, and both crashed the instant anything dispatched "
             "them (_ok signature). That state is worse than a missing connector: the graph "
             "advertises it, a bench calls it, the call dies, and the bench records a COVERAGE GAP "
             "— infra failure wearing the costume of an analytic absence (the LIND blue bench "
             "caught exactly this). First run found 3 MORE pre-existing breaks: fema_nri_hazard, "
             "laserfiche_weblink and litigation_screen all referenced a non-existent "
             "ErrorKind.BAD_REQUEST — and litigation_screen had been cited as a coverage gap in "
             "the JBGS court while actually crashing. No network by default (seconds)."},
    {"name": "expedition_inventory", "cmd": ["python3", "-m",
     "verticals.buyside_dd.connectors.expedition_inventory"],
     "cadence": "weekly", "log": "desk/data/expedition_inventory.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "FORWARD-BOOKING TELEMETRY for expedition operators (built 2026-08-17 for the LIND "
             "court). Expedition cruises book 2-4 QUARTERS AHEAD, so the operator's own booking "
             "payload knows the season long before the income statement reports it. Reads "
             "Lindblad's Next.js __NEXT_DATA__ (Algolia itinerary index, no API key): per "
             "itinerary isSoldOut, nrDepartures, full vs discounted price, promo labels, ships. "
             "Baseline 2026-08-17: 72 itineraries / 1,986 departures, 59.6% sold out "
             "departure-weighted, and ZERO fare cuts anywhere — the only promotion in the whole "
             "book is '50% Reduced Deposit', i.e. a TERMS concession that preserves revenue per "
             "berth while shifting float and cancellation risk to the operator. THE DELTA IS THE "
             "SIGNAL: a single snapshot's levels are non-discriminating (promo flag fires on 92%). "
             "Weekly is right — booking curves move over weeks, and it is ~10 page fetches."},
    {"name": "print_collision", "cmd": ["python3", "-m", "desk.print_collision"],
     "cadence": "daily", "log": "desk/data/print_collision.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "RESTING-BUY x EARNINGS-GAP TRIPWIRE (built 2026-08-17 off the INTU catch). The "
             "bands-rest-by-default contract already DATES every order and orders_calendar flags "
             "undated ones — INTU passed both (it had INTU-REVIEW|08-18 saying 'pull 08-18') and "
             "still sat 20@312 into an 08-20 print until a human looked. A calendar reminder is "
             "not a tripwire. This measures each resting BUY's distance below spot in units of "
             "the PRINT'S OWN implied move and flags anything inside ~2 sigma: such a limit fills "
             "ONLY on the adverse branch (accidental short vol — NATR filled 6h pre-print, -17.6%). "
             "Pack dates OUTRANK vendor dates (disagreement carried into the flag, never hidden); "
             "vol is realized-30d = CONSERVATIVE by construction (under-flags into a bid-IV print). "
             "CRITICAL <=3 sessions, WARN <=10; emails on any flag; unresolved symbols always named."},
    {"name": "app_review_velocity", "cmd": ["python3", "-m",
     "verticals.buyside_dd.connectors.app_review_velocity", "--run-tracked"],
     "cadence": "daily", "log": "desk/data/app_review_velocity.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "APP-DISTRIBUTED CONSUMER LANE (built 2026-08-16 on the principal's 'app store review "
             "velocity tool' directive): daily snapshot pass over TRACKED app issuers (IBKR/RDDT/"
             "HOOD/SOFI/LMND/ETOR) — App Store RSS dated velocity + lookup lifetime counts + Play "
             "aggregates — so EXACT cohort deltas (R1N1−R0N0 arithmetic) exist by the time a court "
             "asks. Dispatch-indexed in the KG (issuer_features consumer_app/dau_mau_marketed/... "
             "+ SIC 737/6199/6211/63xx) for on-demand per-name calls at DD time. POPULATION "
             "WARNING lives in the connector: written-review cohorts are structurally angrier than "
             "prompted-rating lifetime means — never read visible-vs-lifetime as deterioration; "
             "velocity trend, cohort-vs-own-history, and the exact delta are the valid reads. "
             "MAUDE lesson encoded: spikes near version releases are prompt artifacts; collapses "
             "are the cleaner signal. ~18 HTTP calls/day total, trivially inside rate budgets."},
    {"name": "edge_classes", "cmd": ["python3", "-m", "desk.edge_classes"],
     "cadence": "weekly", "log": "desk/data/edge_classes.out",
     "note": "edge-SOURCE taxonomy (FLOW/INFO/VALUE/CARRY/CONVEXITY/EXCLUSION): backfills edge_source into the ledger + prints the per-class calibration scoreboard so grading stays WITHIN class (a FLOW win never pads the INFO/MFT forward test); surfaces UNCLASSIFIED for review"},
    {"name": "parametric_sync", "cmd": ["python3", "-m", "desk.parametric_sync"],
     "cadence": "daily", "log": "desk/data/parametric_sync.out",
     "note": "auto-ingests the newest ~/Downloads Parametric bundle -> holdings + the harvest-health scorecard (surface, embedded, ossification clock, our-book overlap); the household core finally has telemetry"},
    {"name": "sleeve_benchmark", "cmd": ["python3", "-m", "desk.sleeve_benchmark"],
     "cadence": "weekly", "log": "desk/data/sleeve_benchmark.out",
     "note": "the OFFICE THESIS's P&L referee: IBKR sleeve vs dump-it-in-Parametric (SPY-TR on the same flow dates + measured harvest alpha - fees); sleeve_nav.json refreshed on desk polls; flows extended on new wires"},
    {"name": "memory_lint", "cmd": ["python3", "-m", "desk.memory_lint"],
     "cadence": "weekly", "log": "desk/data/memory_lint.out",
     "note": "the memory-rot detector: ranks all memories by perishability x age -> the weekly top-5 re-verification ritual (fix or re-date; a 're-verified: YYYY-MM-DD' stamp resets the clock)"},
    {"name": "gauntlet_book", "cmd": ["python3", "-m", "desk.gauntlet_book"],
     "cadence": "hourly", "log": "desk/data/gauntlet_book.out",
     "note": "the one-place gauntlet + Brier-book review UX (GAUNTLET tab): every frozen call joined to its pack/grader, stake, plain meaning, and grade"},
    {"name": "diagnostics", "cmd": ["python3", "-m", "desk.diagnostics"],
     "cadence": "hourly", "log": "desk/data/diagnostics.out",
     "note": "the self-interrogation page (STANDING GOAL 2026-07-07): grades every subsystem green/yellow/red -> diag.html (the DIAG tab); the morning pass reviews it; anything RED gets interrogated + fixed"},
    {"name": "news_scan", "cmd": ["python3", "-m", "desk.news_scan"],
     "cadence": "hourly", "log": "desk/data/news_scan.out",
     "note": "news/data thesis raw-material collector (EDGAR 8-K material items + GDELT theme spikes -> news_candidates.jsonl); triage = the 4 edge patterns then tape-verify -> conditioning -> courts; OFFICE-THESIS RULE (2026-07-07): microcap 8-K hits are THE POND, not noise — a material 8-K on a sub-$2bn name nobody covers is precisely the un-screened paper the office exists for; triage them by materiality-per-market-cap, never by name recognition"},
    {"name": "catalyst_mispricing", "cmd": ["python3", "-m", "desk.catalyst_mispricing"],
     "cadence": "weekday", "log": "desk/data/catalyst_mispricing.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "portfolio-wide catalyst-mispricing scanner — ranks every 3-scenario name by OUR p(base) vs market-implied p (edge_pp) + upside%; FIREs an ENTRY when edge>=+15pp AND price in the buy band on a non-trap; feeds CATALYST_MISPRICING.md"},
    {"name": "calibration", "cmd": ["python3", "-m", "desk.calibration"],
     "cadence": "weekday", "log": "desk/data/calibration.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "THE CALIBRATION EXPERIMENT — freezes every dated probability call (pre-registration), FLAGs RESOLVE-NEEDED when a catalyst passes, scores Brier(ours) vs Brier(market) + conviction-inversion; the gate: edge_pp sizes positions ONLY once ours beats market"},
    {"name": "antibook_perf", "cmd": ["python3", "-m", "desk.antibook_performance"],
     "cadence": "weekday", "log": "desk/data/antibook_perf.out",
     "asset_class": "cross", "extractor": "generic", "enabled": True,
     "note": "anti-book CALL performance — tracks whether our non-owned watch/catalyst predictions work (hit-rate + signed return + vs SPY) from a baseline"},
    {"name": "quality_wishlist", "cmd": ["python3", "verticals/generators/quality_wishlist.py"],
     "cadence": "daily", "log": "verticals/generators/data/quality_wishlist_cron.out",
     "asset_class": "equities", "extractor": "detector_scan", "enabled": True,
     # RATE BUDGET. Watch mode prices ~75 names + SPY in two batched yfinance calls off a 10y
     # weekly bar (weekly bars are ~1/5 the payload of daily) and makes no SEC calls in steady
     # state — fundamentals come from the cache the weekly refresh maintains, and companyfacts is
     # only reached for to self-heal a name missing from it. Negligible against the
     # sweeps. DAILY not weekday because a band crossing is not a session event: it is a level,
     # and a level does not expire over a weekend.
     "note": "the QUALITY WISHLIST (2026-08-13, QUALITY_WISHLIST_DESIGN.md approved same day; principal rulings A=hybrid seeding, B=two-band, C=manual Parametric list, D=8% aggregate sleeve cap). THE GAP: every other instrument the desk owns is drawdown-triggered — dislocation_sweep, us_broad_dislocation_sweep, cohort_dislocation, broken_print_radar and class_dislocation ALL require something to FALL. The fourth failure class from the SPGI postmortem is the quality name that gets cheap WITHOUT falling, by standing still while earnings grow, and no drawdown screen can express the TINA doctrine ('for quality, fair value IS the entry'). This is a different instrument: a shopping list with prices, not a dislocation detector. TWO MODES, and the split is load-bearing. --screen runs a mechanical five-part quality gate over ten years of audited XBRL companyfacts across the S&P 500 plus broken_print_radar's own cap-ladder US universe (its builder REUSED, not duplicated), excluding financials by SIC (6000-6499, 6700-6799 — ROE is peak-cycle-masked and the financials-screen vertical already owns them) and every name already in the research ledger, and writes the FULL candidate list plus a plain-language cull sheet to desk/reports/. WATCH MODE (this registry entry, the default) reads ONLY verticals/generators/data/quality_wishlist_active.json — the POST-CULL list. Until the principal culls the mechanical candidates to ~75 and saves that file the wishlist is INACTIVE: it degrades LOUD, fires nothing, and exits clean. That is not a bug or a rate-limit; an unculled mechanical list firing its own output is the generator grading itself, which is the invariant this whole pipeline is built on. THE GATE (over 10 fiscal years): ROIC>15% in >=8 years, revenue up in >=8 years (durability, NOT velocity — no growth-rate minimum anywhere, per the GARP lesson that trailing growth screens are fragile), gross margin stable-or-rising (10yr slope >=0 or latest within 300bps of the median), net debt/EBITDA<2.0 (the unlevered-tails carry precondition), diluted share count flat-or-shrinking across the decade (owner-alignment; kills serial diluters and roll-ups whose EPS is acquisition-stepped). No valuation input appears in the gate at all — that is the band's job. ROIC is an APPROXIMATION and the module says so in its docstring: NOPAT (operating income x effective tax rate clamped 10-35%) over book equity plus net debt, leases NOT capitalised (so lease-heavy retailers read high), goodwill left IN (an acquisitive compounder is charged for what it paid), and negative invested capital reported ROIC_UNBOUNDED rather than infinite-good. A name with fewer than 8 usable filing years is DEGRADED-INSUFFICIENT-HISTORY — never silently passed, never silently failed, listed in its own section of the cull sheet. THE BANDS are OWN-HISTORY 10yr weekly percentiles on EV/EBIT and P/E, never cross-sectional (the ADR-P/B and conservative-FV lessons both say peer anchors mislead), combined as the MAX of the two so a name reads cheap only when BOTH multiples do. FAIR (<=own median) proposes a tranche-1 — the TINA doctrine mechanized; CHEAP (<=own p20) proposes a starter; STANDSTILL fires at ANY level when the percentile fell >=25 points in 12 months while trailing EPS rose, which is the SPGI shape and the reason this module exists. FOUR TRAP GUARDS from the desk's own loss catalog, each with an offline test: peak-earnings (latest operating margin above own p90 = denominator-flattered -> REVIEW, court must normalize), crash-cheapness (a live dislocation/broken-print hit is the DISLOCATION pipeline's case — routed to cause-check and deliberately NOT enqueued to court from here), acquisition step-up (share count or goodwill +>10% in a year -> P/E percentile suppressed, EV/EBIT only), and value-trap decay (>12 months in the CHEAP band with no court ACCEPT -> mandatory re-gate, printed every run because the reference distribution itself decays as cheap years enter the lookback). WASH-SALE: any fire on a name in desk/data/parametric_holdings.txt (MANUALLY maintained — the household's Parametric direct-indexing account is not machine-readable to the desk; GOOGL is the one known entry) carries WASH-SALE-CHECK, because buying at IBKR while Parametric harvests the same name is exactly the cross-account interaction the household map warns about. A flag, not a block: skipping those names would surrender the best compounders. LAZY COURT: nothing is courted until it actually gets cheap, at which point the fire enqueues at TRAP_VERIFY so the quality claims are verified before any red or blue bench. PROPOSES ONLY — no band-fire ever places or sizes an order; sleeve metadata carries the 8% aggregate cap for downstream sizing and this module does not enforce it (it does not know the book). Every fire is logged to the PRE-REGISTERED QUALITY_WISHLIST_FIRES.json with the name's and SPY's price on the fire date and 90/180/365-day horizons, so the FAIR-vs-CHEAP comparison accrues as the empirical TINA test — N>=20 graded fires per band before any claim in either direction, per the within-rating-band market-timing lesson. Tests: tests/test_quality_wishlist.py."},
    {"name": "quality_wishlist_refresh",
     "cmd": ["python3", "verticals/generators/quality_wishlist.py", "--refresh-fundamentals"],
     "cadence": "weekly", "log": "verticals/generators/data/quality_wishlist_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "weekly XBRL refresh behind the quality wishlist (§8 cadence). Re-pulls companyfacts for the active list (or, before activation, for the mechanical candidates) and re-derives the ten-year annual records the band engine interpolates. Separate from the daily watch on purpose: the daily leg must stay a pure price-vs-band check with zero SEC calls, and fundamentals that go stale must be VISIBLE — the watch prints a DEGRADED-LOUD line naming every name whose cached fundamentals are older than 10 days, so a dead refresh cron shows up as a named staleness list rather than as quietly wrong percentiles. Failures are named, and the affected names are reported as watching on STALE fundamentals rather than dropped."},
    {"name": "quality_wishlist_grade",
     "cmd": ["python3", "verticals/generators/quality_wishlist.py", "--grade"],
     "cadence": "weekly", "log": "verticals/generators/data/quality_wishlist_cron.out",
     "asset_class": "equities", "extractor": "generic", "enabled": True,
     "note": "fills the SPY-same-window counterfactual on quality-wishlist fires whose 90/180/365-day horizons have come due, and prints the running FAIR-vs-CHEAP excess split with an explicit BELOW-THE-N>=20-GATE label until each band has twenty graded fires. Generator-never-grades-itself: this pass only records outcomes into the pre-registered log — it cannot change a band, a fire or a verdict. A missing SPY series ABORTS the grade rather than recording a one-sided return."},
]

CADENCE_MIN = {"hourly": 60, "weekday": 24 * 60, "daily": 24 * 60, "weekly": 7 * 24 * 60}


def _cadence_minutes(c) -> int:
    return int(c) if isinstance(c, int) else CADENCE_MIN.get(c, 24 * 60)


def _load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except Exception:
            return {}
    return {}


def _save_state(s: dict):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1))


def due(now: float | None = None, force: bool = False) -> list[dict]:
    """Watches whose cadence has elapsed since last run (weekday watches skip Sat/Sun)."""
    import datetime
    now = now or time.time()
    st = _load_state()
    out = []
    for w in WATCHES:
        if not w.get("enabled"):
            continue
        if w["cadence"] == "weekday" and datetime.datetime.fromtimestamp(now).weekday() >= 5:
            continue
        last = st.get(w["name"], 0)
        if force or (now - last) >= _cadence_minutes(w["cadence"]) * 60 - 60:  # 1-min grace
            out.append(w)
    return out


def mark_ran(name: str, now: float | None = None):
    st = _load_state()
    st[name] = now or time.time()
    _save_state(st)
