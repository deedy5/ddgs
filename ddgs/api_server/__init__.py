"""DDGS API server with MCP support.

This module consolidates the FastAPI application and MCP server.
"""

import logging

# Import FastAPI app and MCP server
from ddgs.api_server.api import app as fastapi_app
from ddgs.api_server.mcp import mcp

logger = logging.getLogger(__name__)

# Mount MCP SSE endpoint to FastAPI app
fastapi_app.mount("/", mcp.sse_app())
logger.info("MCP server enabled at /sse")

__all__ = ["fastapi_app", "mcp"]
