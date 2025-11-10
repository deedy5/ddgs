"""Duckduckgo news search engine implementation."""

import json
from collections.abc import Mapping
from typing import Any, ClassVar

from ddgs.base import BaseSearchEngine
from ddgs.results import NewsResult
from ddgs.utils import _extract_vqd


class DuckduckgoNews(BaseSearchEngine[NewsResult]):
    """Duckduckgo news search engine."""

    name = "duckduckgo"
    category = "news"
    provider = "bing"

    search_url = "https://duckduckgo.com/news.js"
    search_method = "GET"

    elements_replace: ClassVar[Mapping[str, str]] = {
        "date": "date",
        "title": "title",
        "excerpt": "body",
        "url": "url",
        "image": "image",
        "source": "source",
    }

    def _get_vqd(self, query: str) -> str:
        """Get vqd value for a search query using DuckDuckGo."""
        resp_content = self.http_client.request("GET", "https://duckduckgo.com", params={"q": query}).content
        return _extract_vqd(resp_content, query)

    def build_payload(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: str,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build a payload for the search request."""
        safesearch_base = {"on": "1", "moderate": "-1", "off": "-2"}
        payload = {
            "l": region,
            "o": "json",
            "noamp": "1",
            "q": query,
            "vqd": self._get_vqd(query),
            "p": safesearch_base[safesearch.lower()],
        }
        if timelimit:
            payload["df"] = timelimit
        if page > 1:
            payload["s"] = f"{(page - 1) * 30}"
        return payload

    def extract_results(self, html_text: str) -> list[NewsResult]:
        """Extract search results from lxml tree."""
        json_data = json.loads(html_text)
        items = json_data.get("results", [])
        results = []
        for item in items:
            result = NewsResult()
            for key, value in self.elements_replace.items():
                data = item.get(key)
                result.__setattr__(value, data)
            results.append(result)
        return results
