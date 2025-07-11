from __future__ import annotations

from types import TracebackType
from typing import Any

from .base import BaseSearchEngine
from .engines import images_engines_dict, news_engines_dict, text_engines_dict, videos_engines_dict
from .engines.google import Google


class DDGS:
    def __init__(self, proxy: str | None = None, timeout: int | None = None, verify: bool = True):
        self._engines: dict[str, list[BaseSearchEngine]] = {
            "text": [E(proxy, timeout, verify) for E in text_engines_dict.values()],
            "images": [E(proxy, timeout, verify) for E in images_engines_dict.values()],
            "news": [E(proxy, timeout, verify) for E in news_engines_dict.values()],
            "videos": [E(proxy, timeout, verify) for E in videos_engines_dict.values()],
        }

    def __enter__(self) -> DDGS:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        pass

    def _search(
        self,
        category: str,
        query: str,
        *,
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
        backend: str = "auto",
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Generic search over a given engine category.
        category must be one of 'text', 'images', 'news', 'videos'.
        """
        results: list[dict[str, Any]] = []

        if backend == "auto":
            engines: list[BaseSearchEngine] = self._engines.get(category, [])
            for engine in engines:
                if category == "text" and not isinstance(engine, Google):  # only google for text search, TODO: fix
                    continue
                engine_results = engine.search(
                    query, region=region, safesearch=safesearch, timelimit=timelimit, page=page, **kwargs
                )
                if engine_results:
                    results.extend(engine_results)

        return results

    def text(
        self,
        query: str,
        keywords: str | None = None,  # deprecated
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        num_results: int | None = None,
        max_results: int | None = None,  # deprecated
        page: int = 1,
        backend: str = "auto",
    ) -> list[dict[str, Any]]:
        results = self._search(
            "text",
            query if keywords is None else keywords,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=page,
            backend=backend,
        )
        if num_results := num_results or max_results:
            results = results[:num_results]
        return results

    def images(
        self,
        query: str,
        keywords: str | None = None,  # deprecated
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        num_results: int | None = None,
        max_results: int | None = None,  # deprecated
        page: int = 1,
        backend: str = "auto",
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        results = self._search(
            "images",
            query if keywords is None else keywords,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=page,
            backend=backend,
            **kwargs,
        )
        if num_results := num_results or max_results:
            results = results[:num_results]
        return results

    def news(
        self,
        query: str,
        keywords: str | None = None,  # deprecated
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        num_results: int | None = None,
        max_results: int | None = None,  # deprecated
        page: int = 1,
        backend: str = "auto",
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        results = self._search(
            "news",
            query if keywords is None else keywords,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=page,
            backend=backend,
            **kwargs,
        )
        if num_results := num_results or max_results:
            results = results[:num_results]
        return results

    def videos(
        self,
        query: str,
        keywords: str | None = None,  # deprecated
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        num_results: int | None = None,
        max_results: int | None = None,  # deprecated
        page: int = 1,
        backend: str = "auto",
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        results = self._search(
            "videos",
            query if keywords is None else keywords,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=page,
            backend=backend,
            **kwargs,
        )
        if num_results := num_results or max_results:
            results = results[:num_results]
        return results
