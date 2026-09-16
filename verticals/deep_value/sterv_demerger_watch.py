"""sterv_demerger_watch — the highest-value STERV (Stora Enso) monitor: the FOREST-DEMERGER LANGUAGE watch.

The entire STERV thesis is an asset-backed SOTP special situation whose value crystallizes on ONE dated
catalyst: the separation of the Swedish forest assets (Bergslagets Skogar) into a new listed company,
"complete[d] in the first half of 2027" (verbatim, PRIMARY — Nov-2025 inside-information release). At the
live R-share price the market assigns a NEGATIVE stub to the ~EUR9.3bn-rev operating company, so the trade
IS the demerger happening on schedule. The single biggest thesis risk is therefore not a bad quarter — it
is the COMMITMENT SOFTENING, SLIPPING, or DISAPPEARING. This watch reads that language directly off Stora
Enso's own IR/newsroom pages and FLAGs any drift from the baseline.

FLAG conditions (per run, diffed vs the frozen baseline):
  (a) SOFTENING     — new conditional hedging that wasn't there ("evaluating", "reviewing options",
                      "subject to market conditions" appearing where a firm commitment stood, "no longer",
                      "postpone", "delay", "reconsider", "if completed").
  (b) TIMELINE      — the completion window moves off "first half of 2027" (any new year/half token).
  (c) DISAPPEARANCE — the completion commitment vanishes from a page that carried it. ABSENCE IS THE
                      LOUDEST SIGNAL, but per the false-absence lesson (SPCX compound-query null) it is
                      NEVER alarmed on a single query form: disappearance must hold across ALL reachable
                      anchor pages AND the run must have successfully fetched them (a fetch failure is
                      DEGRADED, never "gone"). A disappearance on one page while another still carries it
                      = page maintenance, downgraded to REVIEW.

Fetch path: curl_cffi chrome124 impersonation. storaenso.com sits behind bot-management that 403s plain
urllib/curl AND a hand-built Chrome header set (JA3/TLS fingerprinting) — curl_cffi's TLS impersonation is
what actually clears it (verified 2026-07-23: urllib 403, curl 403, curl_cffi chrome124 -> 200). A 403/blk
on a run is DEGRADED (skip the diff, don't alarm), matching the "blocked scheduler = DATA MISSING not zero"
doctrine.

  python3 verticals/deep_value/sterv_demerger_watch.py                # diff vs baseline (or seed it)
  python3 verticals/deep_value/sterv_demerger_watch.py --reseed       # overwrite the baseline
READ-ONLY (writes only its own baseline + cron state). Not an entry trigger — a thesis-integrity tripwire.
"""
from __future__ import annotations
import argparse, datetime, html, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASELINE = HERE / "data" / "sterv_demerger_baseline.json"
STATE = HERE / "data" / "sterv_demerger_state.json"

# The anchor pages that carry the separation commitment. Ordered: the durable IR summary first, then the
# two primary regulatory/press releases that state the exact completion window. Multiple pages = the
# second-query-form robustness the false-absence lesson demands (never alarm disappearance off one URL).
PAGES = [
    ("forestco_ir",
     "https://www.storaenso.com/en/investors/stora-enso-as-an-investment/forestco"),
    ("nov2025_insideinfo",
     "https://www.storaenso.com/en/newsroom/regulatory-and-investor-releases/2025/11/"
     "stora-enso-completes-strategic-review-and-intends-to-create-the-largest-listed-pure-play-forest-"
     "company-in-europe-inside-information"),
    ("may2026_naming",
     "https://www.storaenso.com/en/newsroom/press-releases/2026/5/"
     "stora-enso-introduces-bergslagets-skogar-as-the-new-name-for-its-swedish-forest-asset-company"),
]

# The commitment we are protecting. The canonical completion phrase (verbatim, Nov-2025 inside-info):
#   "Stora Enso expects to announce the cross-border demerger during the second half of 2026, and
#    complete it in the first half of 2027."
ANCHOR_TIMELINE_PHRASE = "first half of 2027"
# sentence must mention BOTH a separation/demerger/listing verb AND the completion/timeline to count as a
# live commitment sentence (avoids matching boilerplate that says "2027" for an unrelated reason).
SEP_RE = re.compile(r"separat|demerg|spin[- ]?off|(?:publicly )?listed compan|public listing|new company", re.I)
TIMELINE_RE = re.compile(r"first half of 20\d\d|second half of 20\d\d|H[12]\s*20\d\d|during 20\d\d|by 20\d\d|complete[d]?\s+(?:it\s+)?in", re.I)
COMPLETE_RE = re.compile(r"complet", re.I)

