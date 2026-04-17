"""Distributed cache DHT module.

This module provides a P2P cache DHT for sharing search results
across multiple ddgs instances using Kademlia DHT.

Usage:
    from ddgs.dht import DhtClient

    # Direct mode (runs Trio in-process)
    client = DhtClient()
    await client.start()

    # REST API mode (connects to ddgs api service)
    client = DhtClient(api_url="http://localhost:4479")

    # Get cached results
    results = await client.get_cached("python tutorial")

    # Store results
    await client.cache("python tutorial", results)

    await client.stop()
"""

import asyncio
import logging
from typing import Any

import primp

from .cache import DEFAULT_TTL, MAX_CACHE_SIZE, ResultCache
from .libp2p_client import DEFAULT_MAX_HOP_CONNECTIONS, Libp2pClient
from .types import compute_query_hash, normalize_query

__all__ = [
    "DEFAULT_MAX_HOP_CONNECTIONS",
    "DEFAULT_TTL",
    "MAX_CACHE_SIZE",
    "DhtClient",
    "Libp2pClient",
    "ResultCache",
    "compute_query_hash",
    "normalize_query",
]

logger = logging.getLogger(__name__)

DEFAULT_API_URL = "http://localhost:4479"
CACHE_TIMEOUT = 1.0


class DhtClient:
    """Client for the distributed cache DHT.

    Provides transparent access to cached results from other peers
    while falling back to direct search engine queries when needed.

    Supports two modes:
    - Direct mode (api_url=None): Runs libp2p/Trio in-process
    - REST mode (api_url set): Connects to ddgs api service via HTTP
    """

    def __init__(
        self,
        *,
        enable_dht: bool = True,
        listen_port: int = 0,
        cache_ttl: int = DEFAULT_TTL,
        max_hop_connections: int = DEFAULT_MAX_HOP_CONNECTIONS,
        api_url: str | None = None,
    ) -> None:
        self.enable_dht = enable_dht
        self.cache_ttl = cache_ttl
        self.api_url = (api_url or DEFAULT_API_URL) if enable_dht and api_url is not None else None
        self._started = False
        self._dht: Libp2pClient | None
        self._cache: ResultCache | None

        if self.api_url:
            self._dht = None
            self._cache = None
        else:
            self._dht = Libp2pClient(
                listen_port=listen_port,
                bootstrap=enable_dht,
                max_hop_connections=max_hop_connections,
            )
            self._cache = ResultCache()

    async def start(self) -> bool:
        """Start the DHT client.

        Returns:
            True if DHT connection successful.

        """
        if self._started:
            return True

        if self.api_url:
            logger.info("DHT client started (REST API mode): %s", self.api_url)
        elif self.enable_dht and self._dht is not None:
            # Run blocking start in thread to not block async loop
            connected = await asyncio.to_thread(self._dht.start)
            logger.info(
                "DHT client started: connected=%s, port=%d",
                connected,
                self._dht.port,
            )
        else:
            logger.info("DHT client started (DHT disabled)")

        self._started = True
        return self._started

    async def _get_from_api(self, query: str, category: str) -> list[dict[str, Any]] | None:
        """Get cached results from API."""
        normalized = normalize_query(query)
        try:
            async with primp.AsyncClient(timeout=CACHE_TIMEOUT) as client:
                resp = await client.get(
                    f"{self.api_url}/dht/cache",
                    params={"query": query, "category": category},
                )
                if resp.status_code == 200:
                    try:
                        data: dict[str, Any] = resp.json()
                        if results := data.get("results"):
                            logger.debug("Cache hit (DHT API): %s", normalized)
                            return results  # type: ignore[no-any-return]
                    except Exception as ex:  # noqa: BLE001
                        logger.debug("Failed to parse API response: %r", ex)
        except Exception as ex:  # noqa: BLE001
            logger.debug("DHT API get failed for %s: %r", normalized, ex)
        return None

    async def get_cached(
        self,
        query: str,
        category: str = "text",
    ) -> list[dict[str, Any]] | None:
        """Get cached results for a query.

        Checks local cache first, then DHT DHT (or REST API).

        Args:
            query: The search query.
            category: The search category.

        Returns:
            Cached results or None.

        """
        if not self._started:
            await self.start()

        query_hash = compute_query_hash(query, category)
        normalized = normalize_query(query)

        if self.api_url:
            return await self._get_from_api(query, category)

        if self._cache is None:
            return None

        local_results = self._cache.get(query_hash)
        if local_results:
            logger.debug("Cache hit (local): %s", normalized)
            return local_results

        if self._dht is not None and self._dht.is_running:
            dht_results = self._dht.get(query_hash)
            if dht_results:
                logger.debug("Cache hit (DHT): %s", normalized)
                self._cache.set(query_hash, normalized, category, dht_results, self.cache_ttl)
                return dht_results
            # Add to negative cache to avoid repeated DHT lookups
            self._cache.add_negative(query_hash)

        return None

    async def cache(
        self,
        query: str,
        results: list[dict[str, Any]],
        category: str = "text",
    ) -> None:
        """Cache search results locally and on DHT.

        Args:
            query: The search query.
            results: The search results.
            category: The search category.

        """
        if not self._started:
            await self.start()

        query_hash = compute_query_hash(query, category)
        normalized = normalize_query(query)

        if self.api_url:
            try:
                async with primp.AsyncClient(timeout=CACHE_TIMEOUT) as client:
                    resp = await client.post(
                        f"{self.api_url}/dht/cache",
                        json={"query": query, "results": results, "category": category},
                    )
                    if resp.status_code in (200, 201):
                        logger.debug("Cached to DHT API: %s", normalized)
            except Exception as ex:  # noqa: BLE001
                logger.debug("DHT API cache failed for %s: %r", normalized, ex)
            return

        if self._cache is None:
            return

        self._cache.set(query_hash, normalized, category, results, self.cache_ttl)

        if self._dht is not None and self._dht.is_running:
            self._dht.set(query_hash, results, self.cache_ttl)
            logger.debug("Cached to DHT: %s", normalized)

    async def invalidate(self, query: str, category: str = "text") -> None:
        """Invalidate cached results for a query.

        Args:
            query: The search query.
            category: The search category.

        """
        query_hash = compute_query_hash(query, category)

        if self.api_url:
            try:
                async with primp.AsyncClient(timeout=CACHE_TIMEOUT) as client:
                    await client.delete(
                        f"{self.api_url}/dht/cache",
                        params={"query": query, "category": category},
                    )
            except Exception as ex:  # noqa: BLE001
                logger.debug("DHT API invalidate failed: %r", ex)
            return

        if self._cache is None:
            return

        self._cache.delete(query_hash)

    async def stop(self) -> None:
        """Stop the DHT client."""
        if self._dht and self._dht.is_running:
            self._dht.stop()

        self._started = False

    @property
    def is_connected(self) -> bool:
        """Check if the DHT client is connected."""
        if self.api_url:
            return self._started
        return self._dht.is_running if self._dht else False

    @property
    def cache_count(self) -> int:
        """Get the number of cached entries."""
        if self._cache:
            return self._cache.count()
        return 0

    @property
    def cache_size(self) -> int:
        """Get the size of the cache in bytes."""
        if self._cache:
            return self._cache.size_bytes()
        return 0


async def get_dht_client(
    api_url: str | None = None,
) -> DhtClient:
    """Get a shared DHT client instance.

    Args:
        api_url: URL of the ddgs API service. If None, uses direct mode.

    Returns:
        A started DhtClient instance.

    """
    client = DhtClient(api_url=api_url)
    await client.start()
    return client
