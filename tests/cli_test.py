import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from ddgs import DDGS, __version__
from ddgs.cli import _download_results, _save_csv, _save_json, cli
from ddgs.mcp_transport import (
    DEFAULT_MCP_TRANSPORT,
    normalize_mcp_endpoint,
    normalize_mcp_transport,
)

runner = CliRunner()


@pytest.fixture(autouse=True)
def pause_between_tests() -> None:
    time.sleep(2)


def test_version_command() -> None:
    result = runner.invoke(cli, ["version"])
    assert result.output.strip() == __version__


def test_text_command() -> None:
    result = runner.invoke(cli, ["text", "-q", "zebra"])
    assert "title" in result.output


def test_images_command() -> None:
    result = runner.invoke(cli, ["images", "-q", "fox"])
    assert "title" in result.output


def test_news_command() -> None:
    result = runner.invoke(cli, ["news", "-q", "deer"])
    assert "title" in result.output


def test_videos_command() -> None:
    result = runner.invoke(cli, ["videos", "-q", "pig"])
    assert "title" in result.output


def test_books_command() -> None:
    result = runner.invoke(cli, ["books", "-q", "bee"])
    assert "title" in result.output


def test_normalize_mcp_transport() -> None:
    assert normalize_mcp_transport(None) == DEFAULT_MCP_TRANSPORT
    assert normalize_mcp_transport("sse") == "sse"
    assert normalize_mcp_transport("http") == "http"


def test_normalize_mcp_endpoint() -> None:
    assert normalize_mcp_endpoint(None, "sse") == "/sse"
    assert normalize_mcp_endpoint("mcp", "http") == "/mcp"
    assert normalize_mcp_endpoint("/custom/", "http") == "/custom"
    assert normalize_mcp_endpoint("//custom//", "http") == "/custom"
    assert normalize_mcp_endpoint("//", "http") == "/"


def test_api_command_uses_transport_and_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    sentinel_app = object()

    def fake_create_api_server_app(transport: str, endpoint: str) -> object:
        captured["transport"] = transport
        captured["endpoint"] = endpoint
        return sentinel_app

    def fake_run(app: object, host: str, port: int, log_level: str, reload: bool) -> None:
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port
        captured["log_level"] = log_level
        captured["reload"] = reload

    monkeypatch.setattr("ddgs.cli._create_api_server_app", fake_create_api_server_app)
    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=fake_run))

    result = runner.invoke(cli, ["api", "--transport", "http", "--endpoint", "search"])

    assert result.exit_code == 0
    assert captured["app"] is sentinel_app
    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 8000
    assert captured["log_level"] == "info"
    assert captured["reload"] is False
    assert captured["transport"] == "http"
    assert captured["endpoint"] == "/search"
    assert "MCP server enabled with http transport at /search" in result.output


def test_text_workflow(tmp_path: Path) -> None:
    """Combined test for text search, save, and download functionality."""
    # Step 1: Get text results
    text_results = DDGS().text("cow", max_results=5)
    assert text_results

    # Step 2: Save to CSV
    csv_file = tmp_path / "test_csv.csv"
    _save_csv(csv_file, text_results)
    assert csv_file.exists()

    # Step 3: Save to JSON
    json_file = tmp_path / "test_json.json"
    _save_json(json_file, text_results)
    assert json_file.exists()

    # Step 4: Download results
    pathname = tmp_path / "text_downloads"
    _download_results("test_text_download", text_results, function_name="text", pathname=str(pathname))
    assert pathname.is_dir() and pathname.iterdir()
    for file in pathname.iterdir():
        assert file.is_file()


def test_images_workflow(tmp_path: Path) -> None:
    """Combined test for images search and download functionality."""
    # Step 1: Get images results
    images_results = DDGS().images("horse", max_results=5)
    assert images_results

    # Step 2: Download results
    pathname = tmp_path / "images_downloads"
    _download_results("test_images_download", images_results, function_name="images", pathname=str(pathname))
    assert pathname.is_dir() and pathname.iterdir()
    for file in pathname.iterdir():
        assert file.is_file()
