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

    name = "wikipedia"
    category = "text"
    provider = "wikipedia"
    priority = 2

    search_url = "https://{lang}.wikipedia.org/w/api.php?action=opensearch&search={query}"
    search_method = "GET"

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        country, lang = region.lower().split("-")
        encoded_query = quote(query)
        self.search_url = (
            f"https://{lang}.wikipedia.org/w/api.php?action=opensearch&profile=fuzzy&limit=1&search={encoded_query}"
        )
        payload: dict[str, Any] = {}
        self.lang = lang  # used in extract_results
        return payload

    def extract_results(self, html_text: str) -> list[TextResult]:
        """Extract search results from html text"""
        json_data = json_loads(html_text)
        if not json_data[1]:
            return []

        result = TextResult()
        result.title = json_data[1][0]
        result.href = json_data[3][0]

        # Add body
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
                logger.warning(f"Error getting body from Wikipedia for title={result.title}:  {ex}")

        if "may refer to:" in result.body:
            return []

        return [result]
