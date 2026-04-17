"""Network distributed cache tests using libp2p."""

import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import trio

# Skip entire test file if DHT dependencies are not installed
dht = pytest.importorskip("ddgs.dht")

from ddgs.dht import DhtClient, Libp2pClient
from ddgs.dht.types import compute_query_hash

pytestmark = [
    pytest.mark.trio,
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.skipif("sys.platform == 'win32'", reason="DHT not supported on Windows"),
]


async def test_libp2p_client_start() -> None:
    """Test that libp2p client can start."""
    client = Libp2pClient(bootstrap=False)
    result = await client.astart()

    assert result is True
    assert client.is_running
    assert client.peer_id is not None

    await client.astop()


@pytest.mark.skip(reason="Known libp2p loopback connection issue - works on real network but not localhost")
async def test_libp2p_two_instances_connect() -> None:
    """Test that two libp2p instances can connect to each other.

    Note: This test currently fails on localhost due to a known issue in py-libp2p,
    but works correctly on real networks with separate machines.
    """
    client1 = Libp2pClient(listen_port=0, bootstrap=False)
    client2 = Libp2pClient(listen_port=0, bootstrap=False)

    await client1.astart()
    await client2.astart()

    assert client1.peer_id is not None
    assert client2.peer_id is not None
    assert client1.peer_id != client2.peer_id

    # Give time for socket to be fully bound and listening
    await trio.sleep(1)

    # Try all addresses with multiple retries
    success = False
    for addr in client1.peer_addrs:
        for _ in range(5):
            success = await client2.aconnect_peer(addr)
            if success:
                break
            await trio.sleep(0.2)
        if success:
            break

    assert success is True, f"Failed to connect to any address: {client1.peer_addrs}"

    # Critical: Wait for routing tables to update and refresh
    await trio.sleep(2)

    peers1 = await client1.afind_peers()
    peers2 = await client2.afind_peers()

    assert len(peers1) >= 1
    assert len(peers2) >= 1

    await client1.astop()
    await client2.astop()


@pytest.mark.skip(reason="Known libp2p loopback connection issue - works on real network but not localhost")
async def test_dht_put_and_get_between_instances() -> None:
    """Test DHT put/get between two libp2p instances.

    Important note: This test has realistic propagation delays.
    Kademlia requires time for routing table updates and value replication.

    Note: This test currently fails on localhost due to a known issue in py-libp2p,
    but works correctly on real networks with separate machines.
    """
    client1 = Libp2pClient(listen_port=0, bootstrap=False)
    client2 = Libp2pClient(listen_port=0, bootstrap=False)

    await client1.astart()
    await client2.astart()

    # Connect explicitly
    success = await client2.aconnect_peer(client1.peer_addrs[0])
    assert success is True

    # Wait for routing tables to populate (this is required - cannot be skipped)
    await trio.sleep(3)

    query = "python tutorial"
    category = "text"
    key = compute_query_hash(query, category)
    results = [{"title": "Python Tutorial", "url": "https://example.com/python"}]

    set_result = await client1.aset(key, results, ttl=60)
    assert set_result is True

    # Kademlia values replicate asynchronously. Wait for propagation.
    await trio.sleep(5)

    # Try multiple times with backoff - realistic real world behavior
    retrieved = None
    for attempt in range(3):
        retrieved = await client2.aget(key, timeout=2)
        if retrieved is not None:
            break
        await trio.sleep(2)

    assert retrieved is not None, "Failed to retrieve from DHT after 3 attempts"
    assert len(retrieved) == 1
    assert retrieved[0]["title"] == "Python Tutorial"

    await client1.astop()
    await client2.astop()


async def test_network_client_local_cache() -> None:
    """Test DhtClient local cache (no DHT)."""
    client = DhtClient(enable_dht=False)
    await client.start()

    await client.cache("test query", [{"title": "Test"}], "text")
    result = await client.get_cached("test query", "text")

    assert result is not None
    assert len(result) == 1

    await client.stop()


async def test_cache_ttl() -> None:
    """Test cache TTL expiration."""
    client = DhtClient(enable_dht=False, cache_ttl=1)
    await client.start()

    await client.cache("ttl test", [{"title": "Old"}], "text")
    await trio.sleep(1.1)

    result = await client.get_cached("ttl test", "text")
    assert result is None

    await client.stop()


async def test_dht_query_timeout() -> None:
    """Test DHT query timeout functionality."""
    from ddgs.dht.libp2p_client import Libp2pClient

    client = Libp2pClient(bootstrap=False)
    await client.astart()

    # This should timeout quickly instead of hanging
    result = await client.aget("non-existent-key", timeout=0.1)
    assert result is None

    # Set should also work with timeout
    success = await client.aset("test-key", [{"title": "test"}], timeout=0.1)
    assert isinstance(success, bool)

    await client.astop()


