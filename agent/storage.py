"""Atomic JSON storage with process and thread serialization; no silent resets."""
from __future__ import annotations

import contextlib
import copy
import json
import os
from pathlib import Path
import tempfile
import threading

_locks: dict[str, threading.RLock] = {}
_guard = threading.Lock()
_local = threading.local()


@contextlib.contextmanager
def file_lock(path: Path):
    key = str(Path(path).resolve())
    with _guard:
        lock = _locks.setdefault(key, threading.RLock())
    with lock:
        held = getattr(_local, "held", set())
        if key in held:
            yield
            return
        lock_path = Path(key + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as handle:
            handle.seek(0, 2)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX)
            _local.held = held | {key}
            try:
                yield
            finally:
                _local.held = held
                handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)


def read_json(path: Path, default):
    path = Path(path)
    if not path.exists():
        return copy.deepcopy(default)
    # A corrupt file is an operational error, never a new empty personality/budget.
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with file_lock(path):
        fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def serialized(path_attribute):
    """Serialize an entire read/modify/write method, including nested methods."""
    import functools
    def decorate(fn):
        @functools.wraps(fn)
        def run(self, *args, **kwargs):
            with file_lock(getattr(self, path_attribute)):
                return fn(self, *args, **kwargs)
        return run
    return decorate
