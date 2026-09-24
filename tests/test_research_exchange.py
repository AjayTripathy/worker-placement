"""The open research exchange: pseudonymous contribution, auto-commit, reuse
across offices, and the authenticated central service."""
import copy
import json
import subprocess
from datetime import date
from pathlib import Path
from research_admission_fixtures import fixture_admission, fixture_reviewer

import pytest

from officekit import strategy_proposals as jobs
from officekit_ai.general_court import run_general_court
from officekit_research import cases, contributor, exchange, general
from test_officekit_strategy_proposals import Provider, clients
from test_contextual_research import proposal, execute, sources

PACK = {"symbol": "VDC", "built": "2026-09-19", "errors": [], "reuse": {}, "sections": {
    "fund_profile": {"url": "https://example.org/issuer/VDC", "fetched_at": "2026-09-19T10:00:00+00:00",
                     "text": "A consumer-staples equity fund.", "truncated": False}}}
OFFICE_A = {"office_id": "11111111-1111-4111-8111-111111111111", "research_sharing": {"contributor": "pseudonymous"}}
OFFICE_B = {"office_id": "22222222-2222-4222-8222-222222222222", "research_sharing": {"contributor": "pseudonymous"}}


PACKS = {}


def write(root, record, *args, **kwargs):
    review = fixture_admission(record, PACKS[record["id"]]) if record["id"] in PACKS else None
    return exchange.write(root, record, *args, review=review, **kwargs)


@pytest.fixture(autouse=True)
def synthetic_publication_reviewer(monkeypatch):
    from officekit_research import admission
    def review(folder, record):
        pack = json.loads((Path(folder) / "research" / "source_packs" / (record["id"] + ".json")).read_text())
        return fixture_admission(record, pack)
    monkeypatch.setattr(admission, "local_review", review)
    yield
    PACKS.clear()


def evidenced(tmp_path, symbol="VDC", pack=None, models=None):
    record, _ = run_general_court(symbol, "etf", pack or {**PACK, "symbol": symbol}, tmp_path,
                                  clients=models or clients(Provider()))
    PACKS[record["id"]] = json.loads((Path(tmp_path) / "research" / "source_packs" / (record["id"] + ".json")).read_text())
    return record


def git_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    return path


def git(path, *args):
    return subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, text=True).stdout


# ---- the pseudonymous key ------------------------------------------------------

def test_key_is_stable_distinct_and_reveals_nothing():
    a = contributor.contributor_key(OFFICE_A)
    assert a == contributor.contributor_key(copy.deepcopy(OFFICE_A)) and contributor.KEY.fullmatch(a)
    assert a != contributor.contributor_key(OFFICE_B)
    assert OFFICE_A["office_id"].replace("-", "")[:8] not in a              # not a truncation of the identity


def test_rotation_unlinks_and_anonymity_is_a_choice():
    office = copy.deepcopy(OFFICE_A)
    before = contributor.contributor_key(office)
    after = contributor.rotate(office)
    assert after != before and contributor.contributor_key(office) == after
    office["research_sharing"]["contributor"] = "anonymous"
    assert contributor.contributor_key(office) is None


def test_sharing_is_off_until_turned_on_and_settings_are_validated():
    assert contributor.settings({})["mode"] == "off"                          # SHARING is opt-in...
    assert contributor.settings({})["auto_push"] is True                      # ...and once on, public equities publish implicitly
    assert contributor.settings({"research_sharing": {"auto_push": False}})["auto_push"] is False
    with pytest.raises(ValueError):
        contributor.settings({"research_sharing": {"mode": "everything"}})
    with pytest.raises(ValueError, match="no identity"):
        contributor.contributor_key({"research_sharing": {"contributor": "pseudonymous"}})


# ---- admission and the directory -----------------------------------------------

def test_identical_research_from_two_offices_is_one_record_two_attributions(tmp_path):
    record = evidenced(tmp_path / "o")
    root = tmp_path / "exchange"
    first = write(root, record, contributor.contributor_key(OFFICE_A))
    assert len(first) == 3                                                   # the record + an attribution
    assert write(root, record, contributor.contributor_key(OFFICE_A)) == []      # idempotent
    second = write(root, record, contributor.contributor_key(OFFICE_B))
    assert len(second) == 1 and "attribution" in str(second[0])
    assert len(exchange.records(root)) == 1 and len(exchange.contributors(root, record["id"])) == 2
    row = exchange.catalog(root)["symbols"]["VDC"][0]
    assert row["contributors"] == 2 and row["factors"]["equity"] == "high"


