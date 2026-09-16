"""Commitment HTTP actions, kept separate from the app's general goal intake."""
import json
import uuid
from datetime import datetime, timedelta, timezone

from officekit.commitments import (add_commitment, apply_edit, edit_values, revision,
                                   validate_patch)
from officekit.intake import build_from_answers

PREVIEW_TTL = timedelta(hours=24)
APPLIED_PREVIEW_TTL = timedelta(days=7)
MAX_PREVIEWS = 100


def _preview_time(record, field, fallback):
    try:
        timestamp = datetime.fromisoformat(record[field])
        return timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp
    except (KeyError, TypeError, ValueError):
        return fallback


def prune_previews(folder, now=None, directory="commitment_previews"):
    """Bound disposable proposals; the durable before/after history is retained."""
    now = now or datetime.now(timezone.utc)
    survivors = []
    for path in (folder / directory).glob("*.json"):
        try:
            uuid.UUID(path.stem)  # only our token files, never neighboring documents
            modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            try:
                record = json.loads(path.read_text())
                if not isinstance(record, dict):
                    record = {}
            except (ValueError, OSError):
                record = {}
            applied = bool(record.get("applied_at"))
            timestamp = _preview_time(record, "applied_at" if applied else "created_at", modified)
            ttl = APPLIED_PREVIEW_TTL if applied else PREVIEW_TTL
            if now - timestamp >= ttl:
                path.unlink(missing_ok=True)
            else:
                survivors.append((timestamp, path))
        except (ValueError, OSError):
            continue
    for _, path in sorted(survivors)[:max(0, len(survivors) - MAX_PREVIEWS)]:
        path.unlink(missing_ok=True)


def handle(path, form, folder, build, ai_available=False):
    def get(key):
        return (form.getvalue(key) or "").strip()

    prune_previews(folder)
    answers = json.loads((folder / "answers.json").read_text())
    expected = get("revision")
    cid = get("cid")
    if path == "/commitments/apply":
        token = str(uuid.UUID(get("token")))
        try:
            proposal = json.loads((folder / "commitment_previews" / f"{token}.json").read_text())
        except FileNotFoundError:
            raise ValueError("This preview has expired or is no longer available. Create a fresh preview.") from None
        if proposal.get("applied_at"):
            raise ValueError("These changes were already applied. Reload to review the current office.")
        cid, expected, patch = proposal["cid"], proposal["revision"], proposal["patch"]
    else:
        keys = ("source", "label", "amount", "annual_amount", "rate_pct", "term_years", "home_value",
                "funding_source", "cadence", "next_due", "ends_on", "settled")
        patch = {k: get(k) for k in keys if get(k)}
    if expected != revision(answers):
        raise ValueError("The office changed since this page was loaded. Reload and review the latest values.")
    # Derive from a copy: read-only previews must not mint new persisted facts.
    data = build_from_answers(json.loads(json.dumps(answers)))
    before = next((c for c in data["commitments"] if c["id"] == cid), None)
    if path == "/commitments/preview":
        if before is None:
            raise ValueError("This commitment no longer exists")
        if not ai_available:
            raise ValueError("AI is not configured. You can edit these details directly.")
        instruction = get("instruction")
        if not instruction or len(instruction) > 8000:
            raise ValueError("Describe the change in 1–8000 characters")
        from officekit_ai.commitment_edit import propose
        from officekit.render_capital import render_preview
        result = propose(before, instruction, folder=folder)
        if not result.get("patch"):
            raise ValueError(result.get("note") or "No specific change was proposed")
        patch = validate_patch(before, result["patch"])
        # Validate the entire candidate before offering an Apply button.
        candidate = apply_edit(answers, cid, patch, expected)
        build_from_answers(candidate)
        token = str(uuid.uuid4())
        previews = folder / "commitment_previews"
        previews.mkdir(exist_ok=True)
        (previews / f"{token}.json").write_text(json.dumps({"cid": cid, "revision": expected,
            "patch": patch, "before": edit_values(before), "model": result.get("model"),
            "note": result.get("note"), "created_at": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n")
        prune_previews(folder)
        return {"html": render_preview(before, patch, token, result.get("note", ""))}
    if path == "/commitments/add":
        updated = add_commitment(answers, patch, expected)
        cid = updated["commitments"][-1]["id"]
    else:
        updated = apply_edit(answers, cid, patch, expected)
    built = build(updated, folder)
    if path == "/commitments/apply":
        proposal["applied_at"] = datetime.now(timezone.utc).isoformat()
        (folder / "commitment_previews" / f"{token}.json").write_text(json.dumps(proposal, indent=2) + "\n")
    after = next((c for c in built["commitments"] if c["id"] == cid), None)
    with (folder / "commitment_history.jsonl").open("a") as ledger:
        ledger.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(), "id": cid,
            "proposal_id": token if path == "/commitments/apply" else None,
            "action": path.rsplit("/", 1)[-1], "before_revision": expected, "after_revision": revision(updated),
            "before": before, "after": after}, ensure_ascii=False) + "\n")
    page = "/pages/office.html" if get("back") == "office" else "/pages/capital.html"
    from urllib.parse import quote
    return {"redirect": page + "#" + quote(cid, safe=":-")}
