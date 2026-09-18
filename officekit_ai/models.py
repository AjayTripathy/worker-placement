"""models — BYOM: the model-slot configuration (contract #10, models.json).

The Q2 ruling made bring-your-own-model a role-slot system, not a free choice:
slots (classify / intake / bench / adjudicate / verify) each name a provider
and model, and the harness — not the user's memory — enforces the constraints
(adjudicator never weaker than bench, generator never grades itself; the
ordering checks land with U2 when bench/adjudicate become real slots).

    office/models.json
    {"v": 1,
     "providers": {"anthropic": {"api_key_env": "ANTHROPIC_API_KEY"}},
     "slots": {"classify": {"provider": "anthropic", "model": "claude-haiku-4-5"},
               "intake":   {"provider": "anthropic", "model": "claude-opus-5"}}}

Rules:
  - SECRETS NEVER ENTER THE DOCUMENT. Providers reference credentials by
    environment-variable NAME (`api_key_env`); a models.json carrying an
    actual key material field is rejected loudly. This is what keeps the
    document uploadable at `officekit link` like every other contract.
  - No models.json -> the defaults above: the built-in anthropic provider
    keyed by ANTHROPIC_API_KEY. Today's behavior, zero configuration.
  - Providers are a REGISTRY (same pattern as sync connectors): the anthropic
    provider ships built in; a community OpenAI/local/vLLM provider is a
    plugin that calls @provider("name") and returns a client exposing
    messages.create with output_config structured outputs.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

SLOTS = ("classify", "intake", "bench", "adjudicate", "verify", "extract")

DEFAULTS = {
    "v": 1,
    "providers": {"anthropic": {"api_key_env": "ANTHROPIC_API_KEY"}},
    "slots": {"classify": {"provider": "anthropic", "model": "claude-haiku-4-5"},
              "intake": {"provider": "anthropic", "model": "claude-opus-5"},
              "extract": {"provider": "anthropic", "model": "claude-opus-5"},
              "bench": {"provider": "anthropic", "model": "claude-opus-5"},
              "adjudicate": {"provider": "anthropic", "model": "claude-opus-5"}},
}

# Fields that look like key material — never allowed in the document.
_SECRET_FIELDS = ("api_key", "key", "secret", "token", "password")

PROVIDERS = {}


def provider(name):
    """Register a provider factory: fn(cfg) -> client with .messages.create."""
    def deco(fn):
        PROVIDERS[name] = fn
        return fn
    return deco


def resolve_key(env="ANTHROPIC_API_KEY"):
    """Key resolution, in order: the named env var, then the conventional
    ~/.anthropic_key file (default env name only — a custom api_key_env means
    the user manages their own environment). The key value is returned to the
    SDK client and never logged, echoed, or written anywhere by this layer."""
    from officekit.runtime import hosted, credential
    if hosted():
        return credential(env)
    k = os.environ.get(env)
    if k:
        return k
    if env == "ANTHROPIC_API_KEY":
        try:
            k = (Path.home() / ".anthropic_key").read_text().strip()
            return k or None
        except OSError:
            return None
    return None


def key_source(env="ANTHROPIC_API_KEY"):
    """WHERE the key came from — for the integrations UI, which treats the AI
    key as an integration like any broker connection. Returns
    'env:<NAME>' | 'file:~/.anthropic_key' | None. Never returns key material."""
    from officekit.runtime import hosted, credential
    if hosted():
        return "office:encrypted" if credential(env) else None
    if os.environ.get(env):
        return f"env:{env}"
    if env == "ANTHROPIC_API_KEY":
        try:
            if (Path.home() / ".anthropic_key").read_text().strip():
                return "file:~/.anthropic_key"
        except OSError:
            pass
    return None


@provider("anthropic")
def _anthropic(cfg):
    env = cfg.get("api_key_env", "ANTHROPIC_API_KEY")
    key = resolve_key(env)
    if not key:
        raise RuntimeError(f"models: provider 'anthropic' needs the {env} environment "
                           f"variable (or ~/.anthropic_key)")
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("models: the `anthropic` SDK is not installed (pip install officekit[ai])")
    return anthropic.Anthropic(api_key=key, timeout=120.0, max_retries=0)


def validate(cfg):
    """Return problems (empty = valid). The secrets rule is the load-bearing one."""
    p = []
    if not isinstance(cfg, dict) or cfg.get("v") != 1:
        return ["models: v must be 1"]
    for name, pc in (cfg.get("providers") or {}).items():
        for f in _SECRET_FIELDS:
            if f in pc:
                p.append(f"models: provider '{name}' carries '{f}' — secrets never enter "
                         f"the document; reference an environment variable via api_key_env")
    for slot, sc in (cfg.get("slots") or {}).items():
        if slot not in SLOTS:
            p.append(f"models: unknown slot '{slot}' (slots: {', '.join(SLOTS)})")
        elif not sc.get("provider") or not sc.get("model"):
            p.append(f"models: slot '{slot}' needs provider and model")
        elif sc["provider"] not in (cfg.get("providers") or {}):
            p.append(f"models: slot '{slot}' names undeclared provider '{sc['provider']}'")
    return p


def load(folder=None):
    """The effective config: models.json overlaid on the defaults (unnamed
    slots/providers fall back). Raises on an invalid document — a malformed
    model config must never be silently ignored."""
    cfg = {"v": 1,
           "providers": dict(DEFAULTS["providers"]),
           "slots": {k: dict(v) for k, v in DEFAULTS["slots"].items()}}
    if folder is not None:
        path = Path(folder) / "models.json"
        if path.exists():
            user = json.loads(path.read_text())
            probs = validate(user)
            if probs:
                raise ValueError("models.json invalid: " + "; ".join(probs))
            cfg["providers"].update(user.get("providers") or {})
            cfg["slots"].update(user.get("slots") or {})
    return cfg


def resolve(slot, folder=None):
    """-> (provider_name, provider_cfg, model) for a slot."""
    cfg = load(folder)
    sc = cfg["slots"].get(slot)
    if not sc:
        raise RuntimeError(f"models: no configuration for slot '{slot}'")
    return sc["provider"], cfg["providers"][sc["provider"]], sc["model"]


def client_for(slot, folder=None):
    """-> (client, model) for a slot, via the provider registry."""
    name, pcfg, model = resolve(slot, folder)
    factory = PROVIDERS.get(name)
    if factory is None:
        raise RuntimeError(f"models: provider '{name}' is not registered — "
                           f"install its plugin package")
    return factory(pcfg), model


def slot_available(slot, folder=None):
    """True iff the slot's provider can actually construct a client — the
    per-slot generalization of available(). Never raises."""
    try:
        client_for(slot, folder)
        return True
    except Exception:
        return False
