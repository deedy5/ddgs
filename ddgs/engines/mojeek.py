from __future__ import annotations

from random import randint, sample
from typing import Any

from ..base import BaseSearchEngine
from ..results import TextResult
from ..utils import _is_custom_date_range, _parse_date_range


class Mojeek(BaseSearchEngine[TextResult]):
    """Mojeek search engine"""

    name = "mojeek"
    category = "text"
    provider = "mojeek"

    search_url = "https://www.mojeek.com/search"
    search_method = "GET"

    items_xpath = "//ul[contains(@class, 'results')]/li"
    elements_xpath = {
        "title": ".//h2//text()",
        "href": ".//h2/a/@href",
        "body": ".//p[@class='s']//text()",
    }
    elements_replace = {}  # Required by BaseSearchEngine for XPath-based engines

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        country, lang = region.lower().split("-")
        payload = {
            "q": query,
            "arc": country,
            "lb": lang,
            "tlen": f"{randint(68, 128)}",  # Title length limit (default=68, max=128)
            "dlen": f"{randint(160, 512)}",  # Description length limit (default=160, max=512)
        }
        if safesearch == "on":
            payload["safe"] = "1"
        if page > 1:
            payload["s"] = f"{(page - 1) * 10 + 1}"
        if timelimit and _is_custom_date_range(timelimit):
            # Handle custom date range: YYYY-MM-DD..YYYY-MM-DD
            date_range = _parse_date_range(timelimit)
            if date_range:
                start_date, end_date = date_range
                # Mojeek supports custom date ranges in query
                payload["q"] += f" after:{start_date} before:{end_date}"
            # Note: Mojeek doesn't have standard predefined time limits like other engines
        # Randomize payload order
        payload = dict(sample(list(payload.items()), len(payload)))
        return payload
