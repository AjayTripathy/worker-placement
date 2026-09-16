# RIPO-Cohort — Blinded R/f(M) Diligencer Forward Test

_Generated 2026-05-30T03:55:58.189801Z_

## Methodology

25 names that the Renaissance IPO ETF actually held AND appear in the survivorship-free 2024-25 primary-IPO backtest. Each scored by an isolated, **blinded** subagent (no outcome labels, no WebSearch/WebFetch, per-name cutoff = IPO date) reading ONLY the IPO prospectus. R (claim in the S-1/F-1/424B4) − f(M, independent registry: USPTO / USAspending / EPA FRS / ClinicalTrials / openFDA / EDGAR full-text counterparty disclosure).

**The question:** within RIPO's already-vetted picks, does composite severity separate the 3 catastrophes (PACS, VG, CHYM) from the 22 survivors? This is the test the buyside_dd structural-screen backtest could not run.

## Composite ranking (OUTCOMES REVEALED)

Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MOD=1, SEVE=2, RED=3).

| Rank | Ticker | Company | Claims | PASS | MOD | SEVE | RED | UNV | Composite | Outcome |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | RDDT | Reddit, Inc. | 7 | 1 | 1 | 0 | 0 | 5 | 0.50 | SURVIVOR |
| 2 | TTAN | ServiceTitan, Inc. | 7 | 1 | 1 | 0 | 0 | 5 | 0.50 | SURVIVOR |
| 3 | CRWV | CoreWeave, Inc. | 7 | 3 | 2 | 0 | 0 | 2 | 0.40 | SURVIVOR |
| 4 | AS | Amer Sports, Inc. | 8 | 2 | 1 | 0 | 0 | 5 | 0.33 | SURVIVOR |
| 5 | TEM | Tempus AI, Inc. | 8 | 4 | 2 | 0 | 0 | 2 | 0.33 | SURVIVOR |
| 6 | LB | LandBridge Co LLC | 7 | 2 | 1 | 0 | 0 | 4 | 0.33 | SURVIVOR |
| 7 | SARO | StandardAero, Inc. | 7 | 4 | 2 | 0 | 0 | 1 | 0.33 | SURVIVOR |
| 8 | SAIL | SailPoint, Inc. | 8 | 3 | 1 | 0 | 0 | 4 | 0.25 | SURVIVOR |
| 9 | LINE | Lineage, Inc. | 6 | 4 | 1 | 0 | 0 | 1 | 0.20 | SURVIVOR |
| 10 | VG | Venture Global, Inc. | 7 | 5 | 1 | 0 | 0 | 1 | 0.17 | **CATASTROPHE** |
| 11 | BTSG | BrightSpring Health Services,  | 7 | 4 | 0 | 0 | 0 | 3 | 0.00 | SURVIVOR |
| 12 | ALAB | Astera Labs, Inc. | 6 | 2 | 0 | 0 | 0 | 4 | 0.00 | SURVIVOR |
| 13 | PACS | PACS Group, Inc. | 7 | 1 | 0 | 0 | 0 | 6 | 0.00 | **CATASTROPHE** |
| 14 | ULS | UL Solutions Inc. | 6 | 4 | 0 | 0 | 0 | 2 | 0.00 | SURVIVOR |
| 15 | LOAR | Loar Holdings Inc. | 6 | 4 | 0 | 0 | 0 | 2 | 0.00 | SURVIVOR |
| 16 | RBRK | Rubrik, Inc. | 6 | 1 | 0 | 0 | 0 | 5 | 0.00 | SURVIVOR |
| 17 | VIK | Viking Holdings Ltd | 7 | 2 | 0 | 0 | 0 | 5 | 0.00 | SURVIVOR |
| 18 | ZEEKR | ZEEKR Intelligent Technology H | 7 | 2 | 0 | 0 | 0 | 5 | 0.00 | MERGER_CASHOUT |
| 19 | WAY | Waystar Holding Corp. | 7 | 2 | 0 | 0 | 0 | 5 | 0.00 | SURVIVOR |
| 20 | ONESTREAM | OneStream, Inc. | 7 | 2 | 0 | 0 | 0 | 5 | 0.00 | MERGER_CASHOUT |
| 21 | PONY | Pony AI Inc. | 6 | 2 | 0 | 0 | 0 | 4 | 0.00 | SURVIVOR |
| 22 | KRMN | Karman Holdings Inc. | 6 | 5 | 0 | 0 | 0 | 1 | 0.00 | SURVIVOR |
| 23 | CRCL | Circle Internet Group, Inc. | 7 | 4 | 0 | 0 | 0 | 3 | 0.00 | SURVIVOR |
| 24 | CHYM | Chime Financial, Inc. | 8 | 3 | 0 | 0 | 0 | 5 | 0.00 | **CATASTROPHE** |
| 25 | CAI | Caris Life Sciences, Inc. | 7 | 5 | 0 | 0 | 0 | 2 | 0.00 | SURVIVOR |

