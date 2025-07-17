from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

from ..base import BaseSearchEngine
from ..results import TextResult
from ..utils import json_loads

logger = logging.getLogger(__name__)


class Wikipedia(BaseSearchEngine[TextResult]):
    """Wikipedia text search engine"""

    search_url = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{query}"
    search_method = "GET"

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        country, lang = region.lower().split("-")
        encoded_query = quote(query)
        self.search_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded_query}"
        payload: dict[str, Any] = {}
        self.lang = lang  # used in extract_results
        return payload

    def extract_results(self, html_text: str) -> list[TextResult]:
        """Extract search results from html text"""
        json_data = json_loads(html_text)
        result = TextResult()
        result.title = json_data.get("title")
        result.href = json_data.get("content_urls", {}).get("desktop", {}).get("page")
        result.body = json_data.get("extract")

        # Add more robust summary
        encoded_query = quote(result.title)
        resp_data = self.request(
            "GET",
            f"https://{self.lang}.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&titles={encoded_query}&explaintext=0&exintro=0&redirects=1",
        )
        if resp_data:
            json_data = json_loads(resp_data)
            try:
                result.body = list(json_data["query"]["pages"].values())[0]["extract"]
            except KeyError as ex:
                logger.warning(f"Error getting robust summary from Wikipedia for title={result.title}:  {ex}")

        return [result]
