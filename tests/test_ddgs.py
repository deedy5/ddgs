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
    query = "wolf"
    results = DDGS().text(query)
    assert isinstance(results, list)
    assert len(results) > 0

def test_images_search() -> None:
    query = "tiger"
    results = DDGS().images(query)
    assert isinstance(results, list)
    assert len(results) > 0

def test_news_search() -> None:
    query = "rabbit"
    results = DDGS().news(query)
    assert isinstance(results, list)
    assert len(results) > 0

def test_videos_search() -> None:
    query = "monkey"
    results = DDGS().videos(query)
    assert isinstance(results, list)
    assert len(results) > 0