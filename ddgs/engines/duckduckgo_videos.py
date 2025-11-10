"""Duckduckgo videos search engine implementation."""

import json
from collections.abc import Mapping
from typing import Any, ClassVar

from ddgs.base import BaseSearchEngine
from ddgs.results import VideosResult
from ddgs.utils import _extract_vqd


class DuckduckgoVideos(BaseSearchEngine[VideosResult]):
    """Duckduckgo videos search engine."""

    name = "duckduckgo"
    category = "videos"
    provider = "bing"

    search_url = "https://duckduckgo.com/v.js"
    search_method = "GET"

    elements_replace: ClassVar[Mapping[str, str]] = {
        "content": "content",
        "description": "description",
        "duration": "duration",
        "embed_html": "embed_html",
        "embed_url": "embed_url",
        "image_token": "image_token",
        "images": "images",
        "provider": "provider",
        "published": "published",
        "publisher": "publisher",
        "statistics": "statistics",
        "title": "title",
        "uploader": "uploader",
    }

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
        safesearch_base = {"on": "1", "moderate": "-1", "off": "-2"}
        timelimit = f"publishedAfter:{timelimit}" if timelimit else ""
        resolution = kwargs.get("resolution")
        duration = kwargs.get("duration")
        license_videos = kwargs.get("license_videos")
        resolution = f"videoDefinition:{resolution}" if resolution else ""
        duration = f"videoDuration:{duration}" if duration else ""
        license_videos = f"videoLicense:{license_videos}" if license_videos else ""
        payload = {
            "l": region,
            "o": "json",
            "q": query,
            "vqd": self._get_vqd(query),
            "f": f"{timelimit},{resolution},{duration},{license_videos}",
            "p": safesearch_base[safesearch.lower()],
        }
        if page > 1:
            payload["s"] = f"{(page - 1) * 60}"
        return payload

    def extract_results(self, html_text: str) -> list[VideosResult]:
        """Extract search results from lxml tree."""
        json_data = json.loads(html_text)
        items = json_data.get("results", [])
        results = []
        for item in items:
            result = VideosResult()
            for key, value in self.elements_replace.items():
                data = item.get(key)
                result.__setattr__(value, data)
            results.append(result)
        return results
