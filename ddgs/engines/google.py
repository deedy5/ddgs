"""Google search engine implementation."""

from __future__ import annotations

from collections.abc import Mapping
from secrets import token_urlsafe
from time import time
from typing import Any, ClassVar

from ..base import BaseSearchEngine
from ..results import TextResult

_arcid_random = None  # (random_token, timestamp)


def ui_async(start: int) -> str:
    """Generate 'async' payload param."""
    global _arcid_random
    now = int(time())
    if not _arcid_random or now - _arcid_random[1] > 3600:
        rnd_token = token_urlsafe(23 * 3 // 4)
        _arcid_random = (rnd_token, now)
    return f"arc_id:srp_{_arcid_random[0]}_1{start:02},use_ac:true,_fmt:prog"


class Google(BaseSearchEngine[TextResult]):
    """Google search engine."""

    disabled = True  # !!!

    name = "google"
    category = "text"
    provider = "google"

    search_url = "https://www.google.com/search"
    search_method = "GET"

    items_xpath = "//div[@data-snc]"
    elements_xpath: ClassVar[Mapping[str, str]] = {
        "title": ".//h3//text()",
        "href": ".//a[h3]/@href",
        "body": ".//div[starts-with(@data-sncf, '1')]//text()",
    }

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        """Build a payload for the Google search request."""
        safesearch_base = {"on": "2", "moderate": "1", "off": "0"}
        start = (page - 1) * 10
        payload = {
            "q": query,
            "filter": safesearch_base[safesearch.lower()],
            "start": str(start),
            "asearch": "arc",
            "async": ui_async(start),
            "ie": "UTF-8",
            "oe": "UTF-8",
        }
        country, lang = region.split("-")
        payload["hl"] = f"{lang}-{country.upper()}"  # interface language
        payload["lr"] = f"lang_{lang}"  # restricts to results written in a particular language
        payload["cr"] = f"country{country.upper()}"  # restricts to results written in a particular country
        if timelimit:
            payload["tbs"] = f"qdr:{timelimit}"
        return payload
