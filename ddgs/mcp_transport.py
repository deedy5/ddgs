"""Helpers for configuring DDGS MCP transports."""

from typing import Final, Literal, TypeAlias

MCPTransport: TypeAlias = Literal["sse", "http"]

DEFAULT_MCP_TRANSPORT: Final[MCPTransport] = "sse"
MCP_TRANSPORT_CHOICES: Final[tuple[MCPTransport, ...]] = ("sse", "http")

_MCP_TRANSPORT_ENDPOINTS: Final[dict[MCPTransport, str]] = {
    "sse": "/sse",
    "http": "/mcp",
}


class InvalidMCPTransportError(ValueError):
    """Raised when DDGS receives an unsupported MCP transport value."""

    def __init__(self, transport: str) -> None:
        self.transport = transport
        super().__init__(transport)

    def __str__(self) -> str:
        """Return a descriptive error for unsupported transport values."""
        choices = ", ".join(MCP_TRANSPORT_CHOICES)
        return f"Unsupported MCP transport {self.transport!r}. Expected one of: {choices}."


def normalize_mcp_transport(transport: str | None) -> MCPTransport:
    """Normalize an MCP transport string to a supported DDGS transport."""
    if transport is None:
        return DEFAULT_MCP_TRANSPORT

    normalized_transport = transport.strip().lower()
    if normalized_transport == "sse":
        return "sse"
    if normalized_transport == "http":
        return "http"
    raise InvalidMCPTransportError(transport)


def get_mcp_transport_endpoint(transport: str | None) -> str:
    """Return the public endpoint path for the configured MCP transport."""
    return _MCP_TRANSPORT_ENDPOINTS[normalize_mcp_transport(transport)]


class InvalidMCPEndpointError(ValueError):
    """Raised when DDGS receives an invalid MCP endpoint value."""

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        super().__init__(endpoint)

    def __str__(self) -> str:
        """Return a descriptive error for unsupported endpoint values."""
        return f"Invalid MCP endpoint {self.endpoint!r}. Expected a non-empty path."


def normalize_mcp_endpoint(endpoint: str | None, transport: str | None = None) -> str:
    """Normalize an MCP endpoint path.

    If no endpoint is provided, the default endpoint for the given transport is used.
    """
    if endpoint is None:
        return get_mcp_transport_endpoint(transport)

    normalized_endpoint = endpoint.strip()
    if not normalized_endpoint:
        raise InvalidMCPEndpointError(endpoint)

    normalized_endpoint = f"/{normalized_endpoint.lstrip('/')}"
    return normalized_endpoint.rstrip("/") or "/"
