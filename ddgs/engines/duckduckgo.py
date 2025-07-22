from __future__ import annotations

from typing import Any

from ..base import BaseSearchEngine
from ..results import TextResult


class Duckduckgo(BaseSearchEngine[TextResult]):
    """Duckduckgo search engine"""

    name = "duckduckgo"
    category = "text"
    provider = "bing"
    disabled = True  # Disabled until ratelimit is fixed

    search_url = "https://html.duckduckgo.com/html/"
    search_method = "POST"

    items_xpath = "//div[contains(@class, 'body')]"
    elements_xpath = {"title": ".//h2//text()", "href": "./a/@href", "body": "./a//text()"}

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        payload = {"q": query, "b": "", "l": region}
        if page > 1:
            payload["s"] = f"{10 + (page - 2) * 15}"
        if timelimit:
            payload["df"] = timelimit
        return payload
