"""Independent, opt-in morning research worker; no broker imports or orders.

python -m desk.odte.forecast_worker --init --office ~/office --submitter local-office
python -m desk.odte.forecast_worker --once
python -m desk.odte.forecast_worker --daemon
python -m desk.odte.forecast_worker --report
"""
from __future__ import annotations

import argparse
import datetime as dt
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as XML

from desk.odte import doctrine as D, text_overlay as E
from desk.odte.storage import atomic_json

S = {"type": "string"}
TAGS = {
    "event_type": ["monetary", "fiscal", "auction", "geopolitical", "earnings", "rebalance", "liquidity", "other"],
    "novelty": ["scheduled", "new_information", "confirmation", "rumor", "correction", "unknown"],
    "timing": ["before_entry", "holding_window", "after_exit", "unknown"],
    "channel": ["rates", "growth", "liquidity", "uncertainty", "positioning", "other"],
    "expected_volatility": ["up", "down", "mixed", "unknown"],
}
REASON_FIELDS = ["source_id", "quote", "mechanism", "falsifier", *TAGS]
SCHEMA = {"type": "object", "properties": {
    "stop_probability": {"type": "number"}, "severe_probability": {"type": "number"},
    "incremental_information": S, "gaps": {"type": "array", "items": S},
    "reasons": {"type": "array", "items": {"type": "object", "properties": {
        "source_id": S, "quote": S, "mechanism": S, "falsifier": S,
        **{name: {"type": "string", "enum": options} for name, options in TAGS.items()}},
        "required": REASON_FIELDS, "additionalProperties": False}}},
    "required": ["stop_probability", "severe_probability", "incremental_information", "gaps", "reasons"],
    "additionalProperties": False}


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def collect(m, *, clock=E.utcnow, opener=urllib.request.urlopen):
    """Snapshot public feed excerpts, never follow article links or ingest a book."""
    sources, gaps = [], []
    for url in m["sources"]:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "WorkerPlacement-ODTE-Research/1"})
            with opener(request, timeout=12) as response:
                if urllib.parse.urlsplit(response.url).hostname != urllib.parse.urlsplit(url).hostname:
                    raise ValueError("cross-publisher redirect")
                raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise ValueError("feed size limit")
            fetched = clock()
            tree = XML.fromstring(raw)
            for item in tree.findall(".//item")[:40]:
                published = parsedate_to_datetime(item.findtext("pubDate") or "")
                if published.tzinfo is None or not 0 <= (fetched - published).total_seconds() <= m["source_max_age_hours"] * 3600:
                    continue
                parser = PlainText(); parser.feed((item.findtext("title") or "") + "\n" + (item.findtext("description") or ""))
                text = " ".join(" ".join(parser.parts).split())[:2400]
                if not text:
                    continue
                source = {"feed": url, "url": item.findtext("link") or url, "text": text,
                          "published_at": published.isoformat(), "fetched_at": fetched.isoformat(),
                          "visibility": "public_feed_excerpt"}
                source["id"] = E.digest(source)
                sources.append(source)
        except Exception as exc:
            gaps.append({"source": url, "error": type(exc).__name__})
    return sources, gaps


def validate_sources(sources, m, cutoff):
    if len({s["feed"] for s in sources}) < m["min_sources"]:
        raise ValueError("insufficient registered feed coverage")
    for s in sources:
        if s["id"] != E.digest({k: v for k, v in s.items() if k != "id"}) or s["feed"] not in m["sources"]:
            raise ValueError("unregistered source or evidence digest mismatch")
        published, fetched = E.timestamp(s["published_at"]), E.timestamp(s["fetched_at"])
        if not published <= fetched <= cutoff or (cutoff - published).total_seconds() > m["source_max_age_hours"] * 3600:
            raise ValueError("evidence is stale, future-dated or was fetched after the cutoff")
        if s["visibility"] != "public_feed_excerpt" or not s["text"].strip():
            raise ValueError("evidence is not eligible public text")


def validate_forecast(out, sources):
    if set(out) != set(SCHEMA["required"]):
        raise ValueError("invalid forecast fields")
    for k in ("stop_probability", "severe_probability"):
        if type(out[k]) not in (int, float) or not 0 <= out[k] <= 1:
            raise ValueError("invalid probability")
    if not isinstance(out["incremental_information"], str) or not out["incremental_information"].strip():
        raise ValueError("missing incremental-information explanation")
    if not isinstance(out["gaps"], list) or any(not isinstance(g, str) for g in out["gaps"]):
        raise ValueError("invalid coverage gaps")
    if not isinstance(out["reasons"], list) or not 1 <= len(out["reasons"]) <= 3:
        raise ValueError("supply 1-3 supported reasons")
    by_id = {s["id"]: s for s in sources}
    for reason in out["reasons"]:
        if not isinstance(reason, dict) or set(reason) != set(REASON_FIELDS):
            raise ValueError("invalid reason fields")
        if any(reason[k] not in options for k, options in TAGS.items()):
            raise ValueError("invalid event taxonomy")
        if any(not isinstance(reason[k], str) or not reason[k].strip() for k in ("mechanism", "falsifier")):
            raise ValueError("missing mechanism or falsifier")
        source = by_id.get(reason.get("source_id"))
        quote = reason.get("quote")
        if source is None or not isinstance(quote, str) or not quote.strip() or quote not in source["text"] or not reason.get("mechanism"):
            raise ValueError("citation is absent from the frozen evidence")


