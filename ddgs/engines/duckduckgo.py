from __future__ import annotations

from typing import Any

from lxml import html

from ..base import BaseSearchEngine
from ..results import SearchResult


class Duckduckgo(BaseSearchEngine):
    """Duckdcukgo search engine"""

    search_url = "https://html.duckduckgo.com/html/"
    search_method = "POST"

    items_xpath = "//div[contains(@class, 'body')]"
    elements_xpath = {"title": ".//h2//text()", "href": "./a/@href", "body": "./a//text()"}

    def build_payload(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "q": kwargs["query"],
            "s": "0",
            "o": "json",
            "api": "d.js",
            "vqd": "",
            "kl": "wt-wt",
            "bing_market": "wt-wt",
        }

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
