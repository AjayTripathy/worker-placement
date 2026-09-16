# Japan TOB / take-private lane — intake 2026-08-24

USD/JPY 159.24 at run. Announced book (spreads) and anticipatory book (fingerprints) are separate and are never summed.

## Channel note

- **Announced deals: TDnet** (`release.tdnet.info/inbs/I_list_NNN_YYYYMMDD.html`) — plain HTTP, no key, no browser, ~850 disclosures/day, formulaic titles, public PDF per row. Terms are read out of the standardised 「買付け等の概要」 table in the commencement notice.
- **EDINET API v2 does not work unkeyed** — returns `401 invalid subscription key`. The statutory TOB filing (docTypeCode 240 公開買付届出書) is the better authority and we should get a key; until then TDnet is the channel and the company's own notice is the source.
- **TDnet retains ~31 days.** The event store is therefore the history — a day we never crawled cannot be recovered. Run daily.
- **Anticipatory side is fully offline**, read from 1,525 cached EDINET annual-report XBRL fact sets: the FIEA Art.24-7 parent declaration, 【関係会社の状況】 owned-by %, 【大株主の状況】, and director birthdates.

## Held-book cross-check

- Announced targets vs the held Japan book (3388 Meiji Electric Industries, 6229 Okada Aiyon, 7222 Nissan Shatai, 8750 Dai-ichi Life): **no overlap** — no live tender touches anything we own.
- **7222 Nissan Shatai appears in the ANTICIPATORY book** (tier A_PARENT_SUB, score 8). We are already long a take-private candidate. Treat this as position context, not a new idea: it means part of the Japan book's return is already levered to this lane's thesis, and it caps how much more of the same exposure the lane should add.

## A. ANNOUNCED — spread book

45 deals tracked in the window; 13 live; 6 with a computable spread.

| target | name | bidder | offer ¥ | spot ¥ | gross % | ann. % | days | liquidity | timing |
|---|---|---|---|---|---|---|---|---|---|
| 7523 | アールビバン | 株式会社Orsay | 1,900 | 1,879 | +1.12 | +51 | 8 | THIN | DATED |
| 2162 | ｎｍｓ　ＨＤ | ワールドＨＤ | 540 | 536 | +0.75 | +34 | 8 | THIN | DATED_STEP2 |
| 4722 | フューチャー | 合同会社キーウェスト・ネットワー | 2,451 | 2,446 | +0.20 | +3 | 24 | QUOTABLE | DATED |
| 3276 | ＪＰＭＣ | 株式会社Amsterdam1及び | 2,250 | 2,244 | +0.27 | +3 | 32 | QUOTABLE | DATED |
| 9110 | ユナイテド海 | 郵船 | 10,600 | 10,480 | +1.15 | — | — | QUOTABLE | TIMING_UNBOUNDED |
| 2371 | カカクコム | ＬＩＮＥヤフー | 3,450 | 3,655 | -5.61 | — | — | QUOTABLE | TIMING_UNBOUNDED |

### 7523 アールビバン — OPEN

- **Bidder / purpose**: 株式会社Orsay · GO_PRIVATE · target opinion not parsed
- **Terms**: offer ¥1,900 vs spot ¥1,879 = +1.12% gross
- **Timing**: DATED — cash expected 2026-09-01 (8d)
- **Minimum-tender condition**: floor 3,845,584 sh; post-deal ownership at the floor = 0.91%. If the floor is missed the offer FAILS: spread -> 0 and the stock re-rates to the un-bid level, so this is a two-sided, not a capped, risk.
- **Squeeze-out**: step 2 = 株式併合 reverse split; requires an EGM special resolution, so a NON-tendering holder waits ~3-5 months beyond tender settlement for the same cash.
- **Liquidity (thin-print gate)**: THIN — 20d median turnover ¥8.8M/day — a quoted spread here is not fillable at size; this is a delisting stub, not a position
- **JPY add**: a ¥1,000,000 clip here is $6,280 of ADDITIONAL unhedged JPY on top of the existing Japan book.
- **Taxable**: tender proceeds are a disposition, not a rollover — short-term gain unless held >1y. On a +1.12% gross spread the after-tax return at a ~50% marginal rate is roughly half the headline.
- Source: https://www.release.tdnet.info/inbs/140120260710591505.pdf

