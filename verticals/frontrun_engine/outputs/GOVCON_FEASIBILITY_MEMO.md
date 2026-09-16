# Gov-Contract Award-Flow Frontrun — Phase 1 Feasibility Memo

**As-of: 2026-06-24. Pre-registered spec: `GOV_CONTRACT_SPEC.md` (LOCKED 2026-06-24). No Phase-2 scoring run.**

The claim under test (do not lose it): the edge is an **aggregation + obscurity moat** — a buried
USASpending award (civilian-agency, or sub-$7.5M defense, i.e. NOT in the DoD daily press list) to a
thinly-covered name predicts its future revenue before earnings, where no analyst/proxy prices it. The
deliverable is whether `edge(Arm A uncovered) − edge(Arm B covered primes)` can even be *tested* — and it
must vanish in the covered control or it's just defense-sector beta (the CEF kill case).

This memo answers the two make-or-break feasibility questions FIRST, because they decide whether the pilot
is runnable at all.

---

## TL;DR verdict

**Conditionally runnable — but only on the CIVILIAN-agency leg of Arm A, not the sub-threshold-defense leg.**
The two feasibility questions split cleanly:

- **(a) Posting lag — PASS for civilian, FAIL for defense.** Civilian-agency obligations post to USASpending
  at **median 0 days** (85% within 7 days) after the action date — near-real-time, and they are not
  press-released, so this is an ideal frontrun substrate. **Defense (DoD, especially DLA `SPE*` logistics)
  posts on a ~quarterly batch: median 98-day lag, 0% within 7 days.** The sub-$7.5M-defense leg of the
  spec's Arm-A definition is obscure but **too stale to frontrun the next print** — by the time it posts, the
  quarter it would predict is often already reported. → **Proposed Amendment #1** (below): restrict the
  live/tradeable Arm-A signal to the civilian-agency channel; keep sub-threshold-defense as a measured-only
  diagnostic.

- **(b) Entity resolution — PASS, with a curated-alias caveat. 89% success (16/18 names VERIFIED).** The
  family roll-up ties to reported gov revenue within band (SAIC 0.64×, Leidos 0.73×). BUT resolution is
  **load-bearing on hand-curated subsidiary aliases** — 9 of 16 verified names need them (QTC→Leidos,
  Sikorsky→LMT, Gulfstream/Bath Iron→GD, Mastodon→CACI, SemanticBits→ICF). The bare token-anchor alone
  understates diversified contractors by 20-40% and short names (SAIC, VSE) fail outright on substring
  collisions. This is automatable per-name but **not** zero-touch; 2 names (VSEC, CMTL) remain UNVERIFIABLE.

Net: the pilot is testable, but the tradeable universe is **the civilian-tilted, thinly-covered tail** —
which is also precisely the spec's stated moat. The defense-logistics obscurity is real but the data latency
eats it. The covered-prime control (Arm B) is intact and necessary.

---

## Feasibility Q(a): USASpending posting lag — the gating fact

**Method.** For each company, pull awards with a recent `action_date`, keep only records *freshly loaded*
(USASpending `Last Modified Date` within 3 days of as-of), then measure how OLD the underlying newest
`action_date` is. `load_lag = last_modified − newest_action_date` = how stale the freshest data we can pull
actually is = the floor cost of the frontrun window. (Code: `engine/award_flow.py::measure_posting_lag`;
data: `outputs/govcon_posting_lag.json`, `outputs/govcon_lag_by_agency.json`.)

**Headline (N=57 freshly-loaded records, 8 recipients):** the distribution is **bimodal and agency-driven.**

| Agency type | N | median load-lag | mean | % posted within 7 days |
|---|---|---|---|---|
| **Civilian** (HHS, GSA, DHS, EPA, Interior, DOJ, NSF, Commerce) | 26 | **0 days** | 3 | **85%** |
| **Defense** (DoD incl. DLA, Navy) | 31 | **98 days** | 101 | **0%** |

Per-agency median load-lag (days): DoD **98**, NASA 34, Treasury 14, Justice 8 — then HHS / GSA / DHS / EPA /
Interior / NSF / Commerce all **0**.

