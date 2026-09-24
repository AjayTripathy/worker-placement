"""Real SDK serialization with an isolated HTTP transport; no provider calls."""
import copy
import json
from types import SimpleNamespace

import httpx
import pytest

from officekit_ai.intelligence import OpenAIResponses, Request, generate
from officekit_ai.provenance import invoke
from officekit_ai import models
from officekit.runtime import hosted_office

SCHEMA = {"type": "object", "properties": {"answer": {"type": "string"}},
          "required": ["answer"], "additionalProperties": False}


def response(**changes):
    return {"id": "resp_test", "object": "response", "created_at": 1,
            "model": "gpt-6-astra", "status": "completed", "error": None,
            "output": [{"id": "msg_test", "type": "message", "status": "completed", "role": "assistant",
                        "content": [{"type": "output_text", "text": '{"answer":"supported"}', "annotations": []}]}],
            "usage": {"input_tokens": 120, "output_tokens": 50, "total_tokens": 170,
                      "input_tokens_details": {"cached_tokens": 20}, "output_tokens_details": {"reasoning_tokens": 30}},
            **changes}


def adapter(payload=None, status=200):
    import openai
    requests = []
    payload = payload if payload is not None else response()
    def handle(request):
        requests.append(json.loads(request.content))
        assert str(request.url) == "https://api.openai.com/v1/responses"
        if status != 200:
            return httpx.Response(status, json={"error": {"message": "Synthetic failure", "type": "test_error"}})
        # Exercise the actual SDK's streaming accumulator and final response.
        events = [dict(type="response.created", response=response(status="in_progress", output=[]), sequence_number=0),
                  dict(type="response.completed", response=payload, sequence_number=1)]
        return httpx.Response(200, text="".join("data: " + json.dumps(e) + "\n\n" for e in events),
                              headers={"content-type": "text/event-stream"})
    sdk = openai.OpenAI(api_key="test-only", max_retries=0, base_url="https://api.openai.com/v1",
                        http_client=httpx.Client(transport=httpx.MockTransport(handle)))
    return OpenAIResponses(sdk), requests


def test_responses_contract_and_provenance():
    client, calls = adapter()
    result, provenance = invoke(client, model="gpt-6-astra", max_tokens=4000,
        system="Use supplied evidence", messages=[{"role": "user", "content": "Synthetic input"}],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}})
    call = calls[0]
    assert call["model"] == "gpt-6-astra" and call["max_output_tokens"] == 4000
    assert call["instructions"] == "Use supplied evidence" and call["store"] is False
    assert call["reasoning"] == {"effort": "medium"}
    assert call["text"]["format"] == {"type": "json_schema", "name": "intelligence_result", "strict": True, "schema": SCHEMA}
    assert not {"max_tokens", "temperature", "top_p", "messages", "output_config"} & set(call)
    assert result.content[0].text == '{"answer":"supported"}'
    assert provenance["resolved_model"] == "gpt-6-astra" and provenance["provider_client"] == "openai.responses"
    assert provenance["reasoning_configuration"] == {"effort": "medium"}
    assert provenance["usage"]["input_tokens"] == 120
    assert provenance["usage"]["output_tokens"] == 50  # Includes billed reasoning tokens.
    assert provenance["usage"]["cache_read_input_tokens"] == 20
    assert provenance["usage"]["cache_creation_input_tokens"] is None


def test_images_pdf_and_conversation_are_translated_without_remote_upload():
    client, calls = adapter()
    generate(client, model="gpt-6-astra", max_tokens=500,
             messages=[{"role": "assistant", "content": "Earlier reply"}, {"role": "user", "content": [
                 {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "eA=="}},
                 {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": "eA=="}},
                 {"type": "text", "text": "Extract"}]}], timeout=45)
    blocks = calls[0]["input"][1]["content"]
    assert blocks[0] == {"type": "input_image", "image_url": "data:image/png;base64,eA=="}
    assert blocks[1] == {"type": "input_file", "filename": "document.pdf", "file_data": "data:application/pdf;base64,eA=="}
    assert blocks[2] == {"type": "input_text", "text": "Extract"}


