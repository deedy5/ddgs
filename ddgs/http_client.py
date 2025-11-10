"""HTTP client."""

import logging
from secrets import choice
from typing import Any, Final, Literal, get_args

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

    _impersonates: Final = get_args(Literal[
        "chrome_100", "chrome_101", "chrome_104", "chrome_105", "chrome_106", "chrome_107",
        "chrome_108", "chrome_109", "chrome_114", "chrome_116", "chrome_117", "chrome_118",
        "chrome_119", "chrome_120", "chrome_123", "chrome_124", "chrome_126", "chrome_127",
        "chrome_128", "chrome_129", "chrome_130", "chrome_131", "chrome_133",
        "safari_15.3", "safari_15.5", "safari_15.6.1", "safari_16", "safari_16.5",
        "safari_17.0", "safari_17.2.1", "safari_17.4.1", "safari_17.5",
        "safari_18", "safari_18.2",
        "edge_101", "edge_122", "edge_127", "edge_131",
        "firefox_109", "firefox_117", "firefox_128", "firefox_133", "firefox_135",
    ])  # fmt: skip
    _impersonates_os: Final = get_args(Literal["macos", "linux", "windows"])

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
            impersonate=choice(self._impersonates),
            impersonate_os=choice(self._impersonates_os),
            verify=verify if isinstance(verify, bool) else True,
            ca_cert_file=verify if isinstance(verify, str) else None,
        )

    def request(self, *args: Any, **kwargs: Any) -> Response:  # noqa: ANN401
        """Make a request to the HTTP client."""
        try:
            resp = self.client.request(*args, **kwargs)
            return Response(status_code=resp.status_code, content=resp.content, text=resp.text)
        except Exception as ex:
            if "timed out" in f"{ex}":
                msg = f"Request timed out: {ex!r}"
                raise TimeoutException(msg) from ex
            msg = f"{type(ex).__name__}: {ex!r}"
            raise DDGSException(msg) from ex

    def get(self, *args: Any, **kwargs: Any) -> Response:  # noqa: ANN401
        """Make a GET request to the HTTP client."""
        return self.request(*args, method="GET", **kwargs)

    def post(self, *args: Any, **kwargs: Any) -> Response:  # noqa: ANN401
        """Make a POST request to the HTTP client."""
        return self.request(*args, method="POST", **kwargs)
