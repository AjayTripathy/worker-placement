"""ALPHA/BETA account registry (runbook amendment 2026-08-21b).

Single-account today; the day BETA activates, any order path that does not pin
an explicit account will let ib_insync pick the first managed account it sees.
Every automated order path must call require_alpha() and stamp order.account.
"""
import json
from pathlib import Path

_REG = Path(__file__).parent / "data" / "accounts.json"


def _accounts():
    return json.loads(_REG.read_text())["accounts"]


def alpha_account() -> str:
    aid = _accounts()["ALPHA"]["account_id"]
    if not aid.startswith("U"):
        raise RuntimeError(f"ALPHA account id malformed in accounts.json: {aid!r}")
    return aid


def beta_account():
    aid = _accounts()["BETA"]["account_id"]
    return aid if aid.startswith("U") else None


def require_alpha(ib) -> str:
    """Assert the connected gateway manages ALPHA and return its id.

    Refuses to proceed if ALPHA is absent (wrong login) — and once BETA exists,
    guarantees automated paths never default into it.
    """
    aid = alpha_account()
    managed = ib.managedAccounts()
    if aid not in managed:
        raise RuntimeError(
            f"ALPHA {aid} not in managed accounts {managed} — refusing to place; "
            "check gateway login / accounts.json")
    return aid
