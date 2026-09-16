## BLUE BENCH — BELFB — RED CASE: PARTIALLY OVERTURNED

**PACK: acknowledged.** Anchors used: hi52 335.285, lo52 129.849, CIK 729580, filing inventory, book NO POSITION/NONE. **Superseded:** (a) pack px 255.96 / dd52 −0.237 — superseded by prev close **$239.89** and a **live intraday $247.01, 2026-09-04 10:12 EDT** ([stockanalysis/belfb](https://stockanalysis.com/stocks/belfb/)); IBKR MCP connected this session but **permission was denied on `search_contracts`** — COVERAGE GAP on broker tape persists, re-poll at stage. (b) Pack XBRL block stale (rev ends 2017) — superseded by `data.sec.gov` companyconcept, PROXY-FETCHED.

### RULINGS

**1. Multiple basis mismatch — REDUCED (red half-right; its inversion is itself a vendor artifact).**
{red claim: same-vendor basis makes BELFB a 9% *premium* to VRT (37.33 vs 34.31) | my check: pulled the **sibling class page same session** — [BELFA](https://stockanalysis.com/stocks/belfa/) shows forward PE **28.01**, trailing **49.96**, price $201.65 | result: **REFUTED as a basis.** One issuer, one earnings stream, two vendor pages, forward PE **28.01 vs 37.33 — a 33% spread on a 19% price spread.** The vendor uses ~14.8M shares for BELFA and Class-B-only 12.66M for BELFB; its per-class PEs are internally inconsistent and cannot carry a dispersion verdict. Applied consistently: BELFA-basis fwd EPS $7.20 → BELFB at $239.89 = **33.3x**, *below* VRT's 34.31. Red's own consensus basis ($8.94) = **26.8x vs 34.3x = 22% discount** | ruling: the brief's 22x is **SUSTAINED as wrong** — $39.1M×4/14.44M = $10.83 implied FY26 EPS exceeds the street high $10.04, indefensible. The **"premium" inversion is OVERTURNED.** Honest gap: **~20–22% discount**, not 40%, not negative. Tag NOVEL sustained.}

**2. "Rented" cash / RNCI — SUSTAINED on arithmetic, OVERTURNED on severity.**
{red claim: EV $3.27B not $3.16B | my check: adding redeemable NCI + earnout to EV is standard; the $441.6M raise's 1.725M shares are **already inside** the 14,439,450 count both benches confirmed | result: **CONFIRMED but 3.5% of EV** — moves 22x to ~22.7x. "Rented" is rhetoric: cash raised at $266 is cash. Red counts the offering twice — once as overhang, once as disqualifying the balance sheet | ruling: REDUCED to a housekeeping adjustment, not a kill.}

**3. GAAP-vs-non-GAAP divergence — OVERTURNED as a kill (red decomposed it itself).**
{red claim: GAAP attrib −5.1% while adjusted +86% | my check: red's own text: Q2-25 carried **+$7,568K other income** and H1-25 a **−$2,653K restructuring credit** | result: **CONFIRMED prior-year-benefit artifact — the III precedent exactly.** Red found the base effect, wrote it down, and kept the finding in the kill list anyway | ruling: OVERTURNED as a kill; retained as a disclosure-quality note. Add-back composition (likely Enercon intangible amortization) **UNVERIFIED** — reconciliation table not read.}

**4. Backlog unquantified — SUSTAINED, with red's supporting number struck.**
{red claim: no backlog balance; RPO only $14.3M | my check: ASC 606 exempts ≤1yr contracts from RPO — $14.3M expiring 2027-31 is the long tail and says nothing about short-cycle backlog | result: **red's inference is unsupported, its coverage gap is real** | ruling: SUSTAINED as a genuine gap. The bookings-streak metric is transcript-only and unfalsifiable; it may not be a refuting metric.}

**5. DIO comparator — OVERTURNED. Red declared uncheckable what was one API call away.**
{red claim: 6/30/25 inventory unavailable, so YoY DIO never run | my check: `InventoryNet`, PROXY-FETCHED: **2025-06-30 = $164,648K**, 2026-06-30 = $200,226K | result: **REFUTED.** Q2-25 COGS ≈ $103.2M ($168.4M sales × 61.3%) → DIO **145.2d**; Q2-26 $200.2M/$126.6M → **143.9d**. YoY DIO **fell**. Inventory +21.6% against sales +25.1% — inventory grew *slower* than sales | ruling: OVERTURNED; the brief's claim survives on the correct comparator, and red's change-my-mind item (c) is now satisfied. RM split at 6/30/25 UNVERIFIED.}

**6. Non-voting-class discount — OVERTURNED, empirically inverted.**
{red claim: BELFB's ~20% gap to VRT is what non-voting stock in a controlled company should trade at | my check: same-session vendor pull of both classes | result: **REFUTED. BELFB $247.01 vs BELFA (the VOTING class) $207.16 — BELFB trades at a 19% PREMIUM to the vote.** In this issuer the non-voting class is the liquid, index-eligible, higher-dividend one; whatever discount the structure imposes is borne by BELFA | ruling: OVERTURNED. Red's tag CONSENSUS is also wrong — no note prices BELFB *below* BELFA. A group-level controlled-issuer discount vs VRT remains PLAUSIBLE but is unmeasured and cannot "spend" the 22%.}

**Selection judgment:** red attacked the strongest leg (the multiple) and won a real point there, but three of its six kills rest on comparators it never pulled (5), a base effect it identified and ignored (3), or a structural claim the tape inverts (6). Its detector section also **did not match the pack's dispatch list** — it invented `albuquerque_permits`/`austin_permits`/`app_review_velocity` and skipped three assigned entries.

### NEW FINDINGS RED MISSED
- **N1 (against the thesis):** buying BELFB means paying the 19% class premium. Look-through blended cap (A@$207.16 + B@$247.01) = **$3.48B vs $3.57B** single-priced — the liquidity/index premium is already in the entry price. A real haircut neither bench booked.
- **N2:** red's `lockup_expiration_calendar` fire conflates three things. The **S-8 registers plan shares and creates no seller**; insider lock-ups bind insiders, not the underwater offering buyers who *are* the overhang and were never locked. Overhang is real; red's mechanism for it is wrong.
- **N3:** three of eight plants are PRC (Dongguan/Guangxi/Shenzhen) plus Netanya. Tariff/export tail is the only genuinely unpriced risk on either side — **UNVERIFIED**, no customer or origin-mix data available.
- **PRIZE TABLE: N/A** — Bel is a profitable operating manufacturer, not a pre-revenue project developer; the magic-funding counterfactual does not apply. Stated per mandate.

### NET POSITION AFTER BOTH BENCHES
What survives: a ~20–22% same-basis consensus discount to the cohort bellwether, with red's structural explanation for it overturned and its balance-sheet kill reduced to 3.5% of EV; damage-absence now **confirmed** on the metric red attacked hardest (YoY DIO fell, inventory grew slower than sales), and **unconfirmed** on the metric red correctly struck (backlog is transcript-only). The brief's $10.83 implied EPS is dead — size off consensus $8.94, i.e. 27.6x at today's $247.01, not 22x. That is not a FLAT: no FATAL, no confirmed valuation kill at FV, and the residual discount is now unexplained rather than explained. **Post-audit kills: 1 novel (reduced to a sizing haircut) / 0 consensus.** Verdict: **STARTER, half the intended tranche**, gated on (i) live IBKR re-poll — the stock is +3% today and the vendor tape is all either bench has, (ii) no entry above the $266 offer, (iii) the 9/10 Citi fireside disclosing a backlog dollar balance or segment margin before the second tranche. Sleeve-capped, unlevered.

**Conviction: 7/10.** High on findings 5 and 6 (both document/tape-confirmed and both flip red's ruling); moderate because the backlog gap red found is real, N1's class premium genuinely narrows the edge, and no broker-side tape was obtainable.

**PRINT PROXIMITY: 2026-10-28 — UNCONFIRMED** (vendor-derived; no company scheduling PR as of 2026-09-04). ~37 trading days. **Dated disclosure event inside 5 days:** CFO fireside, Citi 2026 Global TMT, **Thu 2026-09-10 08:10 ET**, webcast — 4 trading days.

### DETECTORS CONSULTED
- **osha_establishment** — UNCHECKABLE: disputed capacity is Shenzhen/Dubnica/Netanya; OSHA covers only Waseca MN / Glen Rock PA (Connectivity, not the HPC leg). Missing: a US-sited capacity claim.
- **plant_thermal** — UNCHECKABLE: all PRC geocodes are city/province centroids (Guangxi 24.0/109.0). Missing: parcel polygons.
- **sentinel2_buildout** — UNCHECKABLE: same centroid defect; matcher resolved Dongguan (Magnetic Solutions) while the disputed ramp is Power Solutions. Missing: correct parcel.
- **cybercom_budget** — NOT-FIRED: no USCYBERCOM claim; defense leg is EU/Slovakia.
- **doe_budget** — NOT-FIRED: no DOE Office of Science claim.
- **earmark_detector** — NOT-FIRED: commercial/OEM revenue, no congressional line.
- **export_control_check** — FIRED (partial), and **red under-scored it**: 3/8 plants PRC + Netanya, no named customer to screen (COVERAGE GAP). Tariff/export tail is the one unpriced risk on both sides — see N3.
- **pentagon_jbook** — NOT-FIRED: no US DoD program of record.
- **chinese_smallcap_ramp_dump_archetype** — NOT-FIRED, clean: NJ-domiciled, 40-yr NASDAQ history, real HQ; matched on `asia_operating_jurisdiction` only.
- **clinicaltrials_lookup** — NOT-FIRED: no clinical program; matcher artifact. **Red skipped this assigned entry.**
- **common_control_merger_accounting** — NOT-FIRED: Enercon was arm's-length 80% (Nov 2024); RNCI properly carried at $102.6M, stepped $93.2M→$102.6M (marks the acquired leg *up*).
- **competitor_trial_omission** — NOT-FIRED: no trial program. **Red skipped this assigned entry.**
- **lockup_expiration_calendar** — FIRED, **mechanism corrected** (N2): the seller base is the underwater $266 buyers, not lock-up expiry or the routine 9/01 S-8. Overhang real, ~14% float increase, stock 7.1% below offer at $247.01. Lock-up terms UNVERIFIED (prospectus unread).
- **pe_dividend_recap_pre_ipo** — NOT-FIRED: no PE sponsor, no pre-IPO recap; 40-year public issuer. **Red skipped this assigned entry.**

```kg_candidate
{"name": "vendor_per_class_multiple_inconsistency", "kind": "detector", "one_line": "For dual-class issuers, data vendors compute per-class market cap and PE off inconsistent share counts, so the same company's forward PE differs by tens of percent between its own two ticker pages — poisoning any same-vendor peer comparison.", "fires_on": "Any relative-value claim quoting a vendor multiple for a dual-class ticker; test = pull BOTH class pages same session and reconcile fwd PE ratio against the price ratio. Divergence >5pp voids the vendor multiple.", "evidence_here": "stockanalysis 2026-09-04: BELFA fwd PE 28.01 @ $201.65 (cap $2.99B/~14.8M sh) vs BELFB fwd PE 37.33 @ $239.89 (cap $2.96B/12.66M sh, Class-B-only). 33% PE spread on a 19% price spread; red's 'BELFB is a premium to VRT' kill rested entirely on the 37.33.", "applies_to_guess": {"issuer_features": ["dual_class_share_structure", "vendor_multiple_citation", "peer_multiple_comparison"], "sic_prefixes": []}}
```
```kg_candidate
{"name": "nonvoting_class_liquidity_premium", "kind": "mechanism", "one_line": "In small/mid-cap dual-class issuers where the non-voting class holds the float, index membership and a dividend preference, the non-voting share trades at a PREMIUM to the vote — inverting the textbook control discount, so a 'non-voting therefore discounted' argument must be tested against the actual A/B spread before it is spent.", "fires_on": "Any thesis or kill invoking a non-voting-class discount; test = same-session quote of both classes. If non-voting > voting, the structural discount is borne by the voting class and cannot explain the peer-multiple gap.", "evidence_here": "BELFB (non-voting) $247.01 vs BELFA (voting) $207.16 on 2026-09-04 = +19% premium, with Class B holding 12.32M of 14.44M shares. Red's finding 6 used the structure to consume a 20% peer discount; the tape inverts it.", "applies_to_guess": {"issuer_features": ["dual_class_share_structure", "family_controlled", "nonvoting_class_holds_float", "index_membership_asymmetry"], "sic_prefixes": []}}
```