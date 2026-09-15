"""Offline regression tests at the MCP SDK tool-call boundary."""

import asyncio
import json
import threading
from typing import Any
from unittest.mock import Mock

import pytest

pytest.importorskip("mcp.server.mcpserver")

from mcp.server.mcpserver.exceptions import ToolError, UnexpectedToolError
from mcp.types import CallToolResult, TextContent

from ddgs.api_server import mcp as server
from ddgs.exceptions import DDGSException, HTTPStatusException, NoResultsException, RatelimitException, TimeoutException

SECRET = "https://proxy-user:proxy-password@private.example/path?token=secret-token"
COMMON = {
    "query": "offline query",
    "max_results": 3,
    "page": 2,
    "backend": "auto",
}
SEARCH = {**COMMON, "region": "uk-en", "safesearch": "off", "timelimit": "w"}
TOOLS = [
    ("search_text", "text", SEARCH),
    (
        "search_images",
        "images",
        {
            **SEARCH,
            "size": "Large",
            "color": "color",
            "type_image": "photo",
            "layout": "Wide",
            "license_image": "any",
        },
    ),
    ("search_news", "news", SEARCH),
    (
        "search_videos",
        "videos",
        {**SEARCH, "resolution": "high", "duration": "short", "license_videos": "youtube"},
    ),
    ("search_books", "books", COMMON),
    ("extract_content", "extract", {"url": "https://example.test/article", "fmt": "text_plain"}),
]
TOOL_IDS = [tool[0] for tool in TOOLS]


@pytest.mark.parametrize(("tool_name", "method", "arguments"), TOOLS, ids=TOOL_IDS)
def test_success_preserves_output_arguments_and_worker_thread(
    monkeypatch: pytest.MonkeyPatch, tool_name: str, method: str, arguments: dict[str, Any]
) -> None:
    """The registered tools preserve results and run construction/search off-loop."""
    output: dict[str, Any] | list[dict[str, Any]] = (
        {"url": arguments["url"], "content": "Offline content"}
        if method == "extract"
        else [{"title": "Offline result", "url": "https://example.test/result", "body": "Sample"}]
    )
    loop_thread = threading.get_ident()
    worker_threads: list[int] = []

    def run(**kwargs: Any) -> Any:
        worker_threads.append(threading.get_ident())
        return output

    client = Mock()
    operation = Mock(side_effect=run)
    setattr(client, method, operation)

    def construct(**kwargs: Any) -> Mock:
        worker_threads.append(threading.get_ident())
        return client

    constructor = Mock(side_effect=construct)
    monkeypatch.setattr(server, "DDGS", constructor)
    monkeypatch.setenv("DDGS_PROXY", SECRET)

    result = asyncio.run(server.mcp.call_tool(tool_name, arguments))

    assert isinstance(result, CallToolResult)
    assert not result.is_error
    assert result.structured_content == (output if method == "extract" else {"result": output})
    assert len(result.content) == 1
    content = result.content[0]
    assert isinstance(content, TextContent)
    assert json.loads(content.text) == (output if isinstance(output, dict) else output[0])
    constructor.assert_called_once_with(proxy=SECRET)
    operation.assert_called_once_with(**arguments)
    assert len(worker_threads) == 2
    assert worker_threads[0] == worker_threads[1] != loop_thread


@pytest.mark.parametrize(("tool_name", "method", "arguments"), TOOLS, ids=TOOL_IDS)
@pytest.mark.parametrize(
    "failure",
    ["timeout", "ratelimit", "http-403", "http-429", "http-500", "http-503", "noresults", "ddgs", "unexpected"],
)
def test_errors_at_sdk_tool_boundary(
    monkeypatch: pytest.MonkeyPatch, tool_name: str, method: str, arguments: dict[str, Any], failure: str
) -> None:
    """All six tools expose expected failures without revealing exception details."""
    error: Exception
    if failure.startswith("http-"):
        status = int(failure.removeprefix("http-"))
        error = HTTPStatusException(status)
        error.args = (SECRET,)
        expected = f"HTTPStatusException: Upstream returned HTTP {status}."
    elif failure == "timeout":
        error = TimeoutException(SECRET)
        expected = "TimeoutException: DDGS request timed out."
    elif failure == "ratelimit":
        error = RatelimitException(SECRET)
        expected = "RatelimitException: Upstream rate limit reached."
    elif failure == "noresults":
        error = NoResultsException(SECRET)
        expected = "NoResultsException: No results found."
    elif failure == "ddgs":
        error = DDGSException(f"No results found. {SECRET}")
        expected = "DDGSException: Request failed."
    else:
        error = RuntimeError(SECRET)
        expected = f"Error executing tool {tool_name}"

    client = Mock()
    operation = Mock(side_effect=error)
    setattr(client, method, operation)
    monkeypatch.setattr(server, "DDGS", Mock(return_value=client))

    with pytest.raises(ToolError) as caught:
        asyncio.run(server.mcp.call_tool(tool_name, arguments))

    message = str(caught.value)
    if failure == "unexpected":
        assert isinstance(caught.value, UnexpectedToolError)
        assert message == expected
    else:
        assert not isinstance(caught.value, UnexpectedToolError)
        assert expected in message
        assert any(action in message for action in ("Retry", "Wait", "Try"))
    for secret in (SECRET, "proxy-user", "proxy-password", "private.example", "secret-token"):
        assert secret not in message
    operation.assert_called_once_with(**arguments)


@pytest.mark.parametrize(("tool_name", "method", "arguments"), TOOLS, ids=TOOL_IDS)
def test_constructor_errors_use_same_safe_boundary(
    monkeypatch: pytest.MonkeyPatch, tool_name: str, method: str, arguments: dict[str, Any]
) -> None:
    """DDGS initialization failures receive the same handling as method failures."""
    monkeypatch.setattr(server, "DDGS", Mock(side_effect=TimeoutException(SECRET)))
    with pytest.raises(ToolError, match="TimeoutException: DDGS request timed out") as caught:
        asyncio.run(server.mcp.call_tool(tool_name, arguments))
    assert not isinstance(caught.value, UnexpectedToolError)
    assert SECRET not in str(caught.value)
