"""Network types for distributed cache."""

import hashlib
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class NodeInfo:
    """Information about a network node."""

    peer_id: str
    public_key: bytes
    address: str
    seen_at: float

    @property
    def is_alive(self) -> bool:
        """Check if the node has been seen in the last 5 minutes."""
        return time.time() - self.seen_at < 300


@dataclass
class CachedResult:
    """Cached search result stored in the network."""

    query_hash: str
    query: str
    results: list[dict[str, Any]]
    timestamp: float
    ttl: int = 14400

    def is_fresh(self) -> bool:
        """Check if the cached result is still valid based on TTL."""
        return time.time() - self.timestamp < self.ttl

    @property
    def age(self) -> float:
        """Get the age of the cached result in seconds."""
        return time.time() - self.timestamp


def compute_query_hash(query: str, category: str = "text") -> str:
    """Compute a normalized hash for a query.

    Normalization:
    - Strip whitespace
    - Lowercase
    - Sort words alphabetically for deterministic key

    This ensures "Python tutorial" and "tutorial Python" share cache.

    Args:
        query: The search query.
        category: The search category (text, images, etc.).

    Returns:
        A SHA256 hash string.

    """
    words = query.strip().lower().split()
    words.sort()
    normalized = f"{category}:{' '.join(words)}"
    return hashlib.sha256(normalized.encode()).hexdigest()


def normalize_query(query: str) -> str:
    """Normalize query for display/storage.

    Args:
        query: The search query.

    Returns:
        Normalized query string.

    """
    words = query.strip().lower().split()
    words.sort()
    return " ".join(words)
