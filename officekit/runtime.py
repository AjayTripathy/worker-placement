"""Request-scoped capabilities; a hosted office never inherits machine secrets."""
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

_credentials = ContextVar("office_credentials", default={})
_enqueue = ContextVar("office_enqueue", default=None)
_checkpoint = ContextVar("office_checkpoint", default=None)
_research_exchange = ContextVar("office_research_exchange", default=None)
_research_library = ContextVar("office_research_library", default=None)


def research_library():
    return _research_library.get()


def research_exchange():
    return _research_exchange.get()


def credential(name):
    if hosted():
        return _credentials.get().get(name)
    import os
    return os.environ.get(name)


def enqueue_proposal(pid):
    callback = _enqueue.get()
    if callback is None:
        raise ValueError("Research workers are not configured. Try again later.")
    callback(pid)


def checkpoint():
    callback = _checkpoint.get()
    if callback:
        callback()


_hosted_folder = ContextVar('hosted_office_folder', default=None)


def hosted():
    return _hosted_folder.get() is not None


@contextmanager
def hosted_office(folder, credentials=None, enqueue=None, checkpoint=None, research_exchange=None, research_library=None):
    key_token = _credentials.set(dict(credentials or {}))
    queue_token = _enqueue.set(enqueue)
    save_token = _checkpoint.set(checkpoint)
    research_token = _research_exchange.set(research_exchange)
    library_token = _research_library.set(research_library)
    token = _hosted_folder.set(Path(folder).resolve())
    try:
        yield
    finally:
        _hosted_folder.reset(token)
        _credentials.reset(key_token)
        _enqueue.reset(queue_token)
        _checkpoint.reset(save_token)
        _research_exchange.reset(research_token)
        _research_library.reset(library_token)


def import_path(value):
    """Hosted imports may read only an explicitly retained relative CSV."""
    root = _hosted_folder.get()
    if root is None:
        return Path(value)
    from officekit.migration import safe_path
    path = Path(str(value))
    if not safe_path(str(value)) or path.suffix.lower() != '.csv':
        raise ValueError('This import refers to a file on your local machine. Retain its CSV in the office before editing online.')
    target = (root / path).resolve()
    if root not in target.parents or not target.is_file():
        raise ValueError('The CSV needed to rebuild this office was not migrated. Retain it in the office and upload again.')
    return target