def prepare_premarket(root, *, now=None):
    """Seal a pre-open request using only already-captured, explicitly dated context.

    No broker connection, fresh quote claim, retrospective fill, or model call.
    Missing prior data is an explicit gap and never silently fabricated.
    """
    from desk.odte import calendar, volatility
    from desk.odte.templates import build_condor
    root = Path(root); m = E.protocol(root); now = (now or E.utcnow()).astimezone(E.ET)
    date = now.date().isoformat(); hm = now.strftime("%H:%M:%S")
    if not m or m.get("forecast_mode") != "premarket":
        raise ValueError("Register a premarket experiment first")
    if m.get("session_date") and date != m["session_date"]:
        raise ValueError("Not the registered forecast date")
    if not m["request_window_et"][0] <= hm <= m["request_window_et"][1] or E.timestamp(m["registered_at"]) >= now:
        raise ValueError("Outside the prospective premarket preparation window")
    snapshot = None
    for file in sorted(D.CHAINS.glob("*.jsonl"), reverse=True):
        if file.stem >= date:
            continue
        if (now.date() - dt.date.fromisoformat(file.stem)).days > 4:
            break
        # Prior-day captures are complete files; malformed files fail visibly.
        rows = [json.loads(line) for line in file.read_text().splitlines() if line.strip()]
        eligible = [r for r in rows if E.timestamp(r["ts"]) < now and r.get("indices_live")]
        if eligible:
            snapshot = max(eligible, key=lambda r: E.timestamp(r["ts"]))
            break
    candidate = build_condor([r for r in (snapshot or {}).get("rows", []) if r.get("live_eligible")],
                            D.SHORT_DELTA, D.WING_WIDTH) if snapshot else None
    cal = calendar.load()
    job = {"date": date, "protocol": m["protocol"], "created_at": now.isoformat(), "snapshot": snapshot,
           "opening": {}, "market_features": volatility.values(snapshot, []) if snapshot else {},
           "indicative_candidate": candidate, "calendar": cal,
           "event_kinds": [e["kind"] for e in cal.get("events", []) if e.get("date") == date],
           "market_context": {"as_of": snapshot["ts"] if snapshot else None,
               "kind": "prior_session_only" if snapshot else "unavailable",
               "gaps": ["Today's opening range, live chain and dealer positioning are not observed premarket.",
                        "Calendar coverage is incomplete outside its declared events."]}}
    with E.locked(root):
        E.seal(root / "jobs" / (date + ".json"), job)
    return job


