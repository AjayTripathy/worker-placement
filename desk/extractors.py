"""extractors — turn each watch's stdout into unified Signals. One function per watch (keyed by the
registry's `extractor` field) + a generic keyword fallback. Extractors are pure: (stdout) -> [Signal].
Cross-run change detection (e.g. regime flips, new-vs-yesterday virality) is the runner's job.
"""
from __future__ import annotations
import re, json
from pathlib import Path
from . import signals as S

ROOT = Path(__file__).resolve().parents[1]


def smallcap_value(out: str) -> list[dict]:
    sigs = []
    for line in out.splitlines():
        m = re.match(r"\s+([A-Z][A-Z0-9.\-]*)\s+\$([\d.]+)\s+->\s+\[(ENTRY|DEEP-ADD)\]\s+(.*)", line)
        if m:
            tk, px, zone, note = m.groups()
            sev = "HIGH" if zone == "DEEP-ADD" else "MED"
            sigs.append(S.make("smallcap_value", tk, "ENTRY_BAND", f"{zone} @ ${px}: {note}",
                               severity=sev, asset_class="equities",
                               suggested_action=f"accumulate within band ({zone})", entrypoint_ref="value_basket"))
        a = re.search(r">>> ALERTS:\s*(.+)", line)
        if a:
            for piece in a.group(1).split("|"):
                piece = piece.strip()
                if piece:
                    tk = (re.match(r"([A-Z][A-Z0-9.\-]*)", piece) or [None, ""])[1]
                    sigs.append(S.make("smallcap_value", tk or "?", "DELTA_ALERT", piece,
                                       severity="HIGH", asset_class="equities",
                                       suggested_action="check KILL-triggers / band entry", entrypoint_ref="value_basket"))
    return sigs


def krx_value(out: str) -> list[dict]:
    """KRX-direct Korea book: ` TKR  ₩price  [VERDICT] -> ZONE note` lines + a `>>> ALERTS:` line.
    Only ACCUM/WAIT names in their band emit an accumulate ENTRY_BAND (always tagged non-IBKR-executable);
    AVOID/EVENT band touches surface as informational DELTA_ALERTs. Hard moves -> DELTA_ALERT."""
    sigs = []
    for line in out.splitlines():
        m = re.match(r"\s+([A-Z][A-Z0-9]*)\s+₩([\d,]+)\s+\[(ACCUM|WAIT|AVOID|EVENT)\]\s+->\s+"
                     r"(DEEP-ADD|ENTRY|WATCH|ABOVE)\s+(.*)", line)
        if m:
            tk, px, verdict, zone, note = m.groups()
            in_band = zone in ("ENTRY", "DEEP-ADD")
            if verdict in ("ACCUM", "WAIT") and in_band:
                sev = "HIGH" if zone == "DEEP-ADD" else "MED"
                sigs.append(S.make("krx_value", tk, "ENTRY_BAND", f"{zone} @ ₩{px}: {note}",
                                   severity=sev, asset_class="equities",
                                   suggested_action="accumulate on IBKR/KRX (confirm Korea trading permission; size <10-15% ADTV)",
                                   entrypoint_ref="krx_book"))
            elif verdict in ("AVOID", "EVENT") and in_band:
                sigs.append(S.make("krx_value", tk, "DELTA_ALERT",
                                   f"{verdict} name in {zone} band @ ₩{px} (informational, not a buy): {note}",
                                   severity="LOW", asset_class="equities",
                                   suggested_action="context only — AVOID/EVENT-gated, no accumulate",
                                   entrypoint_ref="krx_book"))
        a = re.search(r">>> ALERTS:\s*(.+)", line)
        if a:
            for piece in a.group(1).split("|"):
                piece = piece.strip()
                if piece:
                    tk = (re.match(r"([A-Z][A-Z0-9]*)", piece) or [None, ""])[1]
                    sigs.append(S.make("krx_value", tk or "?", "DELTA_ALERT", piece, severity="HIGH",
                                       asset_class="equities",
                                       suggested_action="check KILL-triggers / band entry (IBKR/KRX)",
                                       entrypoint_ref="krx_book"))
    return sigs