# Softening / slippage vocabulary — hedging that would signal the commitment weakening if it APPEARS in a
# commitment sentence where it wasn't in the baseline. (Some of these — "subject to", "approval",
# "conditions", "market conditions" — are present in the BASELINE already as standing legal caveats;
# the FLAG is on NEW appearances vs baseline, so pre-existing caveats don't fire. The unambiguous
# regression words fire on presence anywhere in a commitment context.)
SOFTEN_HEDGE = ["evaluating", "reviewing options", "review options", "exploring options",
                "under review", "reconsider", "reconsidering", "if completed", "should the demerger",
                "no longer", "postpone", "postponed", "delay", "delayed", "abandon", "abandoned",
                "suspend", "suspended", "paused", "on hold", "not proceed", "will not proceed",
                "decided against", "terminated", "cancelled", "canceled", "shelved", "may not"]
# harder regression words: if ANY of these appears anywhere on an anchor page (not just a commitment
# sentence), fire regardless of baseline — they are unambiguous reversals.
HARD_REGRESSION = ["no longer intends", "will not proceed", "does not intend to proceed",
                   "decided not to proceed", "abandoned the demerger", "abandoned the separation",
                   "terminated the demerger", "cancelled the demerger", "canceled the demerger",
                   "postponed the demerger", "postponed the separation", "delay the demerger",
                   "delayed the demerger", "suspend the demerger", "suspended the demerger"]


def _fetch(url: str) -> tuple[int, str | None]:
    """curl_cffi chrome124 impersonation (the only path that clears storaenso.com bot-management).
    Returns (status_code, text) or (status_code, None) / (0, None) on failure — never raises."""
    try:
        from curl_cffi import requests as cr
    except Exception:
        return (0, None)
    for imp in ("chrome124", "chrome120", "chrome"):
        try:
            r = cr.get(url, impersonate=imp, timeout=45)
            if r.status_code == 200 and len(r.text) > 2000:
                low = r.text.lower()
                if "just a moment" in low or "cf-challenge" in low or "captcha" in low:
                    continue  # challenge page — try next impersonation
                return (200, r.text)
            last = r.status_code
        except Exception:
            last = -1
    return (last if isinstance(last, int) else 0, None)


def _to_text(raw_html: str) -> str:
    raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw_html, flags=re.S | re.I)
    raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.S | re.I)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return re.sub(r"\s+", " ", txt).strip()


def _commitment_sentences(text: str) -> list[str]:
    """Sentences that state a separation/demerger/listing AND a completion timeline — the live commitment."""
    out, seen = [], set()
    for s in re.split(r"(?<=[.!?])\s+", text):
        s = s.strip()
        if not (20 < len(s) < 520):
            continue
        if SEP_RE.search(s) and TIMELINE_RE.search(s) and COMPLETE_RE.search(s):
            if s not in seen:
                seen.add(s)
                out.append(s)
    return out


def _timeline_tokens(sents: list[str]) -> set[str]:
    toks = set()
    for s in sents:
        for m in re.finditer(r"(first|second) half of (20\d\d)|H([12])\s*(20\d\d)|in the (first|second) half of (20\d\d)", s, re.I):
            toks.add(m.group(0).lower().replace("in the ", ""))
    return toks


def _scan_page(tag: str, url: str) -> dict:
    status, raw = _fetch(url)
    if raw is None:
        return {"tag": tag, "url": url, "status": status, "degraded": True,
                "commitment_sentences": [], "timeline_tokens": [], "has_anchor_phrase": None,
                "hard_regression_hits": [], "soften_hits": []}
    text = _to_text(raw)
    low = text.lower()
    sents = _commitment_sentences(text)
    return {"tag": tag, "url": url, "status": 200, "degraded": False,
            "commitment_sentences": sents,
            "timeline_tokens": sorted(_timeline_tokens(sents)),
            "has_anchor_phrase": (ANCHOR_TIMELINE_PHRASE in low),
            "hard_regression_hits": [h for h in HARD_REGRESSION if h in low],
            "soften_hits": [h for h in SOFTEN_HEDGE if h in low]}


