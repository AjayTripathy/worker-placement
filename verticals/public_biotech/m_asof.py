"""As-of-cutoff M reconstruction from ClinicalTrials.gov.

The whole backtest hinges on M being reconstructed as the market could have seen
it at `cutoff` — never after. CT.gov's internal history API exposes every posted
version of a trial's protocol with its posting date, so we can rebuild the
registration EXACTLY as it stood on the cutoff and never leak the post-readout
results update.

  /api/int/studies/{nct}/history            -> list of versions {version, date, moduleLabels}
  /api/int/studies/{nct}/history/{version}  -> full protocolSection snapshot at that version

`fetch_trial_asof(nct, cutoff)` returns the latest pre-cutoff snapshot plus
history-derived signals (did the registered primary endpoint change? did the
primary-completion date drift?) — the M evidence the biotech f-rules adjudicate
marketing claims against.

Leakage guard: we keep ONLY versions whose posting date <= cutoff. The version
that carries topline results is always posted AFTER the catalyst, so it is
mechanically excluded.
"""
from __future__ import annotations

import re
import sys

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}
_BASE = "https://clinicaltrials.gov/api/int/studies"


def _get_json(url: str) -> dict | None:
    try:
        with httpx.Client(timeout=30, headers=HEADERS) as c:
            r = c.get(url)
            if r.status_code != 200:
                return None
            return r.json()
    except Exception as e:
        print(f"CT.gov fetch error {url}: {e}", file=sys.stderr)
        return None


def _primary_measures(record: dict) -> list[str]:
    ps = record.get("study", record).get("protocolSection", {})
    om = ps.get("outcomesModule", {})
    return [o.get("measure", "").strip() for o in (om.get("primaryOutcomes") or [])]


# Construct-grade canonicalization of a primary-endpoint MEASURE string. Used
# ONLY for change-detection so that a pure REWORDING of the same endpoint
# ("Change from baseline in ADAS-Cog11" -> "ADAS-Cog11 change") does not register
# as a primary-endpoint change. A real construct/type swap (a different scale or
# measured quantity) survives canonicalization and still trips primary_changed.
# Deliberately does NOT touch timeFrame — a Week-5-vs-Week-6 difference is not a
# construct change and must never set primary_changed.
_MEASURE_STOPWORDS = re.compile(
    r"\b(change|baseline|from|in|of|the|score|scale|mean|least|squares?|"
    r"adjusted|total|at|week|day|month|to|placebo|versus|vs|compared|"
    r"proportion|percentage|percent|number|subjects?|patients?|with|response|"
    r"responders?|"
    # duration/time-unit nouns: a threshold like "(21.5 hours)" embedded in a
    # measure is a timeFrame-style detail, not a construct change.
    r"hours?|hrs?|minutes?|mins?|seconds?|secs?|years?|weeks?|days?|months?)\b",
    re.I)


def _canon_measure(measure: str) -> str:
    m = (measure or "").lower()
    m = re.sub(r"[\d]+", " ", m)            # drop counts/timepoints embedded in text
    m = re.sub(r"[^a-z\s-]", " ", m)        # keep letters and hyphens (scale names)
    m = _MEASURE_STOPWORDS.sub(" ", m)
    return " ".join(sorted(t for t in m.split() if len(t) > 1))


def _canon_primaries(snapshot: dict) -> tuple[str, ...]:
    return tuple(sorted(_canon_measure(p["measure"]) for p in snapshot["primary_outcomes"]))


# Token-overlap (Jaccard) thresholds for classifying how one primary construct
# relates to the constructs in an adjacent registry version:
#   >= _ANCHOR_SIM  -> essentially the SAME endpoint held fixed (an anchor)
#   <  _DROP_SIM    -> no counterpart -> genuinely DROPPED (a real substitution)
#   in between      -> the same endpoint, reworded (neither anchor nor drop)
_ANCHOR_SIM = 0.85
_DROP_SIM = 0.40


def _tokens(canon_str: str) -> frozenset:
    return frozenset(t for t in canon_str.split() if t)


def _best_sim(a: frozenset, others: list[frozenset]) -> float:
    best = 0.0
    for b in others:
        u = a | b
        if not u:
            continue
        j = len(a & b) / len(u)
        best = max(best, j)
    return best


