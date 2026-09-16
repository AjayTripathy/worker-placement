# THE FULL POSITION MENU + L/S STRATEGY — $5M LANDING
**2026-08-21 · companion to DEPLOYMENT_RUNBOOK_5M_20260821.md (the runbook says HOW/WHEN; this says WHAT)**
Denominator after landing: ~$6.0M. Day-0 split: reserve ~$1.855M (SGOV, anti-correlated tax escrow),
deployable ~$3.2M, Parametric wash sweep before first buy. All positions below are PRE-RULED — nothing
here needs a new court to buy at its stated band; everything outside a band does.

---

## SLEEVE I — TLH QUALITY-CARRY CORE (31 names, $2.50M target; ~$261k already held → ~$2.24M to buy)
The primary landing vehicle under the EOY-2026 harvest amendment: slots first, weeks 1–3.
Ruled 8/02; bands refreshed at band-touches since. Status key: names are bought AT/BELOW band via
GTC ladders — anything >10% above band waits for its rotation trigger, not a chase.

| Name | Axis | Target | Held | Fill | Band / entry mechanics |
|---|---|---:|---:|---:|---|
| MC.PA | luxury | $120k | $0 | 0% | ceiling €520 / FV €572 |
| NOW | enterprise sw | $120k | $3k | 2% | ceiling $112 / FV $120 |
| ONON | consumer disc | $120k | $13k | 11% | accumulate ≤$36 / ceiling $40 |
| KNSL | insurance E&S | $120k | $14k | 12% | starter $322 GTC |
| WRB | insurance E&S | $120k | $11k | 9% | starter $71.50 GTC |
| XOM | energy major | $120k | $11k | 9% | staged $155 GTC |
| CAI | diagnostics | $110k | $12k | 11% | add $15–16 / ownable to $20 |
| MCK | hc distribution | $110k | $0 | 0% | ladder $785/$751/$720 |
| WAL | consumer credit | $110k | $52k | 47% | **CAPPED by principal 8/21** — no adds into weakness; 10/31 pack sets exits |
| EG | insurance | $110k | $20k | 18% | alert $350 |
| LDOS | gov services | $110k | $4k | 4% | add ≤$118 / FV $125–137 |
| SAP | enterprise sw | $100k | $14k | 14% | ceiling €156 / FV €175 |
| BKE | consumer disc | $100k | $4k | 4% | ladder $42/$41 |
| SU | energy major | $100k | $11k | 11% | ladder $64/$62.5/$61 |
| OMF | consumer credit | $90k | $13k | 14% | rung2 $60 |
| EQT | natgas | $90k | $5k | 6% | FV 42/58/75; CSP overlay live — no equity adds while short puts on |
| CI | managed care | $80k | $9k | 12% | starter $290 / add $265 / overshoot $250 |
| VRLA.PA | eu industrials | $80k | $8k | 10% | rung2 €17.20 resting |
| MNDY | enterprise sw | $70k | $10k | 14% | FV base $116 |
| HRTG | insurance P&C | $70k | $7k | 10% | stage ≤$28.50 |
| G | business svcs | $70k | $5k | 7% | filled $29; next rung on band re-derive |
| CTSH | IT services | $60k | $5k | 9% | add on confirmed guide-hold |
| 6804.T | japan value | $55k | $0 | 0% | band ¥2,550–2,700 |
| IBEX | business svcs | $45k | $6k | 13% | alert $30 |
| EOLS | aesthetics | $40k | $0 | 0% | base FV $9 / bear $3.80; GTC $5.55 resting |
| III | investment co | $40k | $6k | 15% | tranche1 $3.97 |
| NPB | consumer credit | $35k | $5k | 14% | alert $17 |
| SBH | personal care | $35k | $0 | 0% | RP_FAIR; re-open ~$12 dislocation |
| FSBW | consumer credit | $30k | $8k | 28% | band $40–44; GTC $40.50/$39 resting |
| NATR | staples | $30k | $5k | 17% | GTC $19.81 |
| VEL | specialty lender | $15k | $0 | 0% | GTC $16.50 / add $15.25 |

Harvest infrastructure: every name above has a validated wash-safe partner + ETF fallback in
`harvest_pair_map_20260821.json`. Seven names (CI CTSH EQT KNSL MCK WRB XOM) are PARAMETRIC_SELF —
trade-file check before any harvest batch.

## SLEEVE II — INDEX COMPLETION (~$1.2–1.4M residual)
Two non-identical broad funds (VTI + SPLG class — NOT QQQ; Parametric already carries 38% AI),
bought same week as Sleeve I, 50/25/25 accelerating into any −2% day. Role: beta from day one;
permanent completion sleeve at month-12 (floor ~$0.5M). Expected 2026 harvest contribution: ~zero,
by design. Pair identity rules in the pair map (never VOO/IVV/SPY against SPLG).