def test_unevidenced_and_tampered_research_is_refused(tmp_path):
    lite, _ = run_general_court("VDC", "etf", {}, tmp_path / "o", clients=clients(Provider()))
    with pytest.raises(ValueError, match="evidenced"):
        write(tmp_path / "x", lite)
    forged = copy.deepcopy(evidenced(tmp_path / "o2"))
    forged["assessment"]["standing"] = "uninvestable"
    with pytest.raises(ValueError, match="digest"):
        exchange.admit(forged)
    root = exchange.init(tmp_path / "x")
    (root / "general" / "VDC").mkdir(parents=True)
    (root / "general" / "VDC" / ("0" * 64 + ".json")).write_text("{not json")
    assert exchange.records(root) == []                                      # garbage is never research


def test_tripwire_blocks_a_breached_boundary_without_echoing_the_secret(tmp_path):
    record = evidenced(tmp_path / "o")
    snapshot = {"answers": {"owner": "Priya Raman", "goals": [{"label": "House", "amount": 1250000}]}}
    exchange.tripwire(record, snapshot)                                      # clean research passes
    leaked = copy.deepcopy(record)
    leaked["assessment"]["summary"] += " Suitable given Priya Raman's 1,250,000 house purchase."
    with pytest.raises(ValueError) as error:
        exchange.tripwire(leaked, snapshot)
    assert "Priya" not in str(error.value) and "1,250,000" not in str(error.value)
    assert "needs investigation" in str(error.value)


# ---- auto-commit ---------------------------------------------------------------

def sharing(office, root, **more):
    return {**office, "research_sharing": {"mode": "general", "contributor": "pseudonymous", "exchange": str(root), **more}}


def test_submit_commits_under_a_neutral_identity_and_respects_push_opt_out(tmp_path, monkeypatch):
    root = git_repo(tmp_path / "exchange")
    (root / "unrelated.txt").write_text("someone's staged work")
    git(root, "add", "unrelated.txt")
    pushed = []
    monkeypatch.setattr(exchange, "push", lambda r: pushed.append(r) or True)
    record = evidenced(tmp_path / "o")
    status = exchange.submit(tmp_path / "o", record, sharing(OFFICE_A, root, auto_push=False), today=date(2026, 9, 19))
    assert status["shared"] and status["new"] and status["commit"] and status["pushed"] is False and pushed == []
    assert "turned implicit publishing off" in status["push_note"]
    assert status["contributor"] == contributor.contributor_key(OFFICE_A)
    author = git(root, "log", "-1", "--format=%an|%ae|%cn|%ce|%aI").strip().replace("+00:00", "Z")
    # Neutral identity (the contributor's own git identity would undo the pseudonym) and a
    # date-only timestamp (a precise commit time is a linkage side-channel).
    assert author == "officekit-exchange|exchange@example.invalid|officekit-exchange|exchange@example.invalid|2026-09-19T00:00:00Z"
    committed = git(root, "show", "--name-only", "--format=", "HEAD").split()
    assert "unrelated.txt" not in committed and "catalog.json" in committed          # pathspec-limited
    assert "unrelated.txt" in git(root, "diff", "--cached", "--name-only")             # their staged work is untouched
    again = exchange.submit(tmp_path / "o", record, sharing(OFFICE_A, root, auto_push=False))
    assert again["shared"] and again["new"] is False and again["commit"] is None       # nothing to commit twice


def test_sharing_failures_never_fail_the_research(tmp_path):
    record = evidenced(tmp_path / "o")
    assert exchange.submit(tmp_path / "o", record, OFFICE_A) == {"shared": False, "reason": "Research sharing is off for this office"}
    lite, _ = run_general_court("VDC", "etf", {}, tmp_path / "o2", clients=clients(Provider()))
    status = exchange.submit(tmp_path / "o2", lite, sharing(OFFICE_A, tmp_path / "x"))
    assert status["shared"] is False and "evidenced" in status["reason"]
    status = exchange.submit(tmp_path / "o", record, sharing(OFFICE_A, tmp_path / "plain-folder"))
    assert status["shared"] and status["commit"] is None                       # a plain folder works; it just isn't git


