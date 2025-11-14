"""Duckduckgo search engine implementation."""

from collections.abc import Mapping
from typing import Any, ClassVar, TypeVar

from fake_useragent import UserAgent

from ddgs.base import BaseSearchEngine
from ddgs.http_client2 import HttpClient2
from ddgs.results import TextResult

ua = UserAgent()

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

    headers: ClassVar[dict[str, str]] = {"User-Agent": ua.random}

    def __init__(self, proxy: str | None = None, timeout: int | None = None, *, verify: bool = True) -> None:
        """Temporary, delete when HttpClient is fixed."""
        self.http_client = HttpClient2(headers=self.headers, proxy=proxy, timeout=timeout, verify=verify)  # type: ignore[assignment]
        self.results: list[T] = []  # type: ignore[valid-type]

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