## SLEEVE III — EDGE BOOK (courted names, re-based to ruled % of $6M through EXISTING gates only)
| Name | Ruling | At $6M | Gate / mechanics |
|---|---|---:|---|
| WAL | complete, capped | $52k held | Edge: scar-discount retirement (FV 70/98/106, p=0.70 pack 10/31). CC Template-3 sequenced behind the pack |
| APP | min-starter 0.25% | $15k | adds: code-P / filed e-comm / $340 basing; stop weekly close <$299; + Jan'27 320/340 spread (filled $7.08) |
| OI | starter 0.25% | $15k | own FV $7.34; add on Q3 Europe SOP>$40M (10/27) |
| BAVA.CO | held half-starter | $6.2k held | **NO TRIMS UNTIL 2027 (principal 8/21, tax)** — LT clock ~Jul-2027; recourt derives rungs, stages nothing; hard-event/kill sells stay immediate and tax-blind |
| ARX | held (instr #100) | $8.1k held | 415sh @12.34, rides the print by design |
| LFTO | held 300sh | $5.7k held | hold-through-unlock review ~10/02 (14-wk cliff, ruled starter) |
| CIFR | REJECT + buy zone | 0 | re-opens ≤$12.50 only (replaced convert-strike provisional) |
| SRAD | REJECT RP_TAINTED | 0 | no price gate; 11/04 grade-only pack |
| BSY, GCT, DFIN, PINS, PL, VMD, HSBK, WF, etc. | held w/ resting exits | ~$150k | exit ladders resting (HSBK 40/44, WF 76/89, J 168/185 …) — trims are the rotation fuel |
| PHYS | held + ladder | $11.2k held | court-named vehicle (beta-placeholder doctrine); adds 30.80/29.20 resting |
| WYNN | call-spread book | ~$4.6k net | defined-risk; Oct/Nov/Jun legs |

## SLEEVE IV — JAPAN ENVELOPES (ADV-bound; EXEMPT from % re-base)
Principal-run daily via envelope_runner (Rung 0.75), expiries 9/30–10/31:
SANYU 5697 (1,400 tgt ≤¥825; 100 filled) · TACHI 7239 (300 ≤¥2,420) · EBARA 2819 (200 ≤¥2,700) ·
ATOMIX 4625 (500 ≤¥815) · plus 9713 GTC ladder (800 held). Size set by liquidity math, not book %.

## SLEEVE V — RESTING COMMITMENT BOOK (the passive net under everything)
~45 GTC buy limits currently resting (LH ladder, DGX, MCK, PEO.WA, KKR/NFLX/TMUS/RDDT/ADBE/TYL
dislocation ladder, CTRI/APTV/VMD, SPR/TFW/FDM/ETL UK-FR small caps, 6626/6932/7722 Japan, 058850
KTCS add, 005387 pref …). These are pre-ruled entries that only fill INTO weakness — the book's
standing answer to a selloff, sized before the money arrives. On landing, re-size the dislocation
ladders to $6M percentages through their existing gates (no new courts).

---

# THE L/S STRATEGY

**Long structure (target at month-3):** ~$4.6–4.9M working long across Sleeves I–IV, ~78% single-name
and ~22% index, migrating index→slots via harvests through 12/31 (EOY amendment). Concentration
rails: ≤20% per axis in the core; edge starters 0.25–0.5% each; WAL capped.

**The short side — what it is and deliberately is not:**
1. **XND Dec'27 puts (the ratified structural short).** Sized 25–50% of the ~$4.5M household AI
   overlap (38–75 contracts, $1.1–2.2M notional), ~10% OTM struck off the FORWARD, collar-financed,
   §1256. Phased: 1/3 at 50% deployed, 2/3 at full, 3/3 only if the quarterly AI-break review
   re-freezes p≥0.45. This is a thesis short (frozen 0.45, CRWV canary), not portfolio insurance.
2. **Single-name short book: EMPTY — by ruling, not neglect.** Short-court doctrine (6 gates incl.
   MEME EXCLUSION and borrow/carry math) has passed zero names to date. Any short idea routes
   through that court; until one passes, no single-name shorts exist in the plan.
3. **Exclusion alpha (the honesty short).** The desk's largest "short" is the refusal list — the
   lying-cohort exclusions and killed verticals. Expressed as zero-weight, tracked in the antibook,
   costing no borrow and no squeeze risk.
4. **Short-vol, three templates ONLY (taxable doctrine):** event-IV CSPs at floors we'd own
   (live: EQT 52.5, QCOM 135/140, MCHP 65, DSGX 70, FAF 70s), dead-chain, PAID-TRIM CCs
   (Template 3, six gates — WAL queued behind its 10/31 pack). Everything else shadow-ledger only.
5. **The reserve is the third leg.** $1.855M in SGOV is deliberately anti-correlated with the long
   book (harvest-hedge doctrine): market down → tax bill down → reserve releases INTO the selloff,
   the same branch where XND pays and the resting commitment book fills. All three legs monetize
   the same event without forecasting it.

**Net profile:** ~100% long day-5 on deployable capital, hedge delta building to roughly −10 to −20%
of the AI-correlated slice as phases complete; net vs $6M including reserve ≈ 55–75% through Q4.
No axis caps beyond the core's 20% rail (capital-abundance doctrine: sleeves are information).

**What would change this document:** landing amount ≠ $5M (re-run day-0 split); AI-break review
moving off 0.45 (hedge size); any short-court PASS (opens the single-name short book); TLH-core
band re-derives at touches (per-name, continuous).
