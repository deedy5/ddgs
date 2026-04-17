"""DDGS class implementation."""

import asyncio
import atexit
import logging
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait
from math import ceil
from pathlib import Path
from random import random, shuffle
from types import TracebackType
from typing import Any, ClassVar

import primp

from .base import BaseSearchEngine
from .engines import ENGINES
from .exceptions import DDGSException, TimeoutException
from .http_client import HttpClient
from .results import ResultsAggregator
from .similarity import SimpleFilterRanker
from .utils import _expand_proxy_tb_alias

logger = logging.getLogger(__name__)

DEFAULT_API_URL = "http://localhost:4479"
NETWORK_START_TIMEOUT = 10.0
NETWORK_CHECK_INTERVAL = 0.5


_http_client: primp.Client | None = None
_cache_executor: ThreadPoolExecutor | None = None
_network_lock = threading.Lock()
_async_loop: asyncio.AbstractEventLoop | None = None
_async_thread: threading.Thread | None = None


def _cleanup_api_process() -> None:
    """Cleanup any spawned API server process on exit."""
    if DDGS._api_process is not None:
        try:
            if DDGS._api_process.poll() is None:
                logger.info("Stopping spawned API server (PID: %d)", DDGS._api_process.pid)
                DDGS._api_process.terminate()
                DDGS._api_process.wait(timeout=5.0)
        except Exception as ex:  # noqa: BLE001
            logger.debug("Failed to stop API server: %r", ex)
            try:
                DDGS._api_process.kill()
                DDGS._api_process.wait(timeout=2.0)
            except Exception as ex:  # noqa: BLE001
                logger.debug("Failed to kill API server: %r", ex)
        finally:
            DDGS._api_process = None

    global _async_loop, _async_thread  # noqa: PLW0603
    if _async_loop is not None and _async_loop.is_running():
        try:
            _async_loop.call_soon_threadsafe(_async_loop.stop)
            if _async_thread is not None:
                _async_thread.join(timeout=5.0)
        except Exception as ex:  # noqa: BLE001
            logger.debug("Failed to stop async loop: %r", ex)
        finally:
            _async_loop = None
            _async_thread = None

    # Cleanup cache executor
    global _cache_executor  # noqa: PLW0603
    if _cache_executor is not None:
        try:
            _cache_executor.shutdown(wait=True)
        except Exception as ex:  # noqa: BLE001
            logger.debug("Failed to shutdown cache executor: %r", ex)
        finally:
            _cache_executor = None


# Register cleanup handlers
atexit.register(_cleanup_api_process)


def _get_cache_executor() -> ThreadPoolExecutor:
    """Get shared thread pool executor for background cache operations."""
    global _cache_executor  # noqa: PLW0603
    if _cache_executor is None:
        # Use a small fixed pool size to avoid thread exhaustion
        _cache_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="DDGS-Cache")
    return _cache_executor


def _get_http_client() -> primp.Client:
    """Get or create the shared primp HTTP client."""
    global _http_client  # noqa: PLW0603
    if _http_client is None:
        _http_client = primp.Client(timeout=5)
    return _http_client


def _get_async_loop() -> asyncio.AbstractEventLoop:
    """Get or create shared async loop running in dedicated thread."""
    global _async_loop, _async_thread  # noqa: PLW0603
    if _async_loop is None:
        with _network_lock:
            if _async_loop is None:
                _async_loop = asyncio.new_event_loop()

                def _run_loop() -> None:
                    asyncio.set_event_loop(_async_loop)
                    _async_loop.run_forever()

                _async_thread = threading.Thread(target=_run_loop, daemon=True)
                _async_thread.start()
    return _async_loop