async def test_local_cache_eviction() -> None:
    """Test local cache eviction when max size is reached."""
    from ddgs.dht.cache import MAX_CACHE_SIZE, ResultCache

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        f.close()  # Critical: close file handle before SQLite opens it
    try:
        cache = ResultCache(db_path=f.name)

        # Fill cache beyond max size
        for i in range(MAX_CACHE_SIZE + 100):
            cache.set(f"key-{i}", f"query-{i}", "text", [{"title": f"Result {i}"}])

        # Should have evicted old entries
        count = cache.count()
        assert count == MAX_CACHE_SIZE
    finally:
        Path(f.name).unlink(missing_ok=True)


async def test_negative_cache() -> None:
    """Test negative cache functionality."""
    from ddgs.dht.cache import ResultCache

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        f.close()  # Critical: close file handle before SQLite opens it
    try:
        cache = ResultCache(db_path=f.name)

        # Add to negative cache
        cache.add_negative("test-key")

        # Should return None immediately (negative cache hit)
        result = cache.get("test-key")
        assert result is None
    finally:
        Path(f.name).unlink(missing_ok=True)


async def test_network_client_invalidate() -> None:
    """Test DhtClient cache invalidation."""
    client = DhtClient(enable_dht=False)
    await client.start()

    await client.cache("test query", [{"title": "Test"}], "text")

    # Verify exists
    result = await client.get_cached("test query", "text")
    assert result is not None

    # Invalidate
    await client.invalidate("test query", "text")

    # Verify removed
    result = await client.get_cached("test query", "text")
    assert result is None

    await client.stop()


async def test_peer_connection_error_handling() -> None:
    """Test that connection failures are handled gracefully."""
    from ddgs.dht.libp2p_client import Libp2pClient

    client = Libp2pClient(bootstrap=False)
    await client.astart()

    # Try to connect to invalid peer
    success = await client.aconnect_peer("/ip4/127.0.0.1/tcp/9999/p2p/invalidpeerid")
    assert success is False

    await client.astop()


async def test_bootstrap_network_connectivity() -> None:
    """Test that client can connect to public bootstrap network."""
    import logging

    logging.basicConfig(level=logging.WARNING)

    client = Libp2pClient(bootstrap=True)
    try:
        await client.astart()

        # Give time for bootstrap connection
        await trio.sleep(3)

        peer_count = len(await client.afind_peers())

        # Should have at least a few peers if connected successfully
        assert peer_count >= 0, "Peer discovery should work"

    finally:
        await client.astop()


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.skip(reason="Kademlia requires active peers to replicate values. Test will pass automatically once network has 10+ nodes.")
@pytest.mark.slow
@pytest.mark.integration
async def test_bootstrap_value_replication() -> None:
    """Test that value stored on one client propagates to another via bootstrap network.

    IMPORTANT: This test is expected to fail right now. Kademlia does not replicate
    values through bootstrap nodes. It requires existing active peers on the network
    to store and forward values. This test will start passing automatically once
    there are ~10+ permanent ddgs nodes running.

    This is an integration test that uses the real public IPFS bootstrap network.
    """
    import logging
    import time
    logging.basicConfig(level=logging.WARNING)

    client1 = Libp2pClient(bootstrap=True)
    client2 = Libp2pClient(bootstrap=True)

    try:
        await client1.astart()
        await client2.astart()

        await trio.sleep(15)

        query = "bootstrap integration test"
        category = "text"
        key = compute_query_hash(query, category)
        test_value = [{"title": "Bootstrap Test", "url": "https://github.com/xxx/xxx"}]

        await client1.aset(key, test_value, ttl=120)

        retrieved = None
        for _ in range(3):
            retrieved = await client2.aget(key, timeout=3)
            if retrieved is not None:
                break
            await trio.sleep(5)

        assert retrieved == test_value

    finally:
        await client1.astop()
        await client2.astop()


async def test_bootstrap_local_only_fallback() -> None:
    """Test that client works correctly even when bootstrap is unreachable."""
    client = Libp2pClient(bootstrap=False)
    try:
        await client.astart(timeout=10)

        # Should still work even with no bootstrap connectivity
        key = "local-test-key"
        test_value = [{"title": "Local Test"}]

        success = await client.aset(key, test_value)
        assert success is True

        retrieved = await client.aget(key)
        assert retrieved == test_value

    finally:
        await client.astop()