### 2162 ｎｍｓ　ＨＤ — SQUEEZE_OUT

- **Bidder / purpose**: ワールドＨＤ · GO_PRIVATE · target opinion SUPPORT_AND_RECOMMEND
- **Terms**: offer ¥540 vs spot ¥536 = +0.75% gross
- **Timing**: DATED_STEP2 — step-2 cash-out effective 2026-09-01 (8d); delisting 2026-08-28
- **Minimum-tender condition**: no floor parsed — treat as UNVERIFIED, not as 'no condition'
- **Squeeze-out**: step 2 = 株式売渡請求 (Companies Act 179): available only at >=90% voting; ~1-2 months post-settlement, no EGM.
- **Liquidity (thin-print gate)**: THIN — 20d median turnover ¥5.8M/day — a quoted spread here is not fillable at size; this is a delisting stub, not a position
- **JPY add**: a ¥1,000,000 clip here is $6,280 of ADDITIONAL unhedged JPY on top of the existing Japan book.
- **Taxable**: tender proceeds are a disposition, not a rollover — short-term gain unless held >1y. On a +0.75% gross spread the after-tax return at a ~50% marginal rate is roughly half the headline.
- Source: https://www.release.tdnet.info/inbs/140120260727599733.pdf

### 4722 フューチャー — OPEN

- **Bidder / purpose**: 合同会社キーウェスト・ネットワーク · GO_PRIVATE · target opinion not parsed
- **Terms**: offer ¥2,451 vs spot ¥2,446 = +0.20% gross
- **Timing**: DATED — cash expected 2026-09-17 (24d)
- **Minimum-tender condition**: floor 23,376,700 sh. If the floor is missed the offer FAILS: spread -> 0 and the stock re-rates to the un-bid level, so this is a two-sided, not a capped, risk.
- **Squeeze-out**: step 2 = 株式併合 reverse split; requires an EGM special resolution, so a NON-tendering holder waits ~3-5 months beyond tender settlement for the same cash.
- **Liquidity (thin-print gate)**: QUOTABLE — 20d median turnover ¥2482M/day
- **JPY add**: a ¥1,000,000 clip here is $6,280 of ADDITIONAL unhedged JPY on top of the existing Japan book.
- **Taxable**: tender proceeds are a disposition, not a rollover — short-term gain unless held >1y. On a +0.20% gross spread the after-tax return at a ~50% marginal rate is roughly half the headline.
- Source: https://www.release.tdnet.info/inbs/140120260729502269.pdf

### 3276 ＪＰＭＣ — OPEN

- **Bidder / purpose**: 株式会社Amsterdam1及び株式会社Amsterdam2 · GO_PRIVATE · target opinion not parsed
- **Terms**: offer ¥2,250 vs spot ¥2,244 = +0.27% gross
- **Timing**: DATED — cash expected 2026-09-25 (32d)
- **Minimum-tender condition**: floor 6,707,800 sh. If the floor is missed the offer FAILS: spread -> 0 and the stock re-rates to the un-bid level, so this is a two-sided, not a capped, risk.
- **Squeeze-out**: step 2 = 株式併合 reverse split; requires an EGM special resolution, so a NON-tendering holder waits ~3-5 months beyond tender settlement for the same cash.
- **Liquidity (thin-print gate)**: QUOTABLE — 20d median turnover ¥474M/day
- **JPY add**: a ¥1,000,000 clip here is $6,280 of ADDITIONAL unhedged JPY on top of the existing Japan book.
- **Taxable**: tender proceeds are a disposition, not a rollover — short-term gain unless held >1y. On a +0.27% gross spread the after-tax return at a ~50% marginal rate is roughly half the headline.
- Source: https://www.release.tdnet.info/inbs/140120260803507167.pdf

### 9110 ユナイテド海 — OPEN

