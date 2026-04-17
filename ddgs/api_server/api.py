"""FastAPI application for DDGS API."""

import asyncio
import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ddgs import DDGS
from ddgs.utils import _expand_proxy_tb_alias

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DDGS API",
    description="A FastAPI wrapper for the DDGS (Dux Distributed Global Search) library",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_ddgs() -> DDGS:
    """Create a DDGS instance with proxy configuration from environment."""
    return DDGS(proxy=_expand_proxy_tb_alias(os.environ.get("DDGS_PROXY")))


# Pydantic models for request/response
class TextSearchRequest(BaseModel):
    """Request model for search operations."""

    query: str = Field(..., description="Search query")
    region: str = Field("us-en", description="Region for search (e.g., us-en, uk-en, ru-ru)")
    safesearch: str = Field("moderate", description="Safe search setting (on, moderate, off)")
    timelimit: str | None = Field(None, description="Time limit (d, w, m, y) or custom date range")
    max_results: int | None = Field(10, description="Maximum number of results to return")
    page: int = Field(1, description="Page number of results")
    backend: str = Field("auto", description="Search backend (auto, or specific engine)")


class ImagesSearchRequest(BaseModel):
    """Request model for image search operations."""

    query: str = Field(..., description="Image search query")
    region: str = Field("us-en", description="Region for search (e.g., us-en, uk-en, ru-ru)")
    safesearch: str = Field("moderate", description="Safe search setting (on, moderate, off)")
    timelimit: str | None = Field(None, description="Time limit (d, w, m, y) or custom date range")
    max_results: int | None = Field(10, description="Maximum number of results to return")
    page: int = Field(1, description="Page number of results")
    backend: str = Field("auto", description="Search backend (auto, or specific engine)")
    size: str | None = Field(None, description="Image size (Small, Medium, Large, Wallpaper)")
    color: str | None = Field(
        None,
        description="Image color (Monochrome, Red, Orange, Yellow, Green, Blue, Purple, Pink, Brown, Black, Gray, Teal, White)",  # noqa: E501
    )
    type_image: str | None = Field(None, description="Image type (photo, clipart, gif, transparent, line)")
    layout: str | None = Field(None, description="Image layout (Square, Tall, Wide)")
    license_image: str | None = Field(
        None, description="Image license (any, Public, Share, ShareCommercially, Modify, ModifyCommercially)"
    )


class NewsSearchRequest(BaseModel):
    """Request model for search operations."""

    query: str = Field(..., description="Search query")
    region: str = Field("us-en", description="Region for search (e.g., us-en, uk-en, ru-ru)")
    safesearch: str = Field("moderate", description="Safe search setting (on, moderate, off)")
    timelimit: str | None = Field(None, description="Time limit (d, w, m, y) or custom date range")
    max_results: int | None = Field(10, description="Maximum number of results to return")
    page: int = Field(1, description="Page number of results")
    backend: str = Field("auto", description="Search backend (auto, or specific engine)")


class VideosSearchRequest(BaseModel):
    """Request model for video search operations."""

    query: str = Field(..., description="Video search query")
    region: str = Field("us-en", description="Region for search (e.g., us-en, uk-en, ru-ru)")
    safesearch: str = Field("moderate", description="Safe search setting (on, moderate, off)")
    timelimit: str | None = Field(None, description="Time limit (d, w, m) or custom date range")
    max_results: int | None = Field(10, description="Maximum number of results to return")
    page: int = Field(1, description="Page number of results")
    backend: str = Field("auto", description="Search backend (auto, or specific engine)")
    resolution: str | None = Field(None, description="Video resolution (high, standard)")
    duration: str | None = Field(None, description="Video duration (short, medium, long)")
    license_videos: str | None = Field(None, description="Video license (creativeCommon, youtube)")


class BooksSearchRequest(BaseModel):
    """Request model for book search operations."""

    query: str = Field(..., description="Books search query")
    max_results: int | None = Field(10, description="Maximum number of results to return")
    page: int = Field(1, description="Page number of results")
    backend: str = Field("auto", description="Search backend (auto, or specific engine)")


class ExtractRequest(BaseModel):
    """Request model for URL content extraction."""

    url: str = Field(..., description="URL to extract content from")
    format: str = Field("text_markdown", description="Format: text_markdown, text_plain, text_rich, text, content")


