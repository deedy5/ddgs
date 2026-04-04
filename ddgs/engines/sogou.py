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

    _data_url_xpath = ".//*[@data-url]/@data-url"

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

    @staticmethod
    def _xpath_join(item: Any, xpath: str) -> str:  # noqa: ANN401
        return " ".join(x.strip() for x in item.xpath(xpath) if x and x.strip())

    @staticmethod
    def _xpath_first(item: Any, xpath: str) -> str:  # noqa: ANN401
        for value in item.xpath(xpath):
            if value and (str_value := value.strip()):
                return str_value
        return ""

    @staticmethod
    def _is_wrapper_link(href: str) -> bool:
        return "/link?url=" in href or "sogou.com/link?url=" in href

    def extract_results(self, html_text: str) -> list[TextResult]:
        """Extract search results from html text."""
        html_text = self.pre_process_html(html_text)
        tree = self.extract_tree(html_text)
        items = tree.xpath(self.items_xpath)
        results = []
        for item in items:
            title = self._xpath_join(item, self.elements_xpath["title"])
            href = self._xpath_first(item, self.elements_xpath["href"])
            body = self._xpath_join(item, self.elements_xpath["body"])
            data_url = self._xpath_first(item, self._data_url_xpath)
            if href and self._is_wrapper_link(href) and data_url.startswith(("http://", "https://")):
                href = data_url
            results.append(TextResult(title=title, href=href, body=body))
        return results

    def post_extract_results(self, results: list[TextResult]) -> list[TextResult]:
        """Post-process search results."""
        post_results = []
        for result in results:
            if not (result.href and result.title):
                continue

            href = urljoin(self.search_url, result.href)
            if self._is_wrapper_link(href):
                continue

            post_results.append(TextResult(title=result.title, href=href, body=result.body))
        return post_results