# ---- one office's research, another office's court ------------------------------

def test_second_office_reuses_exchange_research_but_rules_for_itself(tmp_path, monkeypatch):
    sources(monkeypatch)
    root = git_repo(tmp_path / "exchange")
    donor = tmp_path / "donor"
    _, p = proposal(donor)
    p["snapshot"]["answers"]["office_id"] = OFFICE_A["office_id"]
    p["snapshot"]["answers"]["research_sharing"] = {"mode": "general", "exchange": str(root)}
    jobs.save(donor, p)
    p, first = execute(donor, p)
    shared = p["general"]["VDC"]["shared"]
    assert shared["shared"] and shared["commit"] and len(first.calls) == 7
    assert "PRIVATE OWNER SENTINEL" not in git(root, "log", "-p")               # nothing of the office reached the repo

    recipient = tmp_path / "recipient"
    _, q = proposal(recipient)
    q["snapshot"]["answers"]["office_id"] = OFFICE_B["office_id"]
    q["snapshot"]["answers"]["research_sharing"] = {"mode": "general", "exchange": str(root)}
    jobs.save(recipient, q)
    q, second = execute(recipient, q)
    entry = q["general"]["VDC"]
    assert entry["source"] == "exchange" and entry["record"]["id"] == p["general"]["VDC"]["record"]["id"]
    assert entry["corroboration"] == {"matched_sections": ["fund_profile"], "status": "corroborated"}
    assert len(second.calls) == 4                                               # analyst, ITS OWN suitability ruling, risk, pitch
    assert q["courts"][0]["id"] != p["courts"][0]["id"]                          # an independent ruling
    assert q["courts"][0]["general_id"] == p["courts"][0]["general_id"]          # ...on the same shared research
    assert general.load(recipient, entry["record"]["id"])                       # imported into its own library


def test_a_moving_price_tape_never_blocks_corroboration(tmp_path):
    root = tmp_path / "exchange"
    then = {**PACK, "sections": {**PACK["sections"], "tape": dict(last=100.0, as_of="2026-09-19", wk52_hi=110, wk52_lo=90, off_high_pct=-9, off_low_pct=11)}}
    record = evidenced(tmp_path / "o", pack=then)
    write(root, record)
    now = {**PACK, "sections": {**PACK["sections"], "tape": dict(last=104.25, as_of="2026-09-22", wk52_hi=110, wk52_lo=90, off_high_pct=-5, off_low_pct=16)}}
    found, state = exchange.find(root, "VDC", "etf", record["protocol_hash"], today=cases.day(record["as_of"]), pack=now)
    assert found["id"] == record["id"] and state == {"matched_sections": ["fund_profile"], "status": "corroborated"}


def test_research_is_not_reused_when_the_source_now_says_something_else(tmp_path):
    root = tmp_path / "exchange"
    record = evidenced(tmp_path / "o")
    write(root, record)
    today = cases.day(record["as_of"])
    same = exchange.find(root, "VDC", "etf", record["protocol_hash"], today=today, pack=PACK)
    assert same[0]["id"] == record["id"] and same[1]["status"] == "corroborated"
    moved = copy.deepcopy(PACK)
    moved["sections"]["fund_profile"]["text"] = "The fund changed its mandate to small-cap growth."
    assert exchange.find(root, "VDC", "etf", record["protocol_hash"], today=today, pack=moved) == (None, None)
    unread = exchange.find(root, "VDC", "etf", record["protocol_hash"], today=today, pack={})
    assert unread[1]["status"] == "uncorroborated"                              # usable during an outage, and labelled


def test_weaker_research_on_the_exchange_is_not_trusted_by_a_stronger_office(tmp_path):
    from officekit_ai.court import _tier_of
    weak = {s: (Provider(), "test-sonnet") for s in ("bench", "adjudicate")}
    record = evidenced(tmp_path / "o", models=weak)
    write(tmp_path / "x", record)
    today = cases.day(record["as_of"])
    args = (tmp_path / "x", "VDC", "etf", record["protocol_hash"])
    assert exchange.find(*args, today=today, minimum_tier=_tier_of("sonnet"), tier_of=_tier_of)[0]
    assert exchange.find(*args, today=today, minimum_tier=_tier_of("opus"), tier_of=_tier_of) == (None, None)


