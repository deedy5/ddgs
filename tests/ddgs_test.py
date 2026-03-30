import time

import pytest

from ddgs import DDGS


@pytest.fixture(autouse=True)
def pause_between_tests() -> None:
    time.sleep(2)


def test_context_manager() -> None:
    with DDGS() as ddgs:
        results = ddgs.text("python")
        assert len(results) > 0


def test_text_search() -> None:
    results = DDGS().text("wolf")
    assert isinstance(results, list)
    assert len(results) > 0


def test_images_search() -> None:
    results = DDGS().images("tiger")
    assert isinstance(results, list)
    assert len(results) > 0


def test_news_search() -> None:
    results = DDGS().news("rabbit")
    assert isinstance(results, list)
    assert len(results) > 0


def test_videos_search() -> None:
    results = DDGS().videos("monkey")
    assert isinstance(results, list)
    assert len(results) > 0


def test_books_search() -> None:
    results = DDGS().books("mouse")
    assert isinstance(results, list)
    assert len(results) > 0


def test_extract() -> None:
    result = DDGS().extract("https://httpbin.org/html")
    assert isinstance(result, dict)
    assert "url" in result
    assert "content" in result
    assert isinstance(result["content"], str)
    assert len(result["content"]) > 0


def test_extract_text_plain() -> None:
    result = DDGS().extract("https://httpbin.org/html", fmt="text_plain")
    assert isinstance(result["content"], str)
    assert len(result["content"]) > 0


def test_extract_content() -> None:
    result = DDGS().extract("https://httpbin.org/html", fmt="content")
    assert isinstance(result["content"], bytes)
    assert len(result["content"]) > 0
