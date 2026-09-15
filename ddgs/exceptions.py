"""DDGS exceptions."""


class DDGSException(Exception):
    """Base exception class for ddgs."""


class NoResultsException(DDGSException):
    """Raised when engines return no results without reporting a failure."""


class HTTPStatusException(DDGSException):
    """Raised for an unexpected HTTP response, exposing its status_code."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"Unexpected HTTP status: {status_code}")


class RatelimitException(DDGSException):
    """Raised for rate limit exceeded errors during API requests."""


class TimeoutException(DDGSException):
    """Raised for timeout errors during API requests."""
