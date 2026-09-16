# Defense-Tech Cohort — Material Signals in R/f/M Form

Each material finding from the 5-name blinded cohort, decomposed into:
- **R** — the company's claim, verbatim or close paraphrase from the filing
- **f** — the regulatory / structural relationship: what an external registry SHOULD show if R is true
- **M** — what the registry / data source actually shows
- **Gap** — the divergence (what makes this a signal)
- **Severity** — PASS / MODERATE / SEVERE / RED_FLAG, per the subagent's score
- **Falsification** — what would prove this signal wrong over the 12-month window

Findings are grouped by ticker, ranked within ticker by severity.

---

## ONDS (Ondas Inc.) — Composite 1.29, 2 RED_FLAG

### Signal ONDS-1 — RED_FLAG_NEGATIVE
- **R:** "OAS primarily targets defense, homeland security, and public safety customers. A significant portion of our business... involves sales to government customers, including defense, homeland security, and public safety agencies."
- **f:** A US-defense / homeland-security contractor should appear as a federal contract recipient in USAspending.gov (the authoritative FPDS-backed federal procurement record). Companies that derive material revenue from US federal agencies have prime-contract obligations visible there.
- **M:** USAspending direct queries for Ondas Inc., Ondas Holdings, Ondas Networks, Ondas Autonomous Systems, Airobotics, Sentrycs, Roboteam, 4M Defense → **zero federal contract awards.** Only American Robotics shows up at all, with a single $168K DHS award (2020-2026 window). The 10 "Ondas" matches in USAspending are all HONDASHOKAI Y.K. — a Japanese supplier of plywood, freezer boxes, and flow-meter calibration in Iwakuni (substring noise).
- **Gap:** Entire defense / homeland-security customer narrative has **no traceable US federal contract footprint** despite naming product categories (CUAS, UGV, loitering munitions, force protection) that map directly to USAspending-visible programs.
- **Falsification:** If by 2027-05-16 USAspending shows ≥$5M in cumulative federal contract obligations to Ondas / Airobotics / Sentrycs / Roboteam, the signal is wrong. Alternatively if Ondas restates the narrative ("our government revenue is primarily foreign / Israeli MOD / classified prime flow-through") the divergence resolves on the R-side rather than on the M-side.

### Signal ONDS-2 — SEVERE_UNDERDELIVERY
- **R:** "Ondas Networks has historically targeted North American freight rail (AAR, Class I railroads) as the early adoption market for FullMAX. Industry bodies including AAR adopted IEEE 802.16."
- **f:** A Class I railroad rolling out FullMAX over a multi-year PTC / next-gen-comms program would appear in the railroad's 10-K — risk-factor language, capex disclosure, or vendor mentions. ~8 years of "early adoption" claims should produce at least 1-2 mentions in counterparty 10-Ks.
- **M:** EDGAR fulltext "FullMAX" or "Ondas Networks" restricted to UP (CIK 100885) = 0; CSX (277948) = 0; NSC (702165) = 0; BRK / BNSF (1067983) = 0; CN (16868) = 0; CP/CPKC (1606480) = 0; Wabtec (943452 — dominant rail PTC equipment OEM) = 0. Total cross-filer FullMAX hits = 168, all top hits are Ondas's own filings.
- **Gap:** 8 years of explicit rail-vertical positioning, zero counterparty corroboration in the 7 obvious counterparties' SEC filings.
- **Falsification:** If by 2027-05-16 any of UP / CSX / NSC / BNSF / CN / CPKC / Wabtec discloses a FullMAX deployment in a 10-K / 10-Q / 8-K, the signal is wrong.

