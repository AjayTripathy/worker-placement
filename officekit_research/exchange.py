"""The research exchange: general research, shared as open source.

LAYOUT (a plain directory, designed to live in a git repository):

    general/<SYMBOL>/<record id>.json        the research itself — content-addressed, immutable
    attribution/<record id>/<who>.json       who stands behind it (pseudonym or anonymous)
    reviews/<record id>.json                 publisher's claim-admission receipt
    outcomes/<record id>.jsonl               how its forecasts resolved — append-only, sourced
    catalog.json                             derived listing, rebuilt on every change

One file per record means two contributors never edit the same file, identical
research from two offices collapses to ONE record with two attributions, and a
re-submission is a no-op. Nothing here is ever rewritten except the catalog.

WHAT MAY ENTER. Only GENERAL research (officekit_research.general): evaluated
for no investor, from public evidence, by a court that was never shown an
office. Contextual cases do not belong here — they carry household context and
need a human reviewer (officekit_research.cases). Admission re-validates
the structure and refuses LITE (unevidenced) research. Publication requires a
separate independent claim review. File receipts are publisher assertions;
they are neither signed attestations nor a guarantee of factual correctness.

THE TRIPWIRE. Privacy here is by construction, so the tripwire should never
fire. It exists for the day the construction is broken by a future change:
before an office's own record is committed, every private string the office
knows about itself (names, account labels, dollar amounts) is searched for in
the record. A hit refuses the commit and says why. It is a smoke detector,
not the fire wall.

COMMITS. `submit` commits to the exchange's git repository automatically,
under a neutral author and a date-only timestamp, because a commit signed with
the contributor's own git identity would undo the pseudonym.

PUSH POLICY — by what the research is ABOUT:

    public equities (stock, etf)   pushed IMPLICITLY after the commit. An office
                                   turns that off with `auto_push: false`.
    private companies / deals      NEVER pushed implicitly. Not even committed:
                                   they wait in `held/`, which git ignores,
                                   until someone runs `release`.

`held/` exists because `git push` publishes every local commit on the branch.
A private record that was merely committed would ride out on the next implicit
public-equity push. Keeping it out of the committed tree is the only way
"explicit" can be true.

An implicit push also requires the exchange to be its OWN repository. Pointed
at a folder inside a larger repository, an implicit push would publish that
repository's unrelated commits, so it is refused and reported instead.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess

from officekit.migration import canonical, parse_json
from officekit_research import general as general_store
from officekit_research.cases import (HASH, MAX_BYTES, PUBLIC_SECTIONS, _identifiers, _write, content_sha256, day,
                                      safe_url, text)
from officekit_research.contributor import contributor_key, settings, valid as valid_key

ATTRIBUTION = "research_attribution_v1"
AUTHOR = ("officekit-exchange", "exchange@example.invalid")
MIN_RESOLVED = 20
README = """# Research exchange

General research contributed by officekit offices: securities evaluated for no
particular investor, from public evidence. Nothing here is advice, and nothing
here knows anything about you. Your own office always rules on suitability.

- `general/<SYMBOL>/<id>.json` — immutable, content-addressed evaluations
- `attribution/<id>/` — pseudonymous or anonymous contributors
- `reviews/<id>.json` — record-bound publisher claim-admission receipt
- `outcomes/<id>.jsonl` — how forecasts resolved (append-only, publicly sourced)
- `catalog.json` — derived index; do not edit by hand

