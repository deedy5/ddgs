"""Mojeek search engine implementation."""

from collections.abc import Mapping
from typing import Any, ClassVar

from ddgs.base import BaseSearchEngine
from ddgs.results import TextResult


class Mojeek(BaseSearchEngine[TextResult]):
    """Mojeek search engine."""

    name = "mojeek"
    category = "text"
    provider = "mojeek"

    search_url = "https://www.mojeek.com/search"
    search_method = "GET"

    items_xpath = "//ul[contains(@class, 'results')]/li"
    elements_xpath: ClassVar[Mapping[str, str]] = {
        "title": ".//h2//text()",
        "href": ".//h2/a/@href",
        "body": ".//p[@class='s']//text()",
    }

    def build_payload(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,  # noqa: ARG002
        page: int = 1,
        **kwargs: str,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build a payload for the search request."""
        country, lang = region.lower().split("-")
        cookies = {
            "arc": country,
            "lb": lang,
        }
        self.http_client.client.set_cookies("https://www.mojeek.com", cookies)
        payload = {
            "q": query,
            # "tlen": f"{randint(68, 128)}",  # Title length limit (default=68, max=128)  # noqa: ERA001
            # "dlen": f"{randint(160, 512)}",  # Description length limit (default=160, max=512)  # noqa: ERA001
        }
        if safesearch == "on":
            payload["safe"] = "1"
        if page > 1:
            payload["s"] = f"{(page - 1) * 10 + 1}"
        return payload