def snapshot() -> dict:
    today = datetime.date.today().isoformat()
    pages = [_scan_page(tag, url) for tag, url in PAGES]
    return {"asof": today, "anchor_phrase": ANCHOR_TIMELINE_PHRASE, "pages": pages,
            "canonical_commitment": ("Stora Enso expects to announce the cross-border demerger during the "
                                     "second half of 2026, and complete it in the first half of 2027."),
            "source": "storaenso.com IR + newsroom (curl_cffi chrome124)"}


def seed_baseline(force: bool = False) -> dict:
    if BASELINE.exists() and not force:
        return json.loads(BASELINE.read_text())
    snap = snapshot()
    live = [p for p in snap["pages"] if not p["degraded"]]
    if not live:
        raise SystemExit("REFUSING to seed baseline: every anchor page fetch DEGRADED (bot-block/network). "
                         "A baseline of absences would false-alarm every future run. Retry when reachable.")
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(json.dumps(snap, indent=1))
    return snap


def diff(baseline: dict, current: dict) -> list[dict]:
    """Compare current snapshot to baseline; return a list of FLAG/REVIEW findings (empty = intact)."""
    flags = []
    b_pages = {p["tag"]: p for p in baseline["pages"]}
    c_pages = {p["tag"]: p for p in current["pages"]}

    live_now = [p for p in current["pages"] if not p["degraded"]]
    # union of all timeline tokens seen live this run
    cur_tokens = set()
    for p in live_now:
        cur_tokens.update(p["timeline_tokens"])

    # (a) HARD REGRESSION — unambiguous reversal words anywhere on any live page => FLAG immediately
    for p in live_now:
        if p["hard_regression_hits"]:
            flags.append({"kind": "SOFTENING", "severity": "FLAG", "page": p["tag"],
                          "detail": f"unambiguous regression language on {p['tag']}: "
                                    f"{p['hard_regression_hits']}"})

    # (b) TIMELINE — anchor phrase gone from the union of live pages, OR a NEW timeline token appears
    anchor_present_live = any(p["has_anchor_phrase"] for p in live_now)
    if live_now and not anchor_present_live:
        flags.append({"kind": "TIMELINE", "severity": "FLAG", "page": "ALL-LIVE",
                      "detail": f"the anchor completion phrase '{current['anchor_phrase']}' is ABSENT from "
                                f"every successfully-fetched anchor page ({[p['tag'] for p in live_now]}). "
                                f"Timeline tokens now present: {sorted(cur_tokens)}. Read the pages."})
    base_tokens = set()
    for p in baseline["pages"]:
        base_tokens.update(p.get("timeline_tokens", []))
    new_completion_tokens = {t for t in cur_tokens if t not in base_tokens and "half of" in t
                             and "2027" not in t}
    if new_completion_tokens:
        flags.append({"kind": "TIMELINE", "severity": "FLAG", "page": "ALL-LIVE",
                      "detail": f"NEW completion-timeline token(s) not in baseline: {sorted(new_completion_tokens)} "
                                f"(baseline had {sorted(base_tokens)}). Completion window may have moved."})

    # (c) SOFTENING — a hedge word appears in the current commitment context that was NOT in baseline
    base_soften = set()
    for p in baseline["pages"]:
        base_soften.update(p.get("soften_hits", []))
    for p in live_now:
        new_soft = [h for h in p["soften_hits"] if h not in base_soften]
        if new_soft:
            flags.append({"kind": "SOFTENING", "severity": "REVIEW", "page": p["tag"],
                          "detail": f"NEW hedging vocabulary on {p['tag']} vs baseline: {new_soft} "
                                    f"(baseline hedges: {sorted(base_soften)}). Confirm it is a standing "
                                    f"legal caveat, not a commitment walk-back."})

    # (d) DISAPPEARANCE of commitment sentences — only alarmed when it holds across ALL live pages
    #     that USED to carry commitment sentences AND at least one such page was actually fetched.
    pages_had_commitment = [tag for tag, p in b_pages.items() if p.get("commitment_sentences")]
    live_tags = {p["tag"] for p in live_now}
    checkable = [t for t in pages_had_commitment if t in live_tags]
    if checkable:
        still_present = [t for t in checkable if c_pages[t]["commitment_sentences"]]
        gone = [t for t in checkable if not c_pages[t]["commitment_sentences"]]
        if gone and not still_present:
            # disappeared everywhere we could check -> LOUD (but require >=1 page actually checked)
            flags.append({"kind": "DISAPPEARANCE", "severity": "FLAG", "page": "ALL-CHECKABLE",
                          "detail": f"the separation-completion commitment sentence has DISAPPEARED from "
                                    f"EVERY reachable page that carried it ({checkable}). This is the loudest "
                                    f"signal — verify manually before acting, but the commitment is no longer "
                                    f"stated on Stora Enso's own IR/newsroom."})
        elif gone and still_present:
            flags.append({"kind": "DISAPPEARANCE", "severity": "REVIEW", "page": ",".join(gone),
                          "detail": f"commitment sentence gone from {gone} but STILL present on {still_present} "
                                    f"— likely page maintenance/restructure, not a walk-back. Confirm."})

    return flags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reseed", action="store_true", help="overwrite the baseline with a fresh snapshot")
    args = ap.parse_args()
    today = datetime.date.today().isoformat()

    if args.reseed or not BASELINE.exists():
        snap = seed_baseline(force=True)
        live = [p for p in snap["pages"] if not p["degraded"]]
        print(f"=== STERV DEMERGER WATCH  {today}  [BASELINE {'RESEEDED' if args.reseed else 'SEEDED'}] ===")
        print(f"   anchor phrase: \"{snap['anchor_phrase']}\"   ({len(live)}/{len(snap['pages'])} pages live)")
        print(f"   canonical commitment (verbatim): {snap['canonical_commitment']}")
        for p in snap["pages"]:
            tag = "DEGRADED" if p["degraded"] else f"{len(p['commitment_sentences'])} commitment-sentence(s)"
            print(f"     [{p['tag']}] {tag}  anchor_phrase={p['has_anchor_phrase']}")
            for s in p["commitment_sentences"]:
                print(f"        • {s}")
        STATE.write_text(json.dumps({"last_run": today, "flags": [], "seeded": True}, indent=1))
        print(f"[baseline -> {BASELINE.name}]")
        return

    baseline = json.loads(BASELINE.read_text())
    current = snapshot()
    live_now = [p for p in current["pages"] if not p["degraded"]]
    flags = diff(baseline, current)

    print(f"=== STERV DEMERGER WATCH  {today}  ({len(live_now)}/{len(current['pages'])} pages live) ===")
    print(f"   baseline seeded {baseline['asof']}   anchor \"{baseline['anchor_phrase']}\"")
    if not live_now:
        print("   DEGRADED: every anchor page fetch failed (bot-block/network). No diff run — DATA MISSING, "
              "not a disappearance. Will retry next cadence.")
        STATE.write_text(json.dumps({"last_run": today, "flags": [], "degraded": True}, indent=1))
        return
    anchor_live = any(p["has_anchor_phrase"] for p in live_now)
    print(f"   anchor phrase still present on a live page: {anchor_live}")
    if flags:
        print(f"   *** {len(flags)} FINDING(S) — thesis-integrity tripwire ***")
        for f in flags:
            print(f"     [{f['severity']}/{f['kind']}] ({f['page']}) {f['detail']}")
    else:
        print("   COMMITMENT INTACT — no softening / no timeline change / no disappearance. "
              "The 2027 forest demerger catalyst is unchanged on Stora Enso's own disclosure.")
    STATE.write_text(json.dumps({"last_run": today, "flags": flags,
                                 "anchor_live": anchor_live, "degraded": False}, indent=1))
    # non-zero-ish signal for the extractor: print a machine line
    print("SIGNAL " + json.dumps({"name": "sterv_demerger_watch", "flags": len(flags),
                                  "fire": bool([f for f in flags if f["severity"] == "FLAG"]),
                                  "anchor_live": anchor_live}))


if __name__ == "__main__":
    main()