**Worked examples (true lag, not artifact — verified each award's newest action is the only/newest tx):**

| Award | Awarding agency | Action date | First loaded | Lag |
|---|---|---|---|---|
| SPE8ES26F64B3 (SAIC) | DLA (DoD) | 2026-03-11 | 2026-06-22 | **103 d** |
| SPE8ES26F52R2 (SAIC) | DLA (DoD) | 2026-03-04 | 2026-06-22 | **110 d** |
| N00189... (Booz Allen) | Navy (DoD) | 2026-03-03 | 2026-06-22 | **111 d** |
| 68HERC24F0049 (ICF) | EPA (civilian) | 2026-06-22 | 2026-06-22 | **0 d** |
| 47QFCA26F0005 (Booz) | GSA (civilian) | 2026-06-22 | 2026-06-22 | **0 d** |
| 89243325FFE... (Maximus) | Treasury | 2026-06-15 | (loaded same wk) | ~0-7 d |

I verified the 90-100d defense records are **genuine posting lag**: each `SPE8ES26F*` award has a single
March action date and no intervening transaction — DLA simply batch-loads to USASpending ~quarterly. (An
earlier, narrower probe that happened to sample Leidos/ICF/HHS records read a clean median-0 lag; the broader
sample exposed the defense tail. Reporting the broader, less flattering number.)

**Implication for the frontrun window.** The frontrun thesis needs the obligation to be visible to us *before*
the revenue is recognized and *before* the print. Quarterly outlay-to-revenue lag gives a multi-week-to-quarter
window. A **0-day** civilian posting lag sits comfortably inside that window. A **98-day** defense posting lag
does not — a March DLA obligation that only appears in late June is contemporaneous with (or past) the Q1→Q2
print it might have predicted. **This is the gating fact, and it kills the sub-threshold-defense leg as a
*live* signal while leaving the civilian leg fully viable.**

---

## Feasibility Q(b): recipient → ticker entity resolution — the main failure mode

**Method.** A company = `(search_terms, anchor_tokens, alias_recipients)`. Recipients from
`recipient_search_text` (fuzzy) are kept only if their core tokens SUPERSET the anchor (rejects JV/look-alikes),
plus a hand-curated alias list for named subsidiaries that don't share the parent token. Family obligations are
summed over an FY action-date window and **tied out** against reported US-gov revenue as a scale sanity check
(0.4×–2.0× band; obligations lead revenue and are lumpy, so an exact tie is not expected). Code:
`engine/award_flow.py`; tie-out test: `engine/test_award_flow.py` (3/3 pass).

**Success rate: 89% (16/18 VERIFIED, 2 UNVERIFIABLE).**

**Tie-outs (the unit test):**
- **SAIC** FY25 family obligations **$4.59B** vs ~$7.2B reported gov revenue = **0.64×** (in band). Correctly
  rejected `FORFEITURE SUPPORT ASSOCIATES`, `MOSAIC*` look-alikes.
- **Leidos** FY25 **$10.55B** vs ~$14.5B gov revenue = **0.73×** (in band) — and the **QTC alias added $2.89B**
  that the bare `{leidos}` token would have missed. Correctly rejected the Hanford Mission Integration and
  Stantec JVs.

**Three resolution failure modes encoded (the load-bearing lesson):**
1. **Short-name substring collisions.** `recipient_search_text=["SAIC"]` returns `moSAIC ATM`, `moSAIC
   Technologies`, … and does **not** surface the real SAIC. `["VSE"]` returns net-negative noise. Fix: use a
   distinctive search term (`"Science Applications"`), never the ticker/short-name.
2. **Named subsidiaries that don't share the parent token** — the dominant miss. **9/16 verified names depend on
   curated aliases:** QTC→Leidos, Sikorsky→LMT, Gulfstream + Bath Iron→GD, Mastodon→CACI, SemanticBits +
   Incentive Tech→ICF, MANTECH subs, Vertex→V2X, Empower AI→NCI. Without them the family is understated 20-40%.
3. **JV / look-alike false positives** — Mission Support Alliance (Leidos), Acacia Center for Justice (CACI),
   Forfeiture Support (SAIC). The anchor-subset matcher rejects these correctly.

**UNVERIFIABLE (flagged, not faked): VSEC, CMTL.** Both returned net-negative FY25 family obligations even with
aliases — VSE's fleet/aviation work flows through Wheeler Fleet Solutions / Turbine Controls with FY25 net
deobligations; Comtech's satcom work partly sits under the acquired TeleCommunication Systems entity. These need
deeper alias work or are genuinely small/lumpy; do **not** trade them until resolved.

**Verdict (b): PASS with caveat.** Resolution is reliable (89%) and tie-out is clean, but it is a **per-name
curated process, not zero-touch.** Budget analyst time to build + maintain the alias map; treat any name whose
family obligations don't tie within 0.4×–2.0× of disclosed gov revenue as UNVERIFIABLE and exclude it.

---

## (1) The two arms with classifier values

Classifier (LOCKED §2): Arm A = **≤5 analysts**; Arm B = **≥15 analysts**; middle excluded. Civilian-share =
FY25 (Oct 2024–Sep 2025) non-DoD obligation share from USASpending. Full data: `outputs/govcon_universe.json`.

### Arm A — thinly-covered (≤5 analysts), civilian-tilted (the moat)
| Ticker | Name | Analysts | FY25 family oblig. | Civilian share | Resolution | Arm |
|---|---|---|---|---|---|---|
| DLHC | DLH Holdings | 3 | $196M | **86%** | VERIFIED | **A** |
| ICFI | ICF International | 5 | $395M | **94%** | VERIFIED | **A** |
| VSEC | VSE Corporation | 5 | (net-neg) | — | UNVERIFIABLE | A (blocked) |
| CMTL | Comtech | 4 | (net-neg) | — | UNVERIFIABLE | A (blocked) |
| AVAV | AeroVironment | 8 | $499M | 0% | VERIFIED | EXCLUDED (middle, >5) |
| KTOS | Kratos Defense | 10 | $383M | 15% | VERIFIED | EXCLUDED (middle, >5) |

### Survivorship (delisted/acquired — point-in-time universe)
| Ticker | Name | FY25 family oblig. | Civilian share | Note |
|---|---|---|---|---|
| NCI→Empower AI | NCI Info Systems | $186M | 41% | taken private 2017 (HIG), rebranded Empower AI |
| ManTech→Carlyle | ManTech Intl | $1,477M | 45% | acquired by Carlyle 2022 ($4.2B) |
| Vertex→V2X | Vertex Aerospace | $1,538M | 21% | merged into V2X (VVX) 2022 |

### Arm B — control: heavily-covered primes (≥15 analysts), press-released awards
| Ticker | Name | Analysts | FY25 family oblig. | Civilian share | Resolution |
|---|---|---|---|---|---|
| LMT | Lockheed Martin | 24 | $75.9B | 1% | VERIFIED |
| RTX | RTX | 24 | $23.5B | 2% | VERIFIED |
| GD | General Dynamics | 22 | $10.8B | 33% | VERIFIED |
| NOC | Northrop Grumman | 22 | $12.9B | 4% | VERIFIED |
| LHX | L3Harris | 20 | $5.0B | 28% | VERIFIED |
| BAH | Booz Allen | 18 | $7.3B | **59%** | VERIFIED |
| LDOS | Leidos | 18 | $10.5B | **61%** | VERIFIED |
| SAIC | Science Applications | 15 | $4.6B | **53%** | VERIFIED |
| CACI | CACI International | 17 | $5.1B | 44% | VERIFIED |

**Structural finding (feeds Amendment #2):** Arm B is not homogeneous. The **hardware primes** (LMT/RTX/NOC:
1-4% civilian) are pure DoD; the **IT-services primes** (BAH/LDOS/SAIC: 53-61% civilian) are civilian-tilted —
same coverage axis as Arm B, but the same *agency* axis as Arm A. This is a feature: it gives a clean
within-control contrast (does the civilian-channel posting-lag advantage show up even among the *covered*
IT-primes? If yes, lag matters more than coverage; if the edge still only fires in Arm A, coverage is the moat).

---

## (3) The award-flow engine + tie-out test

- `engine/award_flow.py` — `AwardFlowEngine`:
  - `family_obligations(co, start, end)` — §3 family obligation total, point-in-time by action_date, with the
    anchor-subset matcher + alias list; returns matched recipients AND rejected look-alikes for auditability.
  - `agency_split(co, start, end)` — DoD-vs-civilian split (the Arm-A classifier input).
  - `signal_asof(co, asof, lookback, gov_rev_run_rate)` — the §3 ≥10%-of-gov-revenue signal, point-in-time, with
    an explicit **lag caveat** (recommends an `asof − 14d` buffer; for defense use a full-quarter buffer per Q(a)).
  - `measure_posting_lag(...)` — the Q(a) instrumentation.
- `engine/test_award_flow.py` — tie-out unit tests, **3/3 pass**: SAIC family resolves & rejects Mosaic;
  SAIC obligations tie to gov revenue in 0.4×–2.0× band (0.64×); Leidos QTC alias captured.

---

## (4) Proposed amendments (LOCKED params unchanged; originals preserved)

> Per spec §5/§7, the locked ≤5/≥15 cuts, 10% materiality, A/B split, and success criteria are **unchanged**.
> These are data-forced observations logged as proposed amendments, with the original retained.

**Amendment #1 (data-forced, HIGH priority) — split Arm A by posting-latency.** The spec's Arm-A moat
"civilian-agency AND/OR sub-$7.5M defense" conflates two channels with **opposite posting latency** (civilian
median 0d; defense median 98d). *Proposed:* in Phase 2, define the **tradeable** Arm-A signal on the
**civilian-agency obligation channel only** (0-day lag → actionable); compute the sub-threshold-defense channel
as a **measured-only diagnostic** (it is part of the obscurity story but its ~quarter lag makes it untradeable as
a leading signal). *Original preserved:* the combined "civilian and/or sub-7.5M-defense" Arm-A definition remains
the registered classifier; Amendment #1 only governs which channel the live signal reads.

**Amendment #2 (observation, MEDIUM) — Arm-B sub-strata.** Arm B contains two regimes: hardware primes (1-4%
civilian) and IT-services primes (53-61% civilian). *Proposed:* tag both in Phase 2 so the control can test
whether the civilian-posting-lag advantage produces edge even among *covered* names (isolating coverage-moat
from agency-channel-latency). No change to the ≥15-analyst Arm-B definition.

