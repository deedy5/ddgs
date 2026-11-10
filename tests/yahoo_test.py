"""Regression tests for Yahoo's legacy and current search-result layouts."""

import pytest

from ddgs.engines.yahoo import Yahoo


@pytest.fixture
def yahoo_engine() -> Yahoo:
    """Create a Yahoo engine without making network requests."""
    return Yahoo()


def test_yahoo_current_layout(yahoo_engine: Yahoo) -> None:
    """Extract distinct results from Yahoo's current algo-sr layout."""
    html = """
    <html><body>
      <section class="dd algo-sr">
        <div class="compTitle">
          <h3 class="title">
            <a class="s-title"
               href="https://r.search.yahoo.com/redirect/RU=https%3A%2F%2Fexample.com%2Farticle-one/RK=2">
              <span class="title-url">Example Source</span>Article One
            </a>
          </h3>
        </div>
        <div class="compText">
          <p class="s-desc">Description for article one.</p>
        </div>
      </section>
      <section class="dd algo-sr">
        <div class="compTitle">
          <h3 class="title">
            <a class="s-title" href="https://example.com/article-two">Article Two</a>
          </h3>
        </div>
        <div class="compText">
          <p class="s-desc">Description for article two.</p>
        </div>
      </section>
    </body></html>
    """

    results = yahoo_engine.post_extract_results(yahoo_engine.extract_results(html))

    assert len(results) == 2
    assert results[0].title == "Article One"
    assert results[0].href == "https://example.com/article-one"
    assert results[0].body == "Description for article one."
    assert results[1].title == "Article Two"
    assert results[1].href == "https://example.com/article-two"
    assert results[1].body == "Description for article two."


def test_yahoo_legacy_layout(yahoo_engine: Yahoo) -> None:
    """Preserve extraction of Yahoo's older relsrch result format."""
    html = """
    <html><body>
      <div class="relsrch">
        <div class="Title">
          <h3><a href="https://example.com/legacy">Legacy Article</a></h3>
        </div>
        <div class="Text">Legacy description.</div>
      </div>
    </body></html>
    """

    results = yahoo_engine.post_extract_results(yahoo_engine.extract_results(html))

    assert len(results) == 1
    assert results[0].title == "Legacy Article"
    assert results[0].href == "https://example.com/legacy"
    assert results[0].body == "Legacy description."
