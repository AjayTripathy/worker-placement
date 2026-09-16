# Japan TOB / take-private lane — intake 2026-08-13

USD/JPY 159.32 at run. Announced book (spreads) and anticipatory book (fingerprints) are separate and are never summed.

## Channel note

- **Announced deals: TDnet** (`release.tdnet.info/inbs/I_list_NNN_YYYYMMDD.html`) — plain HTTP, no key, no browser, ~850 disclosures/day, formulaic titles, public PDF per row. Terms are read out of the standardised 「買付け等の概要」 table in the commencement notice.
- **EDINET API v2 does not work unkeyed** — returns `401 invalid subscription key`. The statutory TOB filing (docTypeCode 240 公開買付届出書) is the better authority and we should get a key; until then TDnet is the channel and the company's own notice is the source.
- **TDnet retains ~31 days.** The event store is therefore the history — a day we never crawled cannot be recovered. Run daily.
- **Anticipatory side is fully offline**, read from 1,525 cached EDINET annual-report XBRL fact sets: the FIEA Art.24-7 parent declaration, 【関係会社の状況】 owned-by %, 【大株主の状況】, and director birthdates.

## Held-book cross-check

- Announced targets vs the held Japan book (3388 Meiji Electric Industries, 6229 Okada Aiyon, 7222 Nissan Shatai, 8750 Dai-ichi Life): **no overlap** — no live tender touches anything we own.
- **7222 Nissan Shatai appears in the ANTICIPATORY book** (tier A_PARENT_SUB, score 8). We are already long a take-private candidate. Treat this as position context, not a new idea: it means part of the Japan book's return is already levered to this lane's thesis, and it caps how much more of the same exposure the lane should add.

## A. ANNOUNCED — spread book

42 deals tracked in the window; 13 live; 0 with a computable spread.

| target | name | bidder | offer ¥ | spot ¥ | gross % | ann. % | days | liquidity | timing |
|---|---|---|---|---|---|---|---|---|---|

### Live but not priceable

- 3276 ＪＰＭＣ — DATED; NO_PRINT; terms parsed. 株式会社Amsterdam1及び株式会社Amsterdam2による株式会社ＪＰＭＣ（証券コード：3276）の普通株式に対する公開買付けの開始に関するお知らせ
- 2371 カカクコム — TIMING_UNBOUNDED; NO_PRINT; terms parsed. BCPE Blitz Cayman, L.P.による当社株券等に対する公開買付けの開始予定に関するお知らせ
- 9110 ユナイテド海 — TIMING_UNBOUNDED; NO_PRINT; terms parsed. ＮＳユナイテッド海運株式会社株式（証券コード：9110）に対する 公開買付けの開始予定に関するお知らせ
- 2162 ｎｍｓ　ＨＤ — DATED_STEP2; NO_PRINT; terms parsed. 株式会社ワールドホールディングスによる当社株式に対する公開買付けの結果及び親会社の異動に関するお知らせ
- 4722 フューチャー — DATED; NO_PRINT; terms parsed. 合同会社キーウェスト・ネットワークによるフューチャー株式会社（証券コード：4722）に対する公開買付けの開始に関するお知らせ
- 3480 ジェイ・エス・ビー — TIMING_UNPARSED; NO_PRINT; terms NOT parsed. Ｕｒｓａ ４株式会社による当社株券等に対する公開買付けの結果並びに親会社及び主要株主である筆頭株主の異動に関するお知らせ
- 8283 ＰＡＬＴＡＣ — PAST_STEP2; NO_PRINT; terms parsed. 株式会社ＰＡＬＴＡＣ株式（証券コード：8283）に対する公開買付けの結果に関するお知らせ
- 4171 グローバルＩ — DATED_STEP2; NO_PRINT; terms parsed. 株式会社ユーザベースによる当社株券等に対する公開買付けの結果並びに親会社、主要株主である筆頭株主及び主要株主の異動に関するお知らせ
- 7523 アールビバン — DATED; NO_PRINT; terms parsed. 株式会社Orsayによるアールビバン株式会社株式（証券コード：7523）に対する公開買付けの開始に関するお知らせ
- 2997 Ｇ－ストレージ王 — DATED; NO_PRINT; terms parsed. エリアリンク株式会社による当社株券等に対する公開買付けに関する賛同の意見表明及び応募推奨のお知らせ
- 4320 ＣＥＨＤ — TIMING_UNPARSED; NO_PRINT; terms NOT parsed. SK-03株式会社による株式会社ＣＥホールディングスの株式（証券コード4320） に対する公開買付けの開始に関するお知らせ
- 3676 デジハＨＤ — TIMING_UNPARSED; NO_PRINT; terms NOT parsed. 株式会社デジタルハーツホールディングス（証券コード：3676）に対する公開買付けの開始に関するお知らせ
- 7462 ＣＡＰＩＴＡ — TIMING_UNPARSED; NO_PRINT; terms NOT parsed. 株式会社桃の木による当社株式に対する公開買付けに関する意見表明のお知らせ

