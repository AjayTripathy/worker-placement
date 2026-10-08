"""desk.odte — modular 0DTE research, paper simulation and optional execution rail.

Layout (each file is one concern; the doctrine file is the only place a number lives):
  doctrine.py   frozen parameters, templates, envelope name, caps
  calendar.py   event-day blackout (FOMC / CPI / NFP / half-days) from desk/data/odte/event_calendar.json
  templates.py  PURE: strike selection at touch, mark-to-close, manage (stop / time / expiry settle)
  risk.py       PURE: live gates (envelope, caps, VIX1D kill, blackout, halt) — code, not notes
  capture.py    ib_insync chain capture (XSP 0DTE band, SPX, VIX1D) -> desk/data/odte/chains/DATE.jsonl
  shadow.py     per-template paper book fed by capture; fills at the TOUCH, never the mid
  rail.py       live execution: BAG combo via the Gateway, whatIf before the first order, cancel-all
  runner.py     the resident daemon (principal-launched): capture + shadow + (--live) rail
  grader.py     nightly scoreboard vs the T1 climatology benchmark; graduation rule
"""
