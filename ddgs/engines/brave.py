from __future__ import annotations

from typing import Any

from ..base import BaseSearchEngine
from ..results import TextResult


class Brave(BaseSearchEngine[TextResult]):
    """Brave search engine"""

    name = "brave"
    category = "text"
    provider = "brave"

    search_url = "https://search.brave.com/search"
    search_method = "GET"

    items_xpath = "//div[@data-type='web']"
    elements_xpath = {
        "title": ".//div[(contains(@class,'title') or contains(@class,'sitename-container')) and position()=last()]//text()",  # noqa: E501
        "href": "./a/@href",
        "body": ".//div[contains(@class, 'description')]//text()",
    }

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        payload = {"q": query, "source": "web"}
        country, lang = region.lower().split("-")
        cookies = {country: country, "useLocation": "0"}
        if safesearch != "moderate":
            cookies["safesearch"] = "strict" if safesearch == "on" else "off"
        self.http_client.client.set_cookies("https://search.brave.com", cookies)
        if timelimit:
            payload["tf"] = {"d": "pd", "w": "pw", "m": "pm", "y": "py"}[timelimit]
        if page > 1:
            payload["offset"] = f"{page - 1}"
        return payload
