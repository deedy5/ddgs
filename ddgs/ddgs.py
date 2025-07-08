from __future__ import annotations

from typing import Any

from .engines import search_engines_dict


class DDGS:
    def __init__(self, proxy: str | None = None, timeout: int | None = None):
        self.engines = [e(proxy, timeout) for e in search_engines_dict.values()]

    def text(self, query: str) -> list[dict[str, Any]]:
        """Search multiple engines"""
        results: list[dict[str, Any]] = []
        for engine in self.engines:
            engine_results = engine.search(query)
            if engine_results:
                results.extend(engine_results)
        return results