class DDGS:
    """DDGS | Dux Distributed Global Search.

    A metasearch library that aggregates results from diverse web search services.

    Args:
        proxy: The proxy to use for the search. Defaults to None.
        timeout: The timeout for the search. Defaults to 5.
        verify: bool (True to verify, False to skip) or str path to a PEM file. Defaults to True.

    Attributes:
        threads: The maximum number of threads per search. Defaults to None (automatic, based on max_results).

    Raises:
        DDGSException: If an error occurs during the search.

    Example:
        >>> from ddgs import DDGS
        >>> results = DDGS().search("python")

    """

    threads: ClassVar[int | None] = None
    _network_client: ClassVar[Any] = None
    _api_process: ClassVar[subprocess.Popen[str] | None] = None

    def __init__(
        self,
        proxy: str | None = None,
        timeout: int | None = 5,
        *,
        verify: bool | str = True,
        api_url: str | None = None,
        spawn_api: bool = False,
    ) -> None:
        self._proxy = _expand_proxy_tb_alias(proxy) or os.environ.get("DDGS_PROXY")
        self._timeout = timeout
        self._verify = verify
        self._api_url = api_url
        self._spawn_api = spawn_api
        self._engines_cache: dict[
            type[BaseSearchEngine[Any]], BaseSearchEngine[Any]
        ] = {}  # dict[engine_class, engine_instance]

        # Only enable network if api_url is provided
        if self._api_url and DDGS._network_client is None:
            self._ensure_network_running()

    def __enter__(self) -> "DDGS":  # noqa: PYI034
        """Enter the context manager and return the DDGS instance."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        """Exit the context manager."""

    def _ensure_network_running(self) -> None:  # noqa: C901, PLR0912
        """Ensure the network service is running.

        If not running, spawn a new ddgs api process only if spawn_api is True.
        """
        if DDGS._network_client is not None:
            return

        with _network_lock:
            if DDGS._network_client is not None:
                return

            api_url = self._api_url or DEFAULT_API_URL

            # Check if API is already running
            try:
                resp = _get_http_client().get(f"{api_url}/health")
                if resp.status_code == 200:
                    # Import DhtClient only when needed (optional dependency)
                    from .dht import DhtClient  # noqa: PLC0415

                    DDGS._network_client = DhtClient(api_url=api_url)
                    logger.info("Network client ready: %s", api_url)
                    return
            except ImportError:
                # DHT dependencies not installed - continue without network cache
                logger.debug("DHT dependencies not available - network cache disabled")
            except Exception as ex:  # noqa: BLE001
                logger.debug("API health check failed: %r", ex)

            # API not running, spawn new process only if explicitly requested
            if self._spawn_api and (DDGS._api_process is None or DDGS._api_process.poll() is not None):
                try:
                    venv_bin = str(Path(sys.executable).parent)
                    env = {**os.environ, "PATH": f"{venv_bin}{os.pathsep}{os.environ.get('PATH', '')}"}
                    DDGS._api_process = subprocess.Popen(
                        [sys.executable, "-m", "ddgs", "api", "-d"],
                        env=env,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                        text=True,
                    )
                    logger.info("Spawned ddgs api service (PID: %d)", DDGS._api_process.pid)
                except Exception as ex:  # noqa: BLE001
                    logger.warning("Failed to spawn ddgs api: %r", ex)
                    return

            start_time = time.time()
            while time.time() - start_time < NETWORK_START_TIMEOUT:
                try:
                    resp = _get_http_client().get(f"{api_url}/health")
                    if resp.status_code == 200:
                        break
                except Exception:  # noqa: BLE001, S110
                    pass

                # Check remaining time before sleeping
                remaining = NETWORK_START_TIMEOUT - (time.time() - start_time)
                if remaining <= 0:
                    break
                time.sleep(min(NETWORK_CHECK_INTERVAL, remaining))
            else:
                logger.warning("Timed out waiting for ddgs api service to start")
                return

            # Import DhtClient only when needed (optional dependency)
            try:
                from .dht import DhtClient  # noqa: PLC0415

                DDGS._network_client = DhtClient(api_url=api_url)
                logger.info("Network client ready: %s", api_url)
            except ImportError:
                logger.debug("DHT dependencies not available - network cache disabled")

    def _get_network_client(self) -> Any:  # noqa: ANN401
        """Get the network client for caching.

        Returns:
            DhtClient instance if available, None otherwise.

        """
        return DDGS._network_client

    def _cache_results_async(
        self,
        query: str,
        results: list[dict[str, Any]],
        category: str,
    ) -> None:
        """Cache search results asynchronously."""
        network = self._get_network_client()
        if not network:
            return

        def _cache_worker() -> None:
            try:
                loop = _get_async_loop()
                future = asyncio.run_coroutine_threadsafe(network.cache(query, results, category), loop)
                future.result(timeout=10.0)
                logger.debug("Cached results: %s", query)
            except Exception as ex:  # noqa: BLE001
                logger.debug("Cache failed: %r", ex)

        executor = _get_cache_executor()
        executor.submit(_cache_worker)

    def _get_engines(
        self,
        category: str,
        backend: str,
    ) -> list[BaseSearchEngine[Any]]:
        """Retrieve a list of search engine instances for a given category and backend.

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
                keys = ["wikipedia", "grokipedia"] + [k for k in keys if k not in ("wikipedia", "grokipedia")]
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
        except KeyError as ex:
            logger.warning(
                "%r - backend is not exist or disabled. Available: %s. Using 'auto'",
                ex,
                ", ".join(sorted(engine_keys)),
            )
            return self._get_engines(category, "auto")
        else:
            return instances

    def _search_sync(  # noqa: C901, PLR0912
        self,
        category: str,
        query: str,
        keywords: str | None = None,
        *,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        max_results: int | None = 10,
        page: int = 1,
        backend: str = "auto",
        **kwargs: str,
    ) -> list[dict[str, Any]]:
        """Perform a search across engines in the given category.

        Args:
            category: The category of search engines (e.g., 'text', 'images', etc.).
            query: The search query.
            keywords: Deprecated alias for `query`.
            region: The region to use for the search (e.g., us-en, uk-en, ru-ru, etc.).
            safesearch: The safesearch setting (e.g., on, moderate, off).
            timelimit: The timelimit for the search (e.g., d, w, m, y) or custom date range.
            max_results: The maximum number of results to return. Defaults to 10.
            page: The page of results to return. Defaults to 1.
            backend: A single or comma-delimited backends. Defaults to "auto".
            **kwargs: Additional keyword arguments to pass to the search engines.

        Returns:
            A list of dictionaries containing the search results.

        """
        query = keywords or query
        if not query:
            msg = "query is mandatory."
            raise DDGSException(msg)

        network = self._get_network_client()
        if network:
            try:
                loop = _get_async_loop()
                future = asyncio.run_coroutine_threadsafe(network.get_cached(query, category), loop)
                cached = future.result(timeout=1.0)
                if cached:
                    logger.debug("Cache hit: %s", query)
                    return cached  # type: ignore[no-any-return]
            except Exception as ex:  # noqa: BLE001
                # Any cache failure, proceed normally to search
                logger.debug("Cache check failed: %r", ex)

        engines = self._get_engines(category, backend)
        len_unique_providers = len({engine.provider for engine in engines})
        seen_providers: set[str] = set()

        # Perform search
        results_aggregator: ResultsAggregator[set[str]] = ResultsAggregator({"href", "image", "url", "embed_url"})
        max_workers = min(len_unique_providers, ceil(max_results / 10) + 1) if max_results else len_unique_providers
        if DDGS.threads:
            max_workers = min(max_workers, DDGS.threads)
        futures, err = {}, None
        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="DDGS") as executor:
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
                    **kwargs,
                )
                futures[future] = engine

                if len(futures) >= max_workers or i >= max_workers:
                    done, not_done = wait(futures, timeout=self._timeout, return_when="FIRST_EXCEPTION")
                    for f, f_engine in futures.items():
                        if f in done:
                            try:
                                if r := f.result():
                                    results_aggregator.extend(r)
                                    seen_providers.add(f_engine.provider)
                            except Exception as ex:  # noqa: BLE001
                                err = ex
                                logger.info("Error in engine %s: %r", f_engine.name, ex)
                    futures = {f: futures[f] for f in not_done}

                if max_results and len(results_aggregator) >= max_results:
                    break

        results = results_aggregator.extract_dicts()
        # Rank results
        ranker = SimpleFilterRanker()
        results = ranker.rank(results, query)

        if results:
            if network:
                self._cache_results_async(query, results, category)
            return results[:max_results] if max_results else results

        if "timed out" in f"{err}":
            raise TimeoutException(err)
        raise DDGSException(err or "No results found.")

    def text(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ANN401
        """Perform a text search."""
        return self._search_sync("text", query, **kwargs)

    def images(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ANN401
        """Perform an image search."""
        return self._search_sync("images", query, **kwargs)

    def news(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ANN401
        """Perform a news search."""
        return self._search_sync("news", query, **kwargs)

    def videos(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ANN401
        """Perform a video search."""
        return self._search_sync("videos", query, **kwargs)

    def books(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ANN401
        """Perform a book search."""
        return self._search_sync("books", query, **kwargs)

    def extract(self, url: str, fmt: str = "text_markdown") -> dict[str, str | bytes]:
        """Fetch a URL and extract its content.

        Args:
            url: The URL to fetch and extract content from.
            fmt: Output format: "text_markdown", "text_plain", "text_rich", "text" (raw HTML), "content" (raw bytes).

        Returns:
            A dictionary with 'url' and 'content' keys.

        """
        client = HttpClient(proxy=self._proxy, timeout=self._timeout, verify=self._verify)
        resp = client.get(url)
        if resp.status_code != 200:
            msg = f"Failed to fetch {url}: HTTP {resp.status_code}"
            raise DDGSException(msg)

        content_map: dict[str, str | bytes] = {
            "text_markdown": resp.text_markdown,
            "text_plain": resp.text_plain,
            "text_rich": resp.text_rich,
            "text": resp.text,
            "content": resp.content,
        }
        return {"url": url, "content": content_map.get(fmt, resp.text_markdown)}
