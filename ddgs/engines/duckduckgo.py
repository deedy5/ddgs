from __future__ import annotations

from typing import Any

from lxml import html

from ..base import BaseSearchEngine
from ..results import SearchResult


class Duckduckgo(BaseSearchEngine):
    """Duckduckgo search engine"""

    search_url = "https://html.duckduckgo.com/html/"
    search_method = "POST"

    items_xpath = "//div[contains(@class, 'body')]"
    elements_xpath = {"title": ".//h2//text()", "href": "./a/@href", "body": "./a//text()"}

    def build_payload(self, query: str, region: str | None, timelimit: str | None, page: int) -> dict[str, Any]:
        payload = {"q": query, "b": ""}
        if region:
            payload["l"] = region
        if page > 1:
            payload["s"] = f"{10 + (page - 2) * 15}"
        if timelimit:
            payload["df"] = timelimit
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