**Amendment #3 (mechanical) — entity resolution is curated, not zero-touch.** Add a hard gate: any name whose
family obligations don't tie to disclosed gov revenue within 0.4×–2.0× is UNVERIFIABLE and excluded from
scoring (currently blocks VSEC, CMTL). No change to any locked param.

---

## (5) What Phase 2 needs / is the pilot runnable?

**Runnable: YES, on the civilian-agency channel of Arm A vs the Arm-B control. NO as originally scoped if the
sub-threshold-defense leg is treated as a live signal (the 98-day lag makes it untradeable).**

Phase 2 requirements before any scoring:
1. **Point-in-time obligation panel.** Build a (name, quarter) panel of civilian-channel family obligations
   *as they were available* at each historical decision date — i.e. **censor every action whose load date >
   decision date** (the engine reads action_date; Phase 2 must add the load-date censor using `Last Modified
   Date`, otherwise the backtest leaks the ~0-day-but-occasionally-tail civilian posting lag). This is the §5
   point-in-time discipline and is the single biggest Phase-2 build item.
2. **Quarterly gov-revenue run-rate per name** (from 10-K/10-Q customer-concentration / gov-revenue disclosure)
   to normalize the §3 10% materiality threshold and the tie-out gate.
3. **Earnings-revenue-surprise labels** (consensus vs actual gov/total revenue) and a **drift window** net of
   borrow + bid/ask + a **gov/defense-ETF beta hedge** (ITA/XAR) — the §5 sector-beta confound control (the CEF
   kill mechanism). Pull live prices from IBKR at decision time; do not reuse stale spot.