- **Bidder / purpose**: 郵船 · GO_PRIVATE · target opinion SUPPORT_AND_RECOMMEND
- **Terms**: offer ¥10,600 vs spot ¥10,480 = +1.15% gross
- **Timing**: TIMING_UNBOUNDED — offer is PRE-CONDITIONAL (competition clearance etc.); the commencement date is NOT fixed, so a computed annualized number would be manufactured. Gross only. SCENARIO ONLY: at 128d to cash (from the bidder's own guided commencement window (2026-11-25)) the gross +1.15% annualizes to +3%/yr — an assumption, NOT a term of the offer, and it goes to zero if the conditions fail.
- **Minimum-tender condition**: floor 3,524,375 sh; post-deal ownership at the floor = 66.83%. If the floor is missed the offer FAILS: spread -> 0 and the stock re-rates to the un-bid level, so this is a two-sided, not a capped, risk.
- **Squeeze-out**: step 2 = 株式併合 reverse split; requires an EGM special resolution, so a NON-tendering holder waits ~3-5 months beyond tender settlement for the same cash.
- **Liquidity (thin-print gate)**: QUOTABLE — 20d median turnover ¥1160M/day
- **JPY add**: a ¥1,000,000 clip here is $6,280 of ADDITIONAL unhedged JPY on top of the existing Japan book.
- **Taxable**: tender proceeds are a disposition, not a rollover — short-term gain unless held >1y. On a +1.15% gross spread the after-tax return at a ~50% marginal rate is roughly half the headline.
- Source: https://www.release.tdnet.info/inbs/140120260730503195.pdf

### 2371 カカクコム — OPEN

- **Bidder / purpose**: ＬＩＮＥヤフー · GO_PRIVATE · target opinion SUPPORT_AND_RECOMMEND
- **Terms**: offer ¥3,450 vs spot ¥3,655 = -5.61% gross
- **Timing**: TIMING_UNBOUNDED — offer is PRE-CONDITIONAL (competition clearance etc.); the commencement date is NOT fixed, so a computed annualized number would be manufactured. Gross only. SCENARIO ONLY: at 180d to cash (from a house default 180d, since the bidder guided no window) the gross -5.61% annualizes to -11%/yr — an assumption, NOT a term of the offer, and it goes to zero if the conditions fail.
- **Minimum-tender condition**: floor 131,805,000 sh; post-deal ownership at the floor = 66.05%. If the floor is missed the offer FAILS: spread -> 0 and the stock re-rates to the un-bid level, so this is a two-sided, not a capped, risk.
- **Squeeze-out**: step 2 = 株式併合 reverse split; requires an EGM special resolution, so a NON-tendering holder waits ~3-5 months beyond tender settlement for the same cash.
- **Liquidity (thin-print gate)**: QUOTABLE — 20d median turnover ¥1037M/day
- **JPY add**: a ¥1,000,000 clip here is $6,280 of ADDITIONAL unhedged JPY on top of the existing Japan book.
- **Taxable**: tender proceeds are a disposition, not a rollover — short-term gain unless held >1y. On a -5.61% gross spread the after-tax return at a ~50% marginal rate is roughly half the headline.
- Source: https://www.release.tdnet.info/inbs/140120260803506438.pdf

### Live, but the spread is NOT quotable — do not put these in a return table

- **8283 ＰＡＬＴＡＣ** — headline +0.30% vs offer ¥6,650. not quotable: last print 17d old — spread struck on a stale tape
- **4171 グローバルＩ** — headline +0.90% vs offer ¥1,680. not quotable: last print 12d old — spread struck on a stale tape

### Live but not priceable

- 3480 ジェイ・エス・ビー — TIMING_UNPARSED; QUOTABLE; terms NOT parsed. Ｕｒｓａ ４株式会社による当社株券等に対する公開買付けの結果並びに親会社及び主要株主である筆頭株主の異動に関するお知らせ
- 4320 ＣＥＨＤ — TIMING_UNPARSED; QUOTABLE; terms NOT parsed. SK-03株式会社による株式会社ＣＥホールディングスの株式（証券コード4320） に対する公開買付けの開始に関するお知らせ
- 3676 デジハＨＤ — TIMING_UNPARSED; QUOTABLE; terms NOT parsed. 株式会社デジタルハーツホールディングス（証券コード：3676）に対する公開買付けの開始に関するお知らせ
- 7462 ＣＡＰＩＴＡ — TIMING_UNPARSED; THIN; terms NOT parsed. 株式会社桃の木による当社株式に対する公開買付けに関する意見表明のお知らせ
- 4413 ボードルア — TIMING_UNPARSED; QUOTABLE; terms NOT parsed. ビーシーピーイー ネオン ケイマン エルピーによる株式会社ボードルア（証券コード：4413）に対する公開買付けの開始に関するお知らせ

## B. ANTICIPATORY — fingerprint book (NOT spreads, NOT annualized)

No offer exists for any name below. These are structural candidates only. An anticipatory name that is later bid moves to book A; until then it carries equity risk with an undated, uncertain catalyst and must be sized as equity, not as arbitrage.

| code | name | tier | score | controller | % | float % | cash/mcap | P/B | lead age |
|---|---|---|---|---|---|---|---|---|---|
| 9311 | ASAGAMI COPORATION | A | 9 | 株式会社オーエーコーポレーション | 52.5 | 47 | 0.67 | 0.47 | 88 |
| 4222 | KODAMA CHEMICAL INDUST | A | 8 | エンデバー・ユナイテッド | 52.1 | 48 | 1.13 | 0.37 | 66 |
| 6428 | OIZUMI Corporation | A | 8 | 株式会社オーイズミホールディングス | 47.2 | 53 | 1.10 | 0.39 | 83 |
| 7937 | TSUTSUMI JEWELRY CO.,L | A | 8 | 堤倭 | 51.2 | 49 | 0.80 | 0.58 | 61 |
| 6964 | SANKO CO.,LTD. | A | 8 | 株式会社田村商事 | 51.2 | 49 | 0.79 | 0.38 | 65 |
| 8920 | TOSHO CO., LTD. | A | 8 | 沓名俊 | 43.7 | 56 | 0.76 | 0.72 | 76 |
| 4628 | SK KAKEN CO.,LTD. | B | 8 | 四国興産有限会 | 31.9 | 68 | 0.76 | 0.80 | 94 |
| 9158 | 株式会社シーユーシー | A | 8 | エムスリー株式会社 | 63.5 | 37 | 0.73 | 0.65 | 52 |
| 7238 | AKEBONO BRAKE INDUSTRY | A | 8 | ジャパン・インダストリアル・ソリューショ | 50.8 | 49 | 0.62 | 0.57 | 64 |
| 7222 | NISSAN SHATAI CO.,LTD. | A | 8 | 日産自動車株式会社 | 50.0 | 50 | 0.59 | 0.69 | 64 |
| 8291 | NISSAN TOKYO SALES HOL | A | 8 | 日産ネットワークホールディングス株式会社 | 38.0 | 62 | 0.49 | 0.55 | 58 |
| 9380 | Azuma Shipping Co.,Ltd | A | 8 | 太平洋セメント㈱ | 39.4 | 61 | 0.46 | 0.68 | 63 |
| 7297 | CAR MATE MFG.CO.,LTD | A | 7 | 有限会社エム・テイ興産 | 45.9 | 54 | 1.65 | 0.44 | — |
| 6615 | UMC Electronics Co.,Lt | A | 7 | 株式会社豊田自動織 | 34.6 | 65 | 1.59 | 0.39 | 66 |
| 6059 | UCHIYAMA HOLDINGS Co., | A | 7 | 内山文 | 44.4 | 56 | 1.44 | 0.54 | — |
| 9115 | MEIJI SHIPPING GROUP C | B | 7 | 明治土地建物株式会 | 8.3 | 92 | 1.43 | 0.72 | 81 |
| 9867 | Solekia Limited | B | 7 | フリージア・マクロス株式会社 | 30.1 | 70 | 1.35 | 0.72 | 77 |
| 7521 | MUSASHI CO.,LTD. | B | 7 | 上毛実業株式会社 | 20.4 | 80 | 1.06 | 0.60 | 83 |
| 9229 | SUNWELS Co.,Ltd. | A | 7 | 株式会社杏 | 41.6 | 58 | 1.06 | 0.56 | 53 |
| 5697 | SANYU CO.,LTD. | A | 7 | 日本製鉄株式会社 | 33.7 | 66 | 0.94 | 0.48 | 63 |
| 7991 | MAMIYA-OP CO.,LTD. | A | 7 | 株式会社データ・アート | 38.1 | 62 | 0.94 | 0.42 | 69 |
| 9791 | BIKEN TECHNO CORPORATI | B | 7 | 株式会社東洋商事 | 28.4 | 72 | 0.84 | 0.39 | 91 |
| 4224 | LONSEAL CORPORATION | A | 7 | 東ソー株式会社 | 38.1 | 62 | 0.82 | 0.50 | 64 |
| 8104 | KUWAZAWA Holdings Corp | B | 7 | 太平洋セメント株式会社 | 18.2 | 82 | 0.82 | 0.67 | 73 |
| 2654 | ASMO CORPORATION | A | 7 | 株式会社ベストライフ株式会社ベストライフ | 60.9 | 39 | 0.81 | 0.92 | 47 |

### 9311 ASAGAMI COPORATION — A_PARENT_SUB, score 9
- 株式会社オーエーコーポレーション holds 52.5% — a majority-controlled listed subsidiary. This is the exact cohort the TSE is pressuring to resolve, and the controller can execute a squeeze-out unilaterally once past 90%
- lead director is 88 with no visible successor — a second, independent reason for the register to be resolved
- cash = 67% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.47 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~47% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 4d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 1,418,000 issued shares, unit 百株

### 4222 KODAMA CHEMICAL INDUSTRY CO.,LTD. — A_PARENT_SUB, score 8
- エンデバー・ユナイテッド holds 52.1% — a majority-controlled listed subsidiary. This is the exact cohort the TSE is pressuring to resolve, and the controller can execute a squeeze-out unilaterally once past 90%
- cash = 113% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.37 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~48% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 4d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 15,637,144 issued shares, unit 千株

### 6428 OIZUMI Corporation — A_PARENT_SUB, score 8
- 株式会社オーイズミホールディングス holds 47.2% — above the one-third special-resolution blocking level. The holder already controls the outcome of any squeeze-out vote, so a top-up TOB is the cheapest route to 100%
- lead director is 83 with no visible successor — a second, independent reason for the register to be resolved
- cash = 110% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.39 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~53% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 4d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 22,500,000 issued shares, unit 千株

### 7937 TSUTSUMI JEWELRY CO.,LTD. — A_PARENT_SUB, score 8
- 堤倭 holds 51.2% — a majority-controlled listed subsidiary. This is the exact cohort the TSE is pressuring to resolve, and the controller can execute a squeeze-out unilaterally once past 90%; note the filing declares NO statutory 親会社等, which at exactly 50.0% is legally consistent — control without the FIEA parent label
- cash = 80% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.58 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~49% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 4d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 15,630,000 issued shares, unit 千株

### 6964 SANKO CO.,LTD. — A_PARENT_SUB, score 8
- 株式会社田村商事 holds 51.2% — a majority-controlled listed subsidiary. This is the exact cohort the TSE is pressuring to resolve, and the controller can execute a squeeze-out unilaterally once past 90%
- cash = 79% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.38 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~49% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 4d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 9,000,000 issued shares, unit 千株

### 8920 TOSHO CO., LTD. — A_PARENT_SUB, score 8
- 沓名俊 holds 43.7% — above the one-third special-resolution blocking level. The holder already controls the outcome of any squeeze-out vote, so a top-up TOB is the cheapest route to 100%
- lead director is 76 with no visible successor — a second, independent reason for the register to be resolved
- cash = 76% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.72 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~56% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 4d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 38,315,000 issued shares, unit 千株

### 4628 SK KAKEN CO.,LTD. — B_SUCCESSION, score 8
- lead director is 94 with no same-surname successor on the board and a concentrated founder/family register (31.9% top holder) — the classic estate-driven MBO setup, where the buyer is management itself
- cash = 76% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.80 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- the annual report itself carries 資本コスト / 株価を意識した経営 language — management is already on the TSE improvement track and has committed to closing the discount one way or another
- Minority float ~68% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 4d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 15,673,885 issued shares, unit 千株

### 9158 株式会社シーユーシー — A_PARENT_SUB, score 8
- エムスリー株式会社 holds 63.5% — a majority-controlled listed subsidiary. This is the exact cohort the TSE is pressuring to resolve, and the controller can execute a squeeze-out unilaterally once past 90%; note the filing declares NO statutory 親会社等, which at exactly 50.0% is legally consistent — control without the FIEA parent label
- cash = 73% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.65 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~37% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 4d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 29,990,400 issued shares, unit 株

### 7238 AKEBONO BRAKE INDUSTRY CO.,LTD. — A_PARENT_SUB, score 8
- ジャパン・インダストリアル・ソリューションズ株式会 holds 50.8% — a majority-controlled listed subsidiary. This is the exact cohort the TSE is pressuring to resolve, and the controller can execute a squeeze-out unilaterally once past 90%
- cash = 62% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.57 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~49% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 4d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 273,768,922 issued shares, unit 千株

### 7222 NISSAN SHATAI CO.,LTD. — A_PARENT_SUB, score 8  **[HELD: Nissan Shatai]**
- 日産自動車株式会社 holds 50.0% — a majority-controlled listed subsidiary. This is the exact cohort the TSE is pressuring to resolve, and the controller can execute a squeeze-out unilaterally once past 90%; note the filing declares NO statutory 親会社等, which at exactly 50.0% is legally consistent — control without the FIEA parent label
- cash = 59% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.69 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~50% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 4d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 135,452,804 issued shares, unit 千株

## Structural findings from the first run

1. **The Japanese limit-up lock is this lane's dominant failure mode.** A target bid at a real premium goes limit-up (ストップ高) with an O=H=L bar and an unfilled buy queue for one to three sessions. Any screen that reads that print books a spread that never existed. On the first run this was worth 22 percentage points on one name and 10 on another — both would have been fictional. The lane now carries the TSE 値幅制限 table, detects the lock, and refuses to rank a locked name.
2. **Real Japanese TOB spreads are thin.** Once the phantom spreads are removed, every live quotable deal sits at +0.1% to +0.9% gross. This is an efficiently arbitraged market; the return lives in the annualization of very short dated-cash events, not in the headline spread, and it is entirely eaten by a taxable short-term rate unless the days-to-cash is genuinely small.
3. **The residual step-2 stub is where the yield is, and it is nearly untradeable.** The highest annualized numbers all come from post-tender squeeze-out stubs, which trade a few hundred to a few thousand shares a day. The spread is real; the capacity is not.
4. **A cheapness screen is not a take-private screen.** The first version of the anticipatory scorer summed cash + low P/B + old directors and simply reproduced the deep-value shelf. Requiring a control channel first — a >=33.4% holder, or an aged owner-operator with no successor — is what makes the book distinct from the value book.
5. **Japan's parent-subsidiary cohort is enormous.** 320 of 1,316 listed non-financial issuers with a cached annual report clear a control gate (238 parent-subsidiary, 82 succession). The constraint on this lane is not finding candidates; it is that the catalyst is undated, so the anticipatory book is an equity position with optionality, never an arbitrage.

## Gaps, honestly

- No EDINET API key: we read the company's TDnet notice, not the statutory 公開買付届出書. Terms should agree; where a notice was amended we take the newest PDF that parses.
- TDnet 31-day retention means the deal book is only as deep as our crawl history.
- Anticipatory fundamentals come from the last ANNUAL report and a cached close, so cash/mcap and P/B can be several months stale; treat as a screen, not a valuation.
- JPX publishes the improvement-plan list as PDFs only; the TSE-plan flag is derived from the issuer's own annual-report language instead and is a proxy for list membership.
- Anticipatory names below ¥3bn market cap are excluded as unownable; the count is printed every run so the exclusion is never silent.
- The minimum-tender floor did not parse on the step-2 squeeze-out notices, which is expected (the condition already resolved) but is reported as UNVERIFIED rather than as 'no condition'.
- Bidder identity is read from the disclosure title when only the target filed; it is a label, not a verified counterparty, and a competing-bid situation (2371) makes 'the offer price' genuinely ambiguous — that name is flagged, not priced.
