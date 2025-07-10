from __future__ import annotations

from typing import Any

from .base import BaseSearchEngine
from .engines import images_engines_dict, news_engines_dict, text_engines_dict, videos_engines_dict


class DDGS:
    def __init__(self, proxy: str | None = None, timeout: int | None = None, verify: bool = True):
        self._engines: dict[str, list[BaseSearchEngine]] = {
            "text": [E(proxy, timeout, verify) for E in text_engines_dict.values()],
            "images": [E(proxy, timeout, verify) for E in images_engines_dict.values()],
            "news": [E(proxy, timeout, verify) for E in news_engines_dict.values()],
            "videos": [E(proxy, timeout, verify) for E in videos_engines_dict.values()],
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
        backend: str = "auto",
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Generic search over a given engine category.
        category must be one of 'text', 'images', 'news', 'videos'.
        """
        results: list[dict[str, Any]] = []

        if backend == "auto":
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
        backend: str = "auto",
    ) -> list[dict[str, Any]]:
        return self._search(
            "text",
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=page,
            backend=backend,
        )

    def images(
        self,
        query: str,
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
        backend: str = "auto",
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        return self._search(
            "images",
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=page,
            backend=backend,
            **kwargs,
        )

    def news(
        self,
        query: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
        backend: str = "auto",
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        return self._search(
            "news",
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=page,
            backend=backend,
            **kwargs,
        )

    def videos(
        self,
        query: str,
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
        backend: str = "auto",
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        return self._search(
            "videos",
            query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            page=page,
            backend=backend,
            **kwargs,
        )
