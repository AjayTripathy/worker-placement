"""Explicit local/hosted-folder corpus exchange: python -m officekit_research.corpus."""
import argparse
import json
from pathlib import Path

from .cases import (MAX_BYTES, approve, digest, import_bundle, load_library, prepare_case,
                    read_bundle, retrieve)
from officekit.migration import parse_json


def main(argv=None):
    parser = argparse.ArgumentParser(description="Prepare, review and reuse contextual research. No command publishes to the Internet.")
    sub = parser.add_subparsers(dest="command", required=True)
    draft = sub.add_parser("prepare", help="Write a private projection for review")
    draft.add_argument("--office", required=True, type=Path)
    draft.add_argument("--proposal", required=True)
    draft.add_argument("--symbol", required=True)
    draft.add_argument("--out", required=True, type=Path)
    seal = sub.add_parser("approve", help="Approve exactly the projection you have reviewed")
    seal.add_argument("draft", type=Path)
    seal.add_argument("--reviewed-sha256", required=True)
    seal.add_argument("--reuse-grants", type=Path, help="JSON list of section/basis/valid_until grants; absent means reference-only")
    seal.add_argument("--out", required=True, type=Path)
    imp = sub.add_parser("import", help="Import one reviewed bundle for consideration")
    imp.add_argument("bundle", type=Path)
    imp.add_argument("--office", required=True, type=Path)
    ls = sub.add_parser("list")
    ls.add_argument("--office", required=True, type=Path)
    query = sub.add_parser("query")
    query.add_argument("--office", required=True, type=Path)
    query.add_argument("--proposal", required=True)
    idx = sub.add_parser("index", help="Rebuild the derived research index and list research on a subject")
    idx.add_argument("--office", required=True, type=Path)
    idx.add_argument("--symbol")
    idx.add_argument("--strategy")
    idx.add_argument("--min-tier", type=int, help="Only research adjudicated at this capability tier or stronger")
    res = sub.add_parser("resolve", help="Record how a forecast resolved (append-only; needs a public source)")
    res.add_argument("--office", required=True, type=Path)
    res.add_argument("--forecast", required=True, help="<general research id>:<n>")
    res.add_argument("--outcome", required=True, choices=["true", "false"])
    res.add_argument("--source", required=True, help="Public HTTPS locator that settles it")
    res.add_argument("--note", default="")
    predict = sub.add_parser('predict', help='Register an immutable private binary prediction from JSON')
    predict.add_argument('--office', required=True, type=Path)
    predict.add_argument('file', type=Path)
    board = sub.add_parser("scoreboard", help="Calibration (Brier vs base rate) grouped by any research key")
    board.add_argument("--office", required=True, type=Path)
    board.add_argument("--by", default="adjudicate_model")
    args = parser.parse_args(argv)
    if args.command == 'predict':
        from officekit_research.predictions import record
        print(json.dumps(record(args.office, **parse_json(args.file.read_bytes())), indent=2))
        return 0
    if args.command in {"index", "resolve", "scoreboard"}:
        from officekit_research import index
        if args.command == "index":
            print(json.dumps(index.query(args.office, args.symbol, args.strategy, args.min_tier), indent=2))
        elif args.command == "resolve":
            print(json.dumps(index.resolve(args.office, args.forecast, args.outcome == "true", args.source, args.note), indent=2))
        else:
            print(json.dumps(index.scoreboard(args.office, args.by), indent=2))
        return 0
    if args.command in {"prepare", "query"}:
        from officekit.strategy_proposals import load
        proposal = load(args.office, args.proposal)
    if args.command == "prepare":
        record = prepare_case(proposal, args.symbol)
        args.out.write_text(json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        print("Private draft written. Review all narrative and source content before approving.")
        print("Current projection SHA256: " + digest(record["case"]))
    elif args.command == "approve":
        if args.draft.stat().st_size > MAX_BYTES:
            parser.error("Draft exceeds the case size limit")
        draft = parse_json(args.draft.read_bytes())
        grants = parse_json(args.reuse_grants.read_bytes()) if args.reuse_grants else []
        record = approve(draft, args.reviewed_sha256, grants)
        args.out.write_text(json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        print("Reviewed bundle written: " + record["id"] + ". Nothing has been published.")
    elif args.command == "import":
        print("Imported for consideration: " + import_bundle(args.office, read_bundle(args.bundle)))
    elif args.command == "list":
        bundles, errors = load_library(args.office)
        print(json.dumps({"cases": [{"id": b["id"], "subject": b["case"]["subject"], "context": b["case"]["context"]} for b in bundles], "errors": errors}, indent=2))
    else:
        print(json.dumps(retrieve(args.office, proposal), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
