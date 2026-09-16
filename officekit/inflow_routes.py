"""Revision-checked receipt previews; apply publishes facts and audit together."""
import json
import uuid
from datetime import datetime, timezone

from officekit.commitments import revision
from officekit.commitment_routes import prune_previews
from officekit.inflows import propose
from officekit.render_inflows import render_receipt_preview


def handle(path, form, folder, build, model_for_answers):
    def get(key):
        return (form.getvalue(key) or "").strip()
    prune_previews(folder, directory="inflow_previews")
    answers = json.loads((folder / "answers.json").read_text())
    previews = folder / "inflow_previews"
    if path == "/inflows/preview":
        fields = {k: get(k) for k in ("inflow_id", "action", "gross", "withheld", "date", "account_id",
                                      "included", "reference", "receipt_id", "reason")}
        token = str(uuid.uuid4())
        updated = propose(answers, fields, get("revision"), event_id=token)
        before = model_for_answers(answers, folder)
        after = model_for_answers(updated, folder)
        html = render_receipt_preview(before, after, updated["inflow_events"][-1], token)
        previews.mkdir(exist_ok=True)
        (previews / f"{token}.json").write_text(json.dumps({"fields": fields, "revision": get("revision"),
            "model_revision": revision(before["d"]),
            "created_at": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n")
        prune_previews(folder, directory="inflow_previews")
        return {"html": html}
    token = str(uuid.UUID(get("token")))
    # The durable event, not a disposable preview stamp, is the replay guard.
    if any(e["id"] == token for e in answers.get("inflow_events", [])):
        return {"redirect": "/pages/capital.html#inflows"}
    try:
        proposal = json.loads((previews / f"{token}.json").read_text())
    except FileNotFoundError:
        raise ValueError("This preview expired or is no longer available. Review the receipt again.") from None
    updated = propose(answers, proposal["fields"], proposal["revision"], event_id=token)
    if revision(model_for_answers(answers, folder)["d"]) != proposal["model_revision"]:
        raise ValueError("The account sources or tax model changed. Review the receipt again.")
    build(updated, folder)
    proposal["applied_at"] = datetime.now(timezone.utc).isoformat()
    (previews / f"{token}.json").write_text(json.dumps(proposal, indent=2) + "\n")
    return {"redirect": "/pages/capital.html#inflows"}
