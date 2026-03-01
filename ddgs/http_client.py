"""HTTP client."""

import logging
from typing import Any

import primp

from .exceptions import DDGSException, TimeoutException

logger = logging.getLogger(__name__)


class Response:
    """HTTP response."""

    __slots__ = ("content", "status_code", "text")

    def __init__(self, status_code: int, content: bytes, text: str) -> None:
        self.status_code = status_code
        self.content = content
        self.text = text


class HttpClient:
    """HTTP client."""

    def __init__(self, proxy: str | None = None, timeout: int | None = 10, *, verify: bool | str = True) -> None:
        """Initialize the HttpClient object.

        Args:
            proxy (str, optional): proxy for the HTTP client, supports http/https/socks5 protocols.
                example: "http://user:pass@example.com:3128". Defaults to None.
            timeout (int, optional): Timeout value for the HTTP client. Defaults to 10.
            verify: (bool | str):  True to verify, False to skip, or a str path to a PEM file. Defaults to True.

        """
        self.client = primp.Client(
            proxy=proxy,
            timeout=timeout,
            impersonate="random",
            impersonate_os="random",
            verify=verify if isinstance(verify, bool) else True,
            ca_cert_file=verify if isinstance(verify, str) else None,
        )

    def request(self, *args: Any, **kwargs: Any) -> Response:  # noqa: ANN401
        """Make a request to the HTTP client."""
        try:
            resp = self.client.request(*args, **kwargs)
            return Response(status_code=resp.status_code, content=resp.content, text=resp.text)
        except primp.TimeoutError as ex:
            raise TimeoutException(ex) from ex
        except Exception as ex:
            msg = f"{type(ex).__name__}: {ex!r}"
            raise DDGSException(msg) from ex

    def get(self, *args: Any, **kwargs: Any) -> Response:  # noqa: ANN401
        """Make a GET request to the HTTP client."""
        return self.request(*args, method="GET", **kwargs)

    def post(self, *args: Any, **kwargs: Any) -> Response:  # noqa: ANN401
        """Make a POST request to the HTTP client."""
        return self.request(*args, method="POST", **kwargs)
