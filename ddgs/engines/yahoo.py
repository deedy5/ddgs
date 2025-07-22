from __future__ import annotations

import string
from random import choice
from typing import Any
from urllib.parse import unquote_plus

from ..base import BaseSearchEngine
from ..results import TextResult

_TOKEN_CHARS = string.ascii_letters + string.digits + "-_"


def _random_token(length: int) -> str:
    """Generate a random token."""
    return "".join(choice(_TOKEN_CHARS) for _ in range(length))


def extract_url(u: str) -> str:
    t = u.split("/RU=", 1)[1]
    return unquote_plus(t.split("/RK=", 1)[0].split("/RS=", 1)[0])


class Yahoo(BaseSearchEngine[TextResult]):
    """Yahoo search engine"""

    name = "yahoo"
    category = "text"
    provider = "bing"

    search_url = "https://search.yahoo.com/search"
    search_method = "GET"

    items_xpath = "//div[contains(@class, 'relsrch')]"
    elements_xpath = {
        "title": ".//div[contains(@class, 'Title')]//h3//text()",
        "href": ".//div[contains(@class, 'Title')]//a/@href",
        "body": ".//div[contains(@class, 'Text')]//text()",
    }

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        self.search_url = f"https://search.yahoo.com/search;_ylt={_random_token(24)};_ylu={_random_token(47)}"
        payload = {"p": query}
        if page > 1:
            payload["b"] = f"{(page - 1) * 7 + 1}"
        if timelimit:
            payload["btf"] = timelimit
        return payload

    def post_extract_results(self, results: list[TextResult]) -> list[TextResult]:
        """Post-process search results"""
        post_results = []
        for result in results:
            if result.href.startswith("https://www.bing.com/aclick?"):
                continue
            if "/RU=" in result.href:
                result.href = extract_url(result.href)
            post_results.append(result)
        return post_results
