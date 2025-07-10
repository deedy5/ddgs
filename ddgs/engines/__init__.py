from __future__ import annotations

from .bing import Bing
from .duckduckgo import Duckduckgo
from .duckduckgo_images import DuckduckgoImages
from .duckduckgo_news import DuckduckgoNews
from .duckduckgo_videos import DuckduckgoVideos
from .google import Google

text_engines_dict: dict[str, type[Bing | Duckduckgo | Google]] = {
    "duckduckgo": Duckduckgo,
    "bing": Bing,
    "google": Google,
}

images_engines_dict: dict[str, type[DuckduckgoImages]] = {
    "duckduckgo_images": DuckduckgoImages,
}

news_engines_dict: dict[str, type[DuckduckgoNews]] = {
    "duckduckgo_news": DuckduckgoNews,
}

videos_engines_dict: dict[str, type[DuckduckgoVideos]] = {
    "duckduckgo_videos": DuckduckgoVideos,
}
