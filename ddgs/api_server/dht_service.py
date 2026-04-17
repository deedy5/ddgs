"""DHT service for distributed cache - runs in background thread with Trio."""

import logging
import threading
import time
from typing import Any

import trio

from ddgs.dht import Libp2pClient, ResultCache, compute_query_hash, normalize_query
from ddgs.dht.cache import DEFAULT_TTL
from ddgs.dht.libp2p_client import DEFAULT_MAX_HOP_CONNECTIONS

logger = logging.getLogger(__name__)


class DhtService:
    """Background service running Trio event loop with Libp2pClient and ResultCache.

    Provides thread-safe access to distributed cache DHT from FastAPI.
    """

    def __init__(
        self,
        *,
        listen_port: int = 0,
        cache_ttl: int = DEFAULT_TTL,
        max_hop_connections: int = DEFAULT_MAX_HOP_CONNECTIONS,
    ) -> None:
        self.listen_port = listen_port
        self.cache_ttl = cache_ttl
        self.max_hop_connections = max_hop_connections

        self._dht: Libp2pClient | None = None
        self._cache: ResultCache | None = None
        self._thread: threading.Thread | None = None
        self._started = False
        self._start_event = threading.Event()
        self._stop_event = threading.Event()
        self._trio_token: trio.lowlevel.TrioToken | None = None

    def _run_trio(self) -> None:
        """Run Trio event loop in background thread."""

        async def _main() -> None:
            self._trio_token = trio.lowlevel.current_trio_token()
            self._cancel_scope = trio.CancelScope()
            self._dht = Libp2pClient(
                listen_port=self.listen_port,
                bootstrap=True,
                max_hop_connections=self.max_hop_connections,
            )
            self._cache = ResultCache()

            # Use async start directly now that libp2p is properly async
            await self._dht.astart()
            logger.info(
                "Network service started: connected=%s, port=%d",
                self._dht.is_running,
                self._dht.port,
            )
            self._start_event.set()

            with self._cancel_scope:
                await trio.sleep_forever()

        try:
            trio.run(_main)
        except Exception as ex:  # noqa: BLE001
            logger.warning("Network service loop exited: %r", ex)
        finally:
            self._start_event.set()
            self._stop_event.set()

    def start(self, timeout: float = 10.0) -> bool:
        """Start the DHT service in background thread.

        Args:
            timeout: Maximum time to wait for service to start.

        Returns:
            True if service started successfully.

        """
        if self._started:
            return True

        self._thread = threading.Thread(target=self._run_trio, daemon=True)
        self._thread.start()

        if self._start_event.wait(timeout=timeout):
            self._started = True
            return True
        logger.warning("Network service failed to start within %ds", timeout)
        return False

    def stop(self) -> None:
        """Stop the DHT service."""
        if not self._started or self._dht is None:
            return

        # Cancel the main loop first
        if hasattr(self, "_cancel_scope"):
            self._cancel_scope.cancel()

        try:
            self._dht.stop()
        except Exception as ex:  # noqa: BLE001
            logger.warning("Error stopping DHT service: %r", ex)

        if self._thread:
            self._thread.join(timeout=5.0)

        self._started = False

    def _run_in_trio(self, func: Any, *args: Any) -> Any:  # noqa: ANN401
        """Run an async function in the Trio event loop from another thread."""
        if not self._started or self._trio_token is None:
            return None

        async def _wrapped() -> Any:  # noqa: ANN401
            with trio.fail_after(30):
                return await func(*args)

        return trio.from_thread.run(_wrapped, trio_token=self._trio_token)

    def get_cached(self, query: str, category: str = "text") -> list[dict[str, Any]] | None:
        """Get cached results synchronously (for use from FastAPI).

        Args:
            query: The search query.
            category: The search category.

        Returns:
            Cached results or None.

        """
        if not self._started or self._dht is None or self._cache is None:
            return None

        query_hash = compute_query_hash(query, category)
        normalized = normalize_query(query)

        local_results = self._cache.get(query_hash)
        if local_results:
            logger.debug("Cache hit (local): %s", normalized)
            return local_results

        if self._dht.is_running:
            try:
                dht_results: list[dict[str, Any]] | None = self._run_in_trio(self._dht.aget, query_hash)
                if dht_results:
                    logger.debug("Cache hit (network): %s", normalized)
                    self._cache.set(query_hash, normalized, category, dht_results, self.cache_ttl)
                    return dht_results
                # Add to negative cache to avoid repeated DHT lookups
                self._cache.add_negative(query_hash)
            except Exception as ex:  # noqa: BLE001
                logger.debug("DHT get failed for %s: %r", query_hash, ex)

        return None

    def cache(self, query: str, results: list[dict[str, Any]], category: str = "text") -> None:
        """Cache search results synchronously (for use from FastAPI).

        Args:
            query: The search query.
            results: The search results.
            category: The search category.

        """
        if not self._started or self._dht is None or self._cache is None:
            return

        query_hash = compute_query_hash(query, category)
        normalized = normalize_query(query)

        self._cache.set(query_hash, normalized, category, results, self.cache_ttl)

        if self._dht.is_running:
            try:
                self._run_in_trio(self._dht.aset, query_hash, results, self.cache_ttl)
                logger.debug("Cached to network: %s", normalized)
            except Exception as ex:  # noqa: BLE001
                logger.debug("DHT set failed for %s: %r", query_hash, ex)

    def get_status(self) -> dict[str, Any]:
        """Get DHT service status.

        Returns:
            Dict with status information.

        """
        if not self._started or self._dht is None:
            return {
                "running": False,
                "connected": False,
                "peer_id": None,
                "port": None,
                "cache_size": 0,
                "cache_count": 0,
                "metrics": {},
            }

        return {
            "running": True,
            "connected": self._dht.is_running,
            "peer_id": self._dht.peer_id,
            "port": self._dht.port,
            "listen_addrs": self._dht.listen_addrs,
            "cache_size": self._cache.size_bytes() if self._cache else 0,
            "cache_count": self._cache.count() if self._cache else 0,
            "peer_count": len(self._dht.find_peers()),
            "routing_table_size": self._dht.routing_table_size,
            "metrics": {
                "query_success_rate": self._dht.query_success_rate,
                "average_query_latency_ms": self._dht.average_query_latency_ms,
                "kbucket_distribution": self._dht.kbucket_distribution,
                "uptime_seconds": time.time() - self._dht.metrics["started_at"],
            },
        }

    def get_peers(self) -> list[str]:
        """Get list of connected peers.

        Returns:
            List of peer IDs.

        """
        if not self._started or self._dht is None:
            return []

        try:
            peers: list[str] = self._run_in_trio(self._dht.afind_peers)
        except Exception as ex:  # noqa: BLE001
            logger.debug("Failed to get peers: %r", ex)
            return []
        else:
            return peers or []

    @property
    def is_running(self) -> bool:
        """Check if DHT service is running."""
        return self._started and self._dht is not None and self._dht.is_running

    @property
    def cache_count(self) -> int:
        """Get number of cached entries."""
        return self._cache.count() if self._cache else 0

    @property
    def cache_size(self) -> int:
        """Get cache size in bytes."""
        return self._cache.size_bytes() if self._cache else 0


_dht_service: DhtService | None = None
_dht_service_lock = threading.Lock()


def get_dht_service() -> DhtService:
    """Get the global DHT service instance.

    Returns:
        DhtService singleton.

    """
    global _dht_service  # noqa: PLW0603
    with _dht_service_lock:
        if _dht_service is None:
            _dht_service = DhtService()
            _dht_service.start()
    return _dht_service
