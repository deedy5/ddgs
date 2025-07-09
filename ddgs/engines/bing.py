from __future__ import annotations

import base64
from time import time
from typing import Any
from urllib.parse import parse_qs, urlparse

from lxml import html

from ..base import BaseSearchEngine
from ..results import SearchResult


class Bing(BaseSearchEngine):
    """Bing search engine"""

    search_url = "https://www.bing.com/search"
    search_method = "GET"

    items_xpath = "//li[contains(@class, 'b_algo')]"
    elements_xpath = {
        "title": "./h2/a//text() | ./div[contains(@class, 'header')]/a/h2//text()",
        "href": "./h2/a/@href | ./div[contains(@class, 'header')]/a/@href",
        "body": ".//p//text()",
    }

    def build_params(self, query: str, region: str | None, timelimit: str | None, page: int) -> dict[str, Any]:
        params = {"q": query}
        if region:
            params["cc"] = region.split("-")[0]
            cookies = {
                "_EDGE_CD": f"u={region}&m={region}",
                "_EDGE_S": f"ui={region}&mkt={region}",
            }
            self.http_client.client.set_cookies("https://www.bing.com", cookies)
        if timelimit:
            d = int(time() // 86400)
            code = f"ez5_{d - 365}_{d}" if timelimit == "y" else "ez" + {"d": "1", "w": "2", "m": "3"}[timelimit]
            params["filters"] = f'ex1:"{code}"'
        if page > 1:
            params["first"] = f"{(page - 1) * 10}"
            params["FORM"] = f"PERE{page - 2 if page > 2 else ''}"
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
                if key == "href" and data.startswith("https://www.bing.com/ck/a?"):
                    data = (
                        lambda u: base64.urlsafe_b64decode((b := u[2:]) + "=" * ((-len(b)) % 4)).decode()
                        if u and len(u) > 2
                        else None
                    )(parse_qs(urlparse(data).query).get("u", [""])[0])
                result.__setattr__(key, data)
            results.append(result.__dict__)
        return results
