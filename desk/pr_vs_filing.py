"""pr_vs_filing — marketed-takeaway vs filed-numbers divergence (thesis menu 2026-08-31).

The honesty-alpha plane, mechanized: the press release is the MARKETED document, the filing is
the SWORN one. Divergence between them is the signal (multi-venue consistency sibling; the
BELFA/CDRE class of catches). Narrow high-precision checks, UNION not weighted average:

  1. omitted_metric   — a metric named in the PRIOR earnings PR is absent from the CURRENT one
                        (claim_evolution absence; secondary-endpoint doctrine: absence is a
                        review_flag, not a conviction).
  2. record_vs_gaap   — headline says "record" while the issuer's own XBRL shows latest-quarter
                        revenue AND net income down YoY (checked only when "record" appears —
                        one extra fetch, gated).
  3. guide_language   — prior PR raised guidance, current PR "reaffirms/maintains/revises":
                        language downgrade ahead of the numbers (weak flag, never enqueues
                        alone).

Universe: US-listed research-ledger names (the desk's own book+watch surface — integrity events
on KNOWN names re-triage, P2 flow). EDGAR submissions JSON -> two most recent 8-Ks with an
EX-99 earnings exhibit -> exhibit text. SEC UA header everywhere; ~4 fetches/name worst case.

    python3 -m desk.pr_vs_filing [--max N] [--enqueue] [--dry] [--tickers A,B]
Flags land in desk/data/pr_vs_filing.json; strong flags (1 or 2) mail; --enqueue routes
strong-flag names to the conveyor (TRAP_VERIFY, allow_ledger — courts grade the divergence).
"""
from __future__ import annotations

import datetime
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "pr_vs_filing.json"
CIKMAP = ROOT / "desk" / "data" / "cik_map.json"
UA = {"User-Agent": "SignalOS Research <4tripathy@gmail.com>"}

# Infix-tolerant patterns (NTRS lesson 2026-08-31: "organic trust-fee growth" and "Return on
# Average Common Equity" broke literal bigrams — a matcher artifact, not an omission).
W = r"(?:[\w-]+\s+){0,3}"
METRIC_PATTERNS = {
    "adjusted ebitda": r"adjusted\s+ebitda",
    "free cash flow": r"free\s+cash\s+flow",
    "organic growth": rf"organic\s+{W}(?:growth|revenue)",
    "same-store sales": r"(?:same[- ]store|comparable(?:[- ]store)?)\s+sales",
    "backlog": r"\bbacklog\b",
    "book-to-bill": r"book[- ]to[- ]bill",
    "gross margin": r"gross\s+(?:profit\s+)?margin",
    "operating margin": r"operating\s+margin",
    "net revenue retention": r"net\s+(?:revenue|dollar)\s+retention",
    "recurring revenue": r"(?:annual(?:ized)?\s+)?recurring\s+revenue|\barr\b",
    "bookings": r"\bbookings\b",
    "billings": r"\bbillings\b",
    "unit volume": r"unit\s+volumes?",
    "average selling price": r"average\s+selling\s+price",
    "churn": r"\bchurn\b",
    "net debt": r"net\s+debt",
    "return on equity": rf"return\s+on\s+{W}equity",
    "combined ratio": r"combined\s+ratio",
}
RAISE_RX = re.compile(r"\b(rais\w+|increas\w+)\b[^.]{0,80}\bguidance\b|\bguidance\b[^.]{0,80}\b(rais\w+|increas\w+)\b", re.I)
SOFT_RX = re.compile(r"\b(reaffirm\w*|maintain\w*|revis\w*|updat\w*)\b[^.]{0,80}\bguidance\b|\bguidance\b[^.]{0,80}\b(reaffirm\w*|maintain\w*|revis\w*|updat\w*)\b", re.I)


def _get(url: str, retries: int = 2) -> bytes:
    for i in range(retries + 1):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45).read()
        except Exception:
            if i == retries:
                raise
            time.sleep(1.5 * (i + 1))
    raise RuntimeError("unreachable")


def cik_map() -> dict[str, str]:
    if CIKMAP.exists() and time.time() - CIKMAP.stat().st_mtime < 30 * 86400:
        return json.loads(CIKMAP.read_text())
    data = json.loads(_get("https://www.sec.gov/files/company_tickers.json"))
    m = {r["ticker"].upper(): str(r["cik_str"]).zfill(10) for r in data.values()}
    CIKMAP.write_text(json.dumps(m))
    return m


