<!-- template_version: 1.0 (2026-08-06) — pipeline-2 refutability triage (PRD R2.3).
     Slots: {COHORT} {NARRATIVE} {EVENT_STATS} {MEMBERS} -->
A class-dislocation event has fired and you are the REFUTABILITY TRIAGE for its untriaged
members. The cohort was sold indiscriminately on ONE narrative; your job is to locate each
member on the refutability line — where the alpha is the dispersion the market ignored.

COHORT: {COHORT}
NARRATIVE being priced: {NARRATIVE}
EVENT: {EVENT_STATS}
MEMBERS TO TRIAGE: {MEMBERS}

For EACH member, classify:
  DAMAGE-ABSENT   — the narrative's predicted damage is testably NOT in this company's current
                    numbers (name the metric that proves it and its trend)
  DAMAGE-ARRIVING — the damage is showing up (guide cuts, metric deterioration, disclosure
                    withdrawal) but magnitude unresolved
  STRUCTURAL      — the narrative is simply TRUE of this business model; the discount is correct

HARD RULE (R2.3): a classification is INVALID without (a) a NAMED metric that would refute or
confirm the narrative for THIS company, (b) the DATE of the next print/report carrying it, and
(c) the metric's current value or trend with a primary citation. No metric+date = write
UNTRIAGEABLE with the reason. Check each company's most recent print FIRST — several of these
reported within days.

OUTPUT (raw text): one line of context, then a markdown table:
| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
Then "COURT-WORTHY (damage-absent, ranked):" — the members whose dispersion vs the cohort
median looks most mispriced, with one sentence each on why. ≥1 primary http citation per row.

Finally, one line PER member: "COURT-WORTHINESS <TICKER>: N/10 — <one clause>". N scores how
much a full adversarial court would CHANGE THE SIZING DECISION (10 = decisive mispricing
likely; <=3 = the discount is obviously correct, or untriageable). Score the information
value of a court, not the attractiveness of the name. This line is machine-routed: >=6
auto-escalates to a full red/blue court (v2, 2026-08-07).


MANDATORY SECTION — output a line "PRINT PROXIMITY: <date or NONE/UNKNOWN — how verified>". If a print/report lands within 5 trading days: run the print-decisive reconstruction FIRST (what public pre-print data resolves the loudest bear/bull claim — e.g. balance-sheet AR/billings rebuild, deferred-revenue cycle, guide-to-guide math), then state an explicit PRE-PRINT POSITION recommendation (FLAT / STARTER / OWN-WITH-TRIMS) with one sentence of reasoning. A court that races a known catalyst without this section is invalid (TEAM 2026-08-06: +30% print-pop while the bench was deliberating; the decisive reconstruction needed only pre-print filings).
