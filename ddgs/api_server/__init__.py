"""DDGS API server with MCP support.

This module consolidates the FastAPI application and MCP server.
"""

import importlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from ddgs.mcp_transport import normalize_mcp_endpoint, normalize_mcp_transport


def _mount_http_transport(app: FastAPI, mcp_server: FastMCP[Any], endpoint: str) -> None:
    """Mount the HTTP MCP transport and bridge its lifespan into FastAPI."""
    mcp_server.settings.streamable_http_path = endpoint
    streamable_http_app = mcp_server.streamable_http_app()

    # Mounted sub-app lifespans are not entered by FastAPI/Starlette, so the parent
    # app needs to drive the streamable session manager explicitly.
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(instance: FastAPI) -> AsyncIterator[Any]:
        async with original_lifespan(instance) as lifespan_state, mcp_server.session_manager.run():
            yield lifespan_state

    app.router.lifespan_context = lifespan
    app.mount("/", streamable_http_app)


def _create_fastapi_app_and_mcp(
    transport: str | None = None, endpoint: str | None = None
) -> tuple[FastAPI, FastMCP[Any]]:
    api_module = importlib.reload(importlib.import_module("ddgs.api_server.api"))
    mcp_module = importlib.reload(importlib.import_module("ddgs.api_server.mcp"))

    fastapi_app = api_module.app
    mcp_server = mcp_module.mcp
    normalized_transport = normalize_mcp_transport(transport)
    normalized_endpoint = normalize_mcp_endpoint(endpoint, normalized_transport)

    if normalized_transport == "http":
        _mount_http_transport(fastapi_app, mcp_server, normalized_endpoint)
    else:
        mcp_server.settings.sse_path = normalized_endpoint
        fastapi_app.mount("/", mcp_server.sse_app())

    return fastapi_app, mcp_server


def create_fastapi_app(transport: str | None = None, endpoint: str | None = None) -> FastAPI:
    """Create a FastAPI app with the selected MCP transport and endpoint."""
    fastapi_app, _ = _create_fastapi_app_and_mcp(transport=transport, endpoint=endpoint)
    return fastapi_app

fastapi_app, mcp = _create_fastapi_app_and_mcp()

__all__ = ["create_fastapi_app", "fastapi_app", "mcp"]
