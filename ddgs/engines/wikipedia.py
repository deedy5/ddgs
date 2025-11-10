"""Wikipedia text search engine."""

import json
import logging
from typing import Any
from urllib.parse import quote

from ddgs.base import BaseSearchEngine
from ddgs.results import TextResult

logger = logging.getLogger(__name__)


class Wikipedia(BaseSearchEngine[TextResult]):
    """Wikipedia text search engine."""

    name = "wikipedia"
    category = "text"
    provider = "wikipedia"
    priority = 2

    search_url = "https://{lang}.wikipedia.org/w/api.php?action=opensearch&search={query}"
    search_method = "GET"

    def build_payload(
        self,
        query: str,
        region: str,
        safesearch: str,  # noqa: ARG002
        timelimit: str | None,  # noqa: ARG002
        page: int = 1,  # noqa: ARG002
        **kwargs: str,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build a payload for the search request."""
        _country, lang = region.lower().split("-")
        encoded_query = quote(query)
        self.search_url = (
            f"https://{lang}.wikipedia.org/w/api.php?action=opensearch&profile=fuzzy&limit=1&search={encoded_query}"
        )
        payload: dict[str, Any] = {}
        self.lang = lang  # used in extract_results
        return payload

    def extract_results(self, html_text: str) -> list[TextResult]:
        """Extract search results from html text."""
        json_data = json.loads(html_text)
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
            json_data = json.loads(resp_data)
            result.body = next(iter(json_data["query"]["pages"].values())).get("extract", "")
        if "may refer to:" in result.body:
            return []

        return [result]