## Discrimination

- Catastrophes: ['VG', 'PACS', 'CHYM']
- Mean composite — catastrophes **0.056** vs survivors **0.159**
- Mean RED flags — catastrophes **0.0** vs survivors **0.0**
- Catastrophe ranks by composite (1=highest severity): **[10, 13, 24]** of 25
- Precision@k (exclude top-3 by composite): caught 0/3 catastrophes vs random expectation 0.36

## Per-ticker findings (RED / SEVERE / MODERATE)

### RDDT — Reddit, Inc.  (composite 0.50)

- **[MODERATE_UNDERDELIVERY] RDDT-4** — Reddit's data advantage and intellectual property are a key competitive asset, and the Revolving Credit Facility is secured by liens on substantially all assets including intellectual property assets.
  - M: `uspto_odp.query_assignee('Reddit', cutoff 2024-03-21)` → n_total_applications=2, n_granted (pre-cutoff)=1; only filing is a single provisional/non-provisional pair titled 'Decentralized Social-Media Platform'
  - USPTO shows an essentially empty patent portfolio at the IPO date. However, Reddit's IP claim is explicitly grounded in its DATA CORPUS and trademarks, not a patent estate — the prospectus never asserts a large patent count, so this is NOT the Nikola pattern (CALIBRATION heuristic 7). The thin paten

### TTAN — ServiceTitan, Inc.  (composite 0.50)

- **[MODERATE_UNDERDELIVERY] TTAN-1** — ServiceTitan holds 14 issued U.S. patents (plus 4 issued foreign, 9 U.S. applications) protecting its trades-software technology.
  - M: `uspto_odp.query_assignee(assignee_name='ServiceTitan', cutoff_date='2024-12-12')` → n_total_applications=29, n_granted=7 pre-cutoff. Granted patents (e.g. 12154146 'Automated Customer Review Matching', granted 2024-11-26; 'Systems and Methods for Dynamic Pricing' Notice of Allowance)
  - Partial corroboration. Genuine granted IP exists and is on-thesis (pricing, scheduling, recommendation, review-matching ML), so this is NOT a Nikola-pattern fabrication. But the USPTO ODP single-token firstApplicantName index surfaces only 7 granted patents vs the 14 issued U.S. patents claimed. The

### CRWV — CoreWeave, Inc.  (composite 0.40)

- **[MODERATE_UNDERDELIVERY] CRWV-1** — Microsoft was CoreWeave's largest customer, 62% of 2024 revenue ($1.2B recognized), under a Feb 2023 Microsoft MSA.
  - M: `edgar_fts CoreWeave in Microsoft (CIK 0000789019) filings; megacap_namecheck Microsoft subset` → Microsoft filings: 0 mentions of CoreWeave (10-K/10-Q/8-K, full history). megacap_namecheck Microsoft total_hits=0.
  - The buyer (Microsoft) never names CoreWeave in its SEC filings despite CoreWeave booking 62% of its revenue ($1.2B) from Microsoft. Per Heuristic 5, this asymmetry is benign-explainable: $1.2B of cloud spend is immaterial to Microsoft's ~$245B revenue, so non-disclosure by the buyer is expected and 
- **[MODERATE_UNDERDELIVERY] CRWV-6** — Names AI customers Cohere, Mistral AI, OpenAI, Replicate, and enterprise customers Meta, IBM, Microsoft, Jane Street.
  - M: `edgar_fts CoreWeave in NVIDIA filings; megacap_namecheck (Microsoft, Meta, IBM subset)` → Megacap-side: Microsoft 0, Meta 0, NVIDIA 3 mentions of CoreWeave. Most named customers (Cohere, Mistral AI, OpenAI, Replicate, Jane Street) are private and file no SEC reports, so no counterparty dis
  - The named-customer list is a mix of private AI labs (Cohere, Mistral, OpenAI, Replicate — no registry footprint, UNVERIFIABLE individually) and public megacaps (Meta, IBM, Microsoft) that do NOT name CoreWeave in their filings. Per Heuristic 5, a hyperscaler/enterprise naming a cloud SUPPLIER is rar

