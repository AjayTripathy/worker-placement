"""Research drift is loud and visible without mutating a frozen protocol."""
import datetime as dt

import pytest

from desk.odte import arms as A, text_overlay as E, research_health as H
from test_odte_arms import lab, REGISTER  # noqa: F401
from test_odte_execution import isolation  # noqa: F401


def test_clean_preflight_does_not_create_forecasts_or_touch_registration(lab):
    before = (lab.root/"manifest.json").read_bytes()
    A.write_report(lab.root)
    result, changed = H.publish(lab.root.parent, now=REGISTER+dt.timedelta(minutes=1))
    assert result["status"] == "ready" and changed
    assert (lab.root/"manifest.json").read_bytes() == before
    assert not list((lab.source/"forecasts").glob("*.json"))
    assert "Protocol preflight passed" in (lab.root/"report.html").read_text()
    assert not H.publish(lab.root.parent, now=REGISTER+dt.timedelta(minutes=2))[1]


def test_drift_names_file_warns_and_updates_existing_page(lab, monkeypatch, capsys):
    A.write_report(lab.root)
    with monkeypatch.context() as patch:
        original = E.code_files()
        patch.setattr(E, "code_files", lambda: {**original, "shadow.py": "changed"})
        patch.setattr(E, "code_hash", lambda: "changed")
        result, changed = H.publish(lab.root.parent, now=REGISTER+dt.timedelta(minutes=1))
        H.log(result)
        assert result["status"] == "blocked" and changed
        assert "shadow.py" in result["checks"][0]["changed_files"]
        assert "ACTION REQUIRED" in capsys.readouterr().out
        assert "Research blocked" in (lab.root/"report.html").read_text()
    result, changed = H.publish(lab.root.parent, now=REGISTER+dt.timedelta(minutes=2))
    assert changed and result["status"] == "ready"
    assert "Research blocked" not in (lab.root/"report.html").read_text()


def test_registration_in_future_fails_preflight_without_rewriting_it(lab):
    path = lab.root/"manifest.json"; before = path.read_bytes()
    result = H.check(lab.root.parent, now=REGISTER-dt.timedelta(hours=6))
    assert result["status"] == "blocked"
    assert any("timestamp is in the future" in r.get("error", "") for r in result["checks"])
    assert path.read_bytes() == before


def test_source_identity_replacement_is_loud_even_if_source_hash_is_valid(lab):
    path = lab.source/"manifest.json"
    m = E.read(path); m["submitter"] = "different-source"
    m["protocol"] = E.digest({k: v for k, v in m.items() if k != "protocol"})
    E.atomic_json(path, m)
    result = H.check(lab.root.parent, now=REGISTER+dt.timedelta(minutes=1))
    assert result["status"] == "blocked"
    assert any("identity differs" in r.get("error", "") for r in result["checks"])


def test_cli_returns_failure_for_drift(lab, monkeypatch):
    monkeypatch.setattr(E, "code_hash", lambda: "changed")
    monkeypatch.setattr("sys.argv", ["research_health", "--data", str(lab.root.parent)])
    with pytest.raises(SystemExit) as error:
        H.main()
    assert error.value.code == 1


def test_daemon_preflight_failure_does_not_prevent_ordinary_capture(monkeypatch, capsys):
    from desk.odte import runner as R
    from types import SimpleNamespace as NS
    events = []
    class Clock(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 10, 8, 10, tzinfo=E.ET)
    def broken(*a, **kw):
        raise ValueError("fixture preflight failure")
    def end(*a):
        raise KeyboardInterrupt
    monkeypatch.setattr(R.dt, "datetime", Clock)
    monkeypatch.setattr(R, "_lock", lambda: True)
    monkeypatch.setattr(R, "_unlock", lambda: None)
    monkeypatch.setattr(R, "freeze", lambda: None)
    monkeypatch.setattr(H, "publish", broken)
    monkeypatch.setattr(R, "_connect", lambda **kw: NS(isConnected=lambda: True, managedAccounts=lambda: [], sleep=end))
    monkeypatch.setattr(R, "Session", lambda *a: NS(date="2026-10-08", tick=lambda *a: events.append("captured")))
    R.daemon(False)
    assert events == ["captured"]
    assert "RESEARCH PREFLIGHT FAILED" in capsys.readouterr().out
