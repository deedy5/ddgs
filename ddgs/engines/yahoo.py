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


class Yahoo(BaseSearchEngine):
    """Yahoo search engine"""

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

    def extract_results(self, html_text: str) -> list[dict[str, Any]]:
        """Extract search results from html text"""
        tree = self.extract_tree(html_text)
        items = tree.xpath(self.items_xpath)
        results = []
        for item in items:
            result = TextResult()
            for key, value in self.elements_xpath.items():
                data = item.xpath(value)
                data = "".join(x for x in data if x.strip())
                if key == "href" and "/RU=" in data:
                    data = extract_url(data)
                result.__setattr__(key, data)
            results.append(result.__dict__)
        return results
