# U3 — App courts vs desk-native courts: the dogfood diff (2026-09-05)

Three names from the desk's 2026-09-04 band-touch trio (LULU / STZ / HOFT), each with a
same-day desk-native adjudication (Opus benches via the desk runner, Fable adjudication
in-session, full SignalOS evidence). App courts convened on the same names with the same
band-touch question as mandate context, twice: **flat-tier** (Opus benches + Opus
adjudicate — the product default) and **tiered** (Opus benches + `claude-fable-5`
adjudicate via the API — the desk's tier policy). Evidence packs: the promoted
`officekit_research` layer (filings / XBRL / tape / book), all four sources live.

## Scorecard

| Name | Desk-native | App flat-tier | App tiered (Fable) | Direction |
|---|---|---|---|---|
| LULU | FLAT into 9/8, band withdrawn, mechanism-gated 0.5% starter | STARTER 5/10 — band VOID, withdraw; name not killed | STARTER 6/10 — §CONSENSUS-KILL + §CLEAN-COURT-MINIMUM-STARTER: no named kill, zero must be earned | ✅ all three: band dead, name alive, small-starter-class |
| STZ | Red OVERTURNED — advance post-print ≤$126, 0.4–0.5% | WATCH 6/10 — red's valuation uncomputed (PLAUSIBLE cannot carry); band untouched on closes | STARTER 5/10 — red's conditional stale-anchor kill is a WORK-QUEUE item, not a kill | ✅ no chase now; sizing philosophy differs (see below) |
| HOFT | Band dead (stale vintage), FLAT into 9/11, WATCH-with-gate | WATCH 7/10 — no trigger on tape (FCT.MI), TENX blocks on missing balance sheet, 2 unread 8-Ks flagged | WATCH 7/10 — "cannot fill and should not withdraw" | ✅ exact match |

**3/3 direction agreement at BOTH tiers.** No app court chased a dead band, killed a
living name, or advanced past its evidence.

## What the transcripts show

- **The distilled doctrine is fully operational.** Adjudicators cited §BANDS-OVER-RESTING-GTC
  (LULU's 9/8 catalyst inside the resting window — the same section the desk applied),
  §CONSENSUS-KILL, §CLEAN-COURT-MINIMUM-STARTER, §VERIFICATION-BEFORE-ADVANCE, the TENX
  cap-structure rule, and the FCT.MI/SLS tape-verify reflexes — by name, correctly.
- **Never-rubber-stamps held.** The LULU adjudicator re-verified blue's revenue
  decomposition to the dollar (2,415,631 + 2,471,603 = 4,887,234); the STZ adjudicator
  refused to let a memory-reconstructed valuation carry a verdict (graded PLAUSIBLE).
- **The tier effect is real and matches the desk's empirical finding.** Fable adjudication
  sharpened both movable verdicts: LULU 5→6 with the minimum-starter doctrine correctly
  invoked; STZ WATCH→STARTER by correctly reclassifying red's conditional kill as
  work-queue. The strong-model checkpoint grades bench claims harder — same conclusion as
  the desk's 2026-08-22 tier ruling.
- **A doctrinal tension surfaced worth ruling on:** on LULU the desk withheld the starter
  pending a NAMED mechanism (verification-before-advance posture); the tiered app court
  granted the minimum starter because no NAMED kill existed (clean-court-minimum-starter
  posture). Both are ratified doctrine; they pull opposite ways on borderline names. The
  desk had one extra fact (the Q4 margin-mechanism gap from a deep filing read) that
  arguably names the gate — but the tension is real and predates the app.

## Gap taxonomy → F2 work list

Every divergence traced to evidence, not deliberation quality:

1. **Print proximity** — the desk pack's PRINT section (next earnings date) was not ported
   in F1; the STZ desk ruling deferred entry past a print the app court couldn't see.
   → port the print-date evidence source.
2. **Balance-sheet depth** — the XBRL battery lacks cash/debt/share-count point-in-time
   tags, so TENX correctly blocked per-share claims (HOFT) and benches couldn't compute
   the bond-dominance floor (STZ, the desk's red-overturn). → extend the XBRL tags.
3. **Intraday tape** — the free endpoint is close-only; band *touches* are invisible
   (STZ 128.18-vs-126, HOFT 13.12-vs-12.50 on closes). → broker tape plugin slot (desk
   registers its gateway).
4. **Desk-internal state** — band provenance, prior courts, flow-gate history (LULU's
   collar-floor decoration, HOFT's stale XBRL vintage) live in desk records. The app
   already owns adjudications.jsonl and the book; the pack should carry prior
   adjudications + band context. → pack params.

## Verdict

The app court is **usable for desk work now** at the tiered config: it reached the desk's
conclusions on all three names with honest, doctrine-cited reasoning and refused exactly
what its evidence couldn't support. The four gaps above are data plumbing (F2), not
architecture. Cost per tiered court: ~$1.50–2.50.

---

## Addendum — the approval-side test (LGN, 2026-09-05)

The trio were all rejection-class outcomes; a court that rejects everything is a wall
(ratchet-check doctrine). Test: LGN, which the desk court APPROVED 2026-09-04 (starter 0.4%,
70sh @ ≤$52.60, blue overturn of the comp-settlement kill verified at primary). The app court
ran tiered (Opus benches, Fable adjudicate) with the new `filing_text` evidence source — the
full 10-Q text in the pack (ported for this test; closes F2 gap #2's document half).

**App verdict: STARTER 4/10 (EVIDENCED), 0.25% gated starter floor — direction MATCH.** Not a
wall: §CLEAN-COURT held ("no named kill exists — FLAT is forbidden").

What happened inside it:

1. **The decisive read reproduced.** The bench found the Note 11 Management-Aggregator language
   in the pack text and reached the desk's overturn independently: parent-settled,
   non-dilutive today, $101.7M offset dollar-for-dollar by parent contributions, ~$10.2M
   issuer-level. The evidence port made the desk's key finding reproducible.
2. **The app court found things the desk adjudication did not record** (all pack-grounded,
   flagged for desk verification, not assumed correct):
   - the $342.7M related-party TRA liability (+$135.3M in six months) + $47.4M deferred
     consideration as quasi-debt omitted from the screen's EV — the "11.8x vs EMCOR"
     premise swings ~12.7x–20.5x on comp-add-back conventions (basis-artifact class);
   - a NOVEL red finding: the parent-settled comp is NON-DEDUCTIBLE, producing $11.1M tax
     expense on a Q2 pre-tax loss — a bounded, decaying, real issuer cash leak (a
     second-order channel through which some cost DOES reach the issuer);
   - the mandate's "~47% sponsor" figure graded stale (28.8% NCI; 13G/13G-A refs cited).
3. **Doctrine discipline held under an approval:** §BLUE-CORRECTIONS-AUDITED applied to its
   own blue's omnibus-plan correction; §DIVERGENCE consensus-number gap declared; Gate 1 of
   its mandatory pack is the identical-conventions multiple reproduction that can flip it
   to FLAT.

**Desk follow-up owed (real position):** LGN is a live staged starter. The desk should verify
the app court's three novel findings (TRA-inclusive EV multiple, non-deductible comp tax
leak, sponsor-stake staleness) at its next LGN touch — the first case of the app court
feeding the desk, not just mirroring it.

**Infra hardened by this test:** `filing_text` evidence source (150k-char cap, loud
truncation); bench output caps 16k→30k (truncation guard fired correctly on a document-heavy
bench); streaming transport for long courts (SDK requirement). Cost of the LGN court: ~$4.
