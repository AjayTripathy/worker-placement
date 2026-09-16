# BOOK_REVIEW — SignalOS Rigor Pass on the Consolidated Book

*Reviewer: SignalOS (verification + honesty-alpha layer). Date 2026-06-26. Scope: verify the
existing book (BOOK_REPORT.md) against live prices + the per-name backing DDs. Not a re-diligence.*

Verdict on the book as a whole: **SHIPPABLE with 5 fixes.** The per-name DDs are high-quality and
the report's verdicts are, with a few exceptions, faithful to them. The honesty-alpha discipline is
intact — the report does NOT over-mark honestly-disclosed-bad-news names as catches (INSP/ESTA/EPAM
all correctly graded CLEAN-but-dislocation, not liar-exclusion). The fixes below are about
**staleness** (two catalyst dates have passed; one DD's FV is pre-revision) and **two entry bands
that live price has invalidated**, not about thesis errors.

---

## 1. FACT / PRICE FRESHNESS SPOT-CHECK (live IBKR, 2026-06-26)

| Name | Live | Report entry band | Report FV (bear/base/bull) | In band? | Flag |
|---|---|---|---|---|---|
| **GCT** | **$32.03** | 32–25 | 24/43/60 | YES (top edge) | clean; starter-level, add lower |
| **DFIN** | **$40.55** | 42–36 | 45/56/60 | YES (mid-band) | clean; best risk/reward in basket |
| **EOLS** | **$7.13** | <$6 (put→~$6) | (turnaround) | NO — above band | accumulate target not yet hit; WATCH |
| **INSP** | **$45.72** | 42–38 | 30/60/95 | NO — ~9% above top | just out of band; event-gated; WATCH |
| **ESTA** | **$88.00** | 74–70 (add <70) | 58/92/120 | NO — far above band | at 52-wk high / consensus PT; do NOT chase |
| **EVER** | **$22.70** | 23–18 | 25/38/41 | YES (top edge) | half-size only (40% customer concty) |
| **EPAM** | **$80.50** | ≤80 starter | 65/115/131 | YES (right at line) | starter only; inflection unproven |
| **SBH** | **$14.46** | 15–12 | 16/20/22 | YES (mid-band) | clean; value, not compounder |
| **INMD** | **$14.63** | 13–12 (add <13) | 11/16.2/18.5 | **NO — STALE BAND** | see fix #2 (MBO repriced it) |
| **LRLCY** | **no quote** | 350–375 (EUR) | 310/400/455 | n/a | ADR dead (report says so); trade Paris EUR |
| **COSMECCA** | not in IBKR US | 62.9k–54k KRW | 40k/67k/110k | n/a | KRX-direct; ~66.5k at last DD = above starter |

**Price-driven conclusions:** Only **GCT, DFIN, EVER, EPAM, SBH** are actually in-band right now.
ESTA, INSP, EOLS, INMD are all WATCH-only on price. LRLCY and COSMECCA are not US-tradeable on this
feed (the report already discloses both — not a defect).

---

## 2. INTERNAL-CONSISTENCY + OVERCLAIM AUDIT (the 5 fixes)

### FIX #1 — COSMECCA: the backing DD's FV is PRE-REVISION (stale file, not a thesis error)
- BOOK_REPORT FV = **40k / 67k / 110k**; the DD file (COSMECCA_dd.md) still prints **48k / 82k / 108k**
  and says "base FV revised 82k→67k."
- The **report is the newer, correct artifact** (it pulled the bull-year EPS forward and stripped the
  peer-premium multiple). The DD file is stale. **Action: the report is fine to ship; the DD .md
  should be reconciled to the 67k base before it's used as backing.** Flag, not a block.

### FIX #2 — INMD: entry band is STALE; catalyst date has PASSED (material)
- Report says entry **13–12, add only <$13**, catalyst "**2026-06-15 MBO vote**."
- Reality (from INMD_dd.md + live): the Jun-15 event was the CEO-led **non-binding $16.20 take-private
  OFFER** (not a "vote"); the stock **gapped $13.35→$14.79 on Jun-24** when confirmed, live **$14.63**.
- So the "$13–12 entry" will **not fill unless the deal breaks**, and this is now a **merger-arb
  spread (+10.7% to $16.20)** with standalone value as the downside — NOT a contrarian-value entry.
- **Action: relabel INMD verdict from "standalone-value add <$13" to "MBO-ARB / EVENT (+10.7% gross
  spread, controller-as-buyer take-under risk)." The current band is decision-misleading.**

### FIX #3 — ESTA: verdict text vs price (over-actionable framing)
- Report row reads "WAIT … buy low-$70s, add <$70" with a tidy 74–70 band — but live is **$88**, at
  the 52-wk high and AT consensus PT. The DD itself says "the easy re-rating is largely realized…
  don't chase $89." The report row is internally consistent (it IS a WAIT) but a fast reader sees
  "buy low-$70s" next to a name 25% above that. **Action: keep WAIT, but annotate "spot $88 = NO-TOUCH,
  band is ~20% below market" so it can't be misread as actionable.**

