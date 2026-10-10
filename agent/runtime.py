"""Explicit offline / preview / live execution boundaries."""
from contextlib import contextmanager
from contextvars import ContextVar
import os

MODE = ContextVar("execution_mode", default=os.environ.get("SEOYEON_MODE", "live"))


@contextmanager
def execution_mode(mode):
    if mode not in {"offline", "preview", "live"}:
        raise ValueError("Unknown execution mode")
    token = MODE.set(mode)
    try:
        yield
    finally:
        MODE.reset(token)


def require_network():
    if MODE.get() == "offline":
        raise RuntimeError("Offline mode forbids network calls")


def may_publish():
    return MODE.get() == "live"
