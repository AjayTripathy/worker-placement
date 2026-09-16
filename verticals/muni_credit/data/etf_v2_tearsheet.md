# CA Muni ETF Basket — v2 Tear Sheet

**As of:** 2026-05-30 · **Holdings:** 20 · **Vertical:** muni_credit · **Supersedes:** v1 (20 holdings, scored 2026-05-28)

This is a framework-screened concentrated CA municipal basket. The screen is a *lying-detector* (honesty-alpha framing), not a yield-maximizer: it excludes names where disclosure quality or wrap status fails verification, and keeps names where the security structure is either covenant-inapplicable (statutory lien) or credit-enhanced (Cal-Mortgage / full-faith pledge).

---

## v2 corrections (3 applied)

| # | Action | Out | In | Why |
|---|--------|-----|-----|-----|
| 1 | **Swap** | River Delta USD GO `768040CZ8` | **Duarte USD GO `263597UP9`** | Within-class K-12 GO substitution. Both secured by SB 222 statutory lien on ad valorem property tax; covenant detector inapplicable to either. |
| 2 | **Exclude** | Providence St. Joseph CHFFA `13032UFN3` (A/A3) | — | Confirmed **naked** (NOT_INSURED). Drop unwrapped acute-hospital conduit. |
| 3 | **Exclude** | Adventist Health/West CHFFA `13032UGK8` (BBB+/NR) | — | Confirmed **naked**, lowest-rated of the four CHFFA names. |
| 4 | **Backfill** | — | **Aldersly** + **Bethany Home Society** (both Cal-Mortgage **AA-** wrapped) | Replace naked acute-hospital exposure with the framework's strongest verified muni credit-enhancement mechanism. |

Net holding count unchanged at 20.

### ⚠ Backfill sector-shift caveat (read this)
The two excluded names were **naked acute hospitals**. The two backfill names are **Cal-Mortgage-wrapped senior-living CCRCs** — *not* acute hospitals. The only verified AA- Cal-Mortgage-wrapped candidates in existing research are CCRCs. The deliberate design point is the **wrap** (State of CA AA- credit substitution), which is the muni vertical's highest-conviction masking/enhancement mechanism. The honest cost is that the "hospital sleeve" label from v1 no longer literally applies — it's now a wrapped senior-living sleeve.

