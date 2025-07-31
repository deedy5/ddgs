from __future__ import annotations

from abc import ABC
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar

from .utils import _normalize_date, _normalize_text, _normalize_url

T = TypeVar("T")


class BaseResult:
    """
    Base class for all results. Contains normalization functions.
    """

    _normalizers: dict[str, Callable[[Any], Any]] = {
        "title": _normalize_text,
        "body": _normalize_text,
        "href": _normalize_url,
        "url": _normalize_url,
        "thumbnail": _normalize_url,
        "image": _normalize_url,
        "date": _normalize_date,
    }

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Override setattr to apply normalization functions to certain attributes.
        """
        if value and (normalizer := self._normalizers.get(name)):
            value = normalizer(value)
        object.__setattr__(self, name, value)


@dataclass
class TextResult(BaseResult):
    title: str = ""
    href: str = ""
    body: str = ""


@dataclass
class ImagesResult(BaseResult):
    title: str = ""
    image: str = ""
    thumbnail: str = ""
    url: str = ""
    height: str = ""
    width: str = ""
    source: str = ""


@dataclass
class NewsResult(BaseResult):
    date: str = ""
    title: str = ""
    body: str = ""
    url: str = ""
    image: str = ""
    source: str = ""


@dataclass
class VideosResult(BaseResult):
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
    title: str = ""
    author: str = ""
    publisher: str = ""
    info: str = ""
    url: str = ""
    thumbnail: str = ""


class ResultsAggregator(Generic[T], ABC):
    """
    Aggregates incoming results. Items are deduplicated by `cache_field`.
    Append just increments a counter; `extract_results` returns items
    sorted by descending frequency.
    """

    def __init__(self, cache_fields: set[str]) -> None:
        if not cache_fields:
            raise ValueError("At least one cache_field must be provided")
        self.cache_fields = set(cache_fields)
        self._counter: Counter[str] = Counter()
        self._cache: dict[str, T] = {}

    def _get_key(self, item: T) -> str:
        for key in item.__dict__:
            if key in self.cache_fields:
                return str(item.__dict__[key])
        raise AttributeError(f"Item {item!r} has none of the cache fields {self.cache_fields}")

    def __len__(self) -> int:
        return len(self._cache)

    def append(self, item: T) -> None:
        """
        Register an occurrence of `item`. First time we see its key,
        we store the item; every time we bump the counter.
        """
        key = self._get_key(item)
        if key not in self._cache:
            self._cache[key] = item
        else:
            # prefer longer body
            if len(item.__dict__.get("body", "")) > len(self._cache[key].__dict__.get("body", "")):
                self._cache[key] = item
        self._counter[key] += 1

    def extend(self, items: list[T]) -> None:
        for item in items:
            self.append(item)

    def extract_dicts(self) -> list[dict[str, Any]]:
        """
        Return a list of items, sorted by descending frequency. Each item is returned as a dict.
        """
        return [self._cache[key].__dict__ for key, _ in self._counter.most_common()]