# ---- public outcomes and calibration by contributor ----------------------------

def test_outcomes_are_public_sourced_and_score_the_contributor(tmp_path):
    root = tmp_path / "exchange"
    key = contributor.contributor_key(OFFICE_A)
    for i in range(20):
        record = evidenced(tmp_path / f"o{i}", symbol=f"T{i:03d}")
        write(root, record, key)
        exchange.resolve(root, record["id"] + ":0", True, "https://www.sec.gov/Archives/x.htm", contributor=key)
    with pytest.raises(ValueError):
        exchange.resolve(root, record["id"] + ":0", True, "http://insecure.example/x")
    row = exchange.scoreboard(root, "contributor")[0]
    assert row["contributor"] == key and row["resolved"] == 20 and row["skill_vs_base_rate"] is not None
    thin = exchange.scoreboard(root, "symbol")[0]
    assert thin["skill_vs_base_rate"] is None and "needs 20" in thin["note"]


# ---- the central (hosted) exchange ---------------------------------------------

@pytest.fixture
def central():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from hosting.app.main import create_app
    from test_hosted_migration import Backend, MemoryStore, ORIGIN
    store = MemoryStore()
    from hosting.app.exchange import Exchange
    service = Exchange(store, evidence_loader=lambda record: PACKS[record["id"]], reviewer=fixture_reviewer)
    with TestClient(create_app(Backend(), ORIGIN, store=store, exchange=service), base_url=ORIGIN) as c:
        c.store = store
        yield c


def send(c, data, who="alice"):
    return c.post("/api/research/general", json=data, headers={"Authorization": "Bearer " + who})


def test_central_exchange_verifies_a_key_on_first_use_and_refuses_borrowers(central, tmp_path):
    record = evidenced(tmp_path / "o")
    key = contributor.contributor_key(OFFICE_A)
    first = send(central, {"record": record, "contributor": key})
    assert first.status_code == 200 and first.json() == {"status": "contributed", "record_id": record["id"], "attribution": "verified"}
    stolen = send(central, {"record": evidenced(tmp_path / "o2", symbol="XLP"), "contributor": key}, who="bob")
    assert stolen.status_code == 403 and "another account" in stolen.text           # a track record cannot be borrowed
    assert send(central, {"record": record, "contributor": key}).json()["status"] == "already_present"   # idempotent


def test_central_exchange_requires_credentials_and_refuses_bad_research(central, tmp_path):
    record = evidenced(tmp_path / "o")
    assert central.post("/api/research/general", json={"record": record}).status_code == 401
    lite, _ = run_general_court("VDC", "etf", {}, tmp_path / "o2", clients=clients(Provider()))
    assert send(central, {"record": lite}).status_code == 400
    private = copy.deepcopy(record)
    private["assessment"]["office_id"] = "x"
    assert send(central, {"record": private}).status_code == 400
    assert send(central, {"record": record, "contributor": "not-a-key"}).status_code == 400
    assert central.get("/api/research/general/VDC").status_code in {303, 401}           # reading needs a member


def test_anonymous_contributions_count_once_per_account_and_bindings_never_leave(central, tmp_path):
    from hosting.app.exchange import Exchange
    record = evidenced(tmp_path / "o")
    assert send(central, {"record": record}).json()["attribution"] == "anonymous"
    send(central, {"record": record})                                              # same account again
    send(central, {"record": record}, who="bob")
    listing = central.get("/api/research/general/VDC", headers={"Authorization": "Bearer alice"}).json()["research"]
    assert listing[0]["id"] == record["id"] and listing[0]["contributors"] == 2   # alice once, bob once
    read = central.get(f"/api/research/general/VDC/{record['id']}", headers={"Authorization": "Bearer bob"})
    assert read.status_code == 200 and read.json()["id"] == record["id"]
    send(central, {"record": record, "contributor": contributor.contributor_key(OFFICE_A)})
    exported = list(Exchange(central.store).export())
    blob = json.dumps(exported)
    assert "tenant" not in blob and "alice" not in blob and "exchange/contributors" not in blob


