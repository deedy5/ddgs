from __future__ import annotations

from random import randint
from typing import Any

from ..base import BaseSearchEngine
from ..results import TextResult


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

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        country, lang = region.lower().split("-")
        cookies = {
            "arc": country,
            "lb": lang,
        }
        self.http_client.client.set_cookies("https://www.mojeek.com", cookies)
        payload = {
            "q": query,
            "tlen": f"{randint(68, 128)}",  # Title length limit (default=68, max=128)
            "dlen": f"{randint(160, 512)}",  # Description length limit (default=160, max=512)
        }
        if safesearch == "on":
            payload["safe"] = "1"
        if page > 1:
            payload["s"] = f"{(page - 1) * 10 + 1}"
        return payload
