from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from functools import cached_property
from typing import Any

from lxml import html
from lxml.etree import HTMLParser as LHTMLParser

from .http_client import HttpClient
from .results import ImagesResult, TextResult
from .utils import _normalize_text, _normalize_url


class BaseSearchEngine(ABC):
    search_url: str
    search_method: str  # GET or POST
    search_headers: dict[str, str] = {}
    items_xpath: str
    elements_xpath: dict[str, str]
    elements_replace: dict[str, str]

    def __init__(self, proxy: str | None = None, timeout: int | None = None, verify: bool = True):
        self.http_client = HttpClient(proxy=proxy, timeout=timeout, verify=verify)
        self.results: list[TextResult | ImagesResult] = []

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
            logging.warning(f"{type(ex).__name__}: {ex}", exc_info=True)
        return None

    @cached_property
    def parser(self) -> LHTMLParser:
        """Get HTML parser."""
        return LHTMLParser(remove_blank_text=True, remove_comments=True, remove_pis=True, collect_ids=False)

    def extract_tree(self, html_text: str) -> html.Element:
        """Extract html tree from html text"""
        return html.fromstring(html_text, parser=self.parser)

    @abstractmethod
    def extract_results(self, html_text: str) -> list[dict[str, Any]]:
        """Extract search results from lxml tree"""
        raise NotImplementedError

    def normalize_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for result in results:
            for key, value in result.items():
                # skip empty
                if key in {"title", "body", "href", "url", "image"} and not (
                    value := value.strip() if isinstance(value, str) else value
                ):
                    continue
                if key in {"title", "body"}:
                    result[key] = _normalize_text(value)
                elif key in {"href", "url", "thumbnail", "image"}:
                    result[key] = _normalize_url(value)
                elif key == "date" and isinstance(value, int):
                    result[key] = datetime.fromtimestamp(value, timezone.utc).isoformat()  # int to readable date
                else:
                    result[key] = value
        return results

    def search(
        self,
        query: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
        **kwargs: Any,
    ) -> list[dict[str, Any]] | None:
        """Search the engine"""
        payload = self.build_payload(
            query=query, region=region, safesearch=safesearch, timelimit=timelimit, page=page, **kwargs
        )
        if self.search_method == "GET":
            html_text = self.request(self.search_method, self.search_url, params=payload, headers=self.search_headers)
        else:
            html_text = self.request(self.search_method, self.search_url, data=payload, headers=self.search_headers)
        if html_text:
            results = self.extract_results(html_text)
            results = self.normalize_results(results)
            return results
        return None
