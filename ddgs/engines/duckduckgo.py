"""Duckduckgo search engine implementation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar, TypeVar

from ..base import BaseSearchEngine
from ..http_client2 import HttpClient2
from ..results import TextResult

T = TypeVar("T")


class Duckduckgo(BaseSearchEngine[TextResult]):
    """Duckduckgo search engine."""

    name = "duckduckgo"
    category = "text"
    provider = "bing"

    search_url = "https://html.duckduckgo.com/html/"
    search_method = "POST"

    items_xpath = "//div[contains(@class, 'body')]"
    elements_xpath: ClassVar[Mapping[str, str]] = {"title": ".//h2//text()", "href": "./a/@href", "body": "./a//text()"}

    def __init__(self, proxy: str | None = None, timeout: int | None = None, verify: bool = True):
        """Temporary, delete when HttpClient is fixed."""
        self.http_client = HttpClient2(proxy=proxy, timeout=timeout, verify=verify)  # type: ignore
        self.results: list[T] = []  # type: ignore

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        """Build a payload for the search request."""
        payload = {"q": query, "b": "", "l": region}
        if page > 1:
            payload["s"] = f"{10 + (page - 2) * 15}"
        if timelimit:
            payload["df"] = timelimit
        return payload
