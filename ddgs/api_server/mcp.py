"""MCP server for DDGS."""

import asyncio
import logging
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from ddgs import DDGS
from ddgs.utils import _expand_proxy_tb_alias

logger = logging.getLogger(__name__)

# Create MCP server with secure defaults
mcp = FastMCP("ddgs-search")


@mcp.tool()
async def search_text(
    query: str,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: str | None = None,
    max_results: int = 10,
    page: int = 1,
    backend: str = "auto",
) -> list[dict[str, Any]]:
    """Perform a text search using DDGS.

    Args:
        query: Search query string
        region: Region for search (e.g., us-en, uk-en, ru-ru)
        safesearch: Safe search setting (on, moderate, off)
        timelimit: Time limit (d, w, m, y) or custom date range
        max_results: Maximum number of results to return
        page: Page number of results
        backend: Search backend (auto, or specific engine)

    Returns:
        List of search results with title, href, and body

    """
    results = await asyncio.to_thread(
        lambda: DDGS(proxy=_expand_proxy_tb_alias(os.environ.get("DDGS_PROXY"))).text(
            query=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            page=page,
            backend=backend,
        )
    )
    return list(results)


@mcp.tool()
async def search_images(
    query: str,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: str | None = None,
    max_results: int = 10,
    page: int = 1,
    backend: str = "auto",
    size: str | None = None,
    color: str | None = None,
    type_image: str | None = None,
    layout: str | None = None,
    license_image: str | None = None,
) -> list[dict[str, Any]]:
    """Perform an image search using DDGS.

    Args:
        query: Image search query string
        region: Region for search (e.g., us-en, uk-en, ru-ru)
        safesearch: Safe search setting (on, moderate, off)
        timelimit: Time limit (d, w, m, y) or custom date range
        max_results: Maximum number of results to return
        page: Page number of results
        backend: Search backend (auto, or specific engine)
        size: Image size (Small, Medium, Large, Wallpaper)
        color: Image color filter
        type_image: Image type (photo, clipart, gif, transparent, line)
        layout: Image layout (Square, Tall, Wide)
        license_image: Image license filter

    Returns:
        List of image search results with title, image URL, and source

    """
    results = await asyncio.to_thread(
        lambda: DDGS(proxy=_expand_proxy_tb_alias(os.environ.get("DDGS_PROXY"))).images(
            query=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            page=page,
            backend=backend,
            size=size,
            color=color,
            type_image=type_image,
            layout=layout,
            license_image=license_image,
        )
    )
    return list(results)


@mcp.tool()
async def search_news(
    query: str,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: str | None = None,
    max_results: int = 10,
    page: int = 1,
    backend: str = "auto",
) -> list[dict[str, Any]]:
    """Perform a news search using DDGS.

    Args:
        query: News search query string
        region: Region for search (e.g., us-en, uk-en, ru-ru)
        safesearch: Safe search setting (on, moderate, off)
        timelimit: Time limit (d, w, m, y) or custom date range
        max_results: Maximum number of results to return
        page: Page number of results
        backend: Search backend (auto, or specific engine)

    Returns:
        List of news results with title, URL, source, and date

    """
    results = await asyncio.to_thread(
        lambda: DDGS(proxy=_expand_proxy_tb_alias(os.environ.get("DDGS_PROXY"))).news(
            query=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            page=page,
            backend=backend,
        )
    )
    return list(results)


@mcp.tool()
async def search_videos(
    query: str,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: str | None = None,
    max_results: int = 10,
    page: int = 1,
    backend: str = "auto",
    resolution: str | None = None,
    duration: str | None = None,
    license_videos: str | None = None,
) -> list[dict[str, Any]]:
    """Perform a video search using DDGS.

    Args:
        query: Video search query string
        region: Region for search (e.g., us-en, uk-en, ru-ru)
        safesearch: Safe search setting (on, moderate, off)
        timelimit: Time limit (d, w, m) or custom date range
        max_results: Maximum number of results to return
        page: Page number of results
        backend: Search backend (auto, or specific engine)
        resolution: Video resolution (high, standard)
        duration: Video duration (short, medium, long)
        license_videos: Video license (creativeCommon, youtube)

    Returns:
        List of video search results with title, URL, and metadata

    """
    results = await asyncio.to_thread(
        lambda: DDGS(proxy=_expand_proxy_tb_alias(os.environ.get("DDGS_PROXY"))).videos(
            query=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            page=page,
            backend=backend,
            resolution=resolution,
            duration=duration,
            license_videos=license_videos,
        )
    )
    return list(results)


@mcp.tool()
async def search_books(
    query: str,
    max_results: int = 10,
    page: int = 1,
    backend: str = "auto",
) -> list[dict[str, Any]]:
    """Perform a book search using DDGS.

    Args:
        query: Books search query string
        max_results: Maximum number of results to return
        page: Page number of results
        backend: Search backend (auto, or specific engine)

    Returns:
        List of book search results with title, author, and metadata

    """
    results = await asyncio.to_thread(
        lambda: DDGS(proxy=_expand_proxy_tb_alias(os.environ.get("DDGS_PROXY"))).books(
            query=query,
            max_results=max_results,
            page=page,
            backend=backend,
        )
    )
    return list(results)