### AS — Amer Sports, Inc.  (composite 0.33)

- **[MODERATE_UNDERDELIVERY] AS-8** — The Company restated its FY2022/2021/2020 financials to correct misstatements and is highly levered (~EUR 2bn institutional term loan + ~EUR 4bn related-party shareholder loans), with recurring net lo
  - M: `Internal financial-statement disclosure (audited KPMG report + MD&A in the 424B4); going-concern read from prospectus.` → Auditor (KPMG AB) report explicitly states FY2020-2022 statements were RESTATED to correct misstatements. Recurring net losses: -252.7 (2022), -126.3 (2021), -237.2 (2020); -113.9 nine-mo 2023. Total 
  - These are honestly and prominently DISCLOSED negatives (restatement, leverage, losses), not concealed — consistent with the honesty-alpha framework (disclosed bad news is not a lie). The IPO is structured to deleverage via shareholder-loan equitization and proceeds repayment. Scored MODERATE_UNDERDE

### TEM — Tempus AI, Inc.  (composite 0.33)

- **[MODERATE_UNDERDELIVERY] TEM-4** — Tempus's TIME Trial program (launched June 2019) has more than 230 clinical trials signed into the network, with more than 30,000 patients.
  - M: `clinical_trials.query_by_lead_sponsor(Tempus, cutoff 2024-06-17)` → ClinicalTrials.gov shows Tempus AI as LEAD SPONSOR on only 7 pre-cutoff studies (13 total in registry). The '>230 clinical trials signed into the network' refers to trials Tempus MATCHES patients into
  - Heuristic: the registry confirms Tempus AI is a genuine, active clinical-trial participant (7 sponsored + AstraZeneca/GSK collaborators), which is consistent with operating a trial-matching network. But the specific '>230 trials in network' is a network-participation metric ClinicalTrials.gov's lead
- **[MODERATE_UNDERDELIVERY] TEM-6** — Tempus's offerings have been used by approximately 95% of the largest public pharmaceutical companies based on 2023 revenue.
  - M: `clinical_trials.query_by_lead_sponsor(Tempus) collaborators + edgar_fts(Tempus)` → ClinicalTrials.gov surfaces AstraZeneca + GlaxoSmithKline as Tempus AI trial collaborators (2 of the largest global pharmas) — direct evidence of multiple top-pharma relationships. EDGAR full-text 'Te
  - The registry confirms at least two top-tier pharma customers/collaborators (AZ, GSK), so the claim's direction is corroborated, but '~95% of the largest public pharma companies' is a marketing-penetration metric no federal registry can verify or refute (pharma B2B data licenses are not separately di

### LB — LandBridge Co LLC  (composite 0.33)

- **[MODERATE_UNDERDELIVERY] LB-1** — Desert Environmental developed two non-hazardous oilfield reclamation and solid waste disposal facilities on LandBridge's land, completed/operational in Q1 2024.
  - M: `epa_frs.query_facilities facility_name='Desert Environmental' (and broad 'Desert' / 'reclamation' / 'oilfield') in TX and NM, filtered to Delaware-Basin counties (Loving/Winkler/Reeves/Pecos/Ward/Andrews/Lea).` → 0 facilities registered under 'Desert Environmental' in TX or NM. Broad 'Desert' substring returns 68 TX noise hits, none matching a Desert Environmental waste/reclamation site in the relevant Permian
  - Affiliate-operated non-hazardous oilfield reclamation/solid-waste facilities claimed completed only in Q1 2024. EPA FRS does cover oilfield-waste/landfill sites, so a permitted facility would be expected to appear eventually, but FRS registration commonly lags a few months for newly-completed sites 

### SARO — StandardAero, Inc.  (composite 0.33)

- **[MODERATE_UNDERDELIVERY] SARO-5** — In March 2023 StandardAero became the first and only independent aftermarket provider in North America to join CFM's authorized service network for LEAP-1A/-1B via a CFM Branded Service Agreement (CBS
  - M: `edgar_fts StandardAero @ GE/CFM CIK 0000040545; edgar_fts StandardAero all-filers` → GE direct-CIK mention of 'StandardAero' = 0 hits. All-filer EDGAR full-text = 156 hits across Woodward, Polaris, Audax Credit BDC and other filers — entity is real and widely referenced, but no filing
  - The CBSA is a private commercial OEM-authorization agreement that no federal registry records and that CFM/GE do not separately disclose in SEC filings (counterparty-disclosure absence is non-informative per Heuristic 5). Broad external validation of the company exists (156 filer mentions), but the 
