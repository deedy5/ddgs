from __future__ import annotations

from random import randint
from typing import Any

from ..base import BaseSearchEngine
from ..results import TextResult


class Mojeek(BaseSearchEngine[TextResult]):
    """Mojeek search engine"""

    name = "mojeek"
    category = "text"
    provider = "mojeek"

    search_url = "https://www.mojeek.com/search"
    search_method = "GET"

    items_xpath = "//ul[contains(@class, 'results')]/li"
    elements_xpath = {
        "title": ".//h2//text()",
        "href": ".//h2/a/@href",
        "body": ".//p[@class='s']//text()",
    }

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        country, lang = region.lower().split("-")
        payload = {
            "q": query,
            "arc": country,
            "lb": lang,
            "tlen": f"{randint(118, 128)}",  # Title length limit (max=128)
            "dlen": f"{randint(502, 512)}",  # Description length limit (max=512)
        }
        if safesearch == "on":
            payload["safe"] = "1"
        if page > 1:
            payload["s"] = f"{(page - 1) * 10 + 1}"
        return payload

    def extract_results(self, html_text: str) -> list[TextResult]:
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
            results.append(result)
        return results
