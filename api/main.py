"""FastAPI application for DDGS API."""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ddgs import DDGS

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
        results = DDGS().text(
            query=request.query,
            region=request.region,
            safesearch=request.safesearch,
            timelimit=request.timelimit,
            max_results=request.max_results,
            page=request.page,
            backend=request.backend,
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
        results = DDGS().text(
            query=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            page=page,
            backend=backend,
        )

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in text search (GET): %s", e)
        raise HTTPException(status_code=500, detail=f"Search failed: {e!s}") from e


@app.post("/search/images", response_model=SearchResponse)
async def search_images(request: ImagesSearchRequest) -> SearchResponse:
    """Perform an image search."""
    try:
        results = DDGS().images(
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
        results = DDGS().images(
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

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in image search (GET): %s", e)
        raise HTTPException(status_code=500, detail=f"Image search failed: {e!s}") from e


@app.post("/search/news", response_model=SearchResponse)
async def search_news(request: NewsSearchRequest) -> SearchResponse:
    """Perform a news search."""
    try:
        results = DDGS().news(
            query=request.query,
            region=request.region,
            safesearch=request.safesearch,
            timelimit=request.timelimit,
            max_results=request.max_results,
            page=request.page,
            backend=request.backend,
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
        results = DDGS().news(
            query=query,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit,
            max_results=max_results,
            page=page,
            backend=backend,
        )

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in news search (GET): %s", e)
        raise HTTPException(status_code=500, detail=f"News search failed: {e!s}") from e


@app.post("/search/videos", response_model=SearchResponse)
async def search_videos(request: VideosSearchRequest) -> SearchResponse:
    """Perform a video search."""
    try:
        results = DDGS().videos(
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
        results = DDGS().videos(
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

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in video search (GET): %s", e)
        raise HTTPException(status_code=500, detail=f"Video search failed: {e!s}") from e


@app.post("/search/books", response_model=SearchResponse)
async def search_books(request: BooksSearchRequest) -> SearchResponse:
    """Perform a book search."""
    try:
        results = DDGS().books(
            query=request.query,
            max_results=request.max_results,
            page=request.page,
            backend=request.backend,
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
        results = DDGS().books(
            query=query,
            max_results=max_results,
            page=page,
            backend=backend,
        )

        return SearchResponse(results=results)
    except Exception as e:
        logger.warning("Error in book search (GET): %s", e)
        raise HTTPException(status_code=500, detail=f"Book search failed: {e!s}") from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # noqa: S104
