"""Insider share-pledge detector — the brain-side entry point for the pledge family.

WHAT IT DOES
------------
Classifies an issuer's pledge disclosure (DEF 14A beneficial-ownership footnote,
or the S-1/424B4 at IPO time before a proxy exists) into AFFIRMATIVE_PLEDGE vs
ANTI_PLEDGE_POLICY vs NO_MENTION using the narrow collateral-framing classifier
in `pledge_prevalence_sample.classify` (the one calibrated to ~4% base rate; a
naive "pledge" grep overstates ~20x because the modal mention is an anti-pledge
POLICY). On an AFFIRMATIVE hit it:

  1. FIRES and emits the R/f(M) finding,
  2. SETS the issuer feature `insider_share_pledge` (`SETS_FEATURE`), which is the
     hard gate on the `m_sources.ucc_financing_statement` M-source — so detecting
     a real pledge is what activates the debtor-keyed UCC lookup downstream, and
  3. when a ticker + a pledge time-series are available, attaches the bounded
     margin-call band from `pledge_margin_call.triangulate_with_filings` (which in
     turn mines `pledge_filings` for the Form-4 / 13D timeline and applies the IPO
     lock-up legal floor to shrink the inception window).

This is deliberately a HONESTY-NEUTRAL detector: a disclosed insider pledge is not
a lie, so it carries NO manufactured severity. It fires to ACTIVATE the rest of
the family and surface an UNVERIFIABLE_BOUNDED band — never a pass/fail verdict.

WHY THE FEATURE IS SET HERE AND NOT IN THE KEYWORD NET
------------------------------------------------------
`dispatch_prompt_template.infer_features_from_text` is fast-and-lossy. A bare
"pledge" keyword there would set `insider_share_pledge` on the ~82% of names that
merely PROHIBIT pledging — exactly the false-positive trap the prevalence study
quantified. So determinism lives in THIS classify-based detector, not the keyword
net. The detector is `applies_universally` (cheap, self-gating: returns NO_TEXT
when neither a proxy nor an S-1 is available), so the brain always considers it
and the precise classifier is the real filter.

FUTURE DETECTORS / TECH DEBT
----------------------------
- code-S forced-sale monitor (SIBLING DETECTOR, not built): watch the insider's
  Form 4s for code-S open-market sales clustered near/below the margin-call band —
  that is the actual TRIGGER confirmation the band only bounds. Absence of code-S
  while price sits below the band is itself the signal (conservatively levered or
  actively maintained). High value, fully free (Form 4 XML), should be next.
- UCC-3 top-up cadence detector (needs paid UCC access): once a DE UCC-11 order is
  bought for a material name, the UCC-3 amendment cadence + secured-party identity
  pin the lender and each top-up date to the day — collapses the price window from
  a band to a point. Gated behind on-demand procurement, not a subscription.
- pledge_velocity: pledged-share growth vs concurrent price drawdown — a founder
  topping up collateral INTO a falling price is a distress tell distinct from a
  static legacy pledge.
- The Form-4 footnote / 13D mining in `pledge_filings` is real but ISSUER-
  DEPENDENT (empty for CAI: Caris insiders never restate the pledge there). The
  generalizable window-shrinker when self-disclosure is absent is the IPO lock-up
  legal floor, already wired via `earliest_pledge_date`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from ..edgar import fetch_filing_clean, list_filings
from ..pledge_prevalence_sample import _strip, classify

SETS_FEATURE = "insider_share_pledge"

APPLIES_TO = {
    "asset_classes": [
        "corporate_ipo_dd", "public_co_defense", "public_co_space",
        "public_co_quantum", "public_co_nuclear", "diagnostics_biotech_dd",
    ],
    # The feature this detector SETS (activating ucc_financing_statement +
    # pledge_margin_call), not a gate it requires.
    "issuer_features": [SETS_FEATURE],
    "sets_feature": SETS_FEATURE,
    "applies_universally": True,   # cheap + self-gating; classify is the real filter
    "kind": "detector",
    "summary": ("Detect a genuine insider STOCK PLEDGE (shares pledged as loan "
                "collateral) vs the far-more-common anti-pledge policy; on a true "
                "pledge, set insider_share_pledge (activating the UCC lookup) and "
                "attach a bounded margin-call band."),
    "verification_question": ("Does the issuer disclose an insider who has pledged "
                              "company stock as collateral for personal debt (R, "
                              "DEF 14A / S-1 Item 403), and if so what is the bounded "
                              "margin-call band and is there Form-4 code-S forced "
                              "selling near it (M)?"),
}


def _latest_disclosure_text(
    cik: str,
    data_dir: Optional[str] = None,
    cutoff: Optional[str] = None,
) -> Optional[str]:
    """Most recent pledge-bearing disclosure AS OF the cutoff: latest DEF 14A,
    else the S-1/424B4 (IPO-time, before a proxy exists).

    Point-in-time seam: when `data_dir` is given, the cutoff-filtered corpus index
    (`<data_dir>/filings_index.json` written by `edgar.pull`) is the source of
    truth, and the on-disk `<data_dir>/filings/<accession>_<form>.txt` is read
    first. When only `cutoff` is given, the live filing list is filtered to
    `filing_date <= cutoff`. With neither, behaves live (latest = today)."""
    pref = ("DEF 14A", "424B4", "S-1/A", "S-1")
    ddir = Path(data_dir) if data_dir else None

    rows: list[dict] = []
    if ddir and (ddir / "filings_index.json").exists():
        rows = json.loads((ddir / "filings_index.json").read_text())
    else:
        try:
            _, rows = list_filings(cik)
        except Exception:
            return None
    if cutoff:
        rows = [r for r in rows if r["filing_date"] <= cutoff]

    for form in pref:
        cand = [r for r in rows if r["form"] == form]
        if not cand:
            continue
        cand.sort(key=lambda r: r["filing_date"], reverse=True)
        r = cand[0]
        if ddir:  # prefer the pre-downloaded point-in-time corpus file
            fsafe = form.replace("/", "_").replace(" ", "_")
            local = ddir / "filings" / f"{r['accession']}_{fsafe}.txt"
            if local.exists():
                return local.read_text()
        txt = fetch_filing_clean(cik, r["accession"], r["primary_document"])
        if txt:
            return txt
    return None


def evaluate(issuer_name: str, data: dict) -> dict[str, Any]:
    """Args (in `data`):
        filing_text:   raw proxy / S-1 text (skips the fetch if supplied).
        cik:           issuer CIK (used to fetch the latest disclosure if no text).
        ticker:        for the optional bounded margin-call band.
        pledge_observations: [{date, pledged_shares, source, exact_date}] for the band.
        insider_name, earliest_pledge_date: passed through to the band wrapper.
        data_dir, cutoff, as_of: POINT-IN-TIME seam. `data_dir`+`cutoff` source the
            disclosure text from the cutoff-filtered corpus; `cutoff` caps mined
            Form-4/13D; `as_of` caps the price series + current_price. In a backtest
            pass cutoff=as_of=the evaluation date so nothing post-event leaks in.
    Returns a fire/no-fire dict; on fire, `sets_feature` activates the rest of the
    pledge family and `margin_call_band` carries the UNVERIFIABLE_BOUNDED estimate.
    """
    text = data.get("filing_text")
    cik = data.get("cik")
    cutoff = data.get("cutoff")
    as_of = data.get("as_of")
    if not text and cik:
        text = _latest_disclosure_text(cik, data.get("data_dir"), cutoff)
    if not text:
        return {"fires": False, "reason": "NO_PROXY_OR_S1_TEXT",
                "sets_feature": None, "evidence": {}}

    c = classify(_strip(text))
    if c["category"] != "AFFIRMATIVE_PLEDGE":
        return {"fires": False, "reason": c["category"], "sets_feature": None,
                "evidence": {"n_prohibition": c["n_prohibition"]}}

    shares = c.get("shares_pledged")
    finding = {
        "R": (f"{issuer_name} discloses an insider with company shares PLEDGED as "
              f"collateral" + (f" (~{shares:,} shares)" if shares else "") +
              " in the Item 403 beneficial-ownership disclosure."),
        "f": ("Narrow collateral-framing classifier (affirmative pledge vs anti-"
              "pledge policy vs none); on affirmative, anchor a bounded margin-call "
              "band to pledge-inception price via the Form-4/13D timeline + IPO "
              "lock-up floor."),
        "M": ("SEC EDGAR DEF 14A / S-1 Item 403; UCC-1/UCC-3 (debtor-keyed, on-"
              "demand) pins the exact date + lender."),
        "Finding": ("AFFIRMATIVE insider pledge"
                    + (f" — ~{shares:,} shares" if shares else "")
                    + ". Margin-call exposure is UNVERIFIABLE_BOUNDED."),
    }
    result: dict[str, Any] = {
        "fires": True,
        "reason": "INSIDER_SHARE_PLEDGE_AFFIRMED",
        "signal": "UNVERIFIABLE_BOUNDED",
        "sets_feature": SETS_FEATURE,
        "activates": ["m_sources.ucc_financing_statement",
                      "pledge_margin_call", "pledge_filings"],
        "shares_pledged": shares,
        "evidence": c["evidence"],
        "finding": finding,
    }

    obs = data.get("pledge_observations")
    ticker = data.get("ticker")
    if ticker and obs:
        from .. import pledge_margin_call as pmc
        try:
            result["margin_call_band"] = pmc.triangulate_with_filings(
                ticker, str(cik), obs,
                insider_name=data.get("insider_name"),
                earliest_pledge_date=data.get("earliest_pledge_date"),
                cutoff=cutoff, as_of=as_of,
            )
        except Exception as e:  # band is best-effort; the fire stands without it
            result["margin_call_band"] = {"error": f"{type(e).__name__}: {e}"}
    return result