class SearchResponse(BaseModel):
    """Response model for search operations."""

    results: list[dict[str, Any]]


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    version: str
    service: str


@app.get("/", response_model=HealthResponse)
async def root() -> HealthResponse:
    """Root endpoint with basic service information."""
    return HealthResponse(status="healthy", version="1.0.0", service="DDGS API")


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0", service="DDGS API")


@app.post("/search/text", response_model=SearchResponse)
async def search_text(request: TextSearchRequest) -> SearchResponse:
    """Perform a text search."""
    try:
        results = await asyncio.to_thread(
            lambda: _get_ddgs().text(
                query=request.query,
                region=request.region,
                safesearch=request.safesearch,
                timelimit=request.timelimit,
                max_results=request.max_results,
                page=request.page,
                backend=request.backend,
            )
        )

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in text search: %s", e)
        raise HTTPException(status_code=500, detail=f"Search failed: {e!s}") from e


@app.get("/search/text", response_model=SearchResponse)
async def search_text_get(
    query: str,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: str | None = None,
    max_results: int = 10,
    page: int = 1,
    backend: str = "auto",
) -> SearchResponse:
    """Perform a text search via GET request."""
    try:
        results = await asyncio.to_thread(
            lambda: _get_ddgs().text(
                query=query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                max_results=max_results,
                page=page,
                backend=backend,
            )
        )

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in text search (GET): %s", e)
        raise HTTPException(status_code=500, detail=f"Search failed: {e!s}") from e


@app.post("/search/images", response_model=SearchResponse)
async def search_images(request: ImagesSearchRequest) -> SearchResponse:
    """Perform an image search."""
    try:
        results = await asyncio.to_thread(
            lambda: _get_ddgs().images(
                query=request.query,
                region=request.region,
                safesearch=request.safesearch,
                timelimit=request.timelimit,
                max_results=request.max_results,
                page=request.page,
                backend=request.backend,
                size=request.size,
                color=request.color,
                type_image=request.type_image,
                layout=request.layout,
                license_image=request.license_image,
            )
        )

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in image search: %s", e)
        raise HTTPException(status_code=500, detail=f"Image search failed: {e!s}") from e


