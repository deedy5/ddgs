from __future__ import annotations

from typing import Any

from .engines import images_engines_dict, news_engines_dict, text_engines_dict, videos_engines_dict


class DDGS:
    def __init__(self, proxy: str | None = None, timeout: int | None = None):
        self.text_engines = [e(proxy, timeout) for e in text_engines_dict.values()]
        self.images_engines = [e(proxy, timeout) for e in images_engines_dict.values()]
        self.news_engines = [e(proxy, timeout) for e in news_engines_dict.values()]
        self.videos_engines = [e(proxy, timeout) for e in videos_engines_dict.values()]

    def text(
        self,
        query: str,
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """Search multiple text engines"""
        results: list[dict[str, Any]] = []
        for engine in self.text_engines:
            engine_results = engine.search(query, region=region, safesearch=safesearch, timelimit=timelimit, page=page)
            if engine_results:
                results.extend(engine_results)
        return results

    def images(
        self,
        query: str,
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Search multiple image engines"""
        results: list[dict[str, Any]] = []
        for engine in self.images_engines:
            engine_results = engine.search(
                query, region=region, safesearch=safesearch, timelimit=timelimit, page=page, **kwargs
            )
            if engine_results:
                results.extend(engine_results)
        return results

    def news(
        self,
        query: str,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Search multiple news engines"""
        results: list[dict[str, Any]] = []
        for engine in self.news_engines:
            engine_results = engine.search(
                query, region=region, safesearch=safesearch, timelimit=timelimit, page=page, **kwargs
            )
            if engine_results:
                results.extend(engine_results)
        return results

    def videos(
        self,
        query: str,
        region: str | None = None,
        safesearch: str = "moderate",
        timelimit: str | None = None,
        page: int = 1,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Search multiple video engines"""
        results: list[dict[str, Any]] = []
        for engine in self.videos_engines:
            engine_results = engine.search(
                query, region=region, safesearch=safesearch, timelimit=timelimit, page=page, **kwargs
            )
            if engine_results:
                results.extend(engine_results)
        return results
