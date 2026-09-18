"""Request-scoped capabilities; a hosted office never inherits machine secrets."""
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

_hosted_folder = ContextVar('hosted_office_folder', default=None)


def hosted():
    return _hosted_folder.get() is not None


@contextmanager
def hosted_office(folder):
    token = _hosted_folder.set(Path(folder).resolve())
    try:
        yield
    finally:
        _hosted_folder.reset(token)


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