### FIX #4 — INSP: out-of-band but verdict still says WATCH (OK) — just note the gap
- Report band 42–38; live **$45.72** (+9% above top). Verdict WATCH is correct, but the name is a
  "**falling-knife-until-the-Sept-CPT-panel**" per the DD — entry is event-gated, not a dip-buy.
  **Action: minor — confirm the WATCH note carries "do not chase strength ahead of Sept 2026 panel."**
  No thesis change.

### FIX #5 — EOLS: live $7.13 vs accumulate-<$6; the report already says "no pre-buy yet" — consistent
- Report: "accumulate <$6 (Oct $7.5 put→~$6 basis)." Live $7.13 → the put route is the only entry;
  spot is above the cash-accumulate line. Consistent, **no fix needed**, but list it as WATCH not
  actionable. The tariff DD confirms the drag is real-but-small (~1–3 GM pts), thesis intact.

### OVERCLAIM SCAN — where does marketed takeaway diverge from the DD finding?
- **GCT "THE high-conviction find" / HIGH tier** — the DD *supports* this (clean audit, trapped-cash
  refuted, 5.1x EV/EBIT). BUT the honest catch the DD surfaces — **"it's a 1P distributor/3PL at
  29.8% GM, NOT the asset-light marketplace bulls sell"** — IS carried into the report row. Good. No
  overclaim; the controlled-co (Wu 70.7% vote) discount is disclosed. **AGREE with HIGH, basket-sized.**
- **DFIN "HIGH"** — DD grades REAL/CHEAP, "no takeaway-vs-data divergence found," clean cap structure,
  software 47% rev / 45% profit, pension hit is non-cash. **No overclaim. AGREE — arguably the
  single cleanest name in the book.**
- **EVER "MED (HALF-SIZE)"** — DD says "REAL (lean)" with the 40%-single-customer concentration
  capping size. Report's HALF-SIZE label matches the DD exactly. **No overclaim.** (Note SBC = 33% of
  EBIT — anyone quoting adj-EBITDA multiples is adding back a third of earnings; the report uses the
  honest EV/EBIT, good.)
- **EPAM "MED (STARTER)"** — DD: "FAIR-to-REAL, leaning REAL on a starter only … inflection unproven."
  Report's "STARTER, not a conviction core" matches. **No overclaim.** Watch: revolver now DRAWN
  ($165M), net-cash cushion thinner than the screen implied — already in the DD.
- **SBH "MED-LOW"** — DD: "REAL (lean) … return is buyback + de-lever, not growth." Report says the
  same ("re-rate + buyback + de-lever, NOT organic growth"). **No overclaim.**
- **INSP / ESTA / EPAM honesty grades** — all three are honestly-disclosed dislocations graded CLEAN
  in their DDs, and the report does NOT dress them up as liar-exclusion catches. This is the
  honesty-alpha framework applied correctly (impaired-but-honest = CLEAN; alpha here is fundamental
  dislocation, not exclusion). **No divergence.**

**No contradiction found between any thesis and its own KILL trigger.** FV-vs-multiple math checks
out on the names I recomputed (DFIN 11x×$144M EBIT − $204M ND ÷ 25.3M ≈ $54.5 ✓; GCT prob-weighted
$41 reconciles to trap-filter $42 ✓; SBH 6.2x adj EV/EBIT ✓).

---

## 3. GRADED SCORECARD (one word each; AGREE / CHANGE vs report)

