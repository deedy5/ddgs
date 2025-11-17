"""Sogou search engine implementation."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from typing import Any, ClassVar
from urllib.parse import urljoin

from ddgs.base import BaseSearchEngine
from ddgs.results import TextResult

logger = logging.getLogger(__name__)


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

    _redirect_pattern = re.compile(r"window\.location\.replace\([\"'](?P<url>[^\"']+)[\"']\)")
    _meta_refresh_pattern = re.compile(r"URL='?(?P<url>[^'\"]+)", re.IGNORECASE)

    def __init__(self, proxy: str | None = None, timeout: int | None = None, *, verify: bool | str = True) -> None:
        super().__init__(proxy=proxy, timeout=timeout, verify=verify)
        self._href_cache: dict[str, str] = {}

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
        post_results = []
        for result in results:
            if result.href and result.title:
                result.href = self._normalize_href(result.href)
                post_results.append(result)
        return post_results

    def _normalize_href(self, href: str) -> str:
        """Normalize Sogou link to an absolute URL and resolve redirects when possible."""
        href = urljoin(self.search_url, href)
        if "sogou.com/link?url=" not in href:
            return href

        if href in self._href_cache:
            return self._href_cache[href]

        resolved = href
        try:
            resp = self.http_client.request("GET", href)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Error resolving Sogou link %s: %r", href, exc)
        else:
            if resp.status_code == 200 and resp.text:
                match = self._redirect_pattern.search(resp.text) or self._meta_refresh_pattern.search(resp.text)
                if match:
                    resolved = match.group("url")
        self._href_cache[href] = resolved
        return resolved
