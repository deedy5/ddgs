from __future__ import annotations

import string
from random import choices
from time import time
from typing import Any

from lxml import html

from ..base import BaseSearchEngine
from ..results import SearchResult

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
        "href": ".//a/@href[1]",
        "body": "./div[2]//text()",
    }

    def build_params(self, query: str, region: str | None, timelimit: str | None, page: int) -> dict[str, Any]:
        start = (page - 1) * 10
        params = {
            "q": query,
            "start": str(start),
            "asearch": "arc",
            "async": ui_async(start),
        }
        if region:
            params["hl"] = f"{region.split('-')[1]}-{region.split('-')[0].upper()}"
        if timelimit:
            params["tbs"] = f"qdr:{timelimit}"
        return params

    def extract_results(self, tree: html.Element) -> list[dict[str, Any]]:
        """Extract search results from lxml tree"""
        items = tree.xpath(self.items_xpath)
        results = []
        for item in items:
            result = SearchResult()
            for key, value in self.elements_xpath.items():
                data = item.xpath(value)
                data = "".join(x for x in data if x.strip())
                result.__setattr__(key, data)
            results.append(result.__dict__)
        return results
