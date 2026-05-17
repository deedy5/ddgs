"""DDGS API server.

This module provides the FastAPI application for the DDGS REST API.
"""

__all__: list[str] = []

try:
    from ddgs.api_server.api import app as fastapi_app

    __all__ += ["fastapi_app"]
except ImportError:
    # API dependencies not installed
    pass
