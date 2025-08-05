from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, wait
from math import ceil
from random import random, shuffle
from types import TracebackType
from typing import Any

from .base import BaseSearchEngine
from .engines import ENGINES
from .exceptions import DDGSException, TimeoutException
from .results import ResultsAggregator
from .similarity import SimpleFilterRanker
from .utils import _expand_proxy_tb_alias

logger = logging.getLogger(__name__)


class DDGS:
    threads: int | None = None
    _executor: ThreadPoolExecutor | None = None

    def __init__(self, proxy: str | None = None, timeout: int | None = 5, verify: bool = True):
        self._proxy = _expand_proxy_tb_alias(proxy) or os.environ.get("DDGS_PROXY")
        self._timeout = timeout
        self._verify = verify
        self._engines_cache: dict[
            type[BaseSearchEngine[Any]], BaseSearchEngine[Any]
        ] = {}  # dict[engine_class, engine_instance]

    def __enter__(self) -> DDGS:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        pass

    @classmethod
    def get_executor(cls) -> ThreadPoolExecutor:
        """Get a ThreadPoolExecutor instance and cache it."""
        if cls._executor is None:
            cls._executor = ThreadPoolExecutor(max_workers=cls.threads, thread_name_prefix="DDGS")
        return cls._executor

    def _get_engines(
        self,
        category: str,
        backend: str,
    ) -> list[BaseSearchEngine[Any]]:
        """
        Retrieve a list of search engine instances for a given category and backend.

        Args:
            category: The category of search engines (e.g., 'text', 'images', etc.).
            backend: A single or comma-delimited backends. Defaults to "auto".

        Returns:
            A list of initialized search engine instances corresponding to the specified
            category and backend. Instances are cached for reuse.
        """
        if isinstance(backend, list):  # deprecated
            backend = ",".join(backend)
        backend_list = [x.strip() for x in backend.split(",")]
        engine_keys = list(ENGINES[category].keys())
        shuffle(engine_keys)
        if "auto" in backend_list or "all" in backend_list:
            keys = engine_keys
            if category == "text":
                # ensure Wikipedia is always included and in the first position
                keys = ["wikipedia"] + [key for key in keys if key != "wikipedia"]
        else:
            keys = backend_list

        try:
            engine_classes = [ENGINES[category][key] for key in keys]
            # Initialize and cache engine instances
            instances = []
            for engine_class in engine_classes:
                # If already cached, use the cached instance
                if engine_class in self._engines_cache:
                    instances.append(self._engines_cache[engine_class])
                # If not cached, create a new instance
                else:
                    engine_instance = engine_class(proxy=self._proxy, timeout=self._timeout, verify=self._verify)
                    self._engines_cache[engine_class] = engine_instance
                    instances.append(engine_instance)

            # sorting by `engine.priority`
            instances.sort(key=lambda e: (e.priority, random), reverse=True)
            return instances
        except KeyError as ex:
            logger.warning(
                f"{ex!r} - backend is not exist or disabled. Available: {', '.join(sorted(engine_keys))}. Using 'auto'"
            )
            return self._get_engines(category, "auto")

    def _search(
        self,
        category: str,
        query: str,
        *,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        max_results: int | None = 10,
        page: int = 1,
        backend: str = "auto",
        # deprecated aliases:
        keywords: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Perform a search across engines in the given category.

        Args:
            category: The category of search engines (e.g., 'text', 'images', etc.).
            query: The search query.
            region: The region to use for the search (e.g., us-en, uk-en, ru-ru, etc.).
            safesearch: The safesearch setting (e.g., on, moderate, off).
            timelimit: The timelimit for the search (e.g., d, w, m, y) or custom date range.
            max_results: The maximum number of results to return. Defaults to 10.
            page: The page of results to return. Defaults to 1.
            backend: A single or comma-delimited backends. Defaults to "auto".

        Returns:
            A list of dictionaries containing the search results.
        """
        query = keywords or query
        assert query, "Query is mandatory."

        engines = self._get_engines(category, backend)
        len_unique_providers = len({engine.provider for engine in engines})
        seen_providers: set[str] = set()

        # Perform search
        results_aggregator: ResultsAggregator[set[str]] = ResultsAggregator(set(["href", "image", "url", "embed_url"]))
        max_workers = min(len_unique_providers, ceil(max_results / 10) + 1) if max_results else len_unique_providers
        executor = self.get_executor()
        futures, err = {}, None
        for i, engine in enumerate(engines, start=1):
            if engine.provider in seen_providers:
                continue
            future = executor.submit(
                engine.search,
                query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                page=page,
                max_results=max_results,
                **kwargs,
            )
            futures[future] = engine

            if len(futures) >= max_workers or i >= max_workers:
                done, not_done = wait(futures, timeout=self._timeout, return_when="FIRST_EXCEPTION")
                for future in futures:
                    if future in done:
                        try:
                            if r := future.result():
                                results_aggregator.extend(r)
                                seen_providers.add(futures[future].provider)
                        except Exception as ex:
                            err = ex
                            logger.info(f"engine:{futures[future].name}: {type(ex).__name__}: {ex!r}")
                futures = {f: futures[f] for f in not_done}

            if max_results and len(results_aggregator) >= max_results:
                break

        results = results_aggregator.extract_dicts()
        # Rank results
        ranker = SimpleFilterRanker()
        results = ranker.rank(results, query)

        if results:
            return results[:max_results] if max_results else results

        if "timed out" in f"{err}":
            raise TimeoutException(err)
        raise DDGSException(err or "No results found.")

    def text(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        return self._search("text", query, **kwargs)

    def images(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        return self._search("images", query, **kwargs)

    def news(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        return self._search("news", query, **kwargs)

    def videos(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        return self._search("videos", query, **kwargs)

    def books(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        return self._search("books", query, **kwargs)
