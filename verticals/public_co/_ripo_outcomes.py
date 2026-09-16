"""RIPO-cohort outcomes — REVEALED ONLY at confusion-matrix time.

Kept separate from ripo_cohort.py so the cohort module the subagent reads
contains NO outcome labels. Subagents extracting claims and assigning
severities must NEVER read this file.

Labels come from the survivorship-free backtest (verticals/buyside_dd/.../
_ipo_backtest_2024_2025/outcomes.json), post the merger-delist labeling fix.
'catastrophe' == price drawdown <= -50% from first-day close OR EDGAR hard-
adverse, as of 2026-05-29. r_current = latest close / first-day close - 1.

Of the 25 RIPO-held cohort names, 3 are catastrophes. Two names (ZEEKR,
OneStream) were taken private for cash — NOT failures, excluded from the
return basket; both are non-catastrophes here.
"""

# ticker -> (label, r_current, note)
OUTCOMES = {
    # --- 3 catastrophes ---
    "PACS": ("CATASTROPHE", 0.5833,
             "EDGAR hard-adverse: short-seller report + delayed 10-K / "
             "restatement-class event flagged catastrophe, BUT the stock "
             "RECOVERED (+58% vs first-day close by 2026-05-29). Hard-event "
             "catastrophe whose price round-tripped."),
    "VG":   ("CATASTROPHE", -0.4731,
             "Venture Global -47% from first-day close; offtaker arbitration "
             "(Shell/BP) over Calcasieu Pass cargo allocation; major drawdown."),
    "CHYM": ("CATASTROPHE", -0.5123,
             "Chime -51% from first-day close (priced 2025-06-12, recent IPO; "
             "post-IPO de-rating of neobank multiple)."),

    # --- 22 non-catastrophes ---
    "BTSG": ("SURVIVOR", 4.53,    "BrightSpring +453%."),
    "AS":   ("SURVIVOR", 1.4107,  "Amer Sports +141% (Arc'teryx strength)."),
    "ALAB": ("SURVIVOR", 4.443,   "Astera Labs +444% (AI datacenter demand)."),
    "RDDT": ("SURVIVOR", 2.3245,  "Reddit +232% (data-licensing + ad growth)."),
    "ULS":  ("SURVIVOR", 1.8947,  "UL Solutions +189%."),
    "LOAR": ("SURVIVOR", 0.3114,  "Loar +31%."),
    "RBRK": ("SURVIVOR", 0.8505,  "Rubrik +85%."),
    "VIK":  ("SURVIVOR", 2.4213,  "Viking +242% (cruise demand)."),
    "ZEEKR":("MERGER_CASHOUT", None,
             "ZEEKR taken private by Geely (CB tender 2025-08). Shareholders "
             "cashed out; NOT a failure; excluded from return basket."),
    "WAY":  ("SURVIVOR", -0.0633, "Waystar -6% (roughly flat)."),
    "TEM":  ("SURVIVOR", 0.406,   "Tempus AI +41%."),
    "LB":   ("SURVIVOR", 2.2811,  "LandBridge +228% (data-center land deals)."),
    "ONESTREAM": ("MERGER_CASHOUT", None,
             "OneStream taken private. Cash-out; NOT a failure; excluded."),
    "LINE": ("SURVIVOR", -0.4257, "Lineage -43% (cold-storage REIT de-rate; "
             "NOT a catastrophe by the -50% threshold)."),
    "SARO": ("SURVIVOR", -0.1359, "StandardAero -14%."),
    "PONY": ("SURVIVOR", -0.17,   "Pony AI -17%."),
    "TTAN": ("SURVIVOR", -0.3486, "ServiceTitan -35% (not past -50%)."),
    "KRMN": ("SURVIVOR", 1.1917,  "Karman +119% (defense/space demand)."),
    "SAIL": ("SURVIVOR", -0.3259, "SailPoint -33%."),
    "CRWV": ("SURVIVOR", 1.8819,  "CoreWeave +188% (AI infra)."),
    "CRCL": ("SURVIVOR", 0.3005,  "Circle +30%."),
    "CAI":  ("SURVIVOR", -0.3883, "Caris -39% (not past -50%)."),
}

CATASTROPHES = {t for t, (lab, *_ ) in OUTCOMES.items() if lab == "CATASTROPHE"}
