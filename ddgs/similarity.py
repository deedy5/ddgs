import re


class SimpleFilterRanker:
    """
    1) Pull any doc with 'wikipedia.org' in its href to the top.
    2) Bucket the rest according to where query tokens appear:
       - both title & body/description
       - title only
       - body only
       - neither
    3) Return wikipedia-top + both + title-only + body-only + neither.
    """

    _splitter = re.compile(r"\W+")

    def __init__(self, min_token_length: int = 3):
        self.min_token_length = min_token_length

    def _extract_tokens(self, query: str) -> set[str]:
        """Split on non-word characters & filter out short tokens."""
        return {token for token in self._splitter.split(query.lower()) if len(token) >= self.min_token_length}

    def _has_any_token(self, text: str, tokens: set[str]) -> bool:
        """Check if any token is a substring of the lower-cased text."""
        lower_text = text.lower()
        return any(tok in lower_text for tok in tokens)

    def rank(self, docs: list[dict[str, str]], query: str) -> list[dict[str, str]]:
        tokens = self._extract_tokens(query)

        wiki_hits = []
        both = []
        title_only = []
        body_only = []
        neither = []

        for doc in docs:
            href = doc.get("href", "")
            title = doc.get("title", "")
            # fallback to 'description' if no 'body'
            body = doc.get("body", doc.get("description", ""))

            # Skip Wikimedia category pages
            if all(x in title for x in ["Category:", "Wikimedia"]):
                continue

            # Wikipedia check
            if "wikipedia.org" in href:
                wiki_hits.append(doc)
                continue

            # Title / Body match
            hit_title = self._has_any_token(title, tokens)
            hit_body = self._has_any_token(body, tokens)

            if hit_title and hit_body:
                both.append(doc)
            elif hit_title:
                title_only.append(doc)
            elif hit_body:
                body_only.append(doc)
            else:
                neither.append(doc)

        # final ranking
        return wiki_hits + both + title_only + body_only + neither
