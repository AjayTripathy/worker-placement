"""eVTOL cohort outcomes — REVEALED ONLY at confusion-matrix time.

Kept separate from evtol_cohort.py so the cohort module the subagent reads
contains NO outcome labels. Subagents extracting claims and assigning
severities should NEVER read this file.

Cohort cutoff is 2024-06-30. LILM is the only confirmed bankruptcy in window
(filed Oct 2024). EVEX/EVTL/SRFM are 'still trading' as of writing but with
operational signal varying. JOBY/ACHR are the cleanest live names.
"""

OUTCOMES = {
    "joby": ("ALIVE",
             "Joby Aviation alive; Toyota partnership active; FAA Type Cert "
             "progress; pre-revenue. Confirmed alive."),
    "achr": ("ALIVE",
             "Archer Aviation alive; United Airlines order standing; "
             "Stellantis manufacturing partner; Covington GA plant operational. "
             "Confirmed alive."),
    "evex": ("ALIVE",
             "Eve Holding (Embraer subsidiary) alive but pre-revenue; AAL LOI "
             "for hundreds of aircraft. Status pending — falsifiable forward "
             "prediction window in eVTOL forward-test case study."),
    "lilm": ("BANKRUPT",
             "Lilium GmbH filed Chapter 11 Oct 2024 (~4mo post-cutoff). Confirmed."),
    "evtl": ("ALIVE_STRUGGLING",
             "Vertical Aerospace UK-HQ; pennystock concerns; cash runway tight. "
             "Trading as of writing; status soft."),
    "srfm": ("ALIVE_STRUGGLING",
             "Surf Air Mobility direct listing 2023; mostly fixed-wing operations + "
             "eVTOL future; trading as of writing; status soft."),
}
