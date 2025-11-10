"""Anna's Archive search engine implementation."""

from collections.abc import Mapping
from typing import Any, ClassVar

from ddgs.base import BaseSearchEngine
from ddgs.results import BooksResult


class AnnasArchive(BaseSearchEngine[BooksResult]):
    """Anna's Archive search engine."""

    name = "annasarchive"
    category = "books"
    provider = "annasarchive"

    search_url = "https://annas-archive.li/search"
    search_method = "GET"

    items_xpath = "//div[contains(@class, 'record-list-outer')]/div"
    elements_xpath: ClassVar[Mapping[str, str]] = {
        "title": ".//a[contains(@class, 'text-lg')]//text()",
        "author": ".//a[span[contains(@class, 'user')]]//text()",
        "publisher": ".//a[span[contains(@class, 'company')]]//text()",
        "info": ".//div[contains(@class, 'text-gray-800')]/text()",
        "url": "./a/@href",
        "thumbnail": ".//img/@src",
    }

    def build_payload(
        self,
        query: str,
        region: str,  # noqa: ARG002
        safesearch: str,  # noqa: ARG002
        timelimit: str | None,  # noqa: ARG002
        page: int = 1,
        **kwargs: str,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build a payload for the search request."""
        return {"q": query, "page": f"{page}"}

    def pre_process_html(self, html_text: str) -> str:
        """Pre-process the HTML text before parsing it."""
        return html_text.replace("<!--", "").replace("-->", "")

    def post_extract_results(self, results: list[BooksResult]) -> list[BooksResult]:
        """Post-process search results."""
        base_url = self.search_url.split("/search")[0]
        for result in results:
            result.url = f"{base_url}{result.url}"
        return results
