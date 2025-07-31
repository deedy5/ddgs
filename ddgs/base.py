from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from functools import cached_property
from typing import Any, Generic, Literal, TypeVar

from lxml import html
from lxml.etree import HTMLParser as LHTMLParser

from .http_client import HttpClient
from .results import BooksResult, ImagesResult, NewsResult, TextResult, VideosResult

logger = logging.getLogger(__name__)
T = TypeVar("T")


class BaseSearchEngine(ABC, Generic[T]):
    """
    Abstract base for all search-engine backends.
    """

    name: str  # unique key, e.g. "google"
    category: Literal["text", "images", "videos", "news", "books"]
    provider: str  # source of the search results (e.g. "google" for MullVadLetaGoogle)
    disabled: bool = False  # if True, the engine is disabled
    priority: float = 1

    search_url: str
    search_method: str  # GET or POST
    search_headers: dict[str, str] = {}
    items_xpath: str
    elements_xpath: dict[str, str]
    elements_replace: dict[str, str]

    def __init__(self, proxy: str | None = None, timeout: int | None = None, verify: bool = True):
        self.http_client = HttpClient(proxy=proxy, timeout=timeout, verify=verify)
        self.results: list[T] = []

    @property
    def result_type(self) -> type[T]:
        """Get result type based on category"""
        categories = {
            "text": TextResult,
            "images": ImagesResult,
            "videos": VideosResult,
            "news": NewsResult,
            "books": BooksResult,
        }
        return categories[self.category]

    @abstractmethod
    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int, **kwargs: Any
    ) -> dict[str, Any]:
        """Build a payload for the search request."""
        raise NotImplementedError

    def request(self, *args: Any, **kwargs: Any) -> str | None:
        """Make a request to the search engine"""
        try:
            resp = self.http_client.request(*args, **kwargs)
            if resp.status_code == 200:
                return resp.text
        except Exception as ex:
            raise ex
        return None

    @cached_property
    def parser(self) -> LHTMLParser:
        """Get HTML parser."""
        return LHTMLParser(remove_blank_text=True, remove_comments=True, remove_pis=True, collect_ids=False)

    def extract_tree(self, html_text: str) -> html.Element:
        """Extract html tree from html text"""
        return html.fromstring(html_text, parser=self.parser)

    def pre_process_html(self, html_text: str) -> str:
        """Pre-process html_text before extracting results"""
        return html_text

    def extract_results(self, html_text: str) -> list[T]:
        """Extract search results from html text"""
        html_text = self.pre_process_html(html_text)
        tree = self.extract_tree(html_text)
        items = tree.xpath(self.items_xpath)
        results = []
        for item in items:
            result = self.result_type()
            for key, value in self.elements_xpath.items():
                data = " ".join(x.strip() for x in item.xpath(value))
                result.__setattr__(key, data)
            results.append(result)
        return results

    def post_extract_results(self, results: list[T]) -> list[T]:
        """Post-process search results"""
        return results

    def search(
        self,
        query: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
        **kwargs: Any,
    ) -> list[T] | None:
        """Search the engine"""
        payload = self.build_payload(
            query=query, region=region, safesearch=safesearch, timelimit=timelimit, page=page, **kwargs
        )
        if self.search_method == "GET":
            html_text = self.request(self.search_method, self.search_url, params=payload, headers=self.search_headers)
        else:
            html_text = self.request(self.search_method, self.search_url, data=payload, headers=self.search_headers)
        if not html_text:
            return None
        results = self.extract_results(html_text)
        results = self.post_extract_results(results)
        return results
