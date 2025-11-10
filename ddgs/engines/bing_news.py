"""Bing news engine implementation."""

import re
from collections.abc import Mapping
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from typing import Any, ClassVar

from ddgs.base import BaseSearchEngine
from ddgs.results import NewsResult

DATE_RE = re.compile(r"\b(\d+)\s*(days|tagen|jours|giorni|dias|días|дн\.|день)?\b", re.IGNORECASE)


def extract_date(pub_date_str: str) -> str:
    """Extract date from string."""
    # Try parsing the date with predefined formats
    date_formats = ["%d.%m.%Y", "%m/%d/%Y", "%d/%m/%Y"]
    for date_format in date_formats:
        with suppress(ValueError):
            return datetime.strptime(pub_date_str, date_format).astimezone(timezone.utc).isoformat()

    # Search for relative date expressions
    match = DATE_RE.search(pub_date_str)
    if match:
        days_ago = int(match.group(1))
        return (datetime.now(timezone.utc) - timedelta(days=days_ago)).replace(microsecond=0).isoformat()

    # Return the original string if no date is found
    return pub_date_str


class BingNews(BaseSearchEngine[NewsResult]):
    """Bing news engine."""

    name = "bing"
    category = "news"
    provider = "bing"

    search_url = "https://www.bing.com/news/infinitescrollajax"
    search_method = "GET"

    items_xpath = "//div[contains(@class, 'newsitem')]"
    elements_xpath: ClassVar[Mapping[str, str]] = {
        "date": ".//span[@aria-label]//@aria-label",
        "title": "@data-title",
        "body": ".//div[@class='snippet']//text()",
        "url": "@url",
        "image": ".//a[contains(@class, 'image')]//@src",
        "source": "@data-author",
    }

    def build_payload(
        self,
        query: str,
        region: str,
        safesearch: str,  # noqa: ARG002
        timelimit: str | None,
        page: int = 1,
        **kwargs: str,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build a payload for the Bing search request."""
        country, lang = region.lower().split("-")
        payload = {
            "q": query,
            "InfiniteScroll": "1",
            "first": f"{page * 10 + 1}",
            "SFX": f"{page}",
            "cc": country,
            "setlang": lang,
        }
        if timelimit:
            payload["qft"] = {
                "d": 'interval="4"',  # doesn't exist so it's the same as one hour
                "w": 'interval="7"',
                "m": 'interval="9"',
                "y": 'interval="9"',  # doesn't exist so it's the same as month
            }[timelimit]
        return payload

    def post_extract_results(self, results: list[NewsResult]) -> list[NewsResult]:
        """Post-process search results."""
        for result in results:
            result.date = extract_date(result.date)
            result.image = f"https://www.bing.com{result.image.split('&')[0]}" if result.image else ""
        return results
