class SignalosError(Exception):
    pass

class SourceError(SignalosError):
    pass

class GapError(SignalosError):
    pass

class RuleError(SignalosError):
    pass

class StoreError(SignalosError):
    pass

class LLMError(SignalosError):
    pass

class ConfigError(SignalosError):
    pass
