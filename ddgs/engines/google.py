"""Google search engine implementation."""

from collections.abc import Mapping
from random import SystemRandom
from typing import Any, ClassVar

from ddgs.base import BaseSearchEngine
from ddgs.results import TextResult

random = SystemRandom()


def get_ua() -> str:
    """Return one random Android Google App User-Agent string."""
    # Device templates: (Android version, device string, Chrome major version range)
    devices = (
        ("5.0", "SM-G900P Build/LRX21T", 39, 60),
        ("6.0", "Nexus 5 Build/MRA58N", 39, 60),
        ("8.0", "Pixel 2 Build/OPD3.170816.012", 39, 60),
    )
    android_ver, device, chrome_min, chrome_max = random.choice(devices)
    chrome_major = random.randint(chrome_min, chrome_max)
    chrome_build = random.randint(1000, 9999)
    chrome_patch = random.randint(1000, 1999)
    ua = (
        f"Mozilla/5.0 (Linux; Android {android_ver}; {device}) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) "
        f"Chrome/{chrome_major}.0.{chrome_build}.{chrome_patch} Mobile Safari/537.36"
    )
    return f"{ua} GoogleApp/{random.randint(0, 9)}"


class Google(BaseSearchEngine[TextResult]):
    """Google search engine."""

    name = "google"
    category = "text"
    provider = "google"

    search_url = "https://www.google.com/search"
    search_method = "GET"
    headers_update: ClassVar[dict[str, str]] = {"User-Agent": get_ua()}

    items_xpath = "//div[@data-hveid][.//h3]"
    elements_xpath: ClassVar[Mapping[str, str]] = {
        "title": ".//h3//text()",
        "href": ".//a[.//h3]/@href",
        "body": "./div/div[last()]//text()",
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
        self.http_client.client.set_cookies("google.com", {"CONSENT": "YES+"})
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
