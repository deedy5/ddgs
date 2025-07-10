from __future__ import annotations

import logging
from random import choice
from typing import Any

import primp


class Response:
    __slots__ = ("status_code", "content", "text")

    def __init__(self, status_code: int, content: bytes, text: str):
        self.status_code = status_code
        self.content = content
        self.text = text


class HttpClient:
    def __init__(
        self,
        proxy: str | None = None,
        timeout: int | None = 10,
        verify: bool = True,
    ) -> None:
        """Initialize the HttpClient object.

        Args:
            proxy (str, optional): proxy for the HTTP client, supports http/https/socks5 protocols.
                example: "http://user:pass@example.com:3128". Defaults to None.
            timeout (int, optional): Timeout value for the HTTP client. Defaults to 10.
        """
        self.client = primp.Client(
            proxy=proxy,
            timeout=timeout,
            impersonate="random",
            impersonate_os=choice(["macos", "linux", "windows"]),
            verify=verify,
        )

    def request(self, *args: Any, **kwargs: Any) -> Response:
        try:
            resp = self.client.request(*args, **kwargs)
            return Response(status_code=resp.status_code, content=resp.content, text=resp.text)
        except Exception as ex:
            logging.warning(f"{type(ex).__name__}: {ex}", exc_info=True)
            return Response(status_code=500, content=b"", text="")

    def get(self, *args: Any, **kwargs: Any) -> Response:
        return self.request(*args, method="GET", **kwargs)

    def post(self, *args: Any, **kwargs: Any) -> Response:
        return self.request(*args, method="POST", **kwargs)