### Signal ONDS-3 — RED_FLAG_NEGATIVE
- **R:** Sentrycs (CoRF CUAS), Roboteam (UGV), 4M Defense (demining) are deployed defense capabilities feeding US DoD / Western military customers.
- **f:** Defense platforms pitched to US DoD should show up as Sentrycs / Roboteam contracts in USAspending across DoD + DHS + State (queried unrestricted).
- **M:** Sentrycs = 0 federal awards. Roboteam = 0 federal awards.
- **Gap:** Two named US-DoD-aligned defense platforms with zero federal contract footprint of any kind.
- **Falsification:** If by 2027-05-16 either Sentrycs or Roboteam shows ≥1 federal award, signal is wrong. Alternatively if filing is restated to clarify these are foreign-only (Israel/UAE) sales, divergence resolves.

### Signal ONDS-4 — MODERATE_UNDERDELIVERY
- **R:** Two customers accounted for $27.8M (55%) and $5.4M (11%) of 2025 revenue (vs. $3.8M / $1.9M / $0.7M for top 3 in 2024 — a 7x+ revenue concentration jump). One customer = 73% of A/R at year-end.
- **f:** A $27.8M revenue relationship is not material to the named possible counterparties (defense primes $30-70B revenue, Class I railroads $25-30B). Heuristic 7 says absence-of-mention there alone is not dispositive.
- **M:** Zero counterparty mentions of Ondas / FullMAX / Airobotics in defense primes or Class I railroads. Customer identity not disclosed.
- **Gap:** Unnamed anchor customer + 73% A/R concentration = collection risk + customer-disclosure-quality flag. Not a hard contradiction but a watch item.
- **Falsification:** Resolved if 2026 10-K names the anchor customer AND the receivables are collected. Confirmed if 2026 10-Q discloses A/R write-down or anchor customer loss.

---

## RCAT (Red Cat Holdings) — Composite 0.83, 2 SEVERE

### Signal RCAT-1 — SEVERE_UNDERDELIVERY
- **R:** "Teal selected as winner of U.S. Army Short Range Reconnaissance (SRR) Program of Record (Nov 2024); FY2025 revenue growth attributed primarily to scaling drone deliveries under SRR program." Total FY2025 revenue $40.7M, with ~73% (~$29.7M) attributed to US Government.
- **f:** Companies fulfilling deliveries under a named DoD Program of Record should show contract obligations in USAspending matching or exceeding the revenue attributed to that program.
- **M:** USAspending DoD obligations across all RCAT recipient name variants (Red Cat Holdings, Teal Drones, FlightWave, Skypersonic): **~$4.9M total lifetime DoD obligations** (Teal $2.17M + FlightWave $2.30M + Red Cat $0.47M, 2020-2026). Including non-DoD federal: ~$7M. No award descriptions reference "Short Range Reconnaissance" or "Program of Record." Largest single award is $750K.
- **Gap:** ~6x divergence between claimed FY25 government revenue (~$29.7M) and observable lifetime DoD obligations across all subsidiaries (~$4.9M).
- **Caveat (calibration heuristic):** SRR program selection was only ~14 months before cutoff. Award-data visibility can lag program selection by 6-12 months, and SRR deliveries may flow through DLA, DIU Blue UAS Marketplace, or prime contracts rather than appearing under RCAT's name. Skydio (closest SRR competitor) returns a similar $1.9M / 20 awards baseline — consistent with the small-tactical-UAS category systematically undercounting at recipient-direct search. Scored **SEVERE not RED** because of this lag.
- **Falsification:** If by 2027-05-16 USAspending shows ≥$25M cumulative DoD obligations to RCAT subsidiaries with descriptions referencing SRR or Teal Drones deliveries, signal is wrong.

### Signal RCAT-2 — SEVERE_UNDERDELIVERY
- **R:** Same revenue claim; the "73% from US Gov" attribution implies ~$29.7M of US Government revenue across the consolidated subsidiary set.
- **f:** Same as RCAT-1.
- **M:** Same as RCAT-1 — only $4.9M lifetime DoD obligations.
- **Gap:** Same as RCAT-1; this is the subsidiary-level decomposition of the consolidated divergence.
- **Falsification:** Same as RCAT-1.

