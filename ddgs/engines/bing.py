from __future__ import annotations

import base64
from time import time
from typing import Any
from urllib.parse import parse_qs, urlparse

from ..base import BaseSearchEngine
from ..results import TextResult


class Bing(BaseSearchEngine):
    """Bing search engine"""

    search_url = "https://www.bing.com/search"
    search_method = "GET"

    items_xpath = "//li[contains(@class, 'b_algo')]"
    elements_xpath = {
        "title": ".//h2/a//text()",
        "href": ".//h2/a/@href",
        "body": ".//p//text()",
    }

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        country, lang = region.lower().split("-")
        payload = {"q": query, "pq": query, "cc": lang}
        cookies = {
            "_EDGE_CD": f"m={lang}-{country}&u={lang}-{country}",
            "_EDGE_S": f"mkt={lang}-{country}&ui={lang}-{country}",
        }
        self.http_client.client.set_cookies("https://www.bing.com", cookies)
        if timelimit:
            d = int(time() // 86400)
            code = f"ez5_{d - 365}_{d}" if timelimit == "y" else "ez" + {"d": "1", "w": "2", "m": "3"}[timelimit]
            payload["filters"] = f'ex1:"{code}"'
        if page > 1:
            payload["first"] = f"{(page - 1) * 10}"
            payload["FORM"] = f"PERE{page - 2 if page > 2 else ''}"
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
                if key == "href" and data.startswith("https://www.bing.com/ck/a?"):
                    data = (
                        lambda u: base64.urlsafe_b64decode((b := u[2:]) + "=" * ((-len(b)) % 4)).decode()
                        if u and len(u) > 2
                        else None
                    )(parse_qs(urlparse(data).query).get("u", [""])[0])
                result.__setattr__(key, data)
            results.append(result.__dict__)
        return results
