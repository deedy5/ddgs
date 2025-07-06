import time
import pytest

from ddgs import DDGS


@pytest.fixture(autouse=True)
def pause_between_tests() -> None:
    time.sleep(2)


def test_context_manager() -> None:
    with DDGS() as ddgs:
        results = ddgs.news("cars", max_results=30)
        assert 20 <= len(results) <= 30


#def test_text_html() -> None:
#    results = DDGS().text("eagle", backend="html", region="br-pt", timelimit="y", max_results=20)
#    assert 15 <= len(results) <= 20
#
#
#def test_text_lite() -> None:
#    results = DDGS().text("dog", backend="lite", region="br-pt", timelimit="y", max_results=20)
#    assert 15 <= len(results) <= 20


def test_text_lite() -> None:
    results = DDGS().text("dog", backend="bing", region="br-pt", timelimit="y", max_results=20)
    assert 15 <= len(results) <= 20


def test_images() -> None:
    results = DDGS().images("flower", max_results=200)
    assert 85 <= len(results) <= 200


def test_videos() -> None:
    results = DDGS().videos("sea", max_results=40)
    assert 30 <= len(results) <= 40


def test_news() -> None:
    results = DDGS().news("tesla", max_results=30)
    assert 20 <= len(results) <= 30
