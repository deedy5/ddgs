from __future__ import annotations

from abc import ABC
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from .utils import _normalize_text, _normalize_url

T = TypeVar("T")


class BaseResult:
    def __post_init__(self) -> None:
        """
        Post-processing initialization for a result object. This function iterates over
        the attributes of the object, normalizes certain fields, and formats date fields.
        It skips empty values for specific keys, applies text normalization for title and
        body fields, URL normalization for href, url, thumbnail, and image fields, and
        converts integer timestamps in the date field to ISO format.
        """

        for key, value in self.__dict__.items():
            # skip empty
            if key in {"title", "body", "href", "url", "image"} and not (
                value := value.strip() if isinstance(value, str) else value
            ):
                continue
            if key in {"title", "body"}:
                self.__dict__[key] = _normalize_text(value)
            elif key in {"href", "url", "thumbnail", "image"}:
                self.__dict__[key] = _normalize_url(value)
            elif key == "date" and isinstance(value, int):
                self.__dict__[key] = datetime.fromtimestamp(value, timezone.utc).isoformat()  # int to readable date
            else:
                self.__dict__[key] = value


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
