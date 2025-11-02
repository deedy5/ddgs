"""DDGS | Dux Distributed Global Search.

A metasearch library that aggregates results from diverse web search services.
"""

from __future__ import annotations

import importlib
import logging
import threading
from typing import TYPE_CHECKING, Any

__version__ = "9.6.1"
__all__ = ("DDGS",)

if TYPE_CHECKING:
    from .ddgs import DDGS as _DDGS

# A do-nothing logging handler
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger("ddgs").addHandler(logging.NullHandler())


class _DDGSLazyLoader:
    def __init__(self) -> None:
        self._obj: type[_DDGS] | None = None
        self._lock: threading.Lock = threading.Lock()

    def _load(self) -> type[_DDGS]:
        if self._obj is None:
            with self._lock:
                if self._obj is None:
                    real = importlib.import_module(".ddgs", package=__name__).DDGS
                    globals()["DDGS"] = real
                    self._obj = real
        return self._obj

    def __call__(self, *args: Any, **kwargs: Any) -> _DDGS:
        return self._load()(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._load(), name)

    def __dir__(self) -> list[str]:
        base = set(super().__dir__())
        loaded_names = set(dir(self._load()))
        return sorted(base | (loaded_names - base))


DDGS: type[_DDGS] | _DDGSLazyLoader = _DDGSLazyLoader()
