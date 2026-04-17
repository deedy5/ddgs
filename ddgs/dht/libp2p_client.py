"""libp2p DHT client for distributed cache network."""

import json
import logging
import secrets
import socket
import threading
import time
from typing import TYPE_CHECKING, Any

import trio

# Optional import for dnsaddr resolution
try:
    import dns.resolver
except ImportError:
    dns = None  # type: ignore[assignment]
from libp2p import new_host
from libp2p.crypto.secp256k1 import create_new_key_pair
from libp2p.custom_types import TProtocol
from libp2p.kad_dht import kad_dht
from libp2p.kad_dht.kad_dht import DHTMode
from libp2p.records.pubkey import PublicKeyValidator
from libp2p.records.validator import NamespacedValidator, Validator
from libp2p.relay.circuit_v2 import CircuitV2Protocol, CircuitV2Transport
from libp2p.relay.circuit_v2.config import RelayConfig
from libp2p.relay.circuit_v2.resources import RelayLimits
from libp2p.stream_muxer.mplex.mplex import Mplex
from libp2p.tools.utils import info_from_p2p_addr  # type: ignore[attr-defined]
from libp2p.utils.address_validation import get_available_interfaces
from multiaddr import Multiaddr

if TYPE_CHECKING:
    from libp2p.abc import IHost

logger = logging.getLogger(__name__)


def _resolve_dnsaddr(multiaddr_str: str) -> list[str]:
    """Resolve /dnsaddr/ multiaddrs into concrete addresses using DNS TXT records.

    Follows libp2p dnsaddr specification:
    - Queries TXT records at _dnsaddr.<domain>
    - Extracts all records starting with "dnsaddr="
    - Gracefully falls back to original address on any failure

    Requires dnspython for full functionality.
    """
    try:
        # Manual parsing since multiaddr library doesn't properly handle /dnsaddr/.../p2p/... format
        parts = multiaddr_str.split("/")
        dnsaddr_domain = None

        for i, part in enumerate(parts):
            if part == "dnsaddr" and i + 1 < len(parts):
                dnsaddr_domain = parts[i + 1]
                break

        if not dnsaddr_domain:
            return [multiaddr_str]

        if dns is None:
            logger.debug("dnspython not installed, skipping dnsaddr resolution")
            return [multiaddr_str]

        # Perform TXT lookup
        answers = dns.resolver.resolve(f"_dnsaddr.{dnsaddr_domain}", "TXT")
        results = []

        for rdata in answers:
            for txt_string in rdata.strings:
                decoded = txt_string.decode("utf-8", errors="replace")
                if decoded.startswith("dnsaddr="):
                    results.append(decoded[8:])

        if results:
            return results
        return [multiaddr_str]  # noqa: TRY300

    except Exception:  # noqa: BLE001
        return [multiaddr_str]


# Raw bootstrap node definitions (official IPFS bootstrap nodes)
# Source: https://docs.ipfs.tech/how-to/modify-bootstrap-list/
_RAW_BOOTSTRAP_NODES = [
    "/dnsaddr/bootstrap.libp2p.io/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN",
    "/dnsaddr/bootstrap.libp2p.io/p2p/QmQCU2EcMqAqQPR2i9bChDtGNJchTbq5TbXJJ16u19uLTa",
    "/dnsaddr/bootstrap.libp2p.io/p2p/QmbLHAnMoJPWSCR5Zhtx6BHJX9KiKNN6tpvbUcqanj75Nb",
    "/dnsaddr/bootstrap.libp2p.io/p2p/QmcZf59bWwK5XFi76CZX8cbJ4BhTzzA3gU1ZjYZcYW3dwt",
    "/ip4/104.131.131.82/tcp/4001/p2p/QmaCpDMGvV2BGHeYERUEnRQAwe3N8SzbUtfsmvsqQLuvuJ",
]

# Resolve all dnsaddr addresses once at module load time
BOOTSTRAP_NODES: list[str] = []
for node in _RAW_BOOTSTRAP_NODES:
    BOOTSTRAP_NODES.extend(_resolve_dnsaddr(node))

DEFAULT_MAX_HOP_CONNECTIONS = 10


