"""Duckduckgo images search engine implementation."""

import json
from collections.abc import Mapping
from typing import Any, ClassVar

from ddgs.base import BaseSearchEngine
from ddgs.requests_http_client import RequestsHttpClient
from ddgs.results import ImagesResult
from ddgs.utils import _extract_vqd


class DuckduckgoImages(BaseSearchEngine[ImagesResult]):
    """Duckduckgo images search engine.

    This engine uses RequestsHttpClient instead of the default HttpClient
    to work around DuckDuckGo's detection of the primp library.
    """

    name = "duckduckgo"
    category = "images"
    provider = "bing"

    search_url = "https://duckduckgo.com/i.js"
    search_method = "GET"
    search_headers: ClassVar[Mapping[str, str]] = {
        "Referer": "https://duckduckgo.com/",
        "Origin": "https://duckduckgo.com",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
    }

    elements_replace: ClassVar[Mapping[str, str]] = {
        "title": "title",
        "image": "image",
        "thumbnail": "thumbnail",
        "url": "url",
        "height": "height",
        "width": "width",
        "source": "source",
    }

    def __init__(self, proxy: str | None = None, timeout: int | None = None, *, verify: bool | str = True) -> None:
        """Initialize the DuckduckgoImages engine with RequestsHttpClient.

        Override the base class initialization to use RequestsHttpClient
        instead of the default HttpClient (which uses primp).

        Args:
            proxy: Proxy configuration (same as base class).
            timeout: Request timeout (same as base class).
            verify: SSL verification (same as base class).

        """
        # Use RequestsHttpClient instead of default HttpClient to avoid DuckDuckGo detection
        # RequestsHttpClient has the same interface as HttpClient, so this is type-safe
        self.http_client = RequestsHttpClient(proxy=proxy, timeout=timeout, verify=verify)  # type: ignore[assignment]
        self.results: list[ImagesResult] = []

    def _get_vqd(self, query: str) -> str:
        """Get vqd value for a search query using DuckDuckGo."""
        resp_content = self.http_client.request("GET", "https://duckduckgo.com", params={"q": query}).content
        return _extract_vqd(resp_content, query)

    def build_payload(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: str,
    ) -> dict[str, Any]:
        """Build a payload for the search request."""
        safesearch_base = {"on": "1", "moderate": "1", "off": "-1"}
        timelimit_base = {"d": "Day", "w": "Week", "m": "Month", "y": "Year"}
        timelimit = f"time:{timelimit_base[timelimit]}" if timelimit else ""
        size = kwargs.get("size")
        size = f"size:{size}" if size else ""
        color = kwargs.get("color")
        color = f"color:{color}" if color else ""
        type_image = kwargs.get("type_image")
        type_image = f"type:{type_image}" if type_image else ""
        layout = kwargs.get("layout")
        layout = f"layout:{layout}" if layout else ""
        license_image = kwargs.get("license_image")
        license_image = f"license:{license_image}" if license_image else ""
        payload = {
            "o": "json",
            "q": query,
            "l": region,
            "vqd": self._get_vqd(query),
            "p": safesearch_base[safesearch.lower()],
        }
        if timelimit or size or color or type_image or layout or license_image:
            payload["f"] = f"{timelimit},{size},{color},{type_image},{layout},{license_image}"
        if page > 1:
            payload["s"] = f"{(page - 1) * 100}"
        return payload

    def extract_results(self, html_text: str) -> list[ImagesResult]:
        """Extract search results from html text."""
        json_data = json.loads(html_text)
        items = json_data.get("results", [])
        results = []
        for item in items:
            result = ImagesResult()
            for key, value in self.elements_replace.items():
                data = item.get(key)
                result.__setattr__(value, data)
            results.append(result)
        return results