def stvn_book(out: str) -> list[dict]:
    sigs = []
    for line in out.splitlines():
        m = re.match(r"\s+([A-Z][A-Z0-9.\-]*)\s+\S+\s+->\s+\[([^\]]+)\]\s+(.*)", line)
        if not m:
            continue
        tk, zone, note = m.groups()
        z = zone.upper()
        if any(k in z for k in ("ENTRY", "ACCUM", "DEEP")):
            sev = "HIGH" if "DEEP" in z else "MED"
            sigs.append(S.make("stvn_book", tk, "ENTRY_BAND", f"[{zone}] {note}", severity=sev,
                               asset_class="beauty", suggested_action="accumulate within band",
                               entrypoint_ref="beauty_book"))
    return sigs


def deal_cycle(out: str) -> list[dict]:
    m = re.search(r">>> REGIME:\s*([A-Z\-]+)", out)
    if not m:
        return []
    regime = m.group(1)
    sev = "HIGH" if "FROZEN" in regime else "MED"
    return [S.make("deal_cycle", "DFIN", "REGIME_CHANGE", f"deal-cycle regime = {regime}", severity=sev,
                   asset_class="equities", suggested_action="DFIN context (descriptive; no validated trigger)",
                   entrypoint_ref="deal_cycle")]


def beauty_virality(out: str) -> list[dict]:
    """NEW public-ticker brand vs the prior poll (reads beauty_velocity_log.jsonl, the poll's own log)."""
    log = ROOT / "verticals/buyside_dd/outputs/medspa/beauty_velocity_log.jsonl"
    if not log.exists():
        return []
    lines = [l for l in log.read_text().splitlines() if l.strip()]
    if len(lines) < 2:
        return []
    def mapped(entry):
        return {m.get("ticker"): m for m in json.loads(entry).get("mapped", []) if m.get("ticker")}
    today, prior = mapped(lines[-1]), mapped(lines[-2])
    sigs = []
    for tk, m in today.items():
        if tk not in prior:
            sigs.append(S.make("beauty_virality", tk, "NEW_VIRAL",
                               f"NEW viral brand {m.get('tag','')} ({m.get('views','')}) -> {tk} {m.get('name','')}",
                               severity="HIGH", asset_class="beauty",
                               suggested_action="virality leads the print ~1-2Q — check entrypoint",
                               needs_verification=True, entrypoint_ref="virality_radar"))
    return sigs


def generic(out: str) -> list[dict]:
    sigs = []
    for line in out.splitlines():
        if re.search(r"\b(PROMOTE|FIRE[SD]?|DETECTED|FLAG|MATERIAL)\b", line) and len(line.strip()) > 8:
            sigs.append(S.make("generic", "?", "DETECTOR_FIRE", line.strip(), severity="MED",
                               needs_verification=True))
    return sigs


def detector_scan(out: str) -> list[dict]:
    """Parse DETFIRE|<detector>|<ticker>|<SEV>|<evidence> lines from desk.detector_scan."""
    sigs = []
    for line in out.splitlines():
        if not line.startswith("DETFIRE|"):
            continue
        parts = line.split("|", 4)
        if len(parts) != 5:
            continue
        _, det, tk, sev, ev = parts
        sigs.append(S.make(f"detector:{det}", tk, "DETECTOR_FIRE", ev, severity=sev.strip().upper(),
                           needs_verification=True, suggested_action="auto-verify via SignalOS (read-only)",
                           entrypoint_ref=det))
    return sigs


EXTRACTORS = {"smallcap_value": smallcap_value, "krx_value": krx_value, "stvn_book": stvn_book,
              "deal_cycle": deal_cycle, "beauty_virality": beauty_virality,
              "detector_scan": detector_scan, "generic": generic}


def extract(extractor_key: str, out: str) -> list[dict]:
    return EXTRACTORS.get(extractor_key, generic)(out)
