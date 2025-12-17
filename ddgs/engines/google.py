"""Google search engine implementation."""

from collections.abc import Mapping
from random import SystemRandom
from typing import Any, ClassVar

from ddgs.base import BaseSearchEngine
from ddgs.results import TextResult

random = SystemRandom()


def get_ua() -> str:
    """Return one random User-Agent string."""
    patterns = [
        "Opera/9.80 (J2ME/MIDP; Opera Mini/{v}/{b}; U; {l}) Presto/{p} Version/{f}",
        "Opera/9.80 (Android; Linux; Opera Mobi/{b}; U; {l}) Presto/{p} Version/{f}",
        "Opera/9.80 (iPhone; Opera Mini/{v}/{b}; U; {l}) Presto/{p} Version/{f}",
        "Opera/9.80 (iPad; Opera Mini/{v}/{b}; U; {l}) Presto/{p} Version/{f}",
    ]
    mini_versions = ["4.0", "5.0.17381", "7.1.32444", "9.80"]
    mobi_builds = ["27", "447", "ADR-1011151731"]
    builds = ["18.678", "24.743", "503"]
    prestos = ["2.6.35", "2.7.60", "2.8.119"]
    finals = ["10.00", "11.10", "12.16"]
    langs = ["en-US", "en-GB", "de-DE", "fr-FR", "es-ES", "ru-RU", "zh-CN"]
    fallback = "Opera/9.80 (iPad; Opera Mini/5.0.17381/503; U; eu) Presto/2.6.35 Version/11.10"

    try:
        p = random.choice(patterns)
        vals = {
            "l": random.choice(langs),
            "p": random.choice(prestos),
            "f": random.choice(finals),
        }
        if "{v}" in p:
            vals["v"] = random.choice(mini_versions)
        if "{b}" in p:
            vals["b"] = random.choice(mobi_builds) if "Opera Mobi" in p else random.choice(builds)
        return p.format(**vals)
    except Exception:  # noqa: BLE001
        return fallback


class Google(BaseSearchEngine[TextResult]):
    """Google search engine."""

    name = "google"
    category = "text"
    provider = "google"

    search_url = "https://www.google.com/search"
    search_method = "GET"
    search_headers: ClassVar[dict[str, str]] = {"User-Agent": get_ua()}

    items_xpath = "//div[div[@data-hveid]//div[h3]]"
    elements_xpath: ClassVar[Mapping[str, str]] = {
        "title": ".//h3//text()",
        "href": ".//a/@href",
        "body": "./div/div/div[2]//text()",
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
            post_results.append(result)
        return post_results
