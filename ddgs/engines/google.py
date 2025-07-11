from __future__ import annotations

import string
from random import choices
from time import time
from typing import Any

from ..base import BaseSearchEngine
from ..results import TextResult

_arcid_random = None  # (random_part, timestamp)


def ui_async(start: int) -> str:
    global _arcid_random
    now = int(time())
    # regen if first call or TTL expired
    if not _arcid_random or now - _arcid_random[1] > 3600:
        rnd = "".join(choices(string.ascii_letters + string.digits + "_-", k=23))
        _arcid_random = (rnd, now)
    return f"arc_id:srp_{_arcid_random[0]}_1{start:02},use_ac:true,_fmt:prog"


class Google(BaseSearchEngine):
    """Google search engine"""

    search_url = "https://www.google.com/search"
    search_method = "GET"

    items_xpath = "//div[@data-snc]"
    elements_xpath = {
        "title": ".//h3//text()",
        "href": ".//a[h3]/@href",
        "body": "./div[2]//text()",
    }

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
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

    def extract_results(self, html_text: str) -> list[dict[str, Any]]:
        """Extract search results from html text"""
        tree = self.extract_tree(html_text)
        items = tree.xpath(self.items_xpath)
        results = []
        for item in items:
            result = TextResult()
            for key, value in self.elements_xpath.items():
                data = item.xpath(value)
                data = "".join(x for x in data if x.strip())
                result.__setattr__(key, data)
            results.append(result.__dict__)
        return results
