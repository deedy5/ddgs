"""Yahoo search engine."""

from collections.abc import Mapping
from secrets import token_urlsafe
from typing import Any, ClassVar
from urllib.parse import unquote_plus

from ddgs.base import BaseSearchEngine
from ddgs.results import TextResult


def extract_url(u: str) -> str:
    """Sanitize url."""
    t = u.split("/RU=", 1)[1]
    return unquote_plus(t.split("/RK=", 1)[0].split("/RS=", 1)[0])


class Yahoo(BaseSearchEngine[TextResult]):
    """Yahoo search engine."""

    name = "yahoo"
    category = "text"
    provider = "bing"

    search_url = "https://search.yahoo.com/search"
    search_method = "GET"

    items_xpath = "//div[contains(@class, 'relsrch')]"
    elements_xpath: ClassVar[Mapping[str, str]] = {
        "title": ".//div[contains(@class, 'Title')]//h3//text()",
        "href": ".//div[contains(@class, 'Title')]//a/@href",
        "body": ".//div[contains(@class, 'Text')]//text()",
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
        self.search_url = (
            f"https://search.yahoo.com/search;_ylt={token_urlsafe(24 * 3 // 4)};_ylu={token_urlsafe(47 * 3 // 4)}"
        )
        payload = {"p": query}
        if page > 1:
            payload["b"] = f"{(page - 1) * 7 + 1}"
        if timelimit:
            payload["btf"] = timelimit
        return payload

    def post_extract_results(self, results: list[TextResult]) -> list[TextResult]:
        """Post-process search results."""
        post_results = []
        for result in results:
            if result.href.startswith("https://www.bing.com/aclick?"):
                continue
            if "/RU=" in result.href:
                result.href = extract_url(result.href)
            post_results.append(result)
        return post_results
