from __future__ import annotations

import os
import pathlib
import shutil
import time
from pathlib import Path

import pytest
from click.testing import CliRunner

from ddgs import DDGS, __version__
from ddgs.cli import _download_results, _save_csv, _save_json, cli

runner = CliRunner()
TEXT_RESULTS = []
IMAGES_RESULTS = []

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


@pytest.mark.dependency()
def test_get_text() -> None:
    global TEXT_RESULTS
    TEXT_RESULTS = DDGS().text("cow", num_results=10)
    assert TEXT_RESULTS


@pytest.mark.dependency()
def test_get_images() -> None:
    global IMAGES_RESULTS
    IMAGES_RESULTS = DDGS().images("horse", num_results=10)
    assert IMAGES_RESULTS


@pytest.mark.dependency(depends=["test_get_text"])
def test_save_csv(tmp_path: Path) -> None:
    temp_file = tmp_path / "test_csv.csv"
    _save_csv(temp_file, TEXT_RESULTS)
    assert temp_file.exists()


@pytest.mark.dependency(depends=["test_get_text"])
def test_save_json(tmp_path: Path) -> None:
    temp_file = tmp_path / "test_json.json"
    _save_json(temp_file, TEXT_RESULTS)
    assert temp_file.exists()


@pytest.mark.dependency(depends=["test_get_text"])
def test_text_download() -> None:
    pathname = pathlib.Path("text_downloads")
    _download_results(f"{test_text_download}", TEXT_RESULTS, function_name="text", pathname=str(pathname))
    assert pathname.is_dir() and pathname.iterdir()
    for file in pathname.iterdir():
        assert file.is_file()
    shutil.rmtree(str(pathname))


@pytest.mark.dependency(depends=["test_get_images"])
def test_images_download() -> None:
    pathname = pathlib.Path("images_downloads")
    _download_results(f"{test_images_download}", IMAGES_RESULTS, function_name="images", pathname=str(pathname))
    assert pathname.is_dir() and pathname.iterdir()
    for file in pathname.iterdir():
        assert file.is_file()
    shutil.rmtree(str(pathname))