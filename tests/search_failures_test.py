"""Offline regressions for search error classification and result collection."""

import threading
from collections.abc import Iterator
from concurrent.futures import Future, wait
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from unittest.mock import patch

import pytest

import ddgs.ddgs as search_module
from ddgs.ddgs import DDGS
from ddgs.exceptions import DDGSException, HTTPStatusException, NoResultsException, RatelimitException, TimeoutException
from ddgs.http_client import HttpClient
from ddgs.results import TextResult


class StubEngine:
    """Supply controlled results without issuing requests to external engines."""

    def __init__(
        self,
        name: str,
        outcome: list[TextResult] | Exception | None,
        release: threading.Event | None = None,
    ) -> None:
        self.name = self.provider = name
        self.outcome = outcome
        self.release = release

    def search(self, *args: Any, **kwargs: Any) -> list[TextResult] | None:
        if self.release is not None:
            assert self.release.wait(5), "collector never released the delayed engine"
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def result(name: str) -> TextResult:
    return TextResult(title=f"python {name}", href=f"https://example.org/{name}", body="python")


def search(engines: list[StubEngine], *, limit: int = 10) -> list[dict[str, Any]]:
    with patch.object(DDGS, "_get_engines", return_value=engines):
        return DDGS().text("python", max_results=limit)


@pytest.fixture
def delayed_result() -> Iterator[threading.Event]:
    """Keep one engine pending until FIRST_EXCEPTION's snapshot is captured."""
    release = threading.Event()

    def controlled_wait(
        futures: Any, timeout: float | None = None, return_when: str = "ALL_COMPLETED"
    ) -> tuple[set[Future[Any]], set[Future[Any]]]:
        snapshot = wait(futures, timeout=timeout, return_when=return_when)
        if return_when == "FIRST_EXCEPTION":
            release.set()
        return snapshot

    with patch.object(search_module, "wait", controlled_wait):
        yield release
    release.set()


def test_late_success_survives_early_failure(delayed_result: threading.Event) -> None:
    results = search(
        [
            StubEngine("failed", RatelimitException("429")),
            StubEngine("late", [result("late")], delayed_result),
        ]
    )
    assert [item["href"] for item in results] == ["https://example.org/late"]


@pytest.mark.parametrize("limit", [1, 10])
def test_late_results_deduplicated_and_limited(delayed_result: threading.Event, limit: int) -> None:
    results = search(
        [
            StubEngine("failed", RuntimeError("failed")),
            StubEngine("late", [result("a"), result("a"), result("b")], delayed_result),
        ],
        limit=limit,
    )
    assert len(results) == min(limit, 2)
    assert len({item["href"] for item in results}) == len(results)


@pytest.mark.parametrize(
    "error",
    [
        TimeoutException("deadline exceeded"),
        RatelimitException("429"),
        HTTPStatusException(403),
        DDGSException("connection failed"),
    ],
)
def test_typed_error_preserved(error: DDGSException) -> None:
    with pytest.raises(type(error)) as raised:
        search([StubEngine("failed", error), StubEngine("empty", [])])
    assert raised.value is error


@pytest.mark.parametrize("error", [TimeoutException("deadline exceeded"), RatelimitException("429")])
def test_late_failure_does_not_replace_collected_error(delayed_result: threading.Event, error: DDGSException) -> None:
    with pytest.raises(type(error)) as raised:
        search(
            [
                StubEngine("early", error),
                StubEngine("late", HTTPStatusException(502), delayed_result),
            ]
        )
    assert raised.value is error


@pytest.mark.parametrize("empty", [None, []])
def test_clean_empty_is_distinct_from_failure(empty: list[TextResult] | None) -> None:
    with pytest.raises(NoResultsException):
        search([StubEngine("empty", empty)])


def test_unexpected_engine_error_keeps_cause() -> None:
    error = ValueError("bad parser input")
    with pytest.raises(DDGSException) as raised:
        search([StubEngine("failed", error)])
    assert raised.value.__cause__ is error
    assert not isinstance(raised.value, NoResultsException)


@pytest.fixture
def local_http() -> Iterator[str]:
    """Use real HTTP responses without public engines or HTTP mocks."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(int(self.path.removeprefix("/")))
            self.end_headers()
            self.wfile.write(b"<html><body>local response</body></html>")

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


@pytest.mark.parametrize("status", [202, 204, 403, 429, 500, 502])
def test_http_denials_are_not_empty_results(local_http: str, status: int) -> None:
    expected = RatelimitException if status == 429 else HTTPStatusException
    with pytest.raises(expected) as raised:
        HttpClient(timeout=3).get(f"{local_http}/{status}")
    if isinstance(raised.value, HTTPStatusException):
        assert raised.value.status_code == status


def test_http_success_body_unchanged(local_http: str) -> None:
    response = HttpClient(timeout=3).get(f"{local_http}/200")
    assert response.status_code == 200
    assert "local response" in response.text


def test_extract_preserves_http_status(local_http: str) -> None:
    with pytest.raises(HTTPStatusException) as raised:
        DDGS().extract(f"{local_http}/403")
    assert raised.value.status_code == 403
