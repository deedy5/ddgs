from __future__ import annotations

from typing import Any

from .base import BaseSearchEngine
from .engines import images_engines_dict, news_engines_dict, text_engines_dict, videos_engines_dict


class DDGS:
    def __init__(self, proxy: str | None = None, timeout: int | None = None):
        self._engines: dict[str, list[BaseSearchEngine]] = {
            "text": [E(proxy, timeout) for E in text_engines_dict.values()],
            "images": [E(proxy, timeout) for E in images_engines_dict.values()],
            "news": [E(proxy, timeout) for E in news_engines_dict.values()],
            "videos": [E(proxy, timeout) for E in videos_engines_dict.values()],
        }

    def _search(
        self,
        category: str,
        query: str,
        *,
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Generic search over a given engine category.
        category must be one of 'text', 'images', 'news', 'videos'.
        """
        results: list[dict[str, Any]] = []

        engines: list[BaseSearchEngine] = self._engines.get(category, [])
        for engine in engines:
            engine_results = engine.search(
                query, region=region, safesearch=safesearch, timelimit=timelimit, page=page, **kwargs
            )
            if engine_results:
                results.extend(engine_results)

        return results

    def text(
        self,
        query: str,
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        return self._search(
            "text",
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=page,
        )

    def images(
        self,
        query: str,
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        return self._search(
            "images",
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=page,
            **kwargs,
        )

    def news(
        self,
        query: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        return self._search(
            "news",
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=page,
            **kwargs,
        )

    def videos(
        self,
        query: str,
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        return self._search(
            "videos",
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=page,
            **kwargs,
        )
