#!/usr/bin/env python3
"""In-place re-clean of the on-disk SEC filing corpus.

The saved `data/<ticker>/filings/<accession>_<form>.txt` files are RAW HTML
(tag-polluted): any detector that reads them via `data_dir` gets the pre-clean-extract
recall bug (inline-XBRL tags wedged between a verb and its number; tables invisible).
Live fetches already go through `edgar.fetch_filing_clean`; this fixes what's on disk.

Key point: this is a RE-CLEAN, not a re-harvest — the HTML is already local, so we apply
the SAME pure function (`edgar.html_to_clean_text`) with NO network. It is point-in-time
safe (the filename IS the accession, so the document identity never changes) and
idempotent (already-clean files are skipped).

  DRY RUN (default): reports polluted count, raw size, estimated cleaned size + savings,
                     per-ticker — writes nothing.
  --apply          : rewrite polluted files in place (atomic temp+rename).
  --tickers a,b    : limit scope (e.g. the live set: gps,vrrm).
"""
from __future__ import annotations

import argparse
import os
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # verticals/public_co
sys.path.insert(0, str(ROOT.parents[1]))            # repo root
from verticals.public_co.edgar import html_to_clean_text

DATA = ROOT / "data"
_HTML_SIG = re.compile(r"</?(?:span|div|td|tr|table|p|font|html|body|ix:[a-z]+)\b|style=", re.I)
_XML_SIG = re.compile(r"<\?xml|<ownershipDocument|</XBRL>", re.I)


def _head(path: Path, n: int = 200_000) -> str:
    with open(path, "r", errors="ignore") as fh:
        return fh.read(n)


def classify(path: Path) -> str:
    """clean | xml | polluted — cheap (reads only the head + stat size)."""
    head = _head(path)
    if _XML_SIG.search(head[:2000]) and "<html" not in head[:2000].lower():
        return "xml"
    return "polluted" if len(_HTML_SIG.findall(head)) >= 30 else "clean"


def iter_corpus(tickers: set[str]):
    for f in DATA.rglob("*.txt"):
        if f.parent.name != "filings":
            continue
        tk = f.relative_to(DATA).parts[0].lower()
        if tickers and tk not in tickers:
            continue
        yield tk, f


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="rewrite in place (default: dry run)")
    ap.add_argument("--tickers", default="", help="comma list to limit scope, e.g. gps,vrrm")
    ap.add_argument("--sample", type=int, default=40, help="files parsed to estimate the dry-run ratio")
    args = ap.parse_args()
    tickers = {t.strip().lower() for t in args.tickers.split(",") if t.strip()}

    n_clean = n_xml = 0
    polluted: list[tuple[str, Path, int]] = []
    by_ticker: dict[str, list[int]] = {}
    for tk, f in iter_corpus(tickers):
        kind = classify(f)
        if kind == "polluted":
            sz = f.stat().st_size
            polluted.append((tk, f, sz))
            r = by_ticker.setdefault(tk, [0, 0]); r[0] += 1; r[1] += sz
        elif kind == "xml":
            n_xml += 1
        else:
            n_clean += 1

    raw_poll = sum(s for _, _, s in polluted)

    if not args.apply:
        sample = random.Random(0).sample(polluted, min(args.sample, len(polluted))) if polluted else []
        raw_s = clean_s = 0
        for _, f, sz in sample:
            try:
                cl = html_to_clean_text(f.read_text(errors="ignore")) or ""
            except Exception:
                continue
            raw_s += sz
            clean_s += len(cl)
        ratio = (clean_s / raw_s) if raw_s else 0.1
        print("DRY RUN — no files written\n")
        print(f"scanned           : {n_clean + n_xml + len(polluted):,} .txt files"
              + (f"  (tickers={','.join(sorted(tickers))})" if tickers else ""))
        print(f"  already clean   : {n_clean:,}  (skip)")
        print(f"  xml/structured  : {n_xml:,}  (skip)")
        print(f"  POLLUTED html   : {len(polluted):,}  (would re-clean)")
        print(f"raw size polluted : {raw_poll / 1e9:.2f} GB")
        print(f"est cleaned size  : {raw_poll * ratio / 1e9:.2f} GB   (sample ratio {ratio:.1%}, n={len(sample)})")
        print(f"est savings       : {raw_poll * (1 - ratio) / 1e9:.2f} GB  ({1 - ratio:.0%} smaller)")
        print("\ntop tickers by polluted raw size:")
        for tk, (n, b) in sorted(by_ticker.items(), key=lambda x: -x[1][1])[:15]:
            print(f"  {tk:10s} {n:4d} files  {b / 1e6:8.1f} MB")
        print("\nrun with  --apply  [--tickers gps,vrrm]  to rewrite in place")
        return

    done = skipped = 0
    saved = 0
    for tk, f, raw_sz in polluted:
        try:
            cl = html_to_clean_text(f.read_text(errors="ignore"))
        except Exception as e:
            print(f"  ERR {f.name}: {e}", file=sys.stderr)
            continue
        if not cl or len(cl) >= raw_sz * 0.9:   # didn't actually clean → leave untouched
            skipped += 1
            continue
        tmp = f.with_suffix(".txt.tmp")
        tmp.write_text(cl)
        os.replace(tmp, f)                       # atomic
        done += 1
        saved += raw_sz - len(cl)
        if done % 200 == 0:
            print(f"  ...{done:,} cleaned, {saved / 1e9:.2f} GB freed")
    print(f"APPLIED: re-cleaned {done:,} files, freed {saved / 1e9:.2f} GB"
          f" ({skipped:,} left as-is: cleaning didn't shrink them)")


if __name__ == "__main__":
    main()