def earnings_prs(cik: str) -> list[dict]:
    """Two most recent 8-K filings carrying an EX-99* exhibit whose name suggests results."""
    sub = json.loads(_get(f"https://data.sec.gov/submissions/CIK{cik}.json"))
    rec = sub["filings"]["recent"]
    out = []
    cutoff = (datetime.date.today() - datetime.timedelta(days=450)).isoformat()
    for form, acc, date, doc in zip(rec["form"], rec["accessionNumber"],
                                    rec["filingDate"], rec["primaryDocument"]):
        if form not in ("8-K", "6-K") or len(out) >= 2:
            continue
        if date < cutoff:      # stale-basis guard: the CB first-run false positive compared a
            break              # 2021 PR to a 2023 PR — consecutive-quarter comparisons only
        accn = acc.replace("-", "")
        try:
            idx = json.loads(_get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}/index.json"))
            ex = [f["name"] for f in idx["directory"]["item"]
                  if re.match(r".*ex[-_]?99", f["name"], re.I) and f["name"].endswith((".htm", ".html"))]
            if not ex:
                continue
            txt = _get(f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}/{ex[0]}").decode("utf-8", "ignore")
            txt = re.sub(r"<[^>]+>", " ", txt)
            txt = re.sub(r"\s+", " ", txt).lower()
            if not re.search(r"(quarter|fiscal|full[- ]year).{0,60}(results|revenue|earnings)", txt[:3000]):
                continue
            out.append(dict(date=date, acc=accn, text=txt))
        except Exception:
            continue
    return out


