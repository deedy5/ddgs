from __future__ import annotations

from typing import Any

from ..base import BaseSearchEngine
from ..results import BooksResult


class AnnasArchive(BaseSearchEngine[BooksResult]):
    """Anna's Archive search engine"""

    name = "annasarchive"
    category = "books"
    provider = "annasarchive"

    search_url = "https://annas-archive.li/search"
    search_method = "GET"

    items_xpath = "//div[contains(@id, 'record-list')]//div[a or contains(@class, 'js-scroll-hidden')]"
    elements_xpath = {
        "title": ".//h3//text()",
        "author": ".//div[h3]/div[3]//text()",
        "publisher": ".//div[h3]/div[2]//text()",
        "info": ".//div[h3]/div[1]//text()",
        "url": "./a/@href",
        "thumbnail": ".//img/@src",
    }

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        payload = {"q": query, "page": f"{page}"}
        return payload

    def pre_process_html(self, html_text: str) -> str:
        return html_text.replace("<!--", "").replace("-->", "")

    def post_extract_results(self, results: list[BooksResult]) -> list[BooksResult]:
        base_url = self.search_url.split("/search")[0]
        for result in results:
            result.url = f"{base_url}{result.url}"
        return results
