from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from urllib.parse import unquote_plus

from ..base import BaseSearchEngine
from ..results import NewsResult

logger = logging.getLogger(__name__)

DATE_RE = re.compile(r"\b(\d+)\s*(year|month|week|day|hour|minute)s?\b", re.IGNORECASE)
DATE_UNITS: dict[str, Callable[[int], timedelta]] = {
    "minute": lambda n: timedelta(minutes=n),
    "hour": lambda n: timedelta(hours=n),
    "day": lambda n: timedelta(days=n),
    "week": lambda n: timedelta(weeks=n),
    "month": lambda n: timedelta(days=30 * n),
    "year": lambda n: timedelta(days=365 * n),
}


def extract_date(pub_date_str: str) -> str:
    now = datetime.now(timezone.utc)
    m = DATE_RE.search(pub_date_str)
    if not m:
        return pub_date_str

    number = int(m.group(1))
    unit = m.group(2).lower()
    delta = DATE_UNITS[unit](number)
    dt = (now - delta).replace(microsecond=0)
    return dt.isoformat()


def extract_url(u: str) -> str:
    url = u.split("/RU=", 1)[1].split("/RK=", 1)[0].split("?", 1)[0]
    return unquote_plus(url)


def extract_image(u: str) -> str:
    idx = u.find("-/")
    return u[idx + 2 :] if idx != -1 else u


def extract_source(s: str) -> str:
    return s.split(" ·  via Yahoo")[0]


class YahooNews(BaseSearchEngine[NewsResult]):
    """Yahoo news search engine"""

    name = "yahoo"
    category = "news"
    provider = "yahoo"

    search_url = "https://news.search.yahoo.com/search"
    search_method = "GET"

    items_xpath = "//div[@id='web']//li[a]"
    elements_xpath = {
        "date": ".//span[contains(@class, 'time')]//text()",
        "title": ".//h4//text()",
        "body": ".//p//text()",
        "url": ".//h4/a/@href",
        "image": "(.//img/@data-src | .//img/@src)[1]",
        "source": ".//span[contains(@class, 'source')]//text()",
    }

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        payload = {"p": query}
        if page > 1:
            payload["b"] = f"{(page - 1) * 10 + 1}"
        if timelimit:
            payload["btf"] = timelimit
        return payload

    def post_extract_results(self, results: list[NewsResult]) -> list[NewsResult]:
        try:
            for result in results:
                result.date = extract_date(result.date)
                result.url = extract_url(result.url)
                result.image = extract_image(result.image)
                result.source = extract_source(result.source)
        except Exception:
            logger.exception("Error post-processing results", exc_info=True)
        return results
