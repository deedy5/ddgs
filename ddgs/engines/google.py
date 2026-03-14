"""Google search engine implementation."""

from collections.abc import Mapping
from random import SystemRandom
from typing import Any, ClassVar

from ddgs.base import BaseSearchEngine
from ddgs.results import TextResult

random = SystemRandom()


def get_ua() -> str:
    """Return one random User-Agent string."""
    # iOS version to GSA version mapping based on the provided user agents
    os_gsa_map = {
        "17_4": ["315.0.630091404", "317.0.634488990"],
        "17_6_1": ["411.0.879111500"],
        "18_1_1": ["411.0.879111500"],
        "18_2": ["173.0.391310503"],
        "18_6_2": ["397.0.836500703", "399.2.845414227", "410.0.875971614", "411.0.879111500"],
        "18_7_2": ["411.0.879111500"],
        "18_7_5": ["411.0.879111500"],
        "18_7_6": ["411.0.879111500"],
        "26_1_0": ["411.0.879111500"],
        "26_2_0": ["396.0.833910942", "409.0.872648028", "411.0.879111500"],
        "26_2_1": ["409.0.872648028", "411.0.879111500"],
        "26_3_0": ["406.0.862495628", "410.0.875971614", "411.0.879111500"],
        "26_3_1": ["370.0.762543316", "404.0.856692123", "408.0.868297084", "410.0.875971614", "411.0.879111500"],
        "26_4_0": ["411.0.879111500"],
    }
    os_version = random.choice(list(os_gsa_map.keys()))
    gsa_version = random.choice(os_gsa_map[os_version])
    return f"Mozilla/5.0 (iPhone; CPU iPhone OS {os_version} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) GSA/{gsa_version} Mobile/15E148 Safari/604.1"  # noqa: E501


class Google(BaseSearchEngine[TextResult]):
    """Google search engine."""

    name = "google"
    category = "text"
    provider = "google"

    search_url = "https://www.google.com/search"
    search_method = "GET"
    headers_update: ClassVar[dict[str, str]] = {"User-Agent": get_ua()}

    items_xpath = "//div[@data-snc]"
    elements_xpath: ClassVar[Mapping[str, str]] = {
        "title": ".//div[@role='link']//text()",
        "href": ".//a/@href",
        "body": "./div[@data-sncf]//text()",
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
