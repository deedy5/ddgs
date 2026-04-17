"""Local cache with TTL expiration using SQLite."""

import hashlib
import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_TTL = 14400
MAX_CACHE_SIZE = 10000
NEGATIVE_CACHE_SIZE = 50000
NEGATIVE_CACHE_TTL = 1800  # 30 minutes


class BloomFilter:
    """Simple bloom filter for negative cache lookups."""

    def __init__(self, size: int = NEGATIVE_CACHE_SIZE, hash_count: int = 3) -> None:
        self.size = size
        self.hash_count = hash_count
        self.bit_array = bytearray(size // 8 + 1)
        self._lock = threading.RLock()

    def _hashes(self, key: str) -> list[int]:
        """Generate hash positions for a key using SHA-256 for consistency."""
        result = []
        for i in range(self.hash_count):
            # Use key + seed for each hash, then truncate to 64-bit int
            data = f"{key}:{i}".encode()
            digest = hashlib.sha256(data).digest()
            # Convert first 8 bytes to unsigned integer
            h = int.from_bytes(digest[:8], byteorder="big", signed=False)
            result.append(h % self.size)
        return result

    def add(self, key: str) -> None:
        """Add a key to the filter."""
        with self._lock:
            for pos in self._hashes(key):
                self.bit_array[pos // 8] |= 1 << (pos % 8)

    def __contains__(self, key: str) -> bool:
        """Check if a key may be present."""
        with self._lock:
            return all(self.bit_array[pos // 8] & (1 << (pos % 8)) for pos in self._hashes(key))


class ResultCache:
    """Thread-safe local SQLite cache with TTL support."""

    def __init__(self, db_path: str | None = None) -> None:
        if db_path:
            self._db_path = Path(db_path)
        else:
            ddgs_dir = Path("~/.ddgs").expanduser()
            ddgs_dir.mkdir(parents=True, exist_ok=True)
            self._db_path = ddgs_dir / "cache.db"

        self._lock = threading.RLock()
        self._negative_cache = BloomFilter()
        self._negative_cache_times: dict[str, float] = {}

        # Initialize database schema
        with sqlite3.connect(self._db_path) as conn:
            self._init_db(conn)

    def _init_db(self, conn: sqlite3.Connection) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cached_results (
                query_hash TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                category TEXT NOT NULL,
                results TEXT NOT NULL,
                timestamp REAL NOT NULL,
                ttl INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON cached_results(timestamp)
        """)
        conn.commit()

    def _parse_results(self, results_json: str) -> list[dict[str, Any]] | None:
        """Parse JSON results safely."""
        try:
            return json.loads(results_json)  # type: ignore[no-any-return]
        except Exception:  # noqa: BLE001
            return None

    def get(
        self,
        query_hash: str,
    ) -> list[dict[str, Any]] | None:
        """Get cached results if not expired."""
        with self._lock, sqlite3.connect(self._db_path) as conn:
            result = conn.execute(
                "SELECT results, timestamp, ttl FROM cached_results WHERE query_hash = ?",
                (query_hash,),
            ).fetchone()

            if not result:
                return None

            results_json, timestamp, ttl = result
            if time.time() > timestamp + ttl:
                # Expired, delete it
                conn.execute(
                    "DELETE FROM cached_results WHERE query_hash = ?",
                    (query_hash,),
                )
                conn.commit()
                return None

            return self._parse_results(results_json)

    def set(
        self,
        query_hash: str,
        query: str,
        category: str,
        results: list[dict[str, Any]],
        ttl: int = DEFAULT_TTL,
    ) -> None:
        """Store results with TTL and enforce max size."""
        with self._lock, sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cached_results "
                "(query_hash, query, category, results, timestamp, ttl) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    query_hash,
                    query,
                    category,
                    json.dumps(results, ensure_ascii=False, allow_nan=False),
                    time.time(),
                    ttl,
                ),
            )
            conn.commit()

            # Only run eviction when we exceed max size
            count = conn.execute("SELECT COUNT(*) FROM cached_results").fetchone()[0]
            if count > MAX_CACHE_SIZE:
                excess = count - MAX_CACHE_SIZE + 1  # Remove extra to get under limit
                conn.execute(
                    "DELETE FROM cached_results WHERE query_hash IN ("
                    "SELECT query_hash FROM cached_results "
                    "ORDER BY timestamp ASC LIMIT ?)",
                    (excess,),
                )
                conn.commit()
                logger.debug("Evicted %d old entries", excess)

    def delete(self, query_hash: str) -> None:
        """Delete a cached result."""
        with self._lock, sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "DELETE FROM cached_results WHERE query_hash = ?",
                (query_hash,),
            )
            conn.commit()

    def cleanup_expired(self) -> int:
        """Remove all expired entries."""
        with self._lock, sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM cached_results WHERE timestamp + ttl < ?",
                (time.time(),),
            )
            conn.commit()
            return cursor.rowcount

    def count(self) -> int:
        """Get total number of cached entries."""
        with self._lock, sqlite3.connect(self._db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM cached_results").fetchone()[0]  # type: ignore[no-any-return]

    def __len__(self) -> int:
        """Get total number of cached entries."""
        return self.count()

    def size_bytes(self) -> int:
        """Get database size in bytes."""
        return self._db_path.stat().st_size if self._db_path.exists() else 0

    def add_negative(self, query_hash: str) -> None:
        """Add an entry to the negative cache (no results found)."""
        with self._lock:
            # Cleanup expired entries first when we reach 80% capacity
            if len(self._negative_cache_times) >= NEGATIVE_CACHE_SIZE * 0.8:
                now = time.time()
                expired = [k for k, v in self._negative_cache_times.items() if now - v >= NEGATIVE_CACHE_TTL]
                for k in expired:
                    del self._negative_cache_times[k]

            self._negative_cache.add(query_hash)
            self._negative_cache_times[query_hash] = time.time()
            logger.debug("Added to negative cache: %s", query_hash)
