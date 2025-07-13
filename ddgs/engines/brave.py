from __future__ import annotations

from typing import Any

from ..base import BaseSearchEngine
from ..results import TextResult


class Brave(BaseSearchEngine):
    """Brave search engine"""

    search_url = "https://search.brave.com/search"
    search_method = "GET"

    items_xpath = "//div[@data-type='web']"
    elements_xpath = {
        "title": ".//div[contains(@class, 'title')]//text()",
        "href": "./a/@href",
        "body": ".//div[contains(@class, 'description')]//text()",
    }

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        payload = {"q": query, "source": "web"}
        country, lang = region.lower().split("-")
        cookies = {country: country, "useLocation": "0"}
        if safesearch != "moderate":
            cookies["safesearch"] = "strict" if safesearch == "on" else "off"
        self.http_client.client.set_cookies("https://search.brave.com", cookies)
        if timelimit:
            payload["tf"] = {"d": "pd", "w": "pw", "m": "pm", "y": "py"}[timelimit]
        if page > 1:
            payload["offset"] = f"{page - 1}"
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
