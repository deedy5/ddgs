from __future__ import annotations

import importlib
import inspect
import pkgutil
from collections import defaultdict
from typing import Any

from ..base import BaseSearchEngine

"""
# from .bing import Bing
from .brave import Brave
from .duckduckgo import Duckduckgo
from .duckduckgo_images import DuckduckgoImages
from .duckduckgo_news import DuckduckgoNews
from .duckduckgo_videos import DuckduckgoVideos
from .google import Google
from .mojeek import Mojeek
from .mullvad_leta import MullvadLetaBrave, MullvadLetaGoogle
from .wikipedia import Wikipedia
from .yahoo import Yahoo
from .yandex import Yandex

ENGINES: dict[str, dict[str, type[BaseSearchEngine[Any]]]] = {
    "text": {
        "bing": Bing,
        "brave": Brave,
        "duckduckgo": Duckduckgo,  # bing
        "google": Google,
        "mojeek": Mojeek,
        "mullvad_brave": MullvadLetaBrave,  # brave
        "mullvad_google": MullvadLetaGoogle,  # google
        "yahoo": Yahoo,  # bing
        "yandex": Yandex,
        "wikipedia": Wikipedia,
    },
    "images": {
        "duckduckgo": DuckduckgoImages,
    },
    "news": {
        "duckduckgo": DuckduckgoNews,
    },
    "videos": {
        "duckduckgo": DuckduckgoVideos,
    },
}
"""

# Auto‐built engines registry:
# ENGINES[category][name] = class
ENGINES: dict[str, dict[str, type[BaseSearchEngine[Any]]]] = defaultdict(dict)

package_name = __name__
package = importlib.import_module(package_name)

for finder, modname, _ispkg in pkgutil.iter_modules(package.__path__, package_name + "."):
    module_path = finder.path if hasattr(finder, "path") else finder
    module = importlib.import_module(modname)
    for _, cls in inspect.getmembers(module, inspect.isclass):
        # 1) must subclass BaseSearchEngine (but not the base itself)
        if not issubclass(cls, BaseSearchEngine) or cls is BaseSearchEngine:
            continue

        # 2) skip any class whose name starts with "Base"
        if cls.__name__.startswith("Base"):
            continue

        # 3) skip disabled engines
        if getattr(cls, "disabled", True):
            continue

        # 3) ensure they provided name & category
        name = getattr(cls, "name", None)
        category = getattr(cls, "category", None)
        if not isinstance(name, str) or not isinstance(category, str):
            raise RuntimeError(
                f"{cls.__module__}.{cls.__qualname__} must define class attributes 'name: str' and 'category: str'."
            )

        ENGINES[category][name] = cls

# freeze into normal dicts
ENGINES = {cat: dict(m) for cat, m in ENGINES.items()}
