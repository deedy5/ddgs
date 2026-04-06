"""DDGS API server.

This module provides the FastAPI application for the DDGS REST API.
"""

from ddgs.api_server.api import app as fastapi_app

__all__ = ["fastapi_app"]
