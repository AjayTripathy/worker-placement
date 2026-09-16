# MAUDE Complaint-Velocity → Class I Recall — Phase 2 Result (2026-06-25)

**Pre-registered spec:** `MAUDE_VELOCITY_SPEC.md` (LOCKED before data). Motivated by the
PODD/Insulet recall post-mortem question: *could we have predicted the recall announcement
from the public adverse-event stream that accumulates before a firm decides to recall?*

## Verdict: **KILL on specificity** (§6 kill branch). The public MAUDE velocity channel does NOT predict Class I device recalls with tradeable specificity.

## Phase 1 feasibility (PASSED — reported before scoring)
- Class I device recalls 2015–2024: **2,178**; product_code Z-join (enforcement→recall.json): **100%**.
- MAUDE-cell resolution (≥10 MDRs in 760d): **70%**.
- **MAUDE reporting lag `date_received − date_of_event`: median 25d** (p25 21 / p75 36 / p90 106).
  Survivable for a months-long slow-burn; likely fatal for a sudden lot defect — matched the prior.
- Root-cause buckets balanced: SLOW_BURN 44 / SUDDEN 39 / AMBIGUOUS 28 (structured FDA field, amendment M-1).

## Phase 2 scoring (N=111 events → 53 with a definable baseline)
| metric | value | read |
|---|---|---|
| **Sensitivity** | **0.17** (9/53) | spike fires before only 17% of recalls — misses 83% |
| Median lead \| fired | 77d (range 14–346) | long lead *when* it fires… |
| **Precision** | **0.50** (9 real / 9 control fires) | …but **likelihood ratio ≈ 1.0** — fires in a matched no-recall window exactly as often |
| Control specificity | 7 of 9 control fires were in cells that did **NOT** fire at the real recall | the spike points at non-events and is silent at the real one |
| **Leak-check** | **+46.5d** phantom-lead inflation on `date_of_event` | censoring discipline mattered — leaky axis manufactures a much stronger false edge |

By bucket (directional sub-hypothesis): SLOW_BURN median lead 122d (n=3) > SUDDEN 346d (n=1, noise) /
AMBIGUOUS 54d (n=5). The slow-burn lead is *directionally* consistent with the prior but **N is far
too small to claim, and specificity kills it regardless.**

## Why it fails (the durable microstructure finding)
The fired cells are dominated by **high-volume reporting codes** (Medtronic NVZ baseline 230/30d,
CareFusion FRN 154, Allergan FTR 122). In high-volume cells a "3-sigma velocity spike" is triggered by
**reporting dynamics — batch MDR submissions, litigation-driven reporting, media attention — not by an
emerging defect.** That is exactly why the spike fires in random control windows as often as before
recalls (precision 0.50), and why the surviving "leads" run up to 346 days — implausibly long to be
causally tied to the specific recall. **MAUDE velocity measures reporting behavior, not defect
emergence.** Combined with the 25-day public reporting lag (the firm sees its un-lagged internal
complaint inflow weeks before us), the public stream is both too **insensitive** (misses 83%) and too
**non-specific** (LR≈1) to frontrun a recall.

## Relation to the PODD question that prompted this
PODD's specific recall (Mar 2025, sudden internal-tubing lot defect) sits in the SUDDEN bucket and
outside the test window, but the general result confirms the post-mortem's honest conclusion: the recall
*announcement* was **not predictable** from the public adverse-event stream. The optimistic "slow-burn
is frontrun-able" prior is **not supported** once the precision control is applied — the lead-only
framing (which the naïve version of this idea would have stopped at) is exactly what the spec's §4
precision control was built to catch, and it did.

## What survives (kept as tools, not strategy)
1. The **engine** (`engine/maude_velocity.py`) — point-in-time MAUDE velocity by (firm × product_code)
   with `date_received` censoring — is retained as a **diligence connector** (is a name's adverse-event
   reporting abnormally elevated *right now*?), not a frontrun signal.
2. The **leak-check (+46.5d)** is a textbook demonstration of the censoring rule (sibling to gov-contract
   G-4 load-date) — encode as methodology.

## Frontrun taxonomy (now 3 clean negatives, each breaking a DIFFERENT required link)
- CEF/BDC NAV → input already continuously priced.
- Gov-contract award-flow → input (obligations) doesn't predict the number (revenue).
- **MAUDE velocity → the signal isn't specific to the event (fires on noise, LR≈1) and misses most events;
  the public stream also lags the firm's internal view by ~25d.**

The discipline (pre-registration + reporting-lag feasibility gate + `date_received` censoring +
matched-control precision + bucket split) produced a clean negative and the leak-check caught the phantom
edge — the methodology working as designed, not a disappointment.
