"""Provider-neutral intelligence requests; SDK details live in adapters only.

Implement ``complete(Request)`` to add a provider. ``generate`` also adapts the
legacy messages.create contract so existing plugins and recorded fixtures work.
No implicit fallback, retry, model substitution or credential discovery occurs
here. Failed/refused responses never become a successful research result.
"""
from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True)
class Request:
    model: str
    messages: list
    max_output_tokens: int
    system: str = ""
    schema: Optional[dict] = None
    reasoning: Optional[dict] = None
    timeout: Optional[float] = None


@dataclass(frozen=True)
class Text:
    text: str
    type: str = "text"


@dataclass(frozen=True)
class Usage:
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cache_read_input_tokens: Optional[int] = None
    cache_creation_input_tokens: Optional[int] = None


@dataclass(frozen=True)
class Response:
    content: list
    model: str
    stop_reason: str = "end_turn"
    usage: Optional[Usage] = None


class Intelligence(Protocol):
    def complete(self, request: Request) -> Response: ...


def generate(client, *, model, messages, max_tokens, system="", output_config=None,
             thinking=None, timeout=None):
    """Compatibility boundary for existing prompts; providers receive Request."""
    schema = None
    if output_config:
        fmt = output_config.get("format", {})
        if fmt.get("type") != "json_schema" or not isinstance(fmt.get("schema"), dict):
            raise ValueError("Intelligence requires a JSON schema for structured output")
        schema = fmt["schema"]
    request = Request(model=model, messages=messages, max_output_tokens=max_tokens,
                      system=system, schema=schema, reasoning=thinking, timeout=timeout)
    complete = getattr(client, "complete", None)
    return complete(request) if complete else AnthropicMessages(client).complete(request)


class AnthropicMessages:
    """Adapter for Anthropic and older messages.create provider plugins."""
    def __init__(self, client):
        self.client = client
        self.provider_client = type(client).__module__ + "." + type(client).__name__

    def complete(self, request):
        args = dict(model=request.model, messages=request.messages,
                    max_tokens=request.max_output_tokens)
        if request.system:
            args["system"] = request.system
        if request.schema is not None:
            args["output_config"] = {"format": {"type": "json_schema", "schema": request.schema}}
        if request.reasoning is not None:
            args["thinking"] = request.reasoning
        if request.timeout is not None:
            args["timeout"] = request.timeout
        stream = getattr(self.client.messages, "stream", None)
        if stream is not None:
            with stream(**args) as result:
                return result.get_final_message()
        return self.client.messages.create(**args)


class OpenAIResponses:
    """Responses API adapter. The application sees the same result as any provider."""
    provider_client = "openai.responses"

    def __init__(self, client, reasoning_effort="medium"):
        if reasoning_effort not in {"low", "medium", "high", "xhigh", "max"}:
            raise ValueError("GPT-6 reasoning effort must be low, medium, high, xhigh or max")
        self.client = client
        self.reasoning_configuration = {"effort": reasoning_effort}

    @staticmethod
    def _messages(messages):
        result = []
        for message in messages:
            role, content = message["role"], message["content"]
            if isinstance(content, str):
                result.append({"role": role, "content": content})
                continue
            blocks = []
            for block in content:
                kind = block.get("type")
                if kind == "text":
                    blocks.append({"type": "input_text" if role != "assistant" else "output_text", "text": block["text"]})
                elif kind in {"image", "document"}:
                    source = block.get("source", {})
                    if source.get("type") != "base64":
                        raise ValueError("Intelligence attachments require inline base64 content")
                    data = "data:" + source["media_type"] + ";base64," + source["data"]
                    if kind == "image":
                        blocks.append({"type": "input_image", "image_url": data})
                    elif source["media_type"] == "application/pdf":
                        blocks.append({"type": "input_file", "filename": "document.pdf", "file_data": data})
                    else:
                        raise ValueError("Unsupported intelligence document format")
                else:
                    raise ValueError("Unsupported intelligence content block")
            result.append({"role": role, "content": blocks})
        return result

    def complete(self, request):
        reasoning = request.reasoning or self.reasoning_configuration
        if set(reasoning) != {"effort"} or reasoning["effort"] not in {"low", "medium", "high", "xhigh", "max"}:
            raise ValueError("OpenAI reasoning needs an explicit supported effort")
        args = dict(model=request.model, input=self._messages(request.messages),
                    max_output_tokens=request.max_output_tokens, store=False,
                    reasoning=reasoning)
        if request.system:
            args["instructions"] = request.system
        if request.schema is not None:
            args["text"] = {"format": {"type": "json_schema", "name": "intelligence_result",
                                       "strict": True, "schema": request.schema}}
        if request.timeout is not None:
            args["timeout"] = request.timeout
        stream = getattr(self.client.responses, "stream", None)
        if stream is not None:
            with stream(**args) as result:
                raw = result.get_final_response()
        else:
            raw = self.client.responses.create(**args)
        status = getattr(raw, "status", None)
        incomplete = getattr(getattr(raw, "incomplete_details", None), "reason", None)
        if status != "completed" and not (status == "incomplete" and incomplete == "max_output_tokens"):
            raise RuntimeError("OpenAI intelligence response did not complete")
        parts = []
        for item in raw.output:
            if item.type == "message":
                for block in item.content:
                    if block.type == "refusal":
                        raise RuntimeError("OpenAI intelligence request was refused")
                    if block.type == "output_text":
                        parts.append(Text(block.text))
        if not parts and status == "completed":
            raise RuntimeError("OpenAI intelligence response contains no text")
        usage = getattr(raw, "usage", None)
        measured = None if usage is None else Usage(
            input_tokens=getattr(usage, "input_tokens", None), output_tokens=getattr(usage, "output_tokens", None),
            cache_read_input_tokens=getattr(getattr(usage, "input_tokens_details", None), "cached_tokens", None))
        return Response(parts, raw.model, "max_tokens" if status == "incomplete" else "end_turn", measured)
