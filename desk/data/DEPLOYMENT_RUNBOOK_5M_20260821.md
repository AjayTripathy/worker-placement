# $5M DEPLOYMENT RUNBOOK — two lanes (principal-ratified design, 2026-08-21)

**Trigger:** the ~$5.0M zero-basis payment landing (window: imminent; SGOV ladder rungs 8/27 + 9/24
were pre-timed to it). **Governing doctrine amendments carried in this runbook:** physical index
authorized at IBKR as deployment vehicle + completion sleeve (amends beta-placeholder doctrine,
principal-owned); hedge instrument upgraded QQQ→NDX-class for §1256 60/40 treatment.

## Day 0 — the split (before anything is bought)
1. **Tax reserve ≈ $1.855M** → bills/SGOV ladder extension. Exact figure trues up against the
   estimated-payment calendar at landing (reconcile the $3.145M vs ~$3.3M deployable figures then —
   the delta is timing of estimates, not doctrine).
2. **Wash-sale sweep vs Parametric** (household wash = Parametric + GOOGL) before any purchase list
   is final.
3. Deployable working figure: **~$3.2M.** Post-landing total book ≈ **$6.0M** — the denominator the
   8/02 sizing amendments already assumed.

## LANE A — index-first (fully invested by day 5)
**Long leg (~$3.2M): broad index, NOT QQQ.** QQQ doubles the household's AI concentration
(Parametric $9.19M @159% lev, 38% AI). Buy TWO non-identical broad funds ~50/50 (e.g. VTI + SPLG)
so index-level harvests can swap between them wash-free later.
- Execution: 50% day 0, 25% day 2, 25% day 5, limit-at-market tranches; ACCELERATE the remainder
  into any −2% session (buying weakness is the plan, not a deviation).

**Hedge leg: NDX-class puts (XND for granularity, ~$29k notional/contract), Dec 2027 tenor —
covering the frozen 2027-12-31 AI-break date (p=0.45, CRWV canary).**
- Sizing: household AI/tech overlap ≈ $3.5M (Parametric) + ~$1.0M (new index tech weight) ≈ $4.5M.
  Hedge 25–50% of overlap → **$1.1–2.2M notional ≈ 38–75 XND contracts**, ~10% OTM.
- Cost anchor (priced 8/21): QQQ Dec'27 640P = 5.6%/16mo ≈ 4.2%/yr → $46–92k/yr at full size.
- **Collar to cut carry ~40–50%:** sell XND calls with strikes set off the FORWARD (~+8% over 16mo
  per the long-dated-collar memory), not spot.
- **Phase-in (per the conditioned-insurance memory):** 1/3 of hedge at 50% deployed, 2/3 at fully
  deployed, final 1/3 only if the AI-break freeze re-affirms ≥0.45 at the next quarterly review.
- §1256: NDX-class = 60/40 treatment; never QQQ equity options for this leg.

## LANE B — migration to the slot map (weeks 1 → month 12)
The 32-slot TLH core map (8/02, ~$2.6M targets, lots 2–3 ≈ $1.8–1.9M unfilled) is the destination;
the index is the vehicle. **Every rotation is a harvest.**
- **Rotation rule 1 (harvest-driven):** any session the index shows a harvestable loss ≥$5k OR any
  ≥−1.5% index day → sell index lots (specific-lot, highest basis), buy slot names at their bands,
  in slot-target sizes. The index loss banks; the single-name basis diversifies.
- **Rotation rule 2 (gate-driven):** when a slot band or court gate fires, rotate regardless of
  index P&L — court gates outrank harvest timing. If the index lot is at a gain, use specific-lot
  selection to minimize the realized gain.
- **Edge-lane re-base:** all HELD/STARTER verdicts re-size to their RULED percentages on the $6M
  base (0.25% starter = $15k; OMF-class 1.17% = $70k) — **through their existing gates only**, no
  market-chasing. EXCEPTION: Japan/thin envelopes keep current share targets — ADV caps dominate
  the percentage math there (a 0.75% target on $6M cannot be absorbed at 1%/day of a ¥5B name).
- **Wash check before every rotation batch** (Parametric coordination).
- **Completion criterion — resolves the 8/04 open question:** whatever index remains unrotated at
  month 12 (floor ~$0.5M) IS the completion sleeve, permanently. Breadth beyond the 32 slots comes
  from the index residual, not from courting 60+ names past process depth.

