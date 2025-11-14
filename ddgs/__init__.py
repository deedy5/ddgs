"""DDGS | Dux Distributed Global Search.

A metasearch library that aggregates results from diverse web search services.
"""

import importlib
import logging
import threading
from typing import TYPE_CHECKING, Any

__version__ = "9.9.1"
__all__ = ("DDGS",)

if TYPE_CHECKING:
    from .ddgs import DDGS

# A do-nothing logging handler
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger("ddgs").addHandler(logging.NullHandler())


class _ProxyMeta(type):
    _lock: threading.Lock = threading.Lock()
    _real_cls: type["DDGS"] | None = None

    @classmethod
    def _load_real(cls) -> type["DDGS"]:
        if cls._real_cls is None:
            with cls._lock:
                if cls._real_cls is None:
                    cls._real_cls = importlib.import_module(".ddgs", package=__name__).DDGS
                    globals()["DDGS"] = cls._real_cls
        return cls._real_cls

    def __call__(cls, *args: Any, **kwargs: Any) -> "DDGS":  # noqa: ANN401
        real = type(cls)._load_real()
        return real(*args, **kwargs)

    def __getattr__(cls, name: str) -> Any:  # noqa: ANN401
        return getattr(type(cls)._load_real(), name)

    def __dir__(cls) -> list[str]:
        base = set(super().__dir__())
        loaded_names = set(dir(type(cls)._load_real()))
        return sorted(base | (loaded_names - base))


class DDGS(metaclass=_ProxyMeta):  # type: ignore[no-redef]
    """Proxy class for lazy-loading the real DDGS implementation."""