## B. ANTICIPATORY — fingerprint book (NOT spreads, NOT annualized)

No offer exists for any name below. These are structural candidates only. An anticipatory name that is later bid moves to book A; until then it carries equity risk with an undated, uncertain catalyst and must be sized as equity, not as arbitrage.

| code | name | tier | score | controller | % | float % | cash/mcap | P/B | lead age |
|---|---|---|---|---|---|---|---|---|---|
| 9311 | ASAGAMI COPORATION | A | 9 | 株式会社オーエーコーポレーション | 52.5 | 47 | 0.67 | 0.47 | 88 |
| 4222 | KODAMA CHEMICAL INDUST | A | 8 | エンデバー・ユナイテッド | 52.1 | 48 | 1.24 | 0.34 | 66 |
| 6428 | OIZUMI Corporation | A | 8 | 株式会社オーイズミホールディングス | 47.2 | 53 | 1.12 | 0.38 | 83 |
| 7937 | TSUTSUMI JEWELRY CO.,L | A | 8 | 堤倭 | 51.2 | 49 | 0.81 | 0.57 | 61 |
| 6964 | SANKO CO.,LTD. | A | 8 | 株式会社田村商事 | 51.2 | 49 | 0.81 | 0.37 | 65 |
| 8920 | TOSHO CO., LTD. | A | 8 | 沓名俊 | 43.7 | 56 | 0.79 | 0.69 | 76 |
| 4628 | SK KAKEN CO.,LTD. | B | 8 | 四国興産有限会 | 31.9 | 68 | 0.77 | 0.79 | 94 |
| 9158 | 株式会社シーユーシー | A | 8 | エムスリー株式会社 | 63.5 | 37 | 0.72 | 0.65 | 52 |
| 7222 | NISSAN SHATAI CO.,LTD. | A | 8 | 日産自動車株式会社 | 50.0 | 50 | 0.59 | 0.69 | 64 |
| 7238 | AKEBONO BRAKE INDUSTRY | A | 8 | ジャパン・インダストリアル・ソリューショ | 50.8 | 49 | 0.58 | 0.62 | 64 |
| 9380 | Azuma Shipping Co.,Ltd | A | 8 | 太平洋セメント㈱ | 39.4 | 61 | 0.48 | 0.65 | 63 |
| 8291 | NISSAN TOKYO SALES HOL | A | 8 | 日産ネットワークホールディングス株式会社 | 38.0 | 62 | 0.48 | 0.56 | 58 |
| 9115 | MEIJI SHIPPING GROUP C | B | 7 | 明治土地建物株式会 | 8.3 | 92 | 1.68 | 0.62 | 81 |
| 7297 | CAR MATE MFG.CO.,LTD | A | 7 | 有限会社エム・テイ興産 | 45.9 | 54 | 1.63 | 0.45 | — |
| 6615 | UMC Electronics Co.,Lt | A | 7 | 株式会社豊田自動織 | 34.6 | 65 | 1.55 | 0.40 | 66 |
| 6059 | UCHIYAMA HOLDINGS Co., | A | 7 | 内山文 | 44.4 | 56 | 1.46 | 0.53 | — |
| 9867 | Solekia Limited | B | 7 | フリージア・マクロス株式会社 | 30.1 | 70 | 1.44 | 0.68 | 77 |
| 3851 | NIPPON ICHI SOFTWARE I | A | 7 | 有限会社ローゼンクイーン商 | 46.3 | 54 | 1.22 | 0.68 | — |
| 7521 | MUSASHI CO.,LTD. | B | 7 | 上毛実業株式会社 | 20.4 | 80 | 1.11 | 0.58 | 83 |
| 9229 | SUNWELS Co.,Ltd. | A | 7 | 株式会社杏 | 41.6 | 58 | 0.97 | 0.61 | 53 |
| 5697 | SANYU CO.,LTD. | A | 7 | 日本製鉄株式会社 | 33.7 | 66 | 0.96 | 0.47 | 63 |
| 7991 | MAMIYA-OP CO.,LTD. | A | 7 | 株式会社データ・アート | 38.1 | 62 | 0.88 | 0.45 | 69 |
| 2654 | ASMO CORPORATION | A | 7 | 株式会社ベストライフ株式会社ベストライフ | 60.9 | 39 | 0.83 | 0.90 | 47 |
| 4224 | LONSEAL CORPORATION | A | 7 | 東ソー株式会社 | 38.1 | 62 | 0.82 | 0.50 | 64 |
| 8104 | KUWAZAWA Holdings Corp | B | 7 | 太平洋セメント株式会社 | 18.2 | 82 | 0.82 | 0.66 | 73 |