def _anchored_swap(seq: list[list[frozenset]]) -> bool:
    """A genuine success-slot construct change holds PART of the primary structure
    fixed (an anchor co-primary that stays near-identical across a version) while
    DROPPING/substituting another co-primary — e.g. CRTX GAIN kept ADAS-Cog fixed
    while swapping CDR-SB -> ADCS-ADL. A wholesale registry-template reword (every
    primary's text changes at once, like MDGL's 2022 reformat) leaves no anchor; a
    minor reword of one co-primary is matched by similarity, so it is NOT a drop.
    True iff some consecutive transition has both an anchored construct and a
    genuinely dropped one."""
    for i in range(len(seq) - 1):
        A, B = seq[i], seq[i + 1]
        has_anchor = any(_best_sim(a, B) >= _ANCHOR_SIM for a in A)
        has_drop = any(_best_sim(a, B) < _DROP_SIM for a in A)
        if has_anchor and has_drop:
            return True
    return False


def _is_controlled_pivotal(snapshot: dict) -> bool:
    """True when the trial's OWN design is a randomized, controlled comparison —
    i.e. the catalyst readout is NOT a single-arm / open-label result. Gates the
    open_label_extrapolation channel: citing open-label supporting data is only
    'masking' when the CATALYST itself lacks a controlled comparison. A randomized
    parallel/crossover trial qualifies even if open-label (randomization, not
    blinding, is what defends against regression-to-the-mean on the readout)."""
    alloc = (snapshot.get("allocation") or "").upper()
    model = (snapshot.get("intervention_model") or "").upper()
    return alloc == "RANDOMIZED" and model != "SINGLE_GROUP"


def _snapshot(record: dict) -> dict:
    """Flatten one version's protocolSection into the fields the f-rules need."""
    ps = record.get("study", record).get("protocolSection", {})
    om = ps.get("outcomesModule", {})
    dm = ps.get("designModule", {})
    sm = ps.get("statusModule", {})
    design = dm.get("designInfo", {})
    masking = (design.get("maskingInfo") or {})
    # Trial-IDENTITY fields (condition / intervention / sponsor) — additive; the
    # f-rule M slices cherry-pick keys, so these do not alter evaluate's prompts.
    # They feed the deterministic pre-flight binding check (verify_binding).
    cond = ps.get("conditionsModule", {})
    interventions = (ps.get("armsInterventionsModule", {}) or {}).get("interventions") or []
    lead = (ps.get("sponsorCollaboratorsModule", {}) or {}).get("leadSponsor") or {}
    return {
        "primary_outcomes": [
            {"measure": o.get("measure"), "timeFrame": o.get("timeFrame")}
            for o in (om.get("primaryOutcomes") or [])
        ],
        "secondary_outcomes": [o.get("measure") for o in (om.get("secondaryOutcomes") or [])],
        "phases": dm.get("phases") or [],
        "enrollment": (dm.get("enrollmentInfo") or {}).get("count"),
        "enrollment_type": (dm.get("enrollmentInfo") or {}).get("type"),
        "allocation": design.get("allocation"),
        "intervention_model": design.get("interventionModel"),
        "primary_purpose": design.get("primaryPurpose"),
        "masking": masking.get("masking"),
        "overall_status": sm.get("overallStatus"),
        "primary_completion_date": (sm.get("primaryCompletionDateStruct") or {}).get("date"),
        "primary_completion_type": (sm.get("primaryCompletionDateStruct") or {}).get("type"),
        "conditions": cond.get("conditions") or [],
        "interventions": [i.get("name") for i in interventions if i.get("name")],
        "lead_sponsor": lead.get("name"),
    }


