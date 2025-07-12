from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from types import TracebackType
from typing import Any

from .base import BaseSearchEngine
from .engines import ENGINES
from .similarity import JaccardRanker


class DDGS:
    def __init__(self, proxy: str | None = None, timeout: int | None = None, verify: bool = True):
        self._proxy = proxy
        self._timeout = timeout
        self._verify = verify
        self._engines_cache: dict[type[BaseSearchEngine], BaseSearchEngine] = {}  # dict[engine_class, engine_instance]

    def __enter__(self) -> DDGS:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        pass

    def _get_engines(
        self,
        category: str,
        backend: str | list[str],
    ) -> list[BaseSearchEngine]:
        """
        Retrieve a list of search engine instances for a given category and backend.

        Args:
            category: The category of search engines (e.g., 'text', 'images', etc.).
            backend: A single or list of backends. Defaults to "auto" (first two).

        Returns:
            A list of initialized search engine instances corresponding to the specified
            category and backend. Instances are cached for reuse.
        """

        instances = []
        engine_keys = ENGINES[category].keys()

        # Determine which engine classes to use based on the backend parameter
        if backend == "auto":
            keys = list(engine_keys)[:2]
        elif isinstance(backend, str):
            keys = [backend]
        elif isinstance(backend, list):
            keys = backend

        try:
            engine_classes = [ENGINES[category][key] for key in keys]
        except KeyError as ex:
            raise ValueError(f"Invalid backend: {backend}") from ex

        # Initialize and cache engine instances
        for engine_class in engine_classes:
            if engine_class in self._engines_cache:
                instances.append(self._engines_cache[engine_class])
            else:
                engine_instance = engine_class(proxy=self._proxy, timeout=self._timeout, verify=self._verify)
                self._engines_cache[engine_class] = engine_instance
                instances.append(engine_instance)
        return instances

    def _search(
        self,
        category: str,
        query: str,
        *,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        num_results: int | None = None,
        page: int = 1,
        backend: str | list[str] = "auto",
        # deprecated aliases:
        keywords: str | None = None,
        max_results: int | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Perform a search across engines in the given category.

        Args:
            category: The category of search engines (e.g., 'text', 'images', etc.).
            query: The search query.
            region: The region to use for the search (e.g., us-en, uk-en, ru-ru, etc.).
            safesearch: The safesearch setting (e.g., on, moderate, off).
            timelimit: The timelimit for the search (e.g., d, w, m, y).
            num_results: The number of results to return.
            page: The page of results to return.
            backend: A single or list of backends. Defaults to "auto" (first two).

        Returns:
            A list of dictionaries containing the search results.
        """
        query = keywords or query
        assert query, "Query is mandatory."

        engines = self._get_engines(category, backend)

        # Perform search
        results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=len(engines)) as executor:
            futures = [
                executor.submit(
                    engine.search,
                    query,
                    region=region,
                    safesearch=safesearch,
                    timelimit=timelimit,
                    page=page,
                    **kwargs,
                )
                for engine in engines
            ]
            for future in as_completed(futures):
                try:
                    partial = future.result()
                    if partial:
                        results.extend(partial)
                except Exception as e:
                    logging.warning("Engine failed:", exc_info=e)

        # Rank results
        ranker = JaccardRanker()
        results = ranker.rank(results, query)

        # Slice to requested number of results
        if (num_results := num_results or max_results) and num_results < len(results):
            return results[:num_results]
        return results

    def text(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        return self._search("text", query, **kwargs)

    def images(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        return self._search("images", query, **kwargs)

    def news(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        return self._search("news", query, **kwargs)

    def videos(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        return self._search("videos", query, **kwargs)