def test_operator_export_commits_central_contributions_to_the_open_corpus(central, tmp_path):
    from hosting.gcp.export_exchange import export
    key = contributor.contributor_key(OFFICE_A)
    send(central, {"record": evidenced(tmp_path / "o"), "contributor": key})
    root = git_repo(tmp_path / "oss")
    result = export(central.store, root)
    assert result["commit"] and result["skipped"] == 0
    who = exchange.contributors(root, exchange.records(root)[0]["id"])
    assert who[0]["contributor"] == key and who[0]["attribution"] == "verified"
    assert export(central.store, root)["commit"] is None                            # idempotent


# ---- contextual cases: attribution is opt-in ------------------------------------

def test_contextual_case_is_anonymous_unless_its_reviewer_opts_in(tmp_path, monkeypatch):
    sources(monkeypatch)
    folder = tmp_path / "donor"
    _, p = proposal(folder)
    p, _ = execute(folder, p)
    draft = cases.prepare_case(p, "VDC")
    anonymous = cases.approve(draft, cases.digest(draft["case"]))
    assert "contributor" not in anonymous["review"]                          # the default carries no key
    key = contributor.contributor_key(OFFICE_A)
    attributed = cases.approve(draft, cases.digest(draft["case"]), contributor=key)
    assert attributed["review"]["contributor"] == key and attributed["id"] != anonymous["id"]
    # Attribution is sealed into the bundle's identity: it cannot be swapped afterwards...
    forged = copy.deepcopy(attributed)
    forged["review"]["contributor"] = contributor.contributor_key(OFFICE_B)
    with pytest.raises(ValueError, match="digest mismatch"):
        cases.validate_bundle(forged)
    # ...and a malformed key is refused at approval.
    with pytest.raises(ValueError, match="contributor"):
        cases.approve(draft, cases.digest(draft["case"]), contributor="someone-else")
    from officekit_research import index
    recipient = tmp_path / "recipient"
    recipient.mkdir()
    cases.import_bundle(recipient, attributed)
    assert index.query(recipient, kind="case")[0]["contributor"] == key


def test_a_hosted_office_never_writes_research_to_an_inherited_local_path(tmp_path, monkeypatch):
    import officekit.runtime as runtime
    monkeypatch.setattr(runtime, "hosted", lambda: True)
    target = tmp_path / "path-from-the-old-laptop"
    status = exchange.submit(tmp_path / "o", evidenced(tmp_path / "o"), sharing(OFFICE_A, target))
    assert status["shared"] is False and "central exchange" in status["reason"]
    assert not target.exists()


# ---- push policy: implicit for public equities, explicit for private deals -------

def remote_and_exchange(tmp_path):
    """A dedicated exchange repository with a real (bare) remote to publish to."""
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    root = git_repo(tmp_path / "exchange")
    git(root, "remote", "add", "origin", str(remote))
    git(root, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "--allow-empty", "-m", "init")
    branch = git(root, "branch", "--show-current").strip()
    git(root, "push", "-q", "-u", "origin", branch)
    return remote, root, branch


def published(remote, branch):
    return git(remote, "ls-tree", "-r", "--name-only", branch).split()


def private_record(tmp_path):
    record, _ = run_general_court("ACMEHOUSING", "private", {**PACK, "symbol": "ACMEHOUSING"}, tmp_path,
                                  clients=clients(Provider()))
    PACKS[record["id"]] = json.loads((Path(tmp_path) / "research" / "source_packs" / (record["id"] + ".json")).read_text())
    return record


def test_public_equity_research_is_published_implicitly_by_default(tmp_path):
    remote, root, branch = remote_and_exchange(tmp_path)
    assert contributor.settings(sharing(OFFICE_A, root))["auto_push"] is True        # the default once sharing is on
    record = evidenced(tmp_path / "o")
    status = exchange.submit(tmp_path / "o", record, sharing(OFFICE_A, root))
    assert status["pushed"] is True and status["held"] is False and status["push_note"] is None
    assert f"general/VDC/{record['id']}.json" in published(remote, branch)


def test_an_office_can_turn_implicit_publishing_off(tmp_path):
    remote, root, branch = remote_and_exchange(tmp_path)
    record = evidenced(tmp_path / "o")
    status = exchange.submit(tmp_path / "o", record, sharing(OFFICE_A, root, auto_push=False))
    assert status["commit"] and status["pushed"] is False
    assert not any("general/" in p for p in published(remote, branch))              # committed locally, not published
    exchange.push(root)                                                              # ...until someone says so
    assert f"general/VDC/{record['id']}.json" in published(remote, branch)


