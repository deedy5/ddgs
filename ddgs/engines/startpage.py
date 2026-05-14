"""Startpage search engine implementation."""

import logging
from collections.abc import Mapping
from typing import Any, ClassVar

from ddgs.base import BaseSearchEngine
from ddgs.results import TextResult

logger = logging.getLogger(__name__)


class Startpage(BaseSearchEngine[TextResult]):
    """Startpage search engine."""

    name = "startpage"
    category = "text"
    provider = "google"

    search_url = "https://www.startpage.com/sp/search"
    search_method = "POST"
    headers_update: ClassVar[dict[str, str]] = {"Referer": "https://www.startpage.com/"}

    items_xpath = "//div[contains(@class, 'result')][./a]"
    elements_xpath: ClassVar[Mapping[str, str]] = {
        "title": ".//h2//text()",
        "href": "./a/@href",
        "body": ".//p//text()",
    }

    def get_sc(self) -> str:
        """Get sc param."""
        resp_text = self.http_client.request("GET", "https://www.startpage.com/").text
        tree = self.extract_tree(resp_text)
        sc_elements = tree.xpath('//form[@id="search"]//input[@name="sc"]/@value')
        self._sc = sc_elements[0] if sc_elements else ""
        return self._sc

    def build_payload(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: str,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build a payload for the Startpage search request."""
        country, lang = region.lower().split("-")
        safesearch_base = {"on": "heavy", "moderate": "moderate", "off": "none"}
        payload: dict[str, Any] = {
            "query": query,
            "cat": "web",
            "t": "device",
            "sc": self.get_sc(),
            "lui": "english",
            "language": "english",
            "abp": "1",
            "abd": "0",
            "abe": "0",
            "qsr": f"{lang}_{country.upper()}",
            "qadf": safesearch_base[safesearch.lower()],
            "segment": "organic",
        }
        if page > 1:
            payload["page"] = str(page)
        if timelimit:
            payload["with_date"] = timelimit

        return payload
