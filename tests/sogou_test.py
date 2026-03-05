from ddgs.engines.sogou import Sogou
from ddgs.http_client import Response


def test_sogou_uses_data_url_to_avoid_extra_requests() -> None:
    engine = Sogou()

    def fail_request(*_args: object, **_kwargs: object) -> Response:  # noqa: ARG001
        raise AssertionError("Unexpected request while resolving wrapper links")

    engine.http_client.request = fail_request  # type: ignore[method-assign]
    html_text = """
    <html><body>
      <div class="vrwrap">
        <h3 class="vr-title"><a href="/link?url=abc">Example title</a></h3>
        <div class="space-txt">Example body</div>
        <div class="r-sech" data-url="https://example.com/target"></div>
      </div>
    </body></html>
    """

    results = engine.post_extract_results(engine.extract_results(html_text))
    assert len(results) == 1
    assert results[0].href == "https://example.com/target"


def test_sogou_resolves_wrapper_link_when_data_url_missing() -> None:
    engine = Sogou()

    def fake_request(*args: object, **kwargs: object) -> Response:
        raise AssertionError("Unexpected request while resolving wrapper links")

    engine.http_client.request = fake_request  # type: ignore[method-assign]
    html_text = """
    <html><body>
      <div class="vrwrap">
        <h3 class="vr-title"><a href="/link?url=abc">Example title</a></h3>
        <div class="space-txt">Example body</div>
      </div>
    </body></html>
    """

    results = engine.post_extract_results(engine.extract_results(html_text))
    assert results == []
