"""Grokipedia text search engine."""

import json
import logging
from typing import Any

from ddgs.base import BaseSearchEngine
from ddgs.results import TextResult

logger = logging.getLogger(__name__)


class Grokipedia(BaseSearchEngine[TextResult]):
    """Grokipedia text search engine."""

    name = "grokipedia"
    category = "text"
    provider = "grokipedia"
    priority = 1.9

    search_url = "https://grokipedia.com/api/typeahead"
    search_method = "GET"

    def build_payload(
        self,
        query: str,
        region: str,  # noqa: ARG002
        safesearch: str,  # noqa: ARG002
        timelimit: str | None,  # noqa: ARG002
        page: int = 1,  # noqa: ARG002
        **kwargs: str,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build a payload for the search request."""
        payload: dict[str, Any] = {"query": query, "limit": "1"}
        return payload

    def extract_results(self, html_text: str) -> list[TextResult]:
        """Extract search results from html text."""
        json_data = json.loads(html_text)
        items = json_data.get("results", [])
        if not items:
            return []

        result = TextResult()
        result.title = items[0].get("title", "").strip("_")
        body = items[0].get("snippet", "")
        result.body = body.split("\n\n", 1)[1] if "\n\n" in body else body
        result.href = f"https://grokipedia.com/page/{items[0]['slug']}"
        return [result]
