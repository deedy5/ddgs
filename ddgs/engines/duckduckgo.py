"""Duckduckgo search engine implementation."""

from collections.abc import Mapping
from typing import Any, ClassVar
from urllib.parse import parse_qs, urlsplit

from ddgs.base import BaseSearchEngine
from ddgs.results import TextResult


class Duckduckgo(BaseSearchEngine[TextResult]):
    """Duckduckgo search engine."""

    name = "duckduckgo"
    category = "text"
    provider = "bing"

    search_url = "https://html.duckduckgo.com/html/"
    search_method = "GET"

    items_xpath = "//div[contains(@class, 'body')]"
    elements_xpath: ClassVar[Mapping[str, str]] = {"title": ".//h2//text()", "href": "./a/@href", "body": "./a//text()"}

    def build_payload(
        self,
        query: str,
        region: str,
        safesearch: str,  # noqa: ARG002
        timelimit: str | None,
        page: int = 1,
        **kwargs: str,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build a payload for the search request."""
        payload = {"q": query, "b": "", "l": region}
        if page > 1:
            payload["s"] = f"{10 + (page - 2) * 15}"
        if timelimit:
            payload["df"] = timelimit
        return payload

    def post_extract_results(self, results: list[TextResult]) -> list[TextResult]:
        """Post-process search results."""
        processed_results = []
        for result in results:
            if result.href.startswith("https://duckduckgo.com/y.js?"):
                continue

            if result.href.startswith("//duckduckgo.com/l/?") or result.href.startswith("https://duckduckgo.com/l/?"):
                query_params = parse_qs(urlsplit(result.href).query)
                result.href = query_params.get("uddg", [result.href])[0]

            processed_results.append(result)

        return processed_results