### Signal RCAT-3 — MODERATE_UNDERDELIVERY
- **R:** FlightWave acquisition includes $8.7M of goodwill ascribed to "approved vendor relationships with several US government agencies."
- **f:** "Approved vendor relationship" goodwill should be substantiated by historical USAspending obligations to FlightWave commensurate with the assigned value. Rule of thumb (per subagent-discovered process rule): goodwill / acquiree-lifetime-USAspending ratio >>1 is a stretched-PPA flag.
- **M:** FlightWave lifetime DoD obligations: $2.3M total.
- **Gap:** $8.7M / $2.3M = **3.8x ratio.** PPA values the "approved vendor" relationships at 3.8x what FlightWave has ever billed the government.
- **Falsification:** If by 2027-05-16 FlightWave produces ≥$8.7M in incremental government revenue OR RCAT does not impair the goodwill at year-end, signal is unchanged but pending. Goodwill impairment in next 10-K confirms.

---

## AIRO (AIRO Group Holdings) — Composite 0.75, 1 RED_FLAG

### Signal AIRO-1 — RED_FLAG_NEGATIVE (composite, financial-statement-disclosure-based)
- **R:** Multiple internal accounting / governance disclosures that together constitute a stock-for-services + roll-up distress fingerprint:
  - Vendor / contingent payables converted to equity at IPO across 5+ subsidiaries: Jaunt $44.6M → 1.12M shares; Aspen Bridge $17.5M → 440K shares; Coastal Defense $2M → 203K shares.
  - Investor Notes accruing interest at 100-150% of principal payable in stock.
  - 20% of Sky-Watch EBITDA payable to single stockholder (Dangroup, $5.7M expense 2025).
  - Material weaknesses in ICFR disclosed since FY2023; CEO/CFO concluded controls NOT effective. Unremediated.
  - Operating cash flow swung from +$21.5M to -$32.4M year-over-year.
  - 79% of revenue from 2 customers.
  - Goodwill is 74% of total assets ($571.7M); $38M impairment 2024, no impairment 2025.
  - Electric Air Mobility segment: $0 revenue / $7.6M R&D.
  - Accumulated deficit: $210.6M.
- **f:** None of these disclosures individually proves wrongdoing, but the combination matches the SRFM-Palantir / LILM stock-for-services distress fingerprint (`feedback_stock_for_services_flag.md`). Companies converting vendor payables to equity at IPO, accruing interest at 100-150% in stock, and disclosing unremediated ICFR weaknesses have an elevated rate of subsequent reverse splits, dilutive raises, going-concern qualifiers, and (in some cases) restatements.
- **M:** Self-disclosure — no external M-source needed; the divergence is between the company's narrative of "consolidated defense platform via 4 acquisitions" and the financial-statement disclosure of "operating cash outflow + ICFR weak + goodwill 74% of assets + investor notes at 100-150% in stock."
- **Gap:** The IPO narrative ("we just consolidated 4 strong defense subsidiaries") does not reconcile with the financial reality ("the subsidiaries had vendor payables we settled in equity at IPO, our internal controls are not effective, our cash burn is accelerating, and 74% of our balance sheet is goodwill").
- **Falsification:** If by 2027-05-16 AIRO has (a) remediated ICFR, (b) operating cash flow positive, (c) goodwill not impaired in next 10-K, (d) Sky-Watch Dangroup payments terminated or capped, the signal is wrong.

### Signal AIRO-2 — UNVERIFIABLE (note for posterity)
- **R:** Coastal Defense Inc has $5.7B IDIQ.
- **f:** IDIQ ceiling ≠ obligated dollars; per Calibration Heuristic 10 the M_value should record both.
- **M:** USAspending: 470 DoD task orders / **$23.6M obligated** to Coastal Defense on ISR/JTAC parent IDIQs H9224016D0028 and N0042119D0059. Real underlying business.
- **Gap:** Headline "$5.7B" implies ~250x more revenue than the $23.6M actually obligated. Disclosure technically true (IDIQ ceiling) but misleading. Scored PASS on the underlying-claim verification; flagged here for disclosure-quality context.

