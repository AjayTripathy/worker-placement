import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from officekit.runtime import hosted_office
from officekit_ai import local_agent, models
from officekit_ai.intelligence import Request


@pytest.fixture
def cli(monkeypatch):
    monkeypatch.setattr(local_agent, "executable", lambda: "/test/codex")
    monkeypatch.setattr(local_agent, "signed_in", lambda *_: True)
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        Path(command[command.index("-o") + 1]).write_text('{"answer":"ok"}')
        return SimpleNamespace(returncode=0, stderr="", stdout=json.dumps({
            "type": "turn.completed", "usage": {"input_tokens": 15, "output_tokens": 9,
            "cached_input_tokens": 3, "cache_write_input_tokens": 0}}))
    monkeypatch.setattr(local_agent.subprocess, "run", run)
    return calls


def request():
    return Request("gpt-6-astra", [{"role": "user", "content": "Evidence"}], 1000,
                   system="Review the supplied evidence.", schema={"type": "object"})


def test_local_default_and_saas_credentials_are_separate(tmp_path, cli, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "machine-key-never-used")
    for slot in models.SLOTS:
        client, name = models.client_for(slot, tmp_path)
        assert isinstance(client, local_agent.CodexLocal) and name == "gpt-6-astra"
    (tmp_path / "models.local.json").write_text(json.dumps(models.LOCAL_DEFAULTS))
    with hosted_office(tmp_path):
        assert models.resolve("intake", tmp_path)[0] == "openai"
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            models.client_for("intake", tmp_path)
    with hosted_office(tmp_path, {"OPENAI_API_KEY": "tenant-only"}):
        api, _ = models.client_for("intake", tmp_path)
        assert api.client.api_key == "tenant-only"
        api.client.close()
    assert not cli


def test_local_override_ignores_synced_api_slots_and_is_not_exportable(tmp_path):
    from officekit.migration import safe_path
    (tmp_path / "models.json").write_text(json.dumps(models.DEFAULTS))
    assert models.resolve("intake", tmp_path)[0] == "openai"
    (tmp_path / "models.local.json").write_text(json.dumps(models.LOCAL_DEFAULTS))
    assert models.resolve("intake", tmp_path)[0] == "codex"
    assert not safe_path("models.local.json")
    with hosted_office(tmp_path):
        assert models.resolve("intake", tmp_path)[0] == "openai"


def test_hosted_rejects_even_explicit_or_preconstructed_local_provider(tmp_path, cli):
    client = local_agent.CodexLocal()
    (tmp_path / "models.json").write_text(json.dumps(models.LOCAL_DEFAULTS))
    with hosted_office(tmp_path):
        with pytest.raises(local_agent.LocalAgentError, match="unavailable in SaaS"):
            models.client_for("intake", tmp_path)
        with pytest.raises(local_agent.LocalAgentError, match="unavailable in SaaS"):
            client.complete(request())
    assert not cli


def test_isolated_signed_in_completion_and_honest_provenance(cli, monkeypatch):
    from officekit_ai.provenance import invoke
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://untrusted.invalid")
    result, provenance = invoke(local_agent.CodexLocal(), model="gpt-6-astra", max_tokens=1000,
        messages=[{"role": "user", "content": "Evidence"}],
        output_config={"format": {"type": "json_schema", "schema": {"type": "object"}}})
    cmd, kwargs = cli[0]
    assert "--ephemeral" in cmd and "--ignore-user-config" in cmd
    assert cmd[cmd.index("--sandbox") + 1] == "read-only"
    assert 'forced_login_method="chatgpt"' in cmd
    for setting in ('features.shell_tool=false', 'features.apps=false', 'features.plugins=false',
                    'features.hooks=false', 'agents.enabled=false', 'web_search="disabled"'):
        assert setting in cmd
    assert not {"OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_BASE_URL"} & kwargs["env"].keys()
    assert kwargs["input"].endswith('[{"role": "user", "content": "Evidence"}]')
    assert not Path(kwargs["cwd"]).exists()  # prompt, images and output removed
    assert json.loads(result.content[0].text)["answer"] == "ok"
    assert provenance["requested_model"] == "gpt-6-astra"
    assert provenance["resolved_model"] == "unknown"  # CLI doesn't report it
    assert provenance["provider_client"] == "codex.exec.chatgpt"
    assert provenance["usage"]["input_tokens"] == 15
    assert provenance["cost_usd"] is None


