from __future__ import annotations

from ..base import BaseSearchEngine
from .bing import Bing
from .brave import Brave
from .duckduckgo import Duckduckgo
from .duckduckgo_images import DuckduckgoImages
from .duckduckgo_news import DuckduckgoNews
from .duckduckgo_videos import DuckduckgoVideos
from .google import Google
from .mojeek import Mojeek
from .wikipedia import Wikipedia
from .yahoo import Yahoo
from .yandex import Yandex

ENGINES: dict[str, dict[str, type[BaseSearchEngine]]] = {
    "text": {
        "wikipedia": Wikipedia,
        "google": Google,
        "bing": Bing,
        "brave": Brave,
        "mojeek": Mojeek,
        "yahoo": Yahoo,
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