@pytest.mark.parametrize("payload", [response(status="failed"), response(status="incomplete", incomplete_details={"reason": "content_filter"}),
    response(output=[]), response(output=[{"id": "msg_test", "type": "message", "status": "completed", "role": "assistant",
                                          "content": [{"type": "refusal", "refusal": "Synthetic refusal"}]}])])
def test_failed_empty_or_refused_response_never_succeeds(payload):
    client, calls = adapter(payload)
    with pytest.raises(RuntimeError):
        client.complete(Request("gpt-6-astra", [], 1000))
    assert len(calls) == 1


def test_truncation_and_usage_survive_adapter():
    client, _ = adapter(response(status="incomplete", incomplete_details={"reason": "max_output_tokens"}))
    result = client.complete(Request("gpt-6-astra", [], 1000))
    assert result.stop_reason == "max_tokens" and result.usage.output_tokens == 50


def test_provider_failure_is_not_retried_or_substituted():
    import openai
    client, calls = adapter(status=429)
    with pytest.raises(openai.RateLimitError):
        client.complete(Request("gpt-6-astra", [], 1000))
    assert len(calls) == 1


def test_hosted_openai_credentials_never_use_machine_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "machine-only")
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    (tmp_path / ".openai_key").write_text("file-only")
    with hosted_office(tmp_path):
        assert models.resolve_key("OPENAI_API_KEY") is None
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            models.client_for("intake", tmp_path)
    with hosted_office(tmp_path, {"OPENAI_API_KEY": "tenant-only"}):
        client, model = models.client_for("intake", tmp_path)
        assert client.client.api_key == "tenant-only" and model == "gpt-6-astra"
        client.client.close()
    assert models.resolve_key("OPENAI_API_KEY") == "machine-only"


def test_configured_publisher_uses_registry_and_distinct_key(monkeypatch):
    from hosting.app.exchange import configured_exchange
    monkeypatch.setenv("RESEARCH_REVIEW_PROVIDER", "test-reviewer")
    monkeypatch.setenv("RESEARCH_REVIEW_MODEL", "review-model")
    monkeypatch.setenv("RESEARCH_REVIEW_API_KEY", "review-only")
    seen = []
    monkeypatch.setitem(models.PROVIDERS, "test-reviewer", lambda cfg: seen.append(cfg) or object())
    service = configured_exchange(object())
    assert service.reviewer is not None and seen[0]["api_key_env"] == "RESEARCH_REVIEW_API_KEY"
    assert "review-only" not in json.dumps(seen)


def test_acquisition_detector_uses_injected_intelligence_and_fails_loudly():
    from verticals.public_co.m_sources.acq_coherence import score_acquisition_coherence
    payload = response()
    payload["output"][0]["content"][0]["text"] = json.dumps({"coherence_score": .8, "category": "high_coherence",
            "reasoning": "Synthetic evidence", "is_revenue_synthetic": False})
    client, calls = adapter(payload)
    result = score_acquisition_coherence("Synthetic thesis", [{"acquired_name": "Example"}], client=client, model="gpt-6-astra")
    assert result["status"] == "complete" and result["n_acquisitions_scored"] == 1
    assert result["llm_model"] == "gpt-6-astra" and len(calls) == 1
    broken, calls = adapter(status=402)
    result = score_acquisition_coherence("Synthetic thesis", [{"acquired_name": "Example"}], client=broken, model="gpt-6-astra")
    assert result["status"] == "error" and result["n_acquisitions_failed"] == 1 and len(calls) == 1


def test_existing_explicit_provider_choice_still_wins(tmp_path):
    (tmp_path / "models.json").write_text(json.dumps({"v": 1,
        "providers": {"anthropic": {"api_key_env": "ANTHROPIC_API_KEY"}},
        "slots": {"intake": {"provider": "anthropic", "model": "claude-opus-5"}}}))
    assert models.resolve("intake", tmp_path)[0] == "anthropic"
    assert models.resolve("adjudicate", tmp_path)[2] == "gpt-6-astra"
