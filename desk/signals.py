"""signals — the unified actionable-signal schema every watch normalizes to, plus severity + dedupe.

A Signal is the atom the Desk routes. The whole point is INFORMATION ARBITRAGE: a detector fired (or a
name touched an entrypoint) and it may not be priced yet. The Desk's job is to catch that and route it.

signal_type:
  ENTRY_BAND     a tracked name entered/sits in its accumulate/deep-add band  (entrypoint hit)
  DELTA_ALERT    a tracked name moved hard / changed zone vs the prior run
  DETECTOR_FIRE  a KG detector fired on an asset (the core info-arb event)
  REGIME_CHANGE  a regime gauge flipped (deal-cycle, liquidity, etc.)
  NEW_VIRAL      a new public-ticker brand surfaced in the virality poll
severity: HIGH (push now + candidate to auto-verify) / MED (digest) / LOW (log only)
"""
from __future__ import annotations
import hashlib, time

VALID_TYPES = {"ENTRY_BAND", "DELTA_ALERT", "DETECTOR_FIRE", "REGIME_CHANGE", "NEW_VIRAL"}


def make(source: str, asset: str, signal_type: str, evidence: str,
         severity: str = "MED", suggested_action: str = "", needs_verification: bool = False,
         entrypoint_ref: str = "", asset_class: str = "") -> dict:
    assert signal_type in VALID_TYPES, signal_type
    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": source, "asset": asset, "asset_class": asset_class,
        "signal_type": signal_type, "severity": severity.upper(),
        "evidence": evidence.strip()[:600], "suggested_action": suggested_action,
        "needs_verification": needs_verification, "entrypoint_ref": entrypoint_ref,
    }


def dedupe_key(sig: dict) -> str:
    """Same source+asset+type+evidence on the same day = one signal (don't re-alert a standing zone)."""
    day = sig["ts"][:10]
    raw = f"{day}|{sig['source']}|{sig['asset']}|{sig['signal_type']}|{sig['evidence'][:120]}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def is_push(sig: dict) -> bool:
    return sig["severity"] == "HIGH"


def is_actionable(sig: dict) -> bool:
    return sig["severity"] in ("HIGH", "MED")
