"""Bing images search engine implementation."""

import json
from typing import Any

from ddgs.base import BaseSearchEngine
from ddgs.results import ImagesResult


class BingImages(BaseSearchEngine[ImagesResult]):
    """Bing images search engine."""

    name = "bing"
    category = "images"
    provider = "bing"

    search_url = "https://www.bing.com/images/async"
    search_method = "GET"

    items_xpath = "//div[./div[@class='imgpt']/a[@m] and ./div[@class='infopt']]"

    def build_payload(
        self,
        query: str,
        region: str,  # noqa: ARG002
        safesearch: str,  # noqa: ARG002
        timelimit: str | None,
        page: int = 1,
        **kwargs: str,
    ) -> dict[str, Any]:
        """Build a payload for the search request."""
        count = max(int(kwargs.get("max_results", 10)), 35)
        payload = {
            "q": query,
            "async": "1",
            "first": str((page - 1) * count + 1),
            "count": str(count),
        }
        if timelimit:
            payload["qft"] = (
                f"filterui:age-lt{ ({'day': 1440, 'week': 10080, 'month': 44640, 'year': 525600}[timelimit]) }"
            )
        return payload

    def extract_results(self, html_text: str) -> list[ImagesResult]:
        """Extract search results from html text."""
        html_text = self.pre_process_html(html_text)
        tree = self.extract_tree(html_text)
        items = tree.xpath(self.items_xpath)
        results = []
        for item in items:
            result = ImagesResult()
            if metadata := item.xpath(".//a[@class='iusc']/@m"):
                m = json.loads(metadata[0])
                result.title = m.get("t")
                result.image = m.get("murl")
                result.thumbnail = m.get("turl")
                result.url = m.get("purl")
                if dimension := item.xpath(".//div[contains(@class, 'img_info')][./span]/span[@class='nowrap']/text()"):
                    width, height = dimension[0].replace("×", "x").split("x")  # noqa: RUF001
                    result.width = width.strip()
                    result.height = height.split()[0].strip()
                if source := item.xpath(".//div[@class='lnkw']//a/text()"):
                    result.source = source[0]
                results.append(result)
        return results
