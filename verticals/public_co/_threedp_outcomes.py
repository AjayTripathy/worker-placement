"""3D printing cohort outcomes — REVEALED ONLY at confusion-matrix time.

Kept in a separate module so the cohort definition (threedp_cohort.py) and the
input.json / scores.json files written by the analyst/subagent contain NO
outcome labels. Subagents extracting claims and assigning severities should
NEVER read this file.

Outcomes as known to the cohort author at the time of cohort assembly. Confidence
varies; the cleanest ground-truth pair is VLD (Chapter 11 confirmed Sep 2024)
vs SSYS / MTLS (profitable industrial 3D printing leaders).
"""

OUTCOMES = {
    "vld":  ("BANKRUPT",
             "Velo3D Chapter 11 filed Sep 2024 (~6mo post-cutoff). Confirmed."),
    "vjet": ("DELISTED",
             "voxeljet ADR delisted from NYSE 2024 amid funding distress. Confirmed."),
    "dm":   ("ACQUIRED_DISTRESSED",
             "Desktop Metal acquired by Nano Dimension Q2 2025 after distress; "
             "deal repeatedly renegotiated downward. Confirmed."),
    "mkfg": ("ACQUIRED_DISTRESSED",
             "Markforged acquired by Stratasys 2025 at deep discount to deSPAC valuation. "
             "Confirmed."),
    "ssys": ("ALIVE",
             "Stratasys profitable industrial AM leader; rejected Nano Dimension takeover. "
             "Confirmed alive."),
    "mtls": ("ALIVE",
             "Materialise profitable medical/industrial AM. Confirmed alive."),
    "nndm": ("ALIVE",
             "Nano Dimension cash-rich acquirer; growth-side weak but solvent. Alive."),
    "xmtr": ("ALIVE",
             "Xometry on-demand manufacturing marketplace; growing, not profitable. Alive."),
}
