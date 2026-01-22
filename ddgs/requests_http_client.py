"""HTTP client using requests library for DuckDuckGo images search.

This client is specifically designed to work around DuckDuckGo's detection
of the primp library. It uses requests with proper session management
and browser-like headers.
"""

import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import DDGSException, TimeoutException

logger = logging.getLogger(__name__)


class Response:
    """HTTP response."""

    __slots__ = ("content", "status_code", "text")

    def __init__(self, status_code: int, content: bytes, text: str) -> None:
        self.status_code = status_code
        self.content = content
        self.text = text


class RequestsHttpClient:
    """HTTP client using requests library for DuckDuckGo images search."""

    # Default User-Agent to mimic Chrome
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    def __init__(self, proxy: str | None = None, timeout: int | None = 10, *, verify: bool | str = True) -> None:
        """Initialize the RequestsHttpClient object.

        Args:
            proxy (str, optional): proxy for the HTTP client, supports http/https/socks5 protocols.
                example: "http://user:pass@example.com:3128". Defaults to None.
                If None and environment variables HTTP_PROXY/HTTPS_PROXY are set, they will be used.
            timeout (int, optional): Timeout value for the HTTP client. Defaults to 10.
            verify: (bool | str):  True to verify, False to skip, or a str path to a PEM file. Defaults to True.

        """
        # Create a session for cookie management
        self.session = requests.Session()

        # Configure proxy
        if proxy:
            # Use provided proxy
            self.session.proxies = {
                "http": proxy,
                "https": proxy,
            }
        # If proxy is None, requests will use environment variables automatically

        # Set default headers to mimic a real browser
        self.session.headers.update(
            {
                "User-Agent": self.DEFAULT_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set timeout and verify
        self.timeout = timeout or 10
        self.verify: bool | str = verify if isinstance(verify, bool) else True
        if isinstance(verify, str):
            # If verify is a string, it's a path to a CA cert file
            self.verify = verify

    def request(self, method: str, url: str, *args: Any, **kwargs: Any) -> Response:  # noqa: ANN401, ARG002
        """Make a request to the HTTP client.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            *args: Additional positional arguments (for compatibility)
            **kwargs: Additional keyword arguments including:
                - params: Query parameters (for GET requests)
                - data: Request body (for POST requests)
                - headers: Additional headers
                - timeout: Request timeout (overrides default)
                - verify: SSL verification (overrides default)

        Returns:
            Response object with status_code, content, and text attributes.

        Raises:
            TimeoutException: If the request times out.
            DDGSException: If the request fails.

        """
        # Extract common parameters
        params = kwargs.pop("params", None)
        data = kwargs.pop("data", None)
        headers = kwargs.pop("headers", None)
        timeout = kwargs.pop("timeout", self.timeout)
        verify = kwargs.pop("verify", self.verify)

        # Merge headers
        request_headers: dict[str, str] = dict(self.session.headers)
        if headers:
            request_headers.update(headers)

        try:
            resp = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=request_headers,
                timeout=timeout,
                verify=verify,
                **kwargs,
            )
            return Response(status_code=resp.status_code, content=resp.content, text=resp.text)
        except requests.exceptions.Timeout as ex:
            msg = f"Request timed out: {ex!r}"
            raise TimeoutException(msg) from ex
        except requests.exceptions.RequestException as ex:
            msg = f"{type(ex).__name__}: {ex!r}"
            raise DDGSException(msg) from ex

    def get(self, *args: Any, **kwargs: Any) -> Response:  # noqa: ANN401
        """Make a GET request to the HTTP client."""
        return self.request("GET", *args, **kwargs)

    def post(self, *args: Any, **kwargs: Any) -> Response:  # noqa: ANN401
        """Make a POST request to the HTTP client."""
        return self.request("POST", *args, **kwargs)