def fetch_trial_asof(nct: str, cutoff: str, *, verbose: bool = False) -> dict:
    """Reconstruct trial registration M as of `cutoff` (ISO date, inclusive).

    Returns a dict with the as-of snapshot and history-derived change signals,
    or {error: ...} if no pre-cutoff version exists.
    """
    hist = _get_json(f"{_BASE}/{nct}/history")
    if not hist:
        return {"nct": nct, "error": "history_unavailable"}
    changes = hist.get("changes", [])
    pre = [v for v in changes if v.get("date", "") <= cutoff]
    if not pre:
        return {"nct": nct, "cutoff": cutoff, "error": "no_pre_cutoff_version"}

    latest = pre[-1]
    latest_rec = _get_json(f"{_BASE}/{nct}/history/{latest['version']}")
    if not latest_rec:
        return {"nct": nct, "cutoff": cutoff, "error": "version_record_unavailable"}
    snap = _snapshot(latest_rec)

    # History signals: walk every pre-cutoff version, track primary-endpoint text,
    # primary-completion-date, and enrollment so the adjudicator can compare a
    # claim against the registered value AS OF THE CLAIM'S FILING DATE (trials
    # legitimately expand enrollment / shift dates over time — a value that was
    # correct when filed must not be refuted against a later snapshot).
    primary_timeline: list[dict] = []
    completion_timeline: list[dict] = []
    enrollment_timeline: list[dict] = []
    primary_canon_sets: list[frozenset] = []   # deduped sequence of canon-construct sets
    primary_token_seq: list[list[frozenset]] = []  # per-version list of per-primary token sets
    last_completion: str | None = None
    last_enroll: object = object()
    for v in pre:
        rec = _get_json(f"{_BASE}/{nct}/history/{v['version']}")
        if not rec:
            continue
        s = _snapshot(rec)
        pm = [p["measure"] for p in s["primary_outcomes"]]
        # Compare CONSTRUCT (canonical measure SET), not raw text — a rewording of
        # the same endpoint must not count as a change; a real scale/measure swap
        # does. Track the per-version set so we can later distinguish a genuine
        # construct swap from a wholesale registry-template reword (see below).
        cset = frozenset(_canon_measure(p["measure"]) for p in s["primary_outcomes"])
        if not primary_canon_sets or cset != primary_canon_sets[-1]:
            primary_canon_sets.append(cset)
            primary_token_seq.append([_tokens(_canon_measure(p["measure"]))
                                      for p in s["primary_outcomes"]])
            primary_timeline.append({"version": v["version"], "date": v["date"], "primary": pm,
                                     "timeFrames": [p["timeFrame"] for p in s["primary_outcomes"]]})
        cd = s["primary_completion_date"]
        if cd != last_completion:
            completion_timeline.append({"version": v["version"], "date": v["date"],
                                        "primary_completion_date": cd})
            last_completion = cd
        en = s["enrollment"]
        if en != last_enroll:
            enrollment_timeline.append({"version": v["version"], "date": v["date"],
                                        "enrollment": en, "type": s["enrollment_type"]})
            last_enroll = en

    primary_changed = len(primary_canon_sets) > 1
    # ANCHORED-SWAP signal: a genuine success-slot construct change is one where the
    # trial holds PART of its primary structure fixed (an anchor co-primary that
    # stays canon-identical) while DROPPING/substituting another co-primary — e.g.
    # CRTX GAIN kept ADAS-Cog fixed while swapping CDR-SB→ADCS-ADL. A wholesale
    # registry-template reword (every primary's text changes at once, like MDGL's
    # 2022 reformat that touched both the Week-52 biopsy AND the Month-54 composite
    # co-primary) leaves NO anchor and is NOT a manipulation — it must not trip the
    # gate. Similarity-aware: an anchor is a co-primary that stays >= _ANCHOR_SIM
    # across the transition; a drop is one with no counterpart >= _DROP_SIM. A minor
    # reword (in-between Jaccard) is neither, so it does NOT trip the gate.
    catalyst_primary_construct_changed = _anchored_swap(primary_token_seq)
    completion_slipped = len(completion_timeline) > 1
    if verbose:
        print(f"[{nct}] {len(pre)}/{len(changes)} versions pre-cutoff; "
              f"primary_changed={primary_changed} "
              f"construct_swapped={catalyst_primary_construct_changed} "
              f"completion_slipped={completion_slipped}",
              file=sys.stderr)

    return {
        "nct": nct,
        "cutoff": cutoff,
        "asof_version": latest["version"],
        "asof_version_date": latest["date"],
        "n_versions_pre_cutoff": len(pre),
        "n_versions_total": len(changes),
        "snapshot": snap,
        "primary_endpoint_changed": primary_changed,
        "catalyst_primary_construct_changed": catalyst_primary_construct_changed,
        "controlled_pivotal": _is_controlled_pivotal(snap),
        "primary_endpoint_timeline": primary_timeline,
        "primary_completion_slipped": completion_slipped,
        "primary_completion_timeline": completion_timeline,
        "enrollment_timeline": enrollment_timeline,
        "source_url": f"https://clinicaltrials.gov/study/{nct}?tab=history",
    }


if __name__ == "__main__":
    import json
    nct = sys.argv[1] if len(sys.argv) > 1 else "NCT03900429"
    cutoff = sys.argv[2] if len(sys.argv) > 2 else "2022-12-18"
    print(json.dumps(fetch_trial_asof(nct, cutoff, verbose=True), indent=2))