def test_private_deal_research_is_never_published_implicitly(tmp_path):
    remote, root, branch = remote_and_exchange(tmp_path)
    deal = private_record(tmp_path / "p")
    status = exchange.submit(tmp_path / "p", deal, sharing(OFFICE_A, root))          # auto_push is ON
    assert status == {"shared": True, "held": True, "record_id": deal["id"], "contributor": contributor.contributor_key(OFFICE_A),
                      "commit": None, "pushed": False, "reason": "Private-deal research is held until you release it explicitly"}
    assert git(root, "status", "--porcelain", "--", "held").strip() == ""           # git cannot even see it
    assert exchange.records(root) == [] and [h["record"]["id"] for h in exchange.held(root)] == [deal["id"]]

    # The dangerous moment: a LATER implicit public-equity push must not carry the deal out with it.
    public = evidenced(tmp_path / "o")
    assert exchange.submit(tmp_path / "o", public, sharing(OFFICE_A, root))["pushed"] is True
    out = published(remote, branch)
    assert f"general/VDC/{public['id']}.json" in out
    assert not any(deal["id"] in p or "ACMEHOUSING" in p or p.startswith("held/") for p in out)
    assert "ACMEHOUSING" not in git(remote, "log", "-p", branch)


def test_release_is_the_explicit_act_and_publishing_it_is_a_second_one(tmp_path):
    remote, root, branch = remote_and_exchange(tmp_path)
    deal = private_record(tmp_path / "p")
    exchange.submit(tmp_path / "p", deal, sharing(OFFICE_A, root))
    with pytest.raises(ValueError, match="explicit release"):
        write(root, deal)                                                   # no back door into the corpus
    released = exchange.release(root, deal["id"])
    assert released["commit"] and released["pushed"] is False
    assert exchange.held(root) == [] and exchange.records(root)[0]["id"] == deal["id"]
    assert not any("ACMEHOUSING" in p for p in published(remote, branch))            # released ≠ published
    exchange.push(root)                                                              # the second explicit act
    assert f"general/ACMEHOUSING/{deal['id']}.json" in published(remote, branch)
    with pytest.raises(ValueError, match="No held research"):
        exchange.release(root, "0" * 64)


def test_no_implicit_push_from_a_folder_inside_someone_elses_repository(tmp_path, monkeypatch):
    monorepo = git_repo(tmp_path / "monorepo")
    root = monorepo / "research_exchange"
    pushed = []
    monkeypatch.setattr(exchange, "push", lambda r: pushed.append(r) or True)
    status = exchange.submit(tmp_path / "o", evidenced(tmp_path / "o"), sharing(OFFICE_A, root))
    assert status["commit"] and status["pushed"] is False and pushed == []
    assert "inside a larger repository" in status["push_note"]                       # would have published unrelated commits


def test_a_failed_push_is_reported_and_never_loses_the_research(tmp_path):
    root = git_repo(tmp_path / "exchange")                                           # dedicated, but no remote configured
    status = exchange.submit(tmp_path / "o", evidenced(tmp_path / "o"), sharing(OFFICE_A, root))
    assert status["shared"] and status["commit"] and status["pushed"] is False
    assert "could not be pushed" in status["push_note"]


def test_central_exchange_takes_private_research_only_by_explicit_release(central, tmp_path):
    from hosting.app.exchange import Exchange
    deal = private_record(tmp_path / "p")
    assert send(central, {"record": deal}).status_code == 409
    assert send(central, {"record": deal, "release_private": "yes"}).status_code == 409        # only a literal true
    assert send(central, {"record": deal, "release_private": True}).status_code == 200
    send(central, {"record": evidenced(tmp_path / "o")})
    assert [r["subject"]["symbol"] for r, _ in Exchange(central.store).export()] == ["VDC"]
    assert {r["subject"]["symbol"] for r, _ in Exchange(central.store).export(include_private=True)} == {"VDC", "ACMEHOUSING"}


def test_release_can_publish_in_one_explicit_step(tmp_path):
    remote, root, branch = remote_and_exchange(tmp_path)
    deal = private_record(tmp_path / "p")
    exchange.submit(tmp_path / "p", deal, sharing(OFFICE_A, root))
    assert exchange.release(root, deal["id"], publish=True)["pushed"] is True
    assert f"general/ACMEHOUSING/{deal['id']}.json" in published(remote, branch)
