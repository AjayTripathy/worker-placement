"""Reentrant cross-process transaction barrier for local office snapshots."""
from contextlib import contextmanager
from functools import wraps
import inspect
import os
from pathlib import Path
import threading

_locks = {}
_guard = threading.Lock()
_local = threading.local()

@contextmanager
def locked(folder):
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    key = str(folder)
    with _guard:
        lock = _locks.setdefault(key, threading.RLock())
    with lock:
        active = getattr(_local, 'active', set())
        if key in active:
            yield
            return
        with (folder/'.office-write.lock').open('a+b') as stream:
            if os.name == 'nt':
                import msvcrt
                stream.seek(0); stream.write(b'0'); stream.flush(); stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX)
            _local.active = active | {key}
            try:
                yield
            finally:
                _local.active = active
                if os.name == 'nt':
                    stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(stream, fcntl.LOCK_UN)


def transaction(argument='folder', parent=False):
    def decorate(fn):
        signature = inspect.signature(fn)
        @wraps(fn)
        def wrapped(*args, **kwargs):
            folder = signature.bind(*args, **kwargs).arguments[argument]
            with locked(Path(folder).parent if parent else folder):
                return fn(*args, **kwargs)
        return wrapped
    return decorate