Every record names the models and protocol that produced it. Track records are
scored against each forecast's own base rate and are not reported until a
contributor has enough resolved forecasts to mean something.
"""


# ---- admission ------------------------------------------------------------------

def admit(record):
    """Structural gate only; write/hosted submit also require claim admission."""
    record = general_store.validate(record)
    if record["label"] != "EVIDENCED" or not record["evidence"]:
        raise ValueError("The exchange admits only evidenced research; this evaluation cites no public source")
    if not any(e["source_url"] for e in record["evidence"]):
        raise ValueError("The exchange admits only research with at least one public source locator")
    return record


def tripwire(record, snapshot):
    """Refuse to publish if anything this office knows about itself is in the record."""
    subject = record["subject"]["symbol"]
    blob = canonical({k: v for k, v in record.items() if k != "evidence"}).decode()
    found = []
    for token in _identifiers({"snapshot": snapshot or {}}):
        if token.upper() == subject or len(token) < 4:
            continue
        if re.search(r"(?<!\w)" + re.escape(token) + r"(?!\w)", blob, flags=re.I):
            found.append(token)
    if found:
        # Never echo the private strings themselves into an error that may be logged or shown.
        raise ValueError("Research withheld: %d detail(s) private to this office appear in the record. "
                         "The general court should never have seen them — this needs investigation, not an override." % len(found))


# ---- the directory --------------------------------------------------------------

def _root(root):
    root = Path(root).expanduser().resolve()
    if root.is_symlink():
        raise ValueError("The exchange cannot be a symbolic link")
    return root


def _record_path(root, record):
    return root / "general" / record["subject"]["symbol"] / (record["id"] + ".json")


def init(root):
    root = _root(root)
    for name in ("general", "attribution", "outcomes", "held"):
        (root / name).mkdir(parents=True, exist_ok=True)
    if not (root / "README.md").exists():
        (root / "README.md").write_text(README, encoding="utf-8")
    # held/ must never be committed: it is where private-deal research waits for an explicit release.
    ignore = root / ".gitignore"
    lines = ignore.read_text(encoding="utf-8").splitlines() if ignore.exists() else []
    if "held/" not in lines:
        ignore.write_text("\n".join(lines + ["held/"]) + "\n", encoding="utf-8")
    return root


def is_private(record):
    return record["subject"]["instrument"] not in general_store.PUBLIC_SUBJECTS


def hold(root, record, contributor=None, attribution="claimed", review=None):
    """Park private-deal research outside the committed tree. Returns its path."""
    root = init(root)
    record = admit(record)
    if not valid_key(contributor):
        raise ValueError("Invalid attribution")
    path = root / "held" / (record["id"] + ".json")
    if not path.exists():
        _write(path, {"record": record, "contributor": contributor, "attribution": attribution,
                      "review": review.report if review else None})
    return path


def held(root):
    out = []
    for path in sorted((_root(root) / "held").glob("*.json")):
        try:
            item = parse_json(path.read_bytes())
            record = admit(item["record"])
            if path.stem == record["id"] and valid_key(item.get("contributor")):
                out.append(item)
        except (ValueError, OSError, KeyError, TypeError):
            continue
    return out


def release(root, record_id, publish=False):
    """The EXPLICIT act that lets private-deal research into the shared corpus.

    Moves one held record into the committed tree and commits it. `publish`
    also pushes — still explicit, because the caller asked for it by name.
    """
    root = _root(root)
    item = next((h for h in held(root) if h["record"]["id"] == record_id), None)
    if item is None:
        raise ValueError("No held research with that identity")
    record = item["record"]
    from officekit_research.admission import Admission
    if not item.get("review"):
        raise ValueError("Held research needs independent claim review before release")
    changed = write(root, record, item.get("contributor"), item.get("attribution") or "claimed", released=True,
                    review=Admission(record["id"], item["review"]))
    (root / "held" / (record_id + ".json")).unlink(missing_ok=True)
    catalog(root)
    sha = commit(root, changed + [root / "catalog.json"],
                 f"research: RELEASED private evaluation {record['subject']['symbol']} {record_id[:12]}\n\n"
                 "Released by an explicit act; private-deal research is never published implicitly.")
    return {"record_id": record_id, "commit": sha, "pushed": push(root) if publish else False}


def _who(contributor):
    return contributor if contributor else "anonymous"


def write(root, record, contributor=None, attribution="claimed", submitted=None, released=False, *, review=None):
    """Place an admitted record and its attribution. Idempotent. Returns changed paths."""
    root = init(root)
    record = admit(record)
    if is_private(record) and not released:
        raise ValueError("Private-deal research enters the shared corpus only through an explicit release")
    from officekit_research.admission import Admission, check_receipt
    if not isinstance(review, Admission):
        raise ValueError("Publication requires an independent claim review")
    receipt = check_receipt(record, review.receipt())
    if not valid_key(contributor) or attribution not in {"claimed", "verified"}:
        raise ValueError("Invalid attribution")
    changed = []
    review_path = root / "reviews" / (record["id"] + ".json")
    if not review_path.exists():
        _write(review_path, receipt)
        changed.append(review_path)
    path = _record_path(root, record)
    if not path.exists():
        _write(path, record)
        changed.append(path)
    envelope = {"schema": ATTRIBUTION, "record_id": record["id"], "contributor": contributor,
                "attribution": attribution if contributor else "anonymous",
                "protocol_hash": record["protocol_hash"],
                # Date only: a precise timestamp is a linkage side-channel.
                "submitted_on": (submitted or datetime.now(timezone.utc).date()).isoformat()}
    who = root / "attribution" / record["id"] / (_who(contributor) + ".json")
    if not who.exists():
        _write(who, envelope)
        changed.append(who)
    return changed


def records(root, symbol=None):
    base = _root(root) / "general"
    pattern = (symbol.upper() + "/*.json") if symbol else "*/*.json"
    out = []
    for path in sorted(base.glob(pattern)):
        try:
            if path.is_symlink() or path.stat().st_size > MAX_BYTES:
                continue
            record = admit(parse_json(path.read_bytes()))
            from officekit_research.admission import check_receipt
            check_receipt(record, parse_json((_root(root) / "reviews" / (record["id"] + ".json")).read_bytes()))
            if path.stem == record["id"] and path.parent.name == record["subject"]["symbol"]:
                out.append(record)
        except (ValueError, OSError):
            continue                         # a malformed file is never research
    return out


def contributors(root, record_id):
    out = []
    for path in sorted((_root(root) / "attribution" / record_id).glob("*.json")):
        try:
            e = parse_json(path.read_bytes())
            if e.get("schema") == ATTRIBUTION and e.get("record_id") == record_id and valid_key(e.get("contributor")):
                out.append(e)
        except (ValueError, OSError):
            continue
    return out


def outcomes(root):
    """Latest public resolution per forecast across the exchange."""
    out = {}
    for path in sorted((_root(root) / "outcomes").glob("*.jsonl")):
        if path.is_symlink() or not HASH.fullmatch(path.stem):
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                if str(row["forecast_id"]).startswith(path.stem + ":") and type(row["outcome"]) is bool:
                    safe_url(row["source_url"])
                    out[row["forecast_id"]] = row
            except (ValueError, KeyError, TypeError):
                continue
    return out


def resolve(root, forecast_id, outcome, source_url, note="", contributor=None, resolved_on=None):
    """Publish how a forecast resolved. Anyone may; it must cite a public source."""
    if type(outcome) is not bool or not valid_key(contributor):
        raise ValueError("A forecast resolves true or false")
    safe_url(source_url)
    text(note, 600)
    gid, _, n = str(forecast_id).partition(":")
    record = next((r for r in records(root) if r["id"] == gid), None) if HASH.fullmatch(gid) else None
    if record is None or not n.isdigit() or int(n) >= len(record["assessment"]["forecasts"]):
        raise ValueError("Unknown forecast")
    when = (resolved_on or datetime.now(timezone.utc).date()).isoformat()
    if day(when) > datetime.now(timezone.utc).date():
        raise ValueError("A forecast cannot resolve in the future")
    if day(when) < day(record["as_of"]):
        raise ValueError("A forecast cannot resolve before it was made")
    row = {"forecast_id": forecast_id, "outcome": bool(outcome), "resolved_on": when,
           "source_url": source_url, "note": note, "contributor": contributor}
    path = init(root) / "outcomes" / (gid + ".jsonl")
    if path.is_symlink():
        raise ValueError("Exchange storage cannot follow symbolic links")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def catalog(root):
    """Deterministic, derived listing — stable ordering keeps diffs reviewable."""
    root = init(root)
    resolved = outcomes(root)
    symbols = {}
    for r in records(root):
        who = contributors(root, r["id"])
        forecasts = r["assessment"]["forecasts"]
        symbols.setdefault(r["subject"]["symbol"], []).append({
            "id": r["id"], "instrument": r["subject"]["instrument"], "as_of": r["as_of"],
            "standing": r["assessment"]["standing"], "confidence": r["assessment"]["confidence"],
            "factors": {f["factor"]: f["exposure"] for f in r["assessment"]["factor_profile"]},
            "tier": r["tier"], "models": r["models"], "protocol_hash": r["protocol_hash"],
            "contributors": len(who), "verified_contributors": sum(e["attribution"] == "verified" for e in who),
            "forecasts": len(forecasts),
            "resolved": sum((r["id"] + ":" + str(i)) in resolved for i in range(len(forecasts)))})
    for rows in symbols.values():
        rows.sort(key=lambda x: (x["as_of"], x["id"]), reverse=True)
    value = {"v": 1, "records": sum(map(len, symbols.values())), "symbols": dict(sorted(symbols.items()))}
    _write(root / "catalog.json", value)
    return value


# ---- reading the exchange -------------------------------------------------------

def find(root, symbol, instrument, protocol_hash, today=None, minimum_tier=None, tier_of=None, pack=None):
    """The best usable evaluation of this subject that someone ELSE produced.

    Same gates as an office applies to its own research (protocol, freshness,
    intelligence level) plus one that only matters across offices:
    CORROBORATION. Where this office has just read the same public source, the
    content must match what the contributor read; a mismatch means the source
    moved or the record is wrong, and either way it is not reused. Returns
    (record, corroboration) or (None, None).
    """
    return select(records(root, symbol), instrument, protocol_hash, today=today,
                  minimum_tier=minimum_tier, tier_of=tier_of, pack=pack)


def select(candidates, instrument, protocol_hash, today=None, minimum_tier=None, tier_of=None, pack=None):
    today = today or datetime.now(timezone.utc).date()
    # Corroborate DOCUMENTS only. A price tape differs every time anyone reads it;
    # comparing it would make two offices disagree forever and quietly end all reuse.
    ours = {}
    for section, data in general_store.public_pack(pack)["sections"].items():
        if section in PUBLIC_SECTIONS:
            ours[section] = content_sha256(section, data)
    best = None
    for r in candidates:
        if r["subject"]["instrument"] != instrument or r["protocol_hash"] != protocol_hash:
            continue
        if not 0 <= (today - day(r["as_of"])).days <= general_store.MAX_AGE_DAYS:
            continue
        if minimum_tier is not None and tier_of is not None:
            produced = tier_of(r["models"]["adjudicate"])
            if produced is None or produced < minimum_tier:
                continue
        theirs = {e["section"]: e["content_sha256"] for e in r["evidence"]}
        shared = set(ours) & set(theirs)
        if any(ours[s] != theirs[s] for s in shared):
            continue                                   # we read the same source and it says something else
        state = {"matched_sections": sorted(shared),
                 "status": "corroborated" if shared else "uncorroborated"}
        rank = (bool(shared), day(r["as_of"]).toordinal(), r["id"])
        if best is None or rank > best[0]:
            best = (rank, r, state)
    return (best[1], best[2]) if best else (None, None)


def scoreboard(root, group_by="contributor"):
    from officekit_research.index import summarize
    from officekit_research.predictions import agent_identity
    if group_by not in {'contributor', 'submitter', 'agent', 'submitter_agent', 'adjudicate_model', 'protocol_hash', 'symbol'}:
        raise ValueError('Unsupported grouping')
    resolved = outcomes(root)
    rows = []
    for r in records(root):
        people = contributors(root, r['id']) or [{'contributor': None}]
        for i, f in enumerate(r['assessment']['forecasts']):
            fid = r['id'] + ':' + str(i)
            o = resolved.get(fid)
            for person in people:
                rows.append(dict(f, id=fid, as_of=r['as_of'], agent=agent_identity(r),
                                 contributor=person['contributor'], attribution=person.get('attribution', 'claimed') if person['contributor'] else 'anonymous',
                                 adjudicate_model=r['models']['adjudicate'], protocol_hash=r['protocol_hash'], symbol=r['subject']['symbol'],
                                 outcome=None if o is None else int(o['outcome']),
                                 resolved_at=None if o is None else o['resolved_on']))
    return summarize(rows, group_by)


# ---- git ------------------------------------------------------------------------

def _git(root, *args, check=True):
    env = {**os.environ, "GIT_AUTHOR_NAME": AUTHOR[0], "GIT_AUTHOR_EMAIL": AUTHOR[1],
           "GIT_COMMITTER_NAME": AUTHOR[0], "GIT_COMMITTER_EMAIL": AUTHOR[1]}
    return subprocess.run(["git", "-C", str(root), *args], env=env, check=check, capture_output=True, text=True)


def is_repository(root):
    return _git(root, "rev-parse", "--is-inside-work-tree", check=False).returncode == 0


def commit(root, paths, message, on=None):
    """Commit exactly these paths under the exchange's neutral identity.

    Pathspec-limited, so unrelated staged work in the same repository is never
    swept into a research commit. Returns the commit id, or None if nothing
    changed or the exchange is not a git repository (a plain folder is fine).
    """
    root = _root(root)
    if not paths or not is_repository(root):
        return None
    rel = [str(Path(p).resolve().relative_to(root)) for p in paths]
    _git(root, "add", "--", *rel)
    if _git(root, "diff", "--cached", "--quiet", "--", *rel, check=False).returncode == 0:
        return None
    stamp = (on or datetime.now(timezone.utc).date()).isoformat() + "T00:00:00+00:00"
    env_date = {"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp}
    env = {**os.environ, "GIT_AUTHOR_NAME": AUTHOR[0], "GIT_AUTHOR_EMAIL": AUTHOR[1],
           "GIT_COMMITTER_NAME": AUTHOR[0], "GIT_COMMITTER_EMAIL": AUTHOR[1], **env_date}
    subprocess.run(["git", "-C", str(root), "commit", "--no-gpg-sign", "-m", message, "--", *rel],
                   env=env, check=True, capture_output=True, text=True)
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def dedicated(root):
    """True when the exchange IS a repository, not a folder inside someone else's."""
    root = _root(root)
    top = _git(root, "rev-parse", "--show-toplevel", check=False)
    return top.returncode == 0 and Path(top.stdout.strip()).resolve() == root