- **[MODERATE_UNDERDELIVERY] SARO-6** — As of June 30, 2024 StandardAero holds OEM licenses/authorizations on over 40 key engine platforms from every major OEM including GE Aerospace, CFM, Pratt & Whitney, Rolls-Royce, Honeywell and Safran.
  - M: `edgar_fts StandardAero @ GE CIK 0000040545 and RTX/P&W CIK 0000101829; all-filer full-text` → GE = 0 hits; RTX/P&W = 0 hits for 'StandardAero'. All-filer = 156 hits (real entity). USAspending separately confirms GE/Honeywell/Rolls-Royce-platform military MRO (J85=GE, T56=Rolls-Royce/Allison, A
  - OEM authorization licenses are private contractual instruments; named OEMs do not enumerate their authorized MRO licensees in SEC filings, so 0 counterparty hits is non-informative (Heuristic 5). Indirect corroboration is strong: the DoD MRO award stream confirms StandardAero overhauls multiple OEMs

### SAIL — SailPoint, Inc.  (composite 0.25)

- **[MODERATE_UNDERDELIVERY] SAIL-3** — SailPoint counts half of the Fortune 500 and 25% of the Forbes Global 2000 as customers.
  - M: `edgar_fts.query_fulltext(search_term='SailPoint', forms='10-K')` → 129 total SailPoint mentions across SEC filers (10-K/etc.). The corpus confirms broad enterprise referencing of SailPoint as a vendor/IT-security provider, but the bulk of hits are SailPoint's own pre
  - Independent SEC full-text evidence confirms SailPoint is a real, widely-referenced enterprise vendor (consistent with deep large-enterprise penetration), so the directional claim is corroborated. But the precise 'half the Fortune 500 / 25% of Forbes Global 2000' figures cannot be verified against an

### LINE — Lineage, Inc.  (composite 0.20)

- **[MODERATE_UNDERDELIVERY] LINE-3** — World's largest temperature-controlled warehousing company; largest automated portfolio with 81 automated facilities.
  - M: `epa_frs.query_facilities — registry confirms scale (the 'largest' superlative) but does not record automation status, so the '81 automated facilities' sub-claim and the global-ranking superlative are not registry-recordable.` → EPA FRS confirms a dominant US facility footprint (consistent with 'largest'), but no registry attests automation counts or a global #1 ranking; those are self-asserted competitive claims.
  - Scale portion is registry-corroborated; the 'largest globally' superlative and the 81-automated-facilities count are only partially verifiable (no registry covers automation/ranking). Partial corroboration with no contradiction -> MODERATE on the discriminative sub-claims, not a distress signal.

### VG — Venture Global, Inc.  (composite 0.17)

- **[MODERATE_UNDERDELIVERY] VG-4** — Venture Global has long-term 20-year SPAs (offtake agreements) with named major counterparties including Shell and BP for LNG offtake from its terminals.
  - M: `edgar_fts.query_fulltext(search_term='Venture Global', cik='0001306965' [Shell]); edgar_fts.query_fulltext(search_term='Calcasieu', cik='0000313807' [BP]); all-filer corroboration` → Shell plc parent CIK 0001306965: 0 hits for 'Venture Global'. BP plc parent CIK 0000313807: 0 hits for 'Calcasieu'. All-filer ecosystem search corroborates the terminal/relationship breadth (183 hits 
  - The named offtakers (Shell, BP) are foreign-parent ADR filers whose US SEC filings do not separately disclose a single supply SPA — per Heuristic 5, a large buyer not naming one supply contract is the norm and not itself a contradiction. Offtake SPAs are commercially confidential and predate the IPO

## Caveats

- N=25 with only 3 catastrophes is statistically underpowered; read the separation as anecdote, not significance.
- The cohort skews software/fintech/crypto where registry M-sources have little to cross-check; heavy UNVERIFIABLE on those names is expected and is itself an honest result (the framework declines to opine rather than fabricating signal).
- PACS is a hard-event catastrophe whose PRICE recovered (+58%); a severity screen keyed to disclosure honesty may or may not flag it from the prospectus alone.