## Standing reviews
- Monthly: migration pace, hedge phase vs deployment %, reserve true-up.
- Quarterly: AI-break re-freeze decision gates hedge tranche 3.
- The missed-entry review and confirmation-premium column grade whether Lane B's band discipline
  costs more than it saves — the doctrine self-corrects on evidence.

## What cancels or amends this runbook
Payment size/timing materially different at landing; a reserve true-up moving deployable >±$300k;
or a principal amendment. The runbook is the plan of record until one of those fires.

---

# AMENDMENT 2026-08-21 — THE EOY-2026 HARVEST DEADLINE (principal correction; lane priority FLIPPED)

The original Lane B pace (6-12 months) missed the binding constraint: **losses offset the $5M gain
only if realized by 2026-12-31** (~37.1% combined marginal = each harvested dollar saves ~$0.37
against THIS year's bill; 2027 harvests are only carryforwards). A fresh single-lot index cannot
produce 2026 losses by construction — one wrapper nets winners against losers and a 3-month-old
position rarely shows red lots. Single names disperse: cross-sectional dispersion produces losers
to sell and winners to keep even in a flat tape. Therefore:

## Lane priority flipped: SLOTS FIRST, index for the residual only
1. **Weeks 1-3 post-landing: deploy DIRECTLY into the 32 pre-ruled slots** (~$1.8-1.9M of lots 2-3;
   no courts needed — ruled 8/02). Staged limit ladders at/near market per TINA; envelope-chunked
   for thin names. Every week earlier = a week more dispersion before 12/31.
2. **Index takes only the residual (~$1.2-1.4M)** — as the completion sleeve from day one, bought
   in the same week, ACCEPTING it will contribute ~nothing to the 2026 harvest. Its job is beta,
   not losses. (Two non-identical funds still, for future-year index-level swaps.)
3. Hedge lane unchanged (XND Dec'27 collar, phased with deployment).

## Harvest operations calendar (the part that was missing entirely)
- **NOW (pre-landing): build the harvest-pair map** — every slot name gets a designated
  non-substantially-identical replacement partner (peer holding the factor through the 31-day wash
  window). No pair, no harvest: this table is the whole December bottleneck and it can be built
  before the money arrives.
- **By Nov 28: doubling-up window closes** (buy the replacement 31 days before selling the loser —
  the only way to harvest without ever leaving the exposure). Names down >8% in early Nov are
  doubling-up candidates.
- **Nov 1 onward: weekly loss scan** (tlh_capacity machinery) — harvest any lot at a loss >=$3k on
  each pass; rotate into the pair; calendar the 31-day repurchase dates.
- **Dec 15-29: final sweep** — last clean harvest execution ~Dec 29; every lot re-checked; the
  Parametric wash coordination run on EVERY batch.
- **Expected-harvest honesty:** $3.2M deployed late-Sept produces an expected 2026 harvest of
  roughly $80-250k (dispersion-dependent; zero if everything rallies — a good problem), worth
  ~$30-90k against the 2026 bill. Nobody harvests $5M in four months on $3.2M deployed; the plan's
  value is the OPTION on a Q4 selloff, which this calendar converts at full speed if it comes —
  and a Q4 selloff is exactly when the XND hedge leg pays, funding MORE slot buys at lows. The
  reserve-hedge-harvest triangle is self-reinforcing in the down branch.

## Harvest-pair map: BUILT 2026-08-21
`desk/data/harvest_pair_map_20260821.json` — 31 slots + VTI/SPLG, each with primary partner + ETF
fallback, validated against the LATEST Parametric bundle (2026-08-14, 527 symbols — up from 304 at
the 8/02 build). 12 of the 8/02 partners were swapped (Parametric collisions or structural flaws,
incl. ORCL and the KNSL<->WRB double-collision). Seven slots are themselves Parametric-held
(CI CTSH EQT KNSL MCK WRB XOM): pull the Parametric trade file for the name before every harvest
batch. Index rule: SPLG's partner is never VOO/IVV/SPY (same index = substantially identical).

---

# AMENDMENT 2026-08-21b — TWO-ACCOUNT SEPARATION (ALPHA / BETA)

Principal ruling: court-driven stock-picking and the TLH deployment are different products with
different success metrics — rapid deployment carries NO alpha expectation. Separate them at the
custodian so each account's TWR is native and unarguable.

## Structure
- **ALPHA account (existing U-account):** the court/edge book — starters, edge names, Japan
  envelopes, WYNN structures, CSP templates, resting dislocation ladders. Benchmark: its own
  record (Brier + TWR vs SPY). Nothing changes operationally.
- **BETA account (NEW second linked account — principal opens):** the $5M lands here. TLH core
  (Sleeve I), index completion (Sleeve II), XND hedge, SGOV reserve. Benchmark: blended broad
  index. Success = market return + harvested losses + hedge discipline; alpha is NOT claimed.

## Mechanism (IBKR)
Client Portal -> Settings/Account Settings -> "Open an Additional Account" (individual clients can
hold multiple accounts under one username; exact menu label may vary — verify in Portal). Same
login, separate account ID, SEPARATE: statements, margin, buying power, PortfolioAnalyst TWR.
PortfolioAnalyst assigns a per-account benchmark. Cannot be done by the desk — account creation is
principal-only.

## Consequences the separation does NOT buy
- **Wash sales stay HOUSEHOLD-WIDE** (both accounts + Parametric + GOOGL). The pair map remains
  the binding authority; the broker's per-account wash accounting is not the law's perimeter.
- Tax lots are per-taxpayer regardless of account; the reserve math is unchanged.

## Migration & wiring (CORRECTED 2026-08-21 — principal)
- **NO single-name transfers to BETA — ever.** The TLH core names were picked by the courts as part
  of the rotation/thesis book: they are HEDGE-FUND positions and stay in ALPHA, including the ~$261k
  of partial fills. BETA never holds a single name.
- **BETA holds exactly three things:** the two index funds, the XND hedge, and the SGOV reserve.
  It is the principal's original "simple model" — indexes + puts — as its own measurable account.
- **Slot/core buys are ALPHA activity funded by BETA.** Lane B migration = sell index lots in BETA
  (specific-lot, highest basis), transfer CASH to ALPHA, ALPHA buys court-ruled names at bands.
  Every migration is simultaneously a harvest (BETA's loss), a capital injection (ALPHA's flow,
  TWR-adjusted), and a measured stock decision (ALPHA's record). No in-kind crossings, so both
  TWRs stay clean and the hedge fund's alpha is never diluted by deployment-speed buys.
- **EOY-2026 harvest note under this structure:** single-name dispersion harvesting happens in
  ALPHA on names ALPHA chose; BETA's 2026 harvest is limited to index-lot losses. The slots-first
  pace survives only as fast as ALPHA's own bands/ADV discipline allows — deployment speed is
  BETA's job, never a reason for ALPHA to chase.
- Desk wiring once the account exists: order staging + envelope_runner + gateway get an explicit
  account field (ib_insync order.account); MCP connector account-selection verified; positions
  polls tagged by account. Envelopes remain ALPHA-only by origin rule.

---

# AMENDMENT 2026-08-21c — BETA IS A DIRECT-INDEX COMPLETION SLEEVE (principal correction)

BETA does NOT hold two ETFs — that would rebuild the un-harvestable wrapper the EOY-2026 amendment
exists to avoid. BETA direct-indexes in single names, selected MECHANICALLY:

- **The dividing line between the accounts is judgment vs rule, not single-name vs fund.**
  ALPHA holds names courts chose. BETA holds names an index-replication rule chose. No courted
  name enters BETA; no BETA name is ever sized or timed by view. That is why BETA needs no courts.
- **Completion construction (Parametric collision rule):** the household already direct-indexes
  ~527 large-cap names ($9.19M, Parametric). BETA therefore replicates the broad market MINUS
  Parametric's current holdings — in practice a mid/small-cap completion basket (~100-200 names,
  cap-weighted, sampled), refreshed against the weekly Bundle so the two sleeves never trade the
  same names and household washes are impossible by construction. Bonus: it adds the mid/small
  exposure the household currently lacks.
- **Execution mechanism:** desk generates the basket CSV; principal executes via TWS BasketTrader
  (or staged instructions) over 2-5 sessions per the Lane-A schedule. ETFs may serve as day-0
  parking ONLY if the basket cannot be fully staged in week 1, and must be rotated out (their
  losses harvest into the basket; their gains ride to LT).
- **Harvest capacity restored:** ~$3.2M across 100-200 dispersing names is the 2026 loss engine
  the ETF version lacked. Weekly loss scans (Nov 1+) run on BETA's basket with ETF-pair fallbacks
  (each harvested name's proceeds park in a completion-index ETF slice for the 31-day window —
  no per-name pair map needed at this breadth; the ETF holds the factor).
- Lane B unchanged: BETA basket losses harvest -> cash crosses to ALPHA -> ALPHA buys courted
  names at bands. XND hedge + reserve unchanged.