@pytest.mark.parametrize("failure", ["exit", "event", "empty", "invalid", "tool", "timeout"])
def test_failures_never_succeed_or_fall_back(failure, cli, monkeypatch):
    def fail(command, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, 1, output="private evidence")
        path = Path(command[command.index("-o") + 1])
        path.write_text("not json" if failure == "invalid" else "" if failure == "empty" else '{"ok":true}')
        events = [{"type": "turn.failed", "error": {"message": "private evidence sk-secret"}}] if failure == "event" else [{"type": "turn.completed"}]
        if failure == "tool":
            events.append({"type": "item.completed", "item": {"type": "command_execution"}})
        return SimpleNamespace(returncode=1 if failure == "exit" else 0,
            stdout="\n".join(map(json.dumps, events)), stderr="private evidence sk-secret")
    monkeypatch.setattr(local_agent.subprocess, "run", fail)
    with pytest.raises(local_agent.LocalAgentError) as error:
        local_agent.CodexLocal().complete(request())
    from officekit.api_errors import classify
    code, message = classify(error.value)
    assert code == 502 and "Local Codex" in message
    assert "private evidence" not in message and "sk-secret" not in message


def test_missing_login_does_not_use_available_api_key(monkeypatch, cli):
    monkeypatch.setenv("OPENAI_API_KEY", "not-used")
    monkeypatch.setattr(local_agent, "signed_in", lambda *_: False)
    with pytest.raises(local_agent.LocalAgentError, match="codex login"):
        models.client_for("intake")
    assert not cli


def test_settings_name_active_local_provider_and_hosted_never_checks_cli(tmp_path, cli, monkeypatch):
    from officekit.render_settings import render_settings
    page = render_settings(folder=tmp_path)
    assert "Signed-in local Codex" in page and "gpt-6-astra" in page
    assert "No API key fallback" in page
    monkeypatch.setattr(local_agent, "signed_in", lambda *_: pytest.fail("Hosted settings checked local login"))
    page = render_settings(hosted=True)
    assert "Local intelligence" not in page and "API intelligence" in page


def test_new_office_keeps_runtime_defaults(tmp_path):
    from officekit.cli import _cmd_init
    _cmd_init(SimpleNamespace(dir=str(tmp_path)))
    assert models.resolve("intake", tmp_path)[0] == "codex"
    with hosted_office(tmp_path):
        assert models.resolve("intake", tmp_path)[0] == "openai"


def test_inline_pdf_and_image_are_rendered_without_file_tools(tmp_path):
    import base64
    import io
    pytest.importorskip('pypdfium2')
    Image = pytest.importorskip('PIL.Image')
    raw = io.BytesIO()
    Image.new('RGB', (200, 100), 'white').save(raw, format='PDF')
    messages = [{"role": "user", "content": [
        {"type": "text", "text": "Extract"},
        {"type": "document", "source": {"type": "base64", "media_type": "application/pdf",
                                          "data": base64.b64encode(raw.getvalue()).decode()}}]}]
    conversation, images = local_agent._messages(messages, tmp_path)
    assert len(images) == 1 and images[0].read_bytes().startswith(b'\x89PNG')
    assert "Extract" in conversation[0]['content'] and "image 1" in conversation[0]['content']


@pytest.mark.parametrize('diagnostic,expected', [
    ('usage limit reached', 'ChatGPT usage limit'),
    ('401 authentication failed secret payload', 'fresh ChatGPT sign-in'),
    ('model is not supported', 'selected model is unavailable')])
def test_cli_errors_are_actionable_and_do_not_expose_diagnostics(diagnostic, expected):
    from officekit.api_errors import classify
    assert expected in classify(local_agent._failure(diagnostic))[1]


def test_attachments_are_passed_to_cli_and_removed(cli, monkeypatch):
    import base64
    captured = {}
    original = local_agent.subprocess.run
    def inspect(command, **kwargs):
        path = Path(command[command.index('--image') + 1])
        captured['path'] = path
        assert path.read_bytes() == b'synthetic pixels'
        assert command[-1] == '-'
        return original(command, **kwargs)
    monkeypatch.setattr(local_agent.subprocess, 'run', inspect)
    local_agent.CodexLocal().complete(Request('gpt-6-astra', [{'role': 'user', 'content': [
        {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png',
                                   'data': base64.b64encode(b'synthetic pixels').decode()}}]}], 100))
    assert not captured['path'].exists()
