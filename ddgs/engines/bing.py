from __future__ import annotations

import base64
from time import time
from typing import Any
from urllib.parse import parse_qs, urlparse

from ..base import BaseSearchEngine
from ..results import TextResult


def unwrap_bing_url(raw_url: str) -> str | None:
    """Decode the Bing-wrapped raw_url to extract the original url"""
    parsed = urlparse(raw_url)
    u_vals = parse_qs(parsed.query).get("u", [])
    if not u_vals:
        return None

    u = u_vals[0]
    if len(u) <= 2:
        return None

    # Drop the first two characters, pad to a multiple of 4, then decode
    b64_part = u[2:]
    padding = "=" * (-len(b64_part) % 4)
    decoded = base64.urlsafe_b64decode(b64_part + padding)
    return decoded.decode()


class Bing(BaseSearchEngine[TextResult]):
    """Bing search engine"""

    name = "bing"
    category = "text"
    provider = "bing"

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

    def post_extract_results(self, results: list[TextResult]) -> list[TextResult]:
        """Post-process search results"""
        post_results = []
        for result in results:
            if result.href.startswith("https://www.bing.com/aclick?"):
                continue
            if result.href.startswith("https://www.bing.com/ck/a?"):
                result.href = unwrap_bing_url(result.href) or result.href
            post_results.append(result)
        return post_results
