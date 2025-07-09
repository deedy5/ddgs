from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from functools import cached_property
from typing import Any

from lxml import html
from lxml.etree import HTMLParser as LHTMLParser

from .http_client import HttpClient
from .results import SearchResult
from .utils import _normalize_text, _normalize_url


class BaseSearchEngine(ABC):
    search_url: str
    search_method: str  # GET or POST

    def __init__(self, proxy: str | None = None, timeout: int | None = None):
        self.http_client = HttpClient(proxy=proxy, timeout=timeout)
        self.results: list[SearchResult] = []

    def build_params(self, query: str, region: str | None, timelimit: str | None, page: int) -> dict[str, Any]:
        """
        Override in GET-based engines.
        Return an empty dict by default.
        """
        return {}

    def build_payload(self, query: str, region: str | None, timelimit: str | None, page: int) -> dict[str, Any]:
        """
        Override in POST-based engines.
        Return an empty dict by default.
        """
        return {}

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

    def parse_tree(self, html_text: str) -> html.Element:
        """Parse lxml tree from html text"""
        tree = html.fromstring(html_text, parser=self.parser)
        return tree

    @abstractmethod
    def extract_results(self, tree: html.Element) -> list[dict[str, Any]]:
        """Extract search results from lxml tree"""
        raise NotImplementedError

    def normalize_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for result in results:
            result["title"] = _normalize_text(result["title"])
            result["href"] = _normalize_url(result["href"])
            result["body"] = _normalize_text(result["body"])
        return results

    def search(
        self, query: str, region: str | None = None, timelimit: str | None = None, page: int = 1
    ) -> list[dict[str, Any]] | None:
        """Search the engine"""
        params = self.build_params(query=query, region=region, timelimit=timelimit, page=page)
        payload = self.build_payload(query=query, region=region, timelimit=timelimit, page=page)
        html_text = self.request(self.search_method, self.search_url, params=params, data=payload)
        if html_text:
            tree = self.parse_tree(html_text)
            results = self.extract_results(tree)
            results = self.normalize_results(results)
            return results
        return None
