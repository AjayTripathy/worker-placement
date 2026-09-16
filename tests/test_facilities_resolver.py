"""facilities_resolver failure-semantics tests (all offline — network + LLM monkeypatched).

The contract under test (fc34665d doctrine applied to R1.13):
  - INFRA failure (SEC 403 on the doc, or the extraction dispatch dying) must surface
    as degraded and MUST NOT be cached — a transient outage must never become a
    sticky "0 sites" observation for TTL_DAYS.
  - A genuinely empty Properties read ([] from a successful pass) IS cacheable.
  - A cached degraded record (pre-fix vintage) is retried, not trusted.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desk import facilities_resolver as FR


@pytest.fixture
def cache_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(FR, "CACHE_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def cik_ok(monkeypatch):
    import desk.court_evidence as CE
    monkeypatch.setattr(CE, "_cik", lambda t: 12345)


SUBMISSIONS = json.dumps({
    "name": "TESTCO INC",
    "addresses": {"business": {"street1": "1 MAIN ST", "city": "AUSTIN", "stateOrCountry": "TX"}},
    "filings": {"recent": {"form": ["10-K"], "accessionNumber": ["0000012345-26-000001"],
                           "primaryDocument": ["testco-10k.htm"]}},
})


def _curl_factory(doc_html):
    def _curl(url, timeout=25):
        if "data.sec.gov/submissions" in url:
            return SUBMISSIONS
        if "Archives" in url:
            return doc_html
        return ""
    return _curl


def test_doc_fetch_403_is_degraded_and_not_cached(cache_dir, cik_ok, monkeypatch):
    monkeypatch.setattr(FR, "_curl", _curl_factory(""))          # SEC 403 -> empty body
    monkeypatch.setattr(FR, "_geocode", lambda a: ((30.0, -97.0), "census"))
    out = FR.resolve("TESTCO")
    assert out.get("degraded"), "an empty doc fetch must mark the record degraded"
    assert out["sites"] == []
    assert not (cache_dir / "TESTCO.json").exists(), "degraded results must not be cached"


def test_dispatch_failure_is_degraded_and_not_cached(cache_dir, cik_ok, monkeypatch):
    body = "Item 2. Properties " + "Our plant in Waco, Texas makes widgets. " * 20 + " Item 3."
    monkeypatch.setattr(FR, "_curl", _curl_factory(body))
    monkeypatch.setattr(FR, "_extract_sites", lambda s, e: None)  # infra failure signal
    monkeypatch.setattr(FR, "_geocode", lambda a: ((30.0, -97.0), "census"))
    out = FR.resolve("TESTCO")
    assert out.get("degraded")
    assert not (cache_dir / "TESTCO.json").exists()


def test_genuine_zero_sites_is_cached(cache_dir, cik_ok, monkeypatch):
    body = "Item 2. Properties " + "We lease office space adequate for our needs. " * 10 + " Item 3."
    monkeypatch.setattr(FR, "_curl", _curl_factory(body))
    monkeypatch.setattr(FR, "_extract_sites", lambda s, e: [])    # read fine, held nothing
    monkeypatch.setattr(FR, "_geocode", lambda a: ((30.0, -97.0), "census"))
    out = FR.resolve("TESTCO")
    assert not out.get("degraded")
    assert out["sites"] == []
    assert (cache_dir / "TESTCO.json").exists(), "a real zero-site read is a valid observation"


def test_successful_extraction_caches_and_geocodes(cache_dir, cik_ok, monkeypatch):
    body = "Item 2. Properties our Waco plant " * 30 + " Item 3."
    monkeypatch.setattr(FR, "_curl", _curl_factory(body))
    monkeypatch.setattr(FR, "_extract_sites",
                        lambda s, e: [{"name": "Waco Plant", "location": "Waco, TX",
                                       "purpose": "manufacturing"}])
    monkeypatch.setattr(FR, "_geocode", lambda a: ((31.5, -97.1), "census"))
    out = FR.resolve("TESTCO")
    assert len(out["sites"]) == 1 and out["sites"][0]["lat"] == 31.5
    cached = json.loads((cache_dir / "TESTCO.json").read_text())
    assert cached["sites"][0]["name"] == "Waco Plant"
    # second call comes from cache — poison the network to prove it
    monkeypatch.setattr(FR, "_curl", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network hit")))
    out2 = FR.resolve("TESTCO")
    assert out2["sites"][0]["name"] == "Waco Plant"


def test_cached_degraded_record_is_retried(cache_dir, cik_ok, monkeypatch):
    # pre-fix vintage: a degraded record that DID get written must not be trusted
    import datetime
    (cache_dir / "TESTCO.json").write_text(json.dumps({
        "ticker": "TESTCO", "asof": datetime.datetime.utcnow().isoformat() + "Z",
        "hq": None, "sites": [], "degraded": "properties-doc fetch empty (SEC 403?)",
        "note": "DEGRADED"}))
    body = "Item 2. Properties our Waco plant " * 30 + " Item 3."
    monkeypatch.setattr(FR, "_curl", _curl_factory(body))
    monkeypatch.setattr(FR, "_extract_sites",
                        lambda s, e: [{"name": "Waco Plant", "location": "Waco, TX", "purpose": "mfg"}])
    monkeypatch.setattr(FR, "_geocode", lambda a: ((31.5, -97.1), "census"))
    out = FR.resolve("TESTCO")
    assert out["sites"], "a cached degraded record must be re-resolved, not returned"
