"""universe_eval — grade the AI-1 classifier against the ENTIRE public universe.

    ANTHROPIC_API_KEY=... python3 -m officekit.evals.universe_eval \\
        --equities company_tickers.json --mf company_tickers_mf.json

Principal ruling (2026-09-04): the runtime model is the mechanism — a shipped
precomputed map would rot as tickers churn and get reassigned — so the
universe run is a TEST SUITE. Symbol-only (production worst case, and the MF
file carries no names anyway). What is honestly gradeable at this scale:

  equities file (~10k, SEC company_tickers.json — titles used as GROUND TRUTH
  ONLY, never shown to the model):
    - clear operating companies must classify single_name_equity. The
      load-bearing metric is FALSE-FUND rate: a confident fund suggestion for
      a plain stock is the one failure that reaches the confirm step wrong.
    - clearly fund-titled entries (ETF/index trusts) graded the other way.
    - ambiguous titles (e.g. banks named "... TRUST CORP") are EXCLUDED and
      counted — never fudged into either truth set.
  MF file (~28.5k class tickers, every one a fund by construction):
    - fund-vs-stock direction + confident coverage. Flavor-level truth
      (muni vs bond vs equity) needs the SEC series-name join — tracked as
      the eval's own extension, not silently skipped.

Writes a dated results JSON next to this file. Costs real API dollars — run
deliberately, not in CI.
"""
from __future__ import annotations

import argparse
import json
import re
import threading
import time
from datetime import date
from pathlib import Path

from officekit_ai.classify import _PROMPT, _SCHEMA, CLASSIFY_MODEL

BATCH = 150
WORKERS = 8

FUNDISH = re.compile(r"\bETF\b|\bETN\b|ISHARES|SPDR|PROSHARES|DIREXION|GRANITESHARES"
                     r"|\bINDEX FUND\b|EXCHANGE.TRADED|\bUNIT INVESTMENT TRUST\b", re.I)
AMBIG = re.compile(r"\bTRUST\b|\bFUND\b|\bFD\b|HOLDINGS TRUST|ROYALTY|\bREIT\b|ACQUISITION", re.I)


def load_cases(equities_path, mf_path):
    cases = {}
    eq = json.loads(Path(equities_path).read_text())
    for v in eq.values():
        sym, title = v["ticker"].upper(), v["title"]
        if FUNDISH.search(title):
            kind = "fundish"
        elif AMBIG.search(title):
            kind = "ambiguous"          # excluded from truth, counted
        else:
            kind = "stock"
        cases[sym] = {"kind": kind, "title": title}
    mf = json.loads(Path(mf_path).read_text())
    for row in mf.get("data", []):
        sym = (row[3] or "").upper().strip()
        if sym and sym not in cases:
            cases[sym] = {"kind": "mf", "title": None}
    return cases