### CUSIP integrity — now VERIFIED (2026-05-30)
Aldersly and Bethany Home CUSIPs were previously TBD; they are now **scraped from EMMA and verified against the Official Statement PDFs** (browser-fingerprint session → `Disclaimer.aspx` CUSIP-license postback → OS PDF maturity schedule; EMMA's scale JSON returns only the encrypted `Cusip9Enc` token, so plaintext CUSIPs come from the OS). Both share issuer CUSIP base **13048V** (CMFA Series 2023).

| Obligor | Representative CUSIP | Final maturity | Term-bond par | Full ladder |
|---|---|---|---|---|
| Aldersly | `13048VL55` (2053 term, 5%) | 2053 | $10.645M (+$5.535M 4.25%, +$6.745M 2043) | 9 serials 2027–2035 + 4 term + B-1/B-2/C; base 13048V |
| Bethany Home | `13048VG69` (2052 term, 5%, *Final CUSIP*) | **2052** | $26.565M (+$13.5M 2042) | 9 serials 2026–2034 + 2 term; base 13048V |

Full per-maturity CUSIP arrays are in `etf_v2_holdings.json` (slots 9–10, `cusip_ladder`). Both ladders are **back-loaded** — ~81% of par sits in the 2042/2043 + 2052/2053 term bonds, confirming the long-duration characterization in the inflation section below.

#### All 20 holdings now CUSIP-verified (2026-05-30)
Extending the same EMMA → OS-PDF method to the whole basket, **every slot now carries a verified representative CUSIP** read directly from the OS cover maturity-schedule table (no fabrication; "a wrong CUSIP is worse than none"). "Representative" = the longest-dated live maturity (usually the final term bond) of the chosen representative series — **not** the whole obligor. Per-slot source detail and full ladders are in the sidecar `data/emma_verified_cusips.json`. A reusable scraper bug was fixed in the process (`_partial_pdf_links` only matched `/P`-prefixed OS filenames; now accepts any 1–2-letter prefix, which unblocked the `ER/EP/ES`-coded TABs — Clovis, San Jose, Fontana).

| Slot | Obligor | Representative CUSIP | Final mat. | Note |
|---|---|---|---|---|
| 2 | Alpine **County** USD GO | `02083FBM3` | 2049 | **SUB** — Alpine Union has no live GO (matured 2010 rfdg); same SB-222 class |
| 3 | Clovis USD GO | `189342B49` | 2040 | Elec 2012 Ser D term |
| 4 | Downey USD GO | `261005TX0` | 2057 | Series B term |
| 5 | Sanger USD GO | `800851SZ1` | 2044 | 2021 Rfdg; full ladder verified |
| 6 | Pomona USD GO | `732098RB6` | 2048 | 2008 Elec Ser H term |
| 14 | San Jose Successor TAB | `798147AQ9` | 2035 | 2017A senior |
| 15 | Fontana Successor TAB | `34461CAU8` | 2036 | Series 2017A |
| 16 | **Cloverdale CDA** Successor TAB | `189168AQ0` | 2038 | **CORRECTED ENTITY** — legacy "Cloverdale Redevelopment" was wrong; live entity is the CDA Successor Agency 2020 Ser A |
| 17 | MWD So Cal Water Rev | `59266TTJ0` | 2051 | 2021 Ser A term |
| 18 | Marina Coast Water Rev | `56808CBU2` | 2037 | 2025 Enterprise Rfdg; full ladder live |
| 19 | California State GO | `13063DG36` | 2051 | Various Purpose GO term |
| 20 | County of San Diego **COP** | `7973917R4` | 2046 | **SUB + RELABEL** — no SD County POBs on EMMA; swapped to 2026 Ser A COP (lease-revenue), slot relabeled POB → COP |

Three slots required documented substitutions/corrections (Alpine, Cloverdale, San Diego) — surfaced here and in the holdings `_meta`, mirroring the v2-corrections pattern. Structural facts (par / final maturity / n_maturities) come from the EMMA scale JSON; representative CUSIP + base are read from the OS cover. Early rungs of refunding series may already be matured (we are in 2026).

---

## Holdings by sector

### K-12 dedicated-tax GO (6) — *structurally covenant-inapplicable*
Secured by the SB 222 (2016) statutory lien on ad valorem property tax. No rate covenant, no DSCR, no additional-bonds test. The covenant_breach detector returns INAPPLICABLE by design.

- Duarte USD GO `263597UP9` *(swapped in)*
- Alpine USD GO
- Clovis USD GO *(watchlist: Title IX — run pension/exec-turnover suite)*
- Downey USD GO
- Sanger USD GO
- Pomona USD GO *(watchlist: fiscal-ranking decline — run auditor_change + pension_funded_ratio)*

### Cal-Mortgage-wrapped CCRC (2) — *State AA- credit substitution* ★ framework edge
The investor is buying **State of California AA- credit risk**, not the single-site CCRC underlying. This is the strongest verified wrap in the muni catalog.

| Obligor | Issuer / Series | Par | Maturity | Wrap | Traded gross YTM (EMMA RTRS) |
|---|---|---|---|---|---|
| Aldersly (Garden Retirement) | CMFA Insured 2023 | $61.3M | 2053 | Cal-Mortgage AA- | **4.12%** — sale-to-customer 2026-04-23 (HIGH; 174 trades) |
| Bethany Home Society (San Joaquin) | CMFA Insured 2023 | $49.56M | **2052** | Cal-Mortgage AA-, CMS 4★ | **4.98%** — 2023 issuance only (STALE; 7 trades, $5M blocks) |

*Both construction-period: capitalized-interest / fill-up transition risk in 2025-2026, deferred behind the wrap.*

**Verified security structure (from OS, 2026-05-30).** Both bonds carry the identical Cal-Mortgage package: **Gross Revenue pledge (parity)** + **first-mortgage-lien Deed of Trust** + Bond Reserve Account, all behind the **HCAI Contract of Insurance** — on an insurance default the State Treasurer issues debentures *fully and unconditionally guaranteed by the State*. Regulatory-Agreement financial covenants: **DSCR ≥ 1.25×**, **Current Ratio ≥ 1.50×**, **Days Cash on Hand ≥ 150 (Aldersly) / ≥ 60 (Bethany)**. Two wrap-specific notes for the file: (1) the Deed of Trust may be amended/subordinated/terminated *with Department consent and without bondholder consent* — the lien is real but the State, not the holder, controls it; (2) **Parity Debt is permitted** under the Regulatory Agreement, so the first lien is not a closed lien.

### Naked CHFFA hospital conduit (2) — *kept on underlying-quality grounds*
No wrap, but strong standalone underlying ratings; the two lower-rated CHFFA names were excluded.
- El Camino Hospital `13032UMJ4` (AA/Aa3) — *watchlist*
- Stanford Health Care `13032U3Y2` (AA-/Aa2) — *watchlist*

### Other structured / revenue (10)
- **CalHFA program** `13032WDK7` — mortgage-pool parity lien
- **Anaheim Electric Utility Rev** `032556PX4`, `032556PY2` — rate covenant (~1.10x DSCR)
- **Successor RDA TABs** (3): San Jose *(host-city AAA)*, Fontana, Cloverdale — ROPS allocation intercept
- **Water revenue** (2): MWD *(1.20x DSCR, multi-decade clean)*, Marina Coast *(smallest — reconsider)*
- **CA State GO** — full-faith pledge, covenant-inapplicable
- **County of San Diego** POB/Rev — Fitch AAA (Jun 2024)

---

## Wrap / security structure summary

| Security class | Count |
|---|---|
| Structurally secured, no MTI covenants (6 K-12 GO + 1 State GO) | 7 |
| Cal-Mortgage State AA- insured (CCRC) | 2 |
| Naked conduit / revenue covenant unverified | 11 |

---

## Yield framing (honesty-alpha discipline)

**Indicative yields are now REAL traded gross YTM** pulled from the EMMA RTRS per-CUSIP tape (2026-05-30), sale-to-customer preferred — *not* MMD-modeled, *not* TEY, *not* net-of-fees. Full per-slot detail (price, par, trade type, recency confidence) is in the sidecar `data/emma_trade_activity.json`.

| Slot | Obligor | Traded gross YTM | Last trade | Conf. |
|---|---|---|---|---|
| 1 | Duarte USD GO | 4.90% | 2026-05-19 | HIGH |
| 2 | Alpine County USD GO *(sub)* | 5.00% | 2025-12-17 | MEDIUM |
| 3 | Clovis USD GO | 3.84% | **2015-09-03** | **STALE** |
| 4 | Downey USD GO | 4.24% | 2026-05-26 | HIGH |
| 5 | Sanger USD GO | 5.54% | 2026-05-28 | HIGH |
| 6 | Pomona USD GO | 4.77% | 2026-05-22 | HIGH |
| 7 | El Camino Hosp (naked CHFFA) | 3.46% | 2026-05-29 | HIGH |
| 8 | Stanford Health (naked CHFFA) | 4.38% | 2026-05-26 | HIGH |
| 9 | **Aldersly** (Cal-Mortgage) | **4.12%** | 2026-04-23 | HIGH |
| 10 | **Bethany Home** (Cal-Mortgage) | **4.98%** | **2023-10-31** | **STALE** |
| 11 | CalHFA program | 4.60% | 2026-05-29 | HIGH |
| 12 | Anaheim Electric Rev | 4.21% | 2026-05-26 | HIGH |
| 13 | Anaheim Electric Rev (companion) | 3.83% | 2026-02-11 | MEDIUM |
| 14 | San Jose Successor TAB | **— never traded —** | — | **NO_TAPE** |
| 15 | Fontana Successor TAB | 3.86% | 2026-05-21 | HIGH |
| 16 | Cloverdale CDA Successor TAB | 4.36% | 2026-04-24 | HIGH |
| 17 | MWD So Cal Water Rev | 3.86% | 2026-05-28 | HIGH |
| 18 | Marina Coast Water Rev | 2.93% | 2026-05-07 | HIGH |
| 19 | California State GO | 4.73% | 2026-05-15 | HIGH |
| 20 | San Diego County COP *(sub)* | 4.07% | 2026-05-22 | HIGH |

**Liquidity honesty (3 caveats):** (1) **slot 14 San Jose TAB has never traded** — yield genuinely unknowable, left null, not invented; (2) **slot 3 Clovis** last traded in **2015** and **slot 10 Bethany** only at **2023 issuance** (7 institutional blocks) — both are indicative-only, treat with low weight; (3) several prints are thin retail tickets (<$25k par) that carry wide markups, so a single trade is not a fair mid.

**TEY gross-up (bracket-dependent).** Multiply the *gross* YTM by ~2.01 at CA's top combined rate (37% fed + 13.3% CA ≈ 50.3%, income >~$1M) or ~1.80 at a typical high earner (~44.3%). Worked on the wrapped CCRC sleeve using *Aldersly's real traded 4.12%*: **TEY ≈ 8.3% (top) / ≈ 7.4% (typical)**.[^amt] Two cautions still apply: (1) the top-bracket multiplier makes any long muni *look* like a junk yield, but you are locking decades of duration to get it — don't compare TEY to a nominal Treasury/corporate; (2) Bethany's 4.98% is a stale 2023 print, so its TEY is the softest number on the page.

[^amt]: **AMT.** The TEY assumes full federal exemption. That holds for the CCRC Cal-Mortgage conduits (Aldersly, Bethany) — qualified 501(c)(3) bonds are *excluded* from the AMT preference. It does **not** hold cleanly for the **CalHFA housing bond `13032WDK7`**: single-family mortgage revenue bonds are typically *specified private-activity bonds* subject to AMT, so an AMT payer loses part of the federal exemption and the gross-up overstates that name's TEY.

---

## Alpha sources, inflation risk & ladder stepdown

### Where the edge actually comes from (and what you pay for it)

The framework's edge is **not yield** — it's the honesty/exclusion screen plus credit-enhancement capture. Read this table as "alpha source → mechanism → tradeoff you accept."

| Alpha source | Mechanism | Edge | Tradeoff / risk you accept |
|---|---|---|---|
| **Honesty exclusion screen** | Drop names failing disclosure or wrap verification (e.g. the 2 naked CHFFA conduits) | Avoids the lemons — the framework's *actual* contribution is exclusion, not selection | Shrinks the universe; generates no yield by itself |
| **Credit-ladder stepdown (wrap-protected)** | Buy a nominally *low* credit (single-site CCRC) where the **Cal-Mortgage AA- wrap** lifts effective credit to State-of-CA level | Spread pickup vs the *enhanced* risk — rating-conditional compression ([[rating-conditional-wrap-compression]]) | **Enhancer dependency**: HFCLIF reserve ~$127.8M, State AA-. The St. Rose Hospital claim ($13.96M, 2025) proves claims are real, not theoretical. Construction-period fill-up risk 2025-26. |
| **Statutory-lien capture** | K-12 GO secured by the **SB 222** dedicated property-tax lien (≈5-notch uplift) | AA-equivalent security bought at a GO spread | Concentrated CA property-tax base; no covenant tripwire to monitor |
| **Yield from duration** | Long bullets (2053) at a 4.85% coupon | Highest nominal carry in the basket | **Inflation/rate risk — the dominant *un-hedged* exposure (see below). The framework screens honesty, NOT rate risk.** |

### Inflation risk — current structure vs a laddered stepdown

The basket's *known* maturities cluster at **2053** (the wrapped CCRC sleeve), so as specified it is a **long-duration bullet**, maximally exposed to an inflation/rate shock. A 4.85% / ~27yr bond carries a modified duration ≈ **15**, so a **+100 bp** rate move ≈ **−15% mark-to-market**. That is the single largest risk in the book and it is *uncompensated* by the honesty screen.

A **ladder stepdown** reallocates from the long bullet toward shorter rungs, trading yield for a materially smaller rate shock. Illustrative (rung yields are MMD-curve indicative, not sourced CUSIPs):

| Rung | Maturity | Mod. duration | Indicative gross yield | −100 bp price impact | Role |
|---|---|---|---|---|---|
| 1 | 0–3 yr | ~2.5 | ~2.3% | ≈ −2.5% | liquidity / reinvestment optionality |
| 2 | 3–7 yr | ~5 | ~3.0% | ≈ −5% | core stability |
| 3 | 7–15 yr | ~9 | ~3.7% | ≈ −9% | belly carry |
| 4 | 15–30 yr | ~15 | ~4.85% | ≈ −15% | yield anchor — **where the current basket sits** |

**The tradeoff, quantified.** An equal-weight 4-rung ladder blends to ≈ **3.5% gross yield / duration ~7.9 / −8% per +100 bp** — versus the all-long structure at **4.85% / duration ~15 / −15%**. So the stepdown **gives up ~135 bps of gross yield to roughly halve the inflation/rate shock**. Where on that curve you want to sit is the portfolio decision; this basket currently sits entirely at Rung 4.

> Caveat: the rung *yields* in the stepdown table above are still **generic MMD-curve placeholders** illustrating the duration/yield tradeoff — they are NOT the basket's real holdings. The basket's actual per-CUSIP traded yields are now sourced (see the Yield-framing table above and `data/emma_trade_activity.json`); all 20 also carry a verified final maturity. The stepdown analysis remains a *proposed* restructuring, not the current book.

---

## Verification status (hostile-validator rule)

**0 of the covenant-applicable holdings have had audit text directly retrieved.** UNVERIFIABLE ≠ clean. The v2 corrections are **structural** — wrap status (confirmed via HCAI/CHFFA insurance data) and sector reclassification. They do **not** assert covenant cleanliness on any name.

### Highest-priority verification next steps
1. ~~Pull EMMA CUSIPs for Aldersly / Bethany Home~~ → ~~all 20 CUSIPs~~ → ~~pull EMMA **trade activity** for real traded yields~~ ✅ **DONE 2026-05-30** (CUSIPs OS-verified; per-CUSIP RTRS tape pulled for 19/20 — San Jose TAB has never traded; yields + recency confidence in `data/emma_trade_activity.json`). Residual: re-fresh the 2 STALE prints (Clovis 2015, Bethany 2023-issuance) if/when they next trade.
2. Resolve the 2 naked CHFFA underlyings' latest audits (El Camino, Stanford)
3. Marina Coast Water audit (smallest obligor, thinnest headroom)
4. Anaheim FY25 electric-utility disclosure (URL known, PDF binary-unextractable)
5. MWD FY25 ACFR (403-blocked — needs browser fingerprint)
