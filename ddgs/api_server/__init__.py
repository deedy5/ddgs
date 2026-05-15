"""DDGS API server.

This module provides the FastAPI application for the DDGS REST API
and the distributed network cache service.
"""

__all__: list[str] = []

try:
    from ddgs.api_server.api import app as fastapi_app

    __all__ += ["fastapi_app"]
except ImportError:
    # API dependencies not installed
    pass

try:
    from ddgs.api_server.dht_service import get_dht_service

    __all__ += ["get_dht_service"]
except ImportError:
    # DHT dependencies not installed
    pass
