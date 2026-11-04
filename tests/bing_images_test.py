from ddgs.engines.bing_images import BingImages


def test_bing_images_payload_applies_safesearch() -> None:
    engine = BingImages()

    assert engine.build_payload("cats", "us-en", "on", None)["adlt"] == "strict"
    assert engine.build_payload("cats", "us-en", "moderate", None)["adlt"] == "moderate"
    assert engine.build_payload("cats", "us-en", "off", None)["adlt"] == "off"