---

## UMAC (Unusual Machines) — Composite 0.00, no material flags

No material signals. UMAC is a component supplier B2B to drone OEMs (correctly applies the component-supplier vs prime calibration), has 6 granted patents across UMAC + Fat Shark in-domain, has bi-directional related-party disclosure with Red Cat (UMAC mentioned in 52 of Red Cat's EDGAR filings).

Watch items (not flagged):
- $300M ATM is 3x current cash — planned-dilution appetite
- Related-party concentration with Red Cat (vendor of acquired assets is now also customer)
- Headcount grew 18 → 141 in one year; $5.8M CEO stock comp in 2025

---

## KTOS (Kratos Defense & Security) — Composite 0.00, no material flags

Validates as the control. 242 DoD contracts / $1.67B (2023-2026) across documented subsidiary name set (KUAS, KTTS, KSMDS, KS1, Micro Systems). XQ-58 Valkyrie / BQM-167 / BQM-177 / Skyborg lineage explicitly contracted. 68 granted patents across Kratos parent + Florida Turbine subsidiary, 41 satellite/comms + 10 microwave/RF title hits. EPA FRS confirms 6 CA + 2 AL facilities. GE Aerospace 8-K (2026-04-21) mentions Kratos — corroborates the June 2025 GE-Kratos teaming announcement.

Only UNVERIFIABLE: Sentinel ICBM facility claim — Northrop Grumman (Sentinel prime) does not name Kratos in EDGAR, but per Heuristic 7 sub-tier disclosure is not expected; classification of as investment-stage facility ("establishment of a new facility") supports UNVERIFIABLE rather than RED.

---

## Summary table

| Ticker | Signal | Severity | R-side claim | M-side check | Gap shape |
|---|---|---|---|---|---|
| ONDS | ONDS-1 | RED | "defense, HLS, PS customer base" | USAspending federal contracts | 0 contracts |
| ONDS | ONDS-2 | SEVERE | "Class I railroads adopting FullMAX over 8 years" | EDGAR fulltext in 7 Class I railroad CIKs + Wabtec | 0 mentions across all 7 |
| ONDS | ONDS-3 | RED | "Sentrycs / Roboteam pitched to US DoD" | USAspending federal contracts for both | 0 contracts each |
| ONDS | ONDS-4 | MOD | "55% revenue from anchor customer; 73% A/R" | EDGAR counterparty disclosure | unnamed, no corroboration |
| RCAT | RCAT-1 | SEVERE | "~$29.7M FY25 US Gov revenue from SRR PoR" | USAspending DoD across subsidiaries | $4.9M lifetime → 6x gap |
| RCAT | RCAT-2 | SEVERE | Same revenue claim at subsidiary level | Same M | Same 6x gap |
| RCAT | RCAT-3 | MOD | "$8.7M FlightWave goodwill = approved vendor relationships" | FlightWave USAspending lifetime | $2.3M lifetime → 3.8x ratio |
| AIRO | AIRO-1 | RED | "consolidated 4 strong defense subsidiaries via IPO" | Self-disclosed financial statements | stock-for-services + ICFR weak + 74% goodwill + cash swing |
| UMAC | — | PASS | (no material claims fired) | various | — |
| KTOS | — | PASS | (no material claims fired) | various | — |

## How to read this

Each RED_FLAG_NEGATIVE is a falsifiable bet that the M-side absence will eventually be reflected in either (a) a stock-price re-rating, (b) a company restatement, or (c) third-party identification (short-seller report, journalist piece, regulatory action). Each SEVERE_UNDERDELIVERY is a softer bet on the same shape with more room for the company to bridge the gap via post-cutoff visibility of program flow-through. Each MODERATE is a watch item.

None of these is a fraud accusation. They are specific, dated, falsifiable claim-vs-evidence divergences at the cutoff. The full subagent rationales and supporting query payloads are in `data/_local/{TICKER}.scores.json`.
