from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from math import ceil
from random import shuffle
from types import TracebackType
from typing import Any, Literal

from .base import BaseSearchEngine
from .engines import ENGINES
from .exceptions import DDGSException, TimeoutException
from .results import ResultsAggregator
from .utils import _expand_proxy_tb_alias

logger = logging.getLogger(__name__)


class DDGS:
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

    def _get_engines(
        self,
        category: str,
        backend: str | list[str],
    ) -> list[BaseSearchEngine[Any]]:
        """
        Retrieve a list of search engine instances for a given category and backend.

        Args:
            category: The category of search engines (e.g., 'text', 'images', etc.).
            backend: A single or list of backends. Defaults to "auto".

        Returns:
            A list of initialized search engine instances corresponding to the specified
            category and backend. Instances are cached for reuse.
        """
        backend = [backend] if isinstance(backend, str) else list(backend) if isinstance(backend, tuple) else backend
        engine_keys = list(ENGINES[category].keys())
        shuffle(engine_keys)
        keys = engine_keys if "auto" in backend or "all" in backend else backend

        if category == "text":
            # ensure Wikipedia is always included and in the first position
            keys = ["wikipedia"] + [key for key in keys if key != "wikipedia"]

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
            return instances
        except KeyError:
            logger.warning(
                f"Invalid backend: {backend}. Available backends: {', '.join(engine_keys)}. Falling back to 'auto'."
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
        backend: str | list[str] = "auto",
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
            timelimit: The timelimit for the search (e.g., d, w, m, y).
            max_results: The maximum number of results to return. Defaults to 10.
            page: The page of results to return. Defaults to 1.
            backend: A single or list of backends. Defaults to "auto".

        Returns:
            A list of dictionaries containing the search results.
        """
        query = keywords or query
        assert query, "Query is mandatory."

        engines = self._get_engines(category, backend)
        seen_providers: dict[str, Literal["working", "seen"]] = {}  # dict[provider, state]

        # Perform search
        results_aggregator: ResultsAggregator[set[str]] = ResultsAggregator(set(["href", "image", "url", "embed_url"]))
        err = None
        max_workers = min(len(engines), ceil(max_results / 10) + 1) if max_results else len(engines)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for engine in engines:
                if seen_providers.setdefault(engine.provider, "working") == "seen":
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

                if len(futures) >= max_workers:
                    for future in as_completed(futures):
                        try:
                            r = future.result(timeout=self._timeout)
                            if r:
                                results_aggregator.extend(r)
                                seen_providers[futures[future].provider] = "seen"
                        except Exception as ex:
                            err = ex
                            # logger.info(f"{type(ex).__name__}: {ex}")
                if max_results and len(results_aggregator) >= max_results:
                    break

        # Rank results
        # ranker = SimpleFilterRanker()
        # results = ranker.rank(results, query)

        results = results_aggregator.extract_dicts()
        if results:
            if max_results and max_results < len(results):
                return results[:max_results]
            return results

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
