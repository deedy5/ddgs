"""Yahoo search engine."""

from collections.abc import Mapping
from secrets import token_urlsafe
from typing import Any, ClassVar
from urllib.parse import unquote_plus

from ddgs.base import BaseSearchEngine
from ddgs.exceptions import DDGSException
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

    # Support Yahoo's legacy and current search-result layouts.
    items_xpath = (
        "//div[contains(@class, 'relsrch')]"
        " | //section[contains(concat(' ', normalize-space(@class), ' '), ' algo-sr ')]"
    )
    elements_xpath: ClassVar[Mapping[str, str]] = {
        "title": (
            ".//div[contains(concat(' ', normalize-space(@class), ' '), ' Title ')]//h3//text()"
            " | (.//h3[contains(@class, 'title')]/a[contains(@class, 's-title')])[1]/text()"
        ),
        "href": (
            "(.//div[contains(@class, 'Title')]//a"
            " | .//h3[contains(@class, 'title')]/a[contains(@class, 's-title')])[1]/@href"
        ),
        "body": (
            "(.//div[contains(@class, 'Text')]"
            " | .//div[contains(@class, 'compText')]//p[contains(@class, 's-desc')])[1]//text()"
        ),
    }

    def pre_process_html(self, html_text: str) -> str:
        """Identify Yahoo's explicit temporary search failure response."""
        if "zrp_yst" not in html_text:
            return html_text

        tree = self.extract_tree(html_text)
        messages = tree.xpath(
            "//div[contains(concat(' ', normalize-space(@class), ' '), ' zrp_yst ')]//h2[contains(@class, 'zrpmsg')]"
        )

        for message in messages:
            if "We had temporary problems searching for web pages." in " ".join(message.itertext()):
                msg = "Yahoo reported a temporary search failure"
                raise DDGSException(msg)

        return html_text

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
