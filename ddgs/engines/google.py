"""Google search engine implementation."""

from collections.abc import Mapping
from random import SystemRandom
from typing import Any, ClassVar

from ddgs.base import BaseSearchEngine
from ddgs.results import TextResult

random = SystemRandom()

# iPhone GSA (Google Search App) user agents — Google serves server-rendered
_GSA_TEMPLATE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS {ios} like Mac OS X)"
    " AppleWebKit/605.1.15 (KHTML, like Gecko)"
    " GSA/{gsa} Mobile/15E148 Safari/604.1"
)
_GSA_VARIANTS = [
    ("17_7_1", "406.0.862495628"),
    ("18_0_1", "406.0.862495628"),
    ("18_1_1", "399.2.845414227"),
    ("18_5_0", "406.0.862495628"),
    ("18_6_0", "406.0.862495628"),
    ("18_6_2", "406.0.862495628"),
    ("18_7_2", "404.0.856692123"),
    ("18_7_3", "406.0.862495628"),
    ("18_7_4", "406.0.862495628"),
]


def get_ua() -> str:
    """Return a random GSA (Google Search App) iPhone user agent."""
    ios, gsa = random.choice(_GSA_VARIANTS)
    return _GSA_TEMPLATE.format(ios=ios, gsa=gsa)


class Google(BaseSearchEngine[TextResult]):
    """Google search engine."""

    name = "google"
    category = "text"
    provider = "google"

    search_url = "https://www.google.com/search"
    search_method = "GET"
    headers_update: ClassVar[dict[str, str]] = {"User-Agent": get_ua()}

    # XPaths for GSA user agent response format.
    items_xpath = "//div[contains(@class, 'MjjYud')]"
    elements_xpath: ClassVar[Mapping[str, str]] = {
        "title": ".//div[contains(@role, 'link')]//text()",
        "href": ".//a/@href",
        "body": ".//div[contains(@data-sncf, '1')]//text()",
    }

    def build_payload(
        self,
        query: str,
        region: str,
        safesearch: str,
        timelimit: str | None,
        page: int = 1,
        **kwargs: str,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build a payload for the Google search request."""
        safesearch_base = {"on": "2", "moderate": "1", "off": "0"}
        start = (page - 1) * 10
        payload = {
            "q": query,
            "filter": safesearch_base[safesearch.lower()],
            "start": str(start),
        }
        country, lang = region.split("-")
        payload["hl"] = f"{lang}-{country.upper()}"  # interface language
        payload["lr"] = f"lang_{lang}"  # restricts to results written in a particular language
        payload["cr"] = f"country{country.upper()}"  # restricts to results written in a particular country
        if timelimit:
            payload["tbs"] = f"qdr:{timelimit}"
        return payload

    def post_extract_results(self, results: list[TextResult]) -> list[TextResult]:
        """Post-process search results."""
        post_results = []
        for result in results:
            if result.href.startswith("/url?q="):
                result.href = result.href.split("?q=")[1].split("&")[0]
            if result.title and result.href.startswith("http"):
                post_results.append(result)
        return post_results