def xbrl_down_yoy(cik: str) -> bool | None:
    """True when latest quarterly revenue AND net income are both down YoY per companyfacts."""
    try:
        facts = json.loads(_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"))
        gaap = facts["facts"].get("us-gaap", {})
        def latest_yoy(tags):
            for tag in tags:
                units = gaap.get(tag, {}).get("units", {}).get("USD", [])
                q = [u for u in units if u.get("form") in ("10-Q", "10-K") and u.get("frame") is None
                     and u.get("start") and u.get("end")
                     and 80 <= (datetime.date.fromisoformat(u["end"]) - datetime.date.fromisoformat(u["start"])).days <= 100]
                if len(q) < 5:
                    continue
                q.sort(key=lambda u: u["end"])
                cur = q[-1]
                target = datetime.date.fromisoformat(cur["end"]) - datetime.timedelta(days=365)
                py = min(q[:-1], key=lambda u: abs((datetime.date.fromisoformat(u["end"]) - target).days))
                if abs((datetime.date.fromisoformat(py["end"]) - target).days) > 45:
                    continue
                return cur["val"] < py["val"]
            return None
        rev = latest_yoy(["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                          "RevenueFromContractWithCustomerIncludingAssessedTax"])
        ni = latest_yoy(["NetIncomeLoss"])
        if rev is None or ni is None:
            return None
        return rev and ni
    except Exception:
        return None


def check(t: str, cik: str) -> dict | None:
    prs = earnings_prs(cik)
    if len(prs) < 2:
        return None
    cur, prior = prs[0], prs[1]
    gap = (datetime.date.fromisoformat(cur["date"]) - datetime.date.fromisoformat(prior["date"])).days
    if not 45 <= gap <= 210:   # consecutive-ish quarters only (annual+Q gap tops ~200d)
        return None
    flags = []
    omitted = [label for label, rx in METRIC_PATTERNS.items()
               if re.search(rx, prior["text"], re.I) and not re.search(rx, cur["text"], re.I)]
    if omitted:
        # Direction gate (NTRS lesson): masking requires deterioration. Coarse v1 proxy —
        # suppress the flag when latest-quarter net income is UP YoY (improving book has no
        # masking motive; the omission is presentational).
        ni_down = xbrl_down_yoy(cik)
        if ni_down is False:
            print(f"[pr_vs_filing] {t}: omitted {omitted} SUPPRESSED (direction gate: not "
                  f"deteriorating per XBRL rev+NI)", flush=True)
        else:
            flags.append(dict(kind="omitted_metric", strength="STRONG", detail=omitted,
                              note=f"named in {prior['date']} PR, absent {cur['date']}"
                                   + ("" if ni_down else "; direction UNVERIFIED (XBRL gap)")))
    if "record" in cur["text"][:2500]:
        down = xbrl_down_yoy(cik)
        if down:
            flags.append(dict(kind="record_vs_gaap", strength="STRONG",
                              detail="headline 'record' while XBRL revenue AND net income down YoY"))
    if RAISE_RX.search(prior["text"]) and SOFT_RX.search(cur["text"]) and not RAISE_RX.search(cur["text"]):
        flags.append(dict(kind="guide_language", strength="WEAK",
                          detail=f"raise language {prior['date']} -> maintain/revise {cur['date']}"))
    if not flags:
        return None
    return dict(ticker=t, pr_dates=[prior["date"], cur["date"]], flags=flags)


def run(max_names: int = 40, enqueue: bool = False, dry: bool = False,
        only: list[str] | None = None) -> int:
    led = json.loads((ROOT / "desk/data/research_ledger.json").read_text())["names"]
    us = [n["ticker"] for n in led
          if n.get("state") not in ("KILLED",) and "." not in n.get("ticker", "")
          and "-" not in n.get("ticker", "")]
    if only:
        us = [t for t in us if t in only] or only
    prev = json.loads(STATE.read_text()) if STATE.exists() else {}
    checked_at = prev.get("checked_at", {})
    us.sort(key=lambda t: checked_at.get(t, ""))          # stalest-first rotation
    us = us[:max_names]
    m = cik_map()
    findings, errors = [], 0
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    for t in us:
        cik = m.get(t)
        if not cik:
            continue
        try:
            f = check(t, cik)
            checked_at[t] = now
            if f:
                findings.append(f)
                print(f"[pr_vs_filing] {t}: " + "; ".join(x["kind"] for x in f["flags"]), flush=True)
            else:
                print(f"[pr_vs_filing] {t}: clean", flush=True)
        except Exception as e:
            errors += 1
            print(f"[pr_vs_filing] {t} error {type(e).__name__}")
        time.sleep(0.4)
    if errors and errors >= max(3, len(us) // 2):
        print(f"[pr_vs_filing] INFRA: {errors}/{len(us)} errored — treat run as blocked, not clean")
    out = dict(asof=now, universe_size=len(us), findings=findings,
               checked_at=checked_at, errors=errors)
    if not dry:
        old = prev.get("findings", [])
        keep = [f for f in old if f["ticker"] not in {x["ticker"] for x in findings}]
        out["findings"] = findings + keep[:200]
        STATE.write_text(json.dumps(out, indent=1))
    strong = [f for f in findings if any(x["strength"] == "STRONG" for x in f["flags"])]
    print(f"[pr_vs_filing] {len(us)} checked, {len(findings)} flagged ({len(strong)} strong), {errors} errors")
    if strong and not dry:
        try:
            from desk.mailer import send_raw
            body = "\n\n".join(f"{f['ticker']} ({'/'.join(f['pr_dates'])}): " +
                               "; ".join(f"{x['kind']}[{x['strength']}] {x['detail']}" for x in f["flags"])
                               for f in strong)
            send_raw(f"PR-VS-FILING: {len(strong)} strong divergence flag(s)", body)
        except Exception as e:
            print(f"[pr_vs_filing] mail failed: {e}")
    if strong and enqueue and not dry:
        from desk.court_queue import enqueue_candidates
        rows = [dict(ticker=f["ticker"], pr_dates=f["pr_dates"], flags=f["flags"],
                     context="PR-vs-filing divergence: the marketed document dropped or "
                             "contradicted the sworn one — cause-check whether the omission is "
                             "hierarchical disclosure (review_flag, benign) or masking")
                for f in strong]
        c = enqueue_candidates(rows, source=f"pr_vs_filing/{datetime.date.today()}",
                               allow_ledger=True)
        print(f"[pr_vs_filing] enqueued {c['added']}")
    return 0


if __name__ == "__main__":
    import sys
    a = sys.argv[1:]
    mx = int(a[a.index("--max") + 1]) if "--max" in a else 40
    only = a[a.index("--tickers") + 1].split(",") if "--tickers" in a else None
    run(max_names=mx, enqueue="--enqueue" in a, dry="--dry" in a, only=only)
