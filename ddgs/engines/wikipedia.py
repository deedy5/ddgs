from __future__ import annotations

from typing import Any

from ..base import BaseSearchEngine
from ..results import TextResult
from ..utils import json_loads


class Wikipedia(BaseSearchEngine):
    """Wikipedia text search engine"""

    search_url = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{query}"
    search_method = "GET"

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        country, lang = region.lower().split("-")
        self.search_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{query}"
        payload: dict[str, Any] = {}
        return payload

    def extract_results(self, html_text: str) -> list[dict[str, Any]]:
        """Extract search results from html text"""
        json_data = json_loads(html_text)
        result = TextResult()
        result.title = json_data.get("title")
        result.href = json_data.get("content_urls", {}).get("desktop", {}).get("page")
        result.body = json_data.get("extract")
        results: list[dict[str, Any]] = list([result.__dict__])
        return results