| Name | My grade | Report verdict | Agree? |
|---|---|---|---|
| **GCT** | **ACCUMULATE** | HIGH / 32–25 | AGREE (starter now, add into high-$20s) |
| **DFIN** | **OWN-NOW** | HIGH / 42–36 | AGREE — in-band, cleanest thesis |
| **EVER** | **ACCUMULATE (half)** | MED half-size | AGREE |
| **EPAM** | **SHOW-ME** | MED starter | AGREE (starter ok, but inflection unproven → SHOW-ME not ACCUMULATE) |
| **SBH** | **ACCUMULATE** | MED-LOW | AGREE |
| **INMD** | **EVENT** | "standalone <$13" | **CHANGE → EVENT/arb** (band stale) |
| **ESTA** | **WATCH** | WAIT | AGREE (NO-TOUCH at $88) |
| **INSP** | **WATCH** | WAIT | AGREE (event-gated, Sept panel) |
| **EOLS** | **WATCH** | accumulate <$6 | AGREE (above line; put-only entry) |
| **LFMD** | **WATCH** | wait $3.0–3.5 | AGREE (unproven turn) |
| **STVN** | **WATCH** | above band | AGREE (demand de-risked, price not) |
| **GALD/LRLCY/PGNY/WST** | **WATCH** | WAIT (quality-at-full-price) | AGREE — all "wait for the dip" |
| **HUGEL** | **EVENT** | event-gated | AGREE (control-auction; refi = hold not sell) |
| **BRBR/HIMS/ODD/SILICON2** | **SHOW-ME / AVOID** | SHOW-ME / AVOID | AGREE (broken/over-promo'd) |
| **VERU** | **AVOID (binary)** | BINARY accumulate 1.8–2.4 | AGREE — structure-trap ($3 warrant wall), single-asset |
| **BKE/CRCT** | **WATCH (income)** | LOW income-value | AGREE — paid-to-wait, take-under risk on CRCT |
| **COSMECCA** | **WATCH** | ACCUM <62.9k | AGREE on plan, but DD FV stale (fix #1) |
| **COSMAX** | **WATCH** | WAIT | AGREE (margin-inflection refuted by own deck) |

**Names I'd DOWNGRADE from the report's framing:** only **INMD** (from value-entry to event/arb — a
*reclassification*, the underlying read is fine) and a soft EPAM (MED-starter → SHOW-ME; the AI-
disruption secular question is genuinely unverifiable, so it's not yet accumulate-grade). Nothing in
the book is an over-marked REAL that the DD actually graded FAIR/lean and tried to dress up.

---

## 4. THE VERIFIED ACTIONABLE SET ("what would you actually buy today")

**In-band + conviction holds (genuinely actionable now):**
1. **DFIN $40.55** — OWN-NOW. Mid-band, FCF yield ~10–14%, 1.4x lev, ~5%/yr buyback, clean cap
   structure, software 47% rev / 45% profit. The single cleanest risk/reward.
2. **GCT $32.03** — ACCUMULATE (starter). Top-of-band; net-cash 31% of mcap, 5.1x EV/EBIT, trapped-
   cash refuted. Basket-size only (controlled-co + undisclosed China-origin GMV). Add into high-$20s.
3. **SBH $14.46** — ACCUMULATE. Mid-band, positive comps, de-levering, ~10–14% FCF yield. Value, not
   growth — return is buyback + de-lever.
4. **EVER $22.70** — ACCUMULATE HALF-SIZE. Top-of-band; net cash, ~11% FCF yield, but 40% one-customer
   concentration is the hard cap.
5. **EPAM $80.50** — STARTER ONLY (SHOW-ME). Right at the ≤$80 line; 6.2x EV/EBIT, net-cash, 14.6%
   FCF yield — but organic growth low-single-digit and decelerating; don't size up until cc-organic
   turns or AI-billable-hours fear resolves.

**Watch-only (price out-of-band OR catalyst-gated — do NOT buy today):**
ESTA (chasing 52-wk high), INSP (wait for Sept CPT panel / Q2 trough), EOLS (put-only, <$6),
LFMD, STVN, GALD, LRLCY, PGNY, WST, BEI.DE, ELF, CRDA, COSMECCA, COSMAX, BKE, CRCT.

**Event / arb:** INMD (+10.7% MBO spread, take-under risk), HUGEL (control-auction), VERU (binary).

---

## 5. UNVERIFIABLE / STALE — refresh before this is decision-grade

1. **INMD band + catalyst label are STALE** (fix #2) — the "$13–12 / Jun-15 vote" framing predates the
   Jun-24 deal confirmation. Reprice as MBO-arb. *(Highest priority — it's decision-misleading.)*
2. **COSMECCA DD .md FV is pre-revision** (48/82/108 vs report's 40/67/110) — reconcile the backing
   file to the report (fix #1).
3. **Korean / European names have NO live US quote** — LRLCY ADR returned an empty quote (dead/
   illiquid PINK; trade Paris EUR), COSMECCA/COSMAX/SILICON2/HUGEL are KRX-direct (close-only on
   IBKR). Any sizing on these needs a KRX/Euronext fill check, not the US feed. The report already
   discloses this; just don't treat the FV bands as executable on IBKR US.
4. **GCT China-origin GMV %** — never disclosed in filings; the tariff-bear can't be precisely sized.
   This is why GCT is basket-size, not concentrate. UNVERIFIABLE ≠ clean — carry it as a live risk.
5. **EOLS tariff stockpile** — only stated-intent on the balance sheet as of Mar-2026; the real
   pre-buy should show up in the Q2 (Aug) and Q3 (Sept) 10-Qs as inventory >$33M / >4 months. Verify
   before underwriting the mitigation.
6. **INSP coding-vs-GLP-1 split** of the $120–150M FY26 impact — management would not separate them;
   the swing uncertainty. UNVERIFIABLE.
7. **Report compile date reads "2026-06-26"** in the header line but says "Compiled 2026-06-26 from
   the live watch dicts" — fine; just confirm all live prices in the report body were refreshed to
   today (several entry bands were set at prices that have since moved: ESTA $69→$88, INMD $13→$14.6).

---

### One-line ship call
Ship it after fixing INMD's label (#2) and reconciling the COSMECCA DD file (#1). The thesis work is
sound and honesty-graded correctly; the only real defects are staleness on two names whose catalysts/
prices moved after the bands were written. **Buy-today list: DFIN, GCT, SBH, EVER (half), EPAM
(starter).** Everything else is watch/event.
