"""Frozen call configuration and measured usage, without prompts or credentials."""
import hashlib
import json
from pathlib import Path
import time


def protocol_hash():
    import officekit_agents
    root = Path(officekit_agents.__file__).parent
    documents = {str(p.relative_to(root)): p.read_text() for pattern in ('directives/*.md', 'templates/court_*.md') for p in sorted(root.glob(pattern))}
    for name in ('court.py', 'strategy_proposal.py'):
        documents['officekit_ai/' + name] = (Path(__file__).parent / name).read_text()
    return hashlib.sha256(json.dumps(documents, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def invoke(client, **request):
    from officekit_ai.court import _create
    protocol = protocol_hash()
    started = time.monotonic()
    response = _create(client, **request)
    usage = getattr(response, 'usage', None)
    measured = {key: getattr(usage, key, None) for key in ('input_tokens', 'output_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens')}
    return response, {'requested_model': request['model'], 'resolved_model': getattr(response, 'model', None) or 'unknown',
                      'provider_client': getattr(client, 'provider_client', type(client).__module__ + '.' + type(client).__name__),
                      'reasoning_configuration': request.get('thinking') or 'provider_default',
                      'protocol_hash': protocol, 'latency_s': round(time.monotonic() - started, 3),
                      'usage': measured, 'cost_usd': None}