def run_job(root, date, *, client=None, collector=None, clock=E.utcnow):
    root = Path(root); m = E.protocol(root)
    if m is None:
        raise ValueError("Register the experiment first")
    job = E.read(root / "jobs" / (date + ".json"))
    deadline = dt.datetime.combine(dt.date.fromisoformat(date), dt.time.fromisoformat(m["forecast_deadline_et"]), E.ET)
    now = clock()
    if now.astimezone(E.ET).date().isoformat() != date or now >= deadline:
        raise ValueError("Forecast window closed; retrospective runs cannot enter this experiment")
    if m.get("session_date") and date != m["session_date"]:
        raise ValueError("Not the registered forecast date")
    if job["protocol"] != m["protocol"] or E.timestamp(job["created_at"]) > now:
        raise ValueError("Invalid job protocol/time")
    record = {"date": date, "protocol": m["protocol"], "submitter": m["submitter"], "agent": m["agent"],
              "requested_model": m["requested_model"], "resolved_model": "unknown", "provider": m["provider"],
              "intelligence_level": m["provider_settings"].get("reasoning_effort", "provider_default"),
              "started_at": now.isoformat(), "job_digest": E.digest(job), "forecast": None,
              "status": "running", "usage": None, "measured_cost_usd": None}
    with E.locked(root):
        E.seal(root / "attempts" / (date + ".json"), record)
    stage = "collect_evidence"
    try:
        sources, gaps = (collector or collect)(m)
        cutoff = clock()
        stage = "validate_evidence"
        validate_sources(sources, m, cutoff)
        corpus = {"sources": sources, "coverage_gaps": gaps, "cutoff": cutoff.isoformat(), "protocol": m["protocol"]}
        with E.locked(root):
            E.seal(root / "corpora" / (date + ".json"), corpus)
        record["corpus_digest"] = E.digest(corpus)
        if cutoff >= deadline:
            raise ValueError("collection exceeded forecast deadline")
        stage = "initialize_provider"
        if client is None:
            from officekit_ai.models import provider_client
            client = provider_client(m["provider"], m["provider_settings"])
        from officekit_ai.intelligence import generate
        payload = {"target": m["target"], "rules": m["templates"]["T3_BLACKOUT"],
                   "morning_market": job["snapshot"], "opening": job["opening"],
                   "market_features": job["market_features"], "indicative_candidate": job["indicative_candidate"],
                   "market_context": job.get("market_context", {"kind": "today_morning_snapshot"}),
                   "structured_calendar": job["calendar"], "evidence": corpus,
                   "note": "Forecast future T3 entry policy, not a trade already entered. No forward data."}
        stage = "model_call"
        reply = generate(client, model=m["requested_model"], max_tokens=3200, system=m["prompt"],
                         messages=[{"role": "user", "content": json.dumps(payload)}],
                         output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
                         timeout=max(1, min(240, (deadline - clock()).total_seconds())))
        record.update(resolved_model=reply.model, usage={k: getattr(reply.usage, k, None) for k in
                      ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")}
                      if reply.usage is not None else None)
        record["response_text"] = "".join(b.text for b in reply.content if b.type == "text")
        stage = "validate_forecast"
        if reply.stop_reason != "end_turn":
            raise ValueError("model response incomplete")
        out = json.loads(record["response_text"])
        validate_forecast(out, sources)
        record.update(forecast=out, status="accepted")
    except Exception as exc:
        # No provider diagnostics or credentials persisted; error class and safe stage are enough.
        record.update(status="failed", error_type=type(exc).__name__, failed_stage=stage,
                      error=f"{stage} failed; no decision admitted")
    issued = clock()
    if issued >= deadline:
        record.update(status="late", error="forecast completed after the frozen deadline")
    record["issued_at"] = issued.isoformat()
    record["id"] = E.digest(record)
    with E.locked(root):
        E.seal(root / "forecasts" / (date + ".json"), record)
    return record


def once(root):
    root = Path(root); now = E.utcnow(); date = now.astimezone(E.ET).date().isoformat()
    if not (root / "jobs" / (date + ".json")).exists():
        return {"status": "waiting_for_morning_snapshot"}
    if (root / "forecasts" / (date + ".json")).exists():
        return E.read(root / "forecasts" / (date + ".json"))
    if (root / "attempts" / (date + ".json")).exists():
        return {"status": "incomplete_attempt", "error": "attempt already reserved; not rerunning or selecting another answer"}
    return run_job(root, date)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=D.DATA / "text_overlay")
    parser.add_argument("--office", type=Path, default=Path.home() / "office")
    parser.add_argument("--submitter", default="local-office")
    parser.add_argument("--premarket", action="store_true", help="Freeze an 08:45 request / 09:15 deadline at registration")
    parser.add_argument("--session-date", help="Optional single-session experiment, YYYY-MM-DD")
    action = parser.add_mutually_exclusive_group(required=True)
    for flag in ("init", "prepare", "once", "daemon", "report"):
        action.add_argument("--" + flag, action="store_true")
    args = parser.parse_args()
    if args.init:
        m = E.initialize(args.root, args.office, args.submitter, premarket=args.premarket, session_date=args.session_date)
        print(json.dumps({"status": "registered", "protocol": m["protocol"], "provider": m["provider"], "model": m["requested_model"]}))
    elif args.prepare:
        job = prepare_premarket(args.root)
        print(json.dumps({"status": "prepared", "date": job["date"], "market_context": job["market_context"]}))
    elif args.report:
        from desk.odte.shadow import read_ledger
        print(json.dumps(E.report(args.root, shadow_rows=read_ledger()), indent=2))
    elif args.once:
        result = once(args.root)
        print(json.dumps({k: result.get(k) for k in ("status", "error", "id")}))
        if result["status"] in {"failed", "late", "incomplete_attempt"}:
            raise SystemExit(1)
    else:
        while True:
            try:
                result = once(args.root)
                atomic_json(args.root / "worker_status.json", {"checked_at": E.utcnow().isoformat(), "status": result["status"]})
            except Exception as exc:
                atomic_json(args.root / "worker_status.json", {"checked_at": E.utcnow().isoformat(), "status": "error", "error_type": type(exc).__name__})
            time.sleep(15)


if __name__ == "__main__":
    main()
