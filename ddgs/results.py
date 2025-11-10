"""Result classes."""

from abc import ABC
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar, Generic, TypeVar

from .utils import _normalize_date, _normalize_text, _normalize_url

T = TypeVar("T")


class BaseResult:
    """Base class for all results. Contains normalization functions."""

    _normalizers: ClassVar[Mapping[str, Callable[[Any], str]]] = {
        "title": _normalize_text,
        "body": _normalize_text,
        "href": _normalize_url,
        "url": _normalize_url,
        "thumbnail": _normalize_url,
        "image": _normalize_url,
        "date": _normalize_date,
        "author": _normalize_text,
        "publisher": _normalize_text,
        "info": _normalize_text,
    }

    def __setattr__(self, name: str, value: str) -> None:
        """Override setattr to apply normalization functions to certain attributes."""
        if value and (normalizer := self._normalizers.get(name)):
            value = normalizer(value)
        object.__setattr__(self, name, value)


@dataclass
class TextResult(BaseResult):
    """Text search result."""

    title: str = ""
    href: str = ""
    body: str = ""


@dataclass
class ImagesResult(BaseResult):
    """Image search result."""

    title: str = ""
    image: str = ""
    thumbnail: str = ""
    url: str = ""
    height: str = ""
    width: str = ""
    source: str = ""


@dataclass
class NewsResult(BaseResult):
    """News search result."""

    date: str = ""
    title: str = ""
    body: str = ""
    url: str = ""
    image: str = ""
    source: str = ""


@dataclass
class VideosResult(BaseResult):
    """Video search result."""

    title: str = ""
    content: str = ""
    description: str = ""
    duration: str = ""
    embed_html: str = ""
    embed_url: str = ""
    image_token: str = ""
    images: dict[str, str] = field(default_factory=dict)
    provider: str = ""
    published: str = ""
    publisher: str = ""
    statistics: dict[str, str] = field(default_factory=dict)
    uploader: str = ""


@dataclass
class BooksResult(BaseResult):
    """Book search result."""

    title: str = ""
    author: str = ""
    publisher: str = ""
    info: str = ""
    url: str = ""
    thumbnail: str = ""


class ResultsAggregator(ABC, Generic[T]):
    """Aggregates incoming results.

    Items are deduplicated by `cache_field`. Append just increments a counter;
    `extract_results` returns items sorted by descending frequency.
    """

    def __init__(self, cache_fields: set[str]) -> None:
        if not cache_fields:
            msg = "At least one cache_field must be provided"
            raise ValueError(msg)
        self.cache_fields = set(cache_fields)
        self._counter: Counter[str] = Counter()
        self._cache: dict[str, T] = {}

    def _get_key(self, item: T) -> str:
        for key in item.__dict__:
            if key in self.cache_fields:
                return str(item.__dict__[key])
        msg = f"Item {item!r} has none of the cache fields {self.cache_fields}"
        raise AttributeError(msg)

    def __len__(self) -> int:
        """Return the number of items in the cache."""
        return len(self._cache)

    def append(self, item: T) -> None:
        """Add an item to the cache.

        Register an occurrence of `item`. First time we see its key,
        we store the item; every time we bump the counter.
        """
        key = self._get_key(item)
        if key not in self._cache or len(item.__dict__.get("body", "")) > len(
            self._cache[key].__dict__.get("body", ""),
        ):
            self._cache[key] = item
        self._counter[key] += 1

    def extend(self, items: list[T]) -> None:
        """Add a list of items to the cache."""
        for item in items:
            self.append(item)

    def extract_dicts(self) -> list[dict[str, Any]]:
        """Return a list of items, sorted by descending frequency. Each item is returned as a dict."""
        return [self._cache[key].__dict__ for key, _ in self._counter.most_common()]
