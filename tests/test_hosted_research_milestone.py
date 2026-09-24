"""Two offices through the hosted API and Git release, with synthetic models.

This proves transport/reuse/isolation mechanics, never recommendation quality.
The evidence-only arm has no donor court reuse, isolating source-cache savings.
"""
import copy
import json
import os
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient
from hosting.app.main import create_app
from hosting.app.exchange import Exchange
from hosting.gcp.export_exchange import export
from officekit import strategy_proposals as jobs
from officekit_ai.strategy_proposal import build_proposal
from officekit_research import general, index, cases
from officekit_research.hosted import Client
from officekit_research.evaluate import metrics
from research_admission_fixtures import fixture_reviewer
from test_hosted_migration import MemoryStore, Backend, ORIGIN
from test_officekit_strategy_proposals import Provider, clients
from test_contextual_research import proposal, context, sources, shared


def test_two_office_hosted_milestone(tmp_path, monkeypatch):
    counts = sources(monkeypatch)
    donor = tmp_path / "donor"
    _, p = proposal(donor)
    key = "d" * 32  # explicit attribution opt-in in this test, not the default
    p["snapshot"]["answers"]["research_sharing"] = {"mode": "general"}
    jobs.save(donor, p)
    # The publisher loads its independently controlled frozen source. It never
    # reads an evidence snapshot supplied in the contribution request.
    import officekit_research as research
    publisher_pack = {"symbol": "VDC", "built": cases.utcnow(), "errors": [],
                      "sections": {name: research.SOURCES[name]("VDC", {}) for name in ("fund_profile", "tape")}}
    store = MemoryStore()
    service = Exchange(store, evidence_loader=lambda record: publisher_pack, reviewer=fixture_reviewer)
    with TestClient(create_app(Backend(), ORIGIN, store=store, exchange=service), base_url=ORIGIN) as http:
        donor_client = Client(http, "alice")
        provider = Provider()
        jobs.run(donor, p["id"], lambda r, d, save: build_proposal(r, d, save, clients(provider), exchange_client=donor_client))
        p = jobs.load(donor, p["id"])
        assert p["status"] in {"ready", "needs_review"}, p["errors"]
        original = p["general"]["VDC"]["record"]
        assert p["general"]["VDC"]["shared"]["shared"]
        assert len(provider.calls) == 7
        donor_client.submit(original, key)
        bundle = shared(p)
        results = {}
        for arm, reuse, contextual, general_reuse in (
                ("baseline", False, False, False), ("evidence_only", True, False, False), ("contextual", True, True, True)):
            folder = tmp_path / arm
            _, q = proposal(folder, context(life_stage="decumulating", liquidity="ongoing_spending"))
            q["snapshot"]["answers"]["research_sharing"] = {"mode": "general"}
            jobs.save(folder, q)
            before = copy.deepcopy(q["snapshot"])
            if reuse:
                cases.import_bundle(folder, bundle)
            recipient_model = Provider(verdict="WATCH")  # a distinct suitability judgment
            start = dict(counts)
            jobs.run(folder, q["id"], lambda r, d, save: build_proposal(r, d, save, clients(recipient_model),
                reuse=reuse, contextual_reuse=contextual, general_reuse=general_reuse,
                exchange_client=Client(http, "bob") if arm == "contextual" else None))
            q = jobs.load(folder, q["id"])
            assert q["status"] in {"ready", "needs_review"}, q["errors"]
            assert q["snapshot"] == before
            assert q["courts"][0]["id"] != p["courts"][0]["id"]
            assert q["basket"][0]["amount"] == 0
            assert len(recipient_model.calls) == (4 if arm == "contextual" else 7)
            if arm == "contextual":
                assert q["general"]["VDC"]["source"] == "hosted exchange"
                assert q["courts"][0]["general_id"] == original["id"]
                row = index.query(folder, kind="general")[0]
                assert row["origin"] == "imported" and row["contributor"] != "self"
                assert key in {item["contributor"] for item in row["contributors"]}
            if arm == "evidence_only":
                assert not q["general"]["VDC"]["reused"]
            results[arm] = {**metrics(q), "source_acquisitions": {k: counts[k]-start[k] for k in counts},
                            "fixture_model_calls": len(recipient_model.calls)}
        assert results["baseline"]["source_acquisitions"] == {"fund_profile": 1, "tape": 1, "book": 1}
        assert results["evidence_only"]["source_acquisitions"] == {"fund_profile": 0, "tape": 1, "book": 1}
        assert results["contextual"]["source_acquisitions"] == {"fund_profile": 0, "tape": 1, "book": 1}

    repo = tmp_path / "worker-placement-library"
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    released = export(store, repo / "research_exchange")
    assert released["commit"] and released["skipped"] == 0
    assert export(store, repo / "research_exchange")["commit"] is None
    public_diff = subprocess.run(["git", "-C", str(repo), "show", "HEAD"], check=True, capture_output=True, text=True).stdout
    assert "PRIVATE OWNER SENTINEL" not in public_diff and '"tenant"' not in public_diff
    assert len(list((repo / "research_exchange/general").glob("*/*.json"))) == 1
    report = {"status": "contract_passed_live_quality_pending", "population": "synthetic provider and reviewer fixtures",
              "transport": "actual hosted FastAPI routes, isolated test store and test identities",
              "publication": "one idempotent commit in an isolated worker-placement library; no remote push",
              "arms": results, "quality_audit": "not_assessed", "live_usage_and_cost": "not_measured"}
    if os.environ.get("RESEARCH_MILESTONE_REPORT"):
        Path(os.environ["RESEARCH_MILESTONE_REPORT"]).write_text(json.dumps(report, indent=2) + "\n")