### 9311 ASAGAMI COPORATION — A_PARENT_SUB, score 9
- 株式会社オーエーコーポレーション holds 52.5% — a majority-controlled listed subsidiary. This is the exact cohort the TSE is pressuring to resolve, and the controller can execute a squeeze-out unilaterally once past 90%
- lead director is 88 with no visible successor — a second, independent reason for the register to be resolved
- cash = 67% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.47 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~47% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 7d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 1,418,000 issued shares, unit 百株

### 4222 KODAMA CHEMICAL INDUSTRY CO.,LTD. — A_PARENT_SUB, score 8
- エンデバー・ユナイテッド holds 52.1% — a majority-controlled listed subsidiary. This is the exact cohort the TSE is pressuring to resolve, and the controller can execute a squeeze-out unilaterally once past 90%
- cash = 124% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.34 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~48% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 7d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 15,637,144 issued shares, unit 千株

### 6428 OIZUMI Corporation — A_PARENT_SUB, score 8
- 株式会社オーイズミホールディングス holds 47.2% — above the one-third special-resolution blocking level. The holder already controls the outcome of any squeeze-out vote, so a top-up TOB is the cheapest route to 100%
- lead director is 83 with no visible successor — a second, independent reason for the register to be resolved
- cash = 112% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.38 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~53% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 7d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 22,500,000 issued shares, unit 千株

### 7937 TSUTSUMI JEWELRY CO.,LTD. — A_PARENT_SUB, score 8
- 堤倭 holds 51.2% — a majority-controlled listed subsidiary. This is the exact cohort the TSE is pressuring to resolve, and the controller can execute a squeeze-out unilaterally once past 90%; note the filing declares NO statutory 親会社等, which at exactly 50.0% is legally consistent — control without the FIEA parent label
- cash = 81% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.57 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~49% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 7d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 15,630,000 issued shares, unit 千株

### 6964 SANKO CO.,LTD. — A_PARENT_SUB, score 8
- 株式会社田村商事 holds 51.2% — a majority-controlled listed subsidiary. This is the exact cohort the TSE is pressuring to resolve, and the controller can execute a squeeze-out unilaterally once past 90%
- cash = 80% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.37 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~49% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 7d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 9,000,000 issued shares, unit 千株

### 8920 TOSHO CO., LTD. — A_PARENT_SUB, score 8
- 沓名俊 holds 43.7% — above the one-third special-resolution blocking level. The holder already controls the outcome of any squeeze-out vote, so a top-up TOB is the cheapest route to 100%
- lead director is 76 with no visible successor — a second, independent reason for the register to be resolved
- cash = 79% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.69 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~56% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 7d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 38,315,000 issued shares, unit 千株

### 4628 SK KAKEN CO.,LTD. — B_SUCCESSION, score 8
- lead director is 94 with no same-surname successor on the board and a concentrated founder/family register (31.9% top holder) — the classic estate-driven MBO setup, where the buyer is management itself
- cash = 77% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.79 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- the annual report itself carries 資本コスト / 株価を意識した経営 language — management is already on the TSE improvement track and has committed to closing the discount one way or another
- Minority float ~68% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 7d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 15,673,885 issued shares, unit 千株

### 9158 株式会社シーユーシー — A_PARENT_SUB, score 8
- エムスリー株式会社 holds 63.5% — a majority-controlled listed subsidiary. This is the exact cohort the TSE is pressuring to resolve, and the controller can execute a squeeze-out unilaterally once past 90%; note the filing declares NO statutory 親会社等, which at exactly 50.0% is legally consistent — control without the FIEA parent label
- cash = 72% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.65 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~37% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 7d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 29,990,400 issued shares, unit 株

### 7222 NISSAN SHATAI CO.,LTD. — A_PARENT_SUB, score 8  **[HELD: Nissan Shatai]**
- 日産自動車株式会社 holds 50.0% — a majority-controlled listed subsidiary. This is the exact cohort the TSE is pressuring to resolve, and the controller can execute a squeeze-out unilaterally once past 90%; note the filing declares NO statutory 親会社等, which at exactly 50.0% is legally consistent — control without the FIEA parent label
- cash = 59% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.69 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~50% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 7d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 135,452,804 issued shares, unit 千株

### 7238 AKEBONO BRAKE INDUSTRY CO.,LTD. — A_PARENT_SUB, score 8
- ジャパン・インダストリアル・ソリューションズ株式会 holds 50.8% — a majority-controlled listed subsidiary. This is the exact cohort the TSE is pressuring to resolve, and the controller can execute a squeeze-out unilaterally once past 90%
- cash = 58% of market cap — the target's own balance sheet funds much of the consideration, so the controller needs little outside money
- P/B 0.62 — below the TSE 1.0x line; taking in the minority below stated book is accretive to the acquirer on day one
- Minority float ~49% of shares; the controller needs to reach 90% to squeeze out without an EGM.
- Inputs: annual-report balance sheet, price cached 7d ago — screen-grade, not valuation-grade. 大株主 table reconciled against 273,768,922 issued shares, unit 千株

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