def classify_all(symbols, model=CLASSIFY_MODEL, progress_path=None):
    import anthropic
    out, lock = {}, threading.Lock()
    batches = [symbols[i:i + BATCH] for i in range(0, len(symbols), BATCH)]
    idx = {"n": 0}

    def work(tid):
        cl = anthropic.Anthropic()
        while True:
            with lock:
                if idx["n"] >= len(batches):
                    return
                b = batches[idx["n"]]
                idx["n"] += 1
                done = idx["n"]
            listing = "\n".join(f"- {s}" for s in b)
            for attempt in (1, 2):
                try:
                    resp = cl.messages.create(
                        model=model, max_tokens=8000,
                        messages=[{"role": "user",
                                   "content": _PROMPT.format(symbols=listing)}],
                        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}})
                    text = next(x.text for x in resp.content if x.type == "text")
                    got = {c["symbol"].upper(): c for c in json.loads(text)["classifications"]}
                    with lock:
                        out.update(got)
                    break
                except Exception as e:
                    if attempt == 2:
                        with lock:
                            for s in b:
                                out.setdefault(s, {"category": "ERROR", "style": None,
                                                   "confidence": 0.0, "err": str(e)[:120]})
                    time.sleep(3)
            if progress_path and done % 20 == 0:
                Path(progress_path).write_text(f"{done}/{len(batches)} batches\n")

    threads = [threading.Thread(target=work, args=(i,)) for i in range(WORKERS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return out


def grade(cases, results):
    m = {"n_total": len(cases), "n_stock": 0, "n_fundish": 0, "n_mf": 0, "n_ambiguous_excluded": 0,
         "n_missing": 0, "n_error": 0,
         "stock_false_fund_confident": [],       # THE dangerous class
         "stock_false_fund_rate": None,
         "fundish_detected_confident": 0, "fundish_as_stock": 0,
         "mf_detected_fund_confident": 0, "mf_as_stock": 0, "mf_below_filter": 0}
    for sym, c in cases.items():
        got = results.get(sym)
        if got is None:
            m["n_missing"] += 1
            continue
        if got["category"] == "ERROR":
            m["n_error"] += 1
            continue
        conf = float(got.get("confidence") or 0)
        is_conf_fund = got["category"] != "single_name_equity" and conf >= 0.6
        if c["kind"] == "ambiguous":
            m["n_ambiguous_excluded"] += 1
        elif c["kind"] == "stock":
            m["n_stock"] += 1
            if is_conf_fund:
                m["stock_false_fund_confident"].append(
                    {"symbol": sym, "title": c["title"], "got": got["category"], "conf": conf})
        elif c["kind"] == "fundish":
            m["n_fundish"] += 1
            if is_conf_fund:
                m["fundish_detected_confident"] += 1
            elif got["category"] == "single_name_equity":
                m["fundish_as_stock"] += 1
        elif c["kind"] == "mf":
            m["n_mf"] += 1
            if is_conf_fund:
                m["mf_detected_fund_confident"] += 1
            elif got["category"] == "single_name_equity" and conf >= 0.6:
                m["mf_as_stock"] += 1
            else:
                m["mf_below_filter"] += 1
    if m["n_stock"]:
        m["stock_false_fund_rate"] = round(len(m["stock_false_fund_confident"]) / m["n_stock"], 5)
    return m


# ---- flavor pass: MF tickers WITH series names (the CSV production path) ----
# High-precision weak labels from series names: a fund named "...Tax-Exempt..."
# is a muni with near certainty. Label ONLY when exactly one family matches;
# multi-match and no-match are excluded and counted, never fudged.
FLAVOR_PATTERNS = {
    "cash": re.compile(r"MONEY MARKET", re.I),
    "municipal_credit": re.compile(r"TAX.EXEMPT|TAX.FREE|MUNICIPAL|\bMUNI\b", re.I),
    "fixed_income": re.compile(r"\bBOND\b|FIXED.INCOME|\bTREASURY\b", re.I),
    "public_equity": re.compile(r"STOCK MARKET|EQUITY|\bSTOCK\b|S&P 500|500 INDEX"
                                r"|GROWTH FUND|VALUE FUND|TARGET RETIREMENT|TARGET.DATE", re.I),
}


def load_icsc(icsc_path):
    """Class ticker -> series name, from the SEC Investment Company Series and
    Class Information CSV (the join the MF ticker file lacks)."""
    import csv as _csv
    out = {}
    with open(icsc_path, newline="", encoding="utf-8-sig") as f:
        for r in _csv.DictReader(f):
            t = (r.get("Class Ticker") or "").upper().strip()
            if t:
                out[t] = r.get("Series Name") or ""
    return out


def flavor_eval(icsc_path, limit=None, progress_path=None):
    names = load_icsc(icsc_path)
    labeled, skipped_multi, skipped_none = {}, 0, 0
    for sym, name in names.items():
        hits = [cat for cat, pat in FLAVOR_PATTERNS.items() if pat.search(name)]
        # MMF ticker convention: five letters ending XX is a money-market class;
        # a Treasury/bond-worded MMF would otherwise be mislabeled fixed_income
        if sym.endswith("XX") and "cash" not in hits:
            hits.append("cash")
        if len(hits) == 1:
            labeled[sym] = {"name": name, "want": hits[0]}
        elif len(hits) > 1:
            skipped_multi += 1
        else:
            skipped_none += 1
    syms = sorted(labeled)
    if limit:
        syms = syms[:limit]
    # the model sees symbol + series name — exactly what the CSV path sees
    import anthropic  # noqa: F401 — fail early if absent
    results = {}
    batches = [syms[i:i + BATCH] for i in range(0, len(syms), BATCH)]
    lock = threading.Lock()
    idx = {"n": 0}

    def work(tid):
        import anthropic
        cl = anthropic.Anthropic()
        while True:
            with lock:
                if idx["n"] >= len(batches):
                    return
                b = batches[idx["n"]]
                idx["n"] += 1
                done = idx["n"]
            listing = "\n".join(f"- {s}: {labeled[s]['name']}" for s in b)
            for attempt in (1, 2):
                try:
                    resp = cl.messages.create(
                        model=CLASSIFY_MODEL, max_tokens=8000,
                        messages=[{"role": "user", "content": _PROMPT.format(symbols=listing)}],
                        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}})
                    text = next(x.text for x in resp.content if x.type == "text")
                    with lock:
                        results.update({c["symbol"].upper(): c
                                        for c in json.loads(text)["classifications"]})
                    break
                except Exception:
                    if attempt == 2:
                        with lock:
                            for s in b:
                                results.setdefault(s, {"category": "ERROR", "confidence": 0.0})
                    time.sleep(3)
            if progress_path and done % 20 == 0:
                Path(progress_path).write_text(f"flavor {done}/{len(batches)} batches\n")

    threads = [threading.Thread(target=work, args=(i,)) for i in range(WORKERS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    n = correct = 0
    confident_wrong = []
    below_filter = missing = errors = 0
    for sym in syms:
        got = results.get(sym)
        if got is None:
            missing += 1
            continue
        if got["category"] == "ERROR":
            errors += 1
            continue
        n += 1
        conf = float(got.get("confidence") or 0)
        if got["category"] == labeled[sym]["want"]:
            correct += 1
        elif conf >= 0.6 and got["category"] != "single_name_equity":
            confident_wrong.append({"symbol": sym, "name": labeled[sym]["name"],
                                    "want": labeled[sym]["want"],
                                    "got": got["category"], "conf": conf})
        else:
            below_filter += 1
    rows_out = [{"symbol": s, "name": labeled[s]["name"], "want": labeled[s]["want"],
                 "got": results.get(s, {}).get("category"),
                 "conf": results.get(s, {}).get("confidence")} for s in syms]
    return {"date": date.today().isoformat(), "model": CLASSIFY_MODEL,
            "rows": rows_out,
            "n_labeled_universe": len(labeled), "n_graded": n,
            "skipped_multi_pattern": skipped_multi, "skipped_no_pattern": skipped_none,
            "flavor_accuracy": round(correct / n, 4) if n else None,
            "confident_wrong_rate": round(len(confident_wrong) / n, 5) if n else None,
            "confident_wrong_sample": confident_wrong[:40],
            "n_confident_wrong": len(confident_wrong),
            "below_filter_or_stockish": below_filter,
            "missing": missing, "errors": errors}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--equities")
    ap.add_argument("--mf")
    ap.add_argument("--limit", type=int, help="debug: cap symbol count")
    ap.add_argument("--progress")
    ap.add_argument("--icsc", help="SEC series/class CSV — run the FLAVOR pass (names attached, CSV production path) instead")
    args = ap.parse_args(argv)
    if args.icsc:
        metrics = flavor_eval(args.icsc, limit=args.limit, progress_path=args.progress)
        out = Path(__file__).parent / f"universe_flavor_eval_{metrics['date'].replace('-', '')}.json"
        out.write_text(json.dumps(metrics, indent=1))
        print(json.dumps({k: v for k, v in metrics.items()
                          if k not in ("confident_wrong_sample", "rows")}, indent=1))
        print(f"[universe_eval] flavor results -> {out}")
        return
    cases = load_cases(args.equities, args.mf)
    syms = sorted(cases)
    if args.limit:
        syms = syms[:args.limit]
        cases = {s: cases[s] for s in syms}
    print(f"[universe_eval] {len(syms)} symbols "
          f"({sum(1 for c in cases.values() if c['kind'] == 'stock')} stocks, "
          f"{sum(1 for c in cases.values() if c['kind'] == 'fundish')} fund-titled, "
          f"{sum(1 for c in cases.values() if c['kind'] == 'mf')} MF, "
          f"{sum(1 for c in cases.values() if c['kind'] == 'ambiguous')} ambiguous-excluded)")
    t0 = time.time()
    results = classify_all(syms, progress_path=args.progress)
    metrics = grade(cases, results)
    metrics["date"] = date.today().isoformat()
    metrics["model"] = CLASSIFY_MODEL
    metrics["minutes"] = round((time.time() - t0) / 60, 1)
    out = Path(__file__).parent / f"universe_eval_{metrics['date'].replace('-', '')}.json"
    out.write_text(json.dumps({"metrics": metrics,
                               "raw_counts_only": "per-symbol rows omitted; rerun to regenerate"},
                              indent=1))
    print(json.dumps(metrics, indent=1, default=str)[:4000])
    print(f"[universe_eval] results -> {out}")


if __name__ == "__main__":
    main()
