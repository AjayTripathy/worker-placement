# TLH SLEEVE — ARCHITECTURE & INFRASTRUCTURE DESIGN
**SignalOS desk · 2026-08-26 · plan-of-record synthesis (runbook 2026-08-21 + amendments) with build inventory and open decisions**

---

## 1. Executive summary

The tax-loss-harvesting sleeve exists to do one thing on one deadline: **realize enough capital losses by 2026-12-31 to offset the ~$5.0M zero-basis gain landing in September** (~37.1% combined marginal — every harvested dollar saves ~$0.37 against *this year's* bill; anything harvested in 2027 is merely a carryforward). Everything else — account structure, basket mechanics, hedges, and this week's order-integrity infrastructure — is in service of that constraint plus one boundary: **the harvest machine must never contaminate the judgment machine.**

Design in one paragraph: the $5M lands in a separate account (**BETA, ACCOUNT_BETA**), reserves ~$1.855M for tax, and deploys **slots-first** — ~$1.8–1.9M directly into the 32 pre-ruled TLH-core slots (single names disperse; a fresh index lot cannot produce 2026 losses by construction), with the **index residual (~$1.2–1.4M)** as a permanent completion sleeve whose job is beta, not losses. A **Dec-2027 XND collar** hedges the household's AI concentration on §1256 terms, phased with deployment. Harvesting runs on two rotation rules (harvest-driven and gate-driven), a **harvest-pair map** built before the money arrives, and a **Nov-28 doubling-up deadline**. The court book (**ALPHA, ACCOUNT_ALPHA**) never mixes: a courted name may never enter BETA; a replication name may never be sized by view.

## 2. Objectives and binding constraints

| # | Constraint | Consequence in design |
|---|---|---|
| C1 | Losses must **realize by 2026-12-31** | Slots-first deployment (dispersion now); index residual accepts ~zero 2026 harvest |
| C2 | Tax reserve **≈ $1.855M** (true-up at landing) | SGOV/bills ladder extension day 0; deployable ≈ $3.2M |
| C3 | Household wash surface = **Parametric singles + GOOGL** (+ now BETA basket) | Completion-set construction (§4.3) + wash sweep before every rotation batch |
| C4 | Household already ~26% AI-complex ($5.18M) | No QQQ; broad index only; XND hedge sized to the *overlap*, not the sleeve |
| C5 | Judgment/rule boundary (principal-ratified) | Two accounts; courted names structurally excluded from BETA |
| C6 | Ops maturity (this week's evidence) | No automated order paths in BETA — principal-clicked BasketTrader CSVs only |

## 3. Account architecture

```
                         HOUSEHOLD WASH PERIMETER (one taxpayer - rules apply ACROSS accounts)
  ┌──────────────────────────┬──────────────────────────────┬──────────────────────────────┐
  │  PARAMETRIC 038CAG0E4    │  ALPHA  ACCOUNT_ALPHA (LIVE)     │  BETA  ACCOUNT_BETA (pending)   │
  │  $9.19M, 131/31 L/S      │  court book / hedge fund     │  $5M TLH deployment          │
  │  optimizer-run TLH       │  courted names, envelopes,   │  32 slots + index residual   │
  │  ~$105k/mo losses banked │  options templates           │  + XND collar + SGOV reserve │
  │  (external manager)      │  judgment, gated by courts   │  mechanical, no courts       │
  └──────────────────────────┴──────────────────────────────┴──────────────────────────────┘
        weekly bundle ─────────► exclusion stack ◄───────── positions/orders cache
                          (beta_basket_generator: BETA holds ONLY what
                           neither Parametric nor ALPHA touches)
```

- **The dividing line is judgment vs rule, not single-name vs fund.** ALPHA holds anything a court ruled; BETA holds only mechanical replication. This is what makes the wash surface *auditable*: BETA cannot collide with ALPHA by construction, and it cannot collide with Parametric because the basket is built as the **completion set** (index minus Parametric's latest bundle, refreshed weekly).
- **Account pinning:** `require_alpha()` asserts the account on **all four** ALPHA placement paths (sanyu_accumulator, jp_accum_core, japan_stager, order_executor) after the Error-435 incident proved an accountless order dies loudly once two accounts exist. BETA has **no automated paths at all** — CSV staged, principal clicks.
- Cash-only crossings between accounts; BETA activation checklist (managedAccounts verification, MCP account-selection check, PA benchmark) lives in `accounts.json`.

## 4. Sleeve design

### 4.1 Lane priority (amended 2026-08-21): SLOTS FIRST
1. **Weeks 1–3 post-landing:** deploy ~$1.8–1.9M directly into the 32 pre-ruled slots (lots 2–3 of the 8/02 map; no new courts — ruled). Staged limit ladders at/near market per §TINA; envelope-chunked for thin names. Every week earlier = a week more dispersion before 12/31.
2. **Index residual ~$1.2–1.4M**, same week, in **two non-identical broad funds ~50/50** (VTI + SPLG) so future index-level harvests can swap wash-free. Its job is beta.
3. **Completion criterion:** whatever index remains unrotated at month 12 (floor ~$0.5M) **is** the completion sleeve, permanently.

### 4.2 Rotation rules (the harvest engine)
- **R1 (harvest-driven):** any session with a harvestable index loss ≥$5k OR any ≥−1.5% index day → sell index lots (specific-lot, highest basis), buy slot names at their bands in slot-target sizes.
- **R2 (gate-driven):** when a slot band or court gate fires, rotate regardless of index P&L — **court gates outrank harvest timing**. Specific-lot selection minimizes realized gains.
- **Re-base rule:** HELD/STARTER verdicts re-size to ruled percentages on the $6M base (0.25% = $15k) through existing gates only; Japan/thin envelopes keep absolute share targets (ADV caps dominate percentage math).

### 4.3 The basket generator (`desk/beta_basket_generator.py`)
Mechanical, self-documenting, and **any manual edit to its output is a doctrine violation**. Exclusion stack (union): Parametric latest bundle (msprime.db) → research-ledger tickers (every screened name, any state) → edge-classification records → ALPHA live positions → ALPHA resting-order symbols → GOOGL (asserted, never assumed). Output: BasketTrader CSV (LMT at snapshot, DAY) + manifest JSON. Dry run 8/21: **149 names / $1.579M**. Refresh cadence: weekly against the newest `Bundle_*.zip`.

### 4.4 Harvest-pair map (the December bottleneck — build NOW, pre-landing)
Every slot name gets a designated **non-substantially-identical replacement partner** holding the factor through the 31-day wash window. *No pair, no harvest.* Deadline logic: **Nov 28 is the last doubling-up date** (buy the replacement 31 days before selling the loser to never leave the exposure); names down >8% in early November are doubling-up candidates.

### 4.5 PROPOSED, NOT RATIFIED — the diligenced-dispersion sleeve
Principal question 8/26: use FLAT-ruled names as the TLH base with paired shorts. Desk analysis:
- **Adopted-in-principle half:** flat names are diligenced and carry 40–60% single-name vols → an est. **2–3× harvest yield per dollar** vs the index residual ($700k–1.2M vs $350–500k modeled year-one).
- **Rejected half:** (a) flat names are *courted* names — holding them in the TLH base reverses the C5 boundary and manufactures cross-account wash collisions exactly where court gates are dated (CYD 8/27, USNA 10/21, AAP 11/12, PWP band); (b) paired single-name shorts are tax-poison in a TLH vehicle (short gains are always ST; several bear-lean flats are MEME-excluded from shorting; shorting a cohort our own study shows drifting +3% fights our own data); (c) duplicates Parametric's L/S engine with worse ops.
- **Bounded alternative on the table:** $750k–1M **long-only** sleeve of flat names passing three filters — liquid at desk rails, not RP_TAINTED, **no live gate inside the harvest horizon** — hedged at book level by the existing XND collar. **Status: awaiting principal ratification; a filter-screen + harvest simulation is the next artifact if pursued.**

## 5. Hedge architecture (Lane H)
- **Instrument:** XND (NDX-class, ~$29k/contract) Dec-2027 puts — tenor covers the frozen AI-break date (2027-12-31, p=0.45, CRWV canary). **§1256 60/40; never QQQ equity options.**
- **Sizing:** household AI/tech overlap ≈ $4.5M (Parametric $3.5M + new index tech weight ~$1.0M); hedge 25–50% → $1.1–2.2M notional ≈ 38–75 contracts, ~10% OTM. Cost anchor ~4.2%/yr naked → **collared to ~half** by selling calls struck off the **forward** (+8%/16mo), never spot.
- **Phase-in (conditioned-insurance rule):** 1/3 at 50% deployed; 2/3 at full deployment; final 1/3 only if the quarterly AI-break re-freeze holds ≥0.45.
- **Harvest-hedge note:** the tax reserve itself is anti-correlated with the market (a drawdown that hurts the book shrinks the remaining gain to offset) — reserve sits in bills, never risk.

## 6. Tax accounting rails
- **ST/LT clocks on every lot; tax-adjust every exit** (ARX precedent). Specific-lot ID everywhere.
- **Wash discipline:** sweep vs Parametric + GOOGL + BETA before every rotation batch; the pair map (§4.4) is the standing answer; cross-account collisions are structural-impossible for BETA by the exclusion stack, and for ALPHA by the no-courted-names-in-BETA rule.
- **Parametric interplay:** ~$105k/mo realized-loss run-rate already banked (−$425k inception→8/02) — the household's 2026 offset is Parametric + BETA slots combined; **always dedup Parametric G/L by (taxlot, date, qty)** (the 2.5× app inflation lesson).
- **Reserve math:** $5M → ~$1.855M owed → ~$3.2M deployable; true-up at landing against the estimated-payment calendar; >±$300k movement re-opens the runbook.

## 7. Infrastructure inventory (what exists, what watches it)

| Component | File / agent | Job | Failure mode it closes |
|---|---|---|---|
| Basket generator | `desk/beta_basket_generator.py` | completion basket, exclusion stack, CSV | wash-by-construction; judgment leakage |
| Account registry | `desk/account_registry.py` (`require_alpha`) | pins every automated order to ALPHA | Error-435 / wrong-account placement |
| Order sentinel | `desk/order_sentinel.py` + launchd 30-min | zombie cancels, PendingCancel SLA 30m, **cancel-by enforcement**, missing-order verify, gateway 2-strike alarm, runner liveness | the 18h stuck-cancel class; resting-into-print rail now machine-held |
| Intent ledger | `desk/data/order_intents.json` | every cancel/cb directive gets a machine-checked row | directives enforced only by memory |
| Band watch | `desk/band_watch.py` | ledger bands vs live tape; **order-coverage derived from the blotter each run** | suppressed alerts over dead orders (ONON class) |
| Consistency check | `desk/consistency_check.py` | packs dated, resting-orders-have-catalysts, grader health, **unverified-ledger drain stall**, pre-mortem presence | silent-accumulation and dateless-gate classes |
| Envelope runner | `desk.envelope_runner` (Rung 0.75, principal-run + caffeinate) | ALPHA Japan accumulators; **never BETA** | daemon-sleep session loss (sentinel now warns) |
| Court conveyor | `desk.court_runner` (hourly launchd) | produces/updates the slot map ALPHA-side; gates that outrank harvest (R2) | — |
| Mailer / dashboard | `desk/mailer.py`, desk UI `/ticker/{sym}` | every event legible; every ticker → dossier | decisions trapped in chat |

**Known open infra tickets:** court-runner IBKR MCP grant (benches permission-denied — repeated); bench tape-divergence preflight (3 stale-tape instances this docket); runner red/blue pairing defect (3rd recurrence); gateway auto-restart (needs principal security decision); envelope-runner launchd migration (autonomy-rung decision); ZAR permission if MTN.JO ever stages.

## 8. Operating cadences
- **Daily (deployment window):** rotation-rule scan at close; sentinel every 30m; band watch 6:15/7:45.
- **Weekly:** Parametric bundle refresh → basket regen → drift check; wash sweep.
- **Monthly:** migration pace vs 12/31 runway; hedge phase vs deployment %; reserve true-up; MR-scorecard cohort study.
- **Quarterly:** AI-break re-freeze (gates hedge tranche 3); §ALPHA-MIGRATION gate review.
- **Hard dates:** landing (~Sept); **Nov 28** doubling-up close; **Dec 31** harvest deadline; month-12 completion criterion.

## 9. Failure modes and their guards (all OBSERVED this cycle, none hypothetical)

| Failure | Instance | Guard now standing |
|---|---|---|
| Cancels stuck through gateway restart | ACEL/6626/CRM, 18h PendingCancel | sentinel SLA + re-issue protocol |
| Gateway wedge, silent | twice, 8/24–25 | 2-strike CRITICAL alarm |
| Daemon dies on battery sleep | Tokyo session lost 8/17 | caffeinate + plugged-in rule + liveness warn |
| Hand-maintained state rots | ORDER_COVERED 12/15 stale; ONON through its band | live-blotter derivation; static = fallback only |
| Dateless gates invisible | 916 packs; BGSI 12 days | hourly pack-date guard |
| Work queue becomes archive | unverified ledger stalled 5 days | drain-stall flag; R1.13(e) scope |
| Vendor tape lies | PTS marks; intraday-vs-close; BYND reverse split (+2538% fake) | artifact-family memory + split guard in scorecard |
| Wrong-account order | Error 435 | require_alpha in all four paths; BETA has no automated paths |

## 10. Decision queue (principal)
1. Ratify or decline the **bounded dispersion sleeve** (§4.5) — if yes, the three-filter screen + harvest simulation is the next artifact.
2. **§ALPHA-MIGRATION gates** into the runbook (cohort grade 11/22 + Brier record; 30 clean days; $30–60k slot scale test).
3. Gateway auto-restart (credential/2FA trade-off) and envelope-runner launchd (rung change).
4. BETA activation checklist on account approval (managedAccounts, MCP account selection, PA benchmark).

*Prepared by the desk, 2026-08-26. Sources: DEPLOYMENT_RUNBOOK_5M_20260821.md (+8/21 amendments), accounts.json, beta_basket_generator.py, this week's hardening commits, cohort study 8/26.*