@app.get("/search/images", response_model=SearchResponse)
async def search_images_get(
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
) -> SearchResponse:
    """Perform an image search via GET request."""
    try:
        results = await asyncio.to_thread(
            lambda: _get_ddgs().images(
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

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in image search (GET): %s", e)
        raise HTTPException(status_code=500, detail=f"Image search failed: {e!s}") from e


@app.post("/search/news", response_model=SearchResponse)
async def search_news(request: NewsSearchRequest) -> SearchResponse:
    """Perform a news search."""
    try:
        results = await asyncio.to_thread(
            lambda: _get_ddgs().news(
                query=request.query,
                region=request.region,
                safesearch=request.safesearch,
                timelimit=request.timelimit,
                max_results=request.max_results,
                page=request.page,
                backend=request.backend,
            )
        )

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in news search: %s", e)
        raise HTTPException(status_code=500, detail=f"News search failed: {e!s}") from e


@app.get("/search/news", response_model=SearchResponse)
async def search_news_get(
    query: str,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: str | None = None,
    max_results: int = 10,
    page: int = 1,
    backend: str = "auto",
) -> SearchResponse:
    """Perform a news search via GET request."""
    try:
        results = await asyncio.to_thread(
            lambda: _get_ddgs().news(
                query=query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                max_results=max_results,
                page=page,
                backend=backend,
            )
        )

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in news search (GET): %s", e)
        raise HTTPException(status_code=500, detail=f"News search failed: {e!s}") from e


@app.post("/search/videos", response_model=SearchResponse)
async def search_videos(request: VideosSearchRequest) -> SearchResponse:
    """Perform a video search."""
    try:
        results = await asyncio.to_thread(
            lambda: _get_ddgs().videos(
                query=request.query,
                region=request.region,
                safesearch=request.safesearch,
                timelimit=request.timelimit,
                max_results=request.max_results,
                page=request.page,
                backend=request.backend,
                resolution=request.resolution,
                duration=request.duration,
                license_videos=request.license_videos,
            )
        )

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in video search: %s", e)
        raise HTTPException(status_code=500, detail=f"Video search failed: {e!s}") from e


@app.get("/search/videos", response_model=SearchResponse)
async def search_videos_get(
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
) -> SearchResponse:
    """Perform a video search via GET request."""
    try:
        results = await asyncio.to_thread(
            lambda: _get_ddgs().videos(
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

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in video search (GET): %s", e)
        raise HTTPException(status_code=500, detail=f"Video search failed: {e!s}") from e


@app.post("/search/books", response_model=SearchResponse)
async def search_books(request: BooksSearchRequest) -> SearchResponse:
    """Perform a book search."""
    try:
        results = await asyncio.to_thread(
            lambda: _get_ddgs().books(
                query=request.query,
                max_results=request.max_results,
                page=request.page,
                backend=request.backend,
            )
        )

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in book search: %s", e)
        raise HTTPException(status_code=500, detail=f"Book search failed: {e!s}") from e


@app.get("/search/books", response_model=SearchResponse)
async def search_books_get(
    query: str,
    max_results: int = 10,
    page: int = 1,
    backend: str = "auto",
) -> SearchResponse:
    """Perform a book search via GET request."""
    try:
        results = await asyncio.to_thread(
            lambda: _get_ddgs().books(
                query=query,
                max_results=max_results,
                page=page,
                backend=backend,
            )
        )

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in book search (GET): %s", e)
        raise HTTPException(status_code=500, detail=f"Book search failed: {e!s}") from e


@app.post("/extract")
async def extract_content(request: ExtractRequest) -> dict[str, str | bytes]:
    """Extract text content from a URL."""
    try:
        return await asyncio.to_thread(
            lambda: _get_ddgs().extract(
                url=request.url,
                fmt=request.format,
            )
        )
    except Exception as e:
        logger.warning("Error extracting content: %s", e)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e!s}") from e


@app.get("/extract")
async def extract_content_get(url: str, fmt: str = "text_markdown") -> dict[str, str | bytes]:
    """Extract text content from a URL via GET request."""
    try:
        return await asyncio.to_thread(
            lambda: _get_ddgs().extract(
                url=url,
                fmt=fmt,
            )
        )
    except Exception as e:
        logger.warning("Error extracting content (GET): %s", e)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e!s}") from e


# Optional DHT Endpoints - only added if DHT dependencies are installed
try:
    from pydantic import BaseModel, Field

    class CacheRequest(BaseModel):
        """Request model for cache operations."""

        query: str = Field(..., description="Search query")
        results: list[dict[str, Any]] = Field(..., description="Search results to cache")
        category: str = Field("text", description="Search category")

    class DhtStatusResponse(BaseModel):
        """Response model for DHT status."""

        running: bool
        connected: bool
        peer_id: str | None
        port: int | None
        cache_size: int
        cache_count: int
        peer_count: int
        routing_table_size: int
        metrics: dict[str, Any]

    @app.get("/dht/cache", response_model=SearchResponse)
    async def get_cached(query: str, category: str = "text") -> SearchResponse:
        """Get cached results from DHT."""
        from ddgs.api_server import get_dht_service  # noqa: PLC0415

        dht = get_dht_service()
        results = dht.get_cached(query, category)
        if results is None:
            raise HTTPException(status_code=404, detail="Not found in cache")
        return SearchResponse(results=results)

    @app.post("/dht/cache", status_code=201)
    async def cache_results(request: CacheRequest) -> dict[str, str]:
        """Cache results to DHT."""
        from ddgs.api_server import get_dht_service  # noqa: PLC0415

        dht = get_dht_service()
        dht.cache(request.query, request.results, request.category)
        return {"status": "ok"}

    @app.delete("/dht/cache", status_code=204)
    async def invalidate_cache(query: str, category: str = "text") -> None:
        """Invalidate cached results."""
        from ddgs.api_server import get_dht_service  # noqa: PLC0415
        from ddgs.dht.types import compute_query_hash  # noqa: PLC0415

        dht = get_dht_service()
        query_hash = compute_query_hash(query, category)
        if dht._cache:
            dht._cache.delete(query_hash)

    @app.get("/dht/status", response_model=DhtStatusResponse)
    async def dht_status() -> DhtStatusResponse:
        """Get DHT service status."""
        from ddgs.api_server import get_dht_service  # noqa: PLC0415

        dht = get_dht_service()
        status = dht.get_status()
        return DhtStatusResponse(**status)

    @app.get("/dht/peers", response_model=list[str])
    async def dht_peers() -> list[str]:
        """Get list of connected DHT peers."""
        from ddgs.api_server import get_dht_service  # noqa: PLC0415

        dht = get_dht_service()
        return dht.get_peers()

    @app.get("/dht/peers/detailed", response_model=list[dict[str, Any]])
    async def dht_peers_detailed() -> list[dict[str, Any]]:
        """Get detailed information about all connected peers."""
        from ddgs.api_server import get_dht_service  # noqa: PLC0415

        dht = get_dht_service()
        return dht._dht.get_neighbors() if dht._dht else []

    @app.get("/dht/map")
    async def dht_map() -> dict[str, Any]:
        """Get local DHT network map view as graph structure.

        Each node only sees its own routing table neighborhood.
        No global crawling, no gossip, zero additional network traffic.
        """
        from ddgs.api_server import get_dht_service  # noqa: PLC0415

        dht = get_dht_service()
        if not dht._dht:
            return {"nodes": [], "edges": [], "total_peers_estimated": 0, "local_view_size": 0, "bucket_depth": 0}

        peers = dht._dht.get_neighbors()

        # Build graph
        nodes = []
        edges = []

        # Add self node
        nodes.append(
            {
                "id": dht._dht.peer_id,
                "type": "self",
                "connections": len(peers),
            }
        )

        # Add neighbor nodes
        for peer in peers:
            nodes.append(
                {
                    "id": peer["peer_id"],
                    "type": "peer",
                    "xor_distance": peer["xor_distance"],
                    "latency_ms": peer["latency_ms"],
                }
            )
            edges.append(
                {
                    "source": dht._dht.peer_id,
                    "target": peer["peer_id"],
                    "latency_ms": peer["latency_ms"],
                }
            )

        # Network size estimation using Kademlia math
        # For 256 bit ID space: estimated_size = 2^(average_bucket_depth)
        bucket_depth = next((i for i, count in enumerate(dht._dht.kbucket_distribution) if count == 0), 255)
        estimated_size = 2**bucket_depth

        return {
            "nodes": nodes,
            "edges": edges,
            "total_peers_estimated": estimated_size,
            "local_view_size": len(nodes),
            "bucket_depth": bucket_depth,
        }

    @app.get("/dht/metrics")
    async def dht_metrics() -> Response:
        """Get DHT metrics in Prometheus format."""
        from ddgs.api_server import get_dht_service  # noqa: PLC0415

        dht = get_dht_service()
        status = dht.get_status()

        metrics = [
            "# HELP ddgs_dht_running Whether DHT service is running",
            "# TYPE ddgs_dht_running gauge",
            f"ddgs_dht_running {1 if status['running'] else 0}",
            "# HELP ddgs_dht_connected_peers Number of currently connected peers",
            "# TYPE ddgs_dht_connected_peers gauge",
            f"ddgs_dht_connected_peers {status.get('peer_count', 0)}",
            "# HELP ddgs_dht_cache_entries Number of entries in local cache",
            "# TYPE ddgs_dht_cache_entries gauge",
            f"ddgs_dht_cache_entries {status['cache_count']}",
            "# HELP ddgs_dht_cache_size_bytes Size of local cache in bytes",
            "# TYPE ddgs_dht_cache_size_bytes gauge",
            f"ddgs_dht_cache_size_bytes {status['cache_size']}",
            "# HELP ddgs_dht_query_success_rate DHT query success rate (0-1)",
            "# TYPE ddgs_dht_query_success_rate gauge",
            f"ddgs_dht_query_success_rate {status['metrics'].get('query_success_rate', 1.0)}",
            "# HELP ddgs_dht_average_query_latency_ms Average DHT query latency in milliseconds",
            "# TYPE ddgs_dht_average_query_latency_ms gauge",
            f"ddgs_dht_average_query_latency_ms {status['metrics'].get('average_query_latency_ms', 0.0)}",
            "# HELP ddgs_dht_routing_table_size Number of entries in DHT routing table",
            "# TYPE ddgs_dht_routing_table_size gauge",
            f"ddgs_dht_routing_table_size {status.get('routing_table_size', 0)}",
        ]

        return Response("\n".join(metrics), media_type="text/plain")

    logger.info("DHT endpoints enabled - distributed cache available")

except ImportError:
    # DHT dependencies not installed - silently skip adding endpoints
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # noqa: S104