4. **Curated alias map maintenance** for the scored names; exclude UNVERIFIABLE.
5. **Crowding note:** Bloomberg Gov / Govini cover the *defense* prime flow heavily; the uncovered tail is the
   civilian-agency small/mid-cap flow — which is exactly where the 0-day posting lag + ≤5-analyst coverage
   overlap. That intersection (fast-posting + uncovered) is the sharpest test of the moat.

**Expected kill conditions still apply (§6):** if Arm A ≈ Arm B, it's defense-sector beta (CEF kill). If the
civilian-channel signal in Arm A is insignificant, no edge. A negative result still encodes the
signal-to-price-latency microstructure for gov-contract data — which Phase 1 has already partly measured: the
latency is **0 days civilian / ~98 days defense**, and the obscurity is real but the tradeable surface is the
civilian, thinly-covered tail.

---

### Files
- `outputs/govcon_universe.json` — classified universe (2 arms + survivorship), per-name classifier values,
  matched/rejected recipients, entity-resolution summary.
- `outputs/govcon_posting_lag.json` — raw posting-lag rows + summary.
- `outputs/govcon_lag_by_agency.json` — the defense-vs-civilian lag split (the gating finding).
- `engine/award_flow.py` — the award-flow engine.
- `engine/test_award_flow.py` — tie-out unit tests (3/3 pass).
