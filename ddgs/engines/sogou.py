"""Sogou search engine implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar
from urllib.parse import urljoin

if TYPE_CHECKING:
    from collections.abc import Mapping

from ddgs.base import BaseSearchEngine
from ddgs.results import TextResult


class Sogou(BaseSearchEngine[TextResult]):
    """Sogou search engine."""

    name = "sogou"
    category = "text"
    provider = "sogou"

    search_url = "https://www.sogou.com/web"
    search_method = "GET"

    items_xpath = "//div[contains(@class, 'vrwrap') and not(contains(@class, 'hint'))]"
    elements_xpath: ClassVar[Mapping[str, str]] = {
        "title": ".//h3//a//text()",
        "href": ".//h3//a/@href",
        "body": ".//div[contains(@class, 'space-txt')]//text()",
    }

    def build_payload(
        self,
        query: str,
        region: str,  # noqa: ARG002
        safesearch: str,  # noqa: ARG002
        timelimit: str | None,
        page: int = 1,
        **kwargs: str,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build a payload for the search request."""
        payload = {"query": query, "ie": "utf8", "p": "40040100", "dp": "1"}
        if timelimit:
            payload["tsn"] = {"d": "1", "w": "7", "m": "30", "y": "365"}[timelimit]
        if page > 1:
            payload["page"] = str(page)
        return payload

    def post_extract_results(self, results: list[TextResult]) -> list[TextResult]:
        """Post-process search results."""
        return [
            TextResult(
                title=r.title,
                href=urljoin(self.search_url, r.href),
                body=r.body,
            )
            for r in results
            if r.href and r.title
        ]
