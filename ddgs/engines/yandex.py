from __future__ import annotations

from random import randint
from typing import Any

from ..base import BaseSearchEngine
from ..results import TextResult


class Yandex(BaseSearchEngine):
    """Yandex search engine"""

    search_url = "https://yandex.com/search/site/"
    search_method = "GET"

    items_xpath = "//li[contains(@class, 'serp-item')]"
    elements_xpath = {
        "title": ".//h3//text()",
        "href": ".//h3//a/@href",
        "body": ".//div[contains(@class, 'text')]//text()",
    }

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        payload = {
            "text": query,
            "web": "1",
            "searchid": f"{randint(1000000, 9999999)}",
        }
        if page > 1:
            payload["p"] = f"{page - 1}"
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
                result.__setattr__(key, data)
            results.append(result.__dict__)
        return results
