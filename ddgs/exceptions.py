class DDGSException(Exception):
    """Base exception class for ddgs."""


class RatelimitException(DDGSException):
    """Raised for rate limit exceeded errors during API requests."""


class TimeoutException(DDGSException):
    """Raised for timeout errors during API requests."""


class ConversationLimitException(DDGSException):
    """Raised for conversation limit during API requests to AI endpoint."""
