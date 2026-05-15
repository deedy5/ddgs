"""Temporary HTTP client for 'backend=duckduckgo'. Delete when HttpClient is fixed."""

import logging
import ssl
from random import SystemRandom
from types import TracebackType
from typing import TYPE_CHECKING, Any

import h2
import httpcore
import httpx

from .exceptions import DDGSException, TimeoutException

if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)
random = SystemRandom()


class Response:
    """HTTP response."""

    __slots__ = ("content", "status_code", "text")

    def __init__(self, status_code: int, content: bytes, text: str) -> None:
        self.status_code = status_code
        self.content = content
        self.text = text


class HttpClient2:
    """Temporary HTTP client."""

    def __init__(
        self,
        headers: dict[str, str] | None = None,
        proxy: str | None = None,
        timeout: int | None = 10,
        *,
        verify: bool | str = True,
    ) -> None:
        """Initialize the HttpClient object.

        Args:
            headers (dict, optional): headers for the HTTP client.
            proxy (str, optional): proxy for the HTTP client, supports http/https/socks5 protocols.
                example: "http://user:pass@example.com:3128". Defaults to None.
            timeout (int, optional): Timeout value for the HTTP client. Defaults to 10.
            verify: (bool | str):  True to verify, False to skip or str path to a PEM file. Defaults to True.

        """
        self.client = httpx.Client(
            headers=headers,
            proxy=proxy,
            timeout=timeout,
            verify=_get_random_ssl_context(verify=verify) if verify else False,
            follow_redirects=False,
            http2=True,
        )

    def request(self, *args: Any, **kwargs: Any) -> Response:  # noqa: ANN401
        """Make a request to the HTTP client."""
        with Patch():
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


# SSL
DEFAULT_CIPHERS = [  # https://developers.cloudflare.com/ssl/reference/cipher-suites/recommendations/
    "TLS_AES_128_GCM_SHA256", "TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256",
    # Modern:
    "ECDHE-ECDSA-AES128-GCM-SHA256", "ECDHE-ECDSA-CHACHA20-POLY1305", "ECDHE-RSA-AES128-GCM-SHA256",
    "ECDHE-RSA-CHACHA20-POLY1305", "ECDHE-ECDSA-AES256-GCM-SHA384", "ECDHE-RSA-AES256-GCM-SHA384",
    # Compatible:
    "ECDHE-ECDSA-AES128-GCM-SHA256", "ECDHE-ECDSA-CHACHA20-POLY1305", "ECDHE-RSA-AES128-GCM-SHA256",
    "ECDHE-RSA-CHACHA20-POLY1305", "ECDHE-ECDSA-AES256-GCM-SHA384", "ECDHE-RSA-AES256-GCM-SHA384",
    "ECDHE-ECDSA-AES128-SHA256", "ECDHE-RSA-AES128-SHA256", "ECDHE-ECDSA-AES256-SHA384",  "ECDHE-RSA-AES256-SHA384",
    # Legacy:
    "ECDHE-ECDSA-AES128-SHA", "ECDHE-RSA-AES128-SHA", "AES128-GCM-SHA256", "AES128-SHA256", "AES128-SHA",
    "ECDHE-RSA-AES256-SHA", "AES256-GCM-SHA384", "AES256-SHA256", "AES256-SHA", "DES-CBC3-SHA",
]  # fmt: skip


def _get_random_ssl_context(*, verify: bool | str) -> ssl.SSLContext:
    ssl_context = ssl.create_default_context(cafile=verify if isinstance(verify, str) else None)
    shuffled_ciphers = random.sample(DEFAULT_CIPHERS[9:], len(DEFAULT_CIPHERS) - 9)
    ssl_context.set_ciphers(":".join(DEFAULT_CIPHERS[:9] + shuffled_ciphers))
    commands: list[None | Callable[[ssl.SSLContext], None]] = [
        None,
        lambda context: setattr(context, "maximum_version", ssl.TLSVersion.TLSv1_2),
        lambda context: setattr(context, "minimum_version", ssl.TLSVersion.TLSv1_3),
        lambda context: setattr(context, "options", context.options | ssl.OP_NO_TICKET),
    ]
    random_command = random.choice(commands)
    if random_command:
        random_command(ssl_context)
    return ssl_context


class Patch:
    """Patch the HTTP2Connection._send_connection_init method."""

    def __enter__(self) -> None:
        """Enter the context manager."""

        def _send_connection_init(self: httpcore._sync.http2.HTTP2Connection, request: httpcore.Request) -> None:
            self._h2_state.local_settings = h2.settings.Settings(
                client=True,
                initial_values={
                    h2.settings.SettingCodes.INITIAL_WINDOW_SIZE: random.randint(100, 200),
                    h2.settings.SettingCodes.HEADER_TABLE_SIZE: random.randint(4000, 5000),
                    h2.settings.SettingCodes.MAX_FRAME_SIZE: random.randint(16384, 65535),
                    h2.settings.SettingCodes.MAX_CONCURRENT_STREAMS: random.randint(100, 200),
                    h2.settings.SettingCodes.MAX_HEADER_LIST_SIZE: random.randint(65500, 66500),
                    h2.settings.SettingCodes.ENABLE_CONNECT_PROTOCOL: random.randint(0, 1),
                    h2.settings.SettingCodes.ENABLE_PUSH: random.randint(0, 1),
                },
            )
            self._h2_state.initiate_connection()
            self._h2_state.increment_flow_control_window(2**24)
            self._write_outgoing_data(request)

        self.original_send_connection_init = httpcore._sync.http2.HTTP2Connection._send_connection_init
        httpcore._sync.http2.HTTP2Connection._send_connection_init = _send_connection_init  # type: ignore[method-assign]

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        """Exit the context manager."""
        httpcore._sync.http2.HTTP2Connection._send_connection_init = self.original_send_connection_init  # type: ignore[method-assign]
