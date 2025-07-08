from __future__ import annotations

from .bing import Bing
from .duckduckgo import Duckduckgo
from .google import Google

search_engines_dict: dict[str, type[Bing | Duckduckgo | Google]] = {
    "duckduckgo": Duckduckgo,
    "bing": Bing,
    "google": Google,
}