def push(root):
    """Publish local exchange commits. Never called implicitly unless the office set auto_push."""
    root = _root(root)
    if not is_repository(root):
        raise ValueError("The exchange is not a git repository; there is nothing to push")
    done = _git(root, "push", check=False)
    if done.returncode:
        raise ValueError("The exchange could not be pushed: " + (done.stderr.strip().splitlines() or ["unknown error"])[-1][:300])
    return True


# ---- an office contributing -----------------------------------------------------

def local_root(answers):
    """The office's exchange directory, or None when there is none to use.

    A hosted office inherits `exchange` from the machine it migrated from; that
    path means nothing inside a hosted container, and writing research to it
    would be both useless and surprising. Hosted offices contribute through the
    authenticated central exchange instead.
    """
    chosen = settings(answers)
    if chosen["mode"] != "general" or not chosen["exchange"]:
        return None
    from officekit.runtime import hosted
    return None if hosted() else chosen["exchange"]


def submit(folder, record, answers, snapshot=None, today=None):
    """Auto-commit one general record from this office, if the office shares.

    Returns a small status dict and never raises into the research pipeline:
    failing to SHARE research must not fail the research. The tripwire is the
    exception to silence — it is reported loudly in the status.
    """
    try:
        chosen = settings(answers)
        if chosen["mode"] != "general" or not chosen["exchange"]:
            return {"shared": False, "reason": "Research sharing is off for this office"}
        if local_root(answers) is None:
            return {"shared": False, "reason": "Hosted offices contribute through the central exchange, not a local folder"}
        record = admit(record)
        tripwire(record, snapshot if snapshot is not None else {"answers": answers})
        key = contributor_key(answers)
        root = init(chosen["exchange"])
        from officekit_research.admission import local_review
        review = local_review(folder, record)
        if is_private(record):
            hold(root, record, key, review=review)
            return {"shared": True, "held": True, "record_id": record["id"], "contributor": key, "commit": None,
                    "pushed": False, "reason": "Private-deal research is held until you release it explicitly"}
        changed = write(root, record, key, "claimed", today, review=review)
        if changed:
            changed.append(root / "catalog.json")
            catalog(root)
        subject = record["subject"]["symbol"]
        sha = commit(root, changed, f"research: {subject} general evaluation {record['id'][:12]}\n\n"
                     f"standing: {record['assessment']['standing']} ({record['label']}, {record['tier']})\n"
                     f"adjudicated by: {record['models']['adjudicate']}\nprotocol: {record['protocol_hash'][:16]}\n"
                     f"contributor: {key or 'anonymous'}", today)
        # Public equities publish implicitly unless the office turned that off. A failed or
        # refused push is reported, never raised: the research and its commit already succeeded.
        pushed, push_note = False, None
        if sha and chosen["auto_push"]:
            if not dedicated(root):
                push_note = "Not pushed: the exchange is a folder inside a larger repository. Push it explicitly."
            else:
                try:
                    pushed = push(root)
                except ValueError as exc:
                    push_note = str(exc)
        elif sha:
            push_note = "Not pushed: this office turned implicit publishing off"
        return {"shared": True, "held": False, "record_id": record["id"], "contributor": key, "new": bool(changed),
                "commit": sha, "pushed": pushed, "push_note": push_note}
    except ValueError as exc:
        return {"shared": False, "reason": str(exc), "withheld": "private to this office" in str(exc)}
    except (OSError, subprocess.CalledProcessError) as exc:
        return {"shared": False, "reason": "The exchange could not be written: " + type(exc).__name__}


