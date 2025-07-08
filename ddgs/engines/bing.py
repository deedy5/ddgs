from __future__ import annotations

from time import time
from typing import Any

from lxml import html

from ..base import BaseSearchEngine
from ..results import SearchResult


class Bing(BaseSearchEngine):
    """Bing search engine"""

    search_url = "https://www.bing.com/search"
    search_method = "GET"

    items_xpath = "//li[contains(@class, 'b_algo')]"
    elements_xpath = {
        "title": "./h2/a//text() | ./div[contains(@class, 'header')]/a/h2//text()",
        "href": "./h2/a/@href | ./div[contains(@class, 'header')]/a/@href",
        "body": ".//p//text()",
    }

    def build_params(self, **kwargs: Any) -> dict[str, Any]:
        payload = {
            "q": kwargs["query"],
        }
        if timelimit := kwargs.get("timelimit"):
            d = int(time() // 86400)
            code = f"ez5_{d - 365}_{d}" if timelimit == "y" else "ez" + {"d": "1", "w": "2", "m": "3"}[timelimit]
            payload["filters"] = f'ex1:"{code}"'
        return payload

    def extract_results(self, tree: html.Element) -> list[dict[str, Any]]:
        """Extract search results from lxml tree"""
        items = tree.xpath(self.items_xpath)
        results = []
        for item in items:
            result = SearchResult()
            for key, value in self.elements_xpath.items():
                data = item.xpath(value)
                data = "".join(x for x in data if x.strip())
                result.__setattr__(key, data)
            results.append(result.__dict__)
        return results
