# HUMAN OBSERVER BRIEF — what a person can see that the feeds cannot
**2026-08-23 · principal-directed inversion: "given what the market doesn't know now, what can a human observer tell the desk?"**

The v1.7 pre-mortems catalog our tripwire-less unknowns — the failure modes with no sensor. That
catalog IS the field brief: wherever the desk wrote "no feed watches this," a human observation is
the only instrument that exists. This document maps each live unknown to the observation that
resolves it, pre-registers the interpretation (so we can't rationalize after the fact), and sets
the ingestion protocol.

## PROTOCOL (how an observation enters the system)
1. **Log it**: desk/data/human_observations.jsonl — {date, place, observation, position, unknown_resolved,
   direction: CONFIRMS_KILL | DISCONFIRMS_KILL | NEUTRAL, pre_registered: yes/no}. Verbal to the desk
   in chat is fine; the desk writes the row.
2. **Disconfirmation-first**: each entry below states the observation that would HURT our position.
   Go looking for that one. A brief that only collects comfort is marketing.
3. **n-of-1 discount**: a single observation moves TIMING and SIZING through existing gates only
   (tranche pause, add-gate hold, alert tightening). Repeated independent observations, or one that
   directly witnesses a named kill variable, trigger a COURT — never an order.
4. **Absence is observation**: "I looked and the thing wasn't there" gets logged with the same weight.
5. **Hygiene rail**: public-domain scuttlebutt only — shelf space, foot traffic, open professional
   chatter, streamed proceedings, your own org's procurement. Never solicit confidential specifics;
   if someone volunteers something that smells nonpublic-material about a listed company, it does NOT
   enter the ledger and the desk is told only "tainted, name+date" so the name can be frozen.

## TIER 1 — named tripwire-less unknowns (feeds blind; a person is the only sensor)

### BLDR — competitor pricing / builder-direct procurement
- **Our blind spot (pre-mortem #1 verbatim):** "No feed watches competitor pricing... truth arrives with the FY27 10-K."
- **The observation:** any GC, framer, or purchasing manager: "Who's quoting cheapest on lumber
  packages/trusses right now — Builders FirstSource, 84 Lumber, US LBM? Are quotes getting
  aggressive? Any builders buying direct from mills?"
- **Pre-registered:** aggressive-BFS-discounting or builder-direct chatter = CONFIRMS red's price
  mechanism → skip/exit stands regardless of the 10/29 print. "Everyone's quoting the same, volume
  is just dead" = the curve story, ahead of the print.

### 6824.T (New Cosmos) — the NYC compliance wave, on the actual shelves
- **Our blind spot:** kill = "compliance wave split across four certified manufacturers at commodity
  prices." Brand share during an install wave is invisible to every feed we run.
- **The observation:** anyone in NYC: which brands of natural-gas alarms sit on hardware-store
  shelves / appear in building-lobby compliance notices / get named by supers? New Cosmos (DeNova
  Detect) vs the other certified makers; and are they $40 commodities or $80+ devices?
- **Pre-registered:** shelf dominated by others at commodity prices = CONFIRMS the split-wave kill →
  hold at one lot, no adds. DeNova visibly winning installs = the add-gate's real-world leg.

### WAL + AI-break ensemble — fund-finance stress, heard before it prints
- **Our blind spot:** WAL's kill-class is the NDFI book (lending to levered funds); the AI-break
  contagion transmits through exactly this channel. No feed hears credit-fund CFOs.
- **The observation (the principal's own network is the instrument):** among fund CFOs/GPs — are
  NAV-facility and sub-line terms tightening? Any margin-call or borrowing-base-dispute chatter?
  Separately, in AI-adjacent tech: is enterprise AI spend renewing or shelfware? GPU commitments vs
  utilization? Recruiting freezes at AI startups?
- **Pre-registered:** fund-finance stress chatter = tighten WAL kill-trigger review cadence
  (weekly→daily call-report watch) + counts as evidence at the quarterly AI-break re-freeze. The
  ensemble p (frozen 0.45) is the ONE book-level number a pattern of human observations may
  legitimately move — via the re-freeze, sizing XND tranche 3.

### MBI — the 9/15 First Circuit oral argument, listened to by a human
- **Our blind spot:** the opinion is undated; the ruling said 9/15 is "non-resolving." But argument
  audio is public, and judge questioning TONE is exactly what no scraper reads.
- **The observation:** stream the argument (First Circuit posts audio). Which side gets the hostile
  hypotheticals? Does the panel probe remedies (a tell for reversal) or standing/procedure (a tell
  for affirmance)?
- **Pre-registered:** remedy-focused questioning = DISCONFIRMS the affirmance kill → tranche-2 prep
  (after the National statutory filing is read). Hostile-to-appellant = hold floor size, tighten the
  <$4 alert.

### CTMX — the conference floor and the tox question
- **Our blind spot (pre-mortem verbatim):** Merck's unpublished expansion data "exists today in a
  database we cannot see." Second-order: whether oncologists consider EpCAM-ADC diarrhea manageable
  in practice.
- **The observation:** any oncology contact / conference attendance (ESMO Oct): KOL tone on CX-2051
  tox management; any whisper of M9140 expansion-cohort results; site-staff enrollment pace talk.
- **Pre-registered:** "the diarrhea is a real clinic problem" from practitioners = CONFIRMS the tox
  kill early → pause tranches. M9140 expansion whispers >15% ORR = the size-gate re-opens the other
  way → court before tranche 3.

## TIER 2 — consumer/channel positions (classic scuttlebutt, high signal-per-effort)
- **ONON (held, core target):** running-store wall share + promo depth. Pre-registered: On wall
  space shrinking or >30%-off promos spreading = deceleration ahead of the print → pause the
  accumulate-≤$36 ladder. (Absence of promos = the carry case, logged.)
- **BKE/SBH/NATR (held):** mall-store traffic and staffing on a Saturday; promo cadence. Confirmed
  dead malls = these stay carry-size forever.
- **EOLS (band 5.55):** medspa price boards — Jeuveau vs Botox pricing/promos; "which tox do you
  push?" chatter. Aggressive Jeuveau discounting = margin kill confirmation before any fill.
- **MNSO (8/28 pack):** any Miniso store — traffic, IP-collab merchandising freshness, markdown
  bins. Feeds the 8/28 print-gate read.
- **Software sleeve (NOW/SAP/MNDY/HUBS + ai_sass_dislocation):** your own org and peers — are
  AI agents actually displacing SaaS seats at renewal, or is that still deck-talk? Seat-count
  chatter at renewal time is the sleeve's entire thesis, humanly observable quarterly.
- **APP/LFTO:** app-developer contacts on ad-network pricing and AXON e-comm performance vs Meta —
  tests the code-P add-gate's real-world leg.

## TIER 3 — structural/situational (lower frequency, still mapped)
- **PPHC:** DC chatter — which firms are winning new mandates; Tancredi/Advocacy Partners retention
  of principals (the roll-up's real risk is rainmakers walking; no feed sees it pre-K).
- **BAVA:** travel-clinic stocking of Vimkunya; any public-health contact on ACIP/MMWR process.
  MMWR publication = the named US-policy tail resolving, humanly noticeable before we'd scrape it.
- **CIFR/IREN (gated):** datacenter/power-developer chatter on PPA rates and GPU-hosting pricing —
  feeds the CIFR ≤12.50 reopen and the hyperscaler-JV kill variable.
- **Muni wantlist (CA districts):** local-paper/board-meeting noise on enrollment declines and
  parcel-tax fights in named districts — the scanner reads filings; humans hear board meetings.
- **SLS: honest null.** Blinded trial, binary readout — there is no legitimate human observable.
  Anyone claiming one is offering either noise or a problem.

## WHAT THIS CANNOT DO
Move a verdict. Observations are evidence into courts and gates — they pause tranches, tighten
alerts, re-time adds, and feed re-freezes. The court still rules; the doctrine still gates; a
story from one lumberyard is a data point, not a thesis.

## TIER 0 — FRONT-RUN THE FENCE (added 2026-08-23, principal-directed)
WAIT/gated names with dated resolvers and pre-committed entry actions: an early human answer converts
directly into position via existing gates (early court on the observation as evidence). Ranked by
imminence x observability:

| Name | Gate/resolver | The ask | Pre-registered |
|---|---|---|---|
| TSSI | Dell read-through 9/01 -> ~550sh starter | Enterprise infra buyers: "Dell AI-rack lead times — stretching or normalizing?" | Stretching = early court, stage BEFORE the print; push-outs = gate failing, stand down free. ALT-DATA PRIOR 8/24: FINRA shorts -7.5% into the event (DTC 5.5), discovery UNDISCOVERED, TSS production reqs active in Georgetown — rails mildly confirm; your lead-time answer is the discriminator |
| MNSO | 8/28 print pack (GM>=43.3) | Any Miniso store: markdown-bin depth + IP-collab freshness | Fresh-at-full-price = gate likely clears; deep clearance = margin gate failing. ALT-DATA PRIOR 8/24: store-manager hiring 3->22/mo May->Aug (CA cluster) = openings accelerating, SG&A gate pressured; the CURRENT collab to check is Toca Boca; customs consignee rail is Cloudflare-blocked — your eyes are the sell-in sensor |
| FA | Post-lockup re-court 9/10+; unlitigated AI price-per-screen | HR-ops/talent: "Are Checkr-class AI screeners undercutting at renewal? Did you switch?" | "Switched, saved big" = structural kill input; "looked and stayed" = incumbency holds, FV input for re-court |
| NTLA | Band 10.75-11.75 resting below tape | Allergists/immunologists: "Would your HAE patients take one-time gene editing over dailies?" | Enthusiasm = band is a gift, tranche-2 conviction; "orals are fine" = peak-sales kill confirmed, band is fair not cheap |
| TPG | Defer-on-pack; Sept 8-K | LP/placement chatter: how are TPG flagships raising? | Strong raise = FRE case builds pre-8-K; struggling = defer stands |
| HLI | Conditional 44@113 (fills only on bad news) | Restructuring bankers/credit lawyers: pipeline building? | Pipeline boom + gate fills = GOOD fill (countercyclical revenue); no pipeline + fills anyway = adverse selection, re-court before the fill stands |
| CIFR | Reopens <=12.50; kill var = 1st hyperscaler JV | DC/power developers: who's hungry for energized ERCOT sites? | Named hunger = reopen-readiness court early; silence = gate stays |
| DOCS | Re-court ~11/5; build-vs-degradation unresolved | Pharma marketing: 2027 Doximity ad budgets (fall planning season) | Budgets up = the one starter-creating fact, ahead of the print |

Same rails as all tiers: pre-registered before looking, disconfirmation logged with equal weight,
n-of-1 moves timing via courts not orders, MNPI hygiene absolute.

## V2 BOARD — FALSIFIABLE PREDICTIONS WITH REAL-WORLD OBSERVABLES (added 2026-08-30)
Every row: a frozen desk claim + the physical observation that proves or kills it + who observes.
Pre-registered both directions per protocol; log to human_observations.jsonl.

### Desk-observable (connectors / public physical data)
| Prediction | Observable | Falsifier | When |
|---|---|---|---|
| CIFR Barber Lake is physically ramping (hiring says contractor fit-out live) | Sentinel-2 NDBI at the PERMITTED pad vs 2024 baseline (first pass 8/30: NDBI +0.025, veg −0.067 at approx pad, scenes thru 11/25) | flat NDBI on a summer-2026 scene = hiring is for a shell | pre-11/02 gate |
| TTI builds the Arkansas plant it guided ($607M NPV) | El Dorado/Magnolia job postings appear BEFORE startup guided ≤6mo out (baseline = zero, recorded) | startup guided with hiring still zero | monthly |
| XE lockup supply pulls forward via the early-release clause | Form 144 cluster in LATE SEPT (EDGAR, public) instead of post-10/20 | no cluster before 10/20 | daily watch |
| Macau wallet-substitution reversal (frozen 0.72) | DICJ August GGR > +1.3% | print at/below the bar | Tue 9/1 |
| CRWV is the credit canary (ensemble 0.45) | insider Form-4 cadence, posting freezes, credit marks — all public | tells normalize while capex holds | rolling |
| MNSO S&D ramp is structural expansion | new Bay Area store openings materialize (manager hiring 3→22/mo predicted them) | hiring wave with no openings = misread | by year-end |

### Principal-observable (your legwork; the desk cannot see these)
| Prediction | Your observation | Pre-registered read | Gates |
|---|---|---|---|
| ONON deceleration (trim ruling) | running-store walk: wall share + >30% promos | promos spreading = confirmed → conditional add stays dead; clean walls = re-court the trim | the ≤$26 add |
| WAL NDFI tail transmits fund-finance stress | fund-CFO network: NAV-facility/sub-line terms tightening? | tightening = daily call-report watch + ensemble re-freeze input | WAL sizing |
| HLI conditional fill quality | restructuring bankers: pipeline building? | pipeline + fill = good fill; no pipeline + fill = adverse selection, re-court | the 44@113 |
| DOCU-class AI seat erosion | your org + peers at renewal: agents replacing seats or deck-talk? | erosion real = the RP_UNCERTAIN ceiling is right everywhere | software sleeve |
| New Cosmos NYC compliance wave | NYC hardware shelves / lobby notices: DeNova vs commodity brands | commodity-split = kill confirmed | 6824.T adds |

## V3 addition (2026-09-01): OpenAI ad-channel observables
12. **Who advertises in YOUR ChatGPT** (principal-observable, pre-registered): log brand + category of ads seen in
    personal ChatGPT sessions weekly. PREDICTION: if the channel is in land-grab phase, the mix should be
    performance/long-tail heavy (DTC, lead-gen, marketplaces) NOW, shifting toward brand budgets (CPG, auto) within
    2-3 quarters. Brand-heavy NOW = disconfirms the underpriced-arbitrage thesis (channel already mature).
13. **OpenAI ads page case studies** (desk-observable, weekly fetch): named advertisers on openai.com/ads.
    Baseline 2026-09-01: Newegg (+ HarborWest hero). Each new named advertiser = channel-adoption datapoint;
    a named INSURANCE or LEGAL advertiser directly grades the QNST court thesis.

14. **SHOP-vs-AMZN personal purchase split** (principal-observable, pre-registered 2026-09-01): the principal routes ~all purchases through Shopify-merchant checkouts vs Amazon. Log the monthly split (rough count). PREDICTION: if the product-superiority thesis is real and generalizing, aggregate evidence (Shop app ranks, GMV share) should move the same direction; a personal reversion to AMZN = early disconfirmation tell.
