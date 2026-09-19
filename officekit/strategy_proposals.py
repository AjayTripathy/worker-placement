"""Durable proposal jobs, snapshots and review state for all creation doors."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import threading
import uuid
from officekit.office_lock import locked, transaction
from concurrent.futures import ThreadPoolExecutor

_LOCK = threading.RLock()
_RUNNING = set()
_QUEUED = set()
_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="strategy-proposal")


def now():
    return datetime.now(timezone.utc).isoformat()


def error_message(error):
    from officekit.api_errors import message
    return message(error)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def path(folder, pid):
    return Path(folder) / "strategy_proposals" / (str(uuid.UUID(pid)) + ".json")


def load(folder, pid):
    return json.loads(path(folder, pid).read_text())


def list_proposals(folder):
    records = []
    for p in (Path(folder) / "strategy_proposals").glob("*.json"):
        try:
            records.append(load(folder, p.stem))
        except (ValueError, OSError):
            continue
    return sorted(records, key=lambda p: p["created_at"], reverse=True)


def recover_interrupted(folder):
    """A restart never silently re-bills research; retain checkpoints for Retry."""
    with locked(folder), _LOCK:
        for p in list_proposals(folder):
            key = (str(Path(folder).resolve()), p["id"])
            if p["status"] in {"queued", "running"} and key not in _RUNNING | _QUEUED:
                p.update(status="error", stage="Review interrupted", errors=p["errors"] + ["The server restarted during this review. Resume to use the saved checkpoints."])
                save(folder, p)


@transaction()
def save(folder, proposal):
    from officekit.render_proposal import render_proposal
    p = path(folder, proposal["id"])
    p.parent.mkdir(parents=True, exist_ok=True)
    pages = Path(folder) / "pages"
    pages.mkdir(exist_ok=True)
    proposal["updated_at"] = now()
    # Per-job lock is held by callers. Replace complete files, never truncate a
    # record while a browser reloads the progress page.
    temp = p.with_suffix(".tmp")
    temp.write_text(json.dumps(proposal, indent=2, ensure_ascii=False) + "\n")
    temp.replace(p)
    if proposal.get("research"):
        from officekit_research.cases import capture_private
        capture_private(folder, proposal)
    page = pages / f'proposal_{proposal["id"]}.html'
    temp = page.with_suffix(".tmp")
    temp.write_text(render_proposal(proposal))
    temp.replace(page)


def create(folder, answers, model, strategy_id, source, ref, *, option=None, title=None, request="", target_pct=None, revision_of=None, research_context=None):
    from officekit.strategy_playbooks import brief
    from officekit.personal_context import load as load_context
    pc = load_context(folder)
    if not isinstance(title or strategy_id, str) or len(title or strategy_id) > 180 or len(request) > 8000:
        raise ValueError("Use a title up to 180 characters and a request up to 8,000 characters")
    from officekit.mandates import validate_target_pct
    target_pct = validate_target_pct(target_pct)
    if research_context is not None:
        from officekit_research.cases import validate_context
        validate_context(research_context)
    key = digest([strategy_id, source, ref, option, title, request, target_pct] + ([research_context] if research_context is not None else []))
    with locked(folder), _LOCK:
        old = next((p for p in list_proposals(folder) if p["request_key"] == key and p["status"] not in {"declined", "superseded"}), None)
        if revision_of:
            old = None
        if old:
            return old
        pid = str(uuid.uuid4())
        dec = answers.setdefault("strategy_decisions", {}).setdefault(strategy_id, {})
        dec.setdefault("status", "considering")
        origins = dec.setdefault("origins", [])
        if not any(o.get("source") == source and o.get("ref") == ref for o in origins):
            origins.append({"source": source, "ref": ref, "date": now()[:10]})
        if title:
            dec.setdefault("title", title)
        dec.setdefault("proposal_ids", []).append(pid)
        proposal = {"id": pid, "v": 1, "strategy_id": strategy_id, "source": source, "source_ref": ref,
                    "request_key": key, "created_at": now(), "status": "queued", "stage": "Research queued",
                    "brief": brief(strategy_id, option, title, request), "target_pct": target_pct,
                    "snapshot": {"answers": deepcopy(answers), "data": deepcopy(model["d"]), "personal_context": deepcopy(pc)},
                    "snapshot_revision": digest(answers), "history": [{"at": now(), "stage": "Proposal created"}],
                    "research": None, "candidates": [], "courts": [], "risk": None, "pitch": None,
                    "errors": [], "basket": []}
        proposal["revision_of"] = revision_of
        if research_context is not None:
            proposal["research_context"] = deepcopy(research_context)
        save(folder, proposal)
        return proposal


def run(folder, pid, pipeline=None):
    from officekit.api_errors import report, clear
    key = (str(Path(folder).resolve()), pid)
    with locked(folder), _LOCK:
        if key in _RUNNING:
            return
        p = load(folder, pid)
        _QUEUED.discard(key)
        if p["status"] in {"ready", "needs_review", "adopted", "declined", "superseded"}:
            return
        _RUNNING.add(key)
        clear(folder, context='proposal:' + pid)
        p.update(status="running", stage="Research")
        save(folder, p)
    def checkpoint(stage, **fields):
        with locked(folder), _LOCK:
            p.update(fields, stage=stage)
            p["history"].append({"at": now(), "stage": stage})
            save(folder, p)
        from officekit.runtime import checkpoint as persist_checkpoint
        persist_checkpoint()
    try:
        if pipeline is None:
            from officekit_ai.strategy_proposal import build_proposal
            pipeline = build_proposal
        pipeline(p, folder, checkpoint)
    except Exception as e:
        checkpoint("Needs attention", status="error", errors=p["errors"] + [error_message(e)])
        report(folder, 'proposal:' + pid, 'Strategy review failed', e,
               href=f'/pages/proposal_{pid}.html')
    finally:
        with locked(folder), _LOCK:
            _RUNNING.discard(key)


def dispatch(folder, pid):
    """Serialize expensive jobs; repeated submits never multiply court work."""
    key = (str(Path(folder).resolve()), pid)
    with locked(folder), _LOCK:
        if key in _RUNNING or key in _QUEUED:
            return
        if len(_QUEUED) >= 16:
            p = load(folder, pid)
            p.update(status="error", stage="Queue full", errors=["Proposal queue is full. Retry after another review finishes."])
            save(folder, p)
            from officekit.api_errors import report
            report(folder, 'proposal:' + pid, 'Strategy review queue is full',
                   ValueError(p['errors'][0]), href=f'/pages/proposal_{pid}.html')
            return
        _QUEUED.add(key)
        _EXECUTOR.submit(run, Path(folder), pid)


def retry(folder, pid):
    with locked(folder), _LOCK:
        p = load(folder, pid)
        if (str(Path(folder).resolve()), pid) in _RUNNING | _QUEUED:
            return p
        if p["status"] not in {"error", "queued", "running", "awaiting_key"}:
            raise ValueError("This proposal has finished; create a revision to change the thesis")
        p.update(status="queued", stage="Retry queued")
        save(folder, p)
        return p


def bind_snapshot(folder, p, answers, model):
    """Bind after build_office has registered implicit mandates and saved facts."""
    with locked(folder), _LOCK:
        if p["status"] != "queued" or p.get("research"):
            return
        p["snapshot"]["answers"] = deepcopy(answers)
        p["snapshot"]["data"] = deepcopy(model["d"])
        p["snapshot_revision"] = digest(answers)
        save(folder, p)


def decide(folder, answers, pid, action, model=None):
    with locked(folder), _LOCK:
        p = load(folder, pid)
        if action not in {"adopt", "decline"} or p["status"] not in {"ready", "needs_review"}:
            raise ValueError("Complete the proposal review before recording a decision")
        if action == "adopt" and digest(answers) != p["snapshot_revision"]:
            raise ValueError("The office changed during research. Revise the proposal against current balances before adopting.")
        if action == "adopt":
            from officekit.personal_context import load as load_context
            if digest(load_context(folder)) != digest(p["snapshot"]["personal_context"]) or (model is not None and digest(model["d"]) != digest(p["snapshot"]["data"])):
                raise ValueError("Portfolio evidence or constraints changed. Revise this proposal before adopting.")
        updated = deepcopy(answers)
        dec = updated.setdefault("strategy_decisions", {}).setdefault(p["strategy_id"], {})
        if action == "adopt":
            if dec.get("status") != "implemented":
                dec["status"] = "planned"
            dec["adopted_proposal_id"] = pid
        elif dec.get("status") not in {"implemented", "planned"}:
            other = any(q["strategy_id"] == p["strategy_id"] and q["id"] != pid and
                        q["status"] not in {"declined", "superseded"} for q in list_proposals(folder))
            dec["status"] = "considering" if other else "declined"
        dec["proposal_decision"] = {"id": pid, "action": action, "at": now()}
        # A court/Risk Officer advises. Human adoption records intent, never a
        # purchase or a cash reservation; unresolved items remain on the deck.
        return updated, p