def main(argv=None):
    parser = argparse.ArgumentParser(description="The open research exchange. Nothing is pushed unless you run `push`.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (("init", "Create the exchange layout"), ("catalog", "Rebuild the derived catalog"),
                            ("push", "Publish local exchange commits"), ("scoreboard", "Calibration across the exchange")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("root", type=Path)
        if name == "scoreboard":
            p.add_argument("--by", default="contributor")
    enable = sub.add_parser("enable", help="Turn on general-research sharing for an office")
    enable.add_argument("--office", required=True, type=Path)
    enable.add_argument("--exchange", required=True, type=Path)
    enable.add_argument("--anonymous", action="store_true")
    enable.add_argument("--pseudonymous", action="store_true", help="Opt in to a linkable public research history")
    enable.add_argument("--no-push", action="store_true", help="Commit public-equity research locally but do not publish it implicitly")
    rel = sub.add_parser("release", help="EXPLICITLY admit one held private-deal record to the shared corpus")
    rel.add_argument("root", type=Path)
    rel.add_argument("record_id")
    rel.add_argument("--push", action="store_true", help="Also publish it now")
    waiting = sub.add_parser("held", help="List private-deal research waiting for an explicit release")
    waiting.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    if args.command == "release":
        print(json.dumps(release(args.root, args.record_id, publish=args.push), indent=2))
    elif args.command == "held":
        print(json.dumps([{"id": h["record"]["id"], "subject": h["record"]["subject"], "as_of": h["record"]["as_of"]}
                          for h in held(args.root)], indent=2))
    elif args.command == "init":
        print(init(args.root))
    elif args.command == "catalog":
        print(json.dumps({"records": catalog(args.root)["records"]}))
    elif args.command == "push":
        push(args.root)
        print("Pushed.")
    elif args.command == "scoreboard":
        print(json.dumps(scoreboard(args.root, args.by), indent=2))
    else:
        from officekit.office_lock import locked
        with locked(args.office):
            path = args.office / "answers.json"
            answers = json.loads(path.read_text(encoding="utf-8"))
            answers["research_sharing"] = {**(answers.get("research_sharing") or {}), "mode": "general",
                                           "exchange": str(args.exchange.expanduser().resolve()),
                                           "contributor": "pseudonymous" if args.pseudonymous and not args.anonymous else "anonymous",
                                           "auto_push": not args.no_push}
            settings(answers)
            path.write_text(json.dumps(answers, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print("Sharing general research as " + (contributor_key(answers) or "anonymous") + ". Public-equity research is "
              + ("committed locally only." if args.no_push else "published implicitly.")
              + " Private-deal research is held for explicit release. Contextual cases are never auto-shared.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
