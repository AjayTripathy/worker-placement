"""0DTE sleeve doctrine — every number the sleeve uses lives HERE, frozen and hashed.

Instrument: XSP (Mini-SPX, 1/10 SPX, $100 multiplier, CASH-settled PM, European — no assignment,
no pin risk at expiry, Section 1256 60/40 tax treatment). Single-stock / SPY 0DTE are excluded on
tax (short-term) and assignment grounds.

Default sizing: ONE contract, $2 wings.
Max loss per structure = $200 - credit. Caps below are in dollars, not percent, on purpose.

Climatology benchmark = T1_MECH. A template graduates only by beating T1 over GRADUATION_SESSIONS.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "desk" / "data" / "odte"
CHAINS = DATA / "chains"
SHADOW_LEDGER = DATA / "shadow_ledger.jsonl"
LIVE_LEDGER = DATA / "live_ledger.jsonl"
SCOREBOARD = DATA / "scoreboard.json"
UI_BOARD = ROOT / "desk" / "ui" / "static" / "odte_board.json"
HALT_FILE = DATA / "HALT"
LOCK_FILE = DATA / "runner.lock"
FROZEN = DATA / "templates_frozen.json"
EVENT_CALENDAR = DATA / "event_calendar.json"

ENVELOPE = "ODTE-XSP-LIVE"
ACCOUNT_ROLE = "ALPHA"

INSTRUMENT = "XSP"
UNDERLYING_CONID = 137851301
SPX_CONID = 416904
VIX1D_CONID = 627990891
MULTIPLIER = 100
STRIKE_STEP = 1.0
BAND_PCT = 0.025            # chain capture band around spot (±2.5% ≈ 34 strikes ≈ 68 data lines)

CONTRACTS = 1
WING_WIDTH = 2.0            # $ of XSP -> $200 max loss before credit
SHORT_DELTA = 0.10
MIN_CREDIT = 0.15           # $15 per structure; below this the premium cannot cover the touch
MAX_LEG_SPREAD_FRAC = 0.60  # bid-ask / mid on any leg above this = illiquid, skip the day
STOP_MULT = 2.0             # close when cost-to-close >= 2x credit (loss ≈ 1x credit)

ENTRY_ET = (10, 0)          # entry window opens (first 30 min of range is in)
ENTRY_CLOSE_ET = (10, 20)   # ... and closes; no entries after this
TIME_EXIT_ET = (15, 45)     # close anything still open (gamma hour)
CANCEL_ALL_ET = (15, 50)    # cancel any resting order of ours
SETTLE_ET = (16, 2)         # shadow settle on the 16:00 capture (XSP PM cash settlement proxy)
RTH_OPEN_ET = (9, 30)
RTH_CLOSE_ET = (16, 0)

FEE_RESERVE_USD = 3.0       # per structure, charged against the loss caps until the commission reports are in
DAILY_STRUCTURES = 1
WEEKLY_LOSS_CAP = 400.0     # two max losses -> no more live entries this ISO week
MONTHLY_LOSS_CAP = 800.0    # -> envelope PAUSED; needs re-ratification in chat
CONSECUTIVE_LOSS_PAUSE = 4  # -> envelope PAUSED
VIX1D_LEVEL_KILL = 35.0     # no live entry above this
VIX1D_JUMP_KILL = 0.30      # no live entry / flatten if VIX1D is +30% vs its 09:31 read
FIRST30_RANGE_KILL = 0.012  # SPX hi-lo in the first 30 min > 1.2% = no live entry

GRADUATION_SESSIONS = 60
GRADUATION_RULE = ("60 graded sessions AND (mean daily P&L - T1 mean) t-stat >= 2.0 AND max drawdown "
                   "<= 2x T1 max drawdown AND worst-5 sessions inspected one by one in the deck")

# Templates are the pre-registration. T1 trades EVERY session (the climatology); T3 is T1 with the
# event blackout (what real money follows); T2 is the regime-conditioned version (the edge claim).
TEMPLATES = {
    "T1_MECH": {"short_delta": SHORT_DELTA, "wing": WING_WIDTH, "stop_mult": STOP_MULT,
                "entry_et": ENTRY_ET, "entry_close_et": ENTRY_CLOSE_ET, "time_exit_et": TIME_EXIT_ET,
                "blackout": False, "regime": None,
                "claim": "intraday variance risk premium harvested mechanically — the benchmark"},
    "T2_REGIME": {"short_delta": SHORT_DELTA, "wing": WING_WIDTH, "stop_mult": STOP_MULT,
                  "entry_et": ENTRY_ET, "entry_close_et": ENTRY_CLOSE_ET, "time_exit_et": TIME_EXIT_ET,
                  "blackout": True,
                  "regime": {"first30_range_max": 0.006, "vix1d_compressing": True},
                  "claim": "the premium is only worth selling when the first 30 min is quiet (<0.6% SPX range) "
                           "AND VIX1D at entry <= VIX1D at the open (vol compressing, dealers long gamma)"},
    "T3_BLACKOUT": {"short_delta": SHORT_DELTA, "wing": WING_WIDTH, "stop_mult": STOP_MULT,
                    "entry_et": ENTRY_ET, "entry_close_et": ENTRY_CLOSE_ET, "time_exit_et": TIME_EXIT_ET,
                    "blackout": True, "regime": None,
                    "claim": "T1 minus FOMC/CPI/NFP/half-days — what the live contract follows"},
}
LIVE_TEMPLATE = "T3_BLACKOUT"
BENCHMARK_TEMPLATE = "T1_MECH"

# Optional live execution follows a sealed research selection; --live remains explicit.
# The initial order must match the decision's date, protocol, entry timestamp,
# snapshot digest, legs, quotes, credit and maximum risk. Missing/skip/mismatched
# decisions stand down. Calibration is tracked; predictive skill is not assumed.
# Maker entry posts at mid, waits MAKER_PATIENCE_S, then allows one lower post
# after confirmed cancellation and fresh entry-risk checks. Never retry an
# unacknowledged intent. Stops and time exits use the existing marketable ladder.
# Actual fills versus touch are descriptive execution observations, not an
# arm promotion or evidence of positive expectancy.
LIVE_POLICY = {"follow": "arm_selector", "fallback": "stand_down", "execution": "maker"}
MAKER_PATIENCE_S = 120
MAKER_STEP = 0.01
MAKER_RETRIES = 1
MAKER_EXIT_PATIENCE_S = 30
MIN_MAKER_IMPROVEMENT = 0.01   # if mid - touch < this there is nothing to earn: post at the touch


def template_hash(name: str) -> str:
    return hashlib.sha256(json.dumps(TEMPLATES[name], sort_keys=True, default=str).encode()).hexdigest()[:16]


def freeze() -> dict:
    """Write the template hashes once; a later edit that changes a hash is a NEW pre-registration
    (the grader refuses to pool sessions across hashes)."""
    DATA.mkdir(parents=True, exist_ok=True)
    cur = {k: template_hash(k) for k in TEMPLATES}
    if FROZEN.exists():
        old = json.loads(FROZEN.read_text())
        changed = {k: (old.get("hashes", {}).get(k), v) for k, v in cur.items() if old.get("hashes", {}).get(k) not in (None, v)}
        if changed:
            old.setdefault("history", []).append({"hashes": old.get("hashes"), "frozen": old.get("frozen")})
            old["hashes"] = cur; old["frozen"] = __import__("datetime").date.today().isoformat(); old["changed"] = changed
            FROZEN.write_text(json.dumps(old, indent=1))
        return old
    rec = {"hashes": cur, "frozen": __import__("datetime").date.today().isoformat(), "history": []}
    FROZEN.write_text(json.dumps(rec, indent=1))
    return rec
