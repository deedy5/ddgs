from __future__ import annotations

import base64
import logging
import os
import warnings
from datetime import datetime, timezone
from functools import cached_property
from itertools import cycle
from random import shuffle
from time import sleep, time
from types import TracebackType
from typing import Any, Literal
from urllib.parse import parse_qs, urlparse

import primp
from lxml.etree import _Element
from lxml.html import HTMLParser as LHTMLParser
from lxml.html import document_fromstring

from .exceptions import DuckDuckGoSearchException, RatelimitException, TimeoutException
from .utils import (
    _expand_proxy_tb_alias,
    _extract_vqd,
    _normalize,
    _normalize_url,
    json_loads,
)

logger = logging.getLogger("duckduckgo_search.DDGS")


class DDGS:
    """DuckDuckgo_search class to get search results from duckduckgo.com."""

    def __init__(
        self,
        headers: dict[str, str] | None = None,
        proxy: str | None = None,
        proxies: dict[str, str] | str | None = None,  # deprecated
        timeout: int | None = 10,
        verify: bool = True,
    ) -> None:
        """Initialize the DDGS object.

        Args:
            headers (dict, optional): Dictionary of headers for the HTTP client. Defaults to None.
            proxy (str, optional): proxy for the HTTP client, supports http/https/socks5 protocols.
                example: "http://user:pass@example.com:3128". Defaults to None.
            timeout (int, optional): Timeout value for the HTTP client. Defaults to 10.
            verify (bool): SSL verification when making the request. Defaults to True.
        """
        warnings.simplefilter("always")
        warnings.warn(
            "This package (`duckduckgo_search`) has been renamed to `ddgs`! Use `pip install ddgs` instead.",
            RuntimeWarning,
            stacklevel=2,
        )

        ddgs_proxy: str | None = os.environ.get("DDGS_PROXY")
        self.proxy: str | None = ddgs_proxy if ddgs_proxy else _expand_proxy_tb_alias(proxy)
        assert self.proxy is None or isinstance(self.proxy, str), "proxy must be a str"
        if not proxy and proxies:
            warnings.warn("'proxies' is deprecated, use 'proxy' instead.", stacklevel=1)
            self.proxy = proxies.get("http") or proxies.get("https") if isinstance(proxies, dict) else proxies
        self.headers = headers if headers else {}
        # self.headers["Referer"] = "https://duckduckgo.com/"
        self.timeout = timeout
        self.client = primp.Client(
            # headers=self.headers,
            proxy=self.proxy,
            timeout=self.timeout,
            cookie_store=True,
            referer=True,
            impersonate="random",
            impersonate_os="random",
            follow_redirects=False,
            verify=verify,
            # http2_only=True,
        )
        self.sleep_timestamp = 0.0

    def __enter__(self) -> DDGS:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        pass

    @cached_property
    def parser(self) -> LHTMLParser:
        """Get HTML parser."""
        return LHTMLParser(remove_blank_text=True, remove_comments=True, remove_pis=True, collect_ids=False)

    def _sleep(self, sleeptime: float = 0.75) -> None:
        """Sleep between API requests."""
        delay = 0.0 if not self.sleep_timestamp else 0.0 if time() - self.sleep_timestamp >= 20 else sleeptime
        self.sleep_timestamp = time()
        sleep(delay)

    def _get_url(
        self,
        method: Literal["GET", "HEAD", "OPTIONS", "DELETE", "POST", "PUT", "PATCH"],
        url: str,
        params: dict[str, str] | None = None,
        content: bytes | None = None,
        data: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        json: Any = None,
        timeout: float | None = None,
    ) -> Any:
        self._sleep()
        try:
            resp = self.client.request(
                method,
                url,
                params=params,
                content=content,
                data=data,
                headers=headers,
                cookies=cookies,
                json=json,
                timeout=timeout or self.timeout,
            )
        except Exception as ex:
            if "time" in str(ex).lower():
                raise TimeoutException(f"{url} {type(ex).__name__}: {ex}") from ex
            raise DuckDuckGoSearchException(f"{url} {type(ex).__name__}: {ex}") from ex
        logger.debug(f"_get_url() {resp.url} {resp.status_code}")
        if resp.status_code == 200:
            return resp
        elif resp.status_code in (202, 301, 403, 400, 429, 418):
            raise RatelimitException(f"{resp.url} {resp.status_code} Ratelimit")
        raise DuckDuckGoSearchException(f"{resp.url} return None. {params=} {content=} {data=}")

    def _get_vqd(self, keywords: str) -> str:
        """Get vqd value for a search query."""
        resp_content = self._get_url("GET", "https://duckduckgo.com", params={"q": keywords}).content
        return _extract_vqd(resp_content, keywords)

    def text(
        self,
        keywords: str,
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        backend: str = "auto",
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """DuckDuckGo text search. Query params: https://duckduckgo.com/params.

        Args:
            keywords: keywords for query.
            region: us-en, uk-en, ru-ru, etc. Defaults to None.
            safesearch: on, moderate, off. Defaults to "moderate".
            timelimit: d, w, m, y. Defaults to None.
            backend: auto, html, lite. Defaults to auto.
                auto - try all backends in random order,
                html - collect data from https://html.duckduckgo.com,
                lite - collect data from https://lite.duckduckgo.com,
                bing - collect data from https://www.bing.com.
            max_results: max number of results. If None, returns results only from the first response. Defaults to None.

        Returns:
            List of dictionaries with search results, or None if there was an error.

        Raises:
            DuckDuckGoSearchException: Base exception for duckduckgo_search errors.
            RatelimitException: Inherits from DuckDuckGoSearchException, raised for exceeding API request rate limits.
            TimeoutException: Inherits from DuckDuckGoSearchException, raised for API request timeouts.
        """
        if backend in ("api", "ecosia"):
            warnings.warn(f"{backend=} is deprecated, using backend='auto'", stacklevel=2)
            backend = "auto"
        backends = ["html", "lite"] if backend == "auto" else [backend]
        shuffle(backends)
        backends = ["bing"]  # temporaly disable html and lite backends

        results, err = [], None
        for b in backends:
            try:
                if b == "html":
                    results = self._text_html(keywords, region, timelimit, max_results)
                elif b == "lite":
                    results = self._text_lite(keywords, region, timelimit, max_results)
                elif b == "bing":
                    results = self._text_bing(keywords, region, timelimit, max_results)
                return results
            except Exception as ex:
                logger.info(f"Error to search using {b} backend: {ex}")
                err = ex

        raise DuckDuckGoSearchException(err)

    def _text_html(
        self,
        keywords: str,
        region: str | None = None,
        timelimit: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        assert keywords, "keywords is mandatory"

        headers = {
            "Referer": "https://html.duckduckgo.com/",
            "Sec-Fetch-User": "?1",
        }
        self.client.headers_update(headers)

        payload = {
            "q": keywords,
            "b": "",
        }
        if region:
            payload["kl"] = region
        if timelimit:
            payload["df"] = timelimit

        cache = set()
        results: list[dict[str, str]] = []

        for _ in range(5):
            resp_content = self._get_url("POST", "https://html.duckduckgo.com/html", data=payload).content
            if b"No  results." in resp_content:
                return results

            tree = document_fromstring(resp_content, self.parser)
            elements = tree.xpath("//div[h2]")
            if not isinstance(elements, list):
                return results

            for e in elements:
                if isinstance(e, _Element):
                    hrefxpath = e.xpath("./a/@href")
                    href = str(hrefxpath[0]) if hrefxpath and isinstance(hrefxpath, list) else None
                    if (
                        href
                        and href not in cache
                        and not href.startswith(
                            ("http://www.google.com/search?q=", "https://duckduckgo.com/y.js?ad_domain")
                        )
                    ):
                        cache.add(href)
                        titlexpath = e.xpath("./h2/a/text()")
                        title = str(titlexpath[0]) if titlexpath and isinstance(titlexpath, list) else ""
                        bodyxpath = e.xpath("./a//text()")
                        body = "".join(str(x) for x in bodyxpath) if bodyxpath and isinstance(bodyxpath, list) else ""
                        results.append(
                            {
                                "title": _normalize(title),
                                "href": _normalize_url(href),
                                "body": _normalize(body),
                            }
                        )
                        if max_results and len(results) >= max_results:
                            return results

            npx = tree.xpath('.//div[@class="nav-link"]')
            if not npx or not max_results:
                return results
            next_page = npx[-1] if isinstance(npx, list) else None
            if isinstance(next_page, _Element):
                names = next_page.xpath('.//input[@type="hidden"]/@name')
                values = next_page.xpath('.//input[@type="hidden"]/@value')
                if isinstance(names, list) and isinstance(values, list):
                    payload = {str(n): str(v) for n, v in zip(names, values)}

        return results

    def _text_lite(
        self,
        keywords: str,
        region: str | None = None,
        timelimit: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        assert keywords, "keywords is mandatory"

        headers = {
            "Referer": "https://lite.duckduckgo.com/",
            "Sec-Fetch-User": "?1",
        }
        self.client.headers_update(headers)

        payload = {
            "q": keywords,
            "b": "",
        }
        if region:
            payload["kl"] = region
        if timelimit:
            payload["df"] = timelimit

        cache = set()
        results: list[dict[str, str]] = []

        for _ in range(5):
            resp_content = self._get_url("POST", "https://lite.duckduckgo.com/lite/", data=payload).content
            if b"No more results." in resp_content:
                return results

            tree = document_fromstring(resp_content, self.parser)
            elements = tree.xpath("//table[last()]//tr")
            if not isinstance(elements, list):
                return results

            data = zip(cycle(range(1, 5)), elements)
            for i, e in data:
                if isinstance(e, _Element):
                    if i == 1:
                        hrefxpath = e.xpath(".//a//@href")
                        href = str(hrefxpath[0]) if hrefxpath and isinstance(hrefxpath, list) else None
                        if (
                            href is None
                            or href in cache
                            or href.startswith(
                                ("http://www.google.com/search?q=", "https://duckduckgo.com/y.js?ad_domain")
                            )
                        ):
                            [next(data, None) for _ in range(3)]  # skip block(i=1,2,3,4)
                        else:
                            cache.add(href)
                            titlexpath = e.xpath(".//a//text()")
                            title = str(titlexpath[0]) if titlexpath and isinstance(titlexpath, list) else ""
                    elif i == 2:
                        bodyxpath = e.xpath(".//td[@class='result-snippet']//text()")
                        body = (
                            "".join(str(x) for x in bodyxpath).strip()
                            if bodyxpath and isinstance(bodyxpath, list)
                            else ""
                        )
                        if href:
                            results.append(
                                {
                                    "title": _normalize(title),
                                    "href": _normalize_url(href),
                                    "body": _normalize(body),
                                }
                            )
                            if max_results and len(results) >= max_results:
                                return results

            npx = tree.xpath("//form[./input[contains(@value, 'ext')]]")
            if not npx or not max_results:
                return results
            next_page = npx[-1] if isinstance(npx, list) else None
            if isinstance(next_page, _Element):
                names = next_page.xpath('.//input[@type="hidden"]/@name')
                values = next_page.xpath('.//input[@type="hidden"]/@value')
                if isinstance(names, list) and isinstance(values, list):
                    payload = {str(n): str(v) for n, v in zip(names, values)}

        return results

    def _text_bing(
        self,
        keywords: str,
        region: str | None = None,
        timelimit: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        assert keywords, "keywords is mandatory"

        if region:
            cookies = {
                "_EDGE_CD": f"u={region}&m={region}",
                "_EDGE_S": f"ui={region}&mkt={region}",
            }
            self.client.set_cookies("https://www.bing.com", cookies)

        payload = {
            "q": keywords,
        }
        if timelimit:
            d = int(time() // 86400)
            code = f"ez5_{d - 365}_{d}" if timelimit == "y" else "ez" + {"d": "1", "w": "2", "m": "3"}[timelimit]
            payload["filters"] = f'ex1:"{code}"'

        cache = set()
        results: list[dict[str, str]] = []

        for page in range(5):
            resp_content = self._get_url("GET", "https://www.bing.com/search", params=payload).text
            if "There are no results for" in resp_content:
                return results

            tree = document_fromstring(resp_content, self.parser)
            elements = tree.xpath("//li[contains(@class, 'b_algo')]")
            if not isinstance(elements, list):
                return results

            for e in elements:
                if isinstance(e, _Element):
                    hrefxpath = e.xpath("./h2/a/@href | ./div[contains(@class, 'header')]/a/@href")
                    href = str(hrefxpath[0]) if hrefxpath and isinstance(hrefxpath, list) else None
                    if href and href.startswith("https://www.bing.com/ck/a?"):
                        href = (
                            lambda u: base64.urlsafe_b64decode((b := u[2:]) + "=" * ((-len(b)) % 4)).decode()
                            if u and len(u) > 2
                            else None
                        )(parse_qs(urlparse(href).query).get("u", [""])[0])
                    if href and href not in cache:
                        cache.add(href)
                        titlexpath = e.xpath("./h2/a//text() | ./div[contains(@class, 'header')]/a/h2//text()")
                        title = (
                            "".join(str(x) for x in titlexpath) if titlexpath and isinstance(titlexpath, list) else ""
                        )
                        bodyxpath = e.xpath(".//p//text()")
                        body = "".join(str(x) for x in bodyxpath) if bodyxpath and isinstance(bodyxpath, list) else ""
                        results.append(
                            {
                                "title": _normalize(title),
                                "href": _normalize_url(href),
                                "body": _normalize(body).replace("\xa0", " "),
                            }
                        )
                        if max_results and len(results) >= max_results:
                            return results

            if not max_results:
                return results

            payload["first"] = f"{((page + 1) * 10) + 1}"
            payload["FORM"] = f"PERE{page if page > 0 else ''}"

        return results

    def images(
        self,
        keywords: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        size: str | None = None,
        color: str | None = None,
        type_image: str | None = None,
        layout: str | None = None,
        license_image: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """DuckDuckGo images search. Query params: https://duckduckgo.com/params.

        Args:
            keywords: keywords for query.
            region: us-en, uk-en, ru-ru, etc. Defaults to "us-en".
            safesearch: on, moderate, off. Defaults to "moderate".
            timelimit: Day, Week, Month, Year. Defaults to None.
            size: Small, Medium, Large, Wallpaper. Defaults to None.
            color: color, Monochrome, Red, Orange, Yellow, Green, Blue,
                Purple, Pink, Brown, Black, Gray, Teal, White. Defaults to None.
            type_image: photo, clipart, gif, transparent, line.
                Defaults to None.
            layout: Square, Tall, Wide. Defaults to None.
            license_image: any (All Creative Commons), Public (PublicDomain),
                Share (Free to Share and Use), ShareCommercially (Free to Share and Use Commercially),
                Modify (Free to Modify, Share, and Use), ModifyCommercially (Free to Modify, Share, and
                Use Commercially). Defaults to None.
            max_results: max number of results. If None, returns results only from the first response. Defaults to None.

        Returns:
            List of dictionaries with images search results.

        Raises:
            DuckDuckGoSearchException: Base exception for duckduckgo_search errors.
            RatelimitException: Inherits from DuckDuckGoSearchException, raised for exceeding API request rate limits.
            TimeoutException: Inherits from DuckDuckGoSearchException, raised for API request timeouts.
        """
        assert keywords, "keywords is mandatory"

        vqd = self._get_vqd(keywords)

        headers = {
            "Sec-Fetch-Mode": "cors",
        }
        self.client.headers_update(headers)

        safesearch_base = {"on": "1", "moderate": "1", "off": "-1"}
        timelimit = f"time:{timelimit}" if timelimit else ""
        size = f"size:{size}" if size else ""
        color = f"color:{color}" if color else ""
        type_image = f"type:{type_image}" if type_image else ""
        layout = f"layout:{layout}" if layout else ""
        license_image = f"license:{license_image}" if license_image else ""
        payload = {
            "o": "json",
            "q": keywords,
            "l": region,
            "vqd": vqd,
            "p": safesearch_base[safesearch.lower()],
            "f": f"{timelimit},{size},{color},{type_image},{layout},{license_image}",
        }

        cache = set()
        results: list[dict[str, str]] = []

        for _ in range(5):
            resp_content = self._get_url(
                "GET", "https://duckduckgo.com/i.js", params=payload, headers={"Referer": "https://duckduckgo.com/"}
            ).content
            resp_json = json_loads(resp_content)
            page_data = resp_json.get("results", [])

            for row in page_data:
                image_url = row.get("image")
                if image_url and image_url not in cache:
                    cache.add(image_url)
                    result = {
                        "title": row["title"],
                        "image": _normalize_url(image_url),
                        "thumbnail": _normalize_url(row["thumbnail"]),
                        "url": _normalize_url(row["url"]),
                        "height": row["height"],
                        "width": row["width"],
                        "source": row["source"],
                    }
                    results.append(result)
                    if max_results and len(results) >= max_results:
                        return results
            next = resp_json.get("next")
            if next is None or not max_results:
                return results
            payload["s"] = next.split("s=")[-1].split("&")[0]

        return results

    def videos(
        self,
        keywords: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        resolution: str | None = None,
        duration: str | None = None,
        license_videos: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """DuckDuckGo videos search. Query params: https://duckduckgo.com/params.

        Args:
            keywords: keywords for query.
            region: us-en, uk-en, ru-ru, etc. Defaults to "us-en".
            safesearch: on, moderate, off. Defaults to "moderate".
            timelimit: d, w, m. Defaults to None.
            resolution: high, standart. Defaults to None.
            duration: short, medium, long. Defaults to None.
            license_videos: creativeCommon, youtube. Defaults to None.
            max_results: max number of results. If None, returns results only from the first response. Defaults to None.

        Returns:
            List of dictionaries with videos search results.

        Raises:
            DuckDuckGoSearchException: Base exception for duckduckgo_search errors.
            RatelimitException: Inherits from DuckDuckGoSearchException, raised for exceeding API request rate limits.
            TimeoutException: Inherits from DuckDuckGoSearchException, raised for API request timeouts.
        """
        assert keywords, "keywords is mandatory"

        vqd = self._get_vqd(keywords)

        safesearch_base = {"on": "1", "moderate": "-1", "off": "-2"}
        timelimit = f"publishedAfter:{timelimit}" if timelimit else ""
        resolution = f"videoDefinition:{resolution}" if resolution else ""
        duration = f"videoDuration:{duration}" if duration else ""
        license_videos = f"videoLicense:{license_videos}" if license_videos else ""
        payload = {
            "l": region,
            "o": "json",
            "q": keywords,
            "vqd": vqd,
            "f": f"{timelimit},{resolution},{duration},{license_videos}",
            "p": safesearch_base[safesearch.lower()],
        }

        cache = set()
        results: list[dict[str, str]] = []

        for _ in range(8):
            resp_content = self._get_url("GET", "https://duckduckgo.com/v.js", params=payload).content
            resp_json = json_loads(resp_content)
            page_data = resp_json.get("results", [])

            for row in page_data:
                if row["content"] not in cache:
                    cache.add(row["content"])
                    results.append(row)
                    if max_results and len(results) >= max_results:
                        return results
            next = resp_json.get("next")
            if next is None or not max_results:
                return results
            payload["s"] = next.split("s=")[-1].split("&")[0]

        return results

    def news(
        self,
        keywords: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, str]]:
        """DuckDuckGo news search. Query params: https://duckduckgo.com/params.

        Args:
            keywords: keywords for query.
            region: us-en, uk-en, ru-ru, etc. Defaults to "us-en".
            safesearch: on, moderate, off. Defaults to "moderate".
            timelimit: d, w, m. Defaults to None.
            max_results: max number of results. If None, returns results only from the first response. Defaults to None.

        Returns:
            List of dictionaries with news search results.

        Raises:
            DuckDuckGoSearchException: Base exception for duckduckgo_search errors.
            RatelimitException: Inherits from DuckDuckGoSearchException, raised for exceeding API request rate limits.
            TimeoutException: Inherits from DuckDuckGoSearchException, raised for API request timeouts.
        """
        assert keywords, "keywords is mandatory"

        vqd = self._get_vqd(keywords)

        safesearch_base = {"on": "1", "moderate": "-1", "off": "-2"}
        payload = {
            "l": region,
            "o": "json",
            "noamp": "1",
            "q": keywords,
            "vqd": vqd,
            "p": safesearch_base[safesearch.lower()],
        }
        if timelimit:
            payload["df"] = timelimit

        cache = set()
        results: list[dict[str, str]] = []

        for _ in range(5):
            resp_content = self._get_url("GET", "https://duckduckgo.com/news.js", params=payload).content
            resp_json = json_loads(resp_content)
            page_data = resp_json.get("results", [])

            for row in page_data:
                if row["url"] not in cache:
                    cache.add(row["url"])
                    image_url = row.get("image", None)
                    result = {
                        "date": datetime.fromtimestamp(row["date"], timezone.utc).isoformat(),
                        "title": row["title"],
                        "body": _normalize(row["excerpt"]),
                        "url": _normalize_url(row["url"]),
                        "image": _normalize_url(image_url),
                        "source": row["source"],
                    }
                    results.append(result)
                    if max_results and len(results) >= max_results:
                        return results

            next = resp_json.get("next")
            if next is None or not max_results:
                return results
            payload["s"] = next.split("s=")[-1].split("&")[0]

        return results
