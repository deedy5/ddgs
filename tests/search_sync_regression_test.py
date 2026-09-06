"""Regression tests for DDGS._search_sync future-collection bug (issue #427).

These tests use controlled engine stubs that bypass HTTP entirely (no network calls,
no HTTP mocking) so they can run offline and exercise the concurrency timing that
triggers the bug: `wait(..., return_when="FIRST_EXCEPTION")` returning early while a
sibling future is still running and successful.
"""

import time
from collections.abc import Mapping
from typing import Any, ClassVar

import pytest

from ddgs.base import BaseSearchEngine
from ddgs.ddgs import DDGS
from ddgs.exceptions import DDGSException, TimeoutException
from ddgs.results import TextResult


def _make_stub_engine(
    provider_name: str,
    *,
    delay: float,
    raises: bool = False,
    href: str = "",
    error: Exception | None = None,
) -> BaseSearchEngine[TextResult]:
    """Build a search-engine stub with a unique provider name and no HTTP calls."""

    class _Stub(BaseSearchEngine[TextResult]):
        name = provider_name
        category = "text"
        provider = provider_name
        search_url = "http://stub.invalid"
        search_method = "GET"
        items_xpath = ""
        elements_xpath: ClassVar[Mapping[str, str]] = {}

        def __init__(self) -> None:
            self.results: list[TextResult] = []

        def build_payload(self, *args: Any, **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
            """Unused: `search` is overridden directly to avoid HTTP."""
            return {}

        def search(self, *args: Any, **kwargs: Any) -> list[TextResult] | None:  # noqa: ANN401
            """Sleep for `delay`, then either raise or return one canned result."""
            time.sleep(delay)
            if error is not None:
                raise error
            if raises:
                msg = f"{provider_name} failed"
                raise RuntimeError(msg)
            return [TextResult(title=provider_name, href=href, body=provider_name)]

    return _Stub()


class _StubDDGS(DDGS):
    """DDGS subclass that returns a fixed, deterministic list of engine stubs."""

    def __init__(self, engines: list[BaseSearchEngine[Any]]) -> None:
        super().__init__()
        self._stub_engines = engines

    def _get_engines(self, category: str, backend: str) -> list[BaseSearchEngine[Any]]:
        """Return the fixed stub engines instead of the real registry."""
        return self._stub_engines


def test_pending_success_after_first_exception_is_not_dropped() -> None:
    """A slower successful engine must not be dropped when a faster sibling raises first.

    Reproduces #427: `wait(..., return_when="FIRST_EXCEPTION")` returns as soon as the
    fast-failing engine raises, leaving the slow-but-successful engine's future in
    `not_done`. The executor still blocks for it on `__exit__`, but its result was
    previously discarded instead of being collected.
    """
    delay = 0.3
    fast_fail = _make_stub_engine("fast_fail", delay=0.05, raises=True)
    slow_success = _make_stub_engine("slow_success", delay=delay, href="http://slow-success.example")
    ddgs = _StubDDGS([fast_fail, slow_success])

    start = time.monotonic()
    results = ddgs._search_sync("text", "query", max_results=10)
    elapsed = time.monotonic() - start

    # Sanity check that we actually waited for the slow engine rather than passing by luck.
    assert elapsed >= delay
    assert len(results) == 1
    assert results[0]["href"] == "http://slow-success.example"


def test_no_duplicate_results_after_pending_future_collected() -> None:
    """Results resolved before and after the pending-future rescue must not repeat."""
    fast_success = _make_stub_engine("fast_success", delay=0.0, href="http://fast-success.example")
    fast_fail = _make_stub_engine("fast_fail", delay=0.05, raises=True)
    slow_success = _make_stub_engine("slow_success", delay=0.3, href="http://slow-success.example")
    ddgs = _StubDDGS([fast_success, fast_fail, slow_success])

    results = ddgs._search_sync("text", "query", max_results=10)

    hrefs = [r["href"] for r in results]
    assert sorted(hrefs) == ["http://fast-success.example", "http://slow-success.example"]
    assert len(hrefs) == len(set(hrefs))


def test_all_engines_fail_still_raises() -> None:
    """When every backend genuinely fails, DDGSException must still be raised."""
    fast_fail = _make_stub_engine("fast_fail", delay=0.0, raises=True)
    slow_fail = _make_stub_engine("slow_fail", delay=0.1, raises=True)
    ddgs = _StubDDGS([fast_fail, slow_fail])

    with pytest.raises(DDGSException):
        ddgs._search_sync("text", "query", max_results=10)


@pytest.mark.parametrize("first_error", [TimeoutException("timed out"), RuntimeError("first failure")])
def test_pending_failure_preserves_existing_error(first_error: Exception) -> None:
    """Rescuing pending futures must not replace the earlier error or its timeout type."""
    early = _make_stub_engine("early", delay=0.05, error=first_error)
    late = _make_stub_engine("late", delay=0.3, error=RuntimeError("late failure"))
    ddgs = _StubDDGS([early, late])
    expected_type = TimeoutException if isinstance(first_error, TimeoutException) else DDGSException

    with pytest.raises(expected_type, match=str(first_error)):
        ddgs._search_sync("text", "query", max_results=10)
