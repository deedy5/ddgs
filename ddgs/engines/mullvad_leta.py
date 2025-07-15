from __future__ import annotations

from abc import ABC
from typing import Any, Literal

from ..base import BaseSearchEngine
from ..results import TextResult
from ..utils import json_loads


class BaseMullvadLeta(BaseSearchEngine, ABC):
    """Generic Mullvad leta search engine"""

    # sentinel default; subclasses should set this to "google" or "brave"
    engine: Literal["google", "brave"] | None = None

    search_url = "https://leta.mullvad.net/search/__data.json"
    search_method = "GET"

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        country, lang = region.lower().split("-")
        payload = {
            "q": query,
            "engine": self.engine,
            "x-sveltekit-invalidated": "001",
        }
        if country:
            payload["country"] = country
        if lang:
            payload["lang"] = "zh-hans" if lang == "zh" else lang
        if timelimit:
            payload["lastUpdated"] = timelimit
        if page > 1:
            payload["page"] = f"{page}"
        return payload

    def extract_results(self, html_text: str) -> list[dict[str, Any]]:
        """Extract search results from html text"""
        json_data = json_loads(html_text)
        data = json_data["nodes"][2]["data"]
        # locate the real list of item-pointers
        items = data[data[0]["items"]]

        results = []
        for ptr in items:
            result = TextResult()
            record = data[ptr]
            result.title = data[record["title"]]
            result.href = data[record["link"]]
            result.body = data[record["snippet"]]
            results.append(result.__dict__)
        return results


class MullvadLetaBrave(BaseMullvadLeta):
    engine = "brave"


class MullvadLetaGoogle(BaseMullvadLeta):
    engine = "google"
