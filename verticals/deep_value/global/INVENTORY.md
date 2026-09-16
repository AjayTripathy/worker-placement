# Global value screen — market feasibility inventory
*(2026-07-20 — the ranking that decided build order; Japan first)*

Ranked by (free machine-readable fundamentals) x (executable at IBKR) x (cheapness on offer).

## 1. JAPAN — BUILD (this directory)
- **Fundamentals**: EDINET (the FSA's EDGAR), free. API v2 at `api.edinet-fsa.go.jp/api/v2/` —
  `documents.json?date=` lists every filing per submission date; each filing is a ZIP of iXBRL
  under the JPPFS (JP-GAAP) or IFRS taxonomy. ~4,000 listed filers (code list says 3,829 with a
  securities code). No frames-style cross-section endpoint — the crawl is date-by-date over the
  annual-report season (有価証券報告書, form 030000; March fiscal-year-ends file mid/late June),
  concepts extracted once into a local store (`data/edinet_store.json`), screen runs off the store.
- **API key**: v2 requires a free subscription key (Azure AD B2C signup, email-verification code).
  Signup: `https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1` → 今すぐサインアップ → email +
  image CAPTCHA → 確認コードを送信 (code lands in the inbox) → コードの確認 → set password → 作成.
  The key then shows on the api.edinet-fsa.go.jp account page. Store it in env `EDINET_API_KEY` or
  `global/data/edinet_key.txt`. **2026-07-20 status**: signup automated to the code-entry step, but
  the Gmail MCP token had expired mid-flow, so the emailed code was unreachable — key NOT yet held.
- **No-key fallback (what the first RUN used — VALIDATED 2026-07-20)**: the public viewer
  `disclosure2.edinet-fsa.go.jp` serves the SAME search + per-filing XBRL/CSV ZIP downloads with
  no login — but downloads are session-bound GeneXus postbacks (encrypted per-session doc tokens),
  so it needs a real browser. `edinet_browser_crawl.py` (Playwright, headless) drives 書類詳細検索
  date-by-date into the same cache the API client fills; the extractor + screen are
  source-agnostic. Gotchas encoded in the module: checkbox/radio inputs are hidden behind styled
  labels (click via DOM), the 書類種別 grid re-renders on the radio ajax (racing it silently
  desyncs server-side filter state -> "no records"), download handlers live in `href` not
  `onclick`. The API path is preferred once a key exists (documented, resumable, lighter on FSA).
- **Static no-auth extras**: `disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip`
  = the full EDINET-code → securities-code/name/industry/FY-end map (this is our universe file).
- **Prices/mcap**: JPX monthly English listed-company file, or yfinance `.T` per name (batched,
  cached aggressively — yfinance rate-limits; stale prices are flagged, not hidden).
- **Executable**: TSEJ at IBKR, 100-share board lots.
- **Cheapness**: ~27% of Prime below book (Feb-2026); TSE "management conscious of capital cost"
  improvement-plan regime is a live forcing function on the sub-book cohort.
- **PFIC-density WARNING**: the Japan value shelf is cash-heavy — a large minority of net-nets fail
  the PFIC asset test (passive assets >= 50%). Screen carries a PFIC column (pfic_screen.py proxy),
  it never silently excludes: for a taxable US holder the §1291 regime is the landmine, and some
  names are fine via the look-through once tax counsel reads them.

- **First RUN (2026-07-20)**: crawled the June-2026 有報 season via the browser transport —
  submission dates 06-23/24, 06-25/26, 06-29/30 = **1,525 filings extracted (0 unparseable)**
  into `data/edinet_store.json`; universe join = 1,241 listed ex-financials; **968 scored**;
  shortlist 911 after guards, **PFIC-flagged 14%** (30/120 on the saved shortlist file — the
  cash-heavy top of the shelf runs hotter, as predicted). Trap caught during validation:
  post-FYE stock splits (NIHON SEIKO 1:4 on 2026-04-01) — mcap must use the
  as-of-FILING-DATE share count, not fiscal-year-end (encoded in the extractor).

## 2. KOREA — BUILT 2026-07-21 (dart_fundamentals.py + screen_korea.py)
- **Fundamentals**: DART/OpenDART (the FSS's EDGAR). TWO transports, same store
  (`data/dart_store.json`, keyed by 6-digit stock code):
  - **BULK no-auth route (VALIDATED — the first RUN used this)**: OpenDART's
    재무정보 일괄다운로드 serves per-period ZIPs of EVERY periodic filer's XBRL facts as cp949
    TSVs with NO API key: `POST /disclosureinfo/fnltt/dwld/list.do` lists the files (names
    carry a generation timestamp — re-scrape, never hardcode), then
    `GET /cmm/downloadFnlttZip.do?fl_nm=<file>.zip`. One FY set (BS/PL/CF ≈ 18MB) covers the
    whole market — strictly better than 2,500 keyed per-company calls. Banks/insurers/
    securities/other-financial file in SEPARATE members (은행/보험/증권/금융기타), so the
    financials carve-out = don't parse those members. Gotchas encoded in the module: interim
    files head the value column 당기 1분기말/누적 (not bare 당기 — prefer 누적 for flows);
    비유동자산 CONTAINS the substring 유동자산 (Korean-name fallback must guard the prefix);
    values are FULL KRW (Samsung Assets = 566,942,110,000,000 ✓).
  - **Keyed API** (`corpCode.xml` registry + `fnlttSinglAcntAll.json` per company, reprt
    11011/11012/11013/11014, fs_div CFS→OFS): implemented, UNTESTED pending the key.
    **Signup state 2026-07-21**: account CREATED fully headlessly (no CAPTCHA —
    `POST /uss/umt/EgovIdDplctCnfirmAjax.do` email dup-check, then multipart
    `POST /uss/umt/EgovMberInsert.do`; login 4tripathy@gmail.com works but blocks on
    "이메일 인증이 완료되지 않은 사용자" — the verification link is sitting in Gmail and the
    Gmail MCP token was expired (the EDINET failure mode, again). REMAINING STEPS: (1) re-auth
    Gmail MCP, (2) click the 이메일 인증 link in the DART mail, (3) log in at opendart.fss.or.kr
    → 인증키 신청/관리 → copy the 40-char key into `global/data/dart_key.txt` (or env
    DART_API_KEY). Credentials: `global/data/dart_login.txt` (resettable via 이메일/비밀번호재발급).
- **K-IFRS structural note**: 기업회계기준서 제1001호 REQUIRES 영업이익 = 수익-매출원가-판관비,
  so one-time gains sit below EBIT by construction (JP-GAAP-like; OneTimeGain ≡ 0).
- **Prices/mcap**: Yahoo v7 bulk quote via yfinance's authed session (YfData — crumb handled):
  marketCap/price/regularMarketTime for ~200 symbols per request; .KS/.KQ quotes verified
  same-day 2026-07-21 (the "yfinance Korea lags days" warning applies to the chart feed —
  the quote endpoint ran fresh, but staleness is judged per-name on the quote's OWN timestamp).
  Yahoo marketCap = COMMON shares only → issuers with listed prefs understate EV (pref column
  flags them; probe = base5+5/7/9 codes). data.krx.co.kr JSON/OTP endpoints reject headless
  clients ("LOGOUT") — don't burn time there.
- **Value-up catalyst join**: KIND value-up disclosure list, no auth:
  `POST kind.krx.co.kr/valueup/disclsstat.do` (method=valueupDisclsStatSub,
  currentPageSize=5000) → 1,065 disclosures / 752 issuers (746 PLAN, 6 NOTICE) as of
  2026-07-21; KIND exposes the 5-digit issuer code → code6 = code5+"0" (commons end in 0).
  Hyundai/LG/SK/Kia/한미반도체 spot-checked correct.
- **Executable**: KRX at IBKR with LIVE two-sided quotes (krx_value_watch.py corrected
  2026-06-29); KRW, single shares (no board lots); Korea permission + thin foreign-flow
  liquidity caveats. Dividends: 22% WHT (15.4% w/ US treaty W-8BEN).
- **Cheapness**: ~60% of KOSPI below book — the shelf is HUGE; the composite must RANK, not
  threshold. Below-book + NO value-up filing + controller >40% (manual DD) = the Japan
  no-actor law's Korea analog: likely perpetual discount.
- **First RUN (2026-07-21, FY2025 annual bulk gen 2026-07-16 + 2026-1Q interim)**: store
  2,661 filers (2,120 consolidated; interim BS attached for 2,583); universe 2,489 listed
  ex-financials/ex-SPAC (65 SPACs 기업인수목적/스팩 + 12 financial-KSIC dropped; KSIC 649
  non-bank holdcos LG/SK KEPT + flagged); **1,761 priced + in-band (₩40B–₩5T)**; shortlist
  1,332 after guards; **PFIC-flagged 24%** (318/1,332; FMV-basis overlay wired from day one);
  value-up filers on shortlist 502, below-book+PLAN in the saved top-120 = 40 (the catalyst
  cohort). Saved: `data/korea_shortlist.json` (top 120).
- **PFIC map hardening (same day, Stage-2 DD catch on 079960 Dongyang E&P)**: the first map
  captured cash + 단기금융상품 but MISSED the noncurrent investment categories — 079960 held
  ₩97bn of 장기투자증권 under `ifrs-full_EquityInstrumentsHeld` and printed fmv_share 0.46 on
  a true ~1.2. Fixed: all K-IFRS measurement categories mapped (FVOCI/FVTPL/amortised-cost/
  EquityInstrumentsHeld + the Other[Non]currentFinancialAssets umbrellas as a PFIC-ONLY
  over-capture bucket in OtherLongTermInvestments — netcash stays narrow), plus a Korean-label
  contains-tier restricted to 재무상태표 rows (the CF statement carries same-named FLOW rows —
  취득/처분 of FVTPL assets — that must never sum into a balance; caught in validation when
  079960's LT bucket printed ₩132.9bn vs the ₩97.3bn actually on its BS). PFIC rate 13% →
  **24%** (318/1,332); 24 of the saved top-120 flipped, incl. batch-1 VU-PLAN cohort flips
  인크로스 0.24→1.20, 신세계I&C 0.42→0.77, 흥국 0.36→0.56, 유아이엘 0.42→0.51
  (F&F홀딩스 0.41 / 에스넷 0.46 / 동방아그로 0.32 stay below the 0.5 line).

## 3. EUROPE — ESEF — BUILT (2026-07-21: esef_fundamentals.py + screen_europe.py)
ESEF iXBRL (IFRS taxonomy) is mandated across the EEA; one adapter covers GB + Nordics + PL.
- **Fundamentals**: filings.xbrl.org — FREE, no auth. JSON:API index `/api/filings`
  (filter[country], page[size]<=250, include=entity -> LEI + name) + per-filing pre-extracted
  xBRL-JSON facts ("json_url") — no iXBRL parsing needed. Cached to `data/esef_cache/`
  (index per country, gzipped facts per filing), MERGEd into `data/esef_store.json`.
- **FEED LAG is the gotcha (measured 2026-07-21)**: GB/DK/FI are current (FY2025/26 present);
  **SE + NO stop at FY2024, PL at FY2023** (nothing date_added since ~2024/2025); **IE = 0
  filings** (Euronext Dublin OAM not aggregated). The adapter auto-derives each country's
  vintage window from its own max period_end and the screen flags fiscal staleness (FY24!/FY23!)
  rather than pretending freshness. For SE/NO/PL freshness the national OAMs would be the fix.
- **ESEF structural limits**: primary statements only (share counts tagged in only ~2% of
  filings -> mcap leans on Yahoo shares, basis logged); entity extensions eat the operating-
  profit tag on ~19% of GB filings (EBIT falls back to PBT+net-finance, flagged `ebit~`,
  never guessed from extension namespaces); annual cadence only.
- **Prices/mcap**: yfinance fast_info per name (cached, staleness-stamped). **LSE quotes in
  PENCE (GBp) — Yahoo's own market_cap for .L is pence too**; the /100 happens exactly once
  in `_to_filing_ccy()` + a GB median-P/B plane check before anything prints (POLI.TA lesson).
  Ticker resolution = Yahoo search on the entity NAME with region hints (US-region queries
  bury the home line — Experian) + home-exchange gate + similarity bar; ambiguity -> UNRESOLVED.
- **Executable at IBKR**: LSE / WSE / SFB / HEX / CPH / OSE. GB = 0% WHT (the sweet spot)
  + 0.5% stamp on buys; Nordics WHT 25-35% treaty-reclaimable with friction; PL 19%.
- **The prize**: sub-$500M GB main-market names (post-MiFID-II research desert) — flagged
  `orphan` in the output. AIM is NOT ESEF-mandated: GB coverage = main market, logged.

- **First RUN (2026-07-21)**: indexed 9,424 filings across GB/PL/SE/FI/DK/NO; latest-annual
  vintage = **1,708 entities, 1,704 extracted (99.8%)** into `data/esef_store.json`.
  EBIT std-tag loss by country: GB 18.7% / DK 15.8% / NO 11.9% / SE 9.6% / FI 8.1% / PL 1.9%
  (recovered via flagged PBT+net-finance derivation except 37 true absents). DK quirk
  encoded: 52 filings tag the whole report on ConsolidatedAndSeparateFinancialStatementsAxis
  (separate-only accounts -> `solo` flag). After the full resolver pass: **539 scored /
  496 shortlisted** (GB 238, SE 87, FI 80, NO 78, DK 39, PL 17), PFIC-flagged 14,
  GB orphans 55. The OUTPUT-side validator caught filer errors the screen would have
  shipped: HSW.L (every fact 10x mis-scaled) and SCHO.CO (DKK amounts tagged
  iso4217:EUR = the 7.45x EUR/DKK cross) -> `scale_suspect`, demoted from print, kept
  flagged in the JSON. Saved: `data/europe_shortlist.json` ({meta, rows[150]}, every
  row carries its filing URL).
- **Trust/client-cash guard (same day, the OTB.L Stage-2 catch)**: customer-float models
  (travel/OTA, betting/gaming, airlines, ticketing, payments, insurance brokers, estate
  agents) report ring-fenced customer cash on the balance-sheet face and ESEF notes are
  untagged, so netting it manufactures phantom EV (OTB: GBP72m printed vs ~GBP282m honest;
  6.9x vs true ~9-14x EV/EBIT). Guard: `trust_cash_suspect` flag (Yahoo-industry + name
  keywords), and flagged names feed the composite the TRUST-SAFE variant (EV without cash
  netting, netcash floored at 0; `am_asis` keeps the raw number). First run: 15 flagged
  (OTB #15->#43, Betsson #4->#17, Hostelworld #27->#37; none crossed OUT of the top-50 —
  the survivors hold on mcap-clean metrics). OTB validated: am_trustsafe 10.9x on filed
  FY25 EBIT GBP22.9m, inside the 9.4-14x honesty band.

## KILLED
- **India**: no free machine-readable fundamentals access (MCA/BSE gated, XBRL not public at scale).
- **Hong Kong**: HKEX filings are PDF-only — no XBRL, extraction cost kills it.

## Paid tier (Stage-3 only)
EODHD (~EUR100/mo) covers global fundamentals JSON — acceptable as a UNIVERSE GENERATOR
(candidate finder) at stage 3, never as source of record: every number that reaches a shortlist
must re-derive from the primary filing (EDINET/DART/OAM), same as the US screen's SEC-first rule.