class DDGSValidator(Validator):  # type: ignore[misc]
    """Validator for the 'ddgs' namespace."""

    def validate(self, key: str, value: bytes) -> None:  # noqa: ARG002
        """Validate a key-value pair."""
        if not value:
            msg = "Value cannot be empty"
            raise ValueError(msg)

    def select(self, key: str, values: list[bytes]) -> int:  # noqa: ARG002
        """Select the best value (first one)."""
        return 0


class Libp2pClient:
    """libp2p DHT client for distributed cache network."""

    def __init__(
        self,
        *,
        listen_port: int = 0,
        bootstrap: bool = True,
        max_hop_connections: int = DEFAULT_MAX_HOP_CONNECTIONS,
        refresh_interval: int = 3600,  # Refresh DHT records every hour
    ) -> None:
        self.listen_port = listen_port
        self.bootstrap_enabled = bootstrap
        self.max_hop_connections = max_hop_connections
        self._host: IHost | None = None
        self._dht: kad_dht.KadDHT | None = None
        self._running = False
        self._host_cm = None
        self._relay_transport: CircuitV2Transport | None = None
        self._stored_keys: dict[str, tuple[list[dict[str, Any]], int]] = {}
        self._refresh_interval = refresh_interval
        self._dht_thread: threading.Thread | None = None
        self._trio_token: trio.lowlevel.TrioToken | None = None
        self._start_event = threading.Event()
        self._stop_event: threading.Event | None = None
        self._lock = threading.Lock()

        # Metrics tracking
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "total_puts": 0,
            "successful_puts": 0,
            "failed_puts": 0,
            "total_peers_seen": 0,
            "query_latency_sum": 0.0,
            "started_at": time.time(),
        }

    @property
    def query_success_rate(self) -> float:
        """Get DHT query success rate (0-1)."""
        if self.metrics["total_queries"] == 0:
            return 1.0
        return self.metrics["successful_queries"] / self.metrics["total_queries"]

    @property
    def average_query_latency_ms(self) -> float:
        """Get average DHT query latency in milliseconds."""
        if self.metrics["successful_queries"] == 0:
            return 0.0
        return (self.metrics["query_latency_sum"] / self.metrics["successful_queries"]) * 1000

    @property
    def routing_table_size(self) -> int:
        """Get total number of peers in DHT routing table."""
        if not self._dht or not hasattr(self._dht, "routing_table"):
            return 0
        return sum(len(bucket.peers) for bucket in self._dht.routing_table.buckets)

    @property
    def kbucket_distribution(self) -> list[int]:
        """Get peer count per k-bucket (256 buckets total)."""
        if not self._dht or not hasattr(self._dht, "routing_table"):
            return [0] * 256
        return [len(bucket.peers) for bucket in self._dht.routing_table.buckets]

    def _create_host(self) -> "IHost":
        """Create a host with Mplex muxer (default security includes Noise)."""
        secret = secrets.token_bytes(32)
        key_pair = create_new_key_pair(secret)

        # Don't pass sec_opt - use default which includes Noise
        muxer_opt: dict[str, type] = {"/mplex/6.7.0": Mplex}

        # Test if IPv6 is actually working
        has_ipv6 = False
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.bind(("::1", 0))
            sock.close()
            has_ipv6 = True
            logger.debug("IPv6 loopback is functional")
        except OSError:
            logger.debug("IPv6 is not available, using IPv4 only")

        # If listen_port is 0, find an available port first
        if self.listen_port == 0:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", 0))
            self.listen_port = sock.getsockname()[1]
            sock.close()
            logger.debug("Auto-selected port: %d", self.listen_port)

        # Build listen addresses
        listen_addrs = []

        # Always add loopback - we know this port is available since we just bound it
        listen_addrs.append(Multiaddr(f"/ip4/127.0.0.1/tcp/{self.listen_port}"))

        # Add all available non-loopback IPv4 interfaces
        all_addrs = get_available_interfaces(self.listen_port)
        for addr in all_addrs:
            addr_str = str(addr)
            if ("/ip4/" in addr_str and "127.0.0.1" not in addr_str) or (
                has_ipv6 and "/ip6/" in addr_str and "::1" not in addr_str
            ):
                listen_addrs.append(addr)

        if has_ipv6:
            listen_addrs.append(Multiaddr(f"/ip6/::1/tcp/{self.listen_port}"))

        logger.debug("Using listen addresses: %s", [str(a) for a in listen_addrs])

        host = new_host(
            key_pair=key_pair,
            muxer_opt=muxer_opt,  # type: ignore[arg-type]
            listen_addrs=listen_addrs,
            muxer_preference="MPLEX",
        )

        # Store actual bound addresses since new_host may re-bind ports
        self._listen_addrs = host.get_addrs()

        # Update listen_port with actual bound port
        for addr in self._listen_addrs:
            addr_str = str(addr)
            if "/ip4/127.0.0.1/tcp/" in addr_str:
                self.listen_port = int(addr_str.split("/tcp/")[1].split("/")[0])
                break

        return host

    async def _setup_dht(self) -> None:
        """Set up DHT instance with validator."""
        if not self._host:
            return

        validator = NamespacedValidator(
            {
                "pk": PublicKeyValidator(),
                "ddgs": DDGSValidator(),
            }
        )
        self._dht = kad_dht.KadDHT(
            host=self._host,
            mode=DHTMode.SERVER,
            protocol_prefix=TProtocol("/ddgs"),
            validator=validator,
        )

    async def _run_refresh_task(self) -> None:
        """Background task to refresh DHT records periodically."""
        while self._running:
            await trio.sleep(self._refresh_interval)
            if not self._running:
                break

            with self._lock:
                # Make a copy under lock to avoid concurrent modification
                stored_items = list(self._stored_keys.items())

            logger.debug("Refreshing %d DHT records", len(stored_items))
            for key, (results, ttl) in stored_items:
                try:
                    # Re-publish value to refresh its lifetime on the network
                    self.set(key, results, ttl=ttl)
                except Exception as ex:  # noqa: BLE001, PERF203
                    logger.debug("Failed to refresh DHT record %s: %r", key, ex)

    async def _run_main_loop(self) -> None:
        """Run main DHT event loop."""
        from libp2p.tools.anyio_service import AnyIOManager  # noqa: PLC0415

        self._stop_event = threading.Event()

        async with trio.open_nursery() as nursery:
            # Start DHT service
            if self._dht:
                nursery.start_soon(AnyIOManager.run_service, self._dht)

            # Start DHT record refresh background task
            nursery.start_soon(self._run_refresh_task)

            if self._host:
                logger.info(
                    "DHT client started, listening on: %s",
                    [str(addr) for addr in self._host.get_addrs()],
                )

            await trio.to_thread.run_sync(self._stop_event.wait)

    def _run_trio(self) -> None:
        """Run Trio event loop in background thread with all DHT operations."""

        async def _main() -> None:
            self._trio_token = trio.lowlevel.current_trio_token()

            try:
                self._host = self._create_host()
                self.listen_port = max(0, self.listen_port)

                # Reuse the same filtered listen addresses as _create_host
                listen_addrs = self._host.get_addrs()
                async with self._host.run(listen_addrs):
                    # Update listen_port with actual bound port first thing after start
                    for addr in self._host.get_addrs():
                        addr_str = str(addr)
                        if "/ip4/127.0.0.1/tcp/" in addr_str:
                            self.listen_port = int(addr_str.split("/tcp/")[1].split("/", maxsplit=1)[0])
                            break

                    logger.info("Host started, peer ID: %s, port: %d", self._host.get_id(), self.listen_port)

                    await self._setup_relay()
                    await self._setup_dht()

                    # Now mark as running BEFORE signaling
                    self._running = True

                    # Signal that we're started - all addresses and state are ready now
                    self._start_event.set()

                    if self.bootstrap_enabled:
                        await self._connect_bootstrap()

                    # Run the main loop WHILE host is running
                    await self._run_main_loop()

            finally:
                # Cleanup
                self._running = False
                self._start_event.set()

                self._host = None
                self._dht = None
                self._relay_transport = None
                self._stored_keys.clear()

        try:
            trio.run(_main)
        except Exception as ex:  # noqa: BLE001
            logger.warning("DHT service loop exited: %r", ex)
        finally:
            self._running = False
            self._start_event.set()
            if self._stop_event:
                self._stop_event.set()

    def start(self, timeout: float = 2.0) -> bool:
        """Start the DHT client and connect to the network.

        Args:
            timeout: Maximum time to wait for service to start.

        Returns:
            True if connected to network, False otherwise.

        """
        with self._lock:
            if self._running:
                return True

            self._dht_thread = threading.Thread(target=self._run_trio, daemon=True)
            self._dht_thread.start()

            if self._start_event.wait(timeout=timeout):
                logger.info("DHT client started")
                return True

            logger.warning("DHT client failed to start within %ds", timeout)
            return False

    async def astart(self, timeout: float = 2.0) -> bool:  # noqa: ASYNC109
        """Async wrapper for start() for backwards compatibility.

        Args:
            timeout: Maximum time to wait for service to start.

        Returns:
            True if connected to network, False otherwise.

        """
        return await trio.to_thread.run_sync(self.start, timeout)

    async def _setup_relay(self) -> None:
        """Set up Circuit Relay v2 for NAT traversal."""
        if not self._host:
            return

        try:
            limits = RelayLimits(
                duration=300,
                data=1000000,
                max_circuit_conns=self.max_hop_connections,
                max_reservations=self.max_hop_connections,
            )

            relay_protocol = CircuitV2Protocol(
                self._host,
                limits=limits,
                allow_hop=True,
            )

            relay_config = RelayConfig(limits=limits)

            self._relay_transport = CircuitV2Transport(
                self._host,
                relay_protocol,
                relay_config,
            )

            logger.info(
                "Circuit Relay v2 enabled (max_hop_connections=%d)",
                self.max_hop_connections,
            )

        except Exception as ex:  # noqa: BLE001
            logger.warning("Failed to setup relay: %r", ex)

    async def _connect_bootstrap(self) -> None:
        """Connect to bootstrap nodes."""
        if not self._host:
            return

        connected_count = 0
        for addr in BOOTSTRAP_NODES:
            try:
                peer = info_from_p2p_addr(Multiaddr(addr))
                self._host.get_peerstore().add_addrs(peer.peer_id, peer.addrs, 3600)
                await self._host.connect(peer)
                logger.info("Connected to bootstrap: %s", peer.peer_id)
                connected_count += 1
            except Exception as ex:  # noqa: BLE001, PERF203
                logger.debug("Bootstrap %s failed: %s", addr, ex)

        if connected_count == 0:
            logger.warning("Failed to connect to any bootstrap nodes")
        else:
            logger.info("Successfully connected to %d bootstrap nodes", connected_count)

    def connect_peer(self, peer_addr: str) -> bool:
        """Connect to a specific peer.

        Args:
            peer_addr: The multiaddress of the peer to connect to.

        Returns:
            True if connected successfully.

        """
        if not self._running or not self._host or not self._dht:
            return False

        try:

            async def _connect() -> bool:
                peer = info_from_p2p_addr(Multiaddr(peer_addr))
                self._host.get_peerstore().add_addrs(peer.peer_id, peer.addrs, 3600)  # type: ignore[union-attr]
                await self._host.connect(peer)  # type: ignore[union-attr]
                await self._dht.routing_table.add_peer(peer.peer_id)  # type: ignore[union-attr]
                logger.info("Connected to peer: %s", peer.peer_id)
                return True

            result = self._run_in_trio(_connect, timeout=3.0)
        except Exception as ex:  # noqa: BLE001
            logger.warning("Failed to connect to peer %s: %s", peer_addr, ex)
            return False
        else:
            return result if result is not None else False

    async def aconnect_peer(self, peer_addr: str) -> bool:
        """Async wrapper for connect_peer() for backwards compatibility.

        Args:
            peer_addr: The multiaddress of the peer to connect to.

        Returns:
            True if connected successfully.

        """
        return await trio.to_thread.run_sync(self.connect_peer, peer_addr)

    def _run_in_trio(self, func: Any, *args: Any, timeout: float = 30.0) -> Any:  # noqa: ANN401
        """Run an async function in the Trio event loop from another thread."""
        if not self._running or self._trio_token is None:
            return None

        result = None
        done = threading.Event()

        async def _runner() -> None:
            nonlocal result
            try:
                with trio.fail_after(timeout):
                    result = await func(*args)
            except Exception:  # noqa: BLE001
                result = None
            finally:
                done.set()

        trio.from_thread.run(_runner, trio_token=self._trio_token)
        done.wait(timeout + 0.5)
        return result

    def get(self, key: str, *, timeout: float = 2.0) -> list[dict[str, Any]] | None:
        """Get cached results from the DHT.

        Args:
            key: The cache key (query hash).
            timeout: Timeout in seconds for DHT query.

        Returns:
            List of results or None if not found.

        """
        if not self._running or not self._dht:
            return None

        start_time = time.time()
        success = False

        try:
            self.metrics["total_queries"] += 1

            async def _get() -> list[dict[str, Any]] | None:
                dht_key = f"/ddgs/{key}"
                with trio.move_on_after(timeout) as cancel_scope:
                    result = await self._dht.get_value(dht_key)  # type: ignore[union-attr]
                if cancel_scope.cancelled_caught:
                    logger.debug("DHT get timed out for %s", key)
                    return None
                if result and isinstance(result, bytes):
                    data = json.loads(result, parse_constant=lambda _: None, object_hook=None, object_pairs_hook=None)
                    if isinstance(data, dict) and "results" in data:
                        stored_at = data.get("timestamp", 0)
                        ttl = data.get("ttl", 14400)
                        if time.time() - stored_at > ttl:
                            return None
                        return data.get("results")
                return None

            result = self._run_in_trio(_get, timeout=timeout)
            success = result is not None
            return result  # type: ignore[no-any-return]  # noqa: TRY300
        except Exception as ex:  # noqa: BLE001
            logger.debug("DHT get failed for %s: %r", key, ex)
            success = False
            return None
        finally:
            if success:
                self.metrics["successful_queries"] += 1
                self.metrics["query_latency_sum"] += time.time() - start_time
            else:
                self.metrics["failed_queries"] += 1

    def set(
        self,
        key: str,
        results: list[dict[str, Any]],
        ttl: int = 14400,
        *,
        timeout: float = 2.0,
    ) -> bool:
        """Store results in the DHT.

        Args:
            key: The cache key (query hash).
            results: The search results to cache.
            ttl: Time to live in seconds (default 4 hours).
            timeout: Timeout in seconds for DHT query.

        Returns:
            True if stored successfully.

        """
        if not self._running or not self._dht:
            return False

        try:
            self.metrics["total_puts"] += 1

            async def _set() -> bool:
                timestamp = time.time()
                data = {
                    "results": results,
                    "timestamp": timestamp,
                    "ttl": ttl,
                }
                value = json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
                dht_key = f"/ddgs/{key}"
                with trio.move_on_after(timeout) as cancel_scope:
                    if self._dht is not None:
                        await self._dht.put_value(dht_key, value)
                if cancel_scope.cancelled_caught:
                    logger.debug("DHT set timed out for %s", key)
                    return False

                # Track stored keys for periodic refresh
                with self._lock:
                    self._stored_keys[key] = (results, ttl)
                return True

            result = self._run_in_trio(_set, timeout=timeout)
            if result:
                self.metrics["successful_puts"] += 1
                return True
            self.metrics["failed_puts"] += 1
            return False  # noqa: TRY300
        except Exception as ex:  # noqa: BLE001
            logger.debug("DHT set failed for %s: %r", key, ex)
            self.metrics["failed_puts"] += 1
            return False

    async def aget(self, key: str, *, timeout: float = 2.0) -> list[dict[str, Any]] | None:  # noqa: ASYNC109
        """Async wrapper for get() for backwards compatibility.

        Args:
            key: The cache key (query hash).
            timeout: Timeout in seconds for DHT query.

        Returns:
            List of results or None if not found.

        """
        return await trio.to_thread.run_sync(lambda: self.get(key, timeout=timeout))

    async def aset(
        self,
        key: str,
        results: list[dict[str, Any]],
        ttl: int = 14400,
        *,
        timeout: float = 2.0,  # noqa: ASYNC109
    ) -> bool:
        """Async wrapper for set() for backwards compatibility.

        Args:
            key: The cache key (query hash).
            results: The search results to cache.
            ttl: Time to live in seconds (default 4 hours).
            timeout: Timeout in seconds for DHT query.

        Returns:
            True if stored successfully.

        """
        return await trio.to_thread.run_sync(lambda: self.set(key, results, ttl, timeout=timeout))

    def find_peers(self) -> list[str]:
        """Find other peers in the network.

        Returns:
            List of peer addresses.

        """
        if not self._running or not self._host:
            return []

        try:

            async def _find_peers() -> list[str]:
                peers = self._host.get_peerstore().peer_ids()  # type: ignore[union-attr]
                return [str(p) for p in peers]

            result = self._run_in_trio(_find_peers, timeout=5.0)
        except Exception as ex:  # noqa: BLE001
            logger.debug("DHT find_peers failed: %r", ex)
            return []
        else:
            return result if result is not None else []

    def get_neighbors(self) -> list[dict[str, Any]]:
        """Get all peers from routing table with complete metadata.

        Returns:
            List of peer dictionaries with metadata.

        """
        if not self._dht or not hasattr(self._dht, "routing_table"):
            return []

        peers: list[dict[str, Any]] = []
        peers.extend(
            {
                "peer_id": str(peer),
                "xor_distance": bucket_idx,
                "last_seen": peer.last_seen if hasattr(peer, "last_seen") else None,
                "latency_ms": peer.latency * 1000 if hasattr(peer, "latency") else None,
                "agent_version": peer.agent_version if hasattr(peer, "agent_version") else None,
            }
            for bucket_idx, bucket in enumerate(self._dht.routing_table.buckets)
            for peer in bucket.peers
        )
        return peers

    async def afind_peers(self) -> list[str]:
        """Async wrapper for find_peers() for backwards compatibility.

        Returns:
            List of peer addresses.

        """
        return await trio.to_thread.run_sync(self.find_peers)

    @property
    def is_running(self) -> bool:
        """Check if the client is running."""
        return self._running

    @property
    def port(self) -> int:
        """Get the listen port."""
        return self.listen_port

    @property
    def peer_id(self) -> str | None:
        """Get the peer ID of this node."""
        return str(self._host.get_id()) if self._host else None

    @property
    def listen_addrs(self) -> list[str]:
        """Get the listen addresses of this node."""
        if self._host:
            try:
                addrs = [str(addr) for addr in self._host.get_addrs()]
                if addrs:
                    return addrs
            except Exception as ex:  # noqa: BLE001
                logger.debug("Failed to get host addresses: %r", ex)

        # Fall back to manual address construction using known port
        return [f"/ip4/127.0.0.1/tcp/{self.listen_port}"]

    @property
    def peer_addrs(self) -> list[str]:
        """Get full peer addresses with /p2p/ suffix for connecting."""
        if not self.peer_id:
            return []
        return [f"{addr_str}/p2p/{self.peer_id}" for addr_str in self.listen_addrs]

    def stop(self, timeout: float = 2.0) -> None:
        """Stop the DHT client.

        Args:
            timeout: Maximum time to wait for service to stop.

        """
        with self._lock:
            if not self._running:
                return

            self._running = False

            # Signal stop to trio thread - avoid deadlock by using direct set()
            if self._stop_event is not None:
                self._stop_event.set()

            # Wait for thread to exit
            if self._dht_thread:
                self._dht_thread.join(timeout=timeout)

            self._dht_thread = None
            self._trio_token = None
            self._stop_event = None

    async def astop(self, timeout: float = 2.0) -> None:  # noqa: ASYNC109
        """Async wrapper for stop() for backwards compatibility.

        Args:
            timeout: Maximum time to wait for service to stop.

        """
        await trio.to_thread.run_sync(lambda: self.stop(timeout=timeout))
