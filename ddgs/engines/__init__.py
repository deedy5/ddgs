from __future__ import annotations

from ..base import BaseSearchEngine
from .bing import Bing
from .duckduckgo import Duckduckgo
from .duckduckgo_images import DuckduckgoImages
from .duckduckgo_news import DuckduckgoNews
from .duckduckgo_videos import DuckduckgoVideos
from .google import Google
from .yandex import Yandex

ENGINES: dict[str, dict[str, type[BaseSearchEngine]]] = {
    "text": {
        "google": Google,
        "bing": Bing,
        "yandex": Yandex,
        "duckduckgo": Duckduckgo,
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
